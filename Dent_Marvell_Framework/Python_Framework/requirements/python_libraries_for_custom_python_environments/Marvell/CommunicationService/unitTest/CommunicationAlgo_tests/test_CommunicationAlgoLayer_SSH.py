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
from builtins import range
import os, sys
# from Marvell.CommunicationService.Common.ImportExternal import *
# import_external('pytoolsinfra')
file_path = __file__
index = file_path.rfind("Python_Communication_Service") + "Python_Communication_Service".__len__() + 1
file_path = file_path[:index]

sys.path.insert(0, os.path.abspath(file_path))

import pytest
from ...PyCommunicationAlgoLayer.PyCommunicationAlgo import *
from ...PyBaseLayer.serialComm import *
from ...unitTest.UnitTest_config import *

logger = logging.getLogger()
logger.level = logging.INFO  # DEBUG / INFO
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)

SSHConAlgoChannel = None
setup_lua_sim_done = False


def InitSSHConnection():
    global SSHConAlgoChannel
    SSHConAlgoChannel = PyCommunicationAlgo(SERIAL_INIT_PROMPT)

    for i_try in range(3):
        logger.debug("Trying to establish a SSH connection, try: " + str(i_try))
        SSHConAlgoChannel.Connect(CommunicationType.PySSH,
                                  PORT_NUM_SSH,
                                  ipAddr=HOST_NAME_SSH,
                                  uname=UNAME_SSH,
                                  password=PASSWORD_SSH)
        if SSHConAlgoChannel.m_IsConnected:
            break

    if not SSHConAlgoChannel.m_IsConnected:
        raise Exception("Test ,Initialize a SSH connection failed")

    # Init the appDemoSim on the linux machine
    expected_prompt = SERIAL_INIT_PROMPT
    try:
        SSHConAlgoChannel.SendTerminalString(SIMULATION_DIR, waitForPrompt=False)
        SSHConAlgoChannel.SendTerminalString(SIMULATION_EXECUTION, waitForPrompt=False)
        sleep(30)
        SSHConAlgoChannel.SetShellPrompt(SERIAL_INIT_PROMPT)
        expected_prompt = SERIAL_INIT_PROMPT
        SSHConAlgoChannel.SendCommandAndGetBufferTillPrompt(NEW_LINE_CHAR, timeOutSeconds=5)
        SSHConAlgoChannel.SetShellPrompt(CONSOLE_PROMPT)
        expected_prompt = CONSOLE_PROMPT
        SSHConAlgoChannel.SendCommandAndGetBufferTillPrompt(LUA_CLI, timeOutSeconds=25.0)
        SSHConAlgoChannel.SendCommandAndGetBufferTillPrompt(NEW_LINE_CHAR)
    except Exception as e:
        raise Exception(str(e) + "\n Expected Prompt is: " + expected_prompt + "\n Actual Prompt is: " + SSHConAlgoChannel.m_prompt)

def ResetBoardToConsolePrompt(connChannel):
    timeout = 10
    start_time = time()
    while True:
        connChannel.SendTerminalString("end\n",False)
        connChannel.SendTerminalString("\n",False)
        output = connChannel.GetBuffer(timeOutSeconds=3)
        if output.endswith(b"Console# "):
            break
        if (time() - start_time) >= timeout:
            raise PythonComException("cannt exit board to Console#\n"+
                                     "current buffer :" + output)

@pytest.fixture(scope="session", autouse=True)
def setUpClass():
    global SSHConAlgoChannel

    print("++++++++++++++++++++++++++++ setup ++++++++++++++++++++++++++++++++")

    try:
        TerminateSimulation()
        InitSSHConnection()
    except Exception as e:
        raise Exception("Unit test setup failed because:\n" + str(e))

    print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n\n\n")

    yield
    tearDownClass()


def tearDownClass():
    global SSHConAlgoChannel
    logging.debug("++++++++++++++++++++ tearDown +++++++++++++++++++++++++++")

    SSHConAlgoChannel.Disconnect()
    assert SSHConAlgoChannel.m_IsConnected is False

    logging.debug("SSHConAlgoChannel Disconnected")

    logging.debug("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++")


@pytest.fixture(scope="function", autouse=True)
def setUp():
    global SSHConAlgoChannel

    logging.debug("======================= Test Case =============================\n")
    # logging.debug("Test Case : " + _testMethodName)

    ResetBoardToConsolePrompt(SSHConAlgoChannel)
    yield
    tearDown()


def tearDown():
    logging.debug("===============================================================\n\n\n")


def test_send_command_and_get_buffer_with_short_timeout():
    global SSHConAlgoChannel
    ConChannel = SSHConAlgoChannel

    assert ConChannel.m_IsConnected is True

    ConChannel.SetShellPrompt(CONSOLE_PROMPT)
    start = time()
    output = ConChannel.SendCommandAndGetBufferTillPrompt(NEW_LINE_CHAR, 0.5)
    end = time()
    logging.debug(end - start)
    assert 0 <= (end - start < 1)
    assert output.endswith(CONSOLE_PROMPT) is True


def test_send_command_and_get_buffer_with_long_timeout():
    global SSHConAlgoChannel
    ConChannel = SSHConAlgoChannel

    assert ConChannel.m_IsConnected is True
    ConChannel.SetShellPrompt(CONSOLE_PROMPT)
    start = time()
    output = ConChannel.SendCommandAndGetBufferTillPrompt(NEW_LINE_CHAR, 10)
    end = time()
    assert output.endswith(CONSOLE_PROMPT)
    assert end - start <= 10


def test_get_buffer_long_timeout():
    global SSHConAlgoChannel
    ConChannel = SSHConAlgoChannel

    assert ConChannel.m_IsConnected is True
    ConChannel.SendTerminalString(NEW_LINE_CHAR, False)

    GetBufferOut = ConChannel.GetBuffer(10)
    GetBufferTillPromptOut = ConChannel.SendCommandAndGetBufferTillPrompt(NEW_LINE_CHAR)
    assert GetBufferOut.endswith(CONSOLE_PROMPT) and GetBufferTillPromptOut.endswith(CONSOLE_PROMPT)


def test_set_shell_prompt():
    global SSHConAlgoChannel
    ConChannel = SSHConAlgoChannel

    assert ConChannel.m_IsConnected is True
    initial_prompt = ConChannel.m_prompt
    out = ConChannel.SendCommandAndGetBufferTillPrompt(NEW_LINE_CHAR)
    ConChannel.SetShellPrompt("blalsdkjflksjlkasjlawj")
    try:
        out = ConChannel.SendCommandAndGetBufferTillPrompt(NEW_LINE_CHAR)
        assert ConChannel.m_prompt != initial_prompt
    except Exception:
        assert True



def test_send_new_line_and_GetBuffer_with_short_time():
    """
    Test CommSerial.Read ( serialWin32.read(size) case )
    :return:
    """
    global SSHConAlgoChannel
    ConChannel = SSHConAlgoChannel

    for i in range(3):
        ress = ConChannel.SendTerminalString('\n', waitForPrompt=False)
        output = ConChannel.GetBuffer(timeOutSeconds=2)
        assert output.endswith(CONSOLE_PROMPT)


def test_send_and_read_untill_sub_prompt():
    """
    Test CommSerial.Read ( serialWin32.read(size) case )
    :return:
    """
    global SSHConAlgoChannel
    ConChannel = SSHConAlgoChannel

    del_char = 2 if len(CONSOLE_PROMPT) > 2 else 0
    sub_prompt = CONSOLE_PROMPT[:-del_char]

    ConChannel.SetShellPrompt(prompt=sub_prompt)
    ConChannel.SendTerminalString(NEW_LINE_CHAR, False)
    output = ConChannel.GetBufferTillPrompt()
    assert output.endswith(sub_prompt)

    output = ConChannel.GetBuffer(timeOutSeconds=2)
    left_prompt = CONSOLE_PROMPT[len(CONSOLE_PROMPT) - del_char:]

    assert output.startswith(left_prompt)


def test_resend_and_read_untill_sub_prompt():
    """
    Test CommSerial.Read ( serialWin32.read(size) case )
    :return:
    """
    global SSHConAlgoChannel
    ConChannel = SSHConAlgoChannel

    del_char = 2 if len(CONSOLE_PROMPT) > 2 else 0
    sub_prompt = CONSOLE_PROMPT[:-del_char]

    ConChannel.SetShellPrompt(prompt=sub_prompt)
    ConChannel.SendTerminalString(NEW_LINE_CHAR, True)
    ConChannel.SendTerminalString(NEW_LINE_CHAR, False)

    output = ConChannel.GetBuffer(timeOutSeconds=2)

    left_prompt = CONSOLE_PROMPT[len(CONSOLE_PROMPT) - del_char:]
    assert output.startswith(left_prompt)
    assert output.endswith(CONSOLE_PROMPT)


def test_send_and_read_untill_sub_prompt_with_actual_size():
    """
    Test CommSerial.Read ( serialWin32.read(size) case )
    :return:
    """
    global SSHConAlgoChannel
    ConChannel = SSHConAlgoChannel

    del_char = 2 if len(CONSOLE_PROMPT) > 2 else 0
    sub_prompt = CONSOLE_PROMPT[:-del_char]

    ConChannel.SetShellPrompt(prompt=sub_prompt)
    ConChannel.SendTerminalString(NEW_LINE_CHAR, False)
    output = ConChannel.GetBufferTillPrompt()
    assert output.endswith(sub_prompt)

    output = ConChannel.GetBuffer(timeOutSeconds=2, max_bytes=del_char)
    assert len(output) == del_char


def test_send_and_read_untill_sub_prompt_with_less_size():
    """
    Test CommSerial.Read ( serialWin32.read(size) case )
    :return:
    """
    global SSHConAlgoChannel
    ConChannel = SSHConAlgoChannel

    del_char = 2 if len(CONSOLE_PROMPT) > 2 else 0
    sub_prompt = CONSOLE_PROMPT[:-del_char]

    ConChannel.SetShellPrompt(prompt=sub_prompt)
    ConChannel.SendTerminalString(NEW_LINE_CHAR, False)
    output = ConChannel.GetBufferTillPrompt()
    assert output.endswith(sub_prompt)

    output = ConChannel.GetBuffer(timeOutSeconds=2, max_bytes=del_char - 1)
    assert len(output) == del_char - 1

    output = ConChannel.GetBuffer(timeOutSeconds=0)
    assert len(output) == 1


def test_resend_and_read_untill_size_less_than_buffer_content():
    global SSHConAlgoChannel
    ConChannel = SSHConAlgoChannel

    ConChannel.SetShellPrompt(prompt=CONSOLE_PROMPT)
    ConChannel.SendTerminalString(NEW_LINE_CHAR, True)
    ConChannel.SendTerminalString(NEW_LINE_CHAR, False)

    output = ConChannel.GetBuffer(timeOutSeconds=2, max_bytes=4)
    assert len(output) == 4


def test_SendCommandAndGetBufferTillPromptDic_read_untill_included_prompt():
    global SSHConAlgoChannel
    ConChannel = SSHConAlgoChannel

    paterns = {"p1": b"Console# ", "p2": b"->"}
    output = ConChannel.SendCommandAndGetBufferTillPromptDic(command=NEW_LINE_CHAR, dicPattern=paterns, timeOutSeconds=10)
    logging.debug(output)

    regexp = re.compile(b'\s*Console#\s*')

    assert regexp.search(output)


def test_SendCommandAndGetBufferTillPromptDic_read_untill_no_prompt():
    global SSHConAlgoChannel
    ConChannel = SSHConAlgoChannel

    paterns = {"p1": b"prompt", "p2": b"->"}
    output = ""
    try:
        output = ConChannel.SendCommandAndGetBufferTillPromptDic(command=NEW_LINE_CHAR, dicPattern=paterns, timeOutSeconds=10)
        logging.debug(output)
        assert False
    except PythonComException as e:
        logging.debug(output)

        assert True


def test_SendCommandAndGetBufferTillPromptDic_read_untill_more_one_prompt():
    global SSHConAlgoChannel
    ConChannel = SSHConAlgoChannel

    paterns = {"p1": b"lua>", "p2": b"Console# "}
    output = ConChannel.SendCommandAndGetBufferTillPromptDic(command=NEW_LINE_CHAR, dicPattern=paterns, timeOutSeconds=10)
    logging.debug(output)
    assert output.endswith(b"Console# ")


    output = ConChannel.SendCommandAndGetBufferTillPromptDic(command="lua\n", dicPattern=paterns,timeOutSeconds=10)
    logging.debug(output)
    assert output.endswith(b"lua>")


    output = ConChannel.SendCommandAndGetBufferTillPromptDic(command=".\n", dicPattern=paterns,timeOutSeconds=10)
    logging.debug(output)
    assert output.endswith(b"Console# ")


    output = ConChannel.SendCommandAndGetBufferTillPromptDic(command=NEW_LINE_CHAR, dicPattern=paterns, timeOutSeconds=10)
    logging.debug(output)
    assert output.endswith(b"Console# ")


def test_SendCommandAndGetBufferTillPromptDic_read_untill_prompts_scenario():
    global SSHConAlgoChannel
    ConChannel = SSHConAlgoChannel

    paterns = {"p1": b"Console# ", "p2": b"Console\(config\)# "}
    output = ConChannel.SendCommandAndGetBufferTillPromptDic(command=NEW_LINE_CHAR, dicPattern=paterns, timeOutSeconds=10)
    logging.debug(output)
    assert output.endswith(b"Console# ")


    output = ConChannel.GetBuffer(timeOutSeconds=0)
    output = ConChannel.SendCommandAndGetBufferTillPromptDic(command=CONFIGURE, dicPattern=paterns, timeOutSeconds=10)
    logging.debug(output)
    assert output.endswith(b"Console(config)# ")

    output = ConChannel.SendCommandAndGetBufferTillPromptDic(command=END, dicPattern=paterns, timeOutSeconds=10)
    logging.debug(output)
    assert output.endswith(b"Console# ")


def test_SendCommandAndGetBufferTillPromptDic_read_untill_regix_scenario():
    global SSHConAlgoChannel
    ConChannel = SSHConAlgoChannel

    paterns = {"p1": b"Console[\(\)\w]*#\s*"}
    regexp = re.compile(b'Console[\(\)\w]*#\s*')

    output = ConChannel.SendCommandAndGetBufferTillPromptDic(command=NEW_LINE_CHAR, dicPattern=paterns,
                                                             timeOutSeconds=10)
    logging.debug(output)
    assert regexp.search(output)

    output = ConChannel.GetBuffer(timeOutSeconds=0)
    output = ConChannel.SendCommandAndGetBufferTillPromptDic(command=CONFIGURE, dicPattern=paterns,
                                                             timeOutSeconds=10)
    logging.debug(output)
    assert regexp.search(output)

    output = ConChannel.SendCommandAndGetBufferTillPromptDic(command=END, dicPattern=paterns,
                                                             timeOutSeconds=10)
    logging.debug(output)
    assert regexp.search(output)


def test_SendCommandAndGetBufferTillPromptDic_read_with_timeout():
    global SSHConAlgoChannel
    ConChannel = SSHConAlgoChannel

    paterns = {"p1": b"Console[\(\)\w]*#\s*"}
    regexp = re.compile(b'Console[\(\)\w]*#\s*')
    command = 'cpssinitsystem 29,1\n'

    start_time = time()
    output = ConChannel.SendCommandAndGetBufferTillPromptDic(command=command, dicPattern=paterns,
                                                             timeOutSeconds=10)
    exe_time = time() - start_time

    logging.debug(exe_time)
    logging.debug(output)

    assert exe_time <= 5
    assert regexp.search(output)


def test_SendCommandAndGetBufferTillPromptDic_cant_read_and_wait_for_timeout():
    global SSHConAlgoChannel
    ConChannel = SSHConAlgoChannel

    output = ""
    paterns = {"p1": b"Console[\(\)\w]*#\s*"}
    regexp = re.compile(b'Console[\(\)\w]*#\s*')
    command = 'cpssinitsystem 29,1' #without enter
    start_time = time()
    try:
        output = ConChannel.SendCommandAndGetBufferTillPromptDic(command=command, dicPattern=paterns,
                                                                        timeOutSeconds=3)
        assert False
    except PythonComException as e:
        exe_time = time() - start_time

        logging.debug(exe_time)
        logging.debug(output)
        logging.debug(str(e))

        assert exe_time >= 3