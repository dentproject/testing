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

from UnifiedTG.Unified.Port import Port
from UnifiedTG.Ostinato.OstinatoDriver import *
#from ostinato.core import ost_pb
from UnifiedTG.Unified.Utils import Converter
from UnifiedTG.Unified.TGEnums import TGEnums
from UnifiedTG.Ostinato.OstinatoStream import ostinatoStream
import time

class ostinatoPortDriverObj(object):
    def __init__(self):
        self.porConfigObj = None
        self.pidListObj = None


class ostinatoPort(Port):
    def __init__(self,port_uri=None, port_name=None):
        super(self.__class__, self).__init__(port_uri, port_name)
        self._config = None

    def _read_speed(self):
        return TGEnums.PORT_PROPERTIES_SPEED.FAST

    def add_stream(self,stream_name=None):
        name =super(self.__class__, self).add_stream(stream_name=stream_name)
        pid = self._port_driver_obj.port_id[:][0].id
        sid = self._streams_count
        try:
            newStream = ost_pb.StreamIdList()
            newStream.port_id.id = pid
            newStream.stream_id.add().id = sid
            ostinatoConnector.drone().addStream(newStream)
            stream_cfg = ost_pb.StreamConfigList()
            stream_cfg.port_id.id = pid
            s = stream_cfg.stream.add()
            s.stream_id.id = sid
            s.core.name = name
            self.streams[name]._stream_driver_obj.cfg = stream_cfg
            self.streams[name]._stream_driver_obj.stream = s

        except Exception as e:
            raise Exception("Could not add stream: " + "\n" + str(e))
        return name

    def wait_tx_done(self):
        probe_count = 0
        if not self._is_continuous_traffic():
            stats = self.statistics
            self.get_stats()
            ref_sent = stats.frames_sent
            while True:
                time.sleep(0.7)
                self.get_stats()
                if stats.frames_sent == ref_sent:
                    if probe_count > 3:
                        break
                    else:
                        probe_count += 1
                ref_sent = stats.frames_sent

    def wait_link_up(self, timeout=60):
        # currently not supported - stub function
        pass

    def start_traffic(self, blocking=False):
        """ Start transmit on port.
        :param blocking: True - wait for traffic end, False - return after traffic start.
        """
        ostinatoConnector.drone().startTransmit(self._port_driver_obj)
        if blocking:
            self.wait_tx_done()
            pass

    def stop_traffic(self):
        ostinatoConnector.drone().stopTransmit(self._port_driver_obj)

    def start_capture(self):
        ostinatoConnector.drone().startCapture(self._port_driver_obj)

    def stop_capture(self, cap_file_name='capture.pcap', cap_mode="buffer"):
        ostinatoConnector.drone().stopCapture(self._port_driver_obj)
        buff = ostinatoConnector.drone().getCaptureBuffer(self._port_driver_obj.port_id[0])
        ostinatoConnector.drone().saveCaptureBuffer(buff, cap_file_name)
        self.capture_buffer = cap_file_name
        super(self.__class__, self).stop_capture()

    def clear_port_statistics(self):
        super(self.__class__, self).clear_port_statistics()
        ostinatoConnector.drone().clearStats(self._port_driver_obj)

    def clear_all_statistics(self):
        self.clear_port_statistics()

    def get_supported_speeds(self):
        pass

    def clear_ownership(self):
        pass

    def apply(self):
        super(self.__class__, self).apply()
        ostinatoStream._continious_flag = False
        self.apply_streams()

    def apply_port_config(self):
        pass

    def apply_data_integrity(self):
        pass

    def apply_receive_mode(self):
        pass

    def apply_flow_control(self):
        pass

    def get_stats(self):
        '''
        Updates ports stats from HW to port.stats members
            :rtype: OrderedDict
            :return: dict of the port stats as received from HW (some manipulated stats may not appear)
        '''
        port_stats = ostinatoConnector.drone().getStats(self._port_driver_obj).port_stats[0]

        self.statistics.frames_received = port_stats.rx_pkts
        self.statistics.bytes_received = port_stats.rx_bytes
        self.statistics.frames_received_rate = port_stats.rx_pps
        self.statistics.bytes_received_rate = port_stats.rx_bps
        self.statistics.frames_sent = port_stats.tx_pkts
        self.statistics.bytes_sent = port_stats.tx_bytes
        self.statistics.frames_sent_rate = port_stats.tx_pps
        self.statistics.bits_sent_rate = port_stats.tx_bps
        self.statistics.dropped_frames = port_stats.rx_drops
        self.statistics.oversize_and_crc_errors = port_stats.rx_errors
        self.statistics.crc_errors = port_stats.rx_frame_errors
        self.statistics.user_defined_stat_1 = port_stats.triggered_rx_pkts1
        self.statistics.user_defined_stat_2 = port_stats.triggered_rx_pkts2
        self.statistics.capture_trigger = port_stats.triggered_rx_pkts3

        return self.statistics

        #self.statistics.capture_filter

        # update the port stats members with the value from HW
        # self.statistics.bits_received = str(self._IxExPortStats_dict["bitsReceived"])
        # self.statistics.bits_received_rate = str(self._IxExPortStats_dict["bitsReceived_rate"])
        # self.statistics.bits_sent = str(self._IxExPortStats_dict["bitsSent"])
        # self.statistics.bits_sent_rate = str(self._IxExPortStats_dict["bitsSent_rate"])
        # self.statistics.bytes_received = str(self._IxExPortStats_dict["bytesReceived"])
        # self.statistics.bytes_received_rate = str(self._IxExPortStats_dict["bytesReceived_rate"])
        # self.statistics.bytes_sent = str(self._IxExPortStats_dict["bytesSent"])
        # self.statistics.bytes_sent_rate = str(self._IxExPortStats_dict["bytesSent_rate"])
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
        # self.statistics.crc_errors = str(self._IxExPortStats_dict["fcsErrors"])
        # self.statistics.crc_errors_rate = str(self._IxExPortStats_dict["fcsErrors_rate"])
        # self.statistics.flow_control_frames = str(self._IxExPortStats_dict["flowControlFrames"])
        # self.statistics.flow_control_frames_rate = str(self._IxExPortStats_dict["flowControlFrames_rate"])
        # self.statistics.fragments = str(self._IxExPortStats_dict["fragments"])
        # self.statistics.fragments_rate = str(self._IxExPortStats_dict["fragments_rate"])
        # self.statistics.frames_received = str(self._IxExPortStats_dict["framesReceived"])
        # self.statistics.frames_received_rate = str(self._IxExPortStats_dict["framesReceived_rate"])
        # self.statistics.frames_sent = str(self._IxExPortStats_dict["framesSent"])
        # self.statistics.frames_sent_rate = str(self._IxExPortStats_dict["framesSent_rate"])
        # self.statistics.ip_checksum_errors = str(self._IxExPortStats_dict["ipChecksumErrors"])
        # self.statistics.ip_checksum_errors_rate = str(self._IxExPortStats_dict["ipChecksumErrors_rate"])
        # self.statistics.ip_packets = str(self._IxExPortStats_dict["ipPackets"])
        # self.statistics.ip_packets_rate = str(self._IxExPortStats_dict["ipPackets_rate"])
        # self.statistics.late_collisions = str(self._IxExPortStats_dict["lateCollisions"])
        # self.statistics.late_collisions_rate = str(self._IxExPortStats_dict["lateCollisions_rate"])
        # self.statistics.line_speed = str(self._IxExPortStats_dict["lineSpeed"])
        # self.statistics.line_speed_rate = str(self._IxExPortStats_dict["lineSpeed_rate"])
        # self.statistics.link = str(self._IxExPortStats_dict["link"])
        # self.statistics.link_rate = str(self._IxExPortStats_dict["link_rate"])
        # # self.statistics.link_fault_state = str(self._IxExPortStats_dict["linkFaultState"])
        # # self.statistics.link_fault_state_rate = str(self._IxExPortStats_dict["linkFaultState_rate"])
        # self.statistics.oversize = str(self._IxExPortStats_dict["oversize"])
        # self.statistics.oversize_rate = str(self._IxExPortStats_dict["oversize_rate"])
        # self.statistics.oversize_and_crc_errors = str(self._IxExPortStats_dict["oversizeAndCrcErrors"])
        # self.statistics.oversize_and_crc_errors_rate = str(self._IxExPortStats_dict["oversizeAndCrcErrors_rate"])
        # self.statistics.pause_acknowledge = str(self._IxExPortStats_dict["pauseAcknowledge"])
        # self.statistics.pause_acknowledge_rate = str(self._IxExPortStats_dict["pauseAcknowledge_rate"])
        # self.statistics.pause_end_frames = str(self._IxExPortStats_dict["pauseEndFrames"])
        # self.statistics.pause_end_frames_rate = str(self._IxExPortStats_dict["pauseEndFrames_rate"])
        # self.statistics.pause_overwrite = str(self._IxExPortStats_dict["pauseOverwrite"])
        # self.statistics.pause_overwrite_rate = str(self._IxExPortStats_dict["pauseOverwrite_rate"])
        # self.statistics.prbs_errored_bits = str(self._IxExPortStats_dict["prbsErroredBits"])
        # # self.statistics.prbs_errored_bits_rate = str(self._IxExPortStats_dict["prbsErroredBits_rate"])
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
        # self.statistics.tcp_checksum_errors = str(self._IxExPortStats_dict["tcpChecksumErrors"])
        # self.statistics.tcp_checksum_errors_rate = str(self._IxExPortStats_dict["tcpChecksumErrors_rate"])
        # self.statistics.tcp_packets = str(self._IxExPortStats_dict["tcpPackets"])
        # self.statistics.tcp_packets_rate = str(self._IxExPortStats_dict["tcpPackets_rate"])
        # self.statistics.transmit_duration = str(self._IxExPortStats_dict["transmitDuration"])
        # self.statistics.transmit_duration_rate = str(self._IxExPortStats_dict["transmitDuration_rate"])
        #
        # # update a counter that doesn't exist in HW, so it will be easier to work with - duration in seconds
        # self.statistics.transmit_duration_seconds = str(float(self._IxExPortStats_dict["transmitDuration"])/1000.0/1000.0/1000.0)
        #
        # self.statistics.tx_ping_reply = str(self._IxExPortStats_dict["txPingReply"])
        # self.statistics.tx_ping_reply_rate = str(self._IxExPortStats_dict["txPingReply_rate"])
        # self.statistics.tx_ping_request = str(self._IxExPortStats_dict["txPingRequest"])
        # self.statistics.tx_ping_request_rate = str(self._IxExPortStats_dict["txPingRequest_rate"])
        # self.statistics.udp_checksum_errors = str(self._IxExPortStats_dict["udpChecksumErrors"])
        # self.statistics.udp_checksum_errors_rate = str(self._IxExPortStats_dict["udpChecksumErrors_rate"])
        # self.statistics.udp_packets = str(self._IxExPortStats_dict["udpPackets"])
        # self.statistics.udp_packets_rate = str(self._IxExPortStats_dict["udpPackets_rate"])
        # self.statistics.undersize = str(self._IxExPortStats_dict["undersize"])
        # self.statistics.undersize_rate = str(self._IxExPortStats_dict["undersize_rate"])
        # self.statistics.user_defined_stat_1 = str(self._IxExPortStats_dict["userDefinedStat1"])
        # self.statistics.user_defined_stat_1_rate = str(self._IxExPortStats_dict["userDefinedStat1_rate"])
        # self.statistics.user_defined_stat_2 = str(self._IxExPortStats_dict["userDefinedStat2"])
        # self.statistics.user_defined_stat_2_rate = str(self._IxExPortStats_dict["userDefinedStat2_rate"])
        # self.statistics.vlan_tagged_frames_rx = str(self._IxExPortStats_dict["vlanTaggedFramesRx"])
        # self.statistics.vlan_tagged_frames_rx_rate = str(self._IxExPortStats_dict["vlanTaggedFramesRx_rate"])

    def apply_filters(self):
        def handle_filter_conditions(utg_trigger,ost_trigger):
            for cond in utg_trigger.conditions:
                term = ost_trigger.terms.add()
                term.offset = cond.match_term.offset
                pattern = Converter.remove_non_hexa_sumbols(cond.match_term.pattern)
                mask = Converter.remove_non_hexa_sumbols(cond.match_term.mask) if cond.match_term.mask is not None else "F"*len(pattern)
                term.pattern = pattern
                term.mask = mask
                term.is_not = True if cond.logical_operator is TGEnums.LOGICAL_OPERATOR.NOT else False

        portConfig = self._config.port[0]
        triggers = list(filter(lambda x: x is not None, self.filter_properties.filters))
        #triggers.append( self.filter_properties.capture_filter)
        for trId,utg_trigger in enumerate(triggers):
            trId+=1
            if trId == 1:
                ost_trigger = portConfig.user_trigger1
            elif trId == 2:
                ost_trigger = portConfig.user_trigger2
            elif trId == 3:
                ost_trigger = portConfig.user_trigger3
            ost_trigger.Clear()
            if not utg_trigger.enabled:
                continue
            handle_filter_conditions(utg_trigger,ost_trigger)
        ostinatoConnector.drone().modifyPort(self._config)

    def get_stream_count(self):
        pid = self._port_driver_obj.port_id[0]
        StreamIdList = ostinatoConnector.drone().getStreamIdList(pid)
        count = len(StreamIdList.stream_id)
        return count

    def del_all_streams(self, apply_to_hw=True):
        super(self.__class__, self).del_all_streams()
        pid = self._port_driver_obj.port_id[0]
        StreamIdList =ostinatoConnector.drone().getStreamIdList(pid)
        ostinatoConnector.drone().deleteStream(StreamIdList)

    def reset_factory_defaults(self, apply=True):
        super(self.__class__, self).reset_factory_defaults(apply=apply)
        self.stop_traffic()
        # self._port_driver_obj.clear_stats()
        # self._port_driver_obj.write()
        self.del_all_streams()