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

import logging,sys

from UnifiedTG.Unified.TG import TG
from UnifiedTG.Xena.XenaDriver import xenaConnector
from UnifiedTG.Unified.TgInfo import *
from UnifiedTG.Unified.Port import Port

from trafficgenerator.tgn_utils import ApiType
from xenavalkyrie.xena_app import init_xena

api = ApiType.socket

logger = logging.getLogger('log')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))


class xenaTg(TG):
    def __init__(self, server_host, login_name, server_tcp_port = 7878, api_type = None):
        super(self.__class__, self).__init__(server_host, login_name, server_tcp_port)
        self._connector = xenaConnector(self)

    def _connect(self, chassis):
        super(self.__class__, self)._connect(chassis)

    def reserve_ports(self, ports_list,force=False, clear=True):
        self._logger.info(self._get_tg_log_title(), self._get_tg_log_message())
        try:
            reseved_ports = []  # type: list[Port]#TODO
            super(self.__class__, self).reserve_ports(ports_list, force, clear)
            pInfoList = tgPortsInfo(ports_list)
            driverPorts = self._connector.session.reserve_ports(pInfoList.uri_list, force=force, reset=clear)
            for pInfo in pInfoList.pinfoList:
                self.chassis[pInfo.chassis]._init(self)
                self.ports[pInfo.name]._port_driver_obj = driverPorts[pInfo.uri]
                reseved_ports.append(self.ports[pInfo.name])
            return reseved_ports
        except Exception as e:
            raise Exception("Failed to reserve ports... maybe reserved by other?\n" + ", ".join(ports_list) + "\n" + str(e))

    def start_traffic(self, port_or_port_list=None, blocking=False, start_packet_groups=True, wait_up=None):
        # type: (list[Port], Bool, Bool) -> None
        port_or_port_list = super(self.__class__, self).start_traffic(port_or_port_list=port_or_port_list, blocking=blocking,
                                                  start_packet_groups=start_packet_groups)
        for p in port_or_port_list:
            p.start_traffic(blocking)

    def stop_traffic(self, port_or_port_list=None):
        # type: (list[Port]) -> None
        port_or_port_list = super(self.__class__, self).stop_traffic(port_or_port_list)
        for p in port_or_port_list:
            p.stop_traffic()