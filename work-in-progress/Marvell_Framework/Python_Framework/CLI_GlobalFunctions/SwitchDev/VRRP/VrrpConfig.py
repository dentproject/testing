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

from enum import Enum

from CLI_GlobalFunctions.SwitchDev.CLICommands.EntityConfig import L2EntityConfig
from PyInfra.BaseTest_SV.SV_Enums.SwitchDevInterface import SwitchDevDutInterface

KEEPALIVED_CONFIG = r'/etc/keepalived/keepalived.conf'


class WRITE_MODE(Enum):
    APPEND = 'a+'
    OVERWRITE = 'w+'


class VrrpConfig(L2EntityConfig):

    def __init__(self, switchDevInterface, otherDutChannel=False):
        """
        :param switchDevInterface: the entity to be configured (e.g, bond, port, bridge)
        :param otherDutChannel: True if there is another DUT; False otherwise
        """
        super(VrrpConfig, self).__init__(SwitchDevDutInterface(switchDevInterface), "macvlan", otherDutChannel)

    def killKeepalivedDaemon(self):
        return self._getter.execute("if [ ! -z \"$(pidof keepalived)\" ]; then killall keepalived; fi")

    def restartKeepalivedDaemon(self):
        return self._getter.execute("if [ ! -z \"$(pidof keepalived)\" ];"
                                    " then killall keepalived; sleep 2; fi; /usr/sbin/keepalived\n")

    def createKeepalivedConfig(self, configuration, mode: WRITE_MODE = WRITE_MODE.OVERWRITE):
        with self._getter.channel.SSHClient.open_sftp().open(KEEPALIVED_CONFIG, mode.value) as etcNetworkInterfaces:
            etcNetworkInterfaces.write(configuration)

    def cleanupKeepalivedConfig(self):
        return self._getter.execute("echo "" > /etc/keepalived/keepalived.conf")
