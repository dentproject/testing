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

from UnifiedTG.Unified.TG import TG
from UnifiedTG.Ostinato.OstinatoDriver import ostinatoConnector
from UnifiedTG.Unified.TgInfo import *
from UnifiedTG.Unified.Port import Port
from ostinato.core import ost_pb

class ostinatoTg(TG):
    def __init__(self, server_host, login_name, server_tcp_port = 7878, api_type = None):
        super(self.__class__, self).__init__(server_host, login_name, server_tcp_port)
        self._connector = ostinatoConnector
        self._connector.init(server_host)

    def _connect(self, chassis):
        super(self.__class__, self)._connect(None)
        # do specific

    def reserve_ports(self, ports_list,force=False, clear=True):
        super(self.__class__, self).reserve_ports(ports_list,force, clear)
        pInfoList = tgPortsInfo(ports_list)
        reseved_ports = []  # type: list[Port]
        for pInfo in pInfoList.pinfoList:
            ip = ""
            if pInfo.chassis == 'lb':
                pId,pConf = ostinatoConnector._getPortDataConfigDebugLoopback(pInfo.pid)
            else:
                pId,pConf = ostinatoConnector.getPortDataConfig(pInfo.pid)
            self.ports[pInfo.name]._port_driver_obj = pId
            self.ports[pInfo.name]._config = pConf
            self.ports[pInfo.name]._config.port[0].user_name = "{}:{}".format(pInfo.name,ip) + " reserved by: "+self._login_name
            self.ports[pInfo.name].stop_traffic()
            if clear:
                self.ports[pInfo.name].del_all_streams()
                self.ports[pInfo.name].clear_port_statistics()
            reseved_ports.append(self.ports[pInfo.name])
        return reseved_ports

    def start_traffic(self, port_or_port_list=None, blocking=False, start_packet_groups=True, wait_up = None):
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

    def get_all_ports_stats(self):
        port_or_port_list = super(self.__class__, self).get_all_ports_stats()
        all_stats = OrderedDict()
        for p in port_or_port_list:
            p_stats = p.get_stats()
            all_stats[p._port_uri] = p_stats
        return all_stats

    def start_capture(self,port_or_port_list=None):
        """
        Starts capture on all ports or ports names list.
        :param port_or_port_list:
        :type port_or_port_list: list of port names or none for all ports in session.
        """
        port_or_port_list = super(self.__class__, self).start_capture(port_or_port_list)
        for p in port_or_port_list:
            p.start_capture()

    def stop_capture(self,port_or_port_list=None, cap_file_name="", cap_mode="buffer"):
        """
        :param port_or_port_list:
        :type port_or_port_list: list of port names or none for all ports in session.
        :param cap_file_name: currently not implemented.
        :param cap_mode: buffer mode - loops over the frames captured frames on port and append them\n
        to capture_buffer list.\n file_buffer mode - currently not supported.
        The capture_buffer is a list of str of bytes with space separation ("00 11 22 33...").
        """
        port_or_port_list = super(self.__class__, self).stop_capture(port_or_port_list)
        for p in port_or_port_list:
            p.stop_capture()