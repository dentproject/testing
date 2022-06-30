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
from builtins import str
from Marvell.CommunicationService.Common.Types import CommunicationType as ComTypes
from Marvell.CommunicationService.HighCommunicationLayer.CommunicationManagement import CommunicationManagement

from .PyComWrapper import PyBaseComWrapper
from Marvell.CommunicationService.CommunicationWrapper import *

logger = CommWrapper_logger


class PySerialComWrapper(PyBaseComWrapper):
    
    def __init__(self, connectionData, connAlias="", shellPrompt=None, userPrompt=None, passPrompt=None):
        super(self.__class__, self).__init__(connAlias,connectionData, shellPrompt, userPrompt, passPrompt)

        self._port = int(float(connectionData.com_number.value))
        self._baudrate = connectionData.baudrate.value
        # self._timeout = connectionData.timeout
        # self._prompt = connectionData.prompt
        self._commType = ComTypes.PySerial

    def Connect(self):
        # type: () -> bool
        res = None
        self.LogToTestLogger("Connecting to COM"+str(self._port)+"...",force_format=True)
        self.connAlias = CommunicationManagement.Connect(self._commType, self._port)#, prompt=self._prompt)
        if self.connAlias is not None:
            res = True
            if self.login_after_connect:
                res = self.Login()
            if res:
                self.LogToTestLogger("Connection Successful",force_format=True)
        else:
            self.LogToTestLogger("Failed to Connect to COM" + str(self._port) + "...",force_format=True)
            res = False
        return res


# PySerialComWrapper = Log_all_class_methods(PySerialComWrapper, logger, show_func_parameters)