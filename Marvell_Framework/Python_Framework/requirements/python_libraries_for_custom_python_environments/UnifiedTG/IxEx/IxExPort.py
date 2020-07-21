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

from ixexplorer.ixe_statistics_view import IxePortsStats, IxeStreamsStats, IxeCapFileFormat,\
    IxePortsPreemptionStats
from ixexplorer.ixe_port import StreamWarningsError
from UnifiedTG.Unified.Port import Port,trafficFilter,condition,match_term
from UnifiedTG.Unified.TG import TG
from UnifiedTG.Unified.Stream import Stream
from UnifiedTG.IxEx.IxExStream import IxExStream
from UnifiedTG.Unified.TGEnums import TGEnums
from UnifiedTG.Unified.Utils import attrWithDefault,Converter
import re
import platform
import os
from UnifiedTG.IxEx.IxExEnums import IxExEnums
import inspect
from UnifiedTG.IxEx.IxExChassis import IxExCard, IxExCard_NOVUS10, IxExCard_NOVUS100, IxExCard_K400, IxExCard_T400, \
    IxExCard_XM10_40GE12QSFP,IxExCard_STX4

# from Unified.Port import Port
# from Unified.TG import TG
# from Unified.Stream import Stream
# from IxExStream import IxExStream
# from Unified.TGEnums import TGEnums
# from Unified.Utils import attrWithDefault

from collections import OrderedDict, defaultdict
import functools

class IxExPort(Port):
    _sentinel = object()  # used for _update_field function

    def __init__(self,port_uri=None, port_name=None):
        super(self.__class__, self).__init__(port_uri, port_name)
        self._IxExPortStats_dict = OrderedDict()

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

    def _update_field(self, api_field=None, driver_field=None, value=None, exception_info=""):
        try:
            val = None
            # case 1 - field is hidden from api
            if api_field is None:
                if type(value) == attrWithDefault:
                    val = value.current_val
                else:
                    val = value
                # api_field._previous_val = api_field._current_val
                self._rsetattr(self._port_driver_obj, driver_field, val)
                if self._debug_prints: print ("updating " + driver_field)
            else:
                if not driver_field and api_field._driver_field:
                    driver_field = api_field._driver_field
                else:
                    api_field._driver_field = driver_field
                # case 2 - value was never updated in driver
                if not api_field._was_written_to_driver:
                    if value is None:
                        api_field._previous_val = api_field._current_val
                        val = api_field._current_val
                        self._rsetattr(self._port_driver_obj,driver_field, val)
                        if self._debug_prints: print ("updating " + driver_field)
                        api_field._was_written_to_driver = True
                    else:
                        if type(value) == attrWithDefault:
                            val = value.current_val
                        else:
                            val = value
                        api_field._previous_val = api_field._current_val
                        self._rsetattr(self._port_driver_obj, driver_field, val)
                        if self._debug_prints: print ("updating " + driver_field)
                        api_field._was_written_to_driver = True
                # case 3 - value is different than previous
                elif api_field._current_val != api_field._previous_val:
                    if value is None:
                        api_field._previous_val = api_field._current_val
                        val = api_field._current_val
                        self._rsetattr(self._port_driver_obj, driver_field, val)
                        if self._debug_prints: print ("updating " + driver_field)
                        api_field._was_written_to_driver = True
                    else:
                        if type(value) == attrWithDefault:
                            val = value.current_val
                        else:
                            val = value
                        self._rsetattr(self._port_driver_obj, driver_field, val)
                        if self._debug_prints: print ("updating " + driver_field)
                        api_field._was_written_to_driver = True
                else:
                    if self._debug_prints: print ("no update need for " + driver_field)
        except Exception as e:
            raise Exception("Error in update field.\nField name = " + driver_field +
                            "\nValue to set: " + str(val) +
                            "\n"+ exception_info +
                            "\n"+ str(self) +
                            "\nDriver Exeption:\n" + str(e))

    def _get_field(self,name):
        x = self._rgetattr(self._port_driver_obj, name)
        return x

    def _get_field_hw_value(self,field):
        return self._get_field(field._driver_field)

    def _udpate_autoneg_supported(self):
        anSUpported = bool(int(self._port_driver_obj.isValidFeature("portFeatureAutoNeg")))
        anActive =  bool(int(self._port_driver_obj.isActiveFeature("portFeatureAutoNeg")))
        if anSUpported and anActive:
            cardType = type(self.card)
            if cardType is IxExCard and self.properties.speed>=TGEnums.PORT_PROPERTIES_SPEED.GIGA:
                self.properties._auto_neg_adver_supported_list =\
                                [TGEnums.DUPLEX_AND_SPEED.FULL10,
                                 TGEnums.DUPLEX_AND_SPEED.HALF10,
                                 TGEnums.DUPLEX_AND_SPEED.FULL100,
                                 TGEnums.DUPLEX_AND_SPEED.HALF100,
                                 TGEnums.DUPLEX_AND_SPEED.FULL1000
                                 ]
            elif cardType is IxExCard_NOVUS10:
                if self.properties.media_type is TGEnums.PORT_PROPERTIES_MEDIA_TYPE.COPPER:
                    self.properties._auto_neg_adver_supported_list = \
                        [TGEnums.DUPLEX_AND_SPEED.FULL100,
                         TGEnums.DUPLEX_AND_SPEED.FULL1000,
                         TGEnums.DUPLEX_AND_SPEED.FULL2500,
                         TGEnums.DUPLEX_AND_SPEED.FULL5000,
                         TGEnums.DUPLEX_AND_SPEED.FULL10000
                         ]
                elif self.properties.media_type is TGEnums.PORT_PROPERTIES_MEDIA_TYPE.FIBER:
                    self.properties._auto_neg_adver_supported_list = \
                        [TGEnums.DUPLEX_AND_SPEED.FULL1000]
                elif self.properties.media_type is TGEnums.PORT_PROPERTIES_MEDIA_TYPE.SGMII:
                    self.properties._auto_neg_adver_supported_list = \
                        [TGEnums.DUPLEX_AND_SPEED.FULL100,
                         TGEnums.DUPLEX_AND_SPEED.FULL1000
                         ]
        else:
            ixAnList = [{"advertise10HalfDuplex":TGEnums.DUPLEX_AND_SPEED.HALF10},
                        {"advertise10FullDuplex": TGEnums.DUPLEX_AND_SPEED.FULL10},
                        {"advertise100HalfDuplex": TGEnums.DUPLEX_AND_SPEED.HALF100},
                        {"advertise100FullDuplex": TGEnums.DUPLEX_AND_SPEED.FULL100},
                        {"advertise1000FullDuplex": TGEnums.DUPLEX_AND_SPEED.FULL1000},
                        {"advertise2P5FullDuplex": TGEnums.DUPLEX_AND_SPEED.FULL2500},
                        {"advertise5FullDuplex": TGEnums.DUPLEX_AND_SPEED.FULL5000}]
            lastChanceList = []
            for ixAn in ixAnList:
                ixCommand,enumValue = list(ixAn.items())[0]
                res = self._get_field(ixCommand)
                supported = False if res == -1 else bool(res)
                if supported:
                    lastChanceList.append(enumValue)
            self.properties._auto_neg_adver_supported_list = lastChanceList

    def _discover(self):
        if isinstance(self.card, IxExCard_XM10_40GE12QSFP):
            self.data_integrity = None
        portType = self._port_driver_obj.type
        self.properties.port_type = portType
        self._read_speed()
        self.properties._dual_phy = bool(int(self._port_driver_obj.isValidFeature("portFeatureDualPhyMode")))
        self._read_media_type()
        self._udpate_autoneg_supported()

    def _read_media_type(self):
        if self.properties.dual_phy:
            mt= int(self._port_driver_obj.phyMode)
            if mt in TGEnums.PORT_PROPERTIES_MEDIA_TYPE._value2member_map_:
                self.properties.media_type = TGEnums.PORT_PROPERTIES_MEDIA_TYPE._value2member_map_[mt]

    def _read_speed(self):
        speedInt = self._port_driver_obj.speed
        self.properties._speed = TGEnums._converter.speed_to_SPEED(speedInt)

    def _read_link(self):
        ixlink = int(self._port_driver_obj.linkState)
        self.properties._link_state = TGEnums.Link_State._value2member_map_[ixlink] if ixlink in TGEnums.Link_State._value2member_map_ else TGEnums.Link_State.unKnown

    @property
    def rgId(self):
        if not self._rgId:
            from UnifiedTG.Unified.TgInfo import tgPortUri
            uriOb = tgPortUri(self._port_uri)
            self._rgId = self.card._get_port_rgId(uriOb.port)
        return self._rgId

    @property
    def enabled_capture(self):
        if self.rgId:
            return self.card.resourceGroups[self.rgId].enable_capture

    @enabled_capture.setter
    def enabled_capture(self,mode):
        if self.rgId:
            self.card.resourceGroups[self.rgId].enable_capture = mode


    def start_traffic(self, blocking=False, start_packet_groups=True,wait_up = None):
        blocking = blocking if not self._is_continuous_traffic() else False
        super(self.__class__, self).start_traffic(blocking=blocking, start_packet_groups=start_packet_groups, wait_up=wait_up)
        if start_packet_groups:
            self.start_packet_groups()
        self._port_driver_obj.start_transmit(blocking=blocking)

    def stop_traffic(self):
        super(self.__class__, self).stop_traffic()
        # self._port_group.stop_transmit()
        self._port_driver_obj.stop_transmit()

    def start_capture(self):
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())
        super(self.__class__, self).start_capture()
        self.enabled_capture = True
        self._port_driver_obj.start_capture()

    def stop_capture(self, cap_file_name="", cap_mode="buffer"):
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())
        TestCurrentDir = ""
        operating_system = platform.system()
        if operating_system.lower() == "windows":
            TestCurrentDir = r"c:/temp/port_1"
        elif operating_system.lower() == "linux":
            TestCurrentDir = r"/tmp/port_1"

        self.capture_buffer = []
        if cap_mode == "buffer":
            self._port_driver_obj.stop_capture(cap_file_name=None, cap_file_format=IxeCapFileFormat.mem)
            frame_count_in_buff = self._port_driver_obj.capture.nPackets
            start_frame = 1
            stop_frame = frame_count_in_buff + 1
            step_frame = 1
            res = [s for s in range(start_frame, stop_frame, step_frame)]
            temp_buff_list = self._port_driver_obj.get_cap_frames(*res)

            regex = re.compile(r"\s*|\t*", re.IGNORECASE)
            for x, line in enumerate(temp_buff_list):
                temp_buff_list[x] = regex.sub("", line)
            temp_buff_list = temp_buff_list
            self.capture_buffer = temp_buff_list
            temp_buff_list = None
        elif cap_mode == "file_buffer":
            try:
                self._port_driver_obj.stop_capture(TestCurrentDir, cap_file_format=IxeCapFileFormat.txt)
                if self._port_driver_obj.cap_file_name is not None:
                    temp_buff_list = self._port_driver_obj.get_cap_file()[2:]
                    temp_buff = '\n'.join(temp_buff_list)
                    temp_buff_list = re.findall(r'\d+\s*\d+:\d+:\d+.\d*\s*(.*)\t\d*\t',temp_buff, flags=re.MULTILINE)

                    regex = re.compile(r"\s*|\t*", re.IGNORECASE)
                    for x, line in enumerate(temp_buff_list):
                        temp_buff_list[x] = regex.sub("", line)
                    temp_buff_list = temp_buff_list
                    #\d+\s*\d+:\d+:\d+.\d*\s*(.*)\t\d*\t
                    self.capture_buffer = temp_buff_list
                    try:
                        os.remove(self._port_driver_obj.cap_file_name)
                    except Exception as e:
                        print ("capture_buffer_file was not deleted\n" + str(e))
            except Exception as e:
                print ("no frames were captured or there was another issue...\n" + str(e))
        else:
            raise Exception("capture mode not supported: " + cap_mode)

        super(self.__class__, self).stop_capture()

    def start_packet_groups(self, clear_time_stamps=True):
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())
        super(self.__class__, self).start_packet_groups(clear_time_stamps=clear_time_stamps)
        self._port_driver_obj.session.start_packet_groups(str(self._port_driver_obj))

    def clear_port_statistics(self):
        super(self.__class__, self).clear_port_statistics()
        # self._port_driver_obj.clear_port_stats() todo: currently doesn't work
        self._port_driver_obj.clear_all_stats()
        #self.statistics._reset_stats()

    def clear_all_statistics(self):
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())
        super(self.__class__, self).clear_all_statistics()
        self._port_driver_obj.clear_all_stats()
        #self.statistics._reset_stats()

    def get_supported_speeds(self):
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())
        #super(self.__class__, self).get_supported_speeds()
        if not self.card.supported_speeds:
            ss=self._port_driver_obj.supported_speeds()
            ssList = []
            if len(ss):
                for s in ss:
                    ssList.append(TGEnums._converter.speed_to_SPEED(int(s)))
            else:
                ssList.append(self.properties.speed)
            self.card._supported_speeds = ssList
            return ssList
        else:
            return self.card.supported_speeds

    def reset_sequence_index(self):
        self._port_driver_obj.reset_sequence_index()

    def add_stream(self, stream_name=None):
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())
        name =super(self.__class__, self).add_stream(stream_name=stream_name)
        try:
            self.streams[name]._stream_driver_obj = self._port_driver_obj.add_stream(name=name)
        except Exception as e:
            raise Exception("Could not add stream: " + "\n" + str(e))
        return name

    def release(self):
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())
        self._port_driver_obj.release()

    def get_stats(self):
        '''
        Updates ports stats from HW to port.stats members
        :rtype: OrderedDict
        :return: dict of the port stats as received from HW (some manipulated stats may not appear)
        '''
        super(self.__class__, self).get_stats()
        stats = self._get_port_stats()
        self._update_port_stats(stats)
        self._logger.info(self._get_port_log_title(), self._get_port_log_message() + str(self.statistics))
        return stats.statistics[str(self._port_driver_obj)]

    def get_fp_stats(self):
        '''
        Updates ports stats from HW to port.stats members
        :rtype: OrderedDict
        :return: dict of the port stats as received from HW (some manipulated stats may not appear)
        '''
        fp_stats = self._get_frame_preemption_stats()
        self._update_frame_preemption_stats(fp_stats)
        # self._logger.info(self._get_port_log_title(), self._get_port_log_message() + str(self.statistics))
        return fp_stats.statistics[str(self._port_driver_obj)]

    def _get_frame_preemption_stats(self):
        fp_stats = IxePortsPreemptionStats(self._port_driver_obj.session)
        fp_stats.read_stats()
        self._IxExPreemtionStats_dict = fp_stats.statistics[str(self._port_driver_obj)]
        return fp_stats


    def _update_frame_preemption_stats(self, stats):
        #after all stats has been read from HW on all ports as a dict, get only the dict of this port
        self._IxExPortStats_dict = stats.statistics[str(self._port_driver_obj)]

        #set defaults for all keys in case they will not come from HW
        self._IxExPreemtionStats_dict.setdefault("rxFpVerifyProtocolErrors", '-1')
        self._IxExPreemtionStats_dict.setdefault("rxFpSmdRNotTransmittedCount", '-1')
        self._IxExPreemtionStats_dict.setdefault("rxFpSmdVNotTransmittedCount", '-1')
        self._IxExPreemtionStats_dict.setdefault("rxFpUnexpectedSmdRCount", '-1')
        self._IxExPreemtionStats_dict.setdefault("rxFpSmdSStartProtocolErrors", '-1')
        self._IxExPreemtionStats_dict.setdefault("rxFpSmdSFrameCountErrors", '-1')
        self._IxExPreemtionStats_dict.setdefault("rxFpSmdCFrameCountErrors", '-1')
        self._IxExPreemtionStats_dict.setdefault("rxFpFragCountErrors", '-1')
        self._IxExPreemtionStats_dict.setdefault("rxFpInvalidCrcTypeErrors", '-1')
        self._IxExPreemtionStats_dict.setdefault("rxFpExpressCrcTypeErrors", '-1')
        self._IxExPreemtionStats_dict.setdefault("rxFpSmdSTerminationErrors", '-1')
        self._IxExPreemtionStats_dict.setdefault("rxFpSmdCTerminationErrors", '-1')
        self._IxExPreemtionStats_dict.setdefault("rxFpSmdCCrcCalcErrors", '-1')
        self._IxExPreemtionStats_dict.setdefault("rxFpReassemblyGoodCount", '-1')
        self._IxExPreemtionStats_dict.setdefault("rxFpVerifymPacketCount", '-1')
        self._IxExPreemtionStats_dict.setdefault("rxFpRespondmPacketCount", '-1')
        self._IxExPreemtionStats_dict.setdefault("rxFpSmdS0mPacketCount", '-1')
        self._IxExPreemtionStats_dict.setdefault("rxFpSmdS1mPacketCount", '-1')
        self._IxExPreemtionStats_dict.setdefault("rxFpSmdS2mPacketCount", '-1')
        self._IxExPreemtionStats_dict.setdefault("rxFpSmdS3mPacketCount", '-1')
        self._IxExPreemtionStats_dict.setdefault("rxFpSmdC0mPacketCount", '-1')
        self._IxExPreemtionStats_dict.setdefault("rxFpSmdC1mPacketCount", '-1')
        self._IxExPreemtionStats_dict.setdefault("rxFpSmdC2mPacketCount", '-1')
        self._IxExPreemtionStats_dict.setdefault("rxFpSmdC3mPacketCount", '-1')
        self._IxExPreemtionStats_dict.setdefault("rxFpVerifymPacketCrcErrors", '-1')
        self._IxExPreemtionStats_dict.setdefault("rxFpRespondmPacketCrcErrors", '-1')
        self._IxExPreemtionStats_dict.setdefault("rxFpSmdS0mPacketCrcErrors", '-1')

        self.statistics.rx_Fp_VerifyProtocolErrors = str(self._IxExPreemtionStats_dict["rxFpVerifyProtocolErrors"])
        self.statistics.rx_Fp_SmdRNotTransmittedCount = str(self._IxExPreemtionStats_dict["rxFpSmdRNotTransmittedCount"])
        self.statistics.rx_Fp_SmdVNotTransmittedCount = str(self._IxExPreemtionStats_dict["rxFpSmdVNotTransmittedCount"])
        self.statistics.rx_Fp_UnexpectedSmdRCount = str(self._IxExPreemtionStats_dict["rxFpUnexpectedSmdRCount"])
        self.statistics.rx_Fp_SmdSStartProtocolErrors = str(self._IxExPreemtionStats_dict["rxFpSmdSStartProtocolErrors"])
        self.statistics.rx_Fp_SmdSFrameCountErrors = str(self._IxExPreemtionStats_dict["rxFpSmdSFrameCountErrors"])
        self.statistics.rx_Fp_SmdCFrameCountErrors = str(self._IxExPreemtionStats_dict["rxFpSmdCFrameCountErrors"])
        self.statistics.rx_Fp_FragCountErrors = str(self._IxExPreemtionStats_dict["rxFpFragCountErrors"])
        self.statistics.rx_Fp_InvalidCrcTypeErrors = str(self._IxExPreemtionStats_dict["rxFpInvalidCrcTypeErrors"])
        self.statistics.rx_Fp_ExpressCrcTypeErrors = str(self._IxExPreemtionStats_dict["rxFpExpressCrcTypeErrors"])
        self.statistics.rx_Fp_SmdSTerminationErrors = str(self._IxExPreemtionStats_dict["rxFpSmdSTerminationErrors"])
        self.statistics.rx_Fp_SmdCTerminationErrors = str(self._IxExPreemtionStats_dict["rxFpSmdCTerminationErrors"])
        self.statistics.rx_Fp_SmdCCrcCalcErrors = str(self._IxExPreemtionStats_dict["rxFpSmdCCrcCalcErrors"])
        self.statistics.rx_Fp_ReassemblyGoodCount = str(self._IxExPreemtionStats_dict["rxFpReassemblyGoodCount"])
        self.statistics.rx_Fp_VerifymPacketCount = str(self._IxExPreemtionStats_dict["rxFpVerifymPacketCount"])
        self.statistics.rx_Fp_RespondmPacketCount = str(self._IxExPreemtionStats_dict["rxFpRespondmPacketCount"])
        self.statistics.rx_Fp_SmdS0mPacketCount = str(self._IxExPreemtionStats_dict["rxFpSmdS0mPacketCount"])
        self.statistics.rx_Fp_SmdS1mPacketCount = str(self._IxExPreemtionStats_dict["rxFpSmdS1mPacketCount"])
        self.statistics.rx_Fp_SmdS2mPacketCount = str(self._IxExPreemtionStats_dict["rxFpSmdS2mPacketCount"])
        self.statistics.rx_Fp_SmdS3mPacketCount = str(self._IxExPreemtionStats_dict["rxFpSmdS3mPacketCount"])
        self.statistics.rx_Fp_SmdC0mPacketCount = str(self._IxExPreemtionStats_dict["rxFpSmdC0mPacketCount"])
        self.statistics.rx_Fp_FpSmdC1mPacketCount = str(self._IxExPreemtionStats_dict["rxFpSmdC1mPacketCount"])
        self.statistics.rx_Fp_SmdC2mPacketCount = str(self._IxExPreemtionStats_dict["rxFpSmdC2mPacketCount"])
        self.statistics.rx_Fp_SmdC3mPacketCount = str(self._IxExPreemtionStats_dict["rxFpSmdC3mPacketCount"])
        self.statistics.rx_Fp_VerifymPacketCrcErrors = str(self._IxExPreemtionStats_dict["rxFpVerifymPacketCrcErrors"])
        self.statistics.rx_Fp_RespondmPacketCrcErrors = str(self._IxExPreemtionStats_dict["rxFpRespondmPacketCrcErrors"])
        self.statistics.rx_Fp_SmdS0mPacketCrcErrors = str(self._IxExPreemtionStats_dict["rxFpSmdS0mPacketCrcErrors"])


    def _get_port_stats(self):
        stats = IxePortsStats(self._port_driver_obj.session)
        stats.read_stats()
        self._IxExPortStats_dict = stats.statistics[str(self._port_driver_obj)]
        return stats

    def _update_port_stats(self, stats):
        #after all stats has been read from HW on all ports as a dict, get only the dict of this port
        self._IxExPortStats_dict = stats.statistics[str(self._port_driver_obj)]

        #set defaults for all keys in case they will not come from HW
        self._IxExPortStats_dict.setdefault("alignmentErrors", '-1')
        self._IxExPortStats_dict.setdefault("alignmentErrors_rate", '-1')
        self._IxExPortStats_dict.setdefault("asynchronousFramesSent", '-1')
        self._IxExPortStats_dict.setdefault("asynchronousFramesSent_rate", '-1')
        self._IxExPortStats_dict.setdefault("bitsReceived", '-1')
        self._IxExPortStats_dict.setdefault("bitsReceived_rate", '-1')
        self._IxExPortStats_dict.setdefault("bitsSent", '-1')
        self._IxExPortStats_dict.setdefault("bitsSent_rate", '-1')
        self._IxExPortStats_dict.setdefault("bytesReceived", '-1')
        self._IxExPortStats_dict.setdefault("bytesReceived_rate", '-1')
        self._IxExPortStats_dict.setdefault("bytesSent", '-1')
        self._IxExPortStats_dict.setdefault("bytesSent_rate", '-1')
        self._IxExPortStats_dict.setdefault("captureFilter", '-1')
        self._IxExPortStats_dict.setdefault("captureFilter_rate", '-1')
        self._IxExPortStats_dict.setdefault("captureTrigger", '-1')
        self._IxExPortStats_dict.setdefault("captureTrigger_rate", '-1')
        self._IxExPortStats_dict.setdefault("collisionFrames", '-1')
        self._IxExPortStats_dict.setdefault("collisionFrames_rate", '-1')
        self._IxExPortStats_dict.setdefault("collisions", '-1')
        self._IxExPortStats_dict.setdefault("collisions_rate", '-1')
        self._IxExPortStats_dict.setdefault("dataIntegrityErrors", '-1')
        self._IxExPortStats_dict.setdefault("dataIntegrityErrors_rate", '-1')
        self._IxExPortStats_dict.setdefault("dataIntegrityFrames", '-1')
        self._IxExPortStats_dict.setdefault("dataIntegrityFrames_rate", '-1')
        self._IxExPortStats_dict.setdefault("dribbleErrors", '-1')
        self._IxExPortStats_dict.setdefault("dribbleErrors_rate", '-1')
        self._IxExPortStats_dict.setdefault("droppedFrames", '-1')
        self._IxExPortStats_dict.setdefault("droppedFrames_rate", '-1')
        self._IxExPortStats_dict.setdefault("duplexMode", '-1')
        self._IxExPortStats_dict.setdefault("duplexMode_rate", '-1')
        self._IxExPortStats_dict.setdefault("excessiveCollisionFrames", '-1')
        self._IxExPortStats_dict.setdefault("excessiveCollisionFrames_rate", '-1')
        self._IxExPortStats_dict.setdefault("fcsErrors", '-1')  # to user we expose crcErrors
        self._IxExPortStats_dict.setdefault("fcsErrors_rate", '-1')  # to user we expose crcErrors_rate
        self._IxExPortStats_dict.setdefault("flowControlFrames", '-1')
        self._IxExPortStats_dict.setdefault("flowControlFrames_rate", '-1')
        self._IxExPortStats_dict.setdefault("fragments", '-1')
        self._IxExPortStats_dict.setdefault("fragments_rate", '-1')
        self._IxExPortStats_dict.setdefault("framesReceived", '-1')
        self._IxExPortStats_dict.setdefault("framesReceived_rate", '-1')
        self._IxExPortStats_dict.setdefault("framesSent", '-1')
        self._IxExPortStats_dict.setdefault("framesSent_rate", '-1')
        self._IxExPortStats_dict.setdefault("ipChecksumErrors", '-1')
        self._IxExPortStats_dict.setdefault("ipChecksumErrors_rate", '-1')
        self._IxExPortStats_dict.setdefault("ipPackets", '-1')
        self._IxExPortStats_dict.setdefault("ipPackets_rate", '-1')
        self._IxExPortStats_dict.setdefault("lateCollisions", '-1')
        self._IxExPortStats_dict.setdefault("lateCollisions_rate", '-1')
        self._IxExPortStats_dict.setdefault("lineSpeed", '-1')
        self._IxExPortStats_dict.setdefault("lineSpeed_rate", '-1')
        self._IxExPortStats_dict.setdefault("link", '-1')
        self._IxExPortStats_dict.setdefault("link_rate", '-1')
        # self._IxExPortStats_dict.setdefault("linkFaultState", '-1')
        # self._IxExPortStats_dict.setdefault("linkFaultState_rate", '-1')
        self._IxExPortStats_dict.setdefault("oversize", '-1')
        self._IxExPortStats_dict.setdefault("oversize_rate", '-1')
        self._IxExPortStats_dict.setdefault("oversizeAndCrcErrors", '-1')
        self._IxExPortStats_dict.setdefault("oversizeAndCrcErrors_rate", '-1')
        self._IxExPortStats_dict.setdefault("pauseAcknowledge", '-1')
        self._IxExPortStats_dict.setdefault("pauseAcknowledge_rate", '-1')
        self._IxExPortStats_dict.setdefault("pauseEndFrames", '-1')
        self._IxExPortStats_dict.setdefault("pauseEndFrames_rate", '-1')
        self._IxExPortStats_dict.setdefault("pauseOverwrite", '-1')
        self._IxExPortStats_dict.setdefault("pauseOverwrite_rate", '-1')
        self._IxExPortStats_dict.setdefault("prbsFramesReceived", '-1')
        self._IxExPortStats_dict.setdefault("prbsHeaderError", '-1')
        self._IxExPortStats_dict.setdefault("prbsBitsReceived", '-1')
        self._IxExPortStats_dict.setdefault("prbsErroredBits", '-1')
        self._IxExPortStats_dict.setdefault("prbsBerRatio", '-1')
        # self._IxExPortStats_dict.setdefault("prbsErroredBits_rate", '-1')
        self._IxExPortStats_dict.setdefault("rxPingReply", '-1')
        self._IxExPortStats_dict.setdefault("rxPingReply_rate", '-1')
        self._IxExPortStats_dict.setdefault("rxPingRequest", '-1')
        self._IxExPortStats_dict.setdefault("rxPingRequest_rate", '-1')
        self._IxExPortStats_dict.setdefault("scheduledFramesSent", '-1')
        self._IxExPortStats_dict.setdefault("scheduledFramesSent_rate", '-1')
        self._IxExPortStats_dict.setdefault("sequenceErrors", '-1')
        self._IxExPortStats_dict.setdefault("sequenceErrors_rate", '-1')
        self._IxExPortStats_dict.setdefault("sequenceFrames", '-1')
        self._IxExPortStats_dict.setdefault("sequenceFrames_rate", '-1')
        self._IxExPortStats_dict.setdefault("symbolErrorFrames", '-1')
        self._IxExPortStats_dict.setdefault("symbolErrorFrames_rate", '-1')
        self._IxExPortStats_dict.setdefault("symbolErrors", '-1')
        self._IxExPortStats_dict.setdefault("symbolErrors_rate", '-1')
        self._IxExPortStats_dict.setdefault("synchErrorFrames", '-1')
        self._IxExPortStats_dict.setdefault("synchErrorFrames_rate", '-1')
        self._IxExPortStats_dict.setdefault("tcpChecksumErrors", '-1')
        self._IxExPortStats_dict.setdefault("tcpChecksumErrors_rate", '-1')
        self._IxExPortStats_dict.setdefault("tcpPackets", '-1')
        self._IxExPortStats_dict.setdefault("tcpPackets_rate", '-1')
        self._IxExPortStats_dict.setdefault("transmitDuration", '-1')
        self._IxExPortStats_dict.setdefault("transmitDuration_rate", '-1')
        self._IxExPortStats_dict.setdefault("txPingReply", '-1')
        self._IxExPortStats_dict.setdefault("txPingReply_rate", '-1')
        self._IxExPortStats_dict.setdefault("txPingRequest", '-1')
        self._IxExPortStats_dict.setdefault("txPingRequest_rate", '-1')
        self._IxExPortStats_dict.setdefault("udpChecksumErrors", '-1')
        self._IxExPortStats_dict.setdefault("udpChecksumErrors_rate", '-1')
        self._IxExPortStats_dict.setdefault("udpPackets", '-1')
        self._IxExPortStats_dict.setdefault("udpPackets_rate", '-1')
        self._IxExPortStats_dict.setdefault("undersize", '-1')
        self._IxExPortStats_dict.setdefault("undersize_rate", '-1')
        self._IxExPortStats_dict.setdefault("userDefinedStat1", '-1')
        self._IxExPortStats_dict.setdefault("userDefinedStat1_rate", '-1')
        self._IxExPortStats_dict.setdefault("userDefinedStat2", '-1')
        self._IxExPortStats_dict.setdefault("userDefinedStat2_rate", '-1')
        self._IxExPortStats_dict.setdefault("vlanTaggedFramesRx", '-1')
        self._IxExPortStats_dict.setdefault("vlanTaggedFramesRx_rate", '-1')

        self._IxExPortStats_dict.setdefault("fecMaxSymbolErrors", '-1')
        self._IxExPortStats_dict.setdefault("fecUncorrectableCodewords", '-1')
        self._IxExPortStats_dict.setdefault("fecTranscodingUncorrectableErrors", '-1')

        # update the port stats members with the value from HW
        self.statistics.FEC._max_symbol_errors.value = str(self._IxExPortStats_dict["fecMaxSymbolErrors"])
        self.statistics.FEC._uncorrectable_codewords.value = str(self._IxExPortStats_dict["fecUncorrectableCodewords"])
        self.statistics.FEC._transcoding_uncorrectable_events.value = str(self._IxExPortStats_dict["fecTranscodingUncorrectableErrors"])

        self.statistics.alignment_errors = str(self._IxExPortStats_dict["alignmentErrors"])
        self.statistics.alignment_errors_rate = str(self._IxExPortStats_dict["alignmentErrors_rate"])
        self.statistics.asynchronous_frames_sent = str(self._IxExPortStats_dict["asynchronousFramesSent"])
        self.statistics.asynchronous_frames_sent_rate = str(self._IxExPortStats_dict["asynchronousFramesSent_rate"])
        self.statistics.bits_received = str(self._IxExPortStats_dict["bitsReceived"])
        self.statistics.bits_received_rate = str(self._IxExPortStats_dict["bitsReceived_rate"])
        self.statistics.bits_sent = str(self._IxExPortStats_dict["bitsSent"])
        self.statistics.bits_sent_rate = str(self._IxExPortStats_dict["bitsSent_rate"])
        self.statistics.bytes_received = str(self._IxExPortStats_dict["bytesReceived"])
        self.statistics.bytes_received_rate = str(self._IxExPortStats_dict["bytesReceived_rate"])
        self.statistics.bytes_sent = str(self._IxExPortStats_dict["bytesSent"])
        self.statistics.bytes_sent_rate = str(self._IxExPortStats_dict["bytesSent_rate"])
        self.statistics.capture_filter = str(self._IxExPortStats_dict["captureFilter"])
        self.statistics.capture_filter_rate = str(self._IxExPortStats_dict["captureFilter_rate"])
        self.statistics.capture_trigger = str(self._IxExPortStats_dict["captureTrigger"])
        self.statistics.capture_trigger_rate = str(self._IxExPortStats_dict["captureTrigger_rate"])
        self.statistics.collision_frames = str(self._IxExPortStats_dict["collisionFrames"])
        self.statistics.collision_frames_rate = str(self._IxExPortStats_dict["collisionFrames_rate"])
        self.statistics.collisions = str(self._IxExPortStats_dict["collisions"])
        self.statistics.collisions_rate = str(self._IxExPortStats_dict["collisions_rate"])
        self.statistics.data_integrity_errors = str(self._IxExPortStats_dict["dataIntegrityErrors"])
        self.statistics.data_integrity_errors_rate = str(self._IxExPortStats_dict["dataIntegrityErrors_rate"])
        self.statistics.data_integrity_frames = str(self._IxExPortStats_dict["dataIntegrityFrames"])
        self.statistics.data_integrity_frames_rate = str(self._IxExPortStats_dict["dataIntegrityFrames_rate"])
        self.statistics.dribble_errors = str(self._IxExPortStats_dict["dribbleErrors"])
        self.statistics.dribble_errors_rate = str(self._IxExPortStats_dict["dribbleErrors_rate"])
        self.statistics.dropped_frames = str(self._IxExPortStats_dict["droppedFrames"])
        self.statistics.dropped_frames_rate = str(self._IxExPortStats_dict["droppedFrames_rate"])
        self.statistics.duplex_mode = str(self._IxExPortStats_dict["duplexMode"])
        self.statistics.duplex_mode_rate = str(self._IxExPortStats_dict["duplexMode_rate"])
        self.statistics.excessive_collision_frames = str(self._IxExPortStats_dict["excessiveCollisionFrames"])
        self.statistics.excessive_collision_frames_rate = str(self._IxExPortStats_dict["excessiveCollisionFrames_rate"])
        self.statistics.crc_errors = str(self._IxExPortStats_dict["fcsErrors"])
        self.statistics.crc_errors_rate = str(self._IxExPortStats_dict["fcsErrors_rate"])
        self.statistics.flow_control_frames = str(self._IxExPortStats_dict["flowControlFrames"])
        self.statistics.flow_control_frames_rate = str(self._IxExPortStats_dict["flowControlFrames_rate"])
        self.statistics.fragments = str(self._IxExPortStats_dict["fragments"])
        self.statistics.fragments_rate = str(self._IxExPortStats_dict["fragments_rate"])
        self.statistics.frames_received = str(self._IxExPortStats_dict["framesReceived"])
        self.statistics.frames_received_rate = str(self._IxExPortStats_dict["framesReceived_rate"])
        self.statistics.frames_sent = str(self._IxExPortStats_dict["framesSent"])
        self.statistics.frames_sent_rate = str(self._IxExPortStats_dict["framesSent_rate"])
        self.statistics.ip_checksum_errors = str(self._IxExPortStats_dict["ipChecksumErrors"])
        self.statistics.ip_checksum_errors_rate = str(self._IxExPortStats_dict["ipChecksumErrors_rate"])
        self.statistics.ip_packets = str(self._IxExPortStats_dict["ipPackets"])
        self.statistics.ip_packets_rate = str(self._IxExPortStats_dict["ipPackets_rate"])
        self.statistics.late_collisions = str(self._IxExPortStats_dict["lateCollisions"])
        self.statistics.late_collisions_rate = str(self._IxExPortStats_dict["lateCollisions_rate"])
        self.statistics.line_speed = str(self._IxExPortStats_dict["lineSpeed"])
        self.statistics.line_speed_rate = str(self._IxExPortStats_dict["lineSpeed_rate"])
        self.statistics.link = str(self._IxExPortStats_dict["link"])
        self.statistics.link_rate = str(self._IxExPortStats_dict["link_rate"])
        # self.statistics.link_fault_state = str(self._IxExPortStats_dict["linkFaultState"])
        # self.statistics.link_fault_state_rate = str(self._IxExPortStats_dict["linkFaultState_rate"])
        self.statistics.oversize = str(self._IxExPortStats_dict["oversize"])
        self.statistics.oversize_rate = str(self._IxExPortStats_dict["oversize_rate"])
        self.statistics.oversize_and_crc_errors = str(self._IxExPortStats_dict["oversizeAndCrcErrors"])
        self.statistics.oversize_and_crc_errors_rate = str(self._IxExPortStats_dict["oversizeAndCrcErrors_rate"])
        self.statistics.pause_acknowledge = str(self._IxExPortStats_dict["pauseAcknowledge"])
        self.statistics.pause_acknowledge_rate = str(self._IxExPortStats_dict["pauseAcknowledge_rate"])
        self.statistics.pause_end_frames = str(self._IxExPortStats_dict["pauseEndFrames"])
        self.statistics.pause_end_frames_rate = str(self._IxExPortStats_dict["pauseEndFrames_rate"])
        self.statistics.pause_overwrite = str(self._IxExPortStats_dict["pauseOverwrite"])
        self.statistics.pause_overwrite_rate = str(self._IxExPortStats_dict["pauseOverwrite_rate"])
        self.statistics.prbs_frames_received = str(self._IxExPortStats_dict["prbsFramesReceived"])
        self.statistics.prbs_header_error = str(self._IxExPortStats_dict["prbsHeaderError"])
        self.statistics.prbs_bits_received = str(self._IxExPortStats_dict["prbsBitsReceived"])
        self.statistics.prbs_errored_bits = str(self._IxExPortStats_dict["prbsErroredBits"])
        self.statistics.prbs_ber_ratio = str(self._IxExPortStats_dict["prbsBerRatio"])
        # self.statistics.prbs_errored_bits_rate = str(self._IxExPortStats_dict["prbsErroredBits_rate"])
        self.statistics.rx_ping_reply = str(self._IxExPortStats_dict["rxPingReply"])
        self.statistics.rx_ping_reply_rate = str(self._IxExPortStats_dict["rxPingReply_rate"])
        self.statistics.rx_ping_request = str(self._IxExPortStats_dict["rxPingRequest"])
        self.statistics.rx_ping_request_rate = str(self._IxExPortStats_dict["rxPingRequest_rate"])
        self.statistics.scheduled_frames_sent = str(self._IxExPortStats_dict["scheduledFramesSent"])
        self.statistics.scheduled_frames_sent_rate = str(self._IxExPortStats_dict["scheduledFramesSent_rate"])
        self.statistics.sequence_errors = str(self._IxExPortStats_dict["sequenceErrors"])
        self.statistics.sequence_errors_rate = str(self._IxExPortStats_dict["sequenceErrors_rate"])
        self.statistics.sequence_frames = str(self._IxExPortStats_dict["sequenceFrames"])
        self.statistics.sequence_frames_rate = str(self._IxExPortStats_dict["sequenceFrames_rate"])
        self.statistics.symbol_error_frames = str(self._IxExPortStats_dict["symbolErrorFrames"])
        self.statistics.symbol_error_frames_rate = str(self._IxExPortStats_dict["symbolErrorFrames_rate"])
        self.statistics.symbol_errors = str(self._IxExPortStats_dict["symbolErrors"])
        self.statistics.symbol_errors_rate = str(self._IxExPortStats_dict["symbolErrors_rate"])
        self.statistics.synch_error_frames = str(self._IxExPortStats_dict["synchErrorFrames"])
        self.statistics.synch_error_frames_rate = str(self._IxExPortStats_dict["synchErrorFrames_rate"])
        self.statistics.tcp_checksum_errors = str(self._IxExPortStats_dict["tcpChecksumErrors"])
        self.statistics.tcp_checksum_errors_rate = str(self._IxExPortStats_dict["tcpChecksumErrors_rate"])
        self.statistics.tcp_packets = str(self._IxExPortStats_dict["tcpPackets"])
        self.statistics.tcp_packets_rate = str(self._IxExPortStats_dict["tcpPackets_rate"])
        self.statistics.transmit_duration = str(self._IxExPortStats_dict["transmitDuration"])
        self.statistics.transmit_duration_rate = str(self._IxExPortStats_dict["transmitDuration_rate"])

        # update a counter that doesn't exist in HW, so it will be easier to work with - duration in seconds
        self.statistics.transmit_duration_seconds = str(float(self._IxExPortStats_dict["transmitDuration"])/1000.0/1000.0/1000.0)

        self.statistics.tx_ping_reply = str(self._IxExPortStats_dict["txPingReply"])
        self.statistics.tx_ping_reply_rate = str(self._IxExPortStats_dict["txPingReply_rate"])
        self.statistics.tx_ping_request = str(self._IxExPortStats_dict["txPingRequest"])
        self.statistics.tx_ping_request_rate = str(self._IxExPortStats_dict["txPingRequest_rate"])
        self.statistics.udp_checksum_errors = str(self._IxExPortStats_dict["udpChecksumErrors"])
        self.statistics.udp_checksum_errors_rate = str(self._IxExPortStats_dict["udpChecksumErrors_rate"])
        self.statistics.udp_packets = str(self._IxExPortStats_dict["udpPackets"])
        self.statistics.udp_packets_rate = str(self._IxExPortStats_dict["udpPackets_rate"])
        self.statistics.undersize = str(self._IxExPortStats_dict["undersize"])
        self.statistics.undersize_rate = str(self._IxExPortStats_dict["undersize_rate"])
        self.statistics.user_defined_stat_1 = str(self._IxExPortStats_dict["userDefinedStat1"])
        self.statistics.user_defined_stat_1_rate = str(self._IxExPortStats_dict["userDefinedStat1_rate"])
        self.statistics.user_defined_stat_2 = str(self._IxExPortStats_dict["userDefinedStat2"])
        self.statistics.user_defined_stat_2_rate = str(self._IxExPortStats_dict["userDefinedStat2_rate"])
        self.statistics.vlan_tagged_frames_rx = str(self._IxExPortStats_dict["vlanTaggedFramesRx"])
        self.statistics.vlan_tagged_frames_rx_rate = str(self._IxExPortStats_dict["vlanTaggedFramesRx_rate"])

    def apply(self):
        self._logger.info(self._get_port_log_title(), self._get_port_log_message(), True)
        try:
            super(self.__class__, self).apply()
            if self.protocol_managment and self.protocol_managment.active:
                self.protocol_managment.apply()
            for stream in self.streams:
                self.streams[stream].apply(apply_to_hw=False)
        except StreamWarningsError as e:
            print("Exception in IxExPort apply()\n" + str(e))
            self._logger.info("end_level", "end_level")
        try:
            rc = self._port_driver_obj.write()
            self._logger.info("end_level", "end_level")
        except StreamWarningsError as e:
            print (str(e))
            self._logger.info("StreamWarningsError", str(e))
            self._logger.info("end_level", "end_level")

    def apply_port_config(self):
        #self._logger.info(self._get_port_log_title(), "{}{}".format(self._get_port_log_message(), self.properties))
        # 0 - packet, 4 - advanced, 7 - echo
        trans_mode = 0
        if self.properties.transmit_mode == TGEnums.PORT_PROPERTIES_TRANSMIT_MODES.MANUAL_BASED:
            trans_mode = 0
        elif self.properties.transmit_mode == TGEnums.PORT_PROPERTIES_TRANSMIT_MODES.PORT_BASED:
            trans_mode = 4
        elif self.properties.transmit_mode == TGEnums.PORT_PROPERTIES_TRANSMIT_MODES.ECHO:
            trans_mode = 7  # todo doesn't work
        # elif self.properties.transmit_mode == TGEnums.PORT_PROPERTIES_TRANSMIT_MODES.PORT_BASED_DYNAMIC_RATE_CHANGE:
        #     trans_mode = 0
        self._update_field(driver_field="transmitMode", value=trans_mode)
        # self._port_driver_obj.transmitMode = 4

        loopback_mode = 0
        loopback_exc_info = ""
        if self.properties.loopback_mode == TGEnums.PORT_PROPERTIES_LOOPBACK_MODE.NORMAL:
            loopback_mode = 0
        elif self.properties.loopback_mode == TGEnums.PORT_PROPERTIES_LOOPBACK_MODE.INTERNAL_LOOPBACK:
            loopback_mode = 1
        elif self.properties.loopback_mode == TGEnums.PORT_PROPERTIES_LOOPBACK_MODE.LINE_LOOPBACK:
            loopback_mode = 2
            loopback_exc_info += "INTERNAL_LOOPBACK is supported only on 10G ports - please check your port type..."
        self._update_field(driver_field="loopback", value=loopback_mode, exception_info=loopback_exc_info)

        if self.properties.media_type is not TGEnums.PORT_PROPERTIES_MEDIA_TYPE.HW_DEFAULT:
            if self.properties.media_type is not self.properties._media_type._previous_val:
                self._port_driver_obj.set_phy_mode(self.properties.media_type.value)

        ignore_link = 0
        ignore_link_exc_info = ""
        if self.properties.ignore_link_status == True:
            loopback_mode = 0
        elif self.properties.ignore_link_status == TGEnums.PORT_PROPERTIES_LOOPBACK_MODE.INTERNAL_LOOPBACK:
            loopback_mode = 1

        self._update_field(self.properties._ignore_link_status, driver_field="ignoreLink", exception_info=ignore_link_exc_info)
        self._update_field(self.properties._enable_simulate_cable_disconnect, driver_field="enableSimulateCableDisconnect")

        if self.properties.enable_basic_frame_preemption is not None:
            self._update_field(self.properties._enable_basic_frame_preemption, 'enableFramePreemption')

        if(self.properties.speed > TGEnums.PORT_PROPERTIES_SPEED.GIGA_10 and
           self.properties.speed is not TGEnums.PORT_PROPERTIES_SPEED.UNDEFINED):

            self._update_field(self.properties._use_ieee, driver_field='ieeeL1Defaults')

            if bool(int(self._port_driver_obj.isValidFeature(IxExEnums.IxiaFeatures.portFeatureRsFec.name))):

                fecStates = {'firecodeRequest': 0, 'firecodeAdvertise': 0, 'firecodeForceOn': 0, 'firecodeForceOff': 0,
                             'reedSolomonRequest': 0, 'reedSolomonAdvertise': 0, 'reedSolomonForceOn': 0,
                             'reedSolomonForceOff': 0}

                def update_fec_an():
                    if TGEnums.PORT_PROPERTIES_FEC_AN.REQUEST_RS in self.properties.fec_an_list:
                        fecStates['reedSolomonRequest'] = 1
                    if TGEnums.PORT_PROPERTIES_FEC_AN.ADVERTISE_RS in self.properties.fec_an_list:
                        fecStates['reedSolomonAdvertise'] = 1
                    if TGEnums.PORT_PROPERTIES_FEC_AN.REQUEST_FC in self.properties.fec_an_list:
                        fecStates['firecodeRequest'] = 1
                    if TGEnums.PORT_PROPERTIES_FEC_AN.ADVERTISE_FC in self.properties.fec_an_list:
                        fecStates['firecodeAdvertise'] = 1

                if self.properties.use_ieee_defaults is not True and \
                   self.properties.fec_mode is not TGEnums.PORT_PROPERTIES_FEC_MODES.UNDEFINED:
                    self._update_field(self.properties._use_ieee,value=0)
                    if self.properties.speed < TGEnums.PORT_PROPERTIES_SPEED.GIGA_100:
                       if self.properties.fec_mode == TGEnums.PORT_PROPERTIES_FEC_MODES.DISABLED:
                           fecStates['reedSolomonForceOff'] = 1
                           fecStates['firecodeForceOff'] = 1
                       elif self.properties.fec_mode == TGEnums.PORT_PROPERTIES_FEC_MODES.RS_FEC:
                           fecStates['reedSolomonForceOn'] = 1
                       elif self.properties.fec_mode == TGEnums.PORT_PROPERTIES_FEC_MODES.FC_FEC:
                           fecStates['firecodeForceOn'] = 1
                       else:
                           update_fec_an()
                       self._port_driver_obj.ix_set_list(fecStates)
                    else:
                        fecVal = 0
                        if self.properties.fec_mode is not TGEnums.PORT_PROPERTIES_FEC_MODES.DISABLED:
                            fecVal = 1
                        self._update_field(driver_field="enableRsFec", value=fecVal)
                elif self.properties.speed < TGEnums.PORT_PROPERTIES_SPEED.GIGA_100:
                    update_fec_an()
                    self._port_driver_obj.ix_set_list(fecStates)

        try:
            rc = self._port_driver_obj.write()
        except StreamWarningsError as e:
            print (str(e))
            self._logger.info("StreamWarningsError", str(e))

    def apply_receive_mode(self):
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())
        wpg_force = True if isinstance(self.card, IxExCard_K400) or isinstance(self.card, IxExCard_T400) else False
        if self.receive_mode.automatic_signature.enabled is True:
            self.receive_mode.wide_packet_group = True
            self.receive_mode.sequence_checking = True
            self.receive_mode.data_inetgrity = True
        if isinstance(self.card, IxExCard_STX4):
            if self.receive_mode.automatic_signature.enabled or self.receive_mode.wide_packet_group or self.receive_mode.prbs:
                self.receive_mode.capture = False
        capture_force = True if isinstance(self.card, IxExCard_K400) or isinstance(self.card, IxExCard_T400) else False
        receive_mode = int("0", base=16)
        if self.receive_mode.capture == True or capture_force:
            receive_mode += int("1", base=16)
        if self.receive_mode.echo == True:
            receive_mode += int("400", base=16)
        if self.receive_mode.packet_group == True:
            receive_mode += int("2", base=16)
        if self.receive_mode.wide_packet_group== True or wpg_force:
            receive_mode += int("1000", base=16)
        if self.receive_mode.sequence_checking == True:
            receive_mode += int("40", base=16)
        if self.receive_mode.data_inetgrity == True:
            receive_mode += int("10", base=16)
        if self.receive_mode.prbs == True:
            receive_mode += int("2000", base=16)
        self._update_field(driver_field="receiveMode", value=receive_mode,
                           exception_info="Failed to configure receive mode")

        if self.receive_mode.automatic_signature.enabled is not None:
            self._update_field(self.receive_mode.automatic_signature._enabled,'enableAutoDetectInstrumentation')

        #todo hard coded for enabling capture
        self._update_field(driver_field="capture.afterTriggerFilter", value=0, exception_info="Failed to configure capture.afterTriggerFilter")
        self._update_field(driver_field="capture.beforeTriggerFilter", value=0, exception_info="Failed to configure capture.beforeTriggerFilter")
        self._update_field(driver_field="capture.captureMode", value=0, exception_info="Failed to configure capture.captureMode")

    def apply_data_integrity(self):
        di_tx_supported = bool(int(self._port_driver_obj.isValidFeature(IxExEnums.IxiaFeatures.portFeatureTxDataIntegrity.name)))
        if di_tx_supported and self.data_integrity:
            self._logger.info(self._get_port_log_title(), self._get_port_log_message())
            self._update_field(self.data_integrity._enable, "dataIntegrity.insertSignature")
            self._update_field(self.data_integrity._enable_time_stamp, "dataIntegrity.enableTimeStamp")
            self._update_field(self.data_integrity._signature, "dataIntegrity.signature")
            self._update_field(self.data_integrity._signature_offset, "dataIntegrity.signatureOffset")

    def apply_filters(self):
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())
        def handle_filter_conditions(trigger,current_stat_prefix):
            # type: (trafficFilter, object) -> object
            patternCount = 0
            for cond in trigger.conditions:
                if cond.match_term._type is TGEnums.MATCH_TERM_TYPE.MAC_DA:
                    dest_field = 'DA'
                    value = 'notAddr' if cond.logical_operator is TGEnums.LOGICAL_OPERATOR.NOT else 'addr'
                elif cond.match_term._type is TGEnums.MATCH_TERM_TYPE.MAC_SA:
                    dest_field = 'SA'
                    value = 'notAddr' if cond.logical_operator is TGEnums.LOGICAL_OPERATOR.NOT else 'addr'
                elif cond.match_term._type is TGEnums.MATCH_TERM_TYPE.CUSTOM:
                    dest_field = 'Pattern'
                    if patternCount > 0:
                        value = "pattern1AndPattern2"
                    else:
                        value = 'notPattern' if cond.logical_operator is TGEnums.LOGICAL_OPERATOR.NOT else 'pattern'
                    patternCount += 1
                elif cond.match_term._type is TGEnums.MATCH_TERM_TYPE.SIZE:
                    from_size = 'filter.'+current_stat_prefix+'FrameSizeFrom'
                    to_size = 'filter.'+current_stat_prefix+'FrameSizeTo'
                    size_enable = 'filter.'+current_stat_prefix+'FrameSizeEnable'
                    self._update_field(driver_field=from_size, value=cond.match_term._from_size)
                    self._update_field(driver_field=to_size, value=cond.match_term._to_size)
                    self._update_field(driver_field=size_enable, value=1)
                    continue
                if patternCount<2 or cond.match_term._type is not TGEnums.MATCH_TERM_TYPE.CUSTOM:
                    value += str(cond.match_term._id)
                field = 'filter.'+current_stat_prefix+dest_field
                self._update_field(driver_field=field, value=value)

        caller_name = inspect.stack()[1][3]
        need_write = False if caller_name == "apply" else True
        terms = list(set().union(self.filter_properties.filters[1]._get_match_term_list(),
                                 self.filter_properties.filters[2]._get_match_term_list(),
                                 self.filter_properties.filters[3]._get_match_term_list(),
                                 self.filter_properties.capture_filter._get_match_term_list()
                                 )
                     )
        ixiaResourceMap = {'SA': 0, 'DA': 0, 'pattern': 0}
        for term in terms:
            patternValue = term._pattern if term._type is not TGEnums.MATCH_TERM_TYPE.SIZE else None
            if term._type is TGEnums.MATCH_TERM_TYPE.MAC_DA:
                dest_field = 'DA'
            elif term._type is TGEnums.MATCH_TERM_TYPE.MAC_SA:
                dest_field = 'SA'
            elif term._type is TGEnums.MATCH_TERM_TYPE.CUSTOM:
                dest_field = 'pattern'
                patId = ixiaResourceMap[dest_field]+1
                self._update_field(driver_field = 'filterPallette.patternOffset'+ str(patId), value=term._offset)
                spacedPattern = ""
                copyPattern = Converter.remove_non_hexa_sumbols(term._pattern[:])
                while copyPattern:
                    spacedPattern += copyPattern[:2]
                    spacedPattern += " "
                    copyPattern = copyPattern[2:]
                patternValue ="{"+spacedPattern+"}"
            elif term._type is TGEnums.MATCH_TERM_TYPE.SIZE:
                continue
            ixiaResourceMap[dest_field] += 1
            term._id = ixiaResourceMap[dest_field]
            field = 'filterPallette.'+dest_field+str(ixiaResourceMap[dest_field])
            self._update_field(driver_field=field, value=patternValue)
            mask = 'filterPallette.' + dest_field + 'Mask' + str(ixiaResourceMap[dest_field])
            if term._mask is not None:
                mask_val = term._mask
            else:
                pat = Converter.remove_non_hexa_sumbols(patternValue)
                mask_len = len(pat)/2 - 1
                mask_val = "{00"
                for i in range(int(mask_len)):
                    mask_val += " 00"
                mask_val += "}"
            self._update_field(driver_field=mask, value=mask_val)
        triggers = list(filter(lambda x: x is not None, self.filter_properties.filters))
        triggers.append( self.filter_properties.capture_filter)
        self._port_driver_obj.filter.ix_set_default()
        for trId,trigger in enumerate(triggers):
            trId+=1
            if trId <  3:
                current_stat_prefix = 'userDefinedStat' + str(trId)
            elif trId == 4:
                current_stat_prefix = 'captureFilter'
            elif trId == 3:
                current_stat_prefix = 'captureTrigger'
            enabled = 'filter.'+current_stat_prefix+'Enable'
            self._update_field(driver_field=enabled, value=int(trigger.enabled))
            if not trigger.enabled:
                continue
            handle_filter_conditions(trigger,current_stat_prefix)
        if need_write:
            try:
                rc = self._port_driver_obj.write_config()
            except StreamWarningsError as e:
                print (str(e))
                self._logger.info("StreamWarningsError", str(e))

    def write(self):
        try:
            rc = self._port_driver_obj.write()
        except Exception as e:
            print (str(e))
            self._logger.info("write port failed", str(e))

    def apply_flow_control(self):
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())
        fc = self.properties.flow_control
        self._update_field(fc._enabled , "flowControl")
        #if fc.type == TGEnums.Flow_Control_Type.IEEE802_1Qbb
        dc_supported = bool(int(self._port_driver_obj.isValidFeature(IxExEnums.IxiaFeatures.portFeatureDataCenterMode.name)))
        if dc_supported and fc.enable:
            self._update_field(fc._data_center_enabled,'enableDataCenterMode')
            self._update_field(fc._data_center_mode,'dataCenterMode',IxExEnums.DataCenterMode.eightPriorityTrafficMapping.name)
            self._update_field(fc._type, "flowControlType",self.properties.flow_control._type.current_val.value)
            self._update_field(fc._multicast_pause_address, "multicastPauseAddress")
            self._update_field(fc._directed_address, "directedAddress")
            pfcList = '{'
            for i in range (0,8):
                enable_priority_state = str(int(fc.pfc_matrix[i].enable))
                priority_value = str(fc.pfc_matrix[i].value)
                currentPriority = '{'+ enable_priority_state+' '+priority_value+'} '
                pfcList+=currentPriority
            pfcList+='}'
            self._update_field(driver_field='pfcEnableValueListBitMatrix',value = pfcList)
            if fc.enable_response_delay is not None:
                self._update_field(fc._enable_response_delay, 'pfcResponseDelayEnabled')
                self._update_field(fc._delay_quanta, 'pfcResponseDelayQuanta')


    def apply_auto_neg(self):
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())


        speedList = []
        if self.properties.auto_neg_enable:
            speedList = self.properties.auto_neg_adver_list
        else:
            speed2autoneg = {TGEnums.PORT_PROPERTIES_SPEED.MEGA_10: TGEnums.DUPLEX_AND_SPEED.FULL10,
                             TGEnums.PORT_PROPERTIES_SPEED.FAST: TGEnums.DUPLEX_AND_SPEED.FULL100,
                             TGEnums.PORT_PROPERTIES_SPEED.GIGA: TGEnums.DUPLEX_AND_SPEED.FULL1000,
                             TGEnums.PORT_PROPERTIES_SPEED.GIGA_2p5: TGEnums.DUPLEX_AND_SPEED.FULL2500,
                             TGEnums.PORT_PROPERTIES_SPEED.GIGA_5: TGEnums.DUPLEX_AND_SPEED.FULL5000,
                             TGEnums.PORT_PROPERTIES_SPEED.GIGA_10: TGEnums.DUPLEX_AND_SPEED.FULL10000,
                             }
            if speed2autoneg.get(self.properties.auto_neg_speed):
                anSpeed = speed2autoneg[self.properties.auto_neg_speed]
                speedList = [anSpeed]


        if TGEnums.DUPLEX_AND_SPEED.HALF10 in speedList:
            self._update_field(value=True, driver_field="advertise10HalfDuplex")
        else:
            self._update_field(value=False, driver_field="advertise10HalfDuplex")

        if TGEnums.DUPLEX_AND_SPEED.FULL10 in speedList:
            self._update_field(value=True, driver_field="advertise10FullDuplex")
        else:
            self._update_field(value=False, driver_field="advertise10FullDuplex")

        if TGEnums.DUPLEX_AND_SPEED.HALF100 in speedList:
            self._update_field(value=True, driver_field="advertise100HalfDuplex")
        else:
            self._update_field(value=False, driver_field="advertise100HalfDuplex")

        if TGEnums.DUPLEX_AND_SPEED.FULL100 in speedList:
            self._update_field(value=True, driver_field="advertise100FullDuplex")
        else:
            self._update_field(value=False, driver_field="advertise100FullDuplex")

        if TGEnums.DUPLEX_AND_SPEED.FULL1000 in speedList:
            self._update_field(value=True, driver_field="advertise1000FullDuplex")
        else:
            self._update_field(value=False, driver_field="advertise1000FullDuplex")

        if self.properties.port_type == "124":
            if TGEnums.DUPLEX_AND_SPEED.FULL10000 in speedList:
                self._update_field(value=True, driver_field="advertise10FullDuplex")
            else:
                self._update_field(value=False, driver_field="advertise10FullDuplex")

            if self.properties.media_type == TGEnums.PORT_PROPERTIES_MEDIA_TYPE.COPPER:
                if TGEnums.DUPLEX_AND_SPEED.FULL2500 in speedList:
                    self._update_field(value=True, driver_field="advertise2P5FullDuplex")
                else:
                    self._update_field(value=False, driver_field="advertise2P5FullDuplex")

                if TGEnums.DUPLEX_AND_SPEED.FULL5000 in speedList:
                    self._update_field(value=True, driver_field="advertise5FullDuplex")
                else:
                    self._update_field(value=False, driver_field="advertise5FullDuplex")


        master = "portMaster"
        if self.properties._auto_neg_master.current_val == True:
            master = "portMaster"
        elif self.properties._auto_neg_master.current_val == False:
            master = "portSlave"
        self._update_field(value=master, driver_field="masterSlave")

        self._update_field(value=self.properties._auto_neg_negotiate_master_slave.current_val, driver_field="negotiateMasterSlave")
        if self.properties.use_ieee_defaults is not True:
            #self._update_field(value=self.properties._auto_neg_enable.current_val, driver_field="autonegotiate")
            self._update_field(self.properties._auto_neg_enable,driver_field="autonegotiate")

        #for manual auto_neg
        if not self.card.splitable:
            duplex = "full"
            speed = "100"
            if not self.properties._auto_neg_enable.current_val:
                if self.properties.auto_neg_duplex == TGEnums.DUPLEX.FULL:
                    duplex = "full"
                elif self.properties.auto_neg_duplex == TGEnums.DUPLEX.HALF:
                    duplex = "half"
                self._update_field(value=duplex, driver_field="duplex")
                self._update_field(value=duplex, driver_field="duplex")
                if self.properties.auto_neg_speed == TGEnums.SPEED.SPEED100:
                    speed = "100"
                elif self.properties.auto_neg_speed == TGEnums.SPEED.SPEED10:
                    speed = "10"
                else:
                    speed = self.properties.auto_neg_speed.value
                self._update_field(value=speed, driver_field="speed")

        caller_name = inspect.stack()[1][3]
        if caller_name != "apply":
            self.write()



    def get_stream_count(self):
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())
        super(self.__class__, self).get_stream_count()
        return int(self._port_driver_obj.getStreamCount())

    def del_all_streams(self, apply_to_hw=True):
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())
        super(self.__class__, self).del_all_streams()
        self._port_driver_obj.reset()
        self._port_driver_obj.del_objects_by_type('stream')
        if apply_to_hw == True:
            try:
                rc = self._port_driver_obj.write()
            except StreamWarningsError as e:
                print (str(e))
                self._logger.info("StreamWarningsError", str(e))

    def reset_factory_defaults(self, apply=True):
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())
        super(self.__class__, self).reset_factory_defaults(apply=apply)
        # self._port_driver_obj.setModeDefaults()
        # self._port_driver_obj.ix_set_default()
        # self._port_driver_obj.setFactoryDefaults()
        # self._port_driver_obj.reset()
        self._port_driver_obj.clear()
        # self._port_driver_obj.clear_port_stats()
        # self._port_driver_obj.write()
        self.del_all_streams()
        if apply: self.apply()

    def restart_auto_neg(self):
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())
        super(self.__class__, self).restart_auto_neg()
        try:
            self._port_driver_obj.restartAutoNegotiation()
        except Exception as e:
            print("Exception in restart_auto_neg()\n" + str(e))

    def _hw_sync(self):
       x = self._port_driver_obj.flowControl
       self.properties.flow_control.enable = x
