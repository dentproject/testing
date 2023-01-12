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

import functools

from pypacker.layer12.ethernet import Ethernet, Dot1Q
from pypacker.layer12.arp import ARP
from pypacker.layer3.ip6 import IP6
from pypacker.layer3.ip import IP
from pypacker.layer4.tcp import TCP
from pypacker.layer4.udp import UDP


from UnifiedTG.Unified.Stream import Stream, _RATE_CONTROL
from UnifiedTG.Unified.TGEnums import TGEnums
from UnifiedTG.Unified.Utils import attrWithDefault
from UnifiedTG.Xena.XenaDriver import xenaUpdater
from UnifiedTG.Xena.XenaEnums import XenaEnums
from UnifiedTG.Unified.Utils import Converter


class xenaStream(Stream,xenaUpdater):
    _continious_flag = False

    def __init__(self,s_name):
        super(self.__class__, self).__init__(s_name)
        self.rate = _xenaRATE_CONTROL()
        self._tpldid = attrWithDefault(-1)
        self._headers = None

    def apply(self, apply_to_hw=False, selective_update=True):
        self._logger.info(self._get_stream_log_title(), self._get_stream_log_message())
        super(self.__class__, self).apply()
        #disable tplid by default
        self._update_field(self._tpldid, 'PS_TPLDID')

    def _config_field_modifier(self, offset, field):
        count = int(field.count)
        step = int(field.step) if field.step != 'None' else 1
        if field.mode.name.count('CONTINUOUS_INCREMENT'):
            md = TGEnums.MODIFIER_UDF_REPEAT_MODE.UP
        elif field.mode.name.count('INCREMENT'):
            md = TGEnums.MODIFIER_UDF_REPEAT_MODE.UP
        elif field.mode.name.count('CONTINUOUS_DECREMENT'):
            md = TGEnums.MODIFIER_UDF_REPEAT_MODE.DOWN
        elif field.mode.name.count('DECREMENT'):
            md = TGEnums.MODIFIER_UDF_REPEAT_MODE.DOWN
        elif field.mode.name.count('FIXED') and field._driver_obj:
            self._remove_modifier(field._driver_obj.id)
            return
        else:
            return
        self._add_update_modifier(field, offset=offset, count=count, mode=md, initVal=field.value, step=step)


    def _add_update_modifier(self, field, offset, count=None, mode=TGEnums.MODIFIER_UDF_REPEAT_MODE.UP, initVal='0', step=1):
        from xenavalkyrie.xena_stream import XenaModifierAction
        sMask = '0xFFFF0000'
        rep = 1
        smMaxVal = 0xFFFF
        startValue = Converter.convertstring2int(initVal)
        startValue &= 0xFFFF
        adapter = 1 #if step > 1 else 1
        if mode is TGEnums.MODIFIER_UDF_REPEAT_MODE.UP:
            mode = XenaModifierAction.increment
            minVal = startValue
            maxVal = smMaxVal-1 if count is None else startValue+step*(count-adapter)
        else:
            mode = XenaModifierAction.decrement
            maxVal = startValue
            minVal = 0 if count is None else startValue-count*step+adapter
        if not field._driver_obj:
            field._driver_obj = self._stream_driver_obj.add_modifier(position=offset,mask=sMask,action=mode,repeat=rep,min_val=minVal,step=step,max_val=maxVal)
        else:
            field._driver_obj.update(position=offset, mask=sMask, action=mode, repeat=rep, min_val=minVal, step=step, max_val=maxVal)


    def _remove_modifier(self,index):
        self._stream_driver_obj.remove_modifier(index)

    def _apply_mac(self):
        pass  # TODO PACKET BUILDER
        eth = Ethernet(src_s=self.packet.mac.sa.value)
        eth.dst_s = self.packet.mac.da.value
        #TODO fix ethertype
        if self.packet.l2_proto == TGEnums.L2_PROTO.ETHERNETII:
            if self.packet.ethertype != self.packet._ethertype._default_val:
                eth.type = int(self.packet.ethertype, 16)
        else:
            eth.type = None
        self._headers = eth
        self._config_field_modifier(4, self.packet.mac.da)
        self._config_field_modifier(10, self.packet.mac.sa)
        if len(self.packet.vlans) > 0:
            for vlan in self.packet.vlans:
                vid = int(self.packet.vlans[vlan].vid.value)
                cfi = int(self.packet.vlans[vlan].cfi)
                prio = self.packet.vlans[vlan].priority
                vlanObj = Dot1Q(vid=vid,cfi = cfi,prio = prio)
                eth.vlan.append(vlanObj)

    def _apply_ethertype(self):
        pass
        # inside mac

    def _apply_vlans(self):
        pass
        #inside mac

    def _apply_l2_proto(self):
        pass  # TODO

    def _apply_l3_proto(self):
        pass

    def _apply_l4_proto(self):
        pass

    def _apply_ipv4(self):

        headerObj = IP(tos=int(self.packet.ipv4.dscp_decimal_value, 10),  # TODO FIX SHIFT ECN
                       id=int(self.packet.ipv4.identifier),
                       off=int(self.packet.ipv4.fragment_offset_decimal_value),
                       ttl=int(self.packet.ipv4.ttl),
                       p=int(self.packet.ipv4.protocol),
                       src_s=self.packet.ipv4.source_ip.value,
                       dst_s=self.packet.ipv4.destination_ip.value
                       )
        # handle automatic fields & options TODO
        # v_hl ,sum and opts

        header_offset = len(self._headers)
        self._headers += headerObj

        if self.packet.ipv4.destination_ip.mode is not TGEnums.MODIFIER_IPV4_ADDRESS_MODE.FIXED:
            self._config_field_modifier(header_offset + 18, self.packet.ipv4.destination_ip)
        if self.packet.ipv4.source_ip.mode is not TGEnums.MODIFIER_IPV4_ADDRESS_MODE.FIXED:
            self._config_field_modifier(header_offset + 14, self.packet.ipv4.source_ip)

    def _apply_ipv6(self):
        pass  # TODO

    def _apply_tcp(self):

        flags_list = [int(self.packet.tcp.flag_urgent_pointer_valid),
                      int(self.packet.tcp.flag_acknowledge_valid),
                      int(self.packet.tcp.flag_push_function),
                      int(self.packet.tcp.flag_reset_connection),
                      int(self.packet.tcp.flag_synchronize_sequence),
                      int(self.packet.tcp.flag_no_more_data_from_sender)]
        flags = functools.reduce(lambda out,x: (out<<1)+int(x),flags_list,0)

        header_obj = TCP(sport=int(self.packet.tcp.source_port.value),
                         dport=int(self.packet.tcp.destination_port.value),
                         seq=Converter.hexaString2int(self.packet.tcp.sequence_number),
                         ack=Converter.hexaString2int(self.packet.tcp.acknowledgement_number),
                         #off_x2 TODO
                         flags = flags,
                         win = Converter.hexaString2int(self.packet.tcp.window),
                         #sum TODO
                         urp=Converter.hexaString2int(self.packet.tcp.urgent_pointer)
                         #opts TODO
                         )
        self._headers += header_obj


    def _apply_udp(self):

        header_obj = UDP(sport=int(self.packet.udp.source_port.value),
                         dport=int(self.packet.udp.destination_port.value)
                         #ulen= , TODO
                         #sum= ,TODO
                        )
        self._headers += header_obj


    def _apply_data_pattern(self):

        self._stream_driver_obj.set_packet_headers(self._headers)
        port_pl_mode = XenaEnums.PORT_PAYLOAD_MODE.NORMAL
        cmd = 'PS_PAYLOAD'
        param = ''
        pl = self.packet.data_pattern.value
        if self.packet.data_pattern.type is TGEnums.DATA_PATTERN_TYPE.FIXED:
            param = pl+'0' if len(pl)%2 else pl
            param = '0x'+ param
            port_pl_mode = XenaEnums.PORT_PAYLOAD_MODE.EXTPL
            cmd = 'PS_EXTPAYLOAD'
        elif self.packet.data_pattern.type is TGEnums.DATA_PATTERN_TYPE.REPEATING:
            const_xena_repeat = 36
            while len(pl) < const_xena_repeat:
                pl+=pl
            param = 'PATTERN' + ' 0x'+ pl[:const_xena_repeat]
        elif self.packet.data_pattern.type is TGEnums.DATA_PATTERN_TYPE.INCREMENT_BYTE:
            param = 'INCREMENTING'
        elif self.packet.data_pattern.type is TGEnums.DATA_PATTERN_TYPE.INCREMENT_WORD:
            param = 'INCREMENTING'
        elif self.packet.data_pattern.type is TGEnums.DATA_PATTERN_TYPE.RANDOM:
            param = 'RANDOM'
        self._parent.payload_mode = port_pl_mode
        if not self._update_field(self.packet.data_pattern._type,cmd,param):
            self._update_field(self.packet.data_pattern._value,cmd, param)

    def _apply_preamble_size(self):
        pass  # TODO

    def _apply_protocol_offset(self):
        pass  # TODO

    def _apply_stream_rate(self):

        if self.rate.mode == TGEnums.STREAM_RATE_MODE.INTER_PACKET_GAP:
            pass # TODO
            # rate_mode = 0
            # gap_unit = 0
            # if self.rate._inter_packet_gap_mode.current_val == TGEnums.STREAM_RATE_INTER_PACKET_GAP_MODE.NANOSECONDS:
            #     gap_unit = 0
            # elif self.rate._inter_packet_gap_mode.current_val == TGEnums.STREAM_RATE_INTER_PACKET_GAP_MODE.MICROSECONDS:
            #     gap_unit = 1
            # elif self.rate._inter_packet_gap_mode.current_val == TGEnums.STREAM_RATE_INTER_PACKET_GAP_MODE.MILLISECONDS:
            #     gap_unit = 2
            # elif self.rate._inter_packet_gap_mode.current_val == TGEnums.STREAM_RATE_INTER_PACKET_GAP_MODE.SECONDS:
            #     gap_unit = 3
            # elif self.rate._inter_packet_gap_mode.current_val == TGEnums.STREAM_RATE_INTER_PACKET_GAP_MODE.BYTES:
            #     gap_unit = 5
            # self._update_field(driver_field="rateMode", value=rate_mode)
            # self._update_field(driver_field="gapUnit", value=gap_unit)
            # self._update_field(driver_field="ifg", value=self.rate._ipg_value)
        elif self.rate.mode == TGEnums.STREAM_RATE_MODE.UTILIZATION:
            self._update_field(self.rate._utilization_value,"PS_RATEFRACTION")
        elif self.rate.mode == TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND:
            self._update_field(self.rate._pps_value,"PS_RATEPPS")
        elif self.rate.mode == TGEnums.STREAM_RATE_MODE.BITRATE_PER_SECOND:
            self._update_field(self.rate._bitrate_value,"PS_RATEL2BPS")

    def _apply_stream_control(self):
        if self.control.mode == TGEnums.STREAM_TRANSMIT_MODE.CONTINUOUS_PACKET or self.control.mode == TGEnums.STREAM_TRANSMIT_MODE.CONTINUOUS_BURST:
            self._update_field(self.control._packets_per_burst, 'PS_PACKETLIMIT',value= '-1')
        else:
            self._update_field(self.control._packets_per_burst, 'PS_PACKETLIMIT',always_write=True)

    def _apply_stream_status(self):
        self._update_field(self._enabled, "PS_ENABLE", value='ON' if self._enabled else 'SUPPRESS')

    def _apply_frame_size(self):

        rand_type_list = [TGEnums.MODIFIER_FRAME_SIZE_MODE.RANDOM
                          # TGEnums.MODIFIER_FRAME_SIZE_MODE.WEIGHT_PAIRS,
                          # TGEnums.MODIFIER_FRAME_SIZE_MODE.QUAD_GAUSSIAN,
                          # TGEnums.MODIFIER_FRAME_SIZE_MODE.CISCO,
                          # TGEnums.MODIFIER_FRAME_SIZE_MODE.IMIX,
                          # TGEnums.MODIFIER_FRAME_SIZE_MODE.TOLLY,
                          # TGEnums.MODIFIER_FRAME_SIZE_MODE.RPRTRI,
                          # TGEnums.MODIFIER_FRAME_SIZE_MODE.RPRQUAD
                          ]
        if self.frame_size.mode == TGEnums.MODIFIER_FRAME_SIZE_MODE.FIXED:
            params = 'FIXED '+str(self.frame_size.value) + ' ' + str(1518)
        elif self.frame_size.mode in rand_type_list:
            params = 'RANDOM ' + str(self.frame_size.min) + ' ' + str(self.frame_size.max)
        elif self.frame_size.mode == TGEnums.MODIFIER_FRAME_SIZE_MODE.INCREMENT:
            params = 'INCREMENTING ' + str(self.frame_size.min) + ' ' + str(self.frame_size.max)
        elif self.frame_size.mode == TGEnums.MODIFIER_FRAME_SIZE_MODE.AUTO:
            params = 'MIX ' + str(self.frame_size.min) + ' ' + str(self.frame_size.max)
        self._update_field(self.frame_size._value, "PS_PACKETLENGTH", params)

    # def _apply_data_integrity(self):
        # TODO

    def _apply_udfs(self):
        for udf in self.packet.modifiers:
            curUdf = self.packet.modifiers[udf]
            if curUdf.enabled == True:
                count = None if curUdf.continuously_counting else curUdf.repeat_count
                self._add_update_modifier(curUdf,offset=curUdf.byte_offset, count=count, mode=curUdf.repeat_mode, initVal=curUdf.repeat_init, step=curUdf.repeat_step)
            elif curUdf._driver_obj:
                self._stream_driver_obj.remove_modifier(curUdf._driver_obj.id)


    def _get_stream_stats(self):
        pass  # TODO

    def get_stats(self):
        pass  # TODO


    def clear_stats(self):
        self._logger.info(self._get_stream_log_title(), self._get_stream_log_message())
        super(self.__class__, self).clear_stats()
        # self._stream_driver_obj.clear_stream_stats() #todo enable when added to pyixex
        self.statistics._reset_stats()

    def _update_stream_stats(self, stats):
        pass #TODO

class _xenaRATE_CONTROL(_RATE_CONTROL):
    def __init__(self):
        super(self.__class__, self).__init__()
        self._utilization_value = attrWithDefault(1000000)

    @property
    def utilization_value(self):
        """utilization_value : """
        return str(self._utilization_value.current_val/10000)

    @utilization_value.setter
    def utilization_value(self, v):
        """utilization_value : """
        self._utilization_value.current_val = int(v)*10000
