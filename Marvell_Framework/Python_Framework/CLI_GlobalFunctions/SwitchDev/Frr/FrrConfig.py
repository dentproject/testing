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

from CLI_GlobalFunctions.SwitchDev.CLICommands.Executer import Getter


FRR_CONFIG_FILE = r'/etc/frr/frr.conf'
FRR_DEFAULT_CONFIG = "# default to using syslog. /etc/rsyslog.d/45-frr.conf places the log\n " \
                     "# in /var/log/frr/frr.log\nlog syslog informational"


class WRITE_MODE(Enum):
    APPEND = 'a+'
    OVERWRITE = 'w+'

class STATE(Enum):
    ENABLE = "yes"
    DISABLE = "no"

class ACTION(Enum):
    ENABLE = "start"
    DISABLE = "stop"
    RESTART = "restart"


frrConfig="""
frr version 7.3
frr defaults traditional
hostname buildroot
log syslog informational
no ipv6 forwarding
no zebra nexthop kernel enable
service integrated-vtysh-config
{config}
!
line vty
!"""

class FrrConfig:

    def __init__(self, channel):
        self._executer = Getter(channel)

    def enableProtocol(self, protocol, v:ACTION):
        return self._executer.execute(f"sed -i '/^{protocol}/ c{protocol}={v.value}' /etc/frr/daemons")

    def enableDisableFrr(self, state:STATE):
        return self._executer.execute(f"/usr/sbin/frrinit.sh {state.value}")

    def createFrrConfig(self, configuration, mode: WRITE_MODE = WRITE_MODE.OVERWRITE):
        global frrConfig
        with self._executer.channel.SSHClient.open_sftp().open(FRR_CONFIG_FILE, mode.value) as etcNetworkInterfaces:
            etcNetworkInterfaces.write(frrConfig.format(config=f"!\n{configuration}"))

    def sendVtyshCommand(self, command):
        return self._executer.execute(f'vtysh -c "{command}"')
