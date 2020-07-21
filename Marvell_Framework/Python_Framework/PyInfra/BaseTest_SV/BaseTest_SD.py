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
from time import sleep
import re
import inspect
import json
import os
from CLI_GlobalFunctions.SwitchDev.CLICommands.Executer import GlobalGetterSetter
from CLI_GlobalFunctions.SwitchDev.Stress.CPUStress import CPUStress
from PyInfra.BaseTest_SV import BaseTest_SV
from PyInfra.DutManagers.SvDut.SwitchDevDutManager import SwitchDevDutManager
from PyInfraCommon.GlobalFunctions.Utils.Function import GetFunctionName
from PyInfraCommon.Globals.Logger.GlobalTestLogger import GlobalLogger
from PyInfra.BaseTest_SV.SV_Structures.DutInfo import DutInfoSD
from PyInfraCommon.ExternalImports.Communication import PySerialComWrapper

""""
Base Test SwitchDev
"""""


class BaseTest_SD(BaseTest_SV):

    def __init__(self, SuiteName, resource=None, useTG=True):
        self.stress_mode = 0
        super(BaseTest_SD, self).__init__(SuiteName, useTG)
        self.TestData.DutInfo = DutInfoSD()
        self.TestCaseData = None
        self.resource = resource
        self.TGManager.settings.port_cleanup_settings.reset_factory_default = True
        self.TGManager.settings.used_cached_connection = False  # prevent keeping tg instance alive between tests in GRAS
        if int(self.stress_mode) != 0:
            self.TestSteps.Step[-1] = "stress cpu test params with mode {} (1: both, 2: Host, 3: FW)".format(
                self.stress_mode)
        self.isLoad = False

    def _BasicTestInit(self):
        super(BaseTest_SD, self)._BasicTestInit()
        self._GetDutChannels(path_to_setup=self.SetupXlsPath)
        self.DutMainChannel = self.TestData.Resources.Channels['dutmainchannel']
        self.DutManager = SwitchDevDutManager(self.DutMainChannel, testclass=self)
        self._UpdateDutManagerInfo(self.DutManager, self._SvSetup, pduNum=1 if self.MultiplePDU_dict else None)

        if 'dutsecondaychannel' in self.TestData.Resources.Channels:
            self.DutSecondayChannel = self.TestData.Resources.Channels['dutsecondaychannel']
            self.DutSecondayManager = SwitchDevDutManager(self.DutSecondayChannel, testclass=self)
            self._UpdateDutManagerInfo(self.DutSecondayManager, self._SvSetup, pduNum=2 if self.MultiplePDU_dict else None)

        if 'otherchannel' in self.TestData.Resources.Channels:
            self.OtherDutChannel = self.TestData.Resources.Channels['otherchannel']
            self.OtherDutManager = SwitchDevDutManager(self.OtherDutChannel, testclass=self)
            self._UpdateDutManagerInfo(self.OtherDutManager, self._SvSetup, pduNum=3 if self.MultiplePDU_dict else None)

    def SpecificTestInit(self):
        super(BaseTest_SD, self).SpecificTestInit()
        if not self.isLoad:
            self._AddCleanupRecoveryCrashHandler(self.DutManager.reboot, software_reset=False)

            if self.OtherDutManager:
                self._AddCleanupRecoveryCrashHandler(self.OtherDutManager.reboot, software_reset=False)

            self.DutManager.login()
            if self.DutManager.host_kernel_version():
                self.TestData.DutInfo.Host_kernel_version = self.DutManager.host_kernel_version()

            if self.DutManager.uboot_version():
                self.TestData.DutInfo.UBOOT_Version = self.DutManager.uboot_version()

            if self.DutManager.software_version():
                self.TestData.DutInfo.Software_Version = self.DutManager.software_version()

        if 'dutsecondaychannel' in self.TestData.Resources.Channels:
            self.DutSecondayManager.login(isload=self.isLoad)
            GlobalGetterSetter().secondaryDutChannel = self.DutSecondayChannel
            self.DutManager.uboot_manager._uboot_channel_host = self.DutSecondayChannel

        if 'otherchannel' in self.TestData.Resources.Channels:
            self.OtherDutManager.login(isload=self.isLoad)
            GlobalGetterSetter().otherDutChannel = self.OtherDutChannel
            self.DutManager.uboot_manager._uboot_channel_fw = self.OtherDutChannel

        if self.resource:
            import os
            dir_path = os.path.dirname(os.path.realpath(__file__))
            root_folder = os.path.abspath(os.path.join(os.path.join(dir_path, os.pardir), os.pardir))
            json_dir = os.path.join(root_folder, "Tests", "Implementations", *self.resource.split("/")[:-1])
            json_path = os.path.join(json_dir, "{}.json".format(self.resource.split("/")[-1]))
            jsonVersion = json_path if os.path.isfile(json_path) else json_path + '5'
            if os.path.isfile(jsonVersion):
                with open(jsonVersion) as json_file:
                    self.TestCaseData = json5.load(json_file)

        GlobalGetterSetter().channel = self.DutMainChannel
        self._clear_dmesg()
        self._clear_cmd_history()
        self.handle_stress_mode()

    def _InitArgParser(self,init_arg_object=True):
        """
        parse optional command line arguments passed to script
        :return:
        :rtype:
        """
        super(BaseTest_SD,self)._InitArgParser(init_arg_object=False)
        self._args_parser.add_argument("-stress", "--stress",action="store",
        help="Set the level of CPU stress", required=False)
        # parse command line args
        self._args_object = self._args_parser.parse_args()
        #handle input args

    def _HandleCommandLineArgs(self,print_args=True):
        """
        handles passed command line args if passed
        :return:
        :rtype:
        """
        funcname = GetFunctionName(self._HandleCommandLineArgs)
        super(BaseTest_SD,self)._HandleCommandLineArgs(False)
        if hasattr(self._args_object,"stress") and self._args_object.stress:
            self.stress_mode = self._args_object.stress
            launched_with_args = True
        if self._args_object and self._launched_with_args and print_args:
            msg = funcname + "this test has been launched with the following input arguments:\n{}".format(self._args_object)
            print(msg)

    def _stressHost(self):
        """
        Stress the host CPU
        """
        funcname = GetFunctionName(self._stressHost)
        GlobalLogger.logger.debug(funcname)
        ee = None
        for attempt in range(3):
            try:
                self.CPUStress.setCpuUtilization(stress_timeout=0)
                sleep(1)
                during_util = self.CPUStress.getCpuUtilization()
                if float(during_util) < 75.0:
                    raise Exception("Stress Host failed")
            except Exception as e:
                ee = e
            else:
                break
        else:
            raise ee

    def _unstressHost(self):
        """
        Unstress the host CPU
        """
        funcname = GetFunctionName(self._unstressHost)
        GlobalLogger.logger.debug(funcname)
        ee = None
        for attempt in range(3):
            try:
                self.CPUStress.unsetCpuUtilization()
                sleep(1)
                after_util = self.CPUStress.getCpuUtilization()
                if float(after_util) > 50.0:
                    raise Exception("Unstress Host failed")
            except Exception as e:
                ee = e
            else:
                break
        else:
            raise ee

    def _stressFw(self):
        """
        Stress the FW CPU
        """
        funcname = GetFunctionName(self._stressFw)
        GlobalLogger.logger.debug(funcname)
        ee = None
        for attempt in range(3):
            try:
                self.CPUStress.setFwCpuUtilization()
                sleep(1)
                fw_during_util = self.CPUStress.getFwCpuUtilization()
                if float(fw_during_util) < 65.0:
                    raise Exception("Stress FW failed")
            except Exception as e:
                if "NoneType" in str(e):
                    raise Exception("stressFw might be called without specifying DutSecondayChannel in the setup file")
                ee = e
            else:
                break
        else:
            raise ee

    def _unstressFw(self):
        """
        Unstress the FW CPU
        """
        funcname = GetFunctionName(self._unstressFw)
        GlobalLogger.logger.debug(funcname)
        ee = None
        for attempt in range(3):
            try:
                self.CPUStress.unsetFwCpuUtilization()
                sleep(1)
                fw_after_util = self.CPUStress.getFwCpuUtilization()
                if float(fw_after_util) > 45.0:
                    raise Exception("Unstress FW failed")
            except Exception as e:
                ee = e
            else:
                break
        else:
            raise ee

    def stressCpus(self, stressType=0):
        """
        Select the CPU stress mode and apply it
        """
        funcname = GetFunctionName(self.stressCpus)
        GlobalLogger.logger.debug(funcname)
        self.CPUStress = CPUStress(self.DutSecondayChannel)
        if stressType == 0 or self.TestData.TestInfo.Test_Name == "2_2_HardwareReload":
            return
        elif stressType == 1:
            self._stressFw()
            self._stressHost()
            self.Add_Cleanup_Function_To_Stack(self._unstressHost)
            self.Add_Cleanup_Function_To_Stack(self._unstressFw)
        elif stressType == 2:
            self._stressHost()
            self.Add_Cleanup_Function_To_Stack(self._unstressHost)
        elif stressType == 3:
            self._stressFw()
            self.Add_Cleanup_Function_To_Stack(self._unstressFw)

    def TestPreRunConfig(self):
        """
        This method is called by the RunTheTests() method
        it is meant to _execute some initial pre-test configurations before actually running the tests
        if it is not necessary by derived class, then it can be just not implemented
        :return:
        """
        self.stressCpus(stressType=int(self.stress_mode))

    def handle_stress_mode(self):
        if int(self.stress_mode) != 0:
            self.TestSteps.RunStep(-1)

    def _clear_cmd_history(self):
        funcname = GetFunctionName(self._clear_cmd_history)
        GlobalLogger.logger.debug(funcname)
        try:
            if "Load_ver" not in self.TestData.TestInfo.Suite_Name:
                buff = GlobalGetterSetter()._getter._("history -c")
                self.Add_Cleanup_Function_To_Stack(self._log_cmd_history)
        except Exception as e:
            print(e)

    def _log_cmd_history(self):
        funcname = GetFunctionName(self._parse_dmesg)
        GlobalLogger.logger.debug(funcname)
        try:
            buff = GlobalGetterSetter()._getter._("history")
            GlobalLogger.logger.debug("commands history:\n{}".format(buff))
            return True
        except Exception as e:
            print(e)
            return False

    def _clear_dmesg(self):
        funcname = GetFunctionName(self._clear_dmesg)
        GlobalLogger.logger.debug(funcname)
        try:
            if "Load_ver" not in self.TestData.TestInfo.Suite_Name:
                buff = GlobalGetterSetter()._getter._("echo \"\" > /var/log/messages")
                self.Add_Cleanup_Function_To_Stack(self._parse_dmesg)
        except Exception as e:
            print(e)

    def _parse_dmesg(self):
        funcname = GetFunctionName(self._parse_dmesg)
        GlobalLogger.logger.debug(funcname)
        try:
            match_kw = {}
            caller_full_folder_path = inspect.stack()[1][1]
            path = "{}{}Tests{}{}".format(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(caller_full_folder_path)))),os.sep, os.sep, "dmesg_kw.json")
            with open(path) as json_file:
                match_kw = json.load(json_file)
            # for item in match_kw:
            #     match_kw[item]["regex"] = str(match_kw[item]["regex"]).replace("\\\\", "\\")

            log_lines = ""
            buff = GlobalGetterSetter()._getter._("cat /var/log/messages")
            if buff:
                log_lines = buff.split("\n")
            self._process_log_line(log_lines, match_kw)
            self._report_log_lines(match_kw)
            return True
        except Exception as e:
            print(e)
            GlobalLogger.logger.debug("Error - _parse_dmesg had exception:\n{}".format(str(e)))
            # self.FailTheTest("Error - _parse_dmesg had exception:\n{}".format(str(e)), abort_test=False)
            # return False

    def _process_log_line(self, lines, kw_dict):
        try:
            for (key, value) in kw_dict.items():
                kw_dict[key]["found"] = False
                for idx, line in enumerate(lines):
                    pattern = re.compile(kw_dict[key]["regex"])
                    is_found = re.search(pattern, line)
                    if is_found:
                        kw_dict[key]["found"] = True
                        if "lines" not in kw_dict[key]:
                            kw_dict[key]["lines"] = []
                        kw_dict[key]["lines"].append((idx, line))

        except Exception as e:
            print(e)
        finally:
            return kw_dict

    def _report_log_lines(self, kw_dict):
        GlobalLogger.logger.debug("dmesg lines that matched regex for issues:")
        GlobalLogger.logger.debug(json5.dumps(kw_dict, sort_keys=True, indent=4))
        for (key, value) in kw_dict.items():
            if "found" in kw_dict[key]:
                if kw_dict[key]["found"] == True:
                    for line in kw_dict[key]["lines"]:
                        self.FailTheTest("Error - dmesg buffer contain regex match found in line #{}: {}".format(line[0], line[1]), abort_test=False)
