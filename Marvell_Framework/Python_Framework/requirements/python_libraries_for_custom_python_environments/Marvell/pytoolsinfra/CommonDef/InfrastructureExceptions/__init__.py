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
from builtins import range
import inspect


class BaseInfraException(Exception):
    def __init__(self, message=None):
        super(self.__class__, self).__init__(message)

    @staticmethod
    def get_logger_from_class(class_obj):
        return getattr(class_obj, 'logger', None)

    @staticmethod
    def get_class_from_frame():
        instance = None
        for i in range(1, len(inspect.stack())):
            fr = inspect.stack()[i][0]
            args, _, _, value_dict = inspect.getargvalues(fr)
            # we check the first parameter for the frame function is
            # named 'self'
            if len(args) and args[0] == 'self':
                # in that case, 'self' will be referenced in value_dict
                instance = value_dict.get('self', None)
                if not issubclass(instance.__class__, BaseInfraException):
                    break

        # return its class
        # return None otherwise
        return instance


class LoggedException(BaseInfraException):
    def __init__(self, message=None):
        super(BaseInfraException, self).__init__(message)

        caller = self.get_class_from_frame()

        caller_logger = self.get_logger_from_class(caller)
        if caller_logger is not None:
            caller_logger.exception(message)
        else:
            print("Caller has not logger")
