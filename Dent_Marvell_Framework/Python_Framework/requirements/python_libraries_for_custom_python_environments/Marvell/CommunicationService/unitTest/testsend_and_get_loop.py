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
from builtins import range
from ..HighCommunicationLayer.CommunicationManagement import *

from ..HighCommunicationLayer.CommunicationManagement import CommunicationManagement as cm


def initialize(connAlias, runAppDemo, initSys):
    cm.SetShellPrompt(connAlias, "/ #")
    print(cm.GetBuffer(connAlias, 1))
    cm.SetShellPrompt(connAlias, "\n->")
    print(cm.SendCommandAndGetBufferTillPrompt(connAlias, runAppDemo, 20))
    cm.SetShellPrompt(connAlias, "\nConsole#")
    cm.SendTerminalString(connAlias, "\r", 20)
    print(cm.GetBuffer(connAlias,20))
    print(cm.SendCommandAndGetBufferTillPrompt(connAlias, "luaCLI\r", 10))
    print(cm.SendCommandAndGetBufferTillPrompt(connAlias, initSys, 10))

def test_send_get_loop():
    conn = cm.Connect(CommunicationType.PySerial, 6)
    #initialize(conn, "appDemo -tty\r", "cpssInitSystem 29,1\r")
    cm.SetShellPrompt(conn, "Console#")
    #cm.SetShellPrompt(conn, ">")

    print(cm.SendCommandAndGetBufferTillPrompt(conn, "cpssInitSystem 29,1\r", 10))
    option = 1
    command = "show interfaces status all"
    command = "show interfaces ?"
    buff = "show interfaces status all"

    for i in range(0, 3):
        print('................................ itt #{} ................................'.format(i))

        if option == 0:
            buff = cm.SendCommandAndGetBufferTillPrompt(conn,command)
        elif option == 1:
            cm.SendTerminalString(conn, command, False)
            #buff = cm.GetBufferTillPrompt(conn, 20)
        elif option == 2:
            cm.SendTerminalString(conn, command, False)
            buff = ''
            while True:
                ret = cm.GetBuffer(conn, 0)
                buff += ret
                if buff.endswith("Console# "):
                    break
        elif option == 3:
            cm.SendTerminalString(conn, command, False)
            buff = ''
            while True:
                ret = cm.GetBuffer(conn, timeOutSeconds=None)
                buff += ret
                if buff.endswith("Console# "):
                    break

        elif option == 4: # with sleep - work
            cm.SendTerminalString(conn, command, False)
            sleep(0.01)
            buff = cm.GetBufferTillPrompt(conn, 20)

        check1 = buff.startswith("show interfaces status all")
        check2 = buff.startswith(" show interfaces status all")

        if not check1 and not check2:
            raise Exception("wrong in itt #" + str(i) + "\n Buffer :\n" + buff)

    buff = cm.SendCommandAndGetBufferTillPrompt(conn,"\r")

    print(buff)

def main():
    try:
        test_send_get_loop()
        print("\nDone!")
    except Exception as e:
        print("\n\nException : " + e.message)



if __name__ == "__main__":
    main()
