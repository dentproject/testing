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

# Leave this import we need it for other packages
from Marvell.pytoolsinfra.PythonLoggerInfra.LoggerManager.LoggerDecartor import LogWith, Log_all_class_methods
import Marvell.pytoolsinfra.PythonLoggerInfra.LoggerManager as LoggerManager
from Marvell.pytoolsinfra.ConfigurationModule.Configurator.ConfigurationManager.ConfigManager import ConfigManager
import os,platform,pkg_resources

tmpLogger = None
configData = None

if platform.system() == "Linux":
    base_log_dir = "/local/store/ToolsInfraLogs"
    file_locaion_indicator = "/swdev"
else:
    base_log_dir = "c:\\ToolsInfraLogs"
    file_locaion_indicator = "\\\\"

def initLogger():
    global tmpLogger
    if configData.configuration.need_logging:
        if tmpLogger is None:
            l_configData = GetConfigData()
            tmpLogger = LoggerManager.GetLogger(l_configData.configuration.module_name,
                                                GetFullPath(os.path.join('.', l_configData.configuration.logPath)),
                                                l_configData.configuration.logName)
            tmpLogger.setLoggingLevel(LoggerManager.logginglevelNames[l_configData.configuration.logging_level])
    return tmpLogger


base_path = os.path.dirname(os.path.abspath(__file__))


def GetFullPath(path):
    # type: (str) -> str
    if base_path.startswith(file_locaion_indicator):
        base_dir = os.path.join(base_log_dir, GetConfigData().configuration.module_name)
    else:
        base_dir = base_path

    if path.startswith('.'):
        return base_dir + path[1:]
    else:
        return path


def GetConfigData():
    global configData
    if configData is None:
        configData = ConfigManager().read_config_file(os.path.join(base_path, "ResourceManagerConfig.yaml"))
       
    return configData


GetConfigData()
show_func_parameters = configData.configuration.show_func_parameters
ResourceManager_logger = initLogger()

