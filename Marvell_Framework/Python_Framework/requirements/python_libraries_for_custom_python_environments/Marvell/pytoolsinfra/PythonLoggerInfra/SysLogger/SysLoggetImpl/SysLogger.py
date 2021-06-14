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
import os
from abc import ABCMeta
from datetime import datetime
from Marvell.pytoolsinfra.PythonLoggerInfra.SysLogger.SysLoggetImpl.HTMLSysLogFormatter import *
from future.utils import with_metaclass


class SysLogger(with_metaclass(ABCMeta, object)):
    _syslog_filePath = None
    sys_log_name = "PythonInfraSysLog"
    _baseDir = "Results"
    _defaultFormatter = '%(asctime)s:%(levelname)s: %(message)s'
    _bIsFirstTime = True
    _sys_file_handler = None

    def __init__(self):
        raise NotImplementedError('ERROR: Cant instantiate abstract class')

    @classmethod
    def AddSysLog(cls, source_name, *args):

        hnd = cls.initSysFileHandler(source_name)

        for logger in args:
            logger.addHandler(hnd)

    @classmethod
    def initSysFileHandler(cls, logger_source_name):
        """
        :rtype: log_file_handler
        """

        if cls._bIsFirstTime:
            cls.initSysLogPath()
            cls._bIsFirstTime = False

            formatter = SysLogHTMLFormatter(logger_source_name)
            version = "1.0"
            title = cls.sys_log_name
            cls._sys_file_handler = SysHTMLFileHandler(title, version, False, cls._syslog_filePath)
            cls._sys_file_handler.setLevel(logging.TRACE)
            cls._sys_file_handler.setFormatter(formatter)

        return cls._sys_file_handler

    @classmethod
    def initSysLogPath(cls):
        if cls._syslog_filePath is None:
            base_path = os.path.dirname(os.path.abspath(__file__))
            base_path = os.path.dirname(base_path)
            base_path = os.path.dirname(base_path)

            base_path = os.path.join(base_path, cls._baseDir)
            t = datetime.now()
            date_folder = t.strftime("%d_%m_%y")
            tmpFileName = cls.sys_log_name + t.strftime('_%H-%M-%S-f')[:-3]

            cls._syslog_filePath = os.path.join(base_path, date_folder, tmpFileName) + '.html'
            cls.ensure_dir(cls._syslog_filePath)

    @staticmethod
    def ensure_dir(file_path):
        pathdir = os.path.dirname(file_path)
        if not os.path.exists(pathdir):
            os.makedirs(pathdir)

    @classmethod
    def set_log_rename_start(cls):
        cls._sys_file_handler.renamed = True

    @classmethod
    def set_log_rename_end(cls):
        cls._sys_file_handler.renamed = False
