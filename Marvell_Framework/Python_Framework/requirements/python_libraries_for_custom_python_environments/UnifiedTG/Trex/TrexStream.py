###################################################################################
#	Marvell GPL License
#	
#	If you received this File from Marvell, you may opt to use, redistribute and/or
#	modify this File in accordance with the terms and conditions of the General
#	Public License Version 2, June 1991 (the "GPL License"), a copy of which is
#	available along with the File in the license.txt file or by writing to the Free
#	Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 or
#	on the worldwide web at http://www.gnu.org/licenses/gpl.txt.
#	
#	THE FILE IS DISTRIBUTED AS-IS, WITHOUT WARRANTY OF ANY KIND, AND THE IMPLIED
#	WARRANTIES OF MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE ARE EXPRESSLY
#	DISCLAIMED.  The GPL License provides additional details about this warranty
#	disclaimer.
###################################################################################


from UnifiedTG.Unified.Stream import Stream
from UnifiedTG.Unified.TGEnums import TGEnums
from pytrex.trex_stream import TrexRateType, TrexTxType
from pytrex.trex_stl_packet_builder_scapy import STLPktBuilder
from scapy.packet import Packet as scapy_packet
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, ICMP, IPOption, TCP, UDP
from scapy.layers.inet6 import IPv6
from scapy.fields import raw

class TrexStream(Stream):

    _sentinel = object() # used for _update_field function

    def __init__(self, stream_name=None):
        super(self.__class__, self).__init__(stream_name)
        self._scapy_packet = Ether()

    def apply(self, apply_to_hw = False, selective_update=True):
        self._logger.info(self._get_stream_log_title(), self._get_stream_log_message())
        super(self.__class__, self).apply()
        # self.set_from_scapy(self._scapy_packet)
        if apply_to_hw:
            try:
                self._stream_driver_obj.set_packet(packet=STLPktBuilder(pkt=self._scapy_packet))
                rc = self._parent._port_driver_obj.write_streams()
            except Exception as e:
                print(str(e))
                self._logger.info("TrexStream apply exception", str(e))

    def _apply_stream_rate(self):
        rate_mode = None
        value = None
        if self.rate.mode == TGEnums.STREAM_RATE_MODE.UTILIZATION:
            rate_mode = TrexRateType.percentage
            value = self.rate.utilization_value
        elif self.rate.mode == TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND:
            rate_mode = TrexRateType.pps
            value = self.rate.pps_value
        elif self.rate.mode == TGEnums.STREAM_RATE_MODE.BITRATE_PER_SECOND:
            rate_mode = TrexRateType.bps_l2
            value = self.rate.bitrate_value
        elif self.rate.mode == TGEnums.STREAM_RATE_MODE.L1_BITRATE_PER_SECOND:
            rate_mode = TrexRateType.bps_l1
            value = self.rate.bitrate_value
        else:
            raise Exception("rate.mode not support: {}".format(self.rate.mode))
        self._stream_driver_obj.set_rate(type=rate_mode, value=float(value))


    def _apply_stream_control(self):
        gap_val = 0
        if self.control.inter_stream_gap_enable:
            gap_val = self.control.inter_stream_gap_value

        control_mode = None
        next_id = None
        if self.control.mode == TGEnums.STREAM_TRANSMIT_MODE.CONTINUOUS_PACKET:
            control_mode = TrexTxType.continuous
        elif self.control.mode == TGEnums.STREAM_TRANSMIT_MODE.CONTINUOUS_BURST:
            control_mode = TrexTxType.multi_burst
        elif self.control.mode == TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM:
            control_mode = TrexTxType.single_burst
            next_id = None
        elif self.control.mode == TGEnums.STREAM_TRANSMIT_MODE.ADVANCE_TO_NEXT_STREAM:
            control_mode = TrexTxType.single_burst
        elif self.control.mode == TGEnums.STREAM_TRANSMIT_MODE.RETURN_TO_ID:
            control_mode = TrexTxType.single_burst
            next_id = self.control.return_to_id
        else:
            raise Exception("control.mode not support: {}".format(self.control.mode))

        self._stream_driver_obj.set_tx_type(type=control_mode,
                                            packets=int(self.control.packets_per_burst),
                                            ibg=int(gap_val),
                                            count=int(self.control.loop_count))
        self._stream_driver_obj.set_next(next_id)

    def set_from_json(self, path_to_json):
        '''
        Get a path to json file describing the packet and write it to the Packet object
        :param path_to_json: full path to the json file
        :type path_to_json: str
        :return:
        '''
        pass

    def set_from_scapy(self, scapy_packet):
        '''
        Get a Scapy packet obejct and write it to HW (the packet's structure currently doesn't get write to the Packet object
        :param scapy_packet:
        :return:
        '''
        self._logger.info(self._get_stream_log_title(), self._get_stream_log_message())
        try:
            self._apply_stream_rate()
            self._apply_stream_control()
            self._stream_driver_obj.set_packet(packet=STLPktBuilder(pkt=self._scapy_packet))
            rc = self._parent._port_driver_obj.write_streams()
        except Exception as e:
            print(str(e))
            self._logger.info("Trex set_from_scapy exception", str(e))




    def _apply_mac(self):
        fields = {}
        dst = self.packet.mac.da.value
        fields['dst'] = dst
        src = self.packet.mac.sa.value
        fields['src'] = src

        if self.packet.l3_proto == TGEnums.L3_PROTO.IPV4:
            fields['type'] = int("0x0800", 16)
        elif self.packet.l3_proto == TGEnums.L3_PROTO.IPV6:
            fields['type'] = int("0x86dd", 16)
        elif self.packet.l3_proto == TGEnums.L3_PROTO.NONE:
            pass
        elif self.packet.l3_proto == TGEnums.L3_PROTO.CUSTOM:
            fields['type'] = int(self.packet.ethertype, 16)


        self._scapy_packet = Ether(**fields)


    def _apply_ipv4(self, ipv4_obj=None):
        fields = {}
        sip = self.packet.ipv4.source_ip.value
        fields['src'] = sip
        dip = self.packet.ipv4.destination_ip.value
        fields['dst'] = dip
        ttl = int(self.packet.ipv4.ttl)
        fields['ttl'] = ttl
        # version = int(self.packet.ipv4.ver)
        if self.packet.ipv4.enable_header_len_override:
            ihl = int(self.packet.ipv4.header_len_override_value)
            fields['ihl'] = ihl
        tos = int(self.packet.ipv4.dscp_decimal_value) * 4
        fields['tos'] = tos
        if self.packet.ipv4.length_override:
            len = int(self.packet.ipv4.length_value)
            fields['len'] = len
        id = int(self.packet.ipv4.identifier)
        fields['id'] = id
        flags_list = []
        if not self.packet.ipv4.fragment_enable:
            flags_list.append("MF")
        if self.packet.ipv4.fragment_last_enable:
            flags_list.append("DF")
        fields['flags'] = flags_list
        frag = int(self.packet.ipv4.fragment_offset_decimal_value)
        fields['frag'] = frag
        proto = int(self.packet.ipv4.protocol)
        fields['proto'] = proto
        if self.packet.ipv4.checksum_mode == TGEnums.CHECKSUM_MODE.OVERRIDE:
            chksum = int(self.packet.ipv4.custom_checksum)
            fields['chksum'] = chksum
        elif self.packet.ipv4.checksum_mode == TGEnums.CHECKSUM_MODE.INVALID:
            fields['chksum'] = 65534
        if self.packet.ipv4.options_padding != "{}":
            options = [IPOption(self.packet.ipv4.options_padding)]
            fields['options'] = options
        self._scapy_packet = self._scapy_packet / IP(**fields)

    def _apply_ipv6(self):
        fields = {}
        sip = self.packet.ipv6.source_ip.value
        fields['src'] = sip
        dip = self.packet.ipv6.destination_ip.value
        fields['dst'] = dip
        hlim = int(self.packet.ipv6.hop_limit)
        fields['hlim'] = hlim
        tc = int(self.packet.ipv6.traffic_class)
        fields['tc'] = tc
        fl = int(self.packet.ipv6.flow_label)
        fields['fl'] = fl

        self._scapy_packet = self._scapy_packet / IPv6(**fields)

    def _apply_tcp(self):
        fields = {}
        fields['sport'] = int(self.packet.tcp.source_port.value)
        fields['dport'] = int(self.packet.tcp.destination_port.value)
        fields['ack'] = int(self.packet.tcp.acknowledgement_number)
        fields['seq'] = int(self.packet.tcp.sequence_number)
        fields['urgptr'] = int(self.packet.tcp.urgent_pointer)
        fields['window'] = int(self.packet.tcp.window)
        fields['dataofs'] = int(self.packet.tcp.header_length)
        if self.packet.tcp.valid_checksum == TGEnums.CHECKSUM_MODE.OVERRIDE:
            chksum = int(self.packet.tcp.custom_checksum)
            fields['chksum'] = chksum
        elif self.packet.tcp.valid_checksum == TGEnums.CHECKSUM_MODE.INVALID:
            fields['chksum'] = 65534
        flags_list = []
        if self.packet.tcp.flag_acknowledge_valid:
            flags_list.append("A")
        if self.packet.tcp.flag_no_more_data_from_sender:
            flags_list.append("F")
        if self.packet.tcp.flag_push_function:
            flags_list.append("P")
        if self.packet.tcp.flag_reset_connection:
            flags_list.append("R")
        if self.packet.tcp.flag_synchronize_sequence:
            flags_list.append("S")
        if self.packet.tcp.flag_urgent_pointer_valid:
            flags_list.append("U")
        fields['flags'] = flags_list
        self._scapy_packet = self._scapy_packet / TCP(**fields)

    def _apply_udp(self):
        fields = {}
        fields['sport'] = int(self.packet.udp.source_port.value)
        fields['dport'] = int(self.packet.udp.destination_port.value)
        if self.packet.udp.length_override:
            fields['len'] = int(self.packet.udp.custom_length)
        if self.packet.udp.valid_checksum == TGEnums.CHECKSUM_MODE.OVERRIDE:
            chksum = int(self.packet.udp.custom_checksum)
            fields['chksum'] = chksum
        elif self.packet.udp.valid_checksum == TGEnums.CHECKSUM_MODE.INVALID:
            fields['chksum'] = 65534
        self._scapy_packet = self._scapy_packet / UDP(**fields)

    def _apply_data_pattern(self):
        data = str(self.packet.data_pattern.value).encode("utf-8")
        self._scapy_packet = self._scapy_packet / raw(data)
    #set_tx_type
    #set_flow_stats
    #set_packet
    #config
