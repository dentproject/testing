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

from CLI_GlobalFunctions.SwitchDev.CLICommands.EntityConfig import GeneralEntityConfig
from CLI_GlobalFunctions.SwitchDev.CLICommands.Executer import GlobalGetterSetter



class LLDP_config(GeneralEntityConfig):

    def __init__(self, switchDevInterface, otherDutChannel=False, executer=True):
        """
        :param switchDevInterface: the entity to be configured (e.g, bond, port, bridge)
        :param otherDutChannel: True if there is another DUT; False otherwise
        """
        super(LLDP_config, self).__init__(switchDevInterface, otherDutChannel, executer)

    @classmethod
    def LLDPserviceStart(cls):
        """
        start lldp service
        """
        return GlobalGetterSetter().setter.lldpd("-cefs")

    @classmethod
    def LLDPServiceKill(cls):
        """
        start lldp service
        """
        return GlobalGetterSetter().setter.killall("lldpd")

    @classmethod
    def getPortMac(cls, port):
        return GlobalGetterSetter().getter.cat(f'/sys/class/net/{port}/address')

    @classmethod
    def getHostIP(cls):
        return GlobalGetterSetter().getter.execute(fr"ip -o route get to 8.8.8.8 | sed -n 's/.*src \([0-9.]\+\).*/\1/p'")

    @classmethod
    def setPortlink(cls, port, v):
        return GlobalGetterSetter().setter.ip_link_set('dev', port, v)

    @classmethod
    def setInterfaceStat(cls, port, status):
        return GlobalGetterSetter().setter.lldpcli_configure_ports(port, 'lldp', 'status', status)

    @classmethod
    def setTlvFields(cls, oui, subtype, ouiinfo):
        return GlobalGetterSetter().setter.lldpcli_configure_lldp('custom-tlv', 'oui', oui, 'subtype', subtype, 'oui-info', ouiinfo, timeout=15)

    @classmethod
    def getPortStats(cls, port):
        return GlobalGetterSetter().getter.lldpcli_show_statistics_ports(port)

    @classmethod
    def getTrasmittedTLV(cls, port):
        return GlobalGetterSetter().getter.lldpcli_show_interfaces_ports(port)


    @classmethod
    def getTLVNeighborInfo(cls, port):
        return GlobalGetterSetter().getter.lldpcli_show_neighbors_ports(port)

    @classmethod
    def setLLDPTxInterval(cls, interval):
        return GlobalGetterSetter().setter.lldpcli('configure', 'lldp', 'tx-interval', interval)

    @classmethod
    def setLLDPTxHold(cls, hold):
        return GlobalGetterSetter().setter.lldpcli('configure', 'lldp', 'tx-hold', hold)

    @classmethod
    def setBondSlaveVal(cls, value):
        return GlobalGetterSetter().getter.lldpcli_configure_system('bond-slave-src-mac-type', value)