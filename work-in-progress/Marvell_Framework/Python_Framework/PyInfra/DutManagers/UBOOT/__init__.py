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

import os
import sys
import time
from PyInfraCommon.BaseTest.BaseTestExceptions import TestCrashedException
from PyInfraCommon.GlobalFunctions.CLI import clean_dut_cli_buffer
from PyInfra.DutManagers.UBOOT.Types import *
from PyInfraCommon.ExternalImports.Communication import PyBaseComWrapper
from PyInfraCommon.GlobalFunctions.Utils.Function import GetFunctionName


class UBOOTManager(object):
    """
	this class handles common U-BOOT actions
	:type _uboot_channel: PyBaseComWrapper
	:type _uboot_class_ref: CpssDutManager
	"""

    def __init__(self, class_ref):
        from PyInfra.DutManagers.SvDut.SwitchDevDutManager import SwitchDevDutManager
        from PyInfraCommon.ExternalImports.Communication import PyTelnetComWrapper
        self._uboot_class_ref : SwitchDevDutManager = class_ref
        self._uboot_channel_host : PyTelnetComWrapper = None
        self._uboot_channel_fw : PyTelnetComWrapper = None
        self.uboot_version = ""
        self._uboot_NFS_server = ""
        self.__uboot_default_NFS_user = "pt-gen-jenk"
        self.__uboot_default_NFS_pass = "1qaz2wsx!"
        self.__uboot_default_NFS_prompt = r"\$\s*\Z"
        self.uboot_boot_source = UBOOTBootSource.Unset
        self._uboot_environment = UBOOTEnvironment()
        self._uboot_prompt = UBOOTPrompts()
        self._uboot_cpu_arch = UBOOT_CPU_ARCH.Unknown

    def reboot_and_stop_dev_in_marvell_prompt(self, isLoad=False, isM0=False):
        funcname = GetFunctionName(self.reboot_and_stop_dev_in_marvell_prompt)
        self._uboot_class_ref.reboot(poll_dut_loaded=False, software_reset=False, isLoad=isLoad)
        self.uboot_fw_login()
        if not isM0:
            self.uboot_host_login()

    def uboot_host_login(self):
        funcname = GetFunctionName(self.uboot_host_login)
        self._uboot_channel_host.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_autoboot_host_prompt,
                                                              command=chr(49)+chr(50)+chr(51)+"\r", timeOutSeconds=60)

    def uboot_fw_login(self):
        funcname = GetFunctionName(self.uboot_fw_login)
        self._uboot_channel_fw.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_autoboot_fw_prompt, command="\r", timeOutSeconds=60)

    def host_load_ver_cmds(self):
        funcname = GetFunctionName(self.host_load_ver_cmds)
        self._uboot_channel_host.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_prompt,
                                                              command="usb start", timeOutSeconds=60)
        self._uboot_channel_host.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_prompt,
                                                              command="tftp 0x8000000 switchdev/shared/mrvl_val/tn48m-host/sdcard.img", timeOutSeconds=60)
        self._uboot_channel_host.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_prompt,
                                                              command="scsi scan", timeOutSeconds=600)
        self._uboot_channel_host.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_prompt,
                                                              command="scsi write 0x8000000 0 0x3C001", timeOutSeconds=60)
        self._uboot_channel_host.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_prompt,
                                                              command="setenv root 'root=/dev/sda2'", timeOutSeconds=60)
        self._uboot_channel_host.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_prompt,
                                                              command="setenv set_bootargs 'setenv bootargs $console $root ip=$ipaddr:$serverip:$gatewayip:$netmask:$hostname:$netdev:none nfsroot=$serverip:$rootpath,tcp,v3 $extra_params $cpuidle'", timeOutSeconds=60)
        self._uboot_channel_host.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_prompt,
                                                              command="setenv bootcmd 'scsi scan; fatload scsi 0:1 $fdt_addr_r /armada-7040-dni-amzgo.dtb; fatload scsi 0:1 $kernel_addr_r /Image; run set_bootargs; booti $kernel_addr_r - $fdt_addr_r'", timeOutSeconds=60)
        self._uboot_channel_host.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_prompt,
                                                              command="saveenv", timeOutSeconds=60)

    def m0_load_ver_cmds(self):
        funcname = GetFunctionName(self.m0_load_ver_cmds)
        self._uboot_channel_fw.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_prompt,
                                                              command="usb start", timeOutSeconds=60)
        self._uboot_channel_fw.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_prompt,
                                                              command="tftpboot 0x2000000 switchdev/shared/mrvl_val/m0-nl/nand-flash.img ", timeOutSeconds=60)
        self._uboot_channel_fw.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_prompt,
                                                              command="nand erase.part rootfs", timeOutSeconds=600)
        self._uboot_channel_fw.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_prompt,
                                                              command="nand write.trimffs 0x2000000 0x1000000 0x3600000 ", timeOutSeconds=60)
        self._uboot_channel_fw.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_prompt,
                                                              command="saveenv", timeOutSeconds=60)

    def m0_reseting_dev_and_verifying_new_ver(self):
        funcname = GetFunctionName(self.m0_reseting_dev_and_verifying_new_ver)
        self._uboot_channel_fw.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_prompt,
                                                              command="reset", timeOutSeconds=600)
        self._uboot_channel_fw.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.loaded_prompt,
                                                              command="root", timeOutSeconds=600)
        self._uboot_channel_fw.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.dev_prompt,
                                                              command="modinfo prestera_sw", timeOutSeconds=60)
        self._uboot_channel_fw.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.dev_prompt,
                                                              command="", timeOutSeconds=60)
        self._uboot_class_ref.login()
        if self._uboot_class_ref.host_kernel_version():
            self._uboot_class_ref._testclassref.TestData.DutInfo.Host_kernel_version = self._uboot_class_ref.host_kernel_version()

        if self._uboot_class_ref.uboot_version():
            self._uboot_class_ref._testclassref.TestData.DutInfo.UBOOT_Version = self._uboot_class_ref.uboot_version()

        if self._uboot_class_ref.software_version():
            self._uboot_class_ref._testclassref.TestData.DutInfo.Software_Version = self._uboot_class_ref.software_version()


    def fw_ac3x_load_ver_cmds(self):
        funcname = GetFunctionName(self.fw_ac3x_load_ver_cmds)
        self._uboot_channel_fw.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_prompt,
                                                              command="usb start", timeOutSeconds=60)
        self._uboot_channel_fw.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_prompt,
                                                              command="set ethact asx0", timeOutSeconds=60)
        self._uboot_channel_fw.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_prompt,
                                                              command="tftpboot 0x2000000 switchdev/shared/mrvl_val/tn48m-loader/zImage.armada-385-dni-amzgo", timeOutSeconds=60)
        self._uboot_channel_fw.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_prompt,
                                                              command="nand erase 0xa00000 $fw_loader_size", timeOutSeconds=300)
        self._uboot_channel_fw.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_prompt,
                                                              command="nand write 0x2000000 0xa00000 $filesize", timeOutSeconds=60)
        self._uboot_channel_fw.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_prompt,
                                                              command="saveenv", timeOutSeconds=60)

    def fw_aldrin2_load_ver_cmds(self):
        funcname = GetFunctionName(self.fw_aldrin2_load_ver_cmds)
        self._uboot_channel_fw.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_prompt,
                                                              command="usb start", timeOutSeconds=60)
        self._uboot_channel_fw.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_prompt,
                                                              command="set ethact asx0", timeOutSeconds=60)
        self._uboot_channel_fw.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_prompt,
                                                              command="set ethprime asx0", timeOutSeconds=60)
        self._uboot_channel_fw.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_prompt,
                                                              command="set fw_loader_size 0x1700000", timeOutSeconds=60)
        self._uboot_channel_fw.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_prompt,
                                                              command="tftpboot 0x2000000 switchdev/shared/mrvl_val/tn4810m-loader/zImage.armada-385-dni-amzgo", timeOutSeconds=60)
        self._uboot_channel_fw.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_prompt,
                                                              command="nand erase 0xa00000 $fw_loader_size", timeOutSeconds=300)
        self._uboot_channel_fw.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_prompt,
                                                              command="nand write 0x2000000 0xa00000 $filesize", timeOutSeconds=60)
        self._uboot_channel_fw.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_prompt,
                                                              command="saveenv", timeOutSeconds=60)

    def reseting_dev_and_verifying_new_ver(self):
        funcname = GetFunctionName(self.reseting_dev_and_verifying_new_ver)
        self._uboot_channel_host.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.uboot_prompt,
                                                              command="reset", timeOutSeconds=60)
        self._uboot_channel_host.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.loaded_prompt,
                                                              command="root", timeOutSeconds=600)
        self._uboot_channel_host.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.dev_prompt,
                                                              command="modinfo prestera_sw", timeOutSeconds=60)
        self._uboot_channel_host.WaitForPatternAndSendCommand(ExpectedPrompt=self._uboot_prompt.dev_prompt,
                                                              command="", timeOutSeconds=60)
        self._uboot_class_ref.login()
        if self._uboot_class_ref.host_kernel_version():
            self._uboot_class_ref._testclassref.TestData.DutInfo.Host_kernel_version = self._uboot_class_ref.host_kernel_version()

        if self._uboot_class_ref.uboot_version():
            self._uboot_class_ref._testclassref.TestData.DutInfo.UBOOT_Version = self._uboot_class_ref.uboot_version()

        if self._uboot_class_ref.software_version():
            self._uboot_class_ref._testclassref.TestData.DutInfo.Software_Version = self._uboot_class_ref.software_version()
















