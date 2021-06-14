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

from __future__ import print_function
# Leave this import we need it for other packages
from builtins import str
from Marvell.pytoolsinfra.PythonLoggerInfra.LoggerManager.LoggerDecartor import LogWith, Log_all_class_methods
from Marvell.pytoolsinfra.PythonLoggerInfra import LoggerManager
from Marvell.pytoolsinfra.ConfigurationModule.Configurator.ConfigurationManager.ConfigManager import ConfigManager
import os

tmpLogger = None
configData = None
console_only_logger = True

def initLogger():
    global tmpLogger
    if configData.configuration.need_logging:
        if tmpLogger is None:
            l_configData = GetConfigData()
            tmpLogger = LoggerManager.GetLogger(l_configData.configuration.module_name,
                                                GetFullPath(l_configData.configuration.logPath),
                                                l_configData.configuration.logName,
                                                console_only_logger=console_only_logger)
            tmpLogger.setLoggingLevel(LoggerManager.logginglevelNames[l_configData.configuration.logging_level])
    return tmpLogger


base_path = os.path.dirname(os.path.abspath(__file__))


def GetFullPath(path):
    # type: (str) -> str
    config_data = GetConfigData()

    print("config data is: {}".format(str(config_data)))

    if config_data is None:
        return path
    base_dir = "c:\\ToolsInfraLogs\\" + config_data.configuration.module_name if base_path.startswith("\\\\") \
        else base_path
    if path.startswith('.'):
        return base_dir + path[1:]
    else:
        return path


def GetConfigData():
    global configData
    if configData is None:
        configData = ConfigManager().read_config_file(os.path.join(base_path, "CommWrapperConfig.yaml"))
    return configData


GetConfigData()
show_func_parameters = configData.configuration.show_func_parameters
CommWrapper_logger = initLogger()

