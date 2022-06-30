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

from pytrex.trex_port import PortState
from UnifiedTG.Unified.TgInfo import tgPortsInfo
from UnifiedTG.Unified.TG import TG
from UnifiedTG.Trex.TrexDriver import init_trex

class StreamData(object):
    def __init__(self, name, src, src_port, dst, dst_port, stat_id, mac=False, src_mac=None, dst_mac=None):
        self.src = src
        self.src_port = src_port
        self.dst = dst
        self.dst_port = dst_port
        self.name = name
        self.stat_id = stat_id
        self.mac = mac
        self.src_mac = src_mac
        self.dst_mac = dst_mac

class Trex(TG):
    """ Represents Trex.
    """
    def __init__(self, server_host, login_name, server_tcp_port=None, api_type=None):
        super(self.__class__, self).__init__(server_host, login_name, server_tcp_port)
        self._connector = init_trex(logger=self._logger, username=login_name)

    def _connect(self,  chassisList):
        super(self.__class__, self)._connect(chassisList)

    def connect(self):
        self._connector.add(chassis_ip=self._server_host)

    def reserve_ports(self, ports_list, force=False, clear=True):
        self._logger.info(self._get_tg_log_title(), self._get_tg_log_message())
        try:
            reseved_ports = []  # type: list[Port]
            super(self.__class__, self).reserve_ports(ports_list, force, clear)
            pInfoList = tgPortsInfo(ports_list)
            driverPorts = self._connector.reserve_ports(pInfoList.uri_list, force=force, reset=clear)
            for pInfo in pInfoList.pinfoList:
                self.chassis[pInfo.chassis]._init(self)
                self.ports[pInfo.name]._port_driver_obj = driverPorts[pInfo.uri]
                reseved_ports.append(self.ports[pInfo.name])
            return reseved_ports
        except Exception as e:
            raise Exception("Failed to reserve ports... maybe reserved by other?\n" + ", ".join(ports_list) + "\n" + str(e))


    def load_config_file(self, config_file_dict):
        self._logger.info(self._get_tg_log_title(), self._get_tg_log_message())
        super(self.__class__, self).load_config_file(config_file_dict)
        for port_name, config_file in config_file_dict.items():
            try:
                # profile = STLProfile.load_yaml(config_file)
                # self.ports[port_name]._port_driver_obj.add_streams(profile.get_streams())
                self.ports[port_name]._port_driver_obj.remove_all_streams()
                assert self.ports[port_name]._port_driver_obj.get_port_state() == PortState.Idle
                self.ports[port_name]._port_driver_obj.load_streams(config_file)
                self.ports[port_name]._port_driver_obj.write_streams()
                assert self.ports[port_name]._port_driver_obj.get_port_state() == PortState.Streams
            except Exception as e:
                raise Exception("Failed to load config file - " + config_file +
                                ", on port: " + str(self.ports[port_name]) +
                                "\nOriginal exception:\n" + str(e))

    def start_traffic(self, port_or_port_list=None, blocking=False, start_packet_groups=True, wait_up=None):
        # type: (list[Port], Bool, Bool) -> None
        port_or_port_list = super(self.__class__, self).start_traffic(port_or_port_list=port_or_port_list, blocking=blocking,
                                                                      start_packet_groups=start_packet_groups)
        self._connector.start_traffic(blocking, *[p._port_driver_obj for p in port_or_port_list])

    def stop_traffic(self, port_or_port_list=None):
        # type: (list[Port]) -> None
        port_or_port_list = super(self.__class__, self).stop_traffic(port_or_port_list)
        self._connector.stop_traffic(*[p._port_driver_obj for p in port_or_port_list])

    def get_all_ports_stats(self):
        self._logger.info(self._get_tg_log_title(), self._get_tg_log_message(), True)
        super(self.__class__, self).get_all_ports_stats()
        for port in self._create_list_of_port_objects():
            stats_message = ""
            port._update_port_stats(port._port_driver_obj.read_stats())
            stats_message += "{}".format(str(self.ports[port._port_name].statistics))
            self._logger.info(port, stats_message)
        self._logger.info("end_level", "end_level")

    @staticmethod
    def _get_max_ip_string(ip):
        ctr = 0
        i = 0
        string = ""
        while ctr < 2:
            string = string + ip[i]
            if ip[i] == '.':
                ctr = ctr + 1
            i = i + 1
        string = string + '255.255'
        return string

    # def _create_streams(self, stream_data, packet_size, pps, count):
    #     # returns: List[STLStream]
    #     if stream_data.mac:
    #         base_pkt = Ether(src=stream_data.src_mac, dst=stream_data.dst_mac) / \
    #                    IP(dst=stream_data.dst) / \
    #                    UDP(dport=stream_data.dst_port, sport=stream_data.src_port)
    #     else:
    #         base_pkt = Ether() / \
    #                    IP(dst=stream_data.dst) / \
    #                    UDP(dport=stream_data.dst_port, sport=stream_data.src_port)
    #     pad = max(0, packet_size - len(base_pkt)) * 'x'
    #     print(self._get_max_ip_string(stream_data.src))
    #     vm = STLScVmRaw([STLVmFlowVar(name="ip_src",
    #                                   min_value=stream_data.src,
    #                                   max_value=self._get_max_ip_string(stream_data.src),
    #                                   size=4,
    #                                   op="random"),
    #                      STLVmWrFlowVar(fv_name="ip_src",
    #                                     pkt_offset="IP.src"),  # write ip to packet IP.src
    #                      STLVmFixIpv4(offset="IP")  # fix checksum
    #                      ],
    #                     split_by_field="ip_src" # cache the packets, much better performance
    #                     )
    #     streams = []
    #     pkt = STLPktBuilder(pkt=base_pkt / pad, vm=vm)
    #     for i in range(0,count):
    #         stream = STLStream(name=stream_data.name,
    #                            packet=pkt,
    #                            mode=STLTXCont(pps=pps),
    #                            mac_src_override_by_pkt=stream_data.src_mac,
    #                            mac_dst_override_mode=stream_data.dst_mac)
    #         streams.append(stream)
    #     return streams

    # def add_traffic_profile(self, ports, stream_data, count, packet_size, pps):
    #     streams = self._create_streams(stream_data, packet_size, pps, count)
    #     for port_name in ports:
    #         self.ports[port_name]._port_driver_obj.add_streams(streams)
    #         self.ports[port_name].streams = streams

    def reset(self):
        self._logger.info(self._get_tg_log_title(), self._get_tg_log_message(), True)
        self._connector.servers[self._server_host].reset()
        self.clear_all_stats()

    def set_prom_mode(self, ports):
        self._logger.info(self._get_tg_log_title(), self._get_tg_log_message(), True)
        self._connector.servers[self._server_host].set_port_attr(ports, promiscuous=True)

    def disconnect(self):
        super(self.__class__, self).disconnect()
        self._logger.info(self._get_tg_log_title(), self._get_tg_log_message(), True)
        self._connector.servers[self._server_host].disconnect()

    def clear_all_stats(self, port_list=list()):
        self._logger.info(self._get_tg_log_title(), self._get_tg_log_message())
        super(self.__class__, self).clear_all_stats(port_list=port_list)
        self._connector.servers[self._server_host].clear_stats()