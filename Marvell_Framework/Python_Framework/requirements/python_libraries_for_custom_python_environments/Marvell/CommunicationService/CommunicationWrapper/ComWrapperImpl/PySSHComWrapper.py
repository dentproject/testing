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
from Marvell.CommunicationService.HighCommunicationLayer.CommunicationManagement import CommunicationManagement

from .PyComWrapper import PyBaseComWrapper
from Marvell.CommunicationService.Common.Types import CommunicationType as ComTypes
# from Marvell.pytoolsinfra.PythonLoggerInfra.CommonUtils.fileNameUtils import getCurrentFunctionName
from Marvell.CommunicationService.CommunicationWrapper import *

logger = CommWrapper_logger


class PySSHComWrapper(PyBaseComWrapper):

    def __init__(self, connectionData, connAlias="", shellPrompt=None, userPrompt=None, passPrompt=None):
        super(self.__class__, self).__init__(connAlias, connectionData,shellPrompt, userPrompt, passPrompt)

        self._initCommType()
        self._commAlgo = None
        self._port = 22
        self._host = connectionData.ip_address.value
        self._timeout = 0
        self._shell_width = 80
        self._shell_height = 24

        if hasattr(connectionData, "port"):
            self._port = connectionData.port.value
        if hasattr(connectionData, "timeout"):
            self._timeout = connectionData.timeout.value

    def _initCommType(self):
        self.commType = ComTypes.PySSH

    @property
    def shellWidth(self):
        return self._shell_width

    @shellWidth.setter
    def shellWidth(self, width):
        if width > 0:
            self._shell_width = width

    @property
    def shellHeight(self):
        return self._shell_height

    @shellHeight.setter
    def shellHeight(self, height):
        if height > 0:
            self._shell_height = height

    def Connect(self):
        # type: () -> bool

        self.LogToTestLogger("Connecting to "+str(self._host)+":"+str(self._userName)+":"+str(self._port)+" ...",force_format=True)

        self.connAlias = CommunicationManagement.Connect(self.commType, self._port, ipAddr=self._host,
                                                         uname=self._userName,  password=self._password,
                                                         width=self._shell_width, height=self._shell_height,
                                                         uid=self.generate_uid)
        if self.connAlias is not None:
            self.LogToTestLogger("Connection Successful",force_format=True)
            self._commAlgo = CommunicationManagement.activateConnectionChannel(self.connAlias)
            return True
        else:
            self.LogToTestLogger("Failed to Connect to Telnet: " + str(self._host) + "...",force_format=True)
            return False

    @property
    def SSHClient(self):
        if self._commAlgo:
            return self._commAlgo.m_channel._ssh_channel._client

        return None


# This line decorates all the functions in this class with the "LogWith" decorator
# PySSHComWrapper = Log_all_class_methods(PySSHComWrapper, logger, show_func_parameters)
