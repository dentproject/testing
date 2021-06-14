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

from builtins import object
from abc import ABCMeta, abstractmethod
from future.utils import with_metaclass

# === Algorithm Communication Layer ===


"""
This is an abstract class that define all the algorithm functions for our GCS application-
    Algorithm Layer API

each algorithm implemented as a several basic commands , including commands from Basic Layer.

this class is a base class for serial and telnet clasees:
<a href=""></a>
1. **CosCommunicationAlgo** - CommService communication , see <a href="../CoSCommunicationAlgoLayer/CoSCommunicationAlgo.html"> Here</a>
    - based in CommService base implementations
2. **PyCommunicationAlgo** - python communication , see <a href="../PyCommunicationAlgoLayer/PyCommunicationAlgo.html"> Here</a>
    - based in Base Communication Layer

None : for future algorithm communication type ,just implement this API .

"""

class ABCCommunicationAlgo(with_metaclass(ABCMeta, object)):
    def __init__(self):
        raise NotImplementedError('ERROR: Cant instantiate abstract class')

    @abstractmethod
    def Connect(self,channeltype, portId, baudRate = 115200, parity = "N", dataBits=8, stopBits=1,
                 ipAddr=None, uname=None, password=None):
        """connection Algorithm"""
        pass


    @abstractmethod
    def Disconnect(self):
        """disconnect Algorithm"""
        pass



    @abstractmethod
    def SendTerminalString(self, command, waitForPrompt=True):
        """send a given command to the device buffer"""
        pass


    @abstractmethod
    def SetShellPrompt(self, data):
        """update the shell prompt """
        pass

    @abstractmethod
    def SendCommandAndGetBufferTillPrompt(self, commandbuffer,timeOutSeconds=10):
        """send a given command and return the buffer"""
        pass


    @abstractmethod
    def GetBuffer(self, timeOutSeconds, max_bytes=4096):
        """read buffer """
        pass
    @abstractmethod
    def SendCommandAndGetBufferTillPromptDic(self, command, dicPattern, timeOutSeconds=10):
        """ send a given command , filter the result by dictionary of regex prompt ,
        return : isFound suitable regex pattern , key of matched pattern and re.match object
        ( note : see python regex match object)
        """
        pass

    @abstractmethod
    def GetBufferTillPrompt(self, timeOutSeconds, shellPrompt):
        """read buffer until prompt """
        pass

    @abstractmethod
    def SetCommunicationLogger(self, comm_logger):
        """ Sets the logger for communication if the user wants to print all messages to a file """
        pass
