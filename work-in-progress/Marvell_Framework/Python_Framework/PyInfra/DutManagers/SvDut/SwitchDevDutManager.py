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

from builtins import str
import re
from time import sleep

from PyInfra.DutManagers.SvDut.Types import DutChannelType
from PyInfraCommon.ExternalImports.Communication import PySSHComWrapper
from PyInfra.BaseTest_SV.SV_Enums.AppTypes import AppType
from PyInfra.DutManagers.SvDut.BaseSvDutManager import BaseSvDutManager
from PyInfraCommon.GlobalFunctions.IP import ping_till_timeout, poll_socket_till_timeout
from PyInfraCommon.GlobalFunctions.Utils.Exception import GetStackTraceOnException
from PyInfraCommon.GlobalFunctions.Utils.Function import GetFunctionName
from PyInfraCommon.Globals.Logger.GlobalTestLogger import GlobalLogger
from PyInfra.DutManagers.UBOOT import UBOOTManager

class SwitchDevDutManager(BaseSvDutManager):
    """
    specific infra related to SwitchDev Dut management should be added here
    """

    def __init__(self, dut_channel: PySSHComWrapper, testclass):
        BaseSvDutManager.__init__(self, dut_channel, testclass)
        self.appType = AppType.SwitchDev
        self._linux_version = None
        self.Host_kernel_version = None
        self.Host_version = None
        self.UBOOT_Version = None
        self.uboot_manager = UBOOTManager(self)

    def init_dut(self):
        pass

    def login(self, isload=False):
        suite_name = self._testclassref.TestData.TestInfo.Suite_Name
        if self._dut_active_channel_type is DutChannelType.SSH:
            self._dut_active_channel.shellWidth = 500
        isLogged = self._dut_active_channel.Connect()
        if self._dut_active_channel_type is DutChannelType.TELNET and not isload:
            self.telnet_login()
        if self._dut_active_channel_type is not DutChannelType.SERIAL and not isload:
            self._set_prompt()
        return isLogged

    def software_version(self):
        if not self.Host_version:
            return self._get_host_version()
        return self.Host_version

    def host_kernel_version(self):
        if not self.Host_kernel_version:
            return self._get_host_version()
        return self.Host_kernel_version

    def uboot_version(self):
        if not self.UBOOT_Version:
            self.UBOOT_Version = ""
            # return self._get_uboot_version()
        return self.UBOOT_Version

    def _set_prompt(self):
        self._dut_active_channel.SendCommandAndWaitForPattern("\n", ExpectedPrompt='#', timeOutSeconds=20)
        self._dut_active_channel.GetBuffer()
        self._dut_active_channel.SendCommandAndWaitForPattern("\n", ExpectedPrompt='#', timeOutSeconds=20)
        self._dut_active_channel.shellPrompt = str(self._dut_active_channel.lastBufferTillPrompt).split('\r\n')[
                                                   1] + r'\Z'

    def _get_host_version(self):
        """
        reads version from the command 'modinfo prestera_sw' on Dut and saves these params to self class
        :return: host_version str
        :rtype: str
        """
        funcname = GetFunctionName(self._get_host_version)
        cmd = "modinfo prestera_sw"
        board_type = ""
        self._dut_active_channel.GetBuffer()
        if not self._dut_active_channel.SendCommandAndWaitForPattern(
                cmd, ExpectedPrompt=self._dut_active_channel.shellPrompt):
            err = funcname + " failed to detect expected prompt after sending {} command, terminal buffer:\n{}".format(
                cmd, self._dut_active_channel.lastBufferTillPrompt)
            GlobalLogger.logger.error(err)
            return
        else:
            response = self._dut_active_channel.lastBufferTillPrompt
            from PyInfraCommon.GlobalFunctions.CLI import clean_dut_cli_buffer
            clean_dut_cli_buffer(response, [cmd, self._dut_active_channel.shellPrompt])
            try:
                self.Host_version = str(self._dut_active_channel.lastBufferTillPrompt).split("version:")[1].strip().split("\r\n")[0]
                self.Host_kernel_version = str(self._dut_active_channel.lastBufferTillPrompt).split("vermagic:")[1].split()[0]
            except Exception as e:
                print(e)
            try:
                cmd = "i2cget -y 2 0x41 0x01"
                evt_dvt_cmd = "i2cget -y 2 0x41 0x00"

                self._dut_active_channel.SendCommandAndWaitForPattern(cmd, ExpectedPrompt=self._dut_active_channel.shellPrompt)
                response3 = self._dut_active_channel.lastBufferTillPrompt
                response3 = clean_dut_cli_buffer(response3, [cmd, self._dut_active_channel.shellPrompt])

                self._dut_active_channel.SendCommandAndWaitForPattern(evt_dvt_cmd, ExpectedPrompt=self._dut_active_channel.shellPrompt)
                evt_dvt_response = self._dut_active_channel.lastBufferTillPrompt
                evt_dvt_response = clean_dut_cli_buffer(evt_dvt_response, [evt_dvt_cmd, self._dut_active_channel.shellPrompt])

                if "0x0a" in response3:
                    if "0x02" in evt_dvt_response:
                        board_type = "TN48M-DVT"
                    else:
                        board_type = "TN48M-EVT"
                elif "0x0b" in response3:
                    if "0x02" in evt_dvt_response:
                        board_type = "TN48M-P-DVT"
                    else:
                        board_type = "TN48M-P-EVT"
                elif "0x0c" in response3:
                    board_type = "TN4810M"
                elif "0x0d" in response3:
                    board_type = "TN48M2"
                else:
                    board_type = ""
                try:
                    self._testclassref.TestData.DutInfo.Board_Model = board_type
                except: pass

            except Exception as e:
                print(e)
            GlobalLogger.logger.info("switch_dev version:{}/kernel {}/board type {}".format(self.Host_version, self.Host_kernel_version, board_type))
            return self.Host_version

    def _get_uboot_version(self):
        """
        reads the uboot version from the command 'strings /dev/mtd0 | grep U-Boot' on Dut and saves these params to self class
        :return: UBOOT_Version str
        :rtype: str
        """
        funcname = GetFunctionName(self._get_uboot_version)
        cmd = "strings /dev/mtd0 | grep U-Boot"
        self._dut_active_channel.GetBuffer()
        if not self._dut_active_channel.SendCommandAndWaitForPattern(
                cmd, ExpectedPrompt=self._dut_active_channel.shellPrompt, timeOutSeconds=30):
            err = funcname + " failed to detect expected prompt after sending {} command, terminal buffer:\n{}".format(
                cmd, self._dut_active_channel.lastBufferTillPrompt)
            GlobalLogger.logger.error(err)
            return
        else:
            response = self._dut_active_channel.lastBufferTillPrompt
            from PyInfraCommon.GlobalFunctions.CLI import clean_dut_cli_buffer
            response = clean_dut_cli_buffer(response, [cmd, self._dut_active_channel.shellPrompt])

            try:
                self.UBOOT_Version = re.findall(r"ver=(U-Boot\s+.*\d)\s\(", response)[0]
            except Exception as e:
                print(e)
            return self.UBOOT_Version

    def _software_reboot(self, poll_dut_loaded=True, print_exceptions=False, timeout_seconds=20):
        """
        reboots the Dut by software
        :param poll_dut_loaded: polls the Dut has loaded back by either waiting for linux prompt with optionally ping test
        :type poll_dut_loaded:bool
        :param print_exceptions: if True will print exception that ocur
        :type print_exceptions:bool
        :return:True if dut loaded back and polling enabled (or True in polling is disabled)
        :rtype: bool
        """
        funcname = GetFunctionName(self._software_reboot)
        try:
            self._dut_active_channel.SendCommandAndWaitForPattern("reboot", ExpectedPrompt='\n')
            self._dut_active_channel.Disconnect()
            if poll_dut_loaded:
                if self._dut_active_channel_type in (DutChannelType.TELNET, DutChannelType.SSH):
                    if not ping_till_timeout(self._dut_active_channel._host, timeout=timeout_seconds, initial_delay=10):
                        return False
                    port = 22 if self._dut_active_channel_type is DutChannelType.SSH else 23
                    return poll_socket_till_timeout(self._dut_active_channel._host, port, timeout=timeout_seconds)
                else:
                    # wait for linux prompt using serial
                    return self._dut_active_channel.GetBufferTillPattern(
                        ExpectedPrompt=self._dut_active_channel.shellPrompt, timeOutSeconds=timeout_seconds)
            else:
                return True
        except Exception as ex:
            err = funcname + "caught exception:{}".format(GetStackTraceOnException(ex))
            if print_exceptions:
                self.logger.error(err)
            return False

    def reboot(self, poll_dut_loaded=True, max_attempts=3, timeout_seconds=120, software_reset=False, isLoad=False):
        funcname = GetFunctionName(self.reboot)
        if isLoad:
            return super(SwitchDevDutManager, self).reboot(poll_dut_loaded, max_attempts, timeout_seconds, software_reset)
        crashBeforeLogin = self.Host_kernel_version is None and self.Host_version is None and self.UBOOT_Version is None
        if crashBeforeLogin:
            software_reset = False
        res = super(SwitchDevDutManager, self).reboot(poll_dut_loaded, max_attempts, timeout_seconds, software_reset)
        if crashBeforeLogin and res:
            # If we crashed before login the following timeout is required in order to finish CPSS init
            # In the regular scenario this is handled by test
            self.logger.info(f'{funcname}Waiting 30s after power cycle to give CPSS time for init')
            sleep(30)
        return res
