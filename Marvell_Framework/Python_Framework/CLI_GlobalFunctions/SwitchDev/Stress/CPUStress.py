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

import re
from time import sleep
from builtins import str
from PyInfraCommon.Globals.Logger.GlobalTestLogger import GlobalLogger
from CLI_GlobalFunctions.SwitchDev.CLICommands.EntityConfig import GeneralEntityConfig
from CLI_GlobalFunctions.SwitchDev.CLICommands.Executer import GlobalGetterSetter
from PyInfraCommon.GlobalFunctions.Utils.Function import GetFunctionName


class CPUStress(GeneralEntityConfig):

    def __init__(self, otherDutChannel, executer=True):
        super(CPUStress, self).__init__(None, otherDutChannel, executer)

    def send_cmd(self, cmd="", timeout=10, exception_msg=None):
        try:
            res = self._testClassref.DutMainChannel.SendCommandAndWaitForPattern(cmd,
                                                                            timeOutSeconds=timeout)
            if res:
                return self._testClassref.DutMainChannel.lastBufferTillPrompt
            else:
                msg = "Can't setCpuUtilization:\n{}".format(res)
                if exception_msg:
                    msg = exception_msg
                raise Exception("{}\n{}".format(msg, res))
        except Exception as e:
            raise Exception("Can't setCpuUtilization:\n{}".format(e))

    def _get_from_regex(self, buff, ListOfRegx = [], GroupNum = None):

        RetVal = "Param not found !"
        if type(GroupNum) != list:
            GroupNum = [GroupNum]

        if type(ListOfRegx) != list:
            ListOfRegx = [ListOfRegx]

        tmp = buff

        for idx, elem in enumerate(ListOfRegx):
            # TmpElem = elem.decode('string_escape')
            TmpElem = str(elem)
            tmp = str(tmp)
            mo = re.search(str(TmpElem), tmp, flags=re.MULTILINE)
            match_list = re.findall(str(TmpElem), tmp, flags=re.MULTILINE)
            if mo:
                # if idx == (len(ListOfRegx) - 1):
                if GroupNum[idx] == None or GroupNum[idx] == "":
                    tmp = mo.group(0)  # full match

                elif GroupNum[idx] == 'all':
                    tmp = match_list  # update tmp for next iteration
                else:
                    tmp = mo.group(GroupNum[idx]) #
            else:
                tmp = ""

        RetVal = tmp

        return RetVal

    def getCpuUtilization(self):
        funcname = GetFunctionName(self.getCpuUtilization)
        GlobalLogger.logger.debug(funcname)
        cpu_util = None
        ret = GlobalGetterSetter()._getter.top(" -n 1")
        if ret:
            cpu_util = float(self._get_from_regex(ret, "CPU:\s+(\d+)", 1))
        return cpu_util

    def getFwCpuUtilization(self):
        funcname = GetFunctionName(self.getFwCpuUtilization)
        GlobalLogger.logger.debug(funcname)
        cpu_util = None
        ret = GlobalGetterSetter()._getterSecondaryDut.top(" -n 1")
        if ret:
            cpu_util = float(self._get_from_regex(ret, "CPU:\s+(\d+)", 1))
        return cpu_util

    def setCpuUtilization(self, cpu_count=0, stress_timeout=10):
        try:
            funcname = GetFunctionName(self.getCpuUtilization)
            GlobalLogger.logger.debug(funcname)
            buff = GlobalGetterSetter()._getter._("stress-ng --cpu {} --timeout {} &".format(cpu_count, stress_timeout))
            if not buff:
                raise Exception("{} Could not set CPU utilization on {} cpu count and timeout of {}".format(funcname, cpu_count, stress_timeout))
        except Exception as e:
            raise Exception("Can't setCpuUtilization:\n{}".format(e))

    def setFwCpuUtilization(self, cpu_count=0):
        try:
            funcname = GetFunctionName(self.setFwCpuUtilization)
            GlobalLogger.logger.debug(funcname)
            if cpu_count == 0:
                cpu_count = 2
            for i in range(cpu_count):
                buff = GlobalGetterSetter()._getterSecondaryDut._("sha1sum /dev/zero &")
                if not buff:
                    if not GlobalGetterSetter().secondaryDutChannel._lastBufferTillPrompt:
                        raise Exception("{} Could not set CPU utilization".format(funcname))
        except Exception as e:
            raise Exception("Can't setFwCpuUtilization:\n{}".format(e))

    def unsetCpuUtilization(self):
        try:
            funcname = GetFunctionName(self.unsetCpuUtilization)
            GlobalLogger.logger.debug(funcname)
            buff = GlobalGetterSetter()._getter.killall("stress-ng")
            if not buff:
                raise Exception("{} Could not kill stress-ng".format(funcname))
        except Exception as e:
            raise Exception("Can't unsetCpuUtilization:\n{}".format(e))

    def unsetFwCpuUtilization(self):
        try:
            funcname = GetFunctionName(self.unsetFwCpuUtilization)
            GlobalLogger.logger.debug(funcname)
            buff = GlobalGetterSetter()._getterSecondaryDut.killall("killall sha1sum")
            if not buff:
                raise Exception("{} Could not kill sha1sum".format(funcname))
        except Exception as e:
            raise Exception("Can't unsetFwCpuUtilization:\n{}".format(e))
