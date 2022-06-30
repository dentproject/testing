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

from PyInfraCommon.GlobalFunctions.Logger.LoggerCreator import LoggerCreator
from PyInfraCommon.GlobalFunctions.Utils.Exception import GetStackTraceOnException
import functools

def evaluate_and_log_exceptions(func):
    @functools.wraps(func)
    def inner_wrapper(*args,**kwargs):
        try:
            return func(*args,**kwargs)
        except Exception as ex:
            err = "evaluat_and_log_exceptions" + "caught exception while running: {}".format(GetStackTraceOnException(ex))
            logger_tmp = LoggerCreator()
            logger_tmp.Create(file_name_prefix="Crash_")
            logger_tmp.logger.error(err)
            logger_tmp.CloseLogger()

    return inner_wrapper