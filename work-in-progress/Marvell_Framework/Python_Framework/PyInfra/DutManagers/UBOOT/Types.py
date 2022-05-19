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

from enum import IntEnum,Enum

from PyInfraCommon.GlobalFunctions.Utils.Function import GetFunctionName
from PyInfraCommon.Globals.Logger.GlobalTestLogger import GlobalLogger
from PyInfraCommon.Managers.CLI import CliContextNode, CliBasePrompts


class UBOOTPrompts(CliBasePrompts):
    """
    all U-BOOT prompts and their regex patterns
    """
    def __init__(self):
        super(self.__class__, self).__init__()
        self.uboot_prompt = r"(Marvell>>?[\W\s]*)\Z"
        self.uboot_autoboot_fw_prompt = r"(Hit\s+any\s+key\s+to\s+stop\s+autoboot:\s*\d)\s*"
        # Type 123<ENTER> to STOP autoboot
        self.uboot_autoboot_host_prompt = r"(Type\s+123<ENTER>\s+to\s+STOP\s+autoboot\s*)"
        self.loaded_prompt = r"(buildroot\s+login:\s*)"
        self.dev_prompt = r"(amzgo-host#\s*)"

    def set_context_tree(self):
        """
        create the context_tree of all cli contexts
        :return: context tree
        :rtype: CliContextNode
        """
        uboot_prompt = CliContextNode("uboot_prompt", self.uboot_prompt)
        uboot_autoboot_fw_prompt = CliContextNode("uboot_autoboot fw_prompt", self.uboot_autoboot_fw_prompt)
        uboot_autoboot_host_prompt = CliContextNode("uboot_autoboot_host prompt", self.uboot_autoboot_host_prompt)
        self._contextTree = uboot_prompt
        return self._contextTree


class UBOOTIPAssigmentMethod(IntEnum):
    Static = 0
    Dynamic = 1
    Unset = 2


class UBOOTBootSource(IntEnum):
    """
    boot source of UBOOT
    """
    Unset = -1
    NFS = 0
    FLASH = 1
    USB = 2

class ByteOrder(Enum):

    unset = -1
    litte_endian = 0
    big_endian = 1


class UBOOT_CPU_ARCH(Enum):
    Unknown = -1
    ARM32 = 0
    ARM64 = 1


class UBOOTEnvironment(object):
    def __init__(self):
        self.ethprime = ""
        self.ethact = ""
        self.netdev = ""
        self.serverip = ""
        self.fdt_addr_r = ""
        self.fdt_skip_update = ""
        self.rootpath = ""
        self.image_name = ""
        self.fdt_file = ""
        self.root = ""
        self.set_bootargs = ""
        self.bootcmd = ""