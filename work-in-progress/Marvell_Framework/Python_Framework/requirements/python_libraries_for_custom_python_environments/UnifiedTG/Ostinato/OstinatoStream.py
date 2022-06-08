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

#from ostinato.protocols.payload_pb2 import Payload, payload
# from ostinato.protocols.payload_pb2 import Payload, payload
import binascii
from collections import OrderedDict
import functools

from ostinato.protocols import dot3_pb2
from ostinato.protocols import llc_pb2
from ostinato.protocols import dot3_pb2, eth2_pb2, ip4_pb2, vlan_pb2, mac_pb2, dot2llc_pb2, snap_pb2, tcp_pb2, udp_pb2, \
    payload_pb2,ip6_pb2,ip4over6_pb2,ip6over4_pb2,svlan_pb2
from ostinato.protocols.hexdump_pb2 import hexDump

from pypacker import checksum

from UnifiedTG.Ostinato.OstinatoDriver import *
from UnifiedTG.Ostinato.OstinatoEnums import *
from UnifiedTG.Unified.Stream import Stream
from UnifiedTG.Unified.Utils import Converter
from UnifiedTG.Unified.Packet import Packet

from UnifiedTG.PacketBuilder.mpls import MPLS
#from UnifiedTG.PacketBuilder.UTG_2Packer import utg_2packer


class ostinatoPacket(Packet):
    def __init__(self):
        super(self.__class__, self).__init__()

    def add_mpls_label(self,name = None):
        self.l2_proto == TGEnums.L2_PROTO.ETHERNETII
        #self.ethertype = "8847"
        return super(self.__class__, self).add_mpls_label(name)

    def remove_mpls_label(self, name):
        super(self.__class__, self).remove_mpls_label(name)
        if len(self.mpls_labels) == 0:
            self.ethertype = self._ethertype._default_val

class ostinatoStreamDriverObj(object):
    def __init__(self):
        self.cfg = None
        self.stream = None

    @property
    def uri(self):
        return "{} {}".format(self.cfg.port_id.id, self.stream.stream_id.id)


class ostinatoStream(Stream):
    _continious_flag = False

    def __init__(self,s_name):
        super(self.__class__, self).__init__(s_name)
        self._stream_driver_obj = ostinatoStreamDriverObj()
        self._protoMap = OrderedDict()
        self._protoprotoMap = OrderedDict()
        self.packet = ostinatoPacket()

    def _add_protocol(self,proto,ext):
        s = self._stream_driver_obj.stream
        p = s.protocol.add()
        p.protocol_id.id = proto
        if type(ext) is list:
            for ex in ext:
                protoObj = p.Extensions[ex]
                self._protoMap[proto] = protoObj
        else:
            protoObj = p.Extensions[ext]
            self._protoMap[proto] = protoObj
            self._protoprotoMap[id(protoObj)] = p
            if ext is ip4over6_pb2.ip4over6 or ext is ip6over4_pb2.ip6over4:
                return p.Extensions[ip4_pb2.ip4],p.Extensions[ip6_pb2.ip6]
            elif ext is svlan_pb2.svlan:
                return p.Extensions[ext], p.Extensions[vlan_pb2.vlan]
        return protoObj

    def apply(self,apply_to_hw = False, selective_update=True):
        #clean previous protocols
        del self._stream_driver_obj.stream.protocol[:]
        super(self.__class__, self).apply()
        ostinatoConnector.drone().modifyStream(self._stream_driver_obj.cfg)

    def _apply_mac(self):

        my_mac = self._add_protocol(ost_pb.Protocol.kMacFieldNumber,mac_pb2.mac)

        hex_da = '0x'+self.packet.mac.da.value.replace(':','')
        my_mac.dst_mac = int(hex_da, 16)
        x = OstinatoEnums.unified_to_ostinato(self.packet.mac.da.mode)
        my_mac.dst_mac_mode = x
        my_mac.dst_mac_count = int(self.packet.mac.da.count)
        my_mac.dst_mac_step = int(self.packet.mac.da.step)

        hex_sa = '0x' + self.packet.mac.sa.value.replace(':', '')
        my_mac.src_mac = int(hex_sa, 16)
        my_mac.src_mac_mode = OstinatoEnums.unified_to_ostinato(self.packet.mac.sa.mode)
        my_mac.src_mac_count = int(self.packet.mac.sa.count)
        my_mac.src_mac_step = int(self.packet.mac.sa.step)

    def _apply_ethertype(self):
        pass

    def _apply_l2_proto(self):
        if self.packet.l2_proto == TGEnums.L2_PROTO.ETHERNETII:
            my_l2 = self._add_protocol(ost_pb.Protocol.kEth2FieldNumber,eth2_pb2.eth2)
            if self.packet.ethertype != self.packet._ethertype._default_val :
                my_l2.is_override_type = True
                my_l2.type = int(self.packet.ethertype,16)
        elif self.packet.l2_proto == TGEnums.L2_PROTO.SNAP:
            #proto.protocol_id.id = ost_pb.Protocol.kDot2SnapFieldNumber
            # my_dot2llc = proto.Extensions[dot2llc_pb2.Dot2Llc]
            # my_snap = proto.Extensions[snap_pb2.snap]
            self._add_protocol(ost_pb.Protocol.kDot2SnapFieldNumber,snap_pb2.snap)
            #my_l2 = self._add_protocol(ost_pb.Protocol.kDot2SnapFieldNumber,[dot2llc_pb2.Dot2Llc,snap_pb2.snap])
        elif self.packet.l2_proto == TGEnums.L2_PROTO.RAW:
            my_l2 = self._add_protocol(ost_pb.Protocol.kDot3FieldNumber,dot3_pb2.dot3)
        elif self.packet.l2_proto == TGEnums.L2_PROTO.PROTOCOL_OFFSET:
            hd = self._add_protocol(ost_pb.Protocol.kHexDumpFieldNumber, hexDump)
            hd.content = self._pattern_to_ascii_chars(self.packet.protocol_offset.value)
            hd.pad_until_end = False
        else: #self.packet.l2_proto == TGEnums.L2_PROTO.NONE:
            pass

    def _apply_vlans(self):
        def init_vlan(utg_vlan,ost_vlan):
            ost_vlan.is_override_tpid = True
            ost_vlan.tpid = Converter.convertstring2int(utg_vlan.proto)
            priority = (int(utg_vlan.priority) << 13)
            cfi = (int(utg_vlan.cfi) << 12)
            ost_vlan.vlan_tag = int(utg_vlan.vid.value) + priority + cfi

        if len(self.packet.vlans) > 0:
            vlans_list = list(self.packet.vlans.items())
            if len(self.packet.vlans) == 1:
                my_vlan = self._add_protocol(ost_pb.Protocol.kVlanFieldNumber,vlan_pb2.vlan)
                utg_vlan = vlans_list[0][1]
                my_vlan.is_override_tpid = True
                my_vlan.tpid = int(utg_vlan.proto,16)
                priority = (int(utg_vlan.priority)<<13)
                cfi = (int(utg_vlan.cfi)<<12)
                my_vlan.vlan_tag = int(utg_vlan.vid.value)+priority+cfi
            elif len(self.packet.vlans) == 2:
                utg_v1 = vlans_list[0][1]
                utg_v2 = vlans_list[1][1]
                ost_v1,ost_v2 = self._add_protocol(ost_pb.Protocol.kVlanStackFieldNumber, svlan_pb2.svlan)
                init_vlan(utg_v1,ost_v1)
                init_vlan(utg_v2,ost_v2)


    def _apply_mpls(self):
        if len(self.packet.mpls_labels)>0:
            mpls_bin = None
            for idx, mp in enumerate(self.packet.mpls_labels):
                obj = self.packet.mpls_labels[mp]
                mpls =MPLS(label=int(obj.label),ttl=int(obj.ttl))
                mpls.bottom_stack = 1 if len(self.packet.mpls_labels) == idx+1 else 0
                mpls.exp = obj.experimental
                mpls_bin = mpls_bin+mpls.bin() if mpls_bin else mpls.bin()
                #sum_bin = binascii.hexlify(mpls_bin).decode('utf-8')
            hd = self._add_protocol(ost_pb.Protocol.kHexDumpFieldNumber, hexDump)
            hd.content = mpls_bin
            hd.pad_until_end = False


    def _apply_l3_proto(self):
        pass

    def _apply_l4_proto(self):
        pass

    def _update_v4_fields(self, source_obj, dest_obj):


        dest_obj.dst_ip = Converter.stringIp2int(source_obj.destination_ip.value)
        dest_obj.dst_ip_mode = OstinatoEnums.unified_to_ostinato(source_obj.destination_ip.mode)
        dest_obj.dst_ip_count = int(source_obj.destination_ip.count)
        dest_obj.dst_ip_mask = Converter.stringIp2int(source_obj.destination_ip.mask)

        dest_obj.src_ip = Converter.stringIp2int(source_obj.source_ip.value)
        dest_obj.src_ip_mode = OstinatoEnums.unified_to_ostinato(source_obj.source_ip.mode)
        dest_obj.src_ip_count = int(source_obj.source_ip.count)
        dest_obj.src_ip_mask = Converter.stringIp2int(source_obj.source_ip.mask)

        dest_obj.ttl  = int(source_obj.ttl)
        dest_obj.is_override_hdrlen = source_obj.enable_header_len_override
        dest_obj.is_override_totlen = source_obj.length_override
        if source_obj.checksum_mode is TGEnums.CHECKSUM_MODE.OVERRIDE:
            dest_obj.is_override_cksum = True
            dest_obj.cksum = int(source_obj.custom_checksum,16)
        dest_obj.ver_hdrlen = source_obj.header_len_override_value
        dest_obj.tos = int(source_obj.dscp_decimal_value,16)
        dest_obj.totlen = source_obj.length_value
        dest_obj.id = int(source_obj.identifier)
        dest_obj.frag_ofs = source_obj.fragment_offset_decimal_value
        #ip.options = source_obj.options_padding ::==>>Ostinato's TODO ip options
        #ip.is_override_ver =
        if self.packet.l4_proto is TGEnums.L4_PROTO.GRE:
            dest_obj.is_override_proto = True
            dest_obj.proto = 0x2F
        elif self.packet.l4_proto is TGEnums.L4_PROTO.NONE:
            #common default value
            dest_obj.is_override_proto = True
            dest_obj.proto = source_obj.protocol
        elif not source_obj._protocol._is_default:
            dest_obj.is_override_proto = True
            dest_obj.proto = source_obj.protocol
        df = 0 if source_obj.fragment_enable else 2
        mf = 0 if source_obj.fragment_last_enable else 1
        dest_obj.flags = df+mf
        return dest_obj

    def _apply_ipv4(self, source_obj = None):
        source_obj = self.packet.ipv4 if not source_obj else source_obj
        ost_obj = self._add_protocol(ost_pb.Protocol.kIp4FieldNumber,ip4_pb2.ip4)
        self._update_v4_fields(source_obj, ost_obj)

    def _handle_v6(self,input):
        input = Converter.expand_ipv6(input)
        input = Converter.remove_non_hexa_sumbols(input)
        split = int(len(input)/2)
        low = Converter.convertstring2int(input[split:])
        high = Converter.convertstring2int(input[:split])
        return high,low

    def _update_v6_fields(self, source_obj, dest_obj):
        if not source_obj._next_header._is_default:
            dest_obj.is_override_next_header = True
            dest_obj.next_header = Converter.convertstring2int(source_obj._next_header.current_val)
        dest_obj.traffic_class = int(source_obj.traffic_class) #int(Converter.remove_non_hexa_sumbols(hex(int(source_obj.traffic_class))))#Converter.convertstring2int(source_obj.traffic_class)
        dest_obj.hop_limit = int(source_obj.hop_limit) #Converter.convertstring2int
        dest_obj.flow_label = Converter.convertstring2int(source_obj.flow_label)
        dest_obj.src_addr_hi, dest_obj.src_addr_lo = self._handle_v6(source_obj.source_ip.value)
        dest_obj.dst_addr_hi, dest_obj.dst_addr_lo = self._handle_v6(source_obj.destination_ip.value)
        dest_obj.src_addr_mode = OstinatoEnums.unified_to_ostinato(source_obj.source_ip.mode)
        dest_obj.src_addr_count = int(source_obj.source_ip.count) if source_obj.source_ip.count != '0' else 1
        dest_obj.dst_addr_mode = OstinatoEnums.unified_to_ostinato(source_obj.destination_ip.mode)
        dest_obj.dst_addr_count = int(source_obj.destination_ip.count) if source_obj.destination_ip.count != '0' else 1
        return dest_obj

    def _apply_ipv6(self, source_obj=None):
        ip = self._add_protocol(ost_pb.Protocol.kIp6FieldNumber, ip6_pb2.ip6)
        source_obj = self.packet.ipv6 if not source_obj else source_obj
        self._update_v6_fields(source_obj, ip)

    def _apply_v4_over_v6(self):
        ost_v4_obj,ost_v6_obj = self._add_protocol(ost_pb.Protocol.kIp4over6FieldNumber, ip4over6_pb2.ip4over6)
        self._update_v6_fields(self.packet.ipv6,ost_v6_obj)
        self._update_v4_fields(self.packet.ipv4,ost_v4_obj)

    def _apply_v6_over_v4(self):
        ost_v4_obj, ost_v6_obj = self._add_protocol(ost_pb.Protocol.kIp6over4FieldNumber, ip6over4_pb2.ip6over4)
        self._update_v6_fields(self.packet.ipv6,ost_v6_obj)
        self._update_v4_fields(self.packet.ipv4,ost_v4_obj)

    def _apply_tcp(self, source_obj=None):
        source_obj = self.packet.tcp if not source_obj else source_obj
        my_tcp = self._add_protocol(ost_pb.Protocol.kTcpFieldNumber,tcp_pb2.tcp)
        my_tcp.is_override_src_port = True
        my_tcp.is_override_dst_port = True
        #my_tcp.is_override_hdrlen = True
        if source_obj.valid_checksum is TGEnums.CHECKSUM_MODE.OVERRIDE:
            my_tcp.is_override_cksum = True
            my_tcp.cksum = int(source_obj.custom_checksum, 16)
        my_tcp.src_port = int(source_obj.source_port.value)
        my_tcp.dst_port = int(source_obj.destination_port.value)
        my_tcp.seq_num = int(source_obj.sequence_number,16)
        my_tcp.ack_num = int(source_obj.acknowledgement_number,16)
        my_tcp.hdrlen_rsvd = int(source_obj.header_length)
        flags_list = [int(source_obj.flag_urgent_pointer_valid),
                      int(source_obj.flag_acknowledge_valid),
                      int(source_obj.flag_push_function),
                      int(source_obj.flag_reset_connection),
                      int(source_obj.flag_synchronize_sequence),
                      int(source_obj.flag_no_more_data_from_sender)]
        my_tcp.flags = functools.reduce(lambda out,x: (out<<1)+int(x),flags_list,0)
        my_tcp.window = int(source_obj.window,16)
        my_tcp.urg_ptr = int(source_obj.urgent_pointer,16)

    def _apply_udp(self, source_obj=None):
        source_obj = self.packet.udp if not source_obj else source_obj
        my_udp = self._add_protocol(ost_pb.Protocol.kUdpFieldNumber,udp_pb2.udp)
        my_udp.is_override_src_port = True
        my_udp.is_override_dst_port = True
        if source_obj.length_override:
            my_udp.is_override_totlen = True
            my_udp.totlen = source_obj.custom_length
        if source_obj.valid_checksum is TGEnums.CHECKSUM_MODE.OVERRIDE:
            my_udp.is_override_cksum =True
            my_udp.cksum= int(source_obj.custom_checksum,16)
        my_udp.src_port = int(source_obj.source_port.value)
        my_udp.dst_port = int(source_obj.destination_port.value)

    def _apply_gre_fields(self):
        obj = self.packet.gre.to_packer()
        hd = self._add_protocol(ost_pb.Protocol.kHexDumpFieldNumber, hexDump)
        bin_headers = '0x' + binascii.hexlify(obj.bin()).decode('utf-8')
        hd.content = obj.bin()
        hd.pad_until_end = False
        if self.packet.gre.l3_proto is TGEnums.L3_PROTO.IPV4:
            self._apply_ipv4(self.packet.gre.ipv4)
        elif self.packet.gre.l3_proto is TGEnums.L3_PROTO.IPV6:
            self._apply_ipv6(self.packet.gre.ipv6)

        if self.packet.gre.l4_proto is TGEnums.L4_PROTO.UDP:
            self._apply_udp(self.packet.gre.udp)
        elif self.packet.gre.l4_proto is TGEnums.L4_PROTO.TCP:
            self._apply_tcp(self.packet.gre.tcp)

    def _apply_gre(self):
        self._apply_l3()
        self._apply_gre_fields()

    def _pattern_to_ascii_chars(self, pattern):
        PY3K = sys.version_info >= (3, 0)
        asci_chars = bytes() if PY3K else ""
        patternString = Converter.remove_non_hexa_sumbols(pattern[:])
        while patternString:
            tmp_char = chr(int(patternString[:2], 16))
            char = bytes(tmp_char, 'latin-1') if PY3K else tmp_char
            asci_chars += char
            patternString = patternString[2:]
        return bytes(asci_chars) if PY3K else asci_chars

    def _apply_data_pattern(self):

        if self.packet.data_pattern.type == TGEnums.DATA_PATTERN_TYPE.FIXED:
            hd = self._add_protocol(ost_pb.Protocol.kHexDumpFieldNumber, hexDump)
            hd.content = self._pattern_to_ascii_chars(self.packet.data_pattern.value)
        else:
            my_payload = self._add_protocol(ost_pb.Protocol.kPayloadFieldNumber,payload_pb2.payload)
            my_payload.pattern_mode = OstinatoEnums.unified_to_ostinato(self.packet.data_pattern.type)
            my_payload.pattern = int(self.packet.data_pattern.value, 16)

    def _apply_stream_rate(self):
        s = self._stream_driver_obj.stream
        if self.rate.mode == TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND:
            if str(self.control.bursts_per_stream) == '1':
                s.control.packets_per_sec = float(self.rate.pps_value)
            else:
                bps = int(self.rate.pps_value)/int(self.control.packets_per_burst)
                s.control.bursts_per_sec = float(bps)

    def _apply_stream_control(self):
        s = self._stream_driver_obj.stream
        if self.packet.mac.fcs is TGEnums.FCS_ERRORS_MODE.NO_ERROR:
            fcs = 1
        elif self.packet.mac.fcs is TGEnums.FCS_ERRORS_MODE.BAD_CRC:
            fcs = 2
        elif self.packet.mac.fcs is TGEnums.FCS_ERRORS_MODE.NO_CRC:
            fcs = 0

        s.core.force_errors_mode = fcs
        #fake continous mode: once one of the streams should transmit cont_mode it configured to goto_id and rest of the are streams disabled
        s.core.is_enabled = self.enabled if not self.__class__._continious_flag else False
        if int(self.control.bursts_per_stream) == 1:
            s.control.unit = ost_pb.StreamControl.e_su_packets
            s.control.num_packets = int(self.control.packets_per_burst)
        else:
            s.control.unit = ost_pb.StreamControl.e_su_bursts
            s.control.packets_per_burst = int(self.control.packets_per_burst)
            s.control.num_bursts = int(self.control.bursts_per_stream)
            pps = int(self.control.bursts_per_stream)/int(self.control.packets_per_burst)

        if self.control.mode == TGEnums.STREAM_TRANSMIT_MODE.CONTINUOUS_PACKET:
            s.control.mode = ost_pb.StreamControl.e_sm_continuous
            s.control.next = ost_pb.StreamControl.e_nw_goto_id
            ostinatoStream._continious_flag = True
        elif self.control.mode == TGEnums.STREAM_TRANSMIT_MODE.CONTINUOUS_BURST:
            s.control.mode = ost_pb.StreamControl.e_sm_continuous
        elif self.control.mode == TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM:
            s.control.next = ost_pb.StreamControl.e_nw_stop
        elif self.control.mode == TGEnums.STREAM_TRANSMIT_MODE.ADVANCE_TO_NEXT_STREAM:
            s.control.next = ost_pb.StreamControl.e_nw_goto_next
        elif self.control.mode == TGEnums.STREAM_TRANSMIT_MODE.RETURN_TO_ID:
            s.control.next = ost_pb.StreamControl.e_nw_goto_id

    def _apply_frame_size(self):
        s = self._stream_driver_obj.stream
        s.core.len_mode = OstinatoEnums.unified_to_ostinato(self.frame_size.mode)
        if self.frame_size.mode is TGEnums.MODIFIER_FRAME_SIZE_MODE.FIXED:
            s.core.frame_len = int(self.frame_size.value)
        else:
            s.core.frame_len_min = int(self.frame_size.min)
            s.core.frame_len_max = int(self.frame_size.max)

    def _apply_udfs(self):
        for udf in self.packet.modifiers:
            curUdf = self.packet.modifiers[udf]
            if curUdf.enabled is True:
                p, pOffset = self._get_header_by_offset(curUdf.byte_offset)
                if p:
                    protoproto =  self._protoprotoMap[id(p)]
                    variable_field = protoproto.variable_field.add()
                    variable_field.offset = curUdf.byte_offset - pOffset
                    variable_field.type = int(curUdf.bit_type.value/16)
                    variable_field.value = Converter.stringMac2int(curUdf.repeat_init,' ')
                    variable_field.mode = OstinatoEnums.unified_to_ostinato(curUdf.repeat_mode)
                    variable_field.count = int(curUdf.repeat_count)
                    variable_field.step = int(curUdf.repeat_step)
            #variable_field.mask = 0xf0
        # counter = 1
        # for id,udf in enumerate(self.packet.modifiers):
        #     curUdf = self.packet.modifiers[udf]
        #     self._stream_driver_obj.udf.ix_set_default()
        #     self._update_field(driver_field="udf.enable", value=curUdf.enabled)
        #     self._update_field(driver_field="udf.offset", value=curUdf.byte_offset)
        #     self._update_field(driver_field="udf.bitOffset", value=curUdf.bit_offset)
        #     self._update_field(driver_field="udf.counterMode", value=IxExEnums.TGEnums_IxExEnums_map(curUdf.mode,IxExEnums.UDF_COUNTER_MODE))
        #     self._update_field(driver_field="udf.udfSize", value=curUdf.bit_type.value)
        #     self._update_field(driver_field="udf.repeat", value=curUdf.repeat_count)
        #     self._update_field(driver_field="udf.continuousCount", value= curUdf.continuously_counting)
        #     self._update_field(driver_field="udf.initval", value='{'+curUdf.repeat_init+'}')
        #     self._update_field(driver_field="udf.updown", value=IxExEnums.TGEnums_IxExEnums_map(curUdf.repeat_mode,IxExEnums.UDF_REPEAT_MODE))
        #     self._update_field(driver_field="udf.step", value=curUdf.repeat_step)
        #     self._stream_driver_obj.udf.set(counter)
        #     counter += 1
        # self._stream_driver_obj.ix_set()

    def _get_header_by_offset(self,offset):
        protocols = self._stream_driver_obj.stream.protocol[:]
        current_offset=0
        for p in protocols:
            id = p.protocol_id.id
            protoSize=OstinatoEnums._converter.protoSize(id)
            if not isinstance(protoSize, int):
                return None, None
            protoObj = self._protoMap[id]
            if current_offset+protoSize > offset:
                return protoObj,current_offset
            current_offset += protoSize
        return None,None

    def _hw_sync(self):
        pass

    def _apply_stream_status(self):
        pass

    def _apply_preamble_size(self):
        pass

    def _apply_protocol_offset(self):
        pass