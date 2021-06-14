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

import os, platform
from Marvell.pytoolsinfra.PythonLoggerInfra import LoggerManager
from Marvell.pytoolsinfra.PythonLoggerInfra.LoggerManager.DummyLogger import DummyLogger
from Marvell.pytoolsinfra.PythonLoggerInfra.LoggerManager.LoggerDecartor import LogWith, Log_all_class_methods

tmp_logger = None
show_params = True
console_only_logger = True

if platform.system() == "Linux":
    base_log_dir = "/local/store/ToolsInfraLogs"
    file_locaion_indicator = "/swdev"
else:
    base_log_dir = "c:\\ToolsInfraLogs"
    file_locaion_indicator = "\\\\"

base_path = os.path.dirname(os.path.abspath(__file__))


def GetFullPath(path):
    # type: (str) -> str
    if base_path.startswith(file_locaion_indicator):
        base_dir = os.path.join(base_log_dir, "ConfigurationModule")
    else:
        base_dir = base_path

    if path.startswith('.'):
        return base_dir + path[1:]
    else:
        return path

def init_logger():
    global tmp_logger
    if tmp_logger is None:
        tmp_logger = LoggerManager.GetLogger("ConfigurationModule", GetFullPath(os.path.join('.', 'Results')),
                                             "ConfigurationModuleLog", logger_type=LoggerManager.LogType.HTML_LOGGER,
                                             console_only_logger=console_only_logger)
        tmp_logger.setLoggingLevel(LoggerManager.INFO)
    return tmp_logger


config_logger = init_logger()
