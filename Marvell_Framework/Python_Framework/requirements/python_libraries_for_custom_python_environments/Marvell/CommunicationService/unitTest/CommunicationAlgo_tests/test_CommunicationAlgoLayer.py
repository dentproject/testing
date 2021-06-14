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

from builtins import str
from builtins import range
import os, sys, logging

file_path = __file__
index = file_path.rfind("Python_Communication_Service") + "Python_Communication_Service".__len__() + 1
file_path = file_path[:index]

sys.path.insert(0, os.path.abspath(file_path))

import unittest
from ...PyCommunicationAlgoLayer.PyCommunicationAlgo import *
from ...PyBaseLayer.serialComm import *
from ...unitTest.UnitTest_config import *
from ddt import ddt, data

SerialConAlgoChannel = PyCommunicationAlgo(CONSOLE_PROMPT)
TelnetConAlgoChannel = PyCommunicationAlgo(CONSOLE_PROMPT)
setup_lua_sim_done = False

def InitSerialConnection():
    global SerialConAlgoChannel
    SerialConAlgoChannel.Connect(CommunicationType.PySerial, SERIAL_COM_PORT, ipAddr=TELNET_IP_ADDR, uname=UNAME, password=PASSWORD)
    if not SerialConAlgoChannel.m_IsConnected:
        raise Exception("Test , serial connection failed")
    SerialConAlgoChannel.SendCommandAndGetBufferTillPrompt(LUA_CLI)

def InitTelnetConnection():
    global TelnetConAlgoChannel
    TelnetConAlgoChannel.Connect(CommunicationType.PyTelnet, TELNET_PORT_NUM, ipAddr=TELNET_IP_ADDR, uname=UNAME, password=PASSWORD)
    if not TelnetConAlgoChannel.m_IsConnected:
        raise Exception("Test , telnet connection failed")


@ddt
class PyCommunicationAlgoLayerUnitTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global SerialConAlgoChannel,TelnetConAlgoChannel
        try:

            logger = logging.getLogger()
            logger.level = logging.DEBUG  # DEBUG / INFO
            stream_handler = logging.StreamHandler(sys.stdout)
            logger.addHandler(stream_handler)

            TerminateSimulation()
            StartSimulation()
            InitSerialConnection()
            InitTelnetConnection()
        except Exception as e:
            # logging.debug(e.message)
            print(e.message)
            assert False

        logging.debug("+++++++++++++++++++++ setup +++++++++++++++++++++++++\n")
        serialOutput = SerialConAlgoChannel.GetBuffer(timeOutSeconds=2)
        logging.debug(serialOutput)

        telnetOutput = TelnetConAlgoChannel.GetBuffer(timeOutSeconds=2)
        logging.debug(telnetOutput)

        logging.debug("+++++++++++++++++++++++++++++++++++++++++++++++++\n\n\n")

    @classmethod
    def tearDownClass(cls):
        global SerialConAlgoChannel,TelnetConAlgoChannel
        logging.debug("++++++++++++++++++++ tearDown +++++++++++++++++++++++\n")

        SerialConAlgoChannel.Disconnect()
        assert SerialConAlgoChannel.m_IsConnected is False

        logging.debug("SerialConAlgoChannel Disconnected")
        TelnetConAlgoChannel.Disconnect()
        assert TelnetConAlgoChannel.m_IsConnected is False

        logging.debug("TelnetConAlgoChannel Disconnected")
        logging.debug("+++++++++++++++++++++++++++++++++++++++++++++++++\n\n\n")


    def setUp(self):
        global SerialConAlgoChannel,TelnetConAlgoChannel

        logging.debug("==================== Test Case ======================\n")
        logging.debug("Test Case : " + self._testMethodName)

        ResetBoardToConsolePrompt(SerialConAlgoChannel)
        ResetBoardToConsolePrompt(TelnetConAlgoChannel)

    def tearDown(self):
        logging.debug("=================================================\n\n\n")



    @data(SerialConAlgoChannel)
    def test_init_pycommalgo_serial_channel(self,ConChannel):
        assert ConChannel.m_IsConnected is True
        assert isinstance(ConChannel.m_channel, serialComm)

    @data(TelnetConAlgoChannel)
    def test_init_pycommalgo_telnet_channel(self, ConChannel):
        assert ConChannel.m_IsConnected is True
        assert isinstance(ConChannel.m_channel, telnetComm)


    @data(SerialConAlgoChannel)
    def test_disconnect_for_an_open_port_and_reconnect(self,ConChannel):

        assert ConChannel.m_IsConnected is True
        ConChannel.Disconnect()
        assert ConChannel.m_IsConnected is False

        ConChannel.Connect(CommunicationType.PySerial, SERIAL_COM_PORT, ipAddr=TELNET_IP_ADDR, uname=UNAME,
                           password=PASSWORD)

        assert ConChannel.m_IsConnected is True


    @data(SerialConAlgoChannel,TelnetConAlgoChannel)
    def test_send_command_and_get_buffer_with_short_timeout(self,ConChannel):
        assert ConChannel.m_IsConnected is True

        ConChannel.SetShellPrompt(CONSOLE_PROMPT)
        start = time()
        output = ConChannel.SendCommandAndGetBufferTillPrompt(NEW_LINE_CHAR, 0.5)
        end = time()
        logging.debug(end - start)
        assert 0 <= (end - start < 1)
        assert output.endswith(CONSOLE_PROMPT) is True

    @data(SerialConAlgoChannel,TelnetConAlgoChannel)
    def test_send_command_and_get_buffer_with_long_timeout(self,ConChannel):

        assert ConChannel.m_IsConnected is True
        ConChannel.SetShellPrompt(CONSOLE_PROMPT)
        start = time()
        output = ConChannel.SendCommandAndGetBufferTillPrompt(NEW_LINE_CHAR, 10)
        end = time()
        assert output.endswith(CONSOLE_PROMPT)
        assert end-start <= 10

    @data(SerialConAlgoChannel, TelnetConAlgoChannel)
    def test_get_buffer_long_timeout(self,ConChannel):

        assert ConChannel.m_IsConnected is True
        ConChannel.SendTerminalString(NEW_LINE_CHAR, False)

        GetBufferOut = ConChannel.GetBuffer(10)
        GetBufferTillPromptOut = ConChannel.SendCommandAndGetBufferTillPrompt(NEW_LINE_CHAR)
        assert GetBufferOut.endswith(CONSOLE_PROMPT) and GetBufferTillPromptOut.endswith(CONSOLE_PROMPT)

    #bellow dont need
    # def test_get_buffer_closed_port(self):
    #     pycomm_algo_instance = PyCommunicationAlgo(PROMPT)
    #     assert pycomm_algo_instance.m_IsConnected is False
    #     try:
    #         pycomm_algo_instance.GetBuffer(10)
    #         assert False
    #     except Exception:
    #         assert True

    # def test_get_buffer_till_prompt_closed_port(self):
    #     pycomm_algo_instance = PyCommunicationAlgo(PROMPT)
    #     assert pycomm_algo_instance.m_IsConnected is False
    #     try:
    #         pycomm_algo_instance.GetBufferTillPrompt()
    #         assert False
    #     except Exception:
    #         assert True


        # above dont need

    @data(SerialConAlgoChannel,TelnetConAlgoChannel)
    def test_set_shell_prompt(self,ConChannel):

        assert ConChannel.m_IsConnected is True
        initial_prompt = ConChannel.m_prompt
        out = ConChannel.SendCommandAndGetBufferTillPrompt(NEW_LINE_CHAR)
        ConChannel.SetShellPrompt("blalsdkjflksjlkasjlawj")
        try :
            out = ConChannel.SendCommandAndGetBufferTillPrompt(NEW_LINE_CHAR)
            assert ConChannel.m_prompt != initial_prompt
        except Exception:
            assert True


    @data(SerialConAlgoChannel,TelnetConAlgoChannel)
    def test_send_new_line_and_GetBuffer_with_short_time(self,ConChannel):
        """
        Test CommSerial.Read ( serialWin32.read(size) case )
        :return:
        """

        for i in range(3):
            ress= ConChannel.SendTerminalString('\n',waitForPrompt=False)
            output = ConChannel.GetBuffer(timeOutSeconds=2)
            assert output.endswith(CONSOLE_PROMPT)

    @data(SerialConAlgoChannel,TelnetConAlgoChannel)
    def test_send_and_read_untill_sub_prompt(self, ConChannel):
        """
        Test CommSerial.Read ( serialWin32.read(size) case )
        :return:
        """
        del_char = 2 if len(CONSOLE_PROMPT) > 2 else 0
        sub_prompt = CONSOLE_PROMPT[:-del_char]

        ConChannel.SetShellPrompt(prompt=sub_prompt)
        ConChannel.SendTerminalString(NEW_LINE_CHAR, False)
        output = ConChannel.GetBufferTillPrompt()
        assert output.endswith(sub_prompt)

        output = ConChannel.GetBuffer(timeOutSeconds=2)
        left_prompt = CONSOLE_PROMPT[len(CONSOLE_PROMPT) - del_char:]

        assert output.startswith(left_prompt)

    @data(SerialConAlgoChannel,TelnetConAlgoChannel)
    def test_resend_and_read_untill_sub_prompt(self,ConChannel):
        """
        Test CommSerial.Read ( serialWin32.read(size) case )
        :return:
        """
        del_char = 2 if len(CONSOLE_PROMPT) > 2 else 0
        sub_prompt = CONSOLE_PROMPT[:-del_char]

        ConChannel.SetShellPrompt(prompt=sub_prompt)
        ConChannel.SendTerminalString(NEW_LINE_CHAR, True)
        ConChannel.SendTerminalString(NEW_LINE_CHAR, False)

        output = ConChannel.GetBuffer(timeOutSeconds=2)

        left_prompt = CONSOLE_PROMPT[len(CONSOLE_PROMPT) - del_char:]
        assert output.startswith(left_prompt)
        assert output.endswith(CONSOLE_PROMPT)


    @data(SerialConAlgoChannel,TelnetConAlgoChannel)
    def test_send_and_read_untill_sub_prompt_with_actual_size(self,ConChannel):
        """
        Test CommSerial.Read ( serialWin32.read(size) case )
        :return:
        """
        del_char = 2 if len(CONSOLE_PROMPT) > 2 else 0
        sub_prompt = CONSOLE_PROMPT[:-del_char]

        ConChannel.SetShellPrompt(prompt=sub_prompt)
        ConChannel.SendTerminalString(NEW_LINE_CHAR, False)
        output = ConChannel.GetBufferTillPrompt()
        assert output.endswith(sub_prompt)

        output = ConChannel.GetBuffer(timeOutSeconds=2, max_bytes=del_char)
        assert len(output) == del_char

    @data(SerialConAlgoChannel,TelnetConAlgoChannel)
    def test_send_and_read_untill_sub_prompt_with_less_size(self,ConChannel):
        """
        Test CommSerial.Read ( serialWin32.read(size) case )
        :return:
        """
        del_char = 2 if len(CONSOLE_PROMPT) > 2 else 0
        sub_prompt = CONSOLE_PROMPT[:-del_char]

        ConChannel.SetShellPrompt(prompt=sub_prompt)
        ConChannel.SendTerminalString(NEW_LINE_CHAR, False)
        output = ConChannel.GetBufferTillPrompt()
        assert output.endswith(sub_prompt)

        output = ConChannel.GetBuffer(timeOutSeconds=2, max_bytes=del_char-1)
        assert len(output) == del_char-1

        output = ConChannel.GetBuffer(timeOutSeconds=0)
        assert len(output) == 1

    @data(SerialConAlgoChannel,TelnetConAlgoChannel)
    def test_resend_and_read_untill_size_less_than_buffer_content(self,ConChannel):
        ConChannel.SetShellPrompt(prompt=CONSOLE_PROMPT)
        ConChannel.SendTerminalString(NEW_LINE_CHAR, True)
        ConChannel.SendTerminalString(NEW_LINE_CHAR, False)

        output = ConChannel.GetBuffer(timeOutSeconds=2, max_bytes=4)
        assert len(output) == 4

    @data(SerialConAlgoChannel,TelnetConAlgoChannel)
    def test_SendCommandAndGetBufferTillPromptDic_read_untill_included_prompt(self,ConChannel):

        paterns = {"p1":b"Console# ","p2":b"->"}
        output = ConChannel.SendCommandAndGetBufferTillPromptDic(command=NEW_LINE_CHAR, dicPattern=paterns, timeOutSeconds=10)
        logging.debug(output)

        regexp = re.compile(b'\s*Console#\s*')

        assert regexp.search(output)

    @data(SerialConAlgoChannel, TelnetConAlgoChannel)
    def test_SendCommandAndGetBufferTillPromptDic_read_untill_no_prompt(self, ConChannel):
        paterns = {"p1": b"prompt", "p2": b"->"}
        output = ""
        try:
            output = ConChannel.SendCommandAndGetBufferTillPromptDic(command=NEW_LINE_CHAR, dicPattern=paterns,timeOutSeconds=10)
            logging.debug(output)
            assert False
        except PythonComException as e:
            logging.debug(output)

            assert True

    @data(SerialConAlgoChannel, TelnetConAlgoChannel)
    def test_SendCommandAndGetBufferTillPromptDic_read_untill_more_one_prompt(self, ConChannel):
        paterns = {"p1": b"lua>", "p2": b"Console# "}
        output = ConChannel.SendCommandAndGetBufferTillPromptDic(command=NEW_LINE_CHAR, dicPattern=paterns,timeOutSeconds=10)
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



    @data(SerialConAlgoChannel, TelnetConAlgoChannel)
    def test_SendCommandAndGetBufferTillPromptDic_read_untill_prompts_scenario(self, ConChannel):
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

    @data(SerialConAlgoChannel, TelnetConAlgoChannel)
    def test_SendCommandAndGetBufferTillPromptDic_read_untill_regix_scenario(self, ConChannel):
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

    @data(SerialConAlgoChannel, TelnetConAlgoChannel)
    def test_SendCommandAndGetBufferTillPromptDic_read_with_timeout(self, ConChannel):
        timeout = 25
        paterns = {"p1": b"Console[\(\)\w]*#\s*"}
        regexp = re.compile(b'Console[\(\)\w]*#\s*')
        command = 'cpssinitsystem 29,1\n'

        start_time = time()
        output = ConChannel.SendCommandAndGetBufferTillPromptDic(command=command, dicPattern=paterns,
                                                                 timeOutSeconds=timeout)
        exe_time = time() - start_time

        logging.debug(exe_time)
        logging.debug(output)

        assert exe_time <= timeout
        assert regexp.search(output)

    @data(SerialConAlgoChannel, TelnetConAlgoChannel)
    def test_SendCommandAndGetBufferTillPromptDic_cant_read_and_wait_for_timeout(self, ConChannel):
        output = ""
        paterns = {"p1": b"Console[\(\)\w]*#\s*"}
        regexp = re.compile(b'Console[\(\)\w]*#\s*')
        command = 'cpssinitsystem 29,1' #without enter
        start_time = time()
        try:
            output = ConChannel.SendCommandAndGetBufferTillPromptDic(command=command, dicPattern=paterns,
                                                                            timeOutSeconds=3)
            assert False
        except PythonComException as ex:
            exe_time = time() - start_time

            logging.debug(exe_time)
            logging.debug(output)
            logging.debug(str(ex))

            assert exe_time >= 3

if __name__ == '__main__':
    unittest.main()
