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
from __future__ import absolute_import
from builtins import range
import threading
from inspect import getsourcefile
import os.path
import sys, platform
from ...CommonUtils.CustomLoggingLevels import *
import atexit
from datetime import datetime
import shutil
# import distutils.dir_util
# from ...SysLogger.SysLoggetImpl.SysLogger import SysLogger
from .BaseFileHandler import BaseFileHandler
from .CallbackLogHandler import CallbackLogHandler

current_path = os.path.abspath(getsourcefile(lambda: 0))
current_dir = os.path.dirname(current_path)
parent_dir = current_dir[:current_dir.rfind(os.path.sep)]

sys.path.insert(0, parent_dir)

from ..LoggerInterface.ABCTestLogger import *
from ...CommonUtils.fileNameUtils import *


class BaseTestLogger(ABCTestLogger):

    def __init__(self, source_name, log_path="", log_filename="", append_source_name=True, console_only_logger=False):
        # type: (str, str, str, bool) -> BaseTestLogger
        # Register a function to be called befor the class is closing
        # atexit.register(self.cleanup)
        self._console_only_logger = console_only_logger
        self._default_log_level = logging.TRACE
        self._log_extention = '.log'
        self._filePath = ""
        self._file_handler = None
        self._file_handler_no_format = None
        self._logger = None
        self._logger_NoFormat = None
        self._logger_onlyconsole = None
        self._logger_onlyconsole_NoFormat = None
        self._logger_callback_NoFormat = None

        self.callback_handler = None

        self._log_edit_lock = threading.Lock()
        self._testSuffix = ""
        self._isDisabled = False
        # Init logger info
        self._baseDir = './Results'
        self._defaultFormatter = ''
        self._noFormat_Formatter = ''
        self._noFormat_onlyTime_Formatter = ''
        self._logger_source_name = source_name
        self._append_source_name = append_source_name
        self._log_filename = log_filename
        self._log_path = log_path
        self._loggersList = []

        self.init_logger_info()
        self.initLogPath(self._log_path, self._log_filename, self._append_source_name)

        if self.initLogger():
            self.AddSysLog()

            # to avoid root logger dependency we must set it to '0'
            self._logger.propagate = 0
            self._logger_NoFormat.propagate = 0
            self._logger_onlyconsole.propagate = 0
            self._logger_onlyconsole_NoFormat.propagate = 0

            self._loggersList.append(self._logger_onlyconsole_NoFormat)
            self._loggersList.append(self._logger_callback_NoFormat)
            self._loggersList.append(self._logger_NoFormat)
            self._loggersList.append(self._logger_onlyconsole)
            self._loggersList.append(self._logger)

        pass

    def init_logger_info(self):
        self._defaultFormatter = '%(asctime)s:%(levelname)s: %(message)s'
        self._noFormat_Formatter = '%(message)s'
        self._noFormat_onlyTime_Formatter = '%(asctime)s %(message)s'

    def _createLoggers(self):
        # type: () -> bool

        self._logger = logging.getLogger(self._logger_source_name)
        self._logger_NoFormat = logging.getLogger("Logger_NoFormat_" + self._logger_source_name)
        self._logger_onlyconsole = logging.getLogger("Logger_OnlyConsole_" + self._logger_source_name)
        self._logger_onlyconsole_NoFormat = logging.getLogger("Logger_OnlyConsole_NoFormat_" + self._logger_source_name)
        self._logger_callback_NoFormat = logging.getLogger("Logger_CallBack_NoFormat_" + self._logger_source_name)

    def _closeLoggers(self):
        self._logger = None
        self._logger_NoFormat = None
        self._logger_onlyconsole = None
        self._logger_onlyconsole_NoFormat = None
        self._logger_callback_NoFormat = None

    def initLogger(self, rename=False):
        self._createLoggers()
        if not rename and len(self._logger.handlers) > 0:
            return False

        self.setLoggingLevel(self._default_log_level, False)

        formatter = logging.Formatter(self._defaultFormatter)
        formatter_nofrmt = logging.Formatter(self._noFormat_Formatter)

        if not self._console_only_logger:
            if rename:
                self._file_handler = BaseFileHandler(self._filePath, 'a')
            else:
                self._file_handler = BaseFileHandler(self._filePath)

            self._file_handler.setLevel(self._default_log_level)
            self._file_handler.setFormatter(formatter)

            if rename:
                self._file_handler_no_format = BaseFileHandler(self._filePath, 'a')
            else:
                self._file_handler_no_format = BaseFileHandler(self._filePath)

            self._file_handler_no_format.setLevel(self._default_log_level)
            self._file_handler_no_format.setFormatter(formatter_nofrmt)

            # Assign the handlers to the loggers
            self._logger.addHandler(self._file_handler)
            self._logger_NoFormat.addHandler(self._file_handler_no_format)

        if not rename:
            self._init_console_handlers()

        return True

    def _init_console_handlers(self):
        formatter = logging.Formatter(self._defaultFormatter)
        formatter_nofrmt = logging.Formatter(self._noFormat_Formatter)
        stream_handler = logging.StreamHandler(stream=sys.stdout)
        stream_handler.flush = sys.stdout.flush
        stream_handler.setFormatter(formatter)

        stream_handler_no_format = logging.StreamHandler(stream=sys.stdout)
        stream_handler_no_format.flush = sys.stdout.flush
        stream_handler_no_format.setFormatter(formatter_nofrmt)

        self.callback_handler = CallbackLogHandler()
        formatter_only_time = logging.Formatter(self._noFormat_onlyTime_Formatter)
        self.callback_handler.setFormatter(formatter_only_time)

        self._logger_onlyconsole.addHandler(stream_handler)
        self._logger_onlyconsole_NoFormat.addHandler(stream_handler_no_format)
        self._logger_callback_NoFormat.addHandler(self.callback_handler)

    def initLogPath(self, path, logname, append_source_name):
        if self._console_only_logger:
            return

        if logname == "":
            tmpFileNameDir = getFileNameWithoutExtension(findTestName()[0])
        else:
            tmpFileNameDir = logname

        tmpFileName = tmpFileNameDir + datetime.now().strftime('_%H-%M-%S-%f')[:-3]

        source_name = ""
        if append_source_name:
            source_name = self._logger_source_name

        logpath = path
        if path == "":
            logpath = self._baseDir

        self._filePath = os.path.join(logpath, source_name, tmpFileName) + self._log_extention
        if platform.system() == "Windows": # Must add the "\\\\?\\" prefix to support paths that are longer then windows MAX_PATH
            self._filePath = "\\\\?\\" + os.path.abspath(self._filePath)
        elif platform.system() == "Linux":
            self._filePath = os.path.abspath(self._filePath)
        self.ensure_dir(self._filePath)

    def rename_logger(self, path="", logname=""):
        if self._console_only_logger:
            return

        old__filePath = self._filePath

        if path == self._log_path and logname == self._log_filename:
            return

        if path == "":
            path = self._log_path

        if logname == "":
            logname = self._log_filename

        # try get the lock for editing the log file
        self._log_edit_lock.acquire()

        try:
            # must set it to make sure that for 'HTML' format we won't add the footer of the file
            self._file_handler.renamed = True
            self._file_handler_no_format.renamed = True
            # SysLogger.set_log_rename_start()

            logging.shutdown()

            # SysLogger.set_log_rename_end()

            self.initLogPath(path, logname, self._append_source_name)
            try:
                shutil.copy2(old__filePath, self._filePath)
            except Exception as e:
                self._filePath = old__filePath
                print ("can't copy the new file due to "+e.message)
                # the 'finally:' will release the lock
                return

            try:
                os.remove(old__filePath)
            except Exception as e:
                print ("can't remove old logger due to " + e.message)

            self._logger.removeHandler(self._file_handler)
            self._logger_NoFormat.removeHandler(self._file_handler_no_format)

            self.initLogger(True)

        finally:
            # must release the lock to make sure the other functions can run
            self._log_edit_lock.release()

    def cleanup(self):
        self.closeLogger()

    def closeLogger(self):
        # if we already closed the logger we don't need to try to close it again
        if self._isDisabled:
            return

        for l in self._loggersList:
            handlers = l.handlers[:]
            for handler in handlers:
                handler.close()
                l.removeHandler(handler)
            if logging.Logger.manager.loggerDict.get(l.name):
                logging.Logger.manager.loggerDict.pop(l.name)

            no_ext = os.path.splitext(l.name)[0]

            if logging.Logger.manager.loggerDict.get(no_ext):
                logging.Logger.manager.loggerDict.pop(no_ext)
            del l

        self._isDisabled = True
        self._closeLoggers()
        self._loggersList = []
        logging.shutdown()
        if self._console_only_logger:
            return

        if not self._testSuffix == "":
            suffix_added = False
            # as it might take the os some time to release the file resource we try to rename it a few times
            import errno,time
            for i in range(5):
                try:
                    os.rename(self._filePath, self._filePath.replace(self._log_extention, '_{}{}'.format(
                                                                                self._testSuffix,self._log_extention)))
                    suffix_added = True
                    break
                except IOError as e:
                    if e.errno == errno.EBUSY:
                        print ("rename attempt #{}".format(i+1))
                        time.sleep(500)
                        continue
                    break

            if suffix_added:
                self._filePath = self._filePath.replace(self._log_extention, '_{}{}'.format(self._testSuffix,
                                                                                            self._log_extention))

    def AppenSuffixToLogName(self, suffix):
        self._testSuffix = suffix

    def setLoggingLevel(self, level, useLock=True):
        if self._isDisabled:
            return

        # try get the lock for editing the log file
        if useLock:
            self._log_edit_lock.acquire()

        try:
            self._logger_onlyconsole.setLevel(level)
            self._logger_onlyconsole_NoFormat.setLevel(level)
            self._logger_callback_NoFormat.setLevel(level)
            self._logger.setLevel(level)
            self._logger_NoFormat.setLevel(level)
        finally:
            # must release the lock to make sure the other functions can run
            if useLock:
                self._log_edit_lock.release()

    def addLoggingCallBack(self, logFunc):
        if self.callback_handler is not None:
            self.callback_handler.addLogFunc(logFunc)

    def removeLoggingCallBack(self, logFunc):
        if self.callback_handler is not None:
            self.callback_handler.removeLogFunc(logFunc)

    def error(self, msg, *args, **kwargs):
        if self._isDisabled:
            return

        # try get the lock for editing the log file
        self._log_edit_lock.acquire()

        try:
            loggers, kwargs = self._GetRightLogger(**kwargs)
            for logger in loggers:
                logger.error(msg, *args, **kwargs)
        finally:
            # must release the lock to make sure the other functions can run
            self._log_edit_lock.release()

    def exception(self, msg, *args, **kwargs):
        if self._isDisabled:
            return

        # try get the lock for editing the log file
        self._log_edit_lock.acquire()

        try:
            loggers, kwargs = self._GetRightLogger(**kwargs)
            for logger in loggers:
                logger.exception(msg, *args, **kwargs)
        finally:
            # must release the lock to make sure the other functions can run
            self._log_edit_lock.release()
    
    def trace(self, msg, *args, **kwargs):
        if self._isDisabled:
            return

        # try get the lock for editing the log file
        self._log_edit_lock.acquire()

        try:
            loggers, kwargs = self._GetRightLogger(**kwargs)
            for logger in loggers:
                logger.log(logging.TRACE,msg, *args, **kwargs)
        finally:
            # must release the lock to make sure the other functions can run
            self._log_edit_lock.release()
    
    def debug(self, msg, *args, **kwargs):
        if self._isDisabled:
            return

        # try get the lock for editing the log file
        self._log_edit_lock.acquire()

        try:
            loggers, kwargs = self._GetRightLogger(**kwargs)
            for logger in loggers:
                logger.debug(msg, *args, **kwargs)
        finally:
            # must release the lock to make sure the other functions can run
            self._log_edit_lock.release()

    def info(self, msg, *args, **kwargs):
        if self._isDisabled:
            return

        # try get the lock for editing the log file
        self._log_edit_lock.acquire()

        try:
            loggers, kwargs = self._GetRightLogger(**kwargs)
            for logger in loggers:
                logger.info(msg, *args, **kwargs)
        finally:
            # must release the lock to make sure the other functions can run
            self._log_edit_lock.release()

    def critical(self, msg, *args, **kwargs):
        if self._isDisabled:
            return

        # try get the lock for editing the log file
        self._log_edit_lock.acquire()

        try:
            loggers, kwargs = self._GetRightLogger(**kwargs)
            for logger in loggers:
                logger.critical(msg, *args, **kwargs)
        finally:
            # must release the lock to make sure the other functions can run
            self._log_edit_lock.release()

    def warning(self, msg, *args, **kwargs):
        if self._isDisabled:
            return

        # try get the lock for editing the log file
        self._log_edit_lock.acquire()

        try:
            loggers, kwargs = self._GetRightLogger(**kwargs)
            for logger in loggers:
                logger.warning(msg, *args, **kwargs)
        finally:
            # must release the lock to make sure the other functions can run
            self._log_edit_lock.release()

    def _GetRightLogger(self, **kwargs):
        bNoFormat = False
        bOnlyConsole = False
        bOnlyLog = False
        bLogToCallBack = False

        tmp_entry = kwargs.get('noFormat')
        if tmp_entry is not None:
            bNoFormat = tmp_entry
            kwargs.__delitem__('noFormat')

        tmp_entry = kwargs.get('onlyConsole')
        if tmp_entry is not None:
            bOnlyConsole = tmp_entry
            kwargs.__delitem__('onlyConsole')

        tmp_entry = kwargs.get('onlyLog')
        if tmp_entry is not None:
            bOnlyLog = tmp_entry
            kwargs.__delitem__('onlyLog')

        tmp_entry = kwargs.get('logToStream')
        if tmp_entry is not None:
            bLogToCallBack = tmp_entry
            kwargs.__delitem__('logToStream')

        if self._console_only_logger:
            bOnlyConsole = True

        loggersList = []
        if bLogToCallBack:
            loggersList.append(self._logger_callback_NoFormat)

        if bNoFormat:
            if bOnlyConsole:
                loggersList.append(self._logger_onlyconsole_NoFormat)
            elif bOnlyLog:
                loggersList.append(self._logger_NoFormat)
            else:
                loggersList.append(self._logger_NoFormat)
                loggersList.append(self._logger_onlyconsole_NoFormat)

        elif bOnlyConsole:
            loggersList.append(self._logger_onlyconsole)

        elif bOnlyLog:
            loggersList.append(self._logger)

        else:
            loggersList.append(self._logger)
            loggersList.append(self._logger_onlyconsole)

        return loggersList, kwargs

    def AddSysLog(self):
        # SysLogger.AddSysLog(self._logger_source_name, self._logger, self._logger_NoFormat)
        pass

    @staticmethod
    def ensure_dir(file_path):
        pathdir = os.path.dirname(file_path)
        if not os.path.exists(pathdir):
            os.makedirs(pathdir)
            # distutils.dir_util.mkpath(dir1)

            # def findTestName(self):
            #     if _srcfile:
            #         #IronPython doesn't track Python frames, so findCaller raises an
            #         #exception on some versions of IronPython. We trap it here so that
            #         #IronPython can use logging.
            #         try:
            #             return self.findCaller()
            #         except ValueError:
            #             return "(unknown file)", 0, "(unknown function)"
            #     else:
            #         return "(unknown file)", 0, "(unknown function)"

            # def findCaller(self):
            #         """
            #         Find the stack frame of the caller so that we can note the source
            #         file name, line number and function name.
            #         """
            #         f = currentframe()
            #         # On some versions of IronPython, currentframe() returns None if
            #         # IronPython isn't run with -X:Frames.
            #         if f is not None:
            #             f = f.f_back
            #         rv = "(unknown file)", 0, "(unknown function)"
            #         while hasattr(f, "f_code"):
            #             co = f.f_code
            #             filename = os.path.normcase(co.co_filename)
            #             if filename == _srcfile:
            #                 f = f.f_back
            #                 continue
            #             rv = (co.co_filename, f.f_lineno, co.co_name)
            #             break
            #         return rv

# def MyPath():
#     from inspect import getsourcefile
#     import os.path
#     return os.path.abspath(getsourcefile(lambda: 0))

# test = BaseTestLogger()
# test.debug("test")
