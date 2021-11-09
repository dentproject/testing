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

from __future__ import absolute_import
from builtins import object
from .ScriptTypeClassesFactory import *
from .ScriptWrapper import *

"""
Generic Script Handler API .
its support the bellow Functions.
"""

class ScriptHandlerAPI(object):

    @staticmethod
    def ExecuterSync(path, script_params=None):
        """Execute given script and WAIT until it's end of running
        Arguments:
            * path: the path of the script, should be deterministic
            * script_params: parameters to be transfer to script, MUST BE a dictionary type
        Return:
            stdout and stderr of the script
        """
        script_class = ScriptTypeFactory.create_script_class(path,script_params)
        stdout = script_class.ScriptExecuteSync()
        return stdout

    @staticmethod
    def ExecuterAsync(path, script_params=None, timeout = 300):
        """Execute script and NOT wait until it finish
            the script will be terminated after given timeout
        Arguments:
            * path: the path of the script, should be deterministic
            * script_params: parameters to be transfer to script, MUST BE a dictionary type
            * timeout: Terminate the script after given timeout
        Return:
            pid of the script's process
        """
        script_class = ScriptTypeFactory.create_script_class(path,script_params)
        pid = script_class.ScriptExecuteAsync(timeout)
        return pid

    @staticmethod
    def TerminateSync(pid, timeout = None):
        """Terminate given script using it's process pid
        Arguments:
            * pid: The pid of the script's process
            * timeout: Terminate the script after given timeout or if timeout is None terminate
                       immediately
        """
        if timeout is None:
            ScriptWrapper.ScriptTerminator(pid,None)
            return 0
        else:
            assert (timeout is not None)
            return ScriptWrapper.ScriptTerminatorThread(pid,timeout)
