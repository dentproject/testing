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

from trafficgenerator.tgn_utils import ApiType
from ixnetwork.ixn_app import init_ixn
from ixnetwork.ixn_statistics_view import IxnStatsTypes
from UnifiedTG.IxNetwork.IxNetworkPort import ixnPort
from UnifiedTG.Unified.TG import TG, Traffic, Protocols, QuickTests
from UnifiedTG.Unified.TgInfo import tgPortsInfo


class ixnTG(TG):
    def __init__(self, server_host, login_name, server_tcp_port=8009, api_type=ApiType.tcl, api_path=""):
        super(self.__class__, self).__init__(server_host, login_name, server_tcp_port)
        self._connector = init_ixn(api_type, self._logger, api_path)
        self.traffic = ixnTraffic()
        self.protocols = ixnProtocols()
        self.quick_tests = ixnQuickTests()

    def _connect(self, chassisList = None):
        if not self._connector.connected:
            self._connector.connect(api_server=self._server_host,api_port=self._server_tcp_port)

    def load_config_file(self, config_file):
        self._connect()
        self._connector.new_config()
        self._connector.load_config(config_file)
        self._connector.commit()


    def reserve_ports(self,ports_list,force=False,clear=False):
        self._logger.info(self._get_tg_log_title(), self._get_tg_log_message())
        super(self.__class__, self).reserve_ports(ports_list, force, clear)
        driverPorts = self._connector.reserve_loaded_ports(ports_list, force=force, clear=clear)
        pInfoList = tgPortsInfo(ports_list)
        reseved_ports = []  # type: list[ixnPort]
        for pInfo in pInfoList.pinfoList:
            self.ports[pInfo.name]._port_driver_obj = driverPorts[pInfo.name]
            reseved_ports.append(self.ports[pInfo.name])
        return reseved_ports

    def get_all_ports_stats(self):
        res = self._connector.read_stats(IxnStatsTypes.Port)
        for p_name in res:
            res_stats = res[p_name]
            p_stats = self.ports[p_name].statistics
            p_stats.frames_sent = res_stats['Frames Tx.']
            p_stats.frames_sent_rate = res_stats['Frames Tx. Rate']
            p_stats.framesReceived = res_stats['Valid Frames Rx.']
            p_stats.frames_received_rate = res_stats['Valid Frames Rx. Rate']
            p_stats.bits_sent = res_stats['Bits Sent']
            p_stats.bits_sent_rate = res_stats['Tx. Rate (bps)']
            p_stats.bits_received = res_stats['Bits Received']
            p_stats.bits_received_rate = res_stats['Rx. Rate (bps)']
            p_stats.bytes_sent = res_stats['Bytes Tx.']
            p_stats.bytes_sent_rate = res_stats['Bytes Tx. Rate']
            p_stats.bytes_received = res_stats['Bytes Rx.']
            p_stats.bytes_received_rate = res_stats['Bytes Rx. Rate']
            p_stats.crc_errors = res_stats['CRC Errors']
        return res


class ixnTraffic(Traffic):

    def l23_start(self, blocking=False):
        self._parent._connector.l23_traffic_start(blocking)

    def l23_stop(self):
        self._parent._connector.l23_traffic_stop()

    def apply(self):
        self._parent._connector.traffic_apply()

    def read_item_stats(self):
        self.item_stats = self._parent._connector.read_stats(IxnStatsTypes.TrafficItem)
        return self.item_stats



class ixnProtocols(Protocols):

    def start(self,protocol=None):
        self._parent._connector.protocol_start(protocol)

    def stop(self,protocol=None):
        self._parent._connector.protocol_stop(protocol)

    def read_global_stats(self):
        self.global_stats = self._parent._connector.read_stats(IxnStatsTypes.GlobalProtocol)
        return self.global_stats

    def read_flow_stats(self):
        self.flow_stats = self._parent._connector.read_stats(IxnStatsTypes.Flow)
        return self.flow_stats

    def action(self,protocol,action):
        self._parent._connector.protocol_action(protocol,action)


class ixnQuickTests(QuickTests):

    def apply(self,name='QuickTest1'):
        self._parent._connector.quick_test_apply(name)

    def start(self,name='QuickTest1',blocking=False, timeout=3600):
        return self._parent._connector.quick_test_start( name, blocking, timeout)

    def stop(self,name='QuickTest1'):
        self._parent._connector.quick_test_stop(name)

    def wait_for_status(self,name='QuickTest1', status=False, timeout=3600):
        return self._parent._connector.wait_quick_test_status( name, status, timeout)


    def read_flow_view(self):
        self.flow_view = self._parent._connector.read_stats(IxnStatsTypes.FlowView)
        return self.flow_view