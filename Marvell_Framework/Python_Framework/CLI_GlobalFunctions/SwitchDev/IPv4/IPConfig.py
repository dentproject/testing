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

import json5
from CLI_GlobalFunctions.SwitchDev.CLICommands.EntityConfig import GeneralEntityConfig
from CLI_GlobalFunctions.SwitchDev.CLICommands.Executer import GlobalGetterSetter


class IPConfig(GeneralEntityConfig):

    def __init__(self, switchDevDutPort, otherDutChannel, executer=True):
        super(IPConfig, self).__init__(switchDevDutPort, otherDutChannel, executer)
        self._ipAdrr = ''  # type: str
        self._defGw = None

    @classmethod
    def delRoute(cls, addr, mask, via, otherDut=False):
        if not otherDut:
            GlobalGetterSetter().getter.execute(f"ip route del {addr}/{mask} via {via}")
        else:
            GlobalGetterSetter().getterOtherDut.execute(f"ip route del {addr}/{mask} via {via}")

    @classmethod
    def setRoute(self, addr, mask, via, otherDut=False):
        if not otherDut:
            GlobalGetterSetter().getter.execute(f"ip route add {addr}/{mask} via {via}")
        else:
            GlobalGetterSetter().getterOtherDut.execute(f"ip route add {addr}/{mask} via {via}")

    @classmethod
    def getIpRoute(cls, dev=None):
        x = json5.loads(GlobalGetterSetter().getter.ip('-j', 'route', 'show', 'dev' if dev else None, dev.name))

    def setIP(self, addr, mask):
        ret = self._getter.ip_addr_add(f"{addr}/{mask}", 'dev', self._switchdevInterface.name)
        if not ret:
            self._ipAdrr = addr
        return ret

    def delIP(self, addr, mask):
        return self._setter.ip_addr_del(f"{addr}/{mask}", 'dev', self._switchdevInterface.name)

    def getNeigh(self):
        ret = self._getter.ip_neigh_show(dev=self._switchdevInterface.name)
        return ret
