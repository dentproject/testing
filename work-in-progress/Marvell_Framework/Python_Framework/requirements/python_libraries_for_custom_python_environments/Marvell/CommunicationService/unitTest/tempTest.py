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

import sys
from DemoKeywords import *
#from LUACommunication import *
from Common.Types import *
from HighCommunicationLayer.CommunicationManagement import *
import time

import sys
sys.path.append(r'C:\Python27\Lib')
def main():
    try:
        #DemoKeywords.initialize_system()
        num = 100
        types = [CommunicationType.PySerial, CommunicationType.PyTelnet,
                 CommunicationType.CoSSerial, CommunicationType.CoSTelnet]
        i = 3
        prompt = "->"
        portId = 23

        pattern = {"pattern1": "Marvell[\s\w]+:"}

        conn1 = CommunicationManagement.Connect(CommunicationType.PyTelnet, portId,
                                                ipAddr='10.4.48.2', prompt=prompt)
        #
        # conn2 = CommunicationManagement.Connect(CommunicationType.PyTelnet, portId,
        #                                         ipAddr='10.4.48.2', prompt=prompt)
        CommunicationManagement.addToConnectionChannelDict("noAlias",None)
        CommunicationManagement()._private()
        print(CommunicationManagement.GetConnectedChannels())
        # CommunicationManagement.Disconnect(conn1)
        # CommunicationManagement.Disconnect(conn1)

        #conn2 = CommunicationManagement.Connect(CommunicationType.CoSSerial, 9)

        CommunicationManagement.SetShellPrompt(conn1, "/ #")
        #CommunicationManagement.SetShellPrompt(conn2, "Marvell>>")

        print(CommunicationManagement.GetBufferTillPrompt(conn1, 10))#TODO:GetBufferTillPrompt dont work with comservice, raise an exception
        print(CommunicationManagement.SendCommandAndGetBufferTillPrompt(conn1, "", 10))
        #print CommunicationManagement.SendCommandAndGetBufferTillPrompt(conn2, "", 10)
        #print CommunicationManagement.GetBufferTillPrompt(conn2, 10)

        # isMatched, pattern, match = CommunicationManagement.SendCommandAndGetBufferTillPromptDic(conn1, "", pattern,10)
        # print match.string
        # print match.group(0)


        CommunicationManagement.SetShellPrompt(conn1, "->")

        print(CommunicationManagement.SendCommandAndGetBufferTillPrompt(conn1, "appDemo -tty" + "\n", 10))
        #print CommunicationManagement.SendCommandAndGetBufferTillPrompt(conn2, "reset\n", 10)
        # CommunicationManagement.SendTerminalString(conn2, "reset\n", False)
        # print CommunicationManagement.GetBufferTillPrompt(conn2, 2)

        CommunicationManagement.SetShellPrompt(conn1,"\nConsole#")

        print(CommunicationManagement.SendCommandAndGetBufferTillPrompt(conn1,"luaCLI\n", 10))

        print(CommunicationManagement.SendCommandAndGetBufferTillPrompt(conn1,"cpssInitSystem 29,1" + "\n", 10))

    except Exception as e:
        print(str(e))
if __name__ == "__main__":
    sys.exit(int(main() or 0))
