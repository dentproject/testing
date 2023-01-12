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

from UnifiedTG.Unified.TGEnums import TGEnums
from UnifiedTG.Unified.Stream import Stream
from UnifiedTG.Unified.Utils import Converter
from UnifiedTG.Unified.Packet import Packet

from UnifiedTG.PacketBuilder.mpls import MPLS
from testcenter.stc_frame import StcFrame_Layers


class spirentStream(Stream):

    def __init__(self,s_name):
        super(self.__class__, self).__init__(s_name)

    def apply(self,apply_to_hw = False, selective_update=True):
        self._stream_driver_obj.clear_frame_config()
        super(self.__class__, self).apply()
        if apply_to_hw:
            self._stream_driver_obj.write()
    #
    def _apply_mac(self):
        s = self._stream_driver_obj.frame
        s.L2.set_type(StcFrame_Layers.DataLinkLayer.Eth2)
        s.L2.update_fields(dstMac=self.packet.mac.da.value, srcMac=self.packet.mac.sa.value)
        #TODO handle modifiers

    #
    # def _apply_ethertype(self):
    #     pass
    #
    def _apply_l2_proto(self):
        s = self._stream_driver_obj.frame  # type: StcStream()
        if self.packet.l2_proto == TGEnums.L2_PROTO.ETHERNETII:
            if self.packet.ethertype != self.packet._ethertype._default_val :
                s.L2.update_fields(etherType = self.packet.ethertype)
                #stc_mac.set_attributes(etherType = self.packet.ethertype)
        #TODO non ETHERNETII types..
    #
    def _apply_vlans(self):

        if len(self.packet.vlans) > 0:
            if len(self.packet.vlans) == 1:
                utg_vlan = self.packet.vlans.items()[0][1]
                sp_vlan = self._stream_driver_obj.frame.L2.add_vlan(cfi=utg_vlan.cfi,
                                                           id=utg_vlan.vid.value,
                                                           Name=utg_vlan._name,
                                                           pri=utg_vlan.priority,
                                                           type=utg_vlan.proto)
            elif len(self.packet.vlans) == 2:
                pass
    #
    #
    # def _apply_mpls(self):
    #    pass
    #
    # def _apply_l3_proto(self):
    #     pass
    #
    # def _apply_l4_proto(self):
    #     pass
    #

    def _update_v4_fields(self, source_obj, dest_obj):
        dest_obj.update_fields( destAddr= source_obj.destination_ip.value,
                                sourceAddr= source_obj.source_ip.value,
                                ttl=source_obj.ttl,
                                identification=source_obj.identifier
                               )
        #TODO TOS/DSCP,control flags,options
    #
    def _apply_ipv4(self, source_obj = None):
        source_obj = self.packet.ipv4 if not source_obj else source_obj
        sp_obj = self._stream_driver_obj.frame #type: StcStream()
        sp_obj.L3.set_type(StcFrame_Layers.UpperLayerProtocols_I.IpV4)
        self._update_v4_fields(source_obj, sp_obj.L3)
    #
#todo v6,l4(tcp,udp)

    def _apply_data_pattern(self):
        sp_obj = self._stream_driver_obj.frame #type: StcStream()
        if self.packet.data_pattern.type is TGEnums.DATA_PATTERN_TYPE.FIXED:
            #!!! currently custom type not supported by 400G ,used custom header instead
            pl = Converter.remove_non_hexa_sumbols(self.packet.data_pattern.value)
            sp_obj.add_header(StcFrame_Layers.UpperLayerProtocols_II.Custom, pattern=pl)
            #sp_obj.Payload.update_fields(pattern=self.packet.data_pattern.value)
            # pl = self.packet.data_pattern.value
            # res = ''
            # lst = pl.split()
            # for x in lst:
            #     r = Converter.convertstring2int(x)
            #     res += str(r)
            #     res += ' '
            # self._stream_driver_obj.frame.custom_pl(res)
            return
        elif self.packet.data_pattern.type is TGEnums.DATA_PATTERN_TYPE.INCREMENT_BYTE \
                or self.packet.data_pattern.type is TGEnums.DATA_PATTERN_TYPE.INCREMENT_WORD:
            fill_type = 'INCR'
            data = 0
        elif self.packet.data_pattern.type is TGEnums.DATA_PATTERN_TYPE.DECREMENT_BYTE\
                or self.packet.data_pattern.type is TGEnums.DATA_PATTERN_TYPE.DECREMENT_WORD:
            fill_type = 'DECR'
            data = 0
        elif self.packet.data_pattern.type is TGEnums.DATA_PATTERN_TYPE.REPEATING:
            fill_type = 'CONSTANT'
            int_pl = Converter.convertstring2int(self.packet.data_pattern.value)
            data = int_pl
        self._stream_driver_obj.set_attributes(FillType=fill_type, ConstantFillPattern=data)


    def _apply_stream_rate(self):
        if self.rate.mode == TGEnums.STREAM_RATE_MODE.INTER_PACKET_GAP:
            if self.rate._inter_packet_gap_mode.current_val == TGEnums.STREAM_RATE_INTER_PACKET_GAP_MODE.NANOSECONDS:
                gap_unit = 'NANOSECONDS'
            elif self.rate._inter_packet_gap_mode.current_val == TGEnums.STREAM_RATE_INTER_PACKET_GAP_MODE.MICROSECONDS:
                pass #not supported
            elif self.rate._inter_packet_gap_mode.current_val == TGEnums.STREAM_RATE_INTER_PACKET_GAP_MODE.MILLISECONDS:
                gap_unit = 'MILLISECONDS'
            elif self.rate._inter_packet_gap_mode.current_val == TGEnums.STREAM_RATE_INTER_PACKET_GAP_MODE.SECONDS:
                pass  # not supported
            elif self.rate._inter_packet_gap_mode.current_val == TGEnums.STREAM_RATE_INTER_PACKET_GAP_MODE.BYTES:
                gap_unit = 'BYTES'
            ifg_mode = gap_unit
            ifg_value= self.rate.ipg_value
        elif self.rate.mode == TGEnums.STREAM_RATE_MODE.UTILIZATION:
            ifg_mode = 'PERCENT_LINE_RATE'
            ifg_value= self.rate.utilization_value
        elif self.rate.mode == TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND:
            ifg_mode = 'FRAMES_PER_SECOND'
            ifg_value = self.rate.pps_value
        elif self.rate.mode == TGEnums.STREAM_RATE_MODE.BITRATE_PER_SECOND:
            ifg_mode = 'BITS_PER_SECOND'
            ifg_value = self.rate.pps_value
        if self._parent.properties.transmit_mode is TGEnums.PORT_PROPERTIES_TRANSMIT_MODES.PORT_BASED:
            self._stream_driver_obj.set_stream_control(LoadUnit=ifg_mode, LoadMode="FIXED", FixedLoad=ifg_value)
        else:
            self._stream_driver_obj.set_stream_control(InterFrameGapUnit=ifg_mode, InterFrameGap=ifg_value)
    #
    def _apply_stream_control(self):
        config_data = {}
        cont = 0
        dm = 'BURSTS'
        burst= self.control.packets_per_burst
        if self.control.mode == TGEnums.STREAM_TRANSMIT_MODE.CONTINUOUS_PACKET:
            cont = 1
            dm = 'CONTINUOUS'
            burst = 1
        #elif self.control.mode == TGEnums.STREAM_TRANSMIT_MODE.CONTINUOUS_BURST:

        # elif self.control.mode == TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM:
        #     control_mode = 2
        # elif self.control.mode == TGEnums.STREAM_TRANSMIT_MODE.ADVANCE_TO_NEXT_STREAM:
        #     control_mode = 3
        # elif self.control.mode == TGEnums.STREAM_TRANSMIT_MODE.RETURN_TO_ID:
        #     control_mode = 4
        # elif self.control.mode == TGEnums.STREAM_TRANSMIT_MODE.RETURN_TO_ID_FOR_COUNT:
        #     control_mode = 5
        config_data.update(BurstSize=burst)
        if self._parent.properties.transmit_mode is TGEnums.PORT_PROPERTIES_TRANSMIT_MODES.PORT_BASED:
            config_data.update(DurationMode=dm)
            config_data.update(Duration=self.control.bursts_per_stream)
        elif self._parent.properties.transmit_mode is TGEnums.PORT_PROPERTIES_TRANSMIT_MODES.MANUAL_BASED:
            config_data.update(ContinuousTransmission=cont)
            config_data.update(BurstCount=self.control.bursts_per_stream)
            config_data.update(LoopCount=self.control.loop_count)
            #TODO sum of stremas to update port burst

        self._stream_driver_obj.set_stream_control(**config_data)



    def _apply_frame_size(self):

        frame_size_mode = 'FIXED'
        if self.frame_size.mode == TGEnums.MODIFIER_FRAME_SIZE_MODE.FIXED:
            self._stream_driver_obj.set_attributes(FixedFrameLength=self.frame_size.value)
        elif self.frame_size.mode == TGEnums.MODIFIER_FRAME_SIZE_MODE.INCREMENT:
            frame_size_mode = 'INCR'
            self._stream_driver_obj.set_attributes(MinFrameLength=self.frame_size.min,
                                                   MaxFrameLength=self.frame_size.max,
                                                   StepFrameLength=self.frame_size.step
                                                   )
        elif self.frame_size.mode == TGEnums.MODIFIER_FRAME_SIZE_MODE.AUTO:
            frame_size_mode = 'AUTO'
        elif self.frame_size.mode == TGEnums.MODIFIER_FRAME_SIZE_MODE.RANDOM:
            frame_size_mode = 'RANDOM'
            self._stream_driver_obj.set_attributes(MinFrameLength=self.frame_size.min,
                                                   MaxFrameLength=self.frame_size.max,
                                                   )
        self._stream_driver_obj.set_attributes(FrameLengthMode=frame_size_mode,InsertSig='FALSE')
    #

    # def _apply_udfs(self):
    #     for udf in self.packet.modifiers:
    #         curUdf = self.packet.modifiers[udf]
    #         if curUdf.enabled is True:
    #             p, pOffset = self._get_header_by_offset(curUdf.byte_offset)
    #             if p:
    #                 protoproto =  self._protoprotoMap[id(p)]
    #                 variable_field = protoproto.variable_field.add()
    #                 variable_field.offset = curUdf.byte_offset - pOffset
    #                 variable_field.type = int(curUdf.bit_type.value/16)
    #                 variable_field.value = Converter.stringMac2int(curUdf.repeat_init,' ')
    #                 variable_field.mode = OstinatoEnums.unified_to_ostinato(curUdf.repeat_mode)
    #                 variable_field.count = int(curUdf.repeat_count)
    #                 variable_field.step = int(curUdf.repeat_step)
    #         #variable_field.mask = 0xf0
    #     # counter = 1
    #     # for id,udf in enumerate(self.packet.modifiers):
    #     #     curUdf = self.packet.modifiers[udf]
    #     #     self._stream_driver_obj.udf.ix_set_default()
    #     #     self._update_field(driver_field="udf.enable", value=curUdf.enabled)
    #     #     self._update_field(driver_field="udf.offset", value=curUdf.byte_offset)
    #     #     self._update_field(driver_field="udf.bitOffset", value=curUdf.bit_offset)
    #     #     self._update_field(driver_field="udf.counterMode", value=IxExEnums.TGEnums_IxExEnums_map(curUdf.mode,IxExEnums.UDF_COUNTER_MODE))
    #     #     self._update_field(driver_field="udf.udfSize", value=curUdf.bit_type.value)
    #     #     self._update_field(driver_field="udf.repeat", value=curUdf.repeat_count)
    #     #     self._update_field(driver_field="udf.continuousCount", value= curUdf.continuously_counting)
    #     #     self._update_field(driver_field="udf.initval", value='{'+curUdf.repeat_init+'}')
    #     #     self._update_field(driver_field="udf.updown", value=IxExEnums.TGEnums_IxExEnums_map(curUdf.repeat_mode,IxExEnums.UDF_REPEAT_MODE))
    #     #     self._update_field(driver_field="udf.step", value=curUdf.repeat_step)
    #     #     self._stream_driver_obj.udf.set(counter)
    #     #     counter += 1
    #     # self._stream_driver_obj.ix_set()
    #
    # def _get_header_by_offset(self,offset):
    #     protocols = self._stream_driver_obj.stream.protocol._values
    #     current_offset=0
    #     for p in protocols:
    #         id = p.protocol_id.id
    #         protoSize=OstinatoEnums._converter.protoSize(id)
    #         if not isinstance(protoSize, int):
    #             return None, None
    #         protoObj = self._protoMap[id]
    #         if current_offset+protoSize > offset:
    #             return protoObj,current_offset
    #         current_offset += protoSize
        #return None,None

    def _hw_sync(self):
        pass

    def _apply_stream_status(self):
        pass

    def _apply_preamble_size(self):
        pass

    def _apply_protocol_offset(self):
        pass