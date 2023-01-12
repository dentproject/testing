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
import datetime
import inspect
import os, sys, re, site


def getTimeStampStr():
    """
    :return: current timestamp in  %y-%m-%d-%H-%M format
     :rtype: str
    """
    fmt = "%y-%m-%d-%H-%M"
    return datetime.datetime.now().strftime(fmt)


def GetCurrentCodeLineInfo():
    """
    :return: returns caller function file and code in string format
    :rtype: str
    """
    ret = "at "
    cf = inspect.currentframe().f_back
    ret += str(cf.f_code.co_filename) + " line "
    ret += str(cf.f_lineno) + ": "
    return ret


def caller_name(skip=1):
    """Get a name of a caller in the format module.class.method

       `skip` specifies how many levels of stack to skip while getting caller
       name. skip=1 means "who calls me", skip=2 "who calls my caller" etc.

       An empty string is returned if skipped levels exceed stack height
    """
    stack = inspect.stack()
    start = 0 + skip
    if len(stack) < start + 1:
        return ''
    parentframe = stack[start][0]

    name = []
    module = inspect.getmodule(parentframe)
    # `modname` can be None when frame is executed directly in console
    # TODO(techtonik): consider using __main__
    if module:
        name.append(module.__name__)
    # detect classname
    if 'self' in parentframe.f_locals:
        # I don't know any way to detect call from the object method
        # XXX: there seems to be no way to detect static method call - it will
        #      be just a function call
        name.append(parentframe.f_locals['self'].__class__.__name__)
    codename = parentframe.f_code.co_name
    if codename != '<module>':  # top level usually
        name.append(codename)  # function or a method
    del parentframe
    return ".".join(name)


def GetMainFileName(without_extenstion=True):
    """
    searches in the __main__ module launched from commandline
    :param retDir: a prefix that your directory name should contain
    :return: the full path of the seachdir or None if not found
    """
    rootfilename = ""
    import ntpath
    head, tail = ntpath.split(sys.argv[0])
    rootfilename = tail or ntpath.basename(head)
    if without_extenstion:
        temp = rootfilename.split(".")
        temp = temp[:-1]
        if len(temp) >= 2:
            # filename prefix contains "." - take them
            rootfilename = ".".join(temp)
        else:
            rootfilename = "".join(temp)
    return rootfilename
    # def we_are_frozen():
    #     # All of the modules are built-in to the interpreter, e.g., by py2exe
    #     return hasattr(sys , "frozen")
    #
    # def module_path():
    #     encoding = sys.getfilesystemencoding()
    #     if we_are_frozen():
    #         return os.path.dirname(unicode(sys.executable , encoding))
    #     return os.path.dirname(unicode(__file__ , encoding))
    #
    # def get_path_from_sys_argrv():
    #     import ntpath
    #     head, tail = ntpath.split(sys.argv[0])
    #     return tail or ntpath.basename(head)
    # if hasattr(sys.modules['__main__'] , "__file__"):
    #     #rootfilename = sys.modules['__main__'].__file__
    #     rootfilename = get_path_from_sys_argrv()
    # else:
    #     rootfilename = module_path()
    # if rootfilename is not None:
    #     return rootfilename
    # else:
    #     return None


def get_class_that_defined_method(method):
    method_name = ""
    classes = None
    if inspect.ismethod(method):
        method_name = method.__name__
        if method.__self__:
            classes = [method.__self__.__class__]
        elif hasattr(method, "im_class"):
            # unbound method
            classes = [method.__self__.__class__]

            # for cls in inspect.getmro(method.__self__.__class__):
        #     if cls.__dict__.get(method.__name__) == method:
        #         return cls
        # unbound method
        classes = [method.__self__.__class__]
        while classes:
            c = classes.pop()
            if method_name in c.__dict__:
                return c
            else:
                classes = list(c.__bases__) + classes
    return None


def GetFunctionName(func):
    ret = ""
    if hasattr(func, "__name__"):
        ret = func.__name__
    cls = get_class_that_defined_method(func)
    if cls:
        if hasattr(cls, "__name__"):
            ret = cls.__name__ + "::" + ret + ":"
    if ret:
        ret += " "
    return ret


class mswitch(object):
    value = None

    def __new__(self, value):
        self.value = value
        return True


def mcase(*args):
    return any((arg == mswitch.value or arg == "default" for arg in args))


class function_call_params(object):
    def __init__(self):
        self.func = None
        self.args = None
        self.kwargs = None

    def __call__(self, *args, **kwargs):
        if self.func:
            # make sure args and kwargs are iteratble
            if self.args and not hasattr(self.args, "__iter__"):
                self.args = list(self.args)
            if self.kwargs and not hasattr(self.kwargs, "__iter__"):
                self.kwargs = dict((key, val) for key, val in list(self.kwargs.items()))
            if inspect.ismethod(self.func):
                # add self parameter
                if not self.args and not self.kwargs:
                    return self.func()
                elif self.args:
                    self.args = list(self.args)
                    # self.args = [self.func.__self__] +self.args if self.args else [self.func.__self__]
                    if self.kwargs:
                        return self.func(*self.args, **self.kwargs)
                    else:
                        return self.func(*self.args)
                elif self.kwargs:
                    return self.func(**self.kwargs)
            elif not self.args and not self.kwargs:
                self.func()
            else:
                if self.args:
                    if self.kwargs:
                        return self.func(*self.args, **self.kwargs)
                    else:
                        return self.func(*self.args)
                elif self.kwargs:
                    return self.func(**self.kwargs)

    def valditate_params(self, funcname, func, *args, **kwargs):
        #  inner function to validate params
        err = ""
        if not inspect.isfunction(func) and not inspect.ismethod(func):
            err = funcname + " received func variable is not a function or method".format(str(func))
        else:
            signature = inspect.signature(func)
            args_empty = all(len(v) == 0 for v in args)
            kwargs_empty = not bool(kwargs)
            if signature.parameters.keys() and args_empty and kwargs_empty:
                if any(p.default == inspect.Parameter.empty for p in signature.parameters.values()):
                        err = funcname + " received function requires arguments but none given"
            if (not args_empty or not kwargs_empty) and not signature.parameters.keys():
                err = funcname + " received function don't require arguments but args were given:{}". \
                    format(str(args) + str(kwargs))
        if err:
            raise TypeError(err)
