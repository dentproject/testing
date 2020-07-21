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
from builtins import object
import os
from time import strftime

from PyInfraCommon.GlobalFunctions.Utils.Function import GetMainFileName, GetFunctionName
from PyInfraCommon.ExternalImports.Logger import BaseTestLogger, GetLogger, LogType


class _GTestLogger(object):
    """
    this class provides access for external modules to the test logger
    this test logger class is actually a singleton
    this logger should be inited by the BASETest module and it can then be accessed by external modules
    :type logger: BaseTestLogger
    :type _logger: BaseTestLogger
    """
    _logger = None

    @property
    def logger(self):
        """
        :rtype: BaseTestLogger
        """
        if self._logger is not None:
            return self._logger
        else:
            funcname = GetFunctionName(_GTestLogger)
            err = funcname + " Warning: the global logger is not initilized, initializing an logger without a test name"
            print (err)
            if not self._create_temp_logger():
                err = funcname + " Error: failed to initialize a logger without a test name"
                print (err)
            return self._logger

    @logger.setter
    def logger(self, logger):
        self._logger = logger

    def _create_temp_logger(self):
        """
        generates a logfile path in cases where loggers is not initilized
        :return: True if succeeded to generate log or False Otherwise
        :rtype: bool
        """

        def getlogpath(filename):
            currentDir = os.getcwd()
            GrasResultsBasePath = os.path.join(currentDir, "Results", filename) + os.sep
            currentDate = strftime("%d-%m-%Y")
            path = GrasResultsBasePath
            return path

        ret = True
        filename = GetMainFileName()
        funcname = GetFunctionName(self._create_temp_logger)
        # fl = filename.split("/")
        # if "filer" in filename.lower():
        #     fl = filename.split("\\")
        # # extract file name from path
        # filename = fl[-1].split(".")[0]
        log_path = getlogpath(filename)
        try:
            self.logger = GetLogger(filename, log_path, filename, append_source_name=False,
                                    logger_type=LogType.HTML_LOGGER)

        except Exception as e:
            err = funcname + " failed to create a logger, got error {}\n".format(str(e))
            self.logger = None
        if not self.logger:
            ret = False
        return ret


GlobalLogger = _GTestLogger()
