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

import os,sys

# next bit filched from 1.5.2's inspect.py
def currentframe():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        return sys.exc_info()[2].tb_frame.f_back

if hasattr(sys, '_getframe'): currentframe = lambda: sys._getframe(3)
# done filching

#
# _srcfile is used when walking the stack to check when we've got the first
# caller stack frame.
#
_srcfile = os.path.normcase(currentframe.__code__.co_filename)

def getFileNameWithoutExtension(path):
    return path.split('\\').pop().split('/').pop().rsplit('.', 1)[0]

def getFileNameWithExtension(path):
    return path.split('\\').pop().split('/').pop()

def findTestName():
    if _srcfile:
        #IronPython doesn't track Python frames, so findCaller raises an
        #exception on some versions of IronPython. We trap it here so that
        #IronPython can use logging.
        try:
            return findCaller()
        except ValueError:
            return "(unknown file)", 0, "(unknown function)"
    else:
        return "(unknown file)", 0, "(unknown function)"

def findCaller():
        """
        Find the stack frame of the caller so that we can note the source
        file name, line number and function name.
        """
        f = currentframe()
        # On some versions of IronPython, currentframe() returns None if
        # IronPython isn't run with -X:Frames.
        if f is not None:
            f = f.f_back
        rv = "(unknown file)", 0, "(unknown function)"
        while hasattr(f, "f_code"):
            co = f.f_code
            filename = os.path.normcase(co.co_filename)
            if filename == _srcfile:
                f = f.f_back
                continue
            rv = (co.co_filename, f.f_lineno, co.co_name)
            break

        return rv

def findCallerWithClassName():
    """
            Find the stack frame of the caller so that we can note the source
            file name, line number and function name.
            """
    f = currentframe()
    # On some versions of IronPython, currentframe() returns None if
    # IronPython isn't run with -X:Frames.
    if f is not None:
        f = f.f_back

    while hasattr(f, "f_code"):
        co = f.f_code
        filename = os.path.normcase(co.co_filename)
        tmp = f.f_globals['__name__']
        klass = tmp[tmp.rfind('.') + 1:]
        if filename == _srcfile or klass == "LoggerDecartor":
            f = f.f_back
            continue
        break

    if not f:
        return "(unknown file)", 0, "(unknown function)", "(unknown className)"

    co = f.f_code

    tmp = f.f_globals['__name__']
    klass = tmp[tmp.rfind('.') + 1:]
    rv = (co.co_filename, f.f_lineno, co.co_name, klass)
    return rv

def findCallerEx():
    """
    Find the stack frame of the caller so that we can note the source
    file name, line number and function name.
    """
    f = currentframe()
    # On some versions of IronPython, currentframe() returns None if
    # IronPython isn't run with -X:Frames.
    rv = "(unknown file)", 0, "(unknown function)"
    if f is not None:
        co = f.f_code
        rv = (co.co_filename, f.f_lineno, co.co_name)
    
    return rv


def getCurrentFunctionName(caller):
    fn, lno, func1 = findCallerEx()
    return caller.__class__.__name__ + "." + func1
