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

import datetime
import os
from time import strftime
from PyInfraCommon.ExternalImports.Logger import BaseTestLogger,LogType,GetLogger
from PyInfraCommon.GlobalFunctions.Utils.Exception import GetStackTraceOnException
from PyInfraCommon.GlobalFunctions.Utils.Function import GetFunctionName, GetMainFileName


class LoggerCreator(object):
    """
    helper class to create loggers in addition to test logger for cases where tests needs more log files
    """
    def __init__(self):
        self.log_created = False
        self.log_creation_date = ""
        self.log_dir_path = ""
        self.log_GRASS_base_path = ""
        self.file_name = ""
        self.file_name_prefix = ""
        self.log_format = LogType.HTML_LOGGER
        self.log_level = None  # type:BaseTestLogger
        self._logger_callbacks = []
        self._logger = None
        self.file_name_with_timestamp = True
        self.override_dir = None

    @property
    def logger(self):
        """

        :return:
        :rtype: BaseTestLogger
        """
        return self._logger

    def _BuildLogPath(self, path_dir_list=None):
        funcname = GetFunctionName(self._BuildLogPath)
        if self.override_dir:
            self.log_dir_path = self.override_dir
            return
        currentDir = os.getcwd()
        self.log_GRASS_base_path = os.path.join(currentDir, "Results", self.file_name, '')
        log_creation_date = strftime('%d-%m-%Y')
        path = self.log_GRASS_base_path
        if not path_dir_list:
            path_dir_list = [self.log_creation_date]
        for i in range(len(path_dir_list)):
            Dir = path_dir_list[i]
            if Dir != "":
                if i != len(path_dir_list) - 1:
                    path = os.path.join(path, Dir, '')
                else:
                    path = os.path.join(path, Dir)
        self.log_dir_path = path

    def _InitLogFilenameFromTestName(self):
        self.file_name  = GetMainFileName()

    def _InitTestLog(self):
        """
        generates the test log for the test
        :return:
        """
        funcname = GetFunctionName(self._InitTestLog)
        if not self.file_name:
            self._InitLogFilenameFromTestName()
        # update test name based on file name
        self.log_format = LogType.HTML_LOGGER
        self._BuildLogPath()
        tmp_timestamp = datetime.datetime.now().strftime('_%H-%M-%S-%f') if self.file_name_with_timestamp else ""
        logname = self.file_name_prefix+self.file_name + tmp_timestamp
        self._logger = GetLogger(logname, self.log_dir_path,
                                 logname=logname,append_source_name=False, logger_type=self.log_format)
        if self._logger:
            self.log_created = True
        self._logger.setLoggingLevel("TRACE")
        return self._logger

    def Create(self,file_name="",file_name_prefix="",file_name_with_timestamp =True,log_dir=""):
        """
        create a test logger and return instance to caller
        :param file_name: if specified will use this file name else will take main file (test file) file name
        :type file_name: str
        :param file_name_prefix:
        :type file_name_prefix:
        :return:
        :rtype:BaseTestLogger
        """
        self.file_name = file_name
        self.file_name_prefix = file_name_prefix
        self.file_name_with_timestamp = file_name_with_timestamp
        self.override_dir = log_dir
        return self._InitTestLog()

    def CloseLogger(self):
        funcname = GetFunctionName(self.CloseLogger)
        if self.log_created:
            try:
                self.logger.closeLogger()
            except Exception as ex:
                err = funcname + " caught exception: {}".format(GetStackTraceOnException(ex))
                print(err)
            finally:
                self.DeleteLogger()

    def DeleteLogger(self):
        if self.logger is not None:
            del self._logger
            self._logger = None

    def LogUnHandledExceptions(self, msg):
        filename = "unhandled_errors.txt"
        path = os.path.join(self.log_dir_path, filename)
        with open(path, "w") as f:
            f.write(msg)
            f.flush()
            f.close()