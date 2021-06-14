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


# from PyTRex.trex_stl.trex_stl_streams import STLStream
from UnifiedTG.Unified.Port import Port
# from PyTRex.trex.trex_port import decode_multiplier
from pytrex.trex_port import decode_multiplier
from pytrex.trex_capture import TrexCaptureMode
import json
import re
import platform

class TrexPort(Port):

    def __init__(self,port_uri=None, port_name=None):
        super(self.__class__, self).__init__(port_uri, port_name)

    def add_stream(self, stream_name=None):
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())
        name = super(self.__class__, self).add_stream(stream_name=stream_name)
        try:
            self.streams[name]._stream_driver_obj = self._port_driver_obj.add_stream(name)
            self.streams[name]._stream_driver_obj.uri = 'Not Implemented'
            self._port_driver_obj.write_streams()
        except Exception as e:
            raise Exception("Could not add stream: " + "\n" + str(e))
        return name

    def del_all_streams(self, apply_to_hw=True):
        super(self.__class__, self).del_all_streams(apply_to_hw=apply_to_hw)
        self._port_driver_obj.remove_all_streams()

    def apply(self):
        self._logger.info(self._get_port_log_title(), self._get_port_log_message(), True)
        try:
            super(self.__class__, self).apply()
            for stream in self.streams:
                self.streams[stream].apply(apply_to_hw=False)
        except Exception as e:
            print("Exception in rt apply()\n" + str(e))
            self._logger.info("end_level", "end_level")
            raise Exception("Exception in XenaPort apply()\n" + str(e))

    def _update_port_stats(self, stats):
        if stats:
            self.statistics.frames_sent = stats['opackets']
            self.statistics.bytes_sent = stats['obytes']
            self.statistics.frames_sent_rate = stats['m_total_tx_pps']
            self.statistics.bytes_sent_rate = stats['m_total_tx_bps']/8.0

            self.statistics.frames_received = stats['ipackets']
            self.statistics.bytes_received = stats['ibytes']
            self.statistics.frames_received_rate = stats['m_total_rx_pps']
            self.statistics.bytes_received_rate = stats['m_total_rx_bps']/8.0

    def clear_port_statistics(self):
        super(self.__class__, self).clear_port_statistics()
        # self._port_driver_obj.clear_port_stats() todo: currently doesn't work
        self._port_driver_obj.clear_stats()
        #self.statistics._reset_stats()

    def clear_all_statistics(self):
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())
        super(self.__class__, self).clear_all_statistics()
        self._port_driver_obj.clear_stats()
        #self.statistics._reset_stats()

    def start_traffic(self, blocking=False, start_packet_groups=True, wait_up=None):
        # mult_obj = decode_multiplier('1', allow_update=False, divide_count=1)
        blocking = blocking if not self._is_continuous_traffic() else False
        super(self.__class__, self).start_traffic(blocking=blocking, start_packet_groups=start_packet_groups, wait_up=wait_up)

        # if start_packet_groups:
        #     self.start_packet_groups()
        self._port_driver_obj.start_transmit(blocking=blocking)


    def stop_traffic(self):
        super(self.__class__, self).stop_traffic()
        # self._port_group.stop_transmit()
        self._port_driver_obj.stop_transmit()

    def get_stats(self):
        '''
        Updates ports stats from HW to port.stats members
        :rtype: OrderedDict
        :return: dict of the port stats as received from HW (some manipulated stats may not appear)
        '''
        super(self.__class__, self).get_stats()
        stats = self._port_driver_obj.read_stats()
        # stats = self._port_driver_obj.base_stats
        self._update_port_stats(stats)
        self._logger.info(self._get_port_log_title(), self._get_port_log_message() + str(self.statistics))
        # return json.dumps(self._port_driver_obj.read_stats(), indent=2)
        # return stats.statistics[str(self._port_driver_obj)]


    def start_capture(self, rx=True, tx=False, limit=None, mode=None, bpf_filter=None):
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())
        super(self.__class__, self).start_capture()
        self.enabled_capture = True
        self._port_driver_obj.start_capture(rx=rx, tx=tx, limit=1000, mode=TrexCaptureMode.fixed, bpf_filter="")

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
            capture_obj = self._port_driver_obj.stop_capture(limit=1000, output=cap_file_name)
            for packet in capture_obj:
                self.capture_buffer.append(str(packet["hex"])[2:-1])
                self.capture_scapy.append(packet["scapy"])

        super(self.__class__, self).stop_capture()
