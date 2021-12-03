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

from ...unitTest.UnitTest_config import *

from ...PyCommunicationAlgoLayer.PyCommunicationAlgo import PyCommunicationAlgo, \
    CommunicationType

SerialConAlgoChannel = None
TelnetConAlgoChannel = None
setup_lua_sim_done = False

def InitSerialConnection():
    global SerialConAlgoChannel
    SerialConAlgoChannel = PyCommunicationAlgo(CONSOLE_PROMPT)
    SerialConAlgoChannel.Connect(CommunicationType.PySerial, COM_PORT, ipAddr=IP_ADDR, uname=UNAME, password=PASSWORD)
    if not SerialConAlgoChannel.m_IsConnected:
        raise Exception("Test , serial connection failed")

def InitTelnetConnection():
    global TelnetConAlgoChannel
    TelnetConAlgoChannel = PyCommunicationAlgo(CONSOLE_PROMPT)
    TelnetConAlgoChannel.Connect(CommunicationType.PyTelnet, PORT_NUM, ipAddr=IP_ADDR, uname=UNAME, password=PASSWORD)
    if not TelnetConAlgoChannel.m_IsConnected:
        raise Exception("Test , telnet connection failed")

try:
    # InitSerialConnection()
    InitTelnetConnection()
except Exception as e:
    # logging.debug(e.message)
    assert False


def resend_and_read_untill_sub_prompt(ConChannel=TelnetConAlgoChannel):
    """
    Test CommSerial.Read ( serialWin32.read(size) case )
    :return:
    """
    del_char = 4
    sub_prompt = CONSOLE_PROMPT[:-del_char]

    newlineChar = "\n"
    ConChannel.SetShellPrompt(prompt=CONSOLE_PROMPT)
    ConChannel.SendTerminalString(newlineChar, True)
    ConChannel.SendTerminalString(newlineChar, False)

    output = ConChannel.GetBuffer(timeOutSeconds=2, max_bytes=4)
    if len(output) != 4:
        raise Exception()
    # left_prompt = PROMPT[len(PROMPT) - del_char:]
    # assert output.startswith(left_prompt)
    # assert output.endswith(PROMPT)

resend_and_read_untill_sub_prompt()