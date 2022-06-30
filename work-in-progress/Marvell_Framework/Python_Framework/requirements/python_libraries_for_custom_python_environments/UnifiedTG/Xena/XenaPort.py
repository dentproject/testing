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

import time
import inspect
from string import Template

from UnifiedTG.Unified.TGEnums import TGEnums
from UnifiedTG.Xena.XenaEnums import XenaEnums
from UnifiedTG.Unified.Port import Port, condition
from UnifiedTG.Unified.Utils import attrWithDefault,Converter
from UnifiedTG.Xena.XenaDriver import xenaUpdater,xenaCommandParams
from xenavalkyrie.xena_port import XenaCaptureBufferType

class xenaPort(Port,xenaUpdater):

    def __init__(self,port_uri=None, port_name=None):
        super(self.__class__, self).__init__(port_uri, port_name)
        self._config = None
        self._pl_mode = attrWithDefault(XenaEnums.PORT_PAYLOAD_MODE.UNDEFINED)
        self.filter_properties.filters[3].enabled = False
        self.filter_properties.capture_filter.enabled = False

    @property
    def payload_mode(self):
        return self._pl_mode.current_val

    @payload_mode.setter
    def payload_mode(self,mode):
        self._pl_mode.current_val = mode
        self._update_field(self._pl_mode, 'P_PAYLOADMODE')

    # def _udpate_autoneg_supported(self):
         # TODO
    #
    # def _discover(self):
        # TODO
    #
    # def _read_media_type(self):
        # TODO

    def _read_speed(self):
        speedInt = int(self._get_field('P_SPEED'))
        self.properties._speed = TGEnums._converter.speed_to_SPEED(speedInt)

    #
    # def _read_link(self):
        # TODO

    def start_traffic(self, blocking=False, start_packet_groups=True,wait_up = None):
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())
        blocking = blocking if not self._is_continuous_traffic() else False
        super(self.__class__, self).start_traffic(blocking=blocking, start_packet_groups=start_packet_groups, wait_up=wait_up)
        self._port_driver_obj.start_traffic(blocking=blocking)

    def stop_traffic(self):
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())
        super(self.__class__, self).stop_traffic()
        self._port_driver_obj.stop_traffic()
    #
    def start_capture(self):
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())
        super(self.__class__, self).start_capture()
        self.enabled_capture = True
        self._port_driver_obj.start_capture()

    def stop_capture(self, cap_file_name='capture.pcap', cap_mode="buffer"):
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())
        time.sleep(1)
        self._port_driver_obj.stop_capture()
        self._port_driver_obj.capture.get_packets(0, cap_type=XenaCaptureBufferType.pcap, file_name=cap_file_name)
        self.capture_buffer = cap_file_name
        super(self.__class__, self).stop_capture()

    #
    # def start_packet_groups(self, clear_time_stamps=True):
        # TODO


    def clear_port_statistics(self):
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())
        super(self.__class__, self).clear_port_statistics()
        self._port_driver_obj.clear_stats()
    #
    def clear_all_statistics(self):
        self.clear_port_statistics()

    #
    # def get_supported_speeds(self):
        # TODO
    #
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
        # Get port level statistics.
        '''
        Updates ports stats from HW to port.stats members
        :rtype: OrderedDict
        :return: port stats obj
        '''
        self._logger.info(self._get_port_log_title(), self._get_port_log_message() + str(self.statistics))
        #time.sleep(1)

        port_stats = self._port_driver_obj.read_port_stats()
        self.statistics.frames_received = port_stats['pr_total']['packets']
        self.statistics.bytes_received = port_stats['pr_total']['bytes']
        self.statistics.frames_received_rate = port_stats['pr_total']['pps']
        self.statistics.bytes_received_rate = port_stats['pr_total']['bps']
        self.statistics.frames_sent = port_stats['pt_total']['packets']
        self.statistics.bytes_sent = port_stats['pt_total']['bytes']
        self.statistics.frames_sent_rate = port_stats['pt_total']['pps']
        self.statistics.bits_sent_rate = port_stats['pt_total']['bps']
        self.statistics.crc_errors = port_stats['pr_extra']['fcserrors']

        try:
            filter_stats = list(self._port_driver_obj.read_filter_stats().items())
            if len(filter_stats) > 0:
                self.statistics.user_defined_stat_1 = filter_stats[0][1]['PR_FILTER']['packets']
                if len(filter_stats) > 1:
                    self.statistics.user_defined_stat_2 = filter_stats[1][1]['PR_FILTER']['packets']
                    if len(filter_stats) > 2:
                        self.statistics.capture_trigger = filter_stats[2][1]['PR_FILTER']['packets']
        except Exception as e:
            print("no filters defined")

        return self.statistics

    def patch_bug(self):
        self._update_field(driver_field='Px_rw', value=xenaCommandParams.build(['0x00000210'], ix='2000,995412'))
        self._update_field(driver_field='Px_rw', value=xenaCommandParams.build(['0x00000000'], ix='2000,995412'))

    def apply(self):
        self._logger.info(self._get_port_log_title(), self._get_port_log_message(), True)
        try:
            super(self.__class__, self).apply()
            for stream in self.streams:
                self.streams[stream].apply(apply_to_hw=False)
        except Exception as e:
            print("Exception in XenaPort apply()\n" + str(e))
            self._logger.info("end_level", "end_level")
            raise Exception("Exception in XenaPort apply()\n" + str(e))


    def apply_port_config(self):
        #TODO handle port modes  0 - packet, 4 - advanced
        loopback_mode = 'NONE'
        if self.properties.loopback_mode == TGEnums.PORT_PROPERTIES_LOOPBACK_MODE.INTERNAL_LOOPBACK or\
                self.properties.loopback_mode == TGEnums.PORT_PROPERTIES_LOOPBACK_MODE.LINE_LOOPBACK:
            loopback_mode = 'TXOFF2RX'
        self._update_field(self.properties._loopback_mode,'P_LOOPBACK', loopback_mode)

        #FEC
        port_speed = self.properties.speed
        if(port_speed > TGEnums.PORT_PROPERTIES_SPEED.GIGA_10 and
                port_speed is not TGEnums.PORT_PROPERTIES_SPEED.UNDEFINED and
                self.properties.fec_mode is not TGEnums.PORT_PROPERTIES_FEC_MODES.UNDEFINED):
           self._update_field(self.properties._fec_mode,'PP_FECMODE','ON' if self.properties.fec_mode is TGEnums.PORT_PROPERTIES_FEC_MODES.RS_FEC  else 'OFF' )

    def apply_receive_mode(self):
        pass  # TODO

    def apply_data_integrity(self):
        pass #TODOfrom UnifiedTG.Unified.Utils import attrWithDefault,Converter


    def _clear_filters(self):
        self._port_driver_obj.clear_filters()
        #self._update_field(driver_field='PF_INDICES', value='')

    def apply_filters(self):
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())
        terms = list(set().union(self.filter_properties.filters[1]._get_match_term_list(),
                                 self.filter_properties.filters[2]._get_match_term_list(),
                                 self.filter_properties.filters[3]._get_match_term_list(),
                                 self.filter_properties.capture_filter._get_match_term_list()
                                 )
                     )
        self._clear_filters()
        for i, term in enumerate(terms):
            if term._type is not TGEnums.MATCH_TERM_TYPE.SIZE:
                mask = 'FFFFFFFFFFFF0000' if term.mask is None else term.mask
                mask = "{:0<18}".format('0x' + Converter.remove_non_hexa_sumbols(mask.upper()))
                copyPattern = "{:0<18}".format('0x'+Converter.remove_non_hexa_sumbols(term._pattern[:]).upper())
                self._update_field(driver_field='PM_CREATE',value=xenaCommandParams.build(ix=i))
                self._update_field(driver_field='PM_POSITION', value=xenaCommandParams.build([term.offset],ix=i))
                self._update_field(driver_field='PM_MATCH', value=xenaCommandParams.build([mask,copyPattern],ix=i))
                term._id = pow(2, i)
            else:
                self._update_field(driver_field='PL_CREATE', value=xenaCommandParams.build(ix=1))
                self._update_field(driver_field='PL_LENGTH', value=xenaCommandParams.build(['AT_LEAST', term.from_size], ix=1))
                self._update_field(driver_field='PL_CREATE', value=xenaCommandParams.build(ix=2))
                self._update_field(driver_field='PL_LENGTH', value=xenaCommandParams.build(['AT_MOST', term.to_size], ix=2))
                term._id = pow(2, 17) +pow(2, 18)

        triggers = list(filter(lambda x: x is not None, self.filter_properties.filters))
        #TODO delete filters/conditions on reserve
        for trId,trigger in enumerate(triggers):
            if trigger.enabled:
                cond_lst = trigger.conditions  # type: list[condition]
                conditions_matrix = [0, 0, 0, 0, 0, 0]
                pair_index = 0
                for cn in cond_lst:
                    in_pair_index = 1 if cn.logical_operator is TGEnums.LOGICAL_OPERATOR.NOT else 0
                    if cn.logical_operator is TGEnums.LOGICAL_OPERATOR.OR:
                        pair_index += 2
                    conditions_matrix[pair_index+in_pair_index] += cn.match_term._id
                if any(conditions_matrix):
                    self._port_driver_obj.add_filter(xenaCommandParams.build(conditions_matrix))

    #
    # def apply_flow_control(self):
        # TODO
    #
    # def apply_auto_neg(self):
        # TODO
    #
    #
    #
    # def get_stream_count(self):
        # TODO
    #
    def reset_factory_defaults(self, apply=True):
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())
        super(self.__class__, self).reset_factory_defaults(apply=apply)
        # self._port_driver_obj.setModeDefaults()
        # self._port_driver_obj.ix_set_default()
        # self._port_driver_obj.setFactoryDefaults()
        # self._port_driver_obj.reset()
        self._port_driver_obj.reset()
        # self._port_driver_obj.clear_port_stats()
        # self._port_driver_obj.write()
        self.del_all_streams()
        if apply: self.apply()
    #
    # def restart_auto_neg(self):
        # TODO

