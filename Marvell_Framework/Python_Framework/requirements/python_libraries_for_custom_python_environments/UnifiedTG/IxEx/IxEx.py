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

import os
import re
import platform
from ixexplorer.ixe_port import StreamWarningsError
from ixexplorer.ixe_app import init_ixe
from trafficgenerator.tgn_utils import ApiType
from ixexplorer.ixe_statistics_view import IxePortsStats, IxeStreamsStats, IxeCapFileFormat
from UnifiedTG.Unified.TG import TG
from UnifiedTG.IxEx.IxExPort import IxExPort
from UnifiedTG.IxEx.IxExChassis import IxExChassis,IxExCard,IxExResourceGroup
from UnifiedTG.Unified.Chassis import Chassis,Card,resourceGroup
from UnifiedTG.Unified.TgInfo import *
import json
import inspect


class IxEx(TG):
    def __init__(self, server_host, login_name, server_tcp_port=4555, api_type=ApiType.socket,rsaPath = ""):
        super(self.__class__, self).__init__(server_host, login_name, server_tcp_port)
        self._connector = init_ixe(logger=self._logger, host=server_host, port=int(server_tcp_port),rsa_id=rsaPath)

    def discover(self,chassisList):
        self._connect(chassisList)

    def _connect(self, chassisList):
        if chassisList is not None:
            super(self.__class__, self)._connect(chassisList)
            caller_name = inspect.stack()[1][3]
            if caller_name != "discover":
                return
            for chasIp in chassisList:
                if chasIp in self._connector.chassis_chain:
                    if len(self._connector.chassis_chain[chasIp].cards) == 0:
                        self._connector.chassis_chain[chasIp].discover()
                    #if chasIp in self._connector.chassis_chain:
                        self.chassis[chasIp]._discover()

    def _port_uri_in_use(self, pData):
        return True if self._port_name_by_uri(tgPortInfo(pData).uri) else False

    def reserve_ports(self,ports_list,force=False,clear = False):
        self._logger.info(self._get_tg_log_title(), self._get_tg_log_message())
        max_attemps = 4
        for retry in range(max_attemps):
            try:
                reseved_ports = []  # type: list[IxExPort]
                new_ports = list(filter(lambda pData: not self._port_uri_in_use(pData), ports_list))
                if not new_ports:
                    # trying to reserve same ports that were already reserved before by this utg instance will causes
                    # exception when list is empty list will be empty when changed IXIA card mode from 4 X 10G to 4 X 25G
                    # or 1X40 to 1x100 and vice versa while also logged in  in  IxExplorer with same User as this instance
                    new_ports = list(ports_list)
                super(self.__class__, self).reserve_ports(new_ports, force, clear)
                pInfoList = tgPortsInfo(ports_list)
                newPinfoLIst = tgPortsInfo(new_ports)
                driverPorts = self._connector.session.reserve_ports(newPinfoLIst.uri_list, force=force, clear=clear)
                for pInfo in pInfoList.pinfoList:
                    if pInfo in newPinfoLIst.pinfoList:
                        self.chassis[pInfo.chassis]._init(self)
                        self.ports[pInfo.name].card = self.chassis[pInfo.chassis]._create_card(pInfo.slot)
                        self.ports[pInfo.name]._port_driver_obj = driverPorts[pInfo.uri]
                        self.ports[pInfo.name]._discover()
                    reseved_ports.append(self.ports[pInfo.name])
                return reseved_ports
            except Exception as e:
                self._logger.info(self._get_tg_log_title(),'Failed retry #{}\nError: {}'.format(retry, str(e)))
                if retry + 1 < max_attemps:
                    pass
                else:
                    tclVer = self._connector.api._tcl_handler.tcl_ver
                    msg = '{} Failed!!! Tcl server version: {} \nError: {}'.format(self._get_tg_log_title(),tclVer, str(e))
                    self._logger.info(msg)
                    raise Exception(msg)
                    #raise Exception("Failed to reserve ports... maybe reserved by other?\n" + ", ".join(ports_list) + "\n" + str(e))

    def release_ports(self):
        pass


    def load_config_file(self, config_file_dict):
        self._logger.info(self._get_tg_log_title(), self._get_tg_log_message())
        super(self.__class__, self).load_config_file(config_file_dict)
        for port_name, config_file in config_file_dict.items():
            try:
                self.ports[port_name]._port_driver_obj.load_config(config_file)
            except StreamWarningsError as e:
                print (str(e))
            except Exception as e:
                raise Exception("Failed to load config file - " + config_file +
                                ", on port: " + str(self.ports[port_name]) +
                                "\nOriginal exception:\n" + str(e))

    def save_config_file(self, config_file_dict):
        self._logger.info(self._get_tg_log_title(), self._get_tg_log_message())
        super(self.__class__, self).save_config_file(config_file_dict)
        for port_name, config_file in config_file_dict.items():
            try:
                self.ports[port_name]._port_driver_obj.save_config(config_file)
            except StreamWarningsError as e:
                print (str(e))
            except Exception as e:
                raise Exception("Failed to save config file - " + config_file +
                                ", on port: " + str(self.ports[port_name]) +
                                "\nOriginal exception:\n" + str(e))

    def get_all_ports_stats(self):
        self._logger.info(self._get_tg_log_title(), self._get_tg_log_message(), True)
        super(self.__class__, self).get_all_ports_stats()
        stats = IxePortsStats(self._connector.session)
        stats.read_stats()
        for port in self.ports:
            stats_message = ""
            self.ports[port]._update_port_stats(stats)
            stats_message += "{}".format(str(self.ports[port].statistics))
            self._logger.info(port, stats_message)
        self._logger.info("end_level", "end_level")
        return stats.statistics

    def get_all_streams_stats(self):
        self._logger.info(self._get_tg_log_title(), self._get_tg_log_message(), True)
        super(self.__class__, self).get_all_streams_stats()
        stats = IxeStreamsStats(self._connector.session)
        try:
            stats.read_stats()
            for port in self.ports:
                for stream in self.ports[port].streams:
                    self.ports[port].streams[stream]._update_stream_stats(stats)
                    statistics_str = str(self.ports[port].streams[stream].statistics)
                    statistics_dict = json.loads(statistics_str)
                    self._logger.info("tx_stats - port - {}, stream - {}".format(port, stream), "frames_sent:{}\nframes_sent_rate:{}".format(statistics_dict["frames_sent"].replace("\"", ""), statistics_dict["frames_sent_rate"].replace("\"", "")), True)
                    for rx_port in statistics_dict["rx_stats"][0]:
                        rx_dict = statistics_dict["rx_stats"][0][rx_port][0]
                        rx_str = ""
                        for key, val in rx_dict.items():
                            rx_str += "{}:{}\n".format(key, val)
                        rx_str = rx_str.replace("\"", "")
                        rx_str = rx_str.replace("\'", "")
                        self._logger.info(rx_port, rx_str)
                    self._logger.info("end_level", "end_level")
        except Exception as e:
            message = "Could not get streams stats - check if streams\ports are configured to PGID\n{}".format(str(e))
            self._logger.info(self._get_tg_log_title(), message)
            raise Exception(message)
        finally:
            self._logger.info("end_level", "end_level")

    def get_streams_stats_by_list(self, stats_list=None):
        self._logger.info(self._get_tg_log_title(), self._get_tg_log_message(), True)
        super(self.__class__, self).get_streams_stats_by_list(stats_list=stats_list)
        stats = IxeStreamsStats(self._connector.session)
        try:
            stats.read_stats(*stats_list)
            for port in self.ports:
                for stream in self.ports[port].streams:
                    self.ports[port].streams[stream]._update_stream_stats(stats)
                    # statistics_str = str(self.ports[port].streams[stream].statistics)
                    # statistics_dict = json.loads(statistics_str)
                    # self._logger.info("tx_stats - port - {}, stream - {}".format(port, stream),
                    #                   "frames_sent:{}\nframes_sent_rate:{}".format(
                    #                       statistics_dict["frames_sent"].replace("\"", ""),
                    #                       statistics_dict["frames_sent_rate"].replace("\"", "")), True)
                    # for rx_port in statistics_dict["rx_stats"][0]:
                    #     rx_dict = statistics_dict["rx_stats"][0][rx_port][0]
                    #     rx_str = ""
                    #     for key, val in rx_dict.iteritems():
                    #         rx_str += "{}:{}\n".format(key, val)
                    #     rx_str = rx_str.replace("\"", "")
                    #     rx_str = rx_str.replace("\'", "")
                    #     self._logger.info(rx_port, rx_str)
                    # self._logger.info("end_level", "end_level")




                    # stats_message = ""
                    #
                    # stats_message += "{}".format(str(self.ports[port].streams[stream].statistics))
                    # self._logger.info("port - {}, stream - {}".format(port, stream), stats_message)
        except Exception as e:
            message = "Could not get streams stats - check if streams\ports are configured to PGID\n{}".format(str(e))
            self._logger.info(self._get_tg_log_title(), message)
            raise Exception(message)

        self._logger.info("end_level", "end_level")
        return stats.statistics

    def _create_list_of_port_driver_objects(self,list_of_ports=None):
        port_list = []
        if not list_of_ports or type(list_of_ports) is not list or not isinstance(list_of_ports[0], IxExPort):
            list_of_ports = self._create_list_of_port_objects(list_of_ports)
        for port in list_of_ports:
            port_list.append(port._port_driver_obj)
        # if not list_of_ports:
        #     for port in self.ports:
        #         port_list.append(self.ports[port]._port_driver_obj)
        # elif type(list_of_ports) == str:
        #     port_list.append(self.ports[list_of_ports]._port_driver_obj)
        # elif type(list_of_ports) == list:
        #     for port in list_of_ports:
        #         pObj = self.ports[port] if not isinstance(port,IxExPort) else port
        #         port_list.append(pObj._port_driver_obj)
        # else:
        #     raise Exception("port_or_port_list is not a str or list of str of port names")
        return port_list



    def _get_port_name_by_driver_obj(self,driver_obj):
        name = ""
        for port in self.ports:
            if driver_obj is self.ports[port]._port_driver_obj:
                name = port
                break
        return name

    def _get_port_driver_obj_by_name(self, name):
        driver_obj = None
        for port in self.ports:
            if name == self.ports[port]._port_name:
                driver_obj = self.ports[port]._port_driver_obj
                break
        if driver_obj is None:
            self._logger.info(self._get_tg_log_title(), "Could not find a port named: {}".format(name))
            raise Exception("Could not find a port named: {}".format(name))
        return driver_obj

    def _get_stream_driver_obj_by_name(self, port_name, stream_name):
        driver_obj = None
        for port in self.ports:
            if port_name == self.ports[port]._port_name:
                for stream in self.ports[port].streams:
                    if stream_name == self.ports[port].streams[stream]._name:
                        driver_obj = self.ports[port].streams[stream]._stream_driver_obj
                break
        if driver_obj is None:
            self._logger.info(self._get_tg_log_title(), "Could not find a stream named: {} in port named: {}".format(stream_name, port_name))
            raise Exception("Could not find a stream named: {} in port named: {}".format(stream_name, port_name))
        return driver_obj

    def start_traffic(self,port_or_port_list=None, blocking=False, start_packet_groups=True,wait_up = None):
        self._logger.info(self._get_tg_log_title(), self._get_tg_log_message())
        port_or_port_list = super(self.__class__, self).start_traffic(port_or_port_list=port_or_port_list, blocking=blocking,
                                                  start_packet_groups=start_packet_groups,wait_up=wait_up)
        val = self._create_list_of_port_driver_objects(port_or_port_list)
        self._connector.session.start_transmit(blocking, start_packet_groups, *val)

    def stop_traffic(self,port_or_port_list=None):
        self._logger.info(self._get_tg_log_title(), self._get_tg_log_message())
        port_or_port_list = super(self.__class__, self).stop_traffic(port_or_port_list)
        self._connector.session.stop_transmit(*self._create_list_of_port_driver_objects(port_or_port_list))

    def start_capture(self,port_or_port_list=None):
        self._logger.info(self._get_tg_log_title(), self._get_tg_log_message())
        port_or_port_list= super(self.__class__, self).start_capture(port_or_port_list=None)
        self._connector.session.start_capture(*self._create_list_of_port_driver_objects(port_or_port_list))

    def stop_capture(self,port_or_port_list=None, cap_file_name="", cap_mode="buffer"):
        self._logger.info(self._get_tg_log_title(), self._get_tg_log_message())

        TestCurrentDir = ""
        operating_system = platform.system()
        if operating_system.lower() == "windows":
            TestCurrentDir = r"c:/temp/port_1"
        elif operating_system.lower() == "linux":
            TestCurrentDir = r"/tmp/port_1"
        port_or_port_list = super(self.__class__, self).stop_capture(port_or_port_list=port_or_port_list, cap_file_name=cap_file_name,
                                                 cap_mode=cap_mode)

        if cap_mode == "buffer":
            ports_obj_list = self._create_list_of_port_driver_objects(port_or_port_list)

            self._connector.session.stop_capture(TestCurrentDir, IxeCapFileFormat.mem, *ports_obj_list)
            for port in ports_obj_list:
                port_name = self._get_port_name_by_driver_obj(port)
                nPacket_key = "capture {}".format(port.uri)
                frame_count_in_buff = port.objects[nPacket_key].nPackets
                start_frame = 1
                stop_frame = frame_count_in_buff + 1
                step_frame = 1
                res = [s for s in range(start_frame, stop_frame, step_frame)]
                temp_buff_list = port.get_cap_frames(*res)

                regex = re.compile(r"\s*|\t*", re.IGNORECASE)
                for x, line in enumerate(temp_buff_list):
                    temp_buff_list[x] = regex.sub("", line)
                temp_buff_list = temp_buff_list
                self.ports[port_name].capture_buffer = temp_buff_list
                temp_buff_list = None
        # elif cap_mode == "file_buffer":
        #
        #     try:
        #         self._port_driver_obj.stop_capture(TestCurrentDir, cap_file_format=IxeCapFileFormat.txt)
        #         if self._port_driver_obj.cap_file_name != None:
        #             temp_buff_list = self._port_driver_obj.get_cap_file()[2:]
        #             temp_buff = '\n'.join(temp_buff_list)
        #             temp_buff_list = re.findall(r'\d+\s*\d+:\d+:\d+.\d*\s*(.*)\t\d*\t', temp_buff, flags=re.MULTILINE)
        #
        #             regex = re.compile(r"\s*|\t*", re.IGNORECASE)
        #             for x, line in enumerate(temp_buff_list):
        #                 temp_buff_list[x] = regex.sub("", line)
        #             temp_buff_list = temp_buff_list
        #             # \d+\s*\d+:\d+:\d+.\d*\s*(.*)\t\d*\t
        #             self.capture_buffer = temp_buff_list
        #             try:
        #                 os.remove(self._port_driver_obj.cap_file_name)
        #             except Exception, e:
        #                 print ("capture_buffer_file was not deleted\n" + str(e))
        #     except Exception, e:
        #         print ("no frames were captured or there was another issue...\n" + str(e))
        else:
            raise Exception("capture mode not supported: " + cap_mode)

    def hw_refresh(self):
        self._logger.info(self._get_tg_log_title(), self._get_tg_log_message())
        try:
            self._connector.refresh()
            for port in self.ports:
                #self.ports[port]._hw_sync()
                for stream in self.ports[port].streams:
                    # self.ports[port].streams[stream].packet._hw_sync(self.ports[port].streams[stream])
                    self.ports[port].streams[stream]._hw_sync()
            # self.ports["my_port1"].streams["my_stream1"].packet._hw_sync()
            # self.ports["my_port1"].streams["my_stream1"].packet.mac.da.value = \
            #     self.ports["my_port1"].streams["my_stream1"]._stream_driver_obj.da
        except Exception as e:
            print(str(e))
    def configure_advanced_stats(self, rx_port_list=None, tx_streams_list=None, sequence_checking=True,
                                 data_integrity=True, time_stamp=True, starting_offset=40, prbs=False):
        self._logger.info(self._get_tg_log_title(), self._get_tg_log_message())
        rx_port_list_to_driver = []
        if rx_port_list:
            for rx_port in rx_port_list:
                rx_port_list_to_driver.append(self._get_port_driver_obj_by_name(rx_port))


        tx_streams_list_to_driver = {}
        if tx_streams_list:
            for tx_port in tx_streams_list.keys():
                tx_port_obj = self._get_port_driver_obj_by_name(tx_port)
                tx_streams_list_to_driver[tx_port_obj] = []
                for tx_stream in tx_streams_list[tx_port]:
                    tx_streams_list_to_driver[tx_port_obj].append(self._get_stream_driver_obj_by_name(tx_port, tx_stream))


        super(self.__class__, self).configure_advanced_stats(rx_port_list=rx_port_list_to_driver,
                                                             tx_streams_list=tx_streams_list_to_driver,
                                                             starting_offset=starting_offset,
                                                             sequence_checking=sequence_checking,
                                                             data_integrity=data_integrity,
                                                             time_stamp=time_stamp, prbs=False)
        try:
            if prbs == True:
                self._connector.session.set_prbs(rx_ports=rx_port_list_to_driver,
                                                     tx_ports=tx_streams_list_to_driver)
            else:
                self._connector.session.set_stream_stats(rx_ports=rx_port_list_to_driver,
                                                     tx_ports=tx_streams_list_to_driver,
                                                     sequence_checking=sequence_checking,
                                                     data_integrity=data_integrity,
                                                     timestamp=time_stamp,
                                                     start_offset=starting_offset)
        except StreamWarningsError as e:
            self._logger.info(self._get_tg_log_title(), "StreamWarningsError:\n{}".format(str(e)))
        except Exception as e:
            self._logger.info(self._get_tg_log_title(), "Failed to configure_advanced_stats\nOriginal exception:\n" + str(e))
            raise Exception("Failed to configure_advanced_stats\nOriginal exception:\n" + str(e))

    def get_advanced_stats(self,stats_list=None):
        self._logger.info(self._get_tg_log_title(), self._get_tg_log_message(), True)
        super(self.__class__, self).get_advanced_stats()
        stats = IxeStreamsStats(self._connector.session)
        try:
            if stats_list :
                stats.read_stats(*stats_list)
            else:
                stats.read_stats()
            for port in self.ports:
                for stream in self.ports[port].streams:
                    self.ports[port].streams[stream]._update_stream_stats(stats)
        except Exception as e:
            message = "Could not get streams stats - check if streams\ports are configured to PGID\n{}".format(str(e))
            self._logger.info(self._get_tg_log_title(), message)
            raise Exception(message)
        self._logger.info("end_level", "end_level")
        return stats.statistics

    def start_packet_groups(self, clear_time_stamps=True, port_list=list()):
        self._logger.info(self._get_tg_log_title(), self._get_tg_log_message())
        port_list_to_driver = []
        if port_list:
            for port in port_list:
                port_list_to_driver.append(self._get_port_driver_obj_by_name(port))
        super(self.__class__, self).start_packet_groups(clear_time_stamps=clear_time_stamps, port_list=port_list_to_driver)
        self._connector.session.start_packet_groups(clear_time_stamps=clear_time_stamps, *port_list_to_driver)

    def clear_all_stats(self, port_list=list()):
        self._logger.info(self._get_tg_log_title(), self._get_tg_log_message())
        # port_list_to_driver = []
        # if port_list:
        #     for port in port_list:
        #         port_list_to_driver.append(self._get_port_driver_obj_by_name(port))
        super(self.__class__, self).clear_all_stats(port_list=port_list)
        #self._connector.session.clear_all_stats(*port_list_to_driver)

    def wait_for_link_up(self, timeout=60, port_list=list()):
        self._logger.info(self._get_tg_log_title(), self._get_tg_log_message())
        port_list_to_driver = []
        if port_list:
            for port in port_list:
                port_list_to_driver.append(self._get_port_driver_obj_by_name(port))
        else:
            for port in self.ports:
                port_list_to_driver.append(self._get_port_driver_obj_by_name(port))
        super(self.__class__, self).wait_for_link_up(timeout=timeout, port_list=port_list_to_driver)
        ports_for_report = ""
        if port_list:
            ports_for_report = "{}".format(port_list)
        else:
            for port in self.ports:
                ports_for_report += "{}(uri={}), ".format(self.ports[port]._port_name, self.ports[port]._port_uri)
            # ports_for_report = "{}".format(self.ports)
        try:
            self._connector.session.wait_for_up(timeout, port_list_to_driver)
        except Exception as e:
            message = "wait_for_link_up failed.\nPorts included in function: {}\nuri of ports not in up state: {}".format(ports_for_report, str(e))
            self._logger.info(self._get_tg_log_title(), message)
            raise Exception(message)