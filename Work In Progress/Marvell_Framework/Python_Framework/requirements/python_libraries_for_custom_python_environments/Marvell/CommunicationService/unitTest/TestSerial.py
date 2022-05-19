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

from ..HighCommunicationLayer.CommunicationManagement import \
    CommunicationManagement as cm


def initialize(connAlias, runAppDemo, initSys):
    # CommunicationManagement.SetShellPrompt(connAlias, "/ #")
    # print CommunicationManagement.GetBufferTillPrompt(connAlias, 10)
    # CommunicationManagement.SetShellPrompt(connAlias, "\n->")
    # print CommunicationManagement.SendCommandAndGetBufferTillPrompt(connAlias, str(runAppDemo) + "\n", 10)
    cm.SetShellPrompt(connAlias, "\nConsole#")
    cm.SendTerminalString(connAlias, "\r", 10)
    print (cm.GetBuffer(connAlias, 20))
    print (cm.SendCommandAndGetBufferTillPrompt(connAlias, "luaCLI\r", 10))
    print (cm.SendCommandAndGetBufferTillPrompt(connAlias, str(initSys) + "\r", 10))


def test_send_get_loop():
    conn = cm.Connect(CommunicationType.PySerial, 6)
    # initialize(conn, "appDemo -tty", "cpssInitSystem 29,1")
    cm.SetShellPrompt(conn, "Console#")

    for i in range(1, 100):
        print ('................................itt #{}................................'.format(i))
        print (cm.SendCommandAndGetBufferTillPrompt(conn, "show interfaces status all\r"))
        # cm.SendTerminalString(conn,"show interfaces status all\r", False)
        # buffer = cm.GetBufferTillPrompt(conn, 20)
        print (buffer)


def main():
    test_send_get_loop()


if __name__ == "__main__":
    main()
