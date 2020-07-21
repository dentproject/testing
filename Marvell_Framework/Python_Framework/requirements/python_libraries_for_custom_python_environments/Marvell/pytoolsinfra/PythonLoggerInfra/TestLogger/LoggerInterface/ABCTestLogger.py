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
from abc import ABCMeta, abstractmethod
from future.utils import with_metaclass

"""
This is an abstract class that define all the Logger functions for our Test's logger

"""

class ABCTestLogger(with_metaclass(ABCMeta, object)):
    def __init__(self):
        raise NotImplementedError('ERROR: Cant instantiate abstract class')

    @abstractmethod
    def AppenSuffixToLogName(self, suffix):
        """
        This function will add the 'suffix' to the end of the log name when the log is clossing
        :param suffix: string that will be appending to the end of the name
        :return:None
        """
        pass

    @abstractmethod
    def rename_logger(self, path="", logname=""):
        """
        This function will rename the logger's Path and/or Name
        :param path: the new logger's path
        :param logname: The new logger's name
        :return:None
        """
        pass

    @abstractmethod
    def trace(self, msg, *args, **kwargs):
        """Logs a message with level TRACE on the root logger. The msg is the message format string,
        and the args are the arguments which are merged into msg using the string formatting operator."""
        pass
    
    @abstractmethod
    def debug(self, msg, *args, **kwargs):
        """Logs a message with level DEBUG on the root logger. The msg is the message format string, 
        and the args are the arguments which are merged into msg using the string formatting operator."""
        pass

    @abstractmethod
    def info(self, msg, *args, **kwargs):
        """Logs a message with level INFO on the root logger. The arguments are interpreted as for debug()."""
        pass

    @abstractmethod
    def warning(self, msg, *args, **kwargs):
        """Logs a message with level WARNING on the root logger. The arguments are interpreted as for debug()."""
        pass

    @abstractmethod
    def error(self, msg, *args, **kwargs):
        """Logs a message with level ERROR on the root logger. The arguments are interpreted as for debug()."""
        pass

    @abstractmethod
    def critical(self, msg, *args, **kwargs):
        """Logs a message with level CRITICAL on the root logger. The arguments are interpreted as for debug()."""
        pass

    @abstractmethod
    def exception(self, msg, *args, **kwargs):
        """
        Logs a message with level ERROR on the root logger. The arguments are interpreted as for debug(), 
        except that any passed exc_info is not inspected. Exception info is always added to the logging message. 
        This function should only be called from an exception handler.
        """
        pass

    @abstractmethod
    def closeLogger(self):
        """
        Informs the logging system to perform an orderly shutdown by flushing and closing all handlers. 
        This should be called at application exit and no further use of the logging system should be made 
        after this call.
        """
        pass

    @abstractmethod
    def setLoggingLevel(self, level):
        """
        Sets the logging level for this logger.
        """
        pass

    @abstractmethod
    def addLoggingCallBack(self, logFunc):
        """
        adding new 'CallBack' for logging to external application
        :param logFunc: CallBack for logging every message that will have 'logToStream' parameter
        :return:
        """
        pass

    @abstractmethod
    def removeLoggingCallBack(self, logFunc):
        """
        removing the 'CallBack' for logging to external application
        :param logFunc: CallBack ref for removing from the callback Handler
        :return:
        """
        pass