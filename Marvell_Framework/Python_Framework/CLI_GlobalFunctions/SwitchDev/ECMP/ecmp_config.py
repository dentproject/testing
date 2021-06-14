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

from CLI_GlobalFunctions.SwitchDev.CLICommands.Executer import GlobalGetterSetter
from CLI_GlobalFunctions.SwitchDev.IPv4.IPv4Config import IPv4Config


class ECMP_config(IPv4Config):

    _fibMultipathHashPolicy = 0

    def __init__(self, switchDevInterface, otherDutChannel=False, executer=True):
        """
        :param switchDevInterface: the entity to be configured (e.g, bond, port, bridge)
        :param otherDutChannel: True if there is another DUT; False otherwise
        """
        super(ECMP_config, self).__init__(switchDevInterface, otherDutChannel, executer)

    @classmethod
    def setFibMultipathHashPolicy(cls, v):
        GlobalGetterSetter().setter.sysctl('-w', f'net.ipv4.fib_multipath_hash_policy={v}')
        cls._fibMultipathHashPolicy = v

    @classmethod
    def getFibMultipathHashPolicy(cls):
        return cls._fibMultipathHashPolicy

    @classmethod
    def setIgnoreRoutesWithLinkdown(cls, v):
        GlobalGetterSetter().setter.sysctl('-w', f'net.ipv4.conf.default.ignore_routes_with_linkdown={v}')

    @classmethod
    def setECMPRoute(cls, dest_net, next_hop2, next_hop3, next_hop4):
        GlobalGetterSetter().setter.ip_route_add(dest_net,
        "nexthop", "via", next_hop2, "weight 1", "nexthop", "via", next_hop3, "weight 1", "nexthop", "via", next_hop4, "weight 1")

    def setInterfaceIgnoreRoutesWithLinkdown(self, v):
        self._setter.sysctl('-w',f"net.ipv4.conf.{self._switchdevInterface}.ignore_routes_with_linkdown", v)

    def setDevECMPRoute(self, addr, suffix=24, *args, **kwargs):
        commandSuffix=""
        for via, weight in zip(*[iter(list(*args) + list(*kwargs))] * 2):
            commandSuffix += f'nexthop via {via} dev={self._switchdevInterface.name} weight{weight}'
        self._setter.ip_route_add(addr, suffix, commandSuffix)

