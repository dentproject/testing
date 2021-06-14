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

from builtins import str
from builtins import object
import functools
import inspect

# from PythonLoggerInfra.CommonUtils.fileNameUtils import findCallerEx


class LogWith(object):
    '''
        Logging decorator that allows you to log with a
        specific logger.
    '''
    # Customize these messages
    # ENTRY_MESSAGE = 'Entering {} At File {}'
    # EXIT_MESSAGE = 'Exiting {} At File {}'
    ENTRY_MESSAGE = 'Entering {}::{}'
    EXIT_MESSAGE = 'Exiting {}::{}'

    def __init__(self, logger, print_parameters=False):
        self.logger = logger
        self.print_parameters = print_parameters
        self.decorated_class = ""

    def __call__(self, func):
        '''
            Returns a wrapper that wraps func.
            The wrapper will log the entry and exit points of the function
            with logging.INFO level.
        '''
        # set logger if it was not set earlier
        if not self.logger:
            return func

        try:
            self.decorated_class = func.__self__.__class__.__name__
        except Exception as e:
            from Marvell.pytoolsinfra.PythonLoggerInfra.CommonUtils.fileNameUtils import findCallerEx, getFileNameWithoutExtension
            fn, lno, func1 = findCallerEx()
            self.decorated_class = getFileNameWithoutExtension(fn)

        @functools.wraps(func)
        def wrapper(*args, **kwds):
            extraMsg = ""
            if self.print_parameters:
                extraMsg = " with parameters : " + str(args[1:]) + " " + str(list(kwds.items()))

            self.logger.debug(self.ENTRY_MESSAGE.format(self.decorated_class, func.__name__) + extraMsg, onlyLog=True)
            f_result = func(*args, **kwds)
            self.logger.debug(self.EXIT_MESSAGE.format(self.decorated_class, func.__name__), onlyLog=True)

            return f_result
        return wrapper


def Log_all_class_methods(cls, _logger, show_func_parameters):
    for name, method in inspect.getmembers(cls, inspect.ismethod):
        if not name.startswith('__'):
            setattr(cls, name, LogWith(_logger, show_func_parameters)(method))
    return cls

# For Debugging uncomment this and comment the above
# def Log_all_class_methods(cls, _logger, show_func_parameters):
#     return cls
#
# ######### End ##############


# def Log_all_class_methods(cls, logger, print_parameters=False):
#     class NewCls(object):
#         def __init__(self, *args, **kwargs):
#             self.oInstance = cls(*args, **kwargs)
#             self.decorated_class_name = str(cls.__name__)
#
#         def __getattribute__(self, s):
#             """
#             this is called whenever any attribute of a NewCls object is accessed. This function first tries to
#             get the attribute off NewCls. If it fails then it tries to fetch the attribute from self.oInstance (an
#             instance of the decorated class). If it manages to fetch the attribute from self.oInstance, and
#             the attribute is an instance method then `time_this` is applied.
#             """
#             try:
#                 x = super(NewCls, self).__getattribute__(s)
#             except AttributeError:
#                 pass
#             else:
#                 return x
#             x = self.oInstance.__getattribute__(s)
#             if type(x) == type(self.__init__):  # it is an instance method
#                 return LogWith(self.decorated_class_name, logger, print_parameters)(x) # this is equivalent of just decorating the method with LogWith
#             else:
#                 return x
#
#         def __setattr__(self, key, value):
#             try:
#                 super(NewCls, self).__setattr__(key, value)
#             except AttributeError:
#                 pass
#             else:
#                 return
#
#             self.oInstance.setattr(key, value)
#
#     return NewCls
