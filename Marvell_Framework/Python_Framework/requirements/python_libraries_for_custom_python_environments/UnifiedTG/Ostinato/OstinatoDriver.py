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

import sys
import ifaddr
from future.utils import with_metaclass

from ostinato.core import DroneProxy, ost_pb

from UnifiedTG.Unified.Utils import Converter
import sys
import ifaddr
from future.utils import with_metaclass

from ostinato.core import DroneProxy, ost_pb

from UnifiedTG.Unified.Utils import Converter


class ConnectorMeta(type):
    @property
    def connected(self):
        return True if hasattr(self._drone.channel,"sock") else False


class ostinatoConnector(with_metaclass(ConnectorMeta, object)):
    _drone = None

    @classmethod
    def init(cls, host_name):
        cls._drone = DroneProxy(host_name)
        cls._adaptersInfo = ifaddr.get_adapters()

    @classmethod
    def connect(cls, login):
        cls._drone.connect()
        cls._PortConfigList = cls._drone.getPortConfig(cls._drone.getPortIdList())

    # @property
    # def connected(self):
    #     return False

    @classmethod
    def drone(cls):
        return cls._drone

    @classmethod
    def getPortDataByIP(cls, ip):
        try:
            nicInfo = list(filter(lambda p : p.ips[0].ip == ip, cls._adaptersInfo))[0]

            PY3K = sys.version_info >= (3, 0)
            if PY3K:
                searchName = nicInfo.name.decode('utf-8')
            else:
                searchName = nicInfo.name

            ostPortInfo = list(filter(lambda ostPrt: searchName in ostPrt.name ,cls._PortConfigList.port[:]))[0]
            pIdList = ost_pb.PortIdList()
            pIdList.port_id.add().id = ostPortInfo.port_id.id
            pConfig = cls._drone.getPortConfig(pIdList)
        except Exception as e:
            raise Exception("Failed to assotiate ip to Nic... maybe wrong ip?\n" + ip + "\n" + str(e))
        return pIdList,pConfig

    @classmethod
    def getPortDataConfig(cls,pid):
        try:
            isIp = False if pid < 256 else Converter.intIp2string(pid)
            searchName = 'slan0'+str(pid) if not isIp else cls._portNameByIP(isIp)
            ostPortInfo = list(filter(lambda ostPrt: searchName in ostPrt.name.lower() ,cls._PortConfigList.port[:]))[0]
            pIdList = ost_pb.PortIdList()
            pIdList.port_id.add().id = ostPortInfo.port_id.id
            pConfig = cls._drone.getPortConfig(pIdList)
        except Exception as e:
            raise Exception("Failed to assotiate ip to Nic... maybe wrong ip?\n"  + "\n" + str(e))
        return pIdList,pConfig

    @classmethod
    def _portNameByIP(cls,ip):
        nicInfo = list(filter(lambda p: p.ips[0].ip == ip, cls._adaptersInfo))[0]
        PY3K = sys.version_info >= (3, 0)
        if PY3K:
            searchName = nicInfo.name.decode('utf-8')
        else:
            searchName = nicInfo.name

        return searchName
    @classmethod
    def _getPortDataConfigDebugLoopback(cls, pid):
        try:
            for p1 in cls._PortConfigList.port[:]:
                res = [p for p in cls._PortConfigList.port[:] if p.name == p1.name]
                if len(res) > 1:
                    continue
            ostPortInfo = res[pid]
            pIdList = ost_pb.PortIdList()
            pIdList.port_id.add().id = ostPortInfo.port_id.id
            pConfig = cls._drone.getPortConfig(pIdList)
        except Exception as e:
            raise Exception("Failed to assotiate ip to Nic... maybe wrong ip?\n"  + "\n" + str(e))
        return pIdList,pConfig
