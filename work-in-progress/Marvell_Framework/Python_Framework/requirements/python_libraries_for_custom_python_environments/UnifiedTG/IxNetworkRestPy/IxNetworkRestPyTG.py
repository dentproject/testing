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
from UnifiedTG.IxNetworkRestPy.IxNetworkRestPyImport import *
from UnifiedTG.IxNetworkRestPy.IxNetworkRestPyPort import ixnRestpyPort
from UnifiedTG.IxNetworkRestPy.IxNetworkRestPyStats import ixNetworkRestPyStats
from UnifiedTG.Unified.TG import TG, Traffic, Protocols, QuickTests
from UnifiedTG.Unified.TgInfo import tgPortsInfo
from UnifiedTG.IxNetworkRestPy.IxNetworkRestPyHelper import TgHelper


class ixNetworkRestPyTG(TG):
    def __init__(self, server_host='127.0.0.1', login_name='restpy'):
        server_tcp_port = 11009
        super(self.__class__, self).__init__(server_host, login_name, server_tcp_port)
        self.test_platform = TestPlatform(self._server_host, rest_port=self._server_tcp_port, platform='windows')
        self.test_platform.Trace = 'request_response'
        self._sessions = self.test_platform.Sessions.add()  # type: Sessions
        self.ixnetwork = self._sessions.Ixnetwork  # type: Ixnetwork
        self._portMap = PortMapAssistant(self.ixnetwork)
        self.stats = ixNetworkRestPyStats(self.ixnetwork)
        self.ixnetwork.NewConfig()
        self.topology = OrderedDict()  # type: list[Topology]
        self.device_group = OrderedDict()  # type: list[DeviceGroup]
        self.traffic_items = OrderedDict()  # type: list[TrafficItem]
        self.endpoints = OrderedDict()  # type: list[EndpointSet]
        self.ixnHelper = TgHelper(self)

    def _connect(self, chassisList = None):
        pass

    def add_topology(self, topology_name, ports=None):
        self.ixnHelper.add_topology(topology_name,ports)
    #     self.topology[topology_name] = self.ixnetwork.Topology.add(topology_name)
    #     is_object = True if isinstance(ports[0], ixnRestpyPort) else False
    #     if ports:
    #         vports = \
    #             [p._port_driver_obj for p in ports] if is_object else [self.ports[p]._port_driver_obj for p in ports]
    #         self.topology[topology_name].Vports = vports
    #

    def add_device_group(self,topology_name,device_group_name):
        self.ixnHelper.add_device_group(topology_name,device_group_name)
        # self.device_group[device_group_name] = self.topology[topology_name].DeviceGroup.add(1,device_group_name)

    def reserve_ports(self, ports_list,force=False,clear=False):
        self._logger.info(self._get_tg_log_title(), self._get_tg_log_message())
        super(self.__class__, self).reserve_ports(ports_list, force, clear)
        pInfoList = tgPortsInfo(ports_list)
        reseved_ports = []  # type: list[ixnRestpyPort]
        for pInfo in pInfoList.pinfoList:
            self.ports[pInfo.name]._port_driver_obj = self._portMap.Map(IpAddress=pInfo.chassis, CardId=pInfo.slot, PortId=pInfo.pid, Name=pInfo.name)
            reseved_ports.append(self.ports[pInfo.name])
        self._portMap.Connect(ForceOwnership=force)
        return reseved_ports

    def create_scenario(self, topologies):
        self.ixnHelper.create_scenario(topologies)

    def addl23(self, name, traffic_type, endpoints,generate=False):
        return self.ixnHelper.add_L2_3(name, traffic_type, endpoints, generate)

    def load_config_file(self, config_file):
        # load the saved configuration
        self.ixnetwork.LoadConfig(config_file)

class ixNetworkRestPyTraffic(Traffic):

    def l23_start(self, blocking=False):
        self._parent._connector.l23_traffic_start(blocking)

    def l23_stop(self):
        self._parent._connector.l23_traffic_stop()

    def apply(self):
        self._parent._connector.traffic_apply()

    def read_item_stats(self):
        self.item_stats = self._parent._connector.read_stats(IxnStatsTypes.TrafficItem)
        return self.item_stats
