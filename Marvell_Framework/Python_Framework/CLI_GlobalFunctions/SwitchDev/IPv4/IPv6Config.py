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
from CLI_GlobalFunctions.SwitchDev.IPv4.IPConfig import IPConfig


class IPv6Config(IPConfig):
    __ipv6Forwarding = 0

    def __init__(self, switchDevDutPort, channel=None, executer=True):
        super(IPv6Config, self).__init__(switchDevDutPort, channel, executer)

    @classmethod
    def getIpv6Forwarding(cls):
        return cls.__ipv6Forwarding

    @classmethod
    def setIpv6Forwarding(cls, v):
        ret = GlobalGetterSetter().setter.sysctl('-w', f'net.ipv6.conf.all.forwarding={v}')
        if not ret:
            cls.__ipv6Forwarding = v