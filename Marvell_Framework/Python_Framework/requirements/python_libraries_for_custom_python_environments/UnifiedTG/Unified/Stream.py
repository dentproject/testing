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

import inspect
from collections import OrderedDict
from UnifiedTG.Unified.Packet import Packet
from UnifiedTG.Unified.Utils import attrWithDefault,_stat_member
from UnifiedTG.Unified.TGEnums import TGEnums
from UnifiedTG.Unified.UtgObject import UtgObject


class Stream(UtgObject):
    def __init__(self, stream_name=None,debug_prints=False):
        self._port_transmit_mode = None
        self._debug_prints = debug_prints
        self._stream_driver_obj = None
        self._parent = None
        self._name = stream_name
        if self._name is None:
            self._name = ""
        self.packet = Packet()  # type: Packet
        self.rate = _RATE_CONTROL()
        self.frame_size = _FRAME_SIZE(self)
        self.control = _STREAM_CONTROL()
        self.statistics = _stream_stats()
        self.instrumentation= _INSTRUMENTATION()
        self._enabled = attrWithDefault(True)
        self._suspend = attrWithDefault(False)
        # self.packet._update_parent(self)
        self.source_interface = Source_Interface()

    def __str__(self):
        uri = str(self._stream_driver_obj.uri) if hasattr(self._stream_driver_obj,'uri') else str(self._stream_driver_obj.ref)
        tempstr = ""
        tempstr += "Stream name: " + self._name + "\n"
        tempstr += "Stream uri: " + uri + "\n"
        tempstr += "Stream port name: " + self._parent._port_name + "\n"
        tempstr += "Stream packet: " + str(self.packet) + "\n"
        tempstr += "Packet size: " + str(self.frame_size) + "\n"
        tempstr += "Stream control: " + str(self.control) + "\n"
        tempstr += "Stream enabled: " + str(self.enabled) + "\n"
        tempstr += "Stream suspended: " + str(self.suspend) + "\n"
        tempstr += "Stream rate: " + str(self.rate) + "\n"
        tempstr += "Stream port transmit mode: " + str(self._port_transmit_mode) + "\n"

        return tempstr

    @property
    def enabled(self):
        """enabled : True/False """
        return self._enabled.current_val

    @enabled.setter
    def enabled(self, v):
        """enabled : """
        self._enabled.current_val = v

    @property
    def suspend(self):
        """suspend : """
        return self._suspend.current_val

    @suspend.setter
    def suspend(self, v):
        """suspend : """
        self._suspend.current_val = v

    def build(self):
        pass


    def apply(self, apply_to_hw = False, selective_update=True):
        """
        Applies all streams configuration including packet
        :param apply_to_hw: True - write configuration to HW, False - only updated object, useful when adding many
        streams, only apply to HW the last stream or use port apply.
        :param selective_update: Update only relevant configuration (if ipv4 is selected as L3 proto, don't update
        ipv6 configuration for example).
        """
        if selective_update == True:
            self._apply_mac()
            if len(self.packet.vlans) > 0:
                self._apply_vlans()
            self._apply_special_tag()
            self._apply_l2_proto()
            self._apply_mpls()
            self._apply_frame_preemption()
            self._apply_protocol_offset()
            self._apply_ethertype()
            self._apply_l3_proto()
            if self.packet.l4_proto is TGEnums.L4_PROTO.GRE:
                self._apply_gre()
            else:
                self._apply_l4_proto()
                self._apply_l3()
                self._apply_l4()
            self._apply_protocol_pad()
            self._apply_data_pattern()
            self._apply_stream_rate()
            self._apply_stream_control()
            self._apply_stream_status()
            self._apply_frame_size()
            self._apply_preamble_size()
            self._apply_data_integrity()
            if len(self.packet.modifiers) > 0:
                self._apply_udfs()

        else:
            self._apply_mac()
            self._apply_l2_proto()
            self._apply_vlans()
            self._apply_ethertype()
            self._apply_l3_proto()
            self._apply_l4_proto()
            self._apply_ipv4()
            self._apply_ipv6()
            self._apply_tcp()
            self._apply_udp()
            self._apply_data_pattern()
            self._apply_stream_rate()
            self._apply_stream_control()
            self._apply_stream_status()
            self._apply_frame_size()
            self._apply_preamble_size()
            self._apply_udfs()
            # self._stream_driver_obj.write()

    def _apply_l3(self):
        if self.packet.l3_proto == TGEnums.L3_PROTO.IPV4:
            self._apply_ipv4()
        elif self.packet.l3_proto == TGEnums.L3_PROTO.IPV6:
            self._apply_ipv6()
        elif self.packet.l3_proto is TGEnums.L3_PROTO.IPV4_O_IPV6:
            self._apply_v4_over_v6()
        elif self.packet.l3_proto is TGEnums.L3_PROTO.IPV6_O_IPV4:
            self._apply_v6_over_v4()
        elif self.packet.l3_proto is TGEnums.L3_PROTO.ARP:
            self._apply_arp()


    def _apply_l4(self):
        if self.packet.l4_proto == TGEnums.L4_PROTO.TCP:
            self._apply_tcp()
        elif self.packet.l4_proto == TGEnums.L4_PROTO.UDP:
            self._apply_udp()
        elif self.packet.l4_proto is TGEnums.L4_PROTO.ICMP:
            self._apply_icmp()

    def _apply_mac(self):
        pass

    def _apply_ethertype(self):
        pass

    def _apply_l2_proto(self):
        pass

    def _apply_vlans(self):
        pass

    def _apply_mpls(self):
        pass

    def _apply_frame_preemption(self):
        pass

    def _apply_l3_proto(self):
        pass

    def _apply_l4_proto(self):
        pass

    def _apply_ipv4(self):
        pass

    def _apply_ipv6(self):
        pass

    def _apply_v4_over_v6(self):
        pass

    def _apply_v6_over_v4(self):
        pass

    def _apply_tcp(self):
        pass

    def _apply_udp(self):
        pass

    def _apply_icmp(self):
        pass

    def _apply_gre(self):
        pass

    def _apply_protocol_pad(self):
        pass

    def _apply_data_pattern(self):
        pass

    def _apply_stream_rate(self):
        pass

    def _apply_stream_control(self):
        pass

    def _apply_frame_size(self):
        pass

    def _apply_udfs(self):
        pass

    def _hw_sync(self):
        pass

    def _apply_stream_status(self):
        pass

    def _apply_preamble_size(self):
        pass

    def _apply_protocol_offset(self):
        pass

    def _apply_special_tag(self):
        if self.packet.specialTag.type is not TGEnums.SpecialTagType.Undefined:
            tag_obj = self.packet.specialTag.tags_dict[self.packet.specialTag.type]
            self.packet.l2_proto = TGEnums.L2_PROTO.PROTOCOL_OFFSET
            self.packet.protocol_offset.value = tag_obj.to_string()

    def _apply_data_integrity(self):
        pass

    def _get_stream_log_title(self):
        title = "UTG.{}.{}()".format(self._name, inspect.stack()[1][3])
        return title

    def _get_stream_log_message(self):
        message = self.__str__()
        args, _, _, values_dict = inspect.getargvalues(inspect.stack()[1][0])
        values_dict_iter = iter((v, k) for k, v in values_dict.items() if not k.startswith('self') and not k.startswith('__'))
        message += "args:\n"
        for val, key in values_dict_iter:
            message += "{}: {}\n".format(key, val)
        return message

    def _update_stream_stats(self, stats):
        pass

    def get_stats(self):
        """
        Get all stream stats from HW and update the statistics's member attributes
        """
        pass

    def clear_stats(self):
        """
        Clear stream stats on HW and on stats object
        :return:
        """
        pass

    def set_from_json(self, path_to_json):
        '''
        Get a path to json file describing the packet and write it to the Packet object
        :param path_to_json: full path to the json file
        :type path_to_json: str
        :return:
        '''
        raise Exception("Not implemented")

    def set_from_scapy(self, scapy_packet):
        '''
        Get a Scapy packet obejct and write it to HW (the packet's structure currently doesn't get write to the Packet object
        :param scapy_packet:
        :return:
        '''
        raise Exception("Not implemented")

    def dict_to_stream(self, input_dict, configure_packet=True):
        Stream._tg_dict_to_stream(input_dict=input_dict, port_obj=self._parent, configure_packet=configure_packet)

    @staticmethod
    def _tg_dict_to_stream(input_dict, port_obj, configure_packet=True):
        dict_streams = input_dict["streams"]

        for stream in dict_streams:
            if stream["name"] not in port_obj.streams:
                raise Exception("stream: {} - not in {}".format(stream["name"], port_obj.streams))
            hw_stream = port_obj.streams[stream["name"]]  # type: Stream
            ### stream rate
            rate_mode = TGEnums.STREAM_RATE_MODE.UTILIZATION
            if Stream._exist_and_not_empty(stream["rate"], "mode"): rate_mode = TGEnums.STREAM_RATE_MODE[
                stream["rate"]["mode"].strip()]
            hw_stream.rate.mode = rate_mode
            if hw_stream.rate.mode == TGEnums.STREAM_RATE_MODE.UTILIZATION:
                if Stream._exist_and_not_empty(stream["rate"], "utilization_value"): hw_stream.rate.utilization_value = \
                stream["rate"]["utilization_value"]
            elif hw_stream.rate.mode == TGEnums.STREAM_RATE_MODE.BITRATE_PER_SECOND:
                if Stream._exist_and_not_empty(stream["rate"], "bitrate_value"): hw_stream.rate.bitrate_value = \
                stream["rate"]["bitrate_value"]
            elif hw_stream.rate.mode == TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND:
                if Stream._exist_and_not_empty(stream["rate"], "pps_value"): hw_stream.rate.pps_value = stream["rate"][
                    "pps_value"]
            elif hw_stream.rate.mode == TGEnums.STREAM_RATE_MODE.INTER_PACKET_GAP:
                if Stream._exist_and_not_empty(stream["rate"], "ipg_value"): hw_stream.rate.ipg_value = stream["rate"][
                    "ipg_value"]

            ### stream frame_size
            f_side_mode = TGEnums.MODIFIER_FRAME_SIZE_MODE.FIXED
            if Stream._exist_and_not_empty(stream["frame_size"], "mode"): f_side_mode = TGEnums.MODIFIER_FRAME_SIZE_MODE[
                stream["frame_size"]["mode"].strip()]
            hw_stream.frame_size.mode = f_side_mode
            if Stream._exist_and_not_empty(stream["frame_size"], "value"): hw_stream.frame_size.value = \
            stream["frame_size"]["value"]
            if Stream._exist_and_not_empty(stream["frame_size"], "min"): hw_stream.frame_size.min = stream["frame_size"][
                "min"]
            if Stream._exist_and_not_empty(stream["frame_size"], "max"): hw_stream.frame_size.max = stream["frame_size"][
                "max"]
            if Stream._exist_and_not_empty(stream["frame_size"], "step"): hw_stream.frame_size.step = \
            stream["frame_size"]["step"]
            if Stream._exist_and_not_empty(stream["frame_size"],
                                          "weight_pairs_list"): hw_stream.frame_size.weight_pairs_list = \
            stream["frame_size"]["weight_pairs_list"]
            if Stream._exist_and_not_empty(stream["frame_size"],
                                          "quad_gaussian_list"): hw_stream.frame_size.quad_gaussian_list = \
            stream["frame_size"]["quad_gaussian_list"]

            ### stream control
            control_mode = TGEnums.STREAM_TRANSMIT_MODE.CONTINUOUS_PACKET
            if Stream._exist_and_not_empty(stream["control"], "mode"): control_mode = TGEnums.STREAM_TRANSMIT_MODE[
                stream["control"]["mode"].strip()]
            hw_stream.control.mode = control_mode
            if Stream._exist_and_not_empty(stream["control"], "return_to_id"): hw_stream.control.return_to_id = \
            stream["control"]["return_to_id"]
            if Stream._exist_and_not_empty(stream["control"], "loop_count"): hw_stream.control.loop_count = \
            stream["control"]["loop_count"]
            if Stream._exist_and_not_empty(stream["control"], "packets_per_burst"): hw_stream.control.packets_per_burst = \
            stream["control"]["packets_per_burst"]
            if Stream._exist_and_not_empty(stream["control"], "bursts_per_stream"): hw_stream.control.bursts_per_stream = \
            stream["control"]["bursts_per_stream"]

            ### packet
            if configure_packet:
                Stream._tg_dict_to_packet(input_dict, port_obj)

        port_obj.apply()

    @staticmethod
    def _tg_dict_to_packet(input_dict, port_obj):
        dict_streams = input_dict["streams"]

        for stream in dict_streams:
            if stream["name"] not in port_obj.streams:
                raise Exception("stream: {} - not in {}".format(stream["name"], port_obj.streams))
            if Stream._exist_and_not_empty(stream, "packet"):
                hw_packet = port_obj.streams[stream["name"]].packet  # type: Packet
            else:
                break
            ### mac
            packet = stream["packet"]
            if Stream._exist_and_not_empty(packet, "mac"):
                if Stream._exist_and_not_empty(packet["mac"], "da"):
                    mac_da_mode = TGEnums.MODIFIER_MAC_MODE.FIXED
                    if Stream._exist_and_not_empty(packet["mac"]["da"], "mode"):
                        mac_da_mode = TGEnums.MODIFIER_MAC_MODE[packet["mac"]["da"]["mode"]]
                    hw_packet.mac.da.mode = mac_da_mode
                    if Stream._exist_and_not_empty(packet["mac"]["da"], "value"): hw_packet.mac.da.value = \
                    packet["mac"]["da"]["value"]
                    if Stream._exist_and_not_empty(packet["mac"]["da"], "count"): hw_packet.mac.da.count = \
                    packet["mac"]["da"]["count"]
                    if Stream._exist_and_not_empty(packet["mac"]["da"], "step"): hw_packet.mac.da.step = \
                    packet["mac"]["da"]["step"]
                    if Stream._exist_and_not_empty(packet["mac"]["da"], "mask"): hw_packet.mac.da.mask = \
                    packet["mac"]["da"]["mask"]
                if Stream._exist_and_not_empty(packet["mac"], "sa"):
                    mac_sa_mode = TGEnums.MODIFIER_MAC_MODE.FIXED
                    if Stream._exist_and_not_empty(packet["mac"]["sa"], "mode"):
                        mac_sa_mode = TGEnums.MODIFIER_MAC_MODE[packet["mac"]["sa"]["mode"]]
                    hw_packet.mac.sa.mode = mac_sa_mode
                    if Stream._exist_and_not_empty(packet["mac"]["sa"], "value"): hw_packet.mac.sa.value = \
                    packet["mac"]["sa"]["value"]
                    if Stream._exist_and_not_empty(packet["mac"]["sa"], "count"): hw_packet.mac.sa.count = \
                    packet["mac"]["sa"]["count"]
                    if Stream._exist_and_not_empty(packet["mac"]["sa"], "step"): hw_packet.mac.sa.step = \
                    packet["mac"]["sa"]["step"]
                    if Stream._exist_and_not_empty(packet["mac"]["sa"], "mask"): hw_packet.mac.sa.mask = \
                    packet["mac"]["sa"]["mask"]

                fcs_mode = TGEnums.FCS_ERRORS_MODE.NO_ERROR
                if Stream._exist_and_not_empty(packet["mac"], "fcs"):
                    fcs_mode = TGEnums.FCS_ERRORS_MODE[packet["mac"]["fcs"]]
                    hw_packet.mac.fcs = fcs_mode

            ### l2_proto
            l2_proto_mode = TGEnums.L2_PROTO.ETHERNETII
            if Stream._exist_and_not_empty(packet, "l2_proto"):
                l2_proto_mode = TGEnums.L2_PROTO[packet["l2_proto"]]
                hw_packet.l2_proto = l2_proto_mode

            ### vlans
            if Stream._exist_and_not_empty(packet, "vlans"):
                for vidx, vlan in enumerate(packet["vlans"]):
                    vlan_name = "vlan_{}".format(vidx)
                    if Stream._exist_and_not_empty(vlan, "name"):
                        vlan_name = vlan["name"]
                    hw_packet.add_vlan(vlan_name)
                    if Stream._exist_and_not_empty(vlan["vid"], "value"):
                        hw_packet.vlans[vlan_name].vid.value = vlan["vid"]["value"]
                    if Stream._exist_and_not_empty(vlan["vid"], "count"):
                        hw_packet.vlans[vlan_name].vid.count = vlan["vid"]["count"]
                    vid_mode = TGEnums.MODIFIER_VLAN_MODE.FIXED
                    if Stream._exist_and_not_empty(vlan["vid"], "mode"):
                        vid_mode = TGEnums.MODIFIER_VLAN_MODE[vlan["vid"]["mode"]]
                        hw_packet.vlans[vlan_name].vid.mode = vid_mode
                    if Stream._exist_and_not_empty(vlan, "cfi"):
                        hw_packet.vlans[vlan_name].cfi = vlan["cfi"]
                    if Stream._exist_and_not_empty(vlan, "priority"):
                        hw_packet.vlans[vlan_name].priority = vlan["priority"]
                    if Stream._exist_and_not_empty(vlan, "proto"):
                        hw_packet.vlans[vlan_name].proto = vlan["proto"]

            ### ipv4
            if Stream._exist_and_not_empty(packet, "ipv4"):
                if Stream._exist_and_not_empty(packet["ipv4"], "dscp_decimal_value"):
                    hw_packet.ipv4.dscp_decimal_value = packet["ipv4"]["dscp_decimal_value"]
                if Stream._exist_and_not_empty(packet["ipv4"], "identifier"):
                    hw_packet.ipv4.identifier = packet["ipv4"]["identifier"]
                if Stream._exist_and_not_empty(packet["ipv4"], "ttl"):
                    hw_packet.ipv4.ttl = packet["ipv4"]["ttl"]
                if Stream._exist_and_not_empty(packet["ipv4"], "protocol"):
                    hw_packet.ipv4.protocol = packet["ipv4"]["protocol"]
                checksum_mode_ipv4 = TGEnums.CHECKSUM_MODE.VALID
                if Stream._exist_and_not_empty(packet["ipv4"], "checksum_mode"):
                    checksum_mode_ipv4 = TGEnums.CHECKSUM_MODE[packet["ipv4"]["checksum_mode"]]
                    hw_packet.ipv4.checksum_mode = checksum_mode_ipv4
                if Stream._exist_and_not_empty(packet["ipv4"], "checksum_override"):
                    hw_packet.ipv4.custom_checksum = packet["ipv4"]["checksum_override"]
                if Stream._exist_and_not_empty(packet["ipv4"], "fragment_offset_decimal_value"):
                    hw_packet.ipv4.fragment_offset_decimal_value = packet["ipv4"]["fragment_offset_decimal_value"]
                if Stream._exist_and_not_empty(packet["ipv4"], "length_override"):
                    ipv4_length_override = False
                    if "true" in str(packet["ipv4"]["length_override"]).lower():
                        ipv4_length_override = True
                    hw_packet.ipv4.length_override = ipv4_length_override
                    if Stream._exist_and_not_empty(packet["ipv4"], "length_value"):
                        hw_packet.ipv4.length_value = packet["ipv4"]["length_value"]
                if Stream._exist_and_not_empty(packet["ipv4"], "options_padding"):
                    hw_packet.ipv4.options_padding = packet["ipv4"]["options_padding"]

                if Stream._exist_and_not_empty(packet["ipv4"], "source_ip"):
                    if Stream._exist_and_not_empty(packet["ipv4"]["source_ip"], "value"):
                        hw_packet.ipv4.source_ip.value = packet["ipv4"]["source_ip"]["value"]
                    if Stream._exist_and_not_empty(packet["ipv4"]["source_ip"], "count"):
                        hw_packet.ipv4.source_ip.count = packet["ipv4"]["source_ip"]["count"]
                    if Stream._exist_and_not_empty(packet["ipv4"]["source_ip"], "step"):
                        hw_packet.ipv4.source_ip.step = packet["ipv4"]["source_ip"]["step"]
                    if Stream._exist_and_not_empty(packet["ipv4"]["source_ip"], "mask"):
                        hw_packet.ipv4.source_ip.mask = packet["ipv4"]["source_ip"]["mask"]
                    sip_mode = TGEnums.MODIFIER_IPV4_ADDRESS_MODE.FIXED
                    if Stream._exist_and_not_empty(packet["ipv4"]["source_ip"], "mode"):
                        sip_mode = TGEnums.MODIFIER_IPV4_ADDRESS_MODE[packet["ipv4"]["source_ip"]["mode"]]
                        hw_packet.ipv4.source_ip.mode = sip_mode
                if Stream._exist_and_not_empty(packet["ipv4"], "destination_ip"):
                    if Stream._exist_and_not_empty(packet["ipv4"]["destination_ip"], "value"):
                        hw_packet.ipv4.destination_ip.value = packet["ipv4"]["destination_ip"]["value"]
                    if Stream._exist_and_not_empty(packet["ipv4"]["destination_ip"], "count"):
                        hw_packet.ipv4.destination_ip.count = packet["ipv4"]["destination_ip"]["count"]
                    if Stream._exist_and_not_empty(packet["ipv4"]["destination_ip"], "step"):
                        hw_packet.ipv4.destination_ip.step = packet["ipv4"]["destination_ip"]["step"]
                    if Stream._exist_and_not_empty(packet["ipv4"]["destination_ip"], "mask"):
                        hw_packet.ipv4.destination_ip.mask = packet["ipv4"]["destination_ip"]["mask"]
                    dip_mode = TGEnums.MODIFIER_IPV4_ADDRESS_MODE.FIXED
                    if Stream._exist_and_not_empty(packet["ipv4"]["destination_ip"], "mode"):
                        dip_mode = TGEnums.MODIFIER_IPV4_ADDRESS_MODE[packet["ipv4"]["destination_ip"]["mode"]]
                        hw_packet.ipv4.destination_ip.mode = dip_mode

                if Stream._exist_and_not_empty(packet["ipv4"], "fragment_enable"):
                    ipv4_fragment_enable = False
                    if "true" in str(packet["ipv4"]["fragment_enable"]).lower():
                        ipv4_fragment_enable = True
                    hw_packet.ipv4.fragment_enable = ipv4_fragment_enable
                if Stream._exist_and_not_empty(packet["ipv4"], "fragment_last_enable"):
                    ipv4_fragment_last_enable = True
                    if "false" in str(packet["ipv4"]["fragment_last_enable"]).lower():
                        ipv4_fragment_last_enable = False
                    hw_packet.ipv4.fragment_last_enable = ipv4_fragment_last_enable
                if Stream._exist_and_not_empty(packet["ipv4"], "enable_header_len_override"):
                    ipv4_enable_header_len_override = False
                    if "true" in str(packet["ipv4"]["enable_header_len_override"]).lower():
                        ipv4_enable_header_len_override = True
                    hw_packet.ipv4.enable_header_len_override = ipv4_enable_header_len_override
                if Stream._exist_and_not_empty(packet["ipv4"], "header_len_override_value"):
                    hw_packet.ipv4.header_len_override_value = int(packet["ipv4"]["header_len_override_value"])

            ### ipv6
            if Stream._exist_and_not_empty(packet, "ipv6"):
                if Stream._exist_and_not_empty(packet["ipv6"], "traffic_class"):
                    hw_packet.ipv6.traffic_class = packet["ipv6"]["traffic_class"]
                if Stream._exist_and_not_empty(packet["ipv6"], "flow_label"):
                    hw_packet.ipv6.flow_label = packet["ipv6"]["flow_label"]
                if Stream._exist_and_not_empty(packet["ipv6"], "hop_limit"):
                    hw_packet.ipv6.hop_limit = packet["ipv6"]["hop_limit"]
                if Stream._exist_and_not_empty(packet["ipv6"], "next_header"):
                    hw_packet.ipv6.next_header = packet["ipv6"]["next_header"]
                if Stream._exist_and_not_empty(packet["ipv6"], "source_ip"):
                    if Stream._exist_and_not_empty(packet["ipv6"]["source_ip"], "value"):
                        hw_packet.ipv6.source_ip.value = packet["ipv6"]["source_ip"]["value"]
                    if Stream._exist_and_not_empty(packet["ipv6"]["source_ip"], "count"):
                        hw_packet.ipv6.source_ip.count = packet["ipv6"]["source_ip"]["count"]
                    if Stream._exist_and_not_empty(packet["ipv6"]["source_ip"], "step"):
                        hw_packet.ipv6.source_ip.step = packet["ipv6"]["source_ip"]["step"]
                    if Stream._exist_and_not_empty(packet["ipv6"]["source_ip"], "mask"):
                        hw_packet.ipv6.source_ip.mask = packet["ipv6"]["source_ip"]["mask"]
                    sip_mode_ip6 = TGEnums.MODIFIER_IPV6_ADDRESS_MODE.FIXED
                    if Stream._exist_and_not_empty(packet["ipv6"]["source_ip"], "mode"):
                        sip_mode_ip6 = TGEnums.MODIFIER_IPV6_ADDRESS_MODE[packet["ipv6"]["source_ip"]["mode"]]
                        hw_packet.ipv6.source_ip.mode = sip_mode_ip6
                if Stream._exist_and_not_empty(packet["ipv6"], "destination_ip"):
                    if Stream._exist_and_not_empty(packet["ipv6"]["destination_ip"], "value"):
                        hw_packet.ipv6.destination_ip.value = packet["ipv6"]["destination_ip"]["value"]
                    if Stream._exist_and_not_empty(packet["ipv6"]["destination_ip"], "count"):
                        hw_packet.ipv6.destination_ip.count = packet["ipv6"]["destination_ip"]["count"]
                    if Stream._exist_and_not_empty(packet["ipv6"]["destination_ip"], "step"):
                        hw_packet.ipv6.destination_ip.step = packet["ipv6"]["destination_ip"]["step"]
                    if Stream._exist_and_not_empty(packet["ipv6"]["destination_ip"], "mask"):
                        hw_packet.ipv6.destination_ip.mask = packet["ipv6"]["destination_ip"]["mask"]
                    dip_mode_ipv6 = TGEnums.MODIFIER_IPV6_ADDRESS_MODE.FIXED
                    if Stream._exist_and_not_empty(packet["ipv6"]["destination_ip"], "mode"):
                        dip_mode_ipv6 = TGEnums.MODIFIER_IPV6_ADDRESS_MODE[packet["ipv6"]["destination_ip"]["mode"]]
                        hw_packet.ipv6.destination_ip.mode = dip_mode_ipv6

                if Stream._exist_and_not_empty(packet["ipv4"], "fragment_enable"):
                    ipv4_fragment_enable = False
                    if "true" in str(packet["ipv4"]["fragment_enable"]).lower():
                        ipv4_fragment_enable = True
                    hw_packet.ipv4.fragment_enable = ipv4_fragment_enable
                if Stream._exist_and_not_empty(packet["ipv4"], "fragment_last_enable"):
                    ipv4_fragment_last_enable = True
                    if "false" in str(packet["ipv4"]["fragment_last_enable"]).lower():
                        ipv4_fragment_last_enable = False
                    hw_packet.ipv4.fragment_last_enable = ipv4_fragment_last_enable
                if Stream._exist_and_not_empty(packet["ipv4"], "enable_header_len_override"):
                    ipv4_enable_header_len_override = False
                    if "true" in str(packet["ipv4"]["enable_header_len_override"]).lower():
                        ipv4_enable_header_len_override = True
                    hw_packet.ipv4.enable_header_len_override = ipv4_enable_header_len_override
                if Stream._exist_and_not_empty(packet["ipv4"], "header_len_override_value"):
                    hw_packet.ipv4.header_len_override_value = int(packet["ipv4"]["header_len_override_value"])

            ### TCP
            if Stream._exist_and_not_empty(packet, "tcp"):
                if Stream._exist_and_not_empty(packet["tcp"], "source_port"):
                    hw_packet.tcp.source_port.value = packet["tcp"]["source_port"]
                if Stream._exist_and_not_empty(packet["tcp"], "destination_port"):
                    hw_packet.tcp.destination_port.value = packet["tcp"]["destination_port"]
                checksum_mode_tcp = TGEnums.CHECKSUM_MODE.VALID
                if Stream._exist_and_not_empty(packet["tcp"], "checksum_mode"):
                    checksum_mode_tcp = TGEnums.CHECKSUM_MODE[packet["tcp"]["checksum_mode"]]
                    hw_packet.tcp.valid_checksum = checksum_mode_tcp
                if Stream._exist_and_not_empty(packet["tcp"], "checksum_override"):
                    hw_packet.tcp.custom_checksum = packet["tcp"]["checksum_override"]
                if Stream._exist_and_not_empty(packet["tcp"], "sequence_number"):
                    hw_packet.tcp.sequence_number = packet["tcp"]["sequence_number"]
                if Stream._exist_and_not_empty(packet["tcp"], "acknowledgement_number"):
                    hw_packet.tcp.acknowledgement_number = packet["tcp"]["acknowledgement_number"]
                if Stream._exist_and_not_empty(packet["tcp"], "window"):
                    hw_packet.tcp.window = packet["tcp"]["window"]
                if Stream._exist_and_not_empty(packet["tcp"], "urgent_pointer"):
                    hw_packet.tcp.urgent_pointer = packet["tcp"]["urgent_pointer"]
                if Stream._exist_and_not_empty(packet["tcp"], "header_length"):
                    hw_packet.tcp.header_length = packet["tcp"]["header_length"]

                if Stream._exist_and_not_empty(packet["tcp"], "flag_no_more_data_from_sender"):
                    tcp_flag_no_more_data_from_sender = False
                    if "true" in str(packet["tcp"]["flag_no_more_data_from_sender"]).lower():
                        tcp_flag_no_more_data_from_sender = True
                        hw_packet.tcp.flag_no_more_data_from_sender = tcp_flag_no_more_data_from_sender

                if Stream._exist_and_not_empty(packet["tcp"], "flag_acknowledge_valid"):
                    tcp_flag_acknowledge_valid = False
                    if "true" in str(packet["tcp"]["flag_acknowledge_valid"]).lower():
                        tcp_flag_acknowledge_valid = True
                        hw_packet.tcp.flag_acknowledge_valid = tcp_flag_acknowledge_valid

                if Stream._exist_and_not_empty(packet["tcp"], "flag_push_function"):
                    tcp_flag_push_function = False
                    if "true" in str(packet["tcp"]["flag_push_function"]).lower():
                        tcp_flag_push_function = True
                        hw_packet.tcp.flag_push_function = tcp_flag_push_function

                if Stream._exist_and_not_empty(packet["tcp"], "flag_reset_connection"):
                    tcp_flag_reset_connection = False
                    if "true" in str(packet["tcp"]["flag_reset_connection"]).lower():
                        tcp_flag_reset_connection = True
                        hw_packet.tcp.flag_reset_connection = tcp_flag_reset_connection

                if Stream._exist_and_not_empty(packet["tcp"], "flag_synchronize_sequence"):
                    tcp_flag_synchronize_sequence = False
                    if "true" in str(packet["tcp"]["flag_synchronize_sequence"]).lower():
                        tcp_flag_synchronize_sequence = True
                        hw_packet.tcp.flag_synchronize_sequence = tcp_flag_synchronize_sequence

                if Stream._exist_and_not_empty(packet["tcp"], "flag_urgent_pointer_valid"):
                    tcp_flag_urgent_pointer_valid = False
                    if "true" in str(packet["tcp"]["flag_urgent_pointer_valid"]).lower():
                        tcp_flag_urgent_pointer_valid = True
                        hw_packet.tcp.flag_urgent_pointer_valid = tcp_flag_urgent_pointer_valid

            ### UDP
            if Stream._exist_and_not_empty(packet, "udp"):
                if Stream._exist_and_not_empty(packet["udp"], "source_port"):
                    hw_packet.udp.source_port.value = packet["udp"]["source_port"]
                if Stream._exist_and_not_empty(packet["udp"], "destination_port"):
                    hw_packet.udp.destination_port.value = packet["udp"]["destination_port"]
                checksum_mode_udp = TGEnums.CHECKSUM_MODE.VALID
                if Stream._exist_and_not_empty(packet["udp"], "checksum_mode"):
                    checksum_mode_udp = TGEnums.CHECKSUM_MODE[packet["udp"]["checksum_mode"]]
                    hw_packet.udp.valid_checksum = checksum_mode_udp
                if Stream._exist_and_not_empty(packet["udp"], "checksum_override"):
                    hw_packet.udp.custom_checksum = packet["tcp"]["checksum_override"]
                if Stream._exist_and_not_empty(packet["udp"], "length_override"):
                    udp_length_override = False
                    if "true" in str(packet["udp"]["length_override"]).lower():
                        udp_length_override = True
                        hw_packet.udp.length_override = udp_length_override
                if Stream._exist_and_not_empty(packet["udp"], "custom_length"):
                    hw_packet.udp.custom_length = packet["udp"]["custom_length"]

            ### DATA PATTERN
            if Stream._exist_and_not_empty(packet, "data_pattern"):
                if Stream._exist_and_not_empty(packet["data_pattern"], "value"):
                    hw_packet.data_pattern.value = packet["data_pattern"]["value"]
                data_pattern_type = TGEnums.DATA_PATTERN_TYPE.FIXED
                if Stream._exist_and_not_empty(packet["data_pattern"], "type"):
                    data_pattern_type = TGEnums.DATA_PATTERN_TYPE[packet["data_pattern"]["type"]]
                hw_packet.data_pattern.type = data_pattern_type

            ### Protocol offset
            if Stream._exist_and_not_empty(packet, "protocol_offset"):
                if Stream._exist_and_not_empty(packet["protocol_offset"], "offset"):
                    hw_packet.protocol_offset.offset = packet["protocol_offset"]["offset"]
                if Stream._exist_and_not_empty(packet["protocol_offset"], "value"):
                    hw_packet.protocol_offset.value = packet["protocol_offset"]["value"]

            ### Preamble size
            if Stream._exist_and_not_empty(packet, "preamble_size"):
                hw_packet.preamble_size = packet["preamble_size"]

            l3_proto_mode = TGEnums.L3_PROTO.NONE
            if Stream._exist_and_not_empty(packet, "l3_proto"):
                l3_proto_mode = TGEnums.L3_PROTO[packet["l3_proto"]]
                hw_packet.l3_proto = l3_proto_mode

            l4_proto_mode = TGEnums.L4_PROTO.NONE
            if Stream._exist_and_not_empty(packet, "l4_proto"):
                l4_proto_mode = TGEnums.L4_PROTO[packet["l4_proto"]]
                hw_packet.l4_proto = l4_proto_mode

    @staticmethod
    def _exist_and_not_empty(dict_obj, key):
        if key in dict_obj:
            if dict_obj[key] != "":
                return True
        else:
            return False
        return False

class Source_Interface(object):
    def __init__(self):
        self._enabled = attrWithDefault(False)
        self._description_key = attrWithDefault('""')

    @property
    def enabled(self):
        return self._enabled.current_val

    @enabled.setter
    def enabled(self, v):
        self._enabled.current_val = v

    @property
    def description_key(self):
        return self._description_key.current_val

    @description_key.setter
    def description_key(self, v):
        self._description_key.current_val = v


class _packet_group(object):
    def __init__(self):
        self._group_id = attrWithDefault(1)
        self._enable_group_id = attrWithDefault(None)

    @property
    def group_id(self):
        return self._group_id.current_val

    @group_id.setter
    def group_id(self,v):
        self._group_id.current_val = v

    @property
    def enable_group_id(self):
        return self._enable_group_id.current_val

    @enable_group_id.setter
    def enable_group_id(self,v):
        self._enable_group_id.current_val = v


class _INSTRUMENTATION(object):
    def __init__(self):
        self._automatic_enabled = attrWithDefault(False)
        self._time_stamp_enabled = attrWithDefault(False)
        self._packet_groups_enabled = attrWithDefault(False)
        self._sequence_checking_enabled = attrWithDefault(False)
        self.packet_group = _packet_group()


    @property
    def automatic_enabled(self):
        return self._automatic_enabled.current_val

    @automatic_enabled.setter
    def automatic_enabled(self, v):
        self._automatic_enabled.current_val = v

    @property
    def time_stamp_enabled(self):
        return self._time_stamp_enabled.current_val

    @time_stamp_enabled.setter
    def time_stamp_enabled(self, v):
        self._time_stamp_enabled.current_val = v

    @property
    def packet_grouops_enabled(self):
        return self._packet_groups_enabled.current_val

    @packet_grouops_enabled.setter
    def packet_grouops_enabled(self, v):
        self._packet_groups_enabled.current_val = v

    @property
    def sequence_checking_enabled(self):
        return self._sequence_checking_enabled.current_val

    @sequence_checking_enabled.setter
    def sequence_checking_enabled(self, v):
        self._sequence_checking_enabled.current_val = v




class _RATE_CONTROL(object):
    def __init__(self):
        self._mode = attrWithDefault(TGEnums.STREAM_RATE_MODE.UTILIZATION)
        self._utilization_value = attrWithDefault(100)
        self._bitrate_value = attrWithDefault("100")
        self._pps_value = attrWithDefault("100")
        self._ipg_value = attrWithDefault("96.0")
        self._inter_packet_gap_mode = attrWithDefault(TGEnums.STREAM_RATE_INTER_PACKET_GAP_MODE.NANOSECONDS)
        self._inter_packet_gap_value = attrWithDefault("")
        self._inter_packet_gap_enforce_min_value = attrWithDefault("")



    def __iter__(self):
        return iter([attr for attr in dir(self) if attr[:2] != "__"])

    def __str__(self):
        str_delimit = ", "
        temp_str = "MODE[{1}]{0}UTILIZATION_VALUE[{2}]{0}BITRATE_VALUE[{3}]{0}PPS_VALUE[{4}]{0}IPG_VALUE[{5}]{0}INTER_PACKET_GAP_VALUE[{6}]{0}INTER_PACKET_GAP_MODE[{7}]{0}INTER_PACKET_GAP_ENFORCE_MIN_VAL[{8}]".format(
            str_delimit,
            self.mode,
            self.utilization_value,
            self.bitrate_value,
            self.pps_value,
            self.ipg_value,
            self.inter_packet_gap_mode,
            self.inter_packet_gap_value,
            self.inter_packet_gap_enforce_min_value
        )

        return temp_str

    @property
    def mode(self):
        """mode : """
        return self._mode.current_val

    @mode.setter
    def mode(self, v):
        """TGEnums.STREAM_RATE_MODE"""
        self._mode.current_val = v

    @property
    def utilization_value(self):
        """utilization_value : """
        return str(self._utilization_value.current_val)

    @utilization_value.setter
    def utilization_value(self, v):
        """utilization_value : """
        self._utilization_value.current_val = v

    @property
    def pps_value(self):
        """pps_value : """
        return self._pps_value.current_val

    @pps_value.setter
    def pps_value(self, v):
        """pps_value : """
        self._pps_value.current_val = v

    @property
    def bitrate_value(self):
        """bitrate_value : """
        return self._bitrate_value.current_val

    @bitrate_value.setter
    def bitrate_value(self, v):
        """bitrate_value : """
        self._bitrate_value.current_val = v

    @property
    def ipg_value(self):
        """ipg_value : """
        return self._ipg_value.current_val

    @ipg_value.setter
    def ipg_value(self, v):
        """ipg_value : """
        self._ipg_value.current_val = v

    @property
    def inter_packet_gap_mode(self):
        """inter_packet_gap_mode : """
        return self._inter_packet_gap_mode.current_val

    @inter_packet_gap_mode.setter
    def inter_packet_gap_mode(self, v):
        """inter_packet_gap_mode : """
        self._inter_packet_gap_mode.current_val = v

    @property
    def inter_packet_gap_value(self):
        """inter_packet_gap_value : """
        return self._inter_packet_gap_value.current_val

    @inter_packet_gap_value.setter
    def inter_packet_gap_value(self, v):
        """inter_packet_gap_value : """
        self._inter_packet_gap_value.current_val = v

    @property
    def inter_packet_gap_enforce_min_value(self):
        """inter_packet_gap_enforce_min_value : """
        return self._inter_packet_gap_enforce_min_value.current_val

    @inter_packet_gap_enforce_min_value.setter
    def inter_packet_gap_enforce_min_value(self, v):
        """inter_packet_gap_enforce_min_value : """
        self._inter_packet_gap_enforce_min_value.current_val = v

class _FRAME_SIZE(object):
    def __init__(self,parent):
        self._value = attrWithDefault("64")
        self._min = attrWithDefault("64")
        self._max = attrWithDefault("64")
        self._step = attrWithDefault("1")
        self._mode = attrWithDefault(TGEnums.MODIFIER_FRAME_SIZE_MODE.FIXED)
        self._weight_pairs_list = attrWithDefault(["64,1"])
        self._quad_gaussian_list = attrWithDefault(["200.00,100.00,1",
                                                    "200.00,100.00,0",
                                                    "200.00,100.00,0",
                                                    "200.00,100.00,0"])
        self._parent = parent

    def __iter__(self):
        return iter([attr for attr in dir(self) if attr[:2] != "__"])

    def __str__(self):
        str_delimit = ", "
        temp_str = "SIZE[{1}]{0}MODE[{2}]{0}MIN[{3}]{0}MAX[{4}]{0}STEP[{5}]\n\tWEIGHT_PAIRS_LIST[{6}]\n\tQUAD_GAUSSIAN_LIST[{7}]".format(
            str_delimit,
            self.value,
            self.mode,
            self.min,
            self.max,
            self.step,
            self.weight_pairs_list,
            self.quad_gaussian_list,
        )

        return temp_str

    @property
    def value(self):
        """value : """
        return self._value.current_val

    @value.setter
    def value(self, v):
        """value : """
        self._parent.packet.size = v
        self._value._current_val = v

    @property
    def min(self):
        """min : """
        return self._min.current_val

    @min.setter
    def min(self, v):
        """min : """
        self._min._current_val = v

    @property
    def max(self):
        """max : """
        return self._max.current_val

    @max.setter
    def max(self, v):
        """max : """
        self._max._current_val = v

    @property
    def step(self):
        """step : """
        return self._step.current_val

    @step.setter
    def step(self, v):
        """step : """
        self._step._current_val = v

    @property
    def mode(self):
        """mode : """
        return self._mode.current_val

    @mode.setter
    def mode(self, v):
        """mode : """
        self._mode._current_val = v

    @property
    def weight_pairs_list(self):
        """weight_pairs_list : """
        return self._weight_pairs_list.current_val

    @weight_pairs_list.setter
    def weight_pairs_list(self, v):
        """weight_pairs_list : """
        if type(v) != list:
            v = [v]
        self._weight_pairs_list._current_val = v

    @property
    def quad_gaussian_list(self):
        """quad_gaussian_list : """
        return self._quad_gaussian_list.current_val

    @quad_gaussian_list.setter
    def quad_gaussian_list(self, v):
        """quad_gaussian_list : """
        if type(v) != list:
            v = [v]
        self._quad_gaussian_list._current_val = v

class _STREAM_CONTROL(object):
    def __init__(self):
        self._mode = attrWithDefault(TGEnums.STREAM_TRANSMIT_MODE.CONTINUOUS_PACKET) #type: TGEnums.STREAM_TRANSMIT_MODE
        self._return_to_id = attrWithDefault("1")
        self._loop_count = attrWithDefault("1")
        self._packets_per_burst = attrWithDefault("100")
        self._bursts_per_stream = attrWithDefault("1")
        self._inter_burst_gap_enable = attrWithDefault(False)
        self._inter_burst_gap_value = attrWithDefault("9600")
        self._inter_burst_gap_unit = attrWithDefault(TGEnums.STREAM_INTER_BURST_GAP_UNIT.BYTES)
        self._inter_stream_gap_enable = attrWithDefault(False)
        self._inter_stream_gap_value = attrWithDefault("9600")
        self._inter_stream_gap_unit = attrWithDefault(TGEnums.STREAM_INTER_STREAM_GAP_UNIT.BYTES)
        self._start_tx_delay = attrWithDefault("0.0")
        self._start_tx_delay_unit = attrWithDefault(TGEnums.STREAM_START_TX_DELAY_UNIT.BYTES)
        self._pfc_queue = attrWithDefault(0)

    def __iter__(self):
        return iter([attr for attr in dir(self) if attr[:2] != "__"])

    def __str__(self):
        str_delimit = ", "
        temp_str = "MODE[{1}]{0}RETURN_TO_ID[{2}]{0}LOOP_CCOUNT[{3}]{0}PACKETS_PER_BURST[{4}]{0}BURSTS_PER_STREAM[{5}]" \
                   "\n\tINTER_BURST_GAP[enable={6}, value={7}, unit={8}]" \
                   "\n\tINTER_STREAM_GAP[enable={9}, value={10}, unit={11}]" \
                   "\nSTART_TX_DELAY[{12}]{0}START_TX_DELAY_UNIT[{13}]{0}PFC_QUEUE[{14}]".format(
            str_delimit,
            self.mode,
            self.return_to_id,
            self.loop_count,
            self.packets_per_burst,
            self.bursts_per_stream,
            self.inter_burst_gap_enable,
            self.inter_burst_gap_value,
            self.inter_burst_gap_unit,
            self.inter_stream_gap_enable,
            self.inter_stream_gap_value,
            self.inter_stream_gap_unit,
            self.start_tx_delay,
            self.start_tx_delay_unit,
            self.pfc_queue
        )

        return temp_str

    @property
    def mode(self):
        """
        :type : TGEnums.STREAM_TRANSMIT_MODE
        """
        return self._mode.current_val

    @mode.setter
    def mode(self, v ):
        """
        :param v: TGEnums.STREAM_TRANSMIT_MODE
        :type v : TGEnums.STREAM_TRANSMIT_MODE
        """
        self._mode._current_val = v

    @property
    def return_to_id(self):
        """return_to_id : idx in case of IXIA, stream name in case of Trex"""
        return self._return_to_id.current_val

    @return_to_id.setter
    def return_to_id(self, v):
        """return_to_id : """
        self._return_to_id._current_val = v

    @property
    def loop_count(self):
        """loop_count : """
        return self._loop_count.current_val

    @loop_count.setter
    def loop_count(self, v):
        """loop_count : """
        self._loop_count._current_val = v

    @property
    def packets_per_burst(self):
        """packets_per_burst : """
        return self._packets_per_burst.current_val

    @packets_per_burst.setter
    def packets_per_burst(self, v):
        """packets_per_burst : """
        self._packets_per_burst._current_val = v

    @property
    def bursts_per_stream(self):
        """bursts_per_stream : """
        return self._bursts_per_stream.current_val

    @bursts_per_stream.setter
    def bursts_per_stream(self, v):
        """bursts_per_stream : """
        self._bursts_per_stream._current_val = v

    @property
    def inter_burst_gap_enable(self):
        """inter_burst_gap_enable : """
        return self._inter_burst_gap_enable.current_val

    @inter_burst_gap_enable.setter
    def inter_burst_gap_enable(self, v):
        """inter_burst_gap_enable : """
        self._inter_burst_gap_enable._current_val = v

    @property
    def inter_burst_gap_value(self):
        """inter_burst_gap_value : """
        return self._inter_burst_gap_value.current_val

    @inter_burst_gap_value.setter
    def inter_burst_gap_value(self, v):
        """inter_burst_gap_value : """
        self._inter_burst_gap_value._current_val = v

    @property
    def inter_burst_gap_unit(self):
        """:rtype : TGEnums.STREAM_INTER_BURST_GAP_UNIT"""
        return self._inter_burst_gap_unit.current_val

    @inter_burst_gap_unit.setter
    def inter_burst_gap_unit(self, v):
        """:type : TGEnums.STREAM_INTER_BURST_GAP_UNIT"""
        self._inter_burst_gap_unit._current_val = v

    @property
    def inter_stream_gap_enable(self):
        """inter_stream_gap_enable : """
        return self._inter_stream_gap_enable.current_val

    @inter_stream_gap_enable.setter
    def inter_stream_gap_enable(self, v):
        """inter_stream_gap_enable : """
        self._inter_stream_gap_enable._current_val = v

    @property
    def inter_stream_gap_value(self):
        """inter_stream_gap_value : """
        return self._inter_stream_gap_value.current_val

    @inter_stream_gap_value.setter
    def inter_stream_gap_value(self, v):
        """inter_stream_gap_value : """
        self._inter_stream_gap_value._current_val = v

    @property
    def inter_stream_gap_unit(self):
        """:rtype : TGEnums.STREAM_INTER_STREAM_GAP_UNIT"""
        return self._inter_stream_gap_unit.current_val

    @inter_stream_gap_unit.setter
    def inter_stream_gap_unit(self, v):
        """:type : STREAM_INTER_STREAM_GAP_UNIT"""
        self._inter_stream_gap_unit._current_val = v

    @property
    def start_tx_delay(self):
        """:rtype : str"""
        return self._start_tx_delay.current_val

    @start_tx_delay.setter
    def start_tx_delay(self, v):
        """:type : str"""
        self._start_tx_delay._current_val = v

    @property
    def start_tx_delay_unit(self):
        """:rtype : str"""
        return self._start_tx_delay_unit.current_val

    @start_tx_delay_unit.setter
    def start_tx_delay_unit(self, v):
        """:type : str"""
        self._start_tx_delay_unit._current_val = v

    @property
    def pfc_queue(self):
        """:rtype : int"""
        return self._pfc_queue.current_val

    @pfc_queue.setter
    def pfc_queue(self, v):
        """:type : int"""
        self._pfc_queue._current_val = v

class _RX_PORT_STATS(object):
    def __init__(self):
        self._stats_type = str
        self._average_latency = _stat_member()
        self._big_sequence_error = _stat_member()
        self._bit_rate = _stat_member()
        self._byte_rate = _stat_member()
        self._duplicate_frames = _stat_member()
        self._first_time_stamp = _stat_member()
        self._frame_rate = _stat_member()
        self._last_time_stamp = _stat_member()
        self._max_delay_variation = _stat_member()
        self._max_latency = _stat_member()
        self._max_min_delay_variation = _stat_member()
        self._maxmin_interval = _stat_member()
        self._min_delay_variation = _stat_member()
        self._min_latency = _stat_member()
        self._num_groups = _stat_member()
        self._prbs_ber_ratio = _stat_member()
        self._prbs_bits_received = _stat_member()
        self._prbs_errored_bits = _stat_member()
        self._read_time_stamp = _stat_member()
        self._reverse_sequence_error = _stat_member()
        self._sequence_gaps = _stat_member()
        self._small_sequence_error = _stat_member()
        self._standard_deviation = _stat_member()
        self._total_byte_count = _stat_member()
        self._total_frames = _stat_member()
        self._total_sequence_error = _stat_member()

    @property
    def average_latency(self):
        return self._average_latency.value

    @average_latency.setter
    def average_latency(self, v):
        self._average_latency.value = v

    @property
    def big_sequence_error(self):
        return self._big_sequence_error.value

    @big_sequence_error.setter
    def big_sequence_error(self, v):
        self._big_sequence_error.value = v

    @property
    def bit_rate(self):
        return self._bit_rate.value

    @bit_rate.setter
    def bit_rate(self, v):
        self._bit_rate.value = v

    @property
    def byte_rate(self):
        return self._byte_rate.value

    @byte_rate.setter
    def byte_rate(self, v):
        self._byte_rate.value = v

    @property
    def duplicate_frames(self):
        return self._duplicate_frames.value

    @duplicate_frames.setter
    def duplicate_frames(self, v):
        self._duplicate_frames.value = v

    @property
    def first_time_stamp(self):
        return self._first_time_stamp.value

    @first_time_stamp.setter
    def first_time_stamp(self, v):
        self._first_time_stamp.value = v

    @property
    def frame_rate(self):
        return self._frame_rate.value

    @frame_rate.setter
    def frame_rate(self, v):
        self._frame_rate.value = v

    @property
    def last_time_stamp(self):
        return self._last_time_stamp.value

    @last_time_stamp.setter
    def last_time_stamp(self, v):
        self._last_time_stamp.value = v

    @property
    def max_delay_variation(self):
        return self._max_delay_variation.value

    @max_delay_variation.setter
    def max_delay_variation(self, v):
        self._max_delay_variation.value = v

    @property
    def max_latency(self):
        return self._max_latency.value

    @max_latency.setter
    def max_latency(self, v):
        self._max_latency.value = v

    @property
    def max_min_delay_variation(self):
        return self._max_min_delay_variation.value

    @max_min_delay_variation.setter
    def max_min_delay_variation(self, v):
        self._max_min_delay_variation.value = v

    @property
    def maxmin_interval(self):
        return self._maxmin_interval.value

    @maxmin_interval.setter
    def maxmin_interval(self, v):
        self._maxmin_interval.value = v

    @property
    def min_delay_variation(self):
        return self._min_delay_variation.value

    @min_delay_variation.setter
    def min_delay_variation(self, v):
        self._min_delay_variation.value = v

    @property
    def min_latency(self):
        return self._min_latency.value

    @min_latency.setter
    def min_latency(self, v):
        self._min_latency.value = v

    @property
    def num_groups(self):
        return self._num_groups.value

    @num_groups.setter
    def num_groups(self, v):
        self._num_groups.value = v

    @property
    def prbs_ber_ratio(self):
        return self._prbs_ber_ratio.value

    @prbs_ber_ratio.setter
    def prbs_ber_ratio(self, v):
        self._prbs_ber_ratio.value = v

    @property
    def prbs_bits_received(self):
        return self._prbs_bits_received.value

    @prbs_bits_received.setter
    def prbs_bits_received(self, v):
        self._prbs_bits_received.value = v

    @property
    def prbs_errored_bits(self):
        return self._prbs_errored_bits.value

    @prbs_errored_bits.setter
    def prbs_errored_bits(self, v):
        self._prbs_errored_bits.value = v

    @property
    def read_time_stamp(self):
        return self._read_time_stamp.value

    @read_time_stamp.setter
    def read_time_stamp(self, v):
        self._read_time_stamp.value = v

    @property
    def reverse_sequence_error(self):
        return self._reverse_sequence_error.value

    @reverse_sequence_error.setter
    def reverse_sequence_error(self, v):
        self._reverse_sequence_error.value = v

    @property
    def sequence_gaps(self):
        return self._sequence_gaps.value

    @sequence_gaps.setter
    def sequence_gaps(self, v):
        self._sequence_gaps.value = v

    @property
    def small_sequence_error(self):
        return self._small_sequence_error.value

    @small_sequence_error.setter
    def small_sequence_error(self, v):
        self._small_sequence_error.value = v

    @property
    def standard_deviation(self):
        return self._standard_deviation.value

    @standard_deviation.setter
    def standard_deviation(self, v):
        self._standard_deviation.value = v

    @property
    def total_byte_count(self):
        return self._total_byte_count.value

    @total_byte_count.setter
    def total_byte_count(self, v):
        self._total_byte_count.value = v

    @property
    def total_frames(self):
        return self._total_frames.value

    @total_frames.setter
    def total_frames(self, v):
        self._total_frames.value = v

    @property
    def total_sequence_error(self):
        return self._total_sequence_error.value

    @total_sequence_error.setter
    def total_sequence_error(self, v):
        self._total_sequence_error.value = v

    def __str__(self):
        temp_str = ""
        allClassMembers = inspect.getmembers(self)
        for memberType, memberName in allClassMembers:
            if (str(memberType)[0] == "_" and str(memberType)[1] != "_" and str(memberType) != "_stats_type" and not inspect.ismethod(memberName)):
                temp_str += "\n\"{}\":\"{}\",".format(memberName._name, memberName.value)
        temp_str = temp_str[:-1]
        temp_str += "\n"
        return temp_str

    def _reset_stats(self, stat_type=str):
        allClassMembers = inspect.getmembers(self)
        for memberType, memberName in allClassMembers:
            if (str(memberType)[0] == "_" and str(memberType)[1] != "_" and str(memberType) != "_stats_type" and not inspect.ismethod(memberName)):
                memberName._clear()

class _stream_stats(object):
    def __init__(self):
        self._stats_type = str
        self._frames_sent = _stat_member()
        self._frames_sent_rate = _stat_member()
        self.rx_ports = OrderedDict()  #type: list[_RX_PORT_STATS]

    @property
    def frames_sent(self):
        return self._frames_sent.value

    @frames_sent.setter
    def frames_sent(self, v):
        self._frames_sent.value = v

    @property
    def frames_sent_rate(self):
        return self._frames_sent_rate.value

    @frames_sent_rate.setter
    def frames_sent_rate(self, v):
        self._frames_sent_rate.value = v

    def __str__(self):
        temp_str = "{"
        allClassMembers = inspect.getmembers(self)
        for memberType, memberName in allClassMembers:
            if (str(memberType)[0] == "_" and str(memberType)[1] != "_" and str(memberType) != "_stats_type" and not inspect.ismethod(memberName)):
                temp_str += "\n\"{}\":\"{}\",".format(memberName._name, memberName.value)
        temp_str += "\n\"rx_stats\":[{"
        for rx_port in self.rx_ports:
            temp_str += "\n\"" + str(rx_port) + "\":[{\n" + str(self.rx_ports[rx_port]) + "\n}],"
        temp_str = temp_str[:-1]
        temp_str += "}]}"
        return temp_str

    def _reset_stats(self, stat_type=str):
        allClassMembers = inspect.getmembers(self)
        for memberType, memberName in allClassMembers:
            if (str(memberType)[0] == "_" and str(memberType)[1] != "_" and str(memberType) != "_stats_type" and not inspect.ismethod(memberName)):
                memberName._clear()

