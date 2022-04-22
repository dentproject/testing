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
import os, sys ,logging
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
"""
to run from cmd :
> python -m unittest discover -p "*.py" > results.txt 2>&1
"""

# import logging
# logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger()
logger.level = logging.INFO  # DEBUG / INFO
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)

SSHComm = None
setup_lua_sim_done = False


def InitSSHConnection():
    global SSHComm
    SSHComm = sshComm(host=HOST_NAME_SSH, port=PORT_NUM_SSH, username=UNAME_SSH, password=PASSWORD_SSH)

    for i_try in range(3):
        logger.debug("Trying to establish a SSH connection, try: " + str(i_try))
        SSHComm.Connect()
        if SSHComm.is_connected:
            break

    if not SSHComm.is_connected:
        raise Exception("Test ,Initialize a SSH connection failed")

    # Init the appDemoSim on the linux machine
    expected_prompt = SERIAL_INIT_PROMPT
    try:
        SSHComm.Write(SIMULATION_DIR)
        SSHComm.Write(SIMULATION_EXECUTION)
        sleep(30)
        SSHComm.Write(NEW_LINE_CHAR)
        SSHComm.Read(prompt=SERIAL_INIT_PROMPT, timeout=10.0)
        SSHComm.Write(LUA_CLI)  # init LUA CLI, expect to console prompt
        expected_prompt = CONSOLE_PROMPT
        ssh_buffer = SSHComm.Read(prompt=CONSOLE_PROMPT, timeout=30.0)
        assert ssh_buffer.endswith(CONSOLE_PROMPT)
        SSHComm.Write(NEW_LINE_CHAR)
        expected_prompt = CONSOLE_PROMPT
        ssh_buffer = SSHComm.Read(prompt=CONSOLE_PROMPT, timeout=2)
        assert ssh_buffer.endswith(CONSOLE_PROMPT)
    except Exception as e:
        raise Exception(e.message + "\n Expected Prompt is: " + expected_prompt)

def ResetBoardToConsolePrompt(connChannel):
    timeout = 10
    start_time = time()
    while True:
        connChannel.Write(END)
        connChannel.Write(NEW_LINE_CHAR)
        output = connChannel.Read(timeout=3)
        if output.endswith(CONSOLE_PROMPT):
            break
        if (time() - start_time) >= timeout:
            raise PythonComException("cannot exit board to Console#\n" +
                                     "current buffer:" + output)


@pytest.fixture(scope="session", autouse=True)
def setUpClass():
    global SSHComm

    logging.debug("+++++++++++++++++++++ setup +++++++++++++++++++++++++++++")

    try:
        TerminateSimulation()
        InitSSHConnection()
    except Exception as e:
        raise Exception("Unit test setup failed because:\n" + e.message)

    logging.debug("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n\n\n")

    yield
    tearDownClass()


def tearDownClass():
    global SSHComm
    logging.debug("++++++++++++++++++++ tearDown +++++++++++++++++++++++++++")

    SSHComm.Disconnect()
    assert SSHComm.is_connected is False

    logging.debug("SSHComm Disconnected")

    logging.debug("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++")


@pytest.fixture(scope="function", autouse=True)
def setUp():
    global SSHComm

    logging.debug("======================= Test Case =============================\n")
    ResetBoardToConsolePrompt(SSHComm)

    yield

    tearDown()


def tearDown():
    logging.debug("===============================================================\n\n\n")


def test_init_sshcomm_with_default_params():
    ssh_test_instance = sshComm()

    assert ssh_test_instance._ssh_channel._host is None
    assert ssh_test_instance._ssh_channel._password is None
    assert ssh_test_instance._ssh_channel._username is None
    assert ssh_test_instance._ssh_channel._port == PORT_NUM_SSH
    assert ssh_test_instance._ssh_channel._timeout == 10
    assert ssh_test_instance.is_connected is False


def test_local_defined_params_while_init_sshcomm():
    ssh_test_instance = sshComm(HOST_NAME_SSH, PORT_NUM_SSH, UNAME_SSH, PASSWORD_SSH)

    assert ssh_test_instance._ssh_channel._host == convert2bytes(HOST_NAME_SSH)
    assert ssh_test_instance._ssh_channel._password == convert2bytes(PASSWORD_SSH)
    assert ssh_test_instance._ssh_channel._username == convert2bytes(UNAME_SSH)
    assert ssh_test_instance._ssh_channel._port == convert2bytes(PORT_NUM_SSH)
    assert ssh_test_instance._ssh_channel._timeout == 10
    assert ssh_test_instance.is_connected is False

def convert2bytes(instr):
    if isinstance(instr, str):
        instr = instr.encode('utf-8')

    return instr

def test_ssh_connect_when_already_connected():
    global SSHComm

    assert SSHComm.is_connected is True
    SSHComm.is_connected = False

    try:
        InitSSHConnection()
    except BaseCommException:
        assert False

    assert SSHComm.is_connected is True


def test_read_without_prompt_with_timeout():
    global SSHComm
    ConChannel = SSHComm

    assert ConChannel.is_connected is True
    ConChannel.Write(NEW_LINE_CHAR)

    start_time = time()
    output = ConChannel.Read(timeout=5)
    end_time = time()
    logging.debug(end_time - start_time)
    assert (end_time - start_time) >= 4.9 and (end_time - start_time) < 6


def test_write_command_and_read_buffer():
    global SSHComm
    ConChannel = SSHComm

    dummy_command = "command\n"

    assert ConChannel.is_connected is True
    bytes_written = ConChannel.Write(dummy_command)

    assert len(dummy_command) == bytes_written
    output = ConChannel.Read(timeout=3)
    logging.debug(output)
    assert output != ''


def test_read_with_prompt_without_timeout():
    global SSHComm
    ConChannel = SSHComm

    assert ConChannel.is_connected is True
    ConChannel.Write(NEW_LINE_CHAR)

    output = ConChannel.Read(prompt=CONSOLE_PROMPT)
    logging.debug(output)

    assert output.endswith(CONSOLE_PROMPT)


def test_read_with_prompt_with_long_timeout():
    global SSHComm
    ConChannel = SSHComm

    assert ConChannel.is_connected is True
    ConChannel.Write(NEW_LINE_CHAR)

    start_time = time()
    output = ConChannel.Read(prompt=CONSOLE_PROMPT, timeout=7)
    end_time = time()
    assert (end_time - start_time) <= 7
    assert output.endswith(CONSOLE_PROMPT)


def test_read_with_prompt_with_short_timeout():
    global SSHComm
    ConChannel = SSHComm

    assert ConChannel.is_connected is True
    ConChannel.Write(NEW_LINE_CHAR)

    start_time = time()
    output = ConChannel.Read(prompt=CONSOLE_PROMPT, timeout=0)
    end_time = time()
    logging.debug(output)
    assert end_time - start_time < 0.5


def test_new_line_and_wait_for_short_time():
    global SSHComm
    ConChannel = SSHComm

    assert ConChannel.is_connected is True
    ConChannel.Write(NEW_LINE_CHAR)
    start_time = time()
    output = ConChannel.Read(timeout=3)
    end_time = time()
    logging.debug(output)
    logging.debug(end_time - start_time)

    assert 2.9 <= (end_time - start_time) < 4
    assert output.endswith(CONSOLE_PROMPT)


def test_read_without_prompt_without_timeout_None():
    global SSHComm
    ConChannel = SSHComm

    # read all
    assert ConChannel.is_connected is True
    ConChannel.Write(NEW_LINE_CHAR)

    start = time()
    output = ConChannel.Read(timeout=None)
    end = time()
    assert (end - start < 1)


def test_read_all_data_without_prompt_with_timeout_zero_with_loop():
    global SSHComm
    ConChannel = SSHComm

    """ test timeout zero"""
    output = b''

    assert ConChannel.is_connected is True
    ConChannel.Write(NEW_LINE_CHAR)

    loop_start_time = time()
    exe_loop_time = 0
    while True:
        start_time = time()
        output += ConChannel.Read(timeout=0)
        end_time = time()
        print(output)
        assert (end_time - start_time) <= 0.5
        if output.endswith(CONSOLE_PROMPT):
            break
        exe_loop_time = time() - loop_start_time
        if (exe_loop_time > 3):  # if long time and prompt not received
            assert False
    logging.debug(exe_loop_time)
    logging.debug(output)
    assert output.endswith(CONSOLE_PROMPT)


def test_read_all_data_without_prompt_with_timeout_zero_with_waiting():
    global SSHComm
    ConChannel = SSHComm

    """ test timeout zero"""

    assert ConChannel.is_connected is True
    ConChannel.Write(NEW_LINE_CHAR)

    sleep(2)
    start_time = time()
    output = ConChannel.Read(timeout=0)
    end_time = time()
    print(output)

    assert (end_time - start_time) <= 0.2
    logging.debug(output)
    assert output.find(CONSOLE_PROMPT) >= 0


def test_connect_disconnect_scenario():
    ssh_test_instance = sshComm(HOST_NAME_SSH, PORT_NUM_SSH, UNAME_SSH, PASSWORD_SSH)
    ssh_test_instance.Connect()
    assert ssh_test_instance.is_connected is True
    ssh_test_instance.Disconnect()
    assert ssh_test_instance.is_connected is False
