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
from builtins import str
import sys

from ..HighCommunicationLayer.ABCCommunicationAlgo import *
from ..CommunicationExceptions.Exceptions import *
import re
from ..libraries.PythonWrapper import *
from ..Common.Types import *

# === ComService Communication Algo impl ===

class CoSCommunicationAlgo(ABCCommunicationAlgo):
    """inherent ABCCommunicationAlgo ,  implement algorithms API
    based on Comservices implementation
    """
    m_channel = None
    def __init__(self):
        pass

    def Connect(self,channeltype, portId, baudRate = 115200, parity = "N", dataBits=8, stopBits=1,
                 ipAddr=None, uname=None, password=None):

        try:
            #CommonManagement.Connect(portId)
            if channeltype == CommunicationType.CoSSerial:
                self.m_channel = CommonManagement()
                self.m_channel.Connect(portId)
                return "COM" + str(portId)

            elif channeltype == CommunicationType.CoSTelnet:
                r_ipAddr = IPv4Address(str(ipAddr))
                if uname == None :
                    uname = ""
                if password == None:
                    password = ""

                CommonManagement.Connect(r_ipAddr, portId, uname, password, 0)
                return ipAddr + ":" + str(portId)
        except:
            print("Connecttion Failed " + "'Connect' : exception from CommServices code.\n")
            return None

    def Disconnect(self):
        try:
            pId = self.m_port
            self.CommonManagement.Disconnect(pId)
        except:
            err = "'Disconnect' : exception from CommServices code.\n"
            raise CoSException(err)


    def SendTerminalString(self, command, waitForPrompt=True):
        try:
            CommonManagement.SendTerminalString(command, waitForPrompt)
        except:
            err = "'SendTerminalString' : exception from CommServices code.\n"
            raise CoSException(err)


    def SendCommandAndGetBufferTillPrompt(self, command, timeOutSeconds = 10):
        try:
            return CommonManagement.SendCommandAndGetBuffer(command, timeOutSeconds)
        except:
            err = "'SendCommandAndGetBufferTillPrompt' : exception from CommServices code.\n"
            raise CoSException(err)


    def GetBuffer(self, timeOutSeconds):
        try:
            milisec = timeOutSeconds * 1000
            return CommonManagement.GetSerialBuffer(milisec)
        except:
            err = "'GetBuffer' : exception from CommServices code.\n"
            raise CoSException(err)


    def GetBufferTillPrompt(self, timeOutSeconds = 10):
        try:
            return CommonManagement.GetSerialBufferTillPrompt(timeOutSeconds)
        except:
            err = "'GetBufferTillPrompt' : exception from CommServices code.\n"
            raise CoSException(err)

    # def GetBufferTillIdle(self, idleTimeMili=250,  timeOutSec=5):
    #     try:
    #         return CommonManagement.GetSerialBufferTillIdle(idleTimeMili,  timeOutSec)
    #     except:
    #         err = "'Connect' : exception from CommServices code.\n"
    #         raise CoSException(err)

    def SendCommandAndGetBufferTillPromptDic(self, command, dicPattern, timeOutSeconds=10):

        CommonManagement.SendTerminalString(command, False)
        output = CommonManagement.GetBufferTillPrompt(timeOutSeconds)
        try:
            for key, pattern in dicPattern.items():
                match = re.search(pattern, output, re.MULTILINE)
                if match:
                    return True, key, match

            return False, ""
        except Exception as e:
            err = "'SendCommandAndGetBufferTillPromptDic' Failed ! " + e.message
            raise PythonComException(err)

    def SetShellPrompt(self, prompt):
        try:
            CommonManagement.SetShellPrompt(prompt)
        except:
            err = "'SetShellPrompt' : exception from CommServices code.\n"
            raise CoSException(err)
