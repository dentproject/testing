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

from CLI_GlobalFunctions.SwitchDev.CLICommands.EntityConfig import L2EntityConfig
from CLI_GlobalFunctions.SwitchDev.CLICommands.Executer import GlobalGetterSetter


class LagConfig(L2EntityConfig):

    _bondDetails = {}

    def __init__(self, switchDevInterface, otherDutChannel=False, executer=True):
        """
        :param switchDevInterface: the entity to be configured (e.g, bond, port, bridge)
        :param otherDutChannel: True if there is another DUT; False otherwise
        """
        super(LagConfig, self).__init__(switchDevInterface, "bond mode 802.3ad", otherDutChannel, executer)
        self._lagInfo = {}

    @classmethod
    def getLagInfo(cls, otherDut=False):
        import json5
        if otherDut:
            executer = GlobalGetterSetter().getterOtherDut
        else:
            executer = GlobalGetterSetter().getter
        bondDetails = json5.loads(executer.execute('ip -d -j link show'))
        for interfaceDits in filter(lambda x: x.get('linkinfo', {}).get('info_slave_kind') == 'bond' or
                                              x.get('linkinfo', {}).get('info_kind') == 'bond', bondDetails):
            infoDataKey = 'info_slave_data' if 'info_slave_data' in interfaceDits['linkinfo'] else 'info_data'
            cls._bondDetails[interfaceDits['ifname']] = interfaceDits['linkinfo'][infoDataKey]
        return cls._bondDetails

    @classmethod
    def isActive(cls, port):
        state = cls._bondDetails.get(str(port)).get('state')
        return state and state.lower() == 'active'
