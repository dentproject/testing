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

from UnifiedTG.IxEx.IxCreator import ixCreator,ixVirtualSshCreator
from UnifiedTG.IxNetwork.IxNetworkCreator import ixnCreator
from UnifiedTG.Ostinato.OstinatoCreator import ostinatoCreator
from UnifiedTG.Unified.TGEnums import TGEnums
from UnifiedTG.Xena.XenaCreator import xenaCreator
from UnifiedTG.Trex.TrexCreator import TrexCreator
from UnifiedTG.STC.SpirentCreator import spirentCreator
from UnifiedTG.IxNetworkRestPy.IxNetworkRestPyCreator import ixnRestPyCreator

class objectCreator(object):

    _creators = {TGEnums.TG_TYPE.Ixia: ixCreator,
                 TGEnums.TG_TYPE.Ostinato: ostinatoCreator,
                 TGEnums.TG_TYPE.IxiaVirtualSSH: ixVirtualSshCreator,
                 TGEnums.TG_TYPE.IxiaSSH: ixVirtualSshCreator,
                 TGEnums.TG_TYPE.Xena: xenaCreator,
                 TGEnums.TG_TYPE.Trex: TrexCreator,
                 TGEnums.TG_TYPE.Spirent : spirentCreator,
                 TGEnums.TG_TYPE.IxNetwork: ixnCreator,
                 TGEnums.TG_TYPE.IxNetworkRestPy: ixnRestPyCreator
                 }

    def __init__(self, type):
        self._type = type
        try:
            basestring
        except NameError:
            basestring = str
        if isinstance(type, basestring):
            type = TGEnums.TG_TYPE._value2member_map_[type.lower()]
        self.creator = objectCreator._creators[type]()

    def create_tg(self, server_host, login,rsa_path):
        tg = self.creator.create_tg(server_host, login) if rsa_path is None else self.creator.create_tg(server_host, login,rsa_path=rsa_path)
        tg._objCreator = self
        return tg

    def create_chassis(self,ip):
        chassis = self.creator.create_chassis(ip)
        chassis.creator = self
        return chassis

    def create_card(self,id,typeId):
        card = self.creator.create_card(id,typeId)
        card._objCreator = self
        return card

    def create_port(self,pUri, pName):
        port = self.creator.create_port(pUri, pName)
        port._objCreator = self
        return port

    def create_stream(self,sName):
        return self.creator.create_stream(sName)

    def create_router(self):
        return self.creator.create_router()