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

from Marvell.pytoolsinfra.PythonLoggerInfra.TestLogger.LoggerImpl.BaseTestLogger import BaseTestLogger
from Marvell.pytoolsinfra.PythonLoggerInfra.TestLogger.LoggerImpl.HTMLLogFormat import *


class HTMLLogger(BaseTestLogger):
    def __init__(self, source_name, log_path="", log_filename="", append_source_name=True, console_only_logger=False):
        # type: (str, str, str, bool) -> BaseTestLogger
        super(self.__class__, self).__init__(source_name, log_path, log_filename, append_source_name,
                                             console_only_logger)

        self._log_extention = '.html'

    def initLogger(self, rename=False):
        self.version = "1.0"
        self.title = self._logger_source_name + " Log"

        self._createLoggers()

        if not rename and len(self._logger.handlers) > 0:
            return False

        self.setLoggingLevel(self._default_log_level, False)

        html_formatter = HTMLFormatter()
        html_formatter_nofrmt = HTMLFormatter_NoFormat()

        if not self._console_only_logger:
            if rename:
                self._file_handler = HTMLFileHandler(self.title, self.version, rename, self._filePath, 'a')
            else:
                self._file_handler = HTMLFileHandler(self.title, self.version, rename, self._filePath)

            self._file_handler.flush()
            self._file_handler.setLevel(self._default_log_level)
            self._file_handler.setFormatter(html_formatter)

            if rename:
                self._file_handler_no_format = logging.FileHandler(self._filePath, 'a')
            else:
                self._file_handler_no_format = logging.FileHandler(self._filePath)

            self._file_handler_no_format.setLevel(self._default_log_level)
            self._file_handler_no_format.setFormatter(html_formatter_nofrmt)

            # Assign the handlers to the loggers
            self._logger.addHandler(self._file_handler)
            self._logger_NoFormat.addHandler(self._file_handler_no_format)

        if not rename:
            self._init_console_handlers()

        return True

    def initLogPath(self, path, logname, append_source_name):
        super(self.__class__, self).initLogPath(path, logname, append_source_name)
        self._filePath = self._filePath.replace(".log", ".html")
