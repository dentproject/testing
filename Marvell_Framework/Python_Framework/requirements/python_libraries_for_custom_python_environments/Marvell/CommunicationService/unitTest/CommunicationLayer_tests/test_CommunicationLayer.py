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

import os, sys, logging

index = __file__.rfind("Python_Communication_Service") + "Python_Communication_Service".__len__() + 1
file_path = __file__[:index]
sys.path.insert(0, os.path.abspath(file_path))

import unittest
from ddt import ddt, data
from ...PyBaseLayer.serialComm import *
from ...PyBaseLayer.telnetComm import *
from ...unitTest.UnitTest_config import *

logger = logging.getLogger()
logger.level = logging.DEBUG  # DEBUG / INFO
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)


SerialCon = serialComm(PORT_ID)
TelnetCon = telnetComm(TELNET_IP_ADDR, TELNET_PORT_NUM)
setup_lua_sim_done = False


def InitSerialConnection():
    global SerialCon
    SerialCon.Connect()

    if not SerialCon.is_connected:
        raise Exception("Test ,Initialize a Serial connection failed")

    SerialCon.Write(LUA_CLI)
    serial_buffer = SerialCon.Read(prompt=CONSOLE_PROMPT, timeout=30.0)
    assert serial_buffer.endswith(CONSOLE_PROMPT)


def InitTelnetConnection():
    global TelnetCon
    TelnetCon.Connect()

    if not TelnetCon.is_connected:
        raise Exception("Test ,Initialize a Telnet connection failed")

    TelnetCon.Write(NEW_LINE_CHAR)
    telnet_buffer = TelnetCon.Read(prompt=CONSOLE_PROMPT, timeout=10.0)
    assert telnet_buffer.endswith(CONSOLE_PROMPT)


@ddt
class PyCommunicationLayerUnitTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        global SerialCon, TelnetCon
        try:
            TerminateSimulation()
            StartSimulation()
            InitSerialConnection()
            InitTelnetConnection()
        except Exception as e:
            logging.debug(e.message)
            assert False

        logging.debug("+++++++++++++++++++++ setup ++++++++++++++++++++++++++++")
        serialOutput = SerialCon.Read(timeout=2)
        logging.debug(serialOutput)

        telnetOutput = TelnetCon.Read(timeout=2)
        logging.debug(telnetOutput)

        logging.debug("+++++++++++++++++++++++++++++++++++++++++++++++++\n\n\n")

    @classmethod
    def tearDownClass(cls):
        global SerialCon, TelnetCon
        logging.debug("++++++++++++++++++++ tearDown +++++++++++++++++++++++++")

        SerialCon.Disconnect()
        assert SerialCon.is_connected is False
        logging.debug("SerialConAlgoChannel Disconnected")

        TelnetCon.Disconnect()
        assert TelnetCon.is_connected is False
        logging.debug("TelnetConAlgoChannel Disconnected")

        logging.debug("+++++++++++++++++++++++++++++++++++++++++++++++++++++++")

    def setUp(self):
        logging.debug("=================== Test Case =======================\n")
        logging.debug("Test Case : " + self._testMethodName)

    def tearDown(self):
        logging.debug("=================================================\n\n\n")

    def test_init_serialcomm_with_default_params(self):
        serial_test_instance = serialComm(PORT_ID)
        assert serial_test_instance._serial.port == PORT_ID
        assert serial_test_instance._serial.baudrate == 115200
        assert serial_test_instance._serial.timeout == 3
        assert serial_test_instance._prompt == SERIAL_INIT_PROMPT
        assert serial_test_instance.is_connected is False

    def test_init_serialcomm_with_defined_params(self):
        serial_test_instance = serialComm(PORT_ID, CONSOLE_PROMPT, 115200, 10)
        assert serial_test_instance._serial.port == PORT_ID
        assert serial_test_instance._serial.baudrate == 115200
        assert serial_test_instance._serial.timeout == 10
        assert serial_test_instance._prompt == CONSOLE_PROMPT
        assert serial_test_instance.is_connected is False

    def test_init_telnetcomm_with_default_params(self):
        telnet_test_instance = telnetComm()
        assert telnet_test_instance._telnet is None
        assert telnet_test_instance.m_host is None
        assert telnet_test_instance.m_port == DEFAULT_TELNET_PORT
        assert telnet_test_instance.m_timeout == 5
        assert telnet_test_instance.is_connected is False

    def test_local_defined_params_while_init_telnetcomm(self):
        telnet_test_instance = telnetComm(TELNET_IP_ADDR, TELNET_PORT_NUM, 3)
        assert telnet_test_instance.m_host == TELNET_IP_ADDR
        assert telnet_test_instance.m_port == TELNET_PORT_NUM
        assert telnet_test_instance.m_timeout == 3
        assert telnet_test_instance.is_connected is False

    @data(SerialCon)
    def test_serial_connect_when_alredy_connected(self, ConChannel):

        assert ConChannel.is_connected is True
        try:
            ConChannel.Connect()
        except BaseCommException:
            ConChannel.Disconnect()
            sleep(1)
            ConChannel.Connect()
            assert ConChannel.is_connected

    @data(SerialCon)
    def test_serial_try_Disconnect_in_wrong_way(self, ConChannel):

        assert ConChannel.is_connected is True
        ConChannel.is_connected = False
        try:
            ConChannel.Connect()
            assert False
        except BaseCommException:
            assert True
            ConChannel.is_connected = True

    @data(SerialCon)
    def test_disconnect_for_an_open_port_and_reconnect(self, ConChannel):

        assert ConChannel.is_connected is True
        ConChannel.Disconnect()
        assert ConChannel.is_connected is False
        ConChannel.Connect()
        assert ConChannel.is_connected is True

    def test_connect_disconnect_scenario(self):
        telnet_test_instance = telnetComm(TELNET_IP_ADDR, TELNET_PORT_NUM)
        telnet_test_instance.Connect()
        assert telnet_test_instance.is_connected is True
        telnet_test_instance.Disconnect()
        assert telnet_test_instance.is_connected is False

    @data(TelnetCon)
    def test_telnet_connect_when_alredy_connected(self, ConChannel):

        assert ConChannel.is_connected is True
        ConChannel.is_connected = False
        try:
            ConChannel.Connect()
        except BaseCommException:
            assert False
        assert True

    @data(SerialCon, TelnetCon)
    def test_read_without_prompt_with_timeout(self, ConChannel):

        assert ConChannel.is_connected is True
        ConChannel.Write(NEW_LINE_CHAR)

        start_time = time()
        output = ConChannel.Read(timeout=5)
        end_time = time()
        logging.debug(end_time - start_time)
        assert (end_time - start_time) >= 4.9 and (end_time - start_time) < 6

    @data(SerialCon, TelnetCon)
    def test_write_command_and_read_buffer(self, ConChannel):
        dummy_command = "command\n"

        assert ConChannel.is_connected is True
        bytes_written = ConChannel.Write(dummy_command)

        assert len(dummy_command) == bytes_written
        output = ConChannel.Read(timeout=5)
        logging.debug(output)
        assert output != ''

    @data(SerialCon, TelnetCon)
    def test_read_with_prompt_without_timeout(self, ConChannel):

        assert ConChannel.is_connected is True
        ConChannel.Write(NEW_LINE_CHAR)

        output = ConChannel.Read(prompt=CONSOLE_PROMPT)
        logging.debug(output)

        assert output.endswith(CONSOLE_PROMPT)

    @data(SerialCon, TelnetCon)
    def test_read_with_prompt_with_long_timeout(self, ConChannel):

        assert ConChannel.is_connected is True
        ConChannel.Write(NEW_LINE_CHAR)

        start_time = time()
        output = ConChannel.Read(prompt=CONSOLE_PROMPT, timeout=7)
        end_time = time()
        assert (end_time - start_time) <= 7
        assert output.endswith(CONSOLE_PROMPT)

    @data(SerialCon, TelnetCon)
    def test_read_with_prompt_with_short_timeout(self, ConChannel):

        assert ConChannel.is_connected is True
        ConChannel.Write(NEW_LINE_CHAR)

        start_time = time()
        output = ConChannel.Read(prompt=CONSOLE_PROMPT, timeout=0)
        end_time = time()
        logging.debug(output)
        assert end_time - start_time < 0.5

    @data(SerialCon, TelnetCon)
    def test_new_line_and_wait_for_short_time(self, ConChannel):

        assert ConChannel.is_connected is True
        ConChannel.Write(NEW_LINE_CHAR)
        start_time = time()
        output = ConChannel.Read(timeout=4)
        end_time = time()
        logging.debug(output)
        logging.debug(end_time - start_time)

        assert 3.9 <= (end_time - start_time) < 5
        assert output.endswith(CONSOLE_PROMPT)

    @data(SerialCon, TelnetCon)
    def test_read_without_prompt_without_timeout_None(self, ConChannel):
        # read all
        assert ConChannel.is_connected is True
        ConChannel.Write(NEW_LINE_CHAR)

        start = time()
        output = ConChannel.Read(timeout=None)
        end = time()
        assert (end - start < 1)

    @data(SerialCon, TelnetCon)
    def test_read_all_data_without_prompt_with_timeout_zero_with_loop(self, ConChannel):
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
            assert (end_time - start_time) <= 0.5
            if output.endswith(CONSOLE_PROMPT):
                break
            exe_loop_time = time() - loop_start_time
            if (exe_loop_time > 3):  # if long time and prompt not received
                assert False
        logging.debug(exe_loop_time)
        logging.debug(output)
        assert output.endswith(CONSOLE_PROMPT)

    @data(SerialCon, TelnetCon)
    def test_read_all_data_without_prompt_with_timeout_zero_with_waiting(self, ConChannel):
        """ test timeout zero"""

        assert ConChannel.is_connected is True
        ConChannel.Write(NEW_LINE_CHAR)

        sleep(2)
        start_time = time()
        output = ConChannel.Read(timeout=0)
        end_time = time()

        assert (end_time - start_time) <= 0.2
        logging.debug(output)
        assert output.endswith(CONSOLE_PROMPT)


if __name__ == '__main__':
    unittest.main()
