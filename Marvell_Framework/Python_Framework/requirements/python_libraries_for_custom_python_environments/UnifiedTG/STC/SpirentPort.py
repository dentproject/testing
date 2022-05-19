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

from collections import OrderedDict

from UnifiedTG.Unified.Port import Port
from UnifiedTG.Unified.Utils import Converter
from UnifiedTG.Unified.TGEnums import TGEnums
import time

class spirentPort(Port):
    def __init__(self,port_uri=None, port_name=None):
        super(self.__class__, self).__init__(port_uri, port_name)

    def add_stream(self,stream_name=None):
        name =super(self.__class__, self).add_stream(stream_name=stream_name)
        try:
            self.streams[name]._stream_driver_obj = self._port_driver_obj.add_stream(name=name)
        except Exception as e:
            raise Exception("Could not add stream: " + "\n" + str(e))
        return name

    def start_traffic(self, blocking=False,start_packet_groups=False,wait_up=None):
        #blocking = blocking if not self._is_continuous_traffic() else False
        super(self.__class__, self).start_traffic(blocking=blocking, start_packet_groups=start_packet_groups, wait_up=wait_up)
        self._port_driver_obj.start(blocking=blocking)
    #
    def stop_traffic(self):
        super(self.__class__, self).stop_traffic()
        self._port_driver_obj.stop()
    #
    # def start_capture(self):
    #     ostinatoConnector.drone().startCapture(self._port_driver_obj)
    #
    # def stop_capture(self, cap_file_name='capture.pcap', cap_mode="buffer"):
    #     ostinatoConnector.drone().stopCapture(self._port_driver_obj)
    #     buff = ostinatoConnector.drone().getCaptureBuffer(self._port_driver_obj.port_id[0])
    #     ostinatoConnector.drone().saveCaptureBuffer(buff, cap_file_name)
    #     self.capture_buffer = cap_file_name
    #     super(self.__class__, self).stop_capture()
    #
    def clear_port_statistics(self):
        super(self.__class__, self).clear_port_statistics()
        self._port_driver_obj.clear_results()

    def clear_all_statistics(self):
        self.clear_port_statistics()

    def apply(self):
        super(self.__class__, self).apply()
        self.apply_streams()
        self._port_driver_obj.write()

    def apply_port_config(self):
        if self.properties.transmit_mode == TGEnums.PORT_PROPERTIES_TRANSMIT_MODES.MANUAL_BASED:
            trans_mode = 'MANUAL_BASED'
        elif self.properties.transmit_mode == TGEnums.PORT_PROPERTIES_TRANSMIT_MODES.PORT_BASED:
            trans_mode = 'PORT_BASED'
        elif self.properties.transmit_mode == TGEnums.PORT_PROPERTIES_TRANSMIT_MODES.STREAM_BASED:
            trans_mode = 'RATE_BASED'
        self._port_driver_obj.trasmit_mode(trans_mode)

        self._port_driver_obj.ignore_link_status = self.properties.ignore_link_status
        lb = False if self.properties.loopback_mode is TGEnums.PORT_PROPERTIES_LOOPBACK_MODE.NORMAL else True
        self._port_driver_obj.loopback = lb
        #todo state machine update
        #self._update_field(driver_field="SchedulingMode", value=trans_mode)

        #TODO rest of port poperties,fec,speed etc...
    #
    # def apply_data_integrity(self):
    #     pass
    #
    # def apply_receive_mode(self):
    #     pass
    #
    # def apply_flow_control(self):
    #     pass
    #
    def get_stats(self):
        '''
        Updates ports stats from HW to port.stats members
            :rtype: OrderedDict
            :return: dict of the port stats as received from HW (some manipulated stats may not appear)
        '''
        tx = self._port_driver_obj.tx_stats
        rx = self._port_driver_obj.rx_stats

        self.statistics.frames_received = rx['TotalFrameCount']
        self.statistics.bytes_received =rx['TotalOctetCount']
        self.statistics.frames_received_rate = rx['TotalFrameRate']
        self.statistics.bytes_received_rate = rx['TotalOctetRate']
        self.statistics.frames_sent = tx['TotalFrameCount']
        self.statistics.bytes_sent = tx['TotalOctetCount']
        self.statistics.frames_sent_rate = tx['TotalFrameRate']
        self.statistics.dropped_frames = rx['DroppedFrameCount']

        self.statistics.crc_errors = tx['GeneratorCrcErrorFrameCount']

    #     self.statistics.user_defined_stat_1 = port_stats.triggered_rx_pkts1
    #     self.statistics.user_defined_stat_2 = port_stats.triggered_rx_pkts2
    #     self.statistics.capture_trigger = port_stats.triggered_rx_pkts3
    #
    #     #self.statistics.capture_filter
    #
        self.statistics.bits_received = rx['L1BitCount']
        self.statistics.bits_received_rate = rx['L1BitRate']
        self.statistics.bits_sent = tx['L1BitCount']
        self.statistics.bits_sent_rate = tx['L1BitRate']

        # self.statistics.capture_filter = str(self._IxExPortStats_dict["captureFilter"])
        # self.statistics.capture_filter_rate = str(self._IxExPortStats_dict["captureFilter_rate"])
        # self.statistics.capture_trigger = str(self._IxExPortStats_dict["captureTrigger"])
        # self.statistics.capture_trigger_rate = str(self._IxExPortStats_dict["captureTrigger_rate"])
        # self.statistics.collision_frames = str(self._IxExPortStats_dict["collisionFrames"])
        # self.statistics.collision_frames_rate = str(self._IxExPortStats_dict["collisionFrames_rate"])
        # self.statistics.collisions = str(self._IxExPortStats_dict["collisions"])
        # self.statistics.collisions_rate = str(self._IxExPortStats_dict["collisions_rate"])
        # self.statistics.data_integrity_errors = str(self._IxExPortStats_dict["dataIntegrityErrors"])
        # self.statistics.data_integrity_errors_rate = str(self._IxExPortStats_dict["dataIntegrityErrors_rate"])
        # self.statistics.data_integrity_frames = str(self._IxExPortStats_dict["dataIntegrityFrames"])
        # self.statistics.data_integrity_frames_rate = str(self._IxExPortStats_dict["dataIntegrityFrames_rate"])
        # self.statistics.dribble_errors = str(self._IxExPortStats_dict["dribbleErrors"])
        # self.statistics.dribble_errors_rate = str(self._IxExPortStats_dict["dribbleErrors_rate"])
        # self.statistics.dropped_frames = str(self._IxExPortStats_dict["droppedFrames"])
        # self.statistics.dropped_frames_rate = str(self._IxExPortStats_dict["droppedFrames_rate"])
        # self.statistics.duplex_mode = str(self._IxExPortStats_dict["duplexMode"])
        # self.statistics.duplex_mode_rate = str(self._IxExPortStats_dict["duplexMode_rate"])
        # self.statistics.excessive_collision_frames = str(self._IxExPortStats_dict["excessiveCollisionFrames"])
        # self.statistics.excessive_collision_frames_rate = str(self._IxExPortStats_dict["excessiveCollisionFrames_rate"])
        # self.statistics.crc_errors_rate = str(self._IxExPortStats_dict["fcsErrors_rate"])
        # self.statistics.flow_control_frames = str(self._IxExPortStats_dict["flowControlFrames"])
        # self.statistics.flow_control_frames_rate = str(self._IxExPortStats_dict["flowControlFrames_rate"])
        # self.statistics.fragments = str(self._IxExPortStats_dict["fragments"])
        # self.statistics.fragments_rate = str(self._IxExPortStats_dict["fragments_rate"])

        self.statistics.ip_checksum_errors = rx['Ipv4ChecksumErrorCount']
        self.statistics.ip_checksum_errors_rate = rx['Ipv4ChecksumErrorRate']
        self.statistics.ip_packets = rx['Ipv4FrameCount']
        self.statistics.ip_packets_rate = rx['Ipv4FrameRate']
        # self.statistics.late_collisions = str(self._IxExPortStats_dict["lateCollisions"])
        # self.statistics.late_collisions_rate = str(self._IxExPortStats_dict["lateCollisions_rate"])
        # self.statistics.line_speed = str(self._IxExPortStats_dict["lineSpeed"])
        # self.statistics.line_speed_rate = str(self._IxExPortStats_dict["lineSpeed_rate"])
        # self.statistics.link = str(self._IxExPortStats_dict["link"])
        # self.statistics.link_rate = str(self._IxExPortStats_dict["link_rate"])
        # # self.statistics.link_fault_state = str(self._IxExPortStats_dict["linkFaultState"])
        # # self.statistics.link_fault_state_rate = str(self._IxExPortStats_dict["linkFaultState_rate"])
        self.statistics.oversize = rx['OversizeFrameCount']
        self.statistics.oversize_rate = rx['OversizeFrameRate']
        # self.statistics.oversize_and_crc_errors = str(self._IxExPortStats_dict["oversizeAndCrcErrors"])
        # self.statistics.oversize_and_crc_errors_rate = str(self._IxExPortStats_dict["oversizeAndCrcErrors_rate"])
        # self.statistics.pause_acknowledge = str(self._IxExPortStats_dict["pauseAcknowledge"])
        # self.statistics.pause_acknowledge_rate = str(self._IxExPortStats_dict["pauseAcknowledge_rate"])
        # self.statistics.pause_end_frames = str(self._IxExPortStats_dict["pauseEndFrames"])
        # self.statistics.pause_end_frames_rate = str(self._IxExPortStats_dict["pauseEndFrames_rate"])
        # self.statistics.pause_overwrite = str(self._IxExPortStats_dict["pauseOverwrite"])
        # self.statistics.pause_overwrite_rate = str(self._IxExPortStats_dict["pauseOverwrite_rate"])
        self.statistics.prbs_errored_bits = rx['PrbsBitErrorCount']
        self.statistics.prbs_errored_bits_rate = rx['PrbsBitErrorRate']
        # self.statistics.rx_ping_reply = str(self._IxExPortStats_dict["rxPingReply"])
        # self.statistics.rx_ping_reply_rate = str(self._IxExPortStats_dict["rxPingReply_rate"])
        # self.statistics.rx_ping_request = str(self._IxExPortStats_dict["rxPingRequest"])
        # self.statistics.rx_ping_request_rate = str(self._IxExPortStats_dict["rxPingRequest_rate"])
        # self.statistics.scheduled_frames_sent = str(self._IxExPortStats_dict["scheduledFramesSent"])
        # self.statistics.scheduled_frames_sent_rate = str(self._IxExPortStats_dict["scheduledFramesSent_rate"])
        # self.statistics.sequence_errors = str(self._IxExPortStats_dict["sequenceErrors"])
        # self.statistics.sequence_errors_rate = str(self._IxExPortStats_dict["sequenceErrors_rate"])
        # self.statistics.sequence_frames = str(self._IxExPortStats_dict["sequenceFrames"])
        # self.statistics.sequence_frames_rate = str(self._IxExPortStats_dict["sequenceFrames_rate"])
        # self.statistics.symbol_error_frames = str(self._IxExPortStats_dict["symbolErrorFrames"])
        # self.statistics.symbol_error_frames_rate = str(self._IxExPortStats_dict["symbolErrorFrames_rate"])
        # self.statistics.symbol_errors = str(self._IxExPortStats_dict["symbolErrors"])
        # self.statistics.symbol_errors_rate = str(self._IxExPortStats_dict["symbolErrors_rate"])
        # self.statistics.synch_error_frames = str(self._IxExPortStats_dict["synchErrorFrames"])
        # self.statistics.synch_error_frames_rate = str(self._IxExPortStats_dict["synchErrorFrames_rate"])
        self.statistics.tcp_checksum_errors = rx['TcpChecksumErrorCount']
        self.statistics.tcp_checksum_errors_rate = rx['TcpChecksumErrorRate']
        self.statistics.tcp_packets =rx['TcpFrameCount']
        self.statistics.tcp_packets_rate = rx['TcpFrameRate']
        #self.statistics.transmit_duration = str(self._IxExPortStats_dict["transmitDuration"])
        #self.statistics.transmit_duration_rate = str(self._IxExPortStats_dict["transmitDuration_rate"])
        #
        # # update a counter that doesn't exist in HW, so it will be easier to work with - duration in seconds
        # self.statistics.transmit_duration_seconds = str(float(self._IxExPortStats_dict["transmitDuration"])/1000.0/1000.0/1000.0)
        #
        # self.statistics.tx_ping_reply = str(self._IxExPortStats_dict["txPingReply"])
        # self.statistics.tx_ping_reply_rate = str(self._IxExPortStats_dict["txPingReply_rate"])
        # self.statistics.tx_ping_request = str(self._IxExPortStats_dict["txPingRequest"])
        # self.statistics.tx_ping_request_rate = str(self._IxExPortStats_dict["txPingRequest_rate"])

        self.statistics.udp_checksum_errors = rx['UdpChecksumErrorCount']
        self.statistics.udp_checksum_errors_rate = rx['UdpChecksumErrorRate']
        self.statistics.udp_packets = rx['UdpFrameCount']
        self.statistics.udp_packets_rate = rx['UdpFrameRate']
        # self.statistics.undersize = str(self._IxExPortStats_dict["undersize"])
        # self.statistics.undersize_rate = str(self._IxExPortStats_dict["undersize_rate"])
        # self.statistics.user_defined_stat_1 = str(self._IxExPortStats_dict["userDefinedStat1"])
        # self.statistics.user_defined_stat_1_rate = str(self._IxExPortStats_dict["userDefinedStat1_rate"])
        # self.statistics.user_defined_stat_2 = str(self._IxExPortStats_dict["userDefinedStat2"])
        # self.statistics.user_defined_stat_2_rate = str(self._IxExPortStats_dict["userDefinedStat2_rate"])
        self.statistics.vlan_tagged_frames_rx = rx['VlanFrameCount']
        self.statistics.vlan_tagged_frames_rx_rate = rx['VlanFrameRate']
    #
    # def apply_filters(self):
    #     def handle_filter_conditions(utg_trigger,ost_trigger):
    #         for cond in utg_trigger.conditions:
    #             term = ost_trigger.terms.add()
    #             term.offset = cond.match_term.offset
    #             pattern = Converter.remove_non_hexa_sumbols(cond.match_term.pattern)
    #             mask = Converter.remove_non_hexa_sumbols(cond.match_term.mask) if cond.match_term.mask is not None else "F"*len(pattern)
    #             term.pattern = pattern
    #             term.mask = mask
    #             term.is_not = True if cond.logical_operator is TGEnums.LOGICAL_OPERATOR.NOT else False
    #
    #     portConfig = self._config.port[0]
    #     triggers = list(filter(lambda x: x is not None, self.filter_properties.filters))
    #     #triggers.append( self.filter_properties.capture_filter)
    #     for trId,utg_trigger in enumerate(triggers):
    #         trId+=1
    #         if trId == 1:
    #             ost_trigger = portConfig.user_trigger1
    #         elif trId == 2:
    #             ost_trigger = portConfig.user_trigger2
    #         elif trId == 3:
    #             ost_trigger = portConfig.user_trigger3
    #         ost_trigger.Clear()
    #         if not utg_trigger.enabled:
    #             continue
    #         handle_filter_conditions(utg_trigger,ost_trigger)
    #     ostinatoConnector.drone().modifyPort(self._config)
    #
    # def get_stream_count(self):
    #     pid = self._port_driver_obj.port_id[0]
    #     StreamIdList = ostinatoConnector.drone().getStreamIdList(pid)
    #     count = len(StreamIdList.stream_id)
    #     return count
    #
    def del_all_streams(self, apply_to_hw=True):
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())
        super(self.__class__, self).del_all_streams()
        self._port_driver_obj.clear_streams()
        if apply_to_hw == True:
            rc = self._port_driver_obj.write()


    def reset_factory_defaults(self, apply=True):
        super(self.__class__, self).reset_factory_defaults(apply=apply)
        self.streams = OrderedDict()
        self._port_driver_obj.reset()
        #if apply: self.apply()