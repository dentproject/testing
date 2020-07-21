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

from Marvell.pytoolsinfra.PythonLoggerInfra.CommonUtils.CustomLoggingLevels import *

from Marvell.pytoolsinfra.CommonDef.CommonUtils.Switch import Switch, case
from Marvell.pytoolsinfra.PythonLoggerInfra.TestLogger.LoggerInterface.ABCTestLogger import ABCTestLogger
from Marvell.pytoolsinfra.PythonLoggerInfra.TestLogger.LoggerImpl.HTML_Logger import HTMLLogger
from Marvell.pytoolsinfra.PythonLoggerInfra.TestLogger.LoggerImpl.BaseTestLogger import BaseTestLogger


class LogType(Enum):
    TEST_LOGGER = 1
    HTML_LOGGER = 2

def GetLogger(source_name, logPath="", logname="", append_source_name=True, logger_type=LogType.TEST_LOGGER,
              console_only_logger=False):
    # type: (str, str, str) -> ABCTestLogger

    while Switch(logger_type):
        if case(LogType.TEST_LOGGER):
            result = BaseTestLogger(source_name, logPath, logname, append_source_name, console_only_logger)
            break
        if case(LogType.HTML_LOGGER):
            result = HTMLLogger(source_name, logPath, logname, append_source_name, console_only_logger)
            break
   
    return result


# test = GetLogger('name')
# test.info("test")
# test.error("test")
# test.critical("test")
# try:
#     a = 5
#     b = 0
#     c = a/b
# except ZeroDivisionError:
#     test.exception("test")
# test.warning("test")
