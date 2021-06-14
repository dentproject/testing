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

from builtins import object
import json


class CpssLuaJsonApiExecuterService(object):
    channel = None

    def execute_cpss_api(self, connAlias, cmd_str):
        raw_ret = self.execute_cpss_json_command(connAlias, cmd_str, "execGenWrapperC")
        temp = raw_ret["ctrl_func_ret"]
        del temp["funcname"]
        return temp

    def execute_cpss_json_tags(self, connAlias, cmd_str):
        return self.execute_cpss_json_command(connAlias, cmd_str, "execJsonControlC")

    def execute_cpss_json_command(self, connAlias, cmd_str, command_to_send):
        try:
            from Marvell.CommunicationService.CommunicationWrapper.ComWrapperImpl.PyComWrapper import PyBaseComWrapper
            from Marvell.CommunicationService.CommunicationWrapper.ComWrapperImpl.CPSSLuaJsonApiExecuter import \
                CPSSLuaJsonApiExecuter
            from Marvell.pytoolsinfra.PythonLoggerInfra import LoggerManager
        except Exception as e:
            from Marvell.CommunicationService.Common.ImportExternal import import_external
            import_external('CommunicationService')
            import_external('pytoolsinfra')
            from Marvell.CommunicationService.CommunicationWrapper.ComWrapperImpl.PyComWrapper import PyBaseComWrapper
            from Marvell.CommunicationService.CommunicationWrapper.ComWrapperImpl.CPSSLuaJsonApiExecuter import \
                CPSSLuaJsonApiExecuter
            from Marvell.pytoolsinfra.PythonLoggerInfra import LoggerManager

        # CpssJsonApiLogger = LoggerManager.GetLogger("CpssJsonApiLogger", ".\\Results\\", "CpssJsonApiLog",
        #                                             # logger_type=LoggerManager.LogType.TEST_LOGGER)
        #                                             logger_type=LoggerManager.LogType.HTML_LOGGER)

        self.channel = PyBaseComWrapper(connAlias, logObj=None)

        api_inst = CPSSLuaJsonApiExecuter(cmd_str, command_to_send)
        self.channel.execute(api_inst)

        # temp = json.loads(api_inst._get_raw_dut_response())["ctrl_func_ret"]
        # del temp["funcname"]
        return json.loads(api_inst._get_raw_dut_response())