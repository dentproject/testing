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

from UnifiedTG.Unified.Ipv6_extentions import V6Option_PAD1, V6Option_PADN, V6Option_Jumbo, V6Option_RouterAlert, \
    V6Option_BindingUpdate, V6Option_BindingAck
from UnifiedTG.Unified.TGEnums import TGEnums
from UnifiedTG.Unified.Stream import Stream
from UnifiedTG.Unified.TGEnums import TGEnums
from UnifiedTG.Unified.Utils import attrWithDefault
from UnifiedTG.IxEx.IxExEnums import IxExEnums
from ixexplorer.ixe_statistics_view import IxeStreamsStats
from UnifiedTG.Unified.Stream import _RX_PORT_STATS
from UnifiedTG.IxEx.IxExPort import StreamWarningsError
from UnifiedTG.Unified.Utils import Converter
import functools
import json



class IxExStream(Stream):
    _sentinel = object() # used for _update_field function

    def __init__(self,stream_name=None):
        super(self.__class__, self).__init__(stream_name)



    def apply(self, apply_to_hw = False, selective_update=True):
        self._logger.info(self._get_stream_log_title(), self._get_stream_log_message())
        super(self.__class__, self).apply()
        if self.source_interface.enabled:
            driver_if_key = self._parent.protocol_managment.protocol_interfaces.interfaces[self.source_interface.description_key]._driver_if_key
            self._update_field(self.source_interface._description_key, "sourceInterfaceDescription",value=driver_if_key,always_write=True)
        self._update_field(self.source_interface._enabled, "enableSourceInterface")

        if apply_to_hw == True:
            try:
                rc = self._stream_driver_obj.write()
            except StreamWarningsError as e:
                print (str(e))
                self._logger.info("StreamWarningsError", str(e))

    def _rsetattr(self, obj, attr, val):
        pre, _, post = attr.rpartition('.')
        return setattr(self._rgetattr(obj, pre) if pre else obj, post, val)

    def _rgetattr(self, obj, attr, default=_sentinel):
        if default is IxExStream._sentinel:
            _getattr = getattr
        else:
            def _getattr(obj, name):
                return getattr(obj, name, default)
        return functools.reduce(_getattr, [obj] + attr.split('.'))

    def _update_field(self, api_field=None, driver_field=None, value=None, exception_info="", always_write=False):
        try:
            val = None
            # case 1 - field is hidden from api
            if api_field is None:
                if type(value) == attrWithDefault:
                    val = value.current_val
                    value._driver_field = driver_field
                else:
                    val = value
                # api_field._previous_val = api_field._current_val
                self._rsetattr(self._stream_driver_obj, driver_field, val)
                if self._debug_prints: print ("updating " + driver_field)
            else:
                api_field._driver_field = driver_field
                # case 2 - value was never updated in driver
                if api_field._was_written_to_driver == False:
                    if value is None:
                        api_field._previous_val = api_field._current_val
                        val = api_field._current_val
                        self._rsetattr(self._stream_driver_obj,driver_field, val)
                        if self._debug_prints: print ("updating " + driver_field)
                        if not always_write: api_field._was_written_to_driver = True
                    else:
                        if type(value) == attrWithDefault:
                            val = value.current_val
                        else:
                            val = value
                        api_field._previous_val = api_field._current_val
                        self._rsetattr(self._stream_driver_obj, driver_field, val)
                        if self._debug_prints: print ("updating " + driver_field)
                        if not always_write: api_field._was_written_to_driver = True
                # case 3 - value is different than previous
                elif api_field._current_val != api_field._previous_val or always_write:
                    if value is None:
                        api_field._previous_val = api_field._current_val
                        val = api_field._current_val
                        self._rsetattr(self._stream_driver_obj, driver_field, val)
                        if self._debug_prints: print ("updating " + driver_field)
                        if not always_write: api_field._was_written_to_driver = True
                    else:
                        if type(value) == attrWithDefault:
                            val = value.current_val
                        else:
                            val = value
                        self._rsetattr(self._stream_driver_obj, driver_field, val)
                        if self._debug_prints: print ("updating " + driver_field)
                        if not always_write: api_field._was_written_to_driver = True
                else:
                    if self._debug_prints: print ("no update need for " + driver_field)
        except Exception as e:
            raise Exception("Error in update field.\nField name = " + driver_field +
                            "\nValue to set: " + str(val) +
                            "\n" + exception_info +
                            "\n" + str(self) +
                            "\nDriver Exeption:\n" + str(e))


    def _get_field(self,name):
        x = self._rgetattr(self._stream_driver_obj, name)
        return x

    def _get_field_hw_value(self,field):
        return self._get_field(field._driver_field)

    def _packet_view(self):
        return self._get_field('packetView')

    def _apply_mac(self):
        if self.source_interface.enabled is False:
            self._update_field(self.packet.mac.da._value, "da")
            mac_da_mode = IxExEnums.TGEnums_IxExEnums_map(self.packet.mac.da.mode, IxExEnums.MODIFIER_MAC_MODE)
            self._update_field(driver_field="daRepeatCounter", value=mac_da_mode)
            self._update_field(self.packet.mac.da._step, "daStep")
            self._update_field(self.packet.mac.da._count, "numDA")
            if self.packet.mac.da.mode is TGEnums.MODIFIER_MAC_MODE.RANDOM and self.packet.mac.da.mask:
                self._update_field(self.packet.mac.da._mask, "daMaskSelect")
        self._update_field(self.packet.mac.sa._value, "sa")
        mac_sa_mode = IxExEnums.TGEnums_IxExEnums_map(self.packet.mac.sa.mode, IxExEnums.MODIFIER_MAC_MODE)
        self._update_field( driver_field="saRepeatCounter",value=mac_sa_mode)
        self._update_field(self.packet.mac.sa._step, "saStep")
        self._update_field(self.packet.mac.sa._count, "numSA")
        if self.packet.mac.sa.mode is TGEnums.MODIFIER_MAC_MODE.RANDOM and self.packet.mac.sa.mask:
            self._update_field(self.packet.mac.sa._mask, "saMaskSelect")

        fcs_mode = IxExEnums.TGEnums_IxExEnums_map(self.packet.mac.fcs, IxExEnums.FCS_ERRORS_MODE)
        self._update_field(driver_field="fcs", value=fcs_mode)


    def _apply_ethertype(self):
        pass


    def _apply_frame_preemption(self):
        frag_count_list = [TGEnums.FP_PACKET_TYPE.SMD_C0,TGEnums.FP_PACKET_TYPE.SMD_C1,
                           TGEnums.FP_PACKET_TYPE.SMD_C2,TGEnums.FP_PACKET_TYPE.SMD_C3]
        not_end_fragment_list = [TGEnums.FP_PACKET_TYPE.SMD_R,TGEnums.FP_PACKET_TYPE.SMD_V]

        if self.packet.preemption.enabled is not None:
            if self.packet.preemption.enabled is False:
                self._update_field(self.packet.preemption._packet_type, 'fpMPacketType',
                                   value=TGEnums.FP_PACKET_TYPE.Express.value,always_write=True)
            else:
                self._update_field(self.packet.preemption._packet_type, 'fpMPacketType',
                                   value=self.packet.preemption.packetType.value)
                if self.packet.preemption.packetType in frag_count_list:
                    self._update_field(self.packet.preemption._frag_count, 'fpFragCount',
                                   value=self.packet.preemption.fragCount.value)
                if self.packet.preemption.packetType not in not_end_fragment_list:
                    if self.packet.preemption.endFragmet is False:
                        self.packet.preemption._crc_type.current_val = TGEnums.FP_CRC_TYPE.CRCmCRC
                    else:
                        self.packet.preemption._crc_type.current_val = TGEnums.FP_CRC_TYPE.CRCFCS
                    self._update_field(self.packet.preemption._crc_type, 'fpCrcType',
                                       value=self.packet.preemption._crc_type.current_val.value)

    def _apply_mpls(self):
        if len(self.packet.mpls_labels)>0:
            self._stream_driver_obj.protocol.enableMPLS = True
            self._stream_driver_obj.set_auto_set(0)
            self._stream_driver_obj.mpls.setDefault()
            for idx, mp in enumerate(self.packet.mpls_labels):
                obj = self.packet.mpls_labels[mp]
                self._stream_driver_obj.mpls_label.setDefault()
                if obj.label is not None:
                    self._update_field(driver_field="mpls.enableAutomaticallySetLabel", value=False)
                    self._update_field(obj._label, "mpls_label.label", always_write=True)
                else:
                    self._update_field(driver_field="mpls.enableAutomaticallySetLabel", value=True)
                self._update_field(obj._ttl, "mpls_label.timeToLive", always_write=True)
                self._update_field(obj._exp, "mpls_label.experimentalUse", always_write=True)
                self._stream_driver_obj.mpls_label.set(idx+1)
            self._stream_driver_obj.set_auto_set(1)
            self._update_field(driver_field="mpls.forceBottomOfStack", value=True)
        else:
            self._stream_driver_obj.protocol.enableMPLS = False

    def _apply_vlans(self):
        counter = 1

        if len(self.packet.vlans) == 0:
            self._stream_driver_obj.protocol.enable802dot1qTag = 0
        elif len(self.packet.vlans) == 1:
            self._stream_driver_obj.protocol.enable802dot1qTag = 1
        elif len(self.packet.vlans) > 1:
            self._stream_driver_obj.protocol.enable802dot1qTag = 2

        self._stream_driver_obj.stackedVlan.setDefault()
        self._stream_driver_obj.vlan.setDefault()

        # if len(self.packet.vlans) == 1:
        #     for vlan in self.packet.vlans:
        #         self.packet.vlans[vlan]._reset_to_default()
        #         self._update_field(api_field=self.packet.vlans[vlan].vid._value, driver_field="vlan.vlanID")
        #         #todo add/fix vlan repeat & mode
        #         #self._update_field(api_field=self.packet.vlans[vlan].vid._count, driver_field="vlan.repeat")
        #         # self._update_field(api_field=self.packet.vlans[vlan].vid._mode, driver_field="vlan.mode")
        #         self._update_field(api_field=self.packet.vlans[vlan]._priority, driver_field="vlan.userPriority")
        #         self._update_field(api_field=self.packet.vlans[vlan]._cfi, driver_field="vlan.cfi")
        #         self._update_field(api_field=self.packet.vlans[vlan]._proto, driver_field="vlan.protocolTagId")
        #         # self._update_field(driver_field="stackedVlan.setVlan", value=counter)
        #         # self._update_field(driver_field="stackedVlan.addVlan", value=counter)
        #         counter += 1
        # elif len(self.packet.vlans) >= 2:
        for vlan in self.packet.vlans:
            self.packet.vlans[vlan]._reset_to_default()
            self._update_field(api_field=self.packet.vlans[vlan].vid._value, driver_field="vlan.vlanID")
            if self.packet.vlans[vlan]._vid.mode is not TGEnums.MODIFIER_VLAN_MODE.FIXED:
                self._update_field(api_field=self.packet.vlans[vlan].vid._count, driver_field="vlan.repeat")
            self._update_field(api_field=self.packet.vlans[vlan]._priority, driver_field="vlan.userPriority")
            self._update_field(api_field=self.packet.vlans[vlan]._cfi, driver_field="vlan.cfi")
            self._update_field(api_field=self.packet.vlans[vlan]._proto, driver_field="vlan.protocolTagId")
            vid_mod = 0
            if self.packet.vlans[vlan]._vid.mode == TGEnums.MODIFIER_VLAN_MODE.FIXED:
                vid_mod = 0
            elif self.packet.vlans[vlan]._vid.mode == TGEnums.MODIFIER_VLAN_MODE.INCREMENT:
                vid_mod = 1
            elif self.packet.vlans[vlan]._vid.mode == TGEnums.MODIFIER_VLAN_MODE.DECREMENT:
                vid_mod = 2
            elif self.packet.vlans[vlan]._vid.mode == TGEnums.MODIFIER_VLAN_MODE.CONTINUOUS_INCREMENT:
                vid_mod = 3
            elif self.packet.vlans[vlan]._vid.mode == TGEnums.MODIFIER_VLAN_MODE.CONTINUOUS_DECREMENT:
                vid_mod = 4
            elif self.packet.vlans[vlan]._vid.mode == TGEnums.MODIFIER_VLAN_MODE.RANDOM:
                vid_mod = 5
            self._update_field(driver_field="vlan.mode", value=vid_mod)
            if len(self.packet.vlans) >= 2:
                if counter <= 2:
                    self._stream_driver_obj.stackedVlan.ix_set()
                    self._stream_driver_obj.stackedVlan.setVlan(counter)
                else:
                    self._stream_driver_obj.stackedVlan.ix_set()
                    self._stream_driver_obj.stackedVlan.addVlan()
            counter += 1

    def _apply_l2_proto(self):

        proto_name = "1"
        if self.packet.l2_proto == TGEnums.L2_PROTO.ETHERNETII:
            proto_name = '1'
            self._update_field(self.packet._l2_proto, "protocol.ethernetType", proto_name)
            self._update_field(self.packet._ethertype, "frameType")

        elif self.packet.l2_proto == TGEnums.L2_PROTO.SNAP:
            proto_name = '2'
            self._update_field(self.packet._l2_proto, "protocol.ethernetType", proto_name)
        elif self.packet.l2_proto == TGEnums.L2_PROTO.RAW:
            proto_name = '3'
            self._update_field(self.packet._l2_proto, "protocol.ethernetType", proto_name)
        elif self.packet.l2_proto == TGEnums.L2_PROTO.IPX:
            proto_name = '15'
            self._update_field(self.packet._l2_proto, "protocol.ethernetType", proto_name)
        elif self.packet.l2_proto == TGEnums.L2_PROTO.PROTOCOL_OFFSET:
            proto_name = '53'
            self._update_field(self.packet._l2_proto, "protocol.ethernetType", proto_name)
        elif self.packet.l2_proto == TGEnums.L2_PROTO.NONE:
            proto_name = '0'  #todo find which value goes here
            self._update_field(self.packet._l2_proto, "protocol.ethernetType", proto_name)

        else:
            raise Exception ("L3_PROTO \"" + self.packet.l3_proto + "\" supported!")

    def _apply_l3_proto(self):
        proto_name = ""
        if self.packet.l3_proto == TGEnums.L3_PROTO.IPV4:
            proto_name = 'ipV4'
        elif self.packet.l3_proto == TGEnums.L3_PROTO.IPV6:
            proto_name = 'ipV6'  #todo find which value goes here
        elif self.packet.l3_proto == TGEnums.L3_PROTO.ARP:
            self._update_field(self.packet._l4_proto, "protocol.appName", "Arp")
            return
        elif self.packet.l3_proto == TGEnums.L3_PROTO.NONE:
            proto_name = 'mac'  #todo find which value goes here
        elif self.packet.l3_proto is TGEnums.L3_PROTO.IPV4_O_IPV6:
            proto_name = 'ipV6'
        elif self.packet.l3_proto is TGEnums.L3_PROTO.IPV6_O_IPV4:
            proto_name = 'ipV4'
        elif self.packet.l3_proto is TGEnums.L3_PROTO.PAUSE_CONTROL:
            self._update_field(self.packet.pause_control._destination_address, "pauseControl.da")
            self._update_field(self.packet.pause_control._ieee_802._pause_quanta, "pauseControl.pauseTime")
            proto_name = 'pauseControl'

        else:
            raise Exception ("L3_PROTO \"{}\" supported!".format(self.packet.l3_proto))
        self._update_field(self.packet._l3_proto, "protocol.name", proto_name)

    def update_v4_L4(self,l4_proto=None, ipv4_obj=None):
        l4_proto = self.packet.l4_proto if l4_proto is None else l4_proto
        ipv4_obj = self.packet.ipv4 if ipv4_obj is None else ipv4_obj
        if l4_proto == TGEnums.L4_PROTO.TCP:
            self._update_field(ipv4_obj._protocol, "ip.ipProtocol", "6")
        elif l4_proto == TGEnums.L4_PROTO.UDP:
            self._update_field(ipv4_obj._protocol, "ip.ipProtocol", "17")
        elif l4_proto == TGEnums.L4_PROTO.ICMP:
            self._update_field(ipv4_obj._protocol, "ip.ipProtocol", "1")
        elif l4_proto == TGEnums.L4_PROTO.IGMP:
            self._update_field(ipv4_obj._protocol, "ip.ipProtocol", "2")
        elif l4_proto == TGEnums.L4_PROTO.OSPF:
            self._update_field(ipv4_obj._protocol, "ip.ipProtocol", "89")
        elif l4_proto == TGEnums.L4_PROTO.GRE:
            self._update_field(ipv4_obj._protocol, "ip.ipProtocol", "47")
        elif l4_proto == TGEnums.L4_PROTO.NONE:
            self._update_field(ipv4_obj._protocol, "ip.ipProtocol")

    def update_v6_L4(self,l4_proto=None, ipv6_obj=None):
        l4_proto = self.packet.l4_proto if l4_proto is None else l4_proto
        ipv6_obj = self.packet.ipv6 if ipv6_obj is None else ipv6_obj
        if l4_proto == TGEnums.L4_PROTO.TCP:
            self._update_field(ipv6_obj._next_header, "ipV6.nextHeader", "6")
        elif l4_proto == TGEnums.L4_PROTO.UDP:
            self._update_field(ipv6_obj._next_header, "ipV6.nextHeader", "17")
        elif l4_proto == TGEnums.L4_PROTO.ICMP:
            self._update_field(ipv6_obj._next_header, "ipV6.nextHeader", "58")
        elif l4_proto == TGEnums.L4_PROTO.GRE:
            self._update_field(ipv6_obj._next_header, "ipV6.nextHeader", "47")
        elif l4_proto == TGEnums.L4_PROTO.NONE:
            self._update_field(ipv6_obj._next_header, "ipV6.nextHeader", "59")

    def _apply_l4_proto(self, pkt_obj=None):
        # L4 protocol in ixia is configured using ipProtocol command in IP
        proto_name = ""
        proto_appName = ""
        pkt_obj = self.packet if pkt_obj is None else pkt_obj
        if pkt_obj.l3_proto is TGEnums.L3_PROTO.ARP or pkt_obj.l3_proto is TGEnums.L3_PROTO.PAUSE_CONTROL \
                or not isinstance(pkt_obj.l3_proto, TGEnums.L3_PROTO):
            pass
        elif pkt_obj.l3_proto == TGEnums.L3_PROTO.IPV4:
            proto_name = 'ipV4'
            self._update_field(pkt_obj._l3_proto, "protocol.name", proto_name)
            self.update_v4_L4(pkt_obj.l4_proto,pkt_obj.ipv4)
        elif pkt_obj.l3_proto == TGEnums.L3_PROTO.IPV6:
            proto_name = 'ipV6'
            self._update_field(pkt_obj._l3_proto, "protocol.name", proto_name)
            self.update_v6_L4(pkt_obj.l4_proto, pkt_obj.ipv6)
        elif pkt_obj.l3_proto == TGEnums.L3_PROTO.NONE:
            proto_name = 'mac'
            self._update_field(pkt_obj._l3_proto, "protocol.name", proto_name)
        elif pkt_obj.l3_proto is TGEnums.L3_PROTO.IPV6_O_IPV4:
            proto_name = 'ipV4'
            self._update_field(pkt_obj._l3_proto, "protocol.name", proto_name)
            self._update_field(pkt_obj.ipv4._protocol, "ip.ipProtocol", '41')
            self.update_v6_L4(pkt_obj.l4_proto, pkt_obj.ipv6)
        elif pkt_obj.l3_proto is TGEnums.L3_PROTO.IPV4_O_IPV6:
            proto_name = 'ipV6'
            self._update_field(pkt_obj._l3_proto, "protocol.name", proto_name)
            self._update_field(pkt_obj.ipv6._next_header, "ipV6.nextHeader", "4")
            self.update_v4_L4(pkt_obj.l4_proto, pkt_obj.ipv4)
        else:
            raise Exception ("L3_PROTO \"{}\" supported!".format(pkt_obj.l4_proto))
        # self._update_field(pkt_obj._l4_proto, "protocol.appName", proto_appName)

    def _apply_ipv4(self,ipv4_obj = None):

        inc_net = {TGEnums.MODIFIER_IPV4_ADDRESS_MODE.INCREMENT_NET,
             TGEnums.MODIFIER_IPV4_ADDRESS_MODE.DECREMENT_NET,
             TGEnums.MODIFIER_IPV4_ADDRESS_MODE.CONTINUOUS_INCREMENT_NET,
             TGEnums.MODIFIER_IPV4_ADDRESS_MODE.CONTINUOUS_DECREMENT_NET}

        ipv4_obj = self.packet.ipv4 if ipv4_obj is None else ipv4_obj
        self._update_field(ipv4_obj.source_ip._value, "ip.sourceIpAddr")
        ipv4_source_ip_mode = IxExEnums.TGEnums_IxExEnums_map(ipv4_obj.source_ip.mode, IxExEnums.MODIFIER_IPV4_ADDRESS_MODE)
        self._update_field(ipv4_obj.source_ip._mode, "ip.sourceIpAddrMode", value=ipv4_source_ip_mode)
        self._update_field(ipv4_obj.source_ip._count, "ip.sourceIpAddrRepeatCount")
        if ipv4_obj.source_ip.mode in inc_net:
            ip_class = ipv4_obj.source_ip.mask.count('255')-1
            self._update_field(ipv4_obj.source_ip._mask, "ip.sourceClass", ip_class)
        else:
            self._update_field(ipv4_obj.source_ip._mask, "ip.sourceIpMask")
        self._update_field(ipv4_obj.destination_ip._value, "ip.destIpAddr")
        ipv4_dest_ip_mode = IxExEnums.TGEnums_IxExEnums_map(ipv4_obj.destination_ip.mode, IxExEnums.MODIFIER_IPV4_ADDRESS_MODE)
        self._update_field(ipv4_obj.destination_ip._mode, "ip.destIpAddrMode", value=ipv4_dest_ip_mode)
        self._update_field(ipv4_obj.destination_ip._count, "ip.destIpAddrRepeatCount")
        if ipv4_obj.destination_ip.mode in inc_net:
            ip_class = ipv4_obj.destination_ip.mask.count('255')-1
            self._update_field(ipv4_obj.destination_ip._mask, "ip.destClass", ip_class)
        else:
            self._update_field(ipv4_obj.destination_ip._mask, "ip.destIpMask")
        self._update_field(ipv4_obj._ttl, "ip.ttl")
        self._update_field(ipv4_obj._enable_header_len_override, "ip.enableHeaderLengthOverride")
        self._update_field(ipv4_obj._header_len_override_value, "ip.headerLength")
        self._update_field(ipv4_obj._identifier, "ip.identifier")
        self._update_field(ipv4_obj._options_padding, "ip.options")
        self._update_field(ipv4_obj._length_override, "ip.lengthOverride")
        self._update_field(ipv4_obj._length_value, "ip.totalLength")
        self._update_field(ipv4_obj._fragment_enable, "ip.fragment", value=not ipv4_obj._fragment_enable.current_val)
        self._update_field(ipv4_obj._fragment_last_enable, "ip.lastFragment", value=not ipv4_obj._fragment_last_enable.current_val)
        self._update_field(ipv4_obj._fragment_offset_decimal_value, "ip.fragmentOffset")
        self._update_field(ipv4_obj._protocol, "ip.ipProtocol")

        if ipv4_obj._qos_type.current_val == TGEnums.QOS_MODE.DSCP:
            qos_mode = 1
            self._update_field(driver_field="ip.dscpMode", value=4)
            # statically set to custom...
            # 0 - ipV4DscpDefault, 1 - ipV4DscpClassSelector, 2 - ipV4DscpAssuredForwarding,
            # 3 - ipV4DscpExpeditedForwarding, 4 - ipV4DscpCustom
            dscp_hex = hex(int(ipv4_obj.dscp_decimal_value)).split('x')[-1]
            self._update_field(ipv4_obj._dscp_decimal_value, "ip.dscpValue", value=dscp_hex)
        else:
            qos_mode = 0
            self._update_field(ipv4_obj._tos_precedence, "ip.precedence")
            self._update_field(ipv4_obj._tos_delay, "ip.delay")
            self._update_field(ipv4_obj._tos_throughput, "ip.throughput")
            self._update_field(ipv4_obj._tos_reliability, "ip.reliability")
            self._update_field(ipv4_obj._tos_cost, "ip.cost")
            self._update_field(ipv4_obj._tos_reserved, "ip.reserved")
        self._update_field(ipv4_obj._qos_type, "ip.qosMode", value=qos_mode)

        checksum_mode = 1
        if ipv4_obj._checksum_mode.current_val == TGEnums.CHECKSUM_MODE.INVALID:
            checksum_mode = 0
        elif ipv4_obj._checksum_mode.current_val == TGEnums.CHECKSUM_MODE.OVERRIDE:
            checksum_mode = 2
        self._update_field(ipv4_obj._checksum_mode, "ip.useValidChecksum", value=checksum_mode)
        self._update_field(ipv4_obj._custom_checksum, "ip.checksum")

    def _apply_ipv6(self,ipv6_obj = None):
        ipv6_obj = self.packet.ipv6 if ipv6_obj is None else ipv6_obj
        self._stream_driver_obj.set_auto_set(0)
        self._update_field(ipv6_obj.source_ip._value, "ipV6.sourceAddr")
        ipv6_source_ip_mode = IxExEnums.TGEnums_IxExEnums_map(ipv6_obj.source_ip.mode, IxExEnums.MODIFIER_IPV6_ADDRESS_MODE)
        try:
            self._update_field(ipv6_obj.source_ip._mode, "ipV6.sourceAddrMode", value=ipv6_source_ip_mode)
        except Exception as e:
            print("Exception when configuring ipv6 source ip mode, maybe mode ({})"
                  " not supported with address ({})").\
                format(ipv6_obj.source_ip._mode, ipv6_obj.source_ip._value)
            print(str(e))
            raise
        self._update_field(ipv6_obj.source_ip._count, "ipV6.sourceAddrRepeatCount")
        self._update_field(ipv6_obj.source_ip._step, "ipV6.sourceStepSize")
        self._update_field(ipv6_obj.source_ip._mask, "ipV6.sourceMask")
        self._update_field(ipv6_obj.destination_ip._value, "ipV6.destAddr")
        ipv6_destination_ip_mode = IxExEnums.TGEnums_IxExEnums_map(ipv6_obj.destination_ip.mode, IxExEnums.MODIFIER_IPV6_ADDRESS_MODE)
        try:
            self._update_field(self.packet.ipv6.destination_ip._mode, "ipV6.destAddrMode", value=ipv6_destination_ip_mode)
        except Exception as e:
            print("Exception when configuring ipv6 source ip mode, maybe mode ({})"
                  " not supported with address ({})").\
                format(ipv6_obj.destination_ip._mode, ipv6_obj.destination_ip._value)
            print(str(e))
            raise
        self._update_field(ipv6_obj.destination_ip._count, "ipV6.destAddrRepeatCount")
        self._update_field(ipv6_obj.destination_ip._step, "ipV6.destStepSize")
        self._update_field(ipv6_obj.destination_ip._mask, "ipV6.destMask")

        self._update_field(ipv6_obj._traffic_class, "ipV6.trafficClass")
        self._update_field(ipv6_obj._flow_label, "ipV6.flowLabel")
        self._stream_driver_obj.set_auto_set(1)
        self._update_field(ipv6_obj._hop_limit, "ipV6.hopLimit")

        if ipv6_obj.extention_headers._ext_add_seq:
            self._stream_driver_obj.ipV6.clearAllExtensionHeaders()
            [self._add_v6_extension(obj) for obj in ipv6_obj.extention_headers._ext_add_seq]
            #update next header
            l4_proto = self.packet.l4_proto
            if l4_proto is TGEnums.L4_PROTO.TCP:
                l4_next = 'ipV4ProtocolTcp'
            elif l4_proto is TGEnums.L4_PROTO.UDP:
                l4_next = 'ipV4ProtocolUdp'
            elif l4_proto is TGEnums.L4_PROTO.ICMP:
                l4_next = 'icmpV6'
            elif l4_proto is TGEnums.L4_PROTO.GRE:
                l4_next = 'ipV4ProtocolGre'
            else:
                l4_next = 'ipV6NoNextHeader'
            self._stream_driver_obj.ipV6.addExtensionHeader(l4_next)



    def _add_v6_extension(self, extension):

        def handle_options():
            for opt_obj in extension._opt_add_seq:
                ix_opt = self._update_v6_option(opt_obj)
                current_extention.addOption(ix_opt)

        ext_type = extension._mytype
        if ext_type is TGEnums.Ipv6ExtensionType.Routing:
            ix_ex_cmd = 'ipV6Routing'
            self._stream_driver_obj.ipV6Routing.setDefault()
            self._update_field(value=extension.nodes,driver_field="ipV6Routing.nodeList",)
            self._update_field(value=extension.reserved, driver_field = "ipV6Routing.reserved")
        elif ext_type is TGEnums.Ipv6ExtensionType.HopByHop:
            ix_ex_cmd = 'ipV6HopByHop'
            self._stream_driver_obj.ipV6HopByHop.setDefault()
            current_extention = self._stream_driver_obj.ipV6HopByHop
            handle_options()
        elif ext_type is TGEnums.Ipv6ExtensionType.Fragment:
            ix_ex_cmd = 'ipV6Fragment'
            self._update_field(value=extension.fragment_offset,driver_field= "ipV6Fragment.fragmentOffset")
            self._update_field(value=extension.mflag, driver_field="ipV6Fragment.enableFlag")
            self._update_field(value=extension.id, driver_field="ipV6Fragment.identification")
            self._update_field(value=extension.reserved, driver_field="ipV6Fragment.reserved")
            self._update_field(value=extension.res, driver_field="ipV6Fragment.res")
        elif ext_type is TGEnums.Ipv6ExtensionType.Destination:
            ix_ex_cmd = 'ipV6DestinationOptions'
            self._stream_driver_obj.ipV6Destination.setDefault()
            current_extention = self._stream_driver_obj.ipV6Destination
            handle_options()
        elif ext_type is TGEnums.Ipv6ExtensionType.Authentication:
            ix_ex_cmd = 'ipV6Authentication'
            self._update_field(value=extension.payload_length,driver_field= "ipV6Authentication.payloadLength")
            self._update_field(value=extension.security_param_index,driver_field= "ipV6Authentication.securityParamIndex")
            self._update_field(value=extension.sequence_number_filed,driver_field= "ipV6Authentication.sequenceNumberField")

        self._stream_driver_obj.ipV6.addExtensionHeader(ix_ex_cmd)

    def _update_v6_option(self, opt):

        opt_type = opt._mytype
        if opt_type is TGEnums.Ipv6OptionType.PAD1:
            ix_opt = 'ipV6OptionPAD1'
        elif opt_type is TGEnums.Ipv6OptionType.PADN:
            self._stream_driver_obj.ipV6OptionPADN.setDefault()
            ix_opt = 'ipV6OptionPADN'
            lngth = len(Converter.remove_non_hexa_sumbols(opt.value))/2
            val = ''.join(('{',opt.value,'}'))
            self._update_field(driver_field="ipV6OptionPADN.value", value=val)
            self._update_field(driver_field="ipV6OptionPADN.length", value=lngth)
        elif opt_type is TGEnums.Ipv6OptionType.Jumbo:
            ix_opt = 'ipV6OptionJumbo'
            self._update_field(driver_field="ipV6OptionJumbo.payload", value=opt.payload)
        elif opt_type is TGEnums.Ipv6OptionType.RouterAlert:
            ix_opt = 'ipV6OptionRouterAlert'
            self._stream_driver_obj.ipV6OptionRouterAlert.setDefault()
            if opt.alert_type is TGEnums.RouterAlertType.MLD:
                al_type = 'ipV6RouterAlertMLD'
            elif opt.alert_type is TGEnums.RouterAlertType.RSVP:
                al_type = 'ipV6RouterAlertRSVP'
            elif opt.alert_type is TGEnums.RouterAlertType.ActiveNetworks:
                al_type = 'ipV6RouterAlertActiveNet'
            self._update_field(driver_field="ipV6OptionRouterAlert.routerAlert", value=al_type)
        elif opt_type is TGEnums.Ipv6OptionType.BindingUpdate:
            ix_opt = 'ipV6OptionBindingUpdate'
            self._update_field(driver_field="ipV6OptionBindingUpdate.enableAcknowledge", value=opt.acknowledge)
            self._update_field(driver_field="ipV6OptionBindingUpdate.enableBicasting", value=opt.bicasting)
            self._update_field(driver_field="ipV6OptionBindingUpdate.enableDuplicate", value=opt.duplicate)
            self._update_field(driver_field="ipV6OptionBindingUpdate.enableHome", value=opt.home)
            self._update_field(driver_field="ipV6OptionBindingUpdate.enableMAP", value=opt.map)
            self._update_field(driver_field="ipV6OptionBindingUpdate.enableRouter", value=opt.router)
            self._update_field(driver_field="ipV6OptionBindingUpdate.length", value=opt.length)
            self._update_field(driver_field="ipV6OptionBindingUpdate.lifeTime", value=opt.life_time)
            self._update_field(driver_field="ipV6OptionBindingUpdate.prefixLength", value=opt.prefix_length)
            self._update_field(driver_field="ipV6OptionBindingUpdate.sequenceNumber", value=opt.sequence_number)
        elif opt_type is TGEnums.Ipv6OptionType.BindingAcknowledgment:
            ix_opt = 'ipV6OptionBindingAck'
            self._update_field(driver_field="ipV6OptionBindingAck.length", value=opt.length)
            self._update_field(driver_field="ipV6OptionBindingAck.lifeTime", value=opt.life_time)
            self._update_field(driver_field="ipV6OptionBindingAck.status", value=opt.status)
            self._update_field(driver_field="ipV6OptionBindingAck.sequenceNumber", value=opt.sequence_number)
            self._update_field(driver_field="ipV6OptionBindingAck.refresh", value=opt.refresh)
        elif opt_type is TGEnums.Ipv6OptionType.BindingRequest:
            self._stream_driver_obj.ipV6OptionBindingRequest.setDefault()
            ix_opt = 'ipV6OptionBindingRequest'
            self._update_field(driver_field="ipV6OptionBindingRequest.length", value=opt.length)
        elif opt_type is TGEnums.Ipv6OptionType.HomeAddress:
            ix_opt = 'ipV6OptionHomeAddress'
            self._update_field(driver_field="ipV6OptionHomeAddress.address", value=opt.address)
        elif opt_type is TGEnums.Ipv6OptionType.MIpV6UniqueIdSub:
            ix_opt = 'ipV6OptionMIpV6UniqueIdSub'
            self._update_field(driver_field="ipV6OptionMIpV6UniqueIdSub.subUniqueId", value=opt.SubUniqueId)
        elif opt_type is TGEnums.Ipv6OptionType.MlpV6AlternativeCoaSub:
            ix_opt = 'ipV6OptionMIpV6AlternativeCoaSub'
            self._update_field(driver_field="ipV6OptionMIpV6AlternativeCoaSub.address", value=opt.address)
        return ix_opt

    def _apply_v4_over_v6(self):
        self._apply_ipv6()
        self._apply_ipv4()

    def _apply_v6_over_v4(self):
        self._apply_ipv4()
        self._apply_ipv6()

    def _apply_arp(self):
        if self.packet.arp.operation is not None:
            self._update_field(self.packet.arp._operation, "arp.operation",self.packet.arp.operation.value)

        self._update_field(self.packet.arp.sender_hw._value, "arp.sourceHardwareAddr")
        self._update_field(self.packet.arp.sender_hw._mode, "arp.sourceHardwareAddrMode",self.packet.arp.sender_hw.mode.value)
        self._update_field(self.packet.arp.sender_hw._count, "arp.sourceHardwareAddrRepeatCount")

        self._update_field(self.packet.arp.target_hw._value, "arp.destHardwareAddr")
        self._update_field(self.packet.arp.target_hw._mode, "arp.destHardwareAddrMode",self.packet.arp.target_hw.mode.value)
        self._update_field(self.packet.arp.target_hw._count, "arp.destHardwareAddrRepeatCount")

        self._update_field(self.packet.arp._sender_ip._value, "arp.sourceProtocolAddr")
        self._update_field(self.packet.arp._sender_ip._mode, "arp.sourceProtocolAddrMode",self.packet.arp._sender_ip.mode.value)
        self._update_field(self.packet.arp._sender_ip._count, "arp.sourceProtocolAddrRepeatCount")

        self._update_field(self.packet.arp._target_ip._value, "arp.destProtocolAddr")
        self._update_field(self.packet.arp._target_ip._mode, "arp.destProtocolAddrMode",self.packet.arp._target_ip.mode.value)
        self._update_field(self.packet.arp._target_ip._count, "arp.destProtocolAddrRepeatCount")


    def _apply_gre_fields(self,gre_l3_proto):
        self._stream_driver_obj.set_auto_set(0)
        self._update_field(self.packet.gre._version,"gre.version")
        self._update_field(self.packet.gre._reserve_0, "gre.reserved0")
        if self.packet.gre.key_field is None:
            self._update_field(driver_field="gre.enableKey", value=0)
        else:
            self._update_field(driver_field="gre.enableKey", value=1)
            self._update_field(self.packet.gre._key_field, "gre.key")
        if self.packet.gre.sequence_number is None:
            self._update_field(driver_field="gre.enableSequenceNumber", value=0)
        else:
            self._update_field(driver_field="gre.enableSequenceNumber", value=1)
            self._update_field(self.packet.gre._sequence_number, "gre.sequenceNumber")
        if self.packet.gre.use_checksum is False:
            self._update_field(driver_field="gre.enableChecksum", value=0)
        else:
            self._update_field(driver_field="gre.enableChecksum", value=1)
            self._update_field(driver_field="gre.enableValidChecksum", value=1)

        self._stream_driver_obj.set_auto_set(1)
        self._update_field(driver_field="gre.protocolType", value=gre_l3_proto)


    def _apply_gre(self):
        self._apply_l4_proto(self.packet.gre)
        if self.packet.gre.l3_proto is TGEnums.L3_PROTO.IPV4:
            self._apply_ipv4(self.packet.gre.ipv4)
            if self.packet.gre.l4_proto == TGEnums.L4_PROTO.TCP:
                self._apply_tcp(self.packet.gre.tcp)
            elif self.packet.gre.l4_proto == TGEnums.L4_PROTO.UDP:
                self._apply_udp(self.packet.gre.udp)
            gre_val = "{08 00}"
        elif self.packet.gre.l3_proto is TGEnums.L3_PROTO.IPV6:
            self._apply_ipv6(self.packet.gre.ipv6)
            if self.packet.gre.l4_proto == TGEnums.L4_PROTO.TCP:
                self._apply_tcp(self.packet.gre.tcp)
            elif self.packet.gre.l4_proto == TGEnums.L4_PROTO.UDP:
                self._apply_udp(self.packet.gre.udp)
            gre_val = "{86 DD}"
        else:
            proto = Converter.remove_non_hexa_sumbols(self.packet.gre.l3_proto)
            gre_val = '{{{0} {1}}}'.format(proto[:2], proto[2:])

        self._apply_gre_fields(gre_val)
        self._apply_l4_proto()
        self._apply_l3()


    def _apply_tcp(self,tcp_obj = None):
        tcp_obj = self.packet.tcp if tcp_obj is None else tcp_obj
        self._update_field(tcp_obj.source_port._value, "tcp.sourcePort")
        self._update_field(tcp_obj.destination_port._value, "tcp.destPort")

        self._update_field(tcp_obj._sequence_number, "tcp.sequenceNumber")
        self._update_field(tcp_obj._urgent_pointer, "tcp.urgentPointer")
        self._update_field(tcp_obj._acknowledgement_number, "tcp.acknowledgementNumber")
        self._update_field(tcp_obj._window, "tcp.window")
        self._update_field(tcp_obj._header_length, "tcp.offset")

        checksum_mode = 1
        if tcp_obj.valid_checksum == TGEnums.CHECKSUM_MODE.VALID:
            checksum_mode = 1
        elif tcp_obj.valid_checksum == TGEnums.CHECKSUM_MODE.INVALID:
            checksum_mode = 0
        elif tcp_obj.valid_checksum == TGEnums.CHECKSUM_MODE.OVERRIDE:
            checksum_mode = 2
        self._update_field(driver_field="tcp.useValidChecksum", value=checksum_mode)
        self._update_field(tcp_obj._custom_checksum, "tcp.checksum")

        self._update_field(tcp_obj._flag_acknowledge_valid, "tcp.acknowledgeValid")
        self._update_field(tcp_obj._flag_no_more_data_from_sender, "tcp.finished")
        self._update_field(tcp_obj._flag_push_function, "tcp.pushFunctionValid")
        self._update_field(tcp_obj._flag_urgent_pointer_valid, "tcp.urgentPointerValid")
        self._update_field(tcp_obj._flag_reset_connection, "tcp.resetConnection")
        self._update_field(tcp_obj._flag_synchronize_sequence, "tcp.synchronize")

    def _apply_udp(self,udp_obj = None):
        udp_obj = self.packet.udp if udp_obj is None else udp_obj
        self._update_field(udp_obj.source_port._value, "udp.sourcePort")
        self._update_field(udp_obj.destination_port._value, "udp.destPort")

        self._update_field(udp_obj._length_override, "udp.lengthOverride")
        self._update_field(udp_obj._custom_length, "udp.length")

        # checksum_mode = 0
        if udp_obj.valid_checksum == TGEnums.CHECKSUM_MODE.VALID:
            # checksum_mode = 0
            self._update_field(driver_field="udp.enableChecksum", value=1)
        elif udp_obj.valid_checksum == TGEnums.CHECKSUM_MODE.INVALID:
            checksum_mode = 0
            self._update_field(driver_field="udp.checksumMode", value=1)
            self._update_field(driver_field="udp.enableChecksumOverride", value=0)
        elif udp_obj.valid_checksum == TGEnums.CHECKSUM_MODE.OVERRIDE:
            # checksum_mode = 1
            self._update_field(driver_field="udp.enableChecksum", value=0)
            self._update_field(driver_field="udp.enableChecksumOverride", value=1)
            self._update_field(udp_obj._custom_checksum, "udp.checksum")


    def _apply_icmp(self):
        icmp_obj = self.packet.icmp
        ix_icmp_type = icmp_obj.icmp_type.value
        self._update_field(icmp_obj._type, "icmp.type", value=ix_icmp_type)
        self._update_field(icmp_obj._id, "icmp.id")
        self._update_field(icmp_obj._code, "icmp.code")
        self._update_field(icmp_obj._sequence, "icmp.sequence")


    def _apply_protocol_pad(self):
        if self.packet.protocol_pad.enabled is not None:
            self._update_field(self.packet.protocol_pad._enabled, "protocol.enableProtocolPad")
            if self.packet.protocol_pad.enabled is True:
                if self.packet.protocol_pad.type is TGEnums.PROTOCOL_PAD_TYPE.PTP:
                    ptp_string = self.packet.ptp.to_string()
                    length = 2
                    ix_format = ' '.join(ptp_string[i:i + length] for i in range(0, len(ptp_string), length))
                    self.packet.protocol_pad.custom_data = '{'+ix_format+'}'
                self._update_field(self.packet.protocol_pad._custom_data, "protocolPad.dataBytes")


    def _apply_data_pattern(self):
        # self._update_field(driver_field="dataPattern", value=18)
        self._stream_driver_obj.dataPattern = 18
        pattern_type = 0
        if self.packet.data_pattern.type == TGEnums.DATA_PATTERN_TYPE.FIXED:
            pattern_type = 6
        elif self.packet.data_pattern.type == TGEnums.DATA_PATTERN_TYPE.REPEATING:
            pattern_type = 5
        elif self.packet.data_pattern.type == TGEnums.DATA_PATTERN_TYPE.INCREMENT_BYTE:
            pattern_type = 0
        elif self.packet.data_pattern.type == TGEnums.DATA_PATTERN_TYPE.INCREMENT_WORD:
            pattern_type = 1
        elif self.packet.data_pattern.type == TGEnums.DATA_PATTERN_TYPE.DECREMENT_BYTE:
            pattern_type = 2
        elif self.packet.data_pattern.type == TGEnums.DATA_PATTERN_TYPE.DECREMENT_WORD:
            pattern_type = 3
        elif self.packet.data_pattern.type == TGEnums.DATA_PATTERN_TYPE.RANDOM:
            pattern_type = 4
        # elif self.packet.data_pattern.type == TGEnums.DATA_PATTERN_TYPE.LOAD_FROM_FILE:
        #     pattern_type = ???
        self._update_field(driver_field="patternType", value=pattern_type)
        self._update_field(self.packet.data_pattern._value, "pattern")

    def _apply_preamble_size(self):
        self._update_field(self.packet._preamble_size, "preambleSize")

    def _apply_protocol_offset(self):
        self._update_field(self.packet.protocol_offset._value, "protocolOffset.userDefinedTag")
        ix_offset = 12+len(self.packet.protocol_offset.value)/2
        self.packet.protocol_offset.offset = ix_offset
        self._update_field(self.packet.protocol_offset._offset, "protocolOffset.offset")

    def _apply_stream_rate(self):
        '''
        dma
        enableIbg
        enableIncrFrameBurstOverride
        enableIsg
        enforceMinGap
        fcs
        framesize
        frameSizeMAX
        frameSizeMIN
        frameSizeStep
        frameSizeType

        ibg

        ifgMAX
        ifgMIN
        ifgType
        isg
        loopCount
        numBursts
        numFrames

        preambleSize
        returnToId


        enableSuspend
        :return:
        '''

        """
        rateMode
        bpsRate
        fpsRate
        percentPacketRate
        ifg
        gapUnit
        
        """
        rate_mode = 1
        if self.rate.mode == TGEnums.STREAM_RATE_MODE.INTER_PACKET_GAP:
            rate_mode = 0
            gap_unit = 0
            if self.rate._inter_packet_gap_mode.current_val == TGEnums.STREAM_RATE_INTER_PACKET_GAP_MODE.NANOSECONDS:
                gap_unit = 0
            elif self.rate._inter_packet_gap_mode.current_val == TGEnums.STREAM_RATE_INTER_PACKET_GAP_MODE.MICROSECONDS:
                gap_unit = 1
            elif self.rate._inter_packet_gap_mode.current_val == TGEnums.STREAM_RATE_INTER_PACKET_GAP_MODE.MILLISECONDS:
                gap_unit = 2
            elif self.rate._inter_packet_gap_mode.current_val == TGEnums.STREAM_RATE_INTER_PACKET_GAP_MODE.SECONDS:
                gap_unit = 3
            elif self.rate._inter_packet_gap_mode.current_val == TGEnums.STREAM_RATE_INTER_PACKET_GAP_MODE.BYTES:
                gap_unit = 5
            self._update_field(driver_field="rateMode", value=rate_mode)
            self._update_field(driver_field="gapUnit", value=gap_unit)
            self._update_field(driver_field="ifg", value=self.rate._ipg_value)
        elif self.rate.mode == TGEnums.STREAM_RATE_MODE.UTILIZATION:
            rate_mode = 1
            self._update_field(self.rate._mode, driver_field="rateMode", value=rate_mode)
            self._update_field(driver_field="percentPacketRate", value=self.rate._utilization_value)
        elif self.rate.mode == TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND:
            rate_mode = 2
            self._update_field(self.rate._mode, driver_field="rateMode", value=rate_mode)
            self._update_field(driver_field="fpsRate", value=self.rate._pps_value)
        elif self.rate.mode == TGEnums.STREAM_RATE_MODE.BITRATE_PER_SECOND:
            rate_mode = 3
            self._update_field(self.rate._mode, driver_field="rateMode", value=rate_mode)
            self._update_field(driver_field="bpsRate", value=self.rate._bitrate_value)
        # self._update_field(self.rate._mode, driver_field="rateMode", value=rate_mode)


        # self._stream_driver_obj.percentPacketRate = 70

    def _apply_stream_control(self):
        control_mode = 0
        if self.control.mode == TGEnums.STREAM_TRANSMIT_MODE.CONTINUOUS_PACKET:
            control_mode = 0
        elif self.control.mode == TGEnums.STREAM_TRANSMIT_MODE.CONTINUOUS_BURST:
            control_mode = 1
        elif self.control.mode == TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM:
            control_mode = 2
        elif self.control.mode == TGEnums.STREAM_TRANSMIT_MODE.ADVANCE_TO_NEXT_STREAM:
            control_mode = 3
        elif self.control.mode == TGEnums.STREAM_TRANSMIT_MODE.RETURN_TO_ID:
            control_mode = 4
        elif self.control.mode == TGEnums.STREAM_TRANSMIT_MODE.RETURN_TO_ID_FOR_COUNT:
            control_mode = 5
        self._update_field(driver_field="dma", value=control_mode)
        self._update_field(self.control._return_to_id, driver_field="returnToId")
        self._update_field(self.control._loop_count, driver_field="loopCount")
        self._update_field(self.control._packets_per_burst, driver_field="numFrames")
        self._update_field(self.control._bursts_per_stream, driver_field="numBursts")

        self._update_field(self.control._inter_burst_gap_enable, driver_field="enableIbg")
        self._update_field(self.control._inter_burst_gap_value, driver_field="ibg")

        ibg_unit = 0
        if self.control.inter_burst_gap_unit == TGEnums.STREAM_INTER_BURST_GAP_UNIT.NANOSECONDS:
            ibg_unit = 0
        elif self.control.inter_burst_gap_unit == TGEnums.STREAM_INTER_BURST_GAP_UNIT.MICROSECONDS:
            ibg_unit = 1
        elif self.control.inter_burst_gap_unit == TGEnums.STREAM_INTER_BURST_GAP_UNIT.MILLISECONDS:
            ibg_unit = 2
        elif self.control.inter_burst_gap_unit == TGEnums.STREAM_INTER_BURST_GAP_UNIT.SECONDS:
            ibg_unit = 3
        elif self.control.inter_burst_gap_unit == TGEnums.STREAM_INTER_BURST_GAP_UNIT.BYTES:
            ibg_unit = 5
        self._update_field(driver_field="gapUnit", value=ibg_unit)

        self._update_field(self.control._inter_stream_gap_enable, driver_field="enableIsg")
        self._update_field(self.control._inter_stream_gap_value, driver_field="isg")
        isg_unit = 0
        if self.control.inter_stream_gap_unit == TGEnums.STREAM_INTER_STREAM_GAP_UNIT.NANOSECONDS:
            isg_unit = 0
        elif self.control.inter_stream_gap_unit == TGEnums.STREAM_INTER_STREAM_GAP_UNIT.MICROSECONDS:
            isg_unit = 1
        elif self.control.inter_stream_gap_unit == TGEnums.STREAM_INTER_STREAM_GAP_UNIT.MILLISECONDS:
            isg_unit = 2
        elif self.control.inter_stream_gap_unit == TGEnums.STREAM_INTER_STREAM_GAP_UNIT.SECONDS:
            isg_unit = 3
        elif self.control.inter_stream_gap_unit == TGEnums.STREAM_INTER_STREAM_GAP_UNIT.BYTES:
            isg_unit = 5
        self._update_field(driver_field="gapUnit", value=isg_unit)

        # todo fix
        self._update_field(self.control._pfc_queue, driver_field="priorityGroup",
                           exception_info="Make sure port transmit mode is PORT_BASED")
        pass
        # start_tx_delay_unit = 0
        # if self.control.start_tx_delay_unit == TGEnums.STREAM_START_TX_DELAY_UNIT.NANOSECONDS:
        #     start_tx_delay_unit = 0
        # elif self.control.start_tx_delay_unit == TGEnums.STREAM_START_TX_DELAY_UNIT.MICROSECONDS:
        #     start_tx_delay_unit = 1
        # elif self.control.start_tx_delay_unit == TGEnums.STREAM_START_TX_DELAY_UNIT.MILLISECONDS:
        #     start_tx_delay_unit = 2
        # elif self.control.start_tx_delay_unit == TGEnums.STREAM_START_TX_DELAY_UNIT.SECONDS:
        #     start_tx_delay_unit = 3
        # elif self.control.start_tx_delay_unit == TGEnums.STREAM_START_TX_DELAY_UNIT.BYTES:
        #     start_tx_delay_unit = 5
        # self._update_field(driver_field="startTxDelayUnit_temp", value=start_tx_delay_unit, exception_info="Make sure port transmit mode is PORT_BASED")
        # self._update_field(self.control._start_tx_delay, driver_field="startTxDelay_temp", exception_info="Make sure port transmit mode is PORT_BASED")

    def _apply_stream_status(self):
        self._update_field(self._enabled, "enable")
        self._update_field(self._suspend, "enableSuspend")

    def _apply_frame_size(self):
        self._update_field(self.frame_size._value, "framesize", always_write=True)

        rand_type_list = [TGEnums.MODIFIER_FRAME_SIZE_MODE.RANDOM,
                          TGEnums.MODIFIER_FRAME_SIZE_MODE.WEIGHT_PAIRS,
                          TGEnums.MODIFIER_FRAME_SIZE_MODE.QUAD_GAUSSIAN,
                          TGEnums.MODIFIER_FRAME_SIZE_MODE.CISCO,
                          TGEnums.MODIFIER_FRAME_SIZE_MODE.IMIX,
                          TGEnums.MODIFIER_FRAME_SIZE_MODE.TOLLY,
                          TGEnums.MODIFIER_FRAME_SIZE_MODE.RPRTRI,
                          TGEnums.MODIFIER_FRAME_SIZE_MODE.RPRQUAD
                          ]

        frame_size_mode = 0
        frame_size_ex_info = ""
        if self.frame_size.mode == TGEnums.MODIFIER_FRAME_SIZE_MODE.FIXED:
            frame_size_mode = 0
        elif self.frame_size.mode in rand_type_list:
            frame_size_mode = 1
            self._update_field(self.frame_size._min, "frameSizeMIN")
            self._update_field(self.frame_size._max, "frameSizeMAX")

            random_type = 0
            random_type_ex_info = ""
            if self.frame_size.mode == TGEnums.MODIFIER_FRAME_SIZE_MODE.WEIGHT_PAIRS:
                random_type = 1
                self._stream_driver_obj.weightedRandomFramesize.ix_set_default()
                self._update_field(driver_field="frameSizeType", value=frame_size_mode,
                                   exception_info=frame_size_ex_info)
                self._update_field(driver_field="weightedRandomFramesize.randomType", value=random_type,
                                   exception_info=random_type_ex_info)

                for pair in self.frame_size.weight_pairs_list:
                    size, weight = pair.split(",")
                    self._stream_driver_obj.weightedRandomFramesize.addPair(size,weight)
                self._stream_driver_obj.weightedRandomFramesize.delPair(64, 1)

            elif self.frame_size.mode == TGEnums.MODIFIER_FRAME_SIZE_MODE.QUAD_GAUSSIAN:
                random_type = 3
                self._update_field(driver_field="frameSizeType", value=frame_size_mode,
                                   exception_info=frame_size_ex_info)
                self._update_field(driver_field="weightedRandomFramesize.randomType", value=random_type,
                                   exception_info=random_type_ex_info)
                curve_id = 1
                for struct in self.frame_size.quad_gaussian_list:
                    center, width, weight = struct.split(",")
                    self._stream_driver_obj.weightedRandomFramesize.center = center
                    self._stream_driver_obj.weightedRandomFramesize.widthAtHalf = width
                    self._stream_driver_obj.weightedRandomFramesize.weight = weight
                    self._stream_driver_obj.weightedRandomFramesize.updateQuadGaussianCurve(curve_id)
                    curve_id += 1

            elif self.frame_size.mode == TGEnums.MODIFIER_FRAME_SIZE_MODE.CISCO:
                random_type = 4
            elif self.frame_size.mode == TGEnums.MODIFIER_FRAME_SIZE_MODE.IMIX:
                random_type = 5
            elif self.frame_size.mode == TGEnums.MODIFIER_FRAME_SIZE_MODE.TOLLY:
                random_type = 7
            elif self.frame_size.mode == TGEnums.MODIFIER_FRAME_SIZE_MODE.RPRTRI:
                random_type = 8
            elif self.frame_size.mode == TGEnums.MODIFIER_FRAME_SIZE_MODE.RPRQUAD:
                random_type = 9
            self._update_field(driver_field="weightedRandomFramesize.randomType", value=random_type,
                               exception_info=random_type_ex_info)
        elif self.frame_size.mode == TGEnums.MODIFIER_FRAME_SIZE_MODE.INCREMENT:
            frame_size_mode = 2
            self._update_field(self.frame_size._min, "frameSizeMIN")
            self._update_field(self.frame_size._max, "frameSizeMAX")
            self._update_field(self.frame_size._step, "frameSizeStep")
        elif self.frame_size.mode == TGEnums.MODIFIER_FRAME_SIZE_MODE.AUTO:
            frame_size_mode = 3
        self._update_field(driver_field="frameSizeType", value=frame_size_mode, exception_info=frame_size_ex_info)



        #weightedRandomFramesize.randomType = 1

    def _apply_data_integrity(self):
        di_rx_supported = bool(int(self._parent._port_driver_obj.isValidFeature(IxExEnums.IxiaFeatures.portFeatureRxDataIntegrity.name)))
        if di_rx_supported:
            self._update_field(self.packet.data_integrity._enable, "dataIntegrity.insertSignature")
            self._update_field(self.packet.data_integrity._enable_time_stamp, "dataIntegrity.enableTimeStamp")
            self._update_field(self.packet.data_integrity._signature, "dataIntegrity.signature")
            self._update_field(self.packet.data_integrity._signature_offset, "dataIntegrity.signatureOffset")

            self._update_field(self.instrumentation._automatic_enabled,
                               "autoDetectInstrumentation.enableTxAutomaticInstrumentation")
            self._update_field(self.instrumentation._time_stamp_enabled, "enableTimestamp")
            self._stream_driver_obj.packetGroup.ix_set_default()
            self._update_field(self.instrumentation._packet_groups_enabled, "packetGroup.insertSignature")
            self._update_field(self.instrumentation._sequence_checking_enabled, "packetGroup.insertSequenceSignature")
            if self.instrumentation.packet_group.enable_group_id is not None:
                self._update_field(self.instrumentation.packet_group._enable_group_id, "packetGroup.enableInsertPgid")
                self._update_field(self.instrumentation.packet_group._group_id, "packetGroup.groupId")



    def _apply_udfs(self):
        counter = 1
        nested_mode_counter = 5
        for id,udf in enumerate(self.packet.modifiers):
            curUdf = self.packet.modifiers[udf]
            self._stream_driver_obj.udf.ix_set_default()
            self._update_field(driver_field="udf.enable", value=curUdf.enabled)
            self._update_field(driver_field="udf.offset", value=curUdf.byte_offset)
            self._update_field(driver_field="udf.bitOffset", value=curUdf.bit_offset)
            self._update_field(driver_field="udf.counterMode", value=IxExEnums.TGEnums_IxExEnums_map(curUdf.mode,IxExEnums.UDF_COUNTER_MODE))
            self._update_field(driver_field="udf.udfSize", value=curUdf.bit_type.value)
            self._update_field(driver_field="udf.repeat", value=curUdf.repeat_count)
            self._update_field(driver_field="udf.continuousCount", value= curUdf.continuously_counting)
            self._update_field(driver_field="udf.initval", value='{'+curUdf.repeat_init+'}')
            self._update_field(driver_field="udf.updown", value=IxExEnums.TGEnums_IxExEnums_map(curUdf.repeat_mode,IxExEnums.UDF_REPEAT_MODE))
            self._update_field(driver_field="udf.step", value=curUdf.repeat_step)
            self._update_field(driver_field="udf.chainFrom", value=curUdf.from_chain.value)
            if curUdf.mode is TGEnums.MODIFIER_UDF_MODE.VALUE_LIST:
                self._update_field(driver_field="udf.valueList", value=curUdf.value_list)
            if curUdf.mode is TGEnums.MODIFIER_UDF_MODE.NESTED_COUNTER:
                self._update_field(driver_field="udf.innerLoop", value=curUdf.inner_repeat_loop)
                self._update_field(driver_field="udf.innerRepeat", value=curUdf.inner_repeat_count)
                self._update_field(driver_field="udf.innerStep", value=curUdf.inner_repeat_step)
                self._stream_driver_obj.udf.set(nested_mode_counter)
                nested_mode_counter -= 1
            else :
                self._stream_driver_obj.udf.set(counter)
                counter += 1
        self._stream_driver_obj.ix_set()

    def _hw_sync(self):
        ############################## mac ##############################
        self.packet.mac.da.value = self._rgetattr(self._stream_driver_obj, "da")
        self.packet.mac.da.count = self._rgetattr(self._stream_driver_obj, "numDA")
        self.packet.mac.da.step = self._rgetattr(self._stream_driver_obj, "daStep")
        self.packet.mac.da.mode = IxExEnums.IxExEnums_TGEnums_map(
            IxExEnums.MODIFIER_MAC_MODE(
                int(self._rgetattr(self._stream_driver_obj, "daRepeatCounter"))),TGEnums.MODIFIER_MAC_MODE)


        self.packet.mac.sa.value = self._rgetattr(self._stream_driver_obj,"sa")
        self.packet.mac.sa.count = self._rgetattr(self._stream_driver_obj, "numSA")
        self.packet.mac.sa.step = self._rgetattr(self._stream_driver_obj, "saStep")
        self.packet.mac.sa.mode = IxExEnums.IxExEnums_TGEnums_map(
            IxExEnums.MODIFIER_MAC_MODE(
                int(self._rgetattr(self._stream_driver_obj, "saRepeatCounter"))),TGEnums.MODIFIER_MAC_MODE)


        self.packet.mac.fcs = IxExEnums.IxExEnums_TGEnums_map(
            IxExEnums.FCS_ERRORS_MODE(
                int(self._rgetattr(self._stream_driver_obj, "fcs"))),TGEnums.FCS_ERRORS_MODE)

        ############################## ipv4 ##############################
        self.packet.ipv4.source_ip.value = self._rgetattr(self._stream_driver_obj, "ip.sourceIpAddr")
        self.packet.ipv4.source_ip.count = self._rgetattr(self._stream_driver_obj, "ip.sourceIpAddrRepeatCount")
        self.packet.ipv4.source_ip.mode = IxExEnums.IxExEnums_TGEnums_map(
            IxExEnums.MODIFIER_IPV4_ADDRESS_MODE(
                int(self._rgetattr(self._stream_driver_obj, "ip.sourceIpAddrMode"))),TGEnums.MODIFIER_IPV4_ADDRESS_MODE)

        self.packet.ipv4.destination_ip.value = self._rgetattr(self._stream_driver_obj, "ip.destIpAddr")
        self.packet.ipv4.destination_ip.count = self._rgetattr(self._stream_driver_obj, "ip.destIpAddrRepeatCount")
        self.packet.ipv4.destination_ip.mode = IxExEnums.IxExEnums_TGEnums_map(
            IxExEnums.MODIFIER_IPV4_ADDRESS_MODE(
                int(self._rgetattr(self._stream_driver_obj, "ip.destIpAddrMode"))),
            TGEnums.MODIFIER_IPV4_ADDRESS_MODE)


        self.packet.ipv4.ttl = self._rgetattr(self._stream_driver_obj, "ip.ttl")
        self.packet.ipv4.enable_header_len_override = self._rgetattr(self._stream_driver_obj, "ip.enableHeaderLengthOverride")
        #todo issue with ip.headerLength
        header_len_override_value_temp = self._rgetattr(self._stream_driver_obj, "ip.headerLength")
        if len(header_len_override_value_temp) > 0:
            if len (header_len_override_value_temp) == 2:
                header_len_override_value_temp = str(int(header_len_override_value_temp)/4)
                self.packet.ipv4._header_len_override_value.current_val = header_len_override_value_temp
            else:
                header_len_override_value_temp_len = len(header_len_override_value_temp)/4
                header_len_override_value_temp = header_len_override_value_temp[:header_len_override_value_temp_len]
                header_len_override_value_temp = str(int(header_len_override_value_temp)/4)
                self.packet.ipv4._header_len_override_value.current_val = header_len_override_value_temp
        else:
            self.packet.ipv4.header_len_override_value = ''
        self.packet.ipv4.identifier = self._rgetattr(self._stream_driver_obj, "ip.identifier")
        # self.packet.ipv4.options_padding = self._rgetattr(self._stream_driver_obj, "ip.options")
        self.packet.ipv4.length_override = self._rgetattr(self._stream_driver_obj, "ip.lengthOverride")
        self.packet.ipv4.length_value = self._rgetattr(self._stream_driver_obj, "ip.totalLength")
        self.packet.ipv4.fragment_enable = not self._rgetattr(self._stream_driver_obj, "ip.fragment")
        self.packet.ipv4.fragment_last_enable = not self._rgetattr(self._stream_driver_obj, "ip.lastFragment")
        self.packet.ipv4.fragment_offset_decimal_value = self._rgetattr(self._stream_driver_obj, "ip.fragmentOffset")
        self.packet.ipv4.protocol = self._rgetattr(self._stream_driver_obj, "ip.ipProtocol")

    def _get_stream_stats(self):
        stats = IxeStreamsStats(self._stream_driver_obj.session)
        stats.read_stats()
        self._IxExStreamStats_dict = stats.statistics[str(self._stream_driver_obj)]
        return stats

    def get_stats(self):
        '''
        Updates stream stats from HW to stream.stats members
            :rtype: OrderedDict
            :return: dict of the stream stats as received from HW (some manipulated stats may not appear)
        '''
        self._logger.info(self._get_stream_log_title(), self._get_stream_log_message(), True)
        super(self.__class__, self).get_stats()
        stats = self._get_stream_stats()
        self._update_stream_stats(stats)
        statistics_str = str(self.statistics)
        statistics_dict = json.loads(statistics_str)
        self._logger.info("tx_stats", "frames_sent:{}\nframes_sent_rate:{}".format(statistics_dict["frames_sent"].replace("\"",""), statistics_dict["frames_sent_rate"].replace("\"","")), True)
        for rx_port in statistics_dict["rx_stats"][0]:
            rx_dict = statistics_dict["rx_stats"][0][rx_port][0]
            rx_str = ""
            for key, val in rx_dict.items():
                rx_str += "{}:{}\n".format(key, val)
            rx_str = rx_str.replace("\"","")
            rx_str = rx_str.replace("\'", "")
            self._logger.info("rx_port - {}".format(rx_port), rx_str)
        self._logger.info("end_level", "end_level")
        self._logger.info("end_level", "end_level")
        return stats.statistics[str(self._stream_driver_obj)]

    def clear_stats(self):
        self._logger.info(self._get_stream_log_title(), self._get_stream_log_message())
        super(self.__class__, self).clear_stats()
        # self._stream_driver_obj.clear_stream_stats() #todo enable when added to pyixex
        self.statistics._reset_stats()

    def _update_stream_stats(self, stats):
        super(self.__class__, self)._update_stream_stats(stats)
        # after all stats has been read from HW on all streams as a dict, get only the dict of this stream
        self._IxExStreamStats_dict = stats.statistics[str(self._stream_driver_obj)]

        # set defaults for all keys in case they will not come from HW
        self._IxExStreamStats_dict.setdefault("frames_sent", '-1')
        self._IxExStreamStats_dict.setdefault("frames_sent_rate", '-1')

        # update the stream stats members with the value from HW
        self.statistics.frames_sent = str(self._IxExStreamStats_dict["tx"]["framesSent"])
        self.statistics.frames_sent_rate = str(self._IxExStreamStats_dict["tx"]["frameRate"])
        # if "rx" in self._IxExStreamStats_dict:
        temp_session_ports_dict = {}
        for session_port_name, session_port_obj in list(self._parent._parent.ports.items()):
            temp_session_ports_dict[session_port_obj._port_uri] = session_port_name

        temp_rx_ports_dict = self._IxExStreamStats_dict["rx"]
        for rx_port_stat in temp_rx_ports_dict:
            port_uri = rx_port_stat
            # port_name = temp_session_ports_dict[port_uri]
            port_name = temp_session_ports_dict.get(port_uri,port_uri) # get the name by name as key, else the key is the uri
            port_dict = _RX_PORT_STATS()
            port_dict.average_latency = temp_rx_ports_dict[port_uri].get('averageLatency','-1')
            port_dict.big_sequence_error = temp_rx_ports_dict[port_uri].get('bigSequenceError','-1')
            port_dict.bit_rate = temp_rx_ports_dict[port_uri].get('bitRate','-1')
            port_dict.byte_rate = temp_rx_ports_dict[port_uri].get('byteRate','-1')
            port_dict.duplicate_frames = temp_rx_ports_dict[port_uri].get('duplicateFrames','-1')
            port_dict.first_time_stamp = temp_rx_ports_dict[port_uri].get('firstTimeStamp','-1')
            port_dict.frame_rate = temp_rx_ports_dict[port_uri].get('frameRate','-1')
            port_dict.last_time_stamp = temp_rx_ports_dict[port_uri].get('lastTimeStamp','-1')
            port_dict.max_delay_variation = temp_rx_ports_dict[port_uri].get('maxDelayVariation','-1')
            port_dict.max_latency = temp_rx_ports_dict[port_uri].get('maxLatency','-1')
            port_dict.max_min_delay_variation = temp_rx_ports_dict[port_uri].get('maxMinDelayVariation','-1')
            port_dict.maxmin_interval = temp_rx_ports_dict[port_uri].get('maxminInterval','-1')
            port_dict.min_delay_variation = temp_rx_ports_dict[port_uri].get('minDelayVariation','-1')
            port_dict.min_latency = temp_rx_ports_dict[port_uri].get('minLatency','-1')
            port_dict.num_groups = temp_rx_ports_dict[port_uri].get('numGroups','-1')
            port_dict.prbs_ber_ratio = temp_rx_ports_dict[port_uri].get('prbsBerRatio','-1')
            port_dict.prbs_bits_received = temp_rx_ports_dict[port_uri].get('prbsBitsReceived','-1')
            port_dict.prbs_errored_bits = temp_rx_ports_dict[port_uri].get('prbsErroredBits','-1')
            port_dict.read_time_stamp = temp_rx_ports_dict[port_uri].get('readTimeStamp','-1')
            port_dict.reverse_sequence_error = temp_rx_ports_dict[port_uri].get('reverseSequenceError','-1')
            port_dict.sequence_gaps = temp_rx_ports_dict[port_uri].get('sequenceGaps','-1')
            port_dict.small_sequence_error = temp_rx_ports_dict[port_uri].get('smallSequenceError','-1')
            port_dict.standard_deviation = temp_rx_ports_dict[port_uri].get('standardDeviation','-1')
            port_dict.total_byte_count = temp_rx_ports_dict[port_uri].get('totalByteCount','-1')
            port_dict.total_frames = temp_rx_ports_dict[port_uri].get('totalFrames','-1')
            port_dict.total_sequence_error = temp_rx_ports_dict[port_uri].get('totalSequenceError','-1')
            self.statistics.rx_ports[port_name] = port_dict
