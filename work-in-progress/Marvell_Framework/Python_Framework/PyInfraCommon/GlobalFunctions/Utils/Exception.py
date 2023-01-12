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
import sys,traceback
try:
    from exceptions import Exception
except Exception as ex:
    pass
from PyInfraCommon.GlobalFunctions.Utils.Function import GetFunctionName


def GetStackTraceOnException(exeception_obj):
    """
    :param exeception_obj: exception object that was caught
    :type exeception_obj: Exception
    :return: returns string of exception information and stack trace
    :rtype: str
    """
    funcname = GetFunctionName(GetStackTraceOnException)
    exp_info = ""
    if not isinstance(exeception_obj,BaseException):
        err = funcname + "Warning: exeception_obj is not inherited from BaseException"
        print(err)
    try:
        exp_info = "type {}, message {}".format(type(exeception_obj),exeception_obj)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        err = "\nFull Exception Call Stack\n"
        traceblist = traceback.format_exception(exc_type, exc_value, exc_traceback)
        for tb in traceblist:
            err += tb
        exp_info += err
        return exp_info
    except Exception as e:
        err = funcname + "caught exception: {}".format(str(e))
        print(err)
    finally:
        return exp_info