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
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import object
from .ScriptExecuterExceptions import *
from abc import abstractmethod
import os, signal,time
from _thread import start_new_thread




class ScriptWrapper(object):
    _path_ =""
    _params_= None

    def __init__(self,path, params = None):
        self._path_=path
        self._params_ = params

    @abstractmethod
    def getScriptPath(self):
        """return a string of script's path"""
        return str(self._path_)

    @abstractmethod
    def getScriptParams(self):
        """return a dictionary of script's params as provided if exists otherwise return None"""
        if self._params_ is not None:
            return dict(self._params_)
        return None

    @abstractmethod
    def ScriptExecuteSync(self):
        """script executer algorithm,wait for script to finish,should be implemented by subclass"""
        pass

    @abstractmethod
    def ScriptExecuteAsync(self, timeout):
        """script execute algorithm,NOT wait for script to finish ,should be implemented by
        subclass"""
        pass


    @staticmethod
    def ScriptTerminatorThread(pid,timeout):
        terminator_thread = start_new_thread(ScriptWrapper.ScriptTerminator, (pid,timeout))
        return terminator_thread

    @staticmethod
    def ScriptTerminator(pid,timeout):
        """script terminator algorithm"""
        if timeout is not None:
            time.sleep(timeout)
        try:
            os.kill(pid, signal.SIGTERM)  # or signal.SIGKILL
        except OSError:
            if timeout is None:
                raise ProcessIDException("The given Process ID: "+ str(pid) +" cannot be terminated")
