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
import os, sys

try:
    from Marvell.pytoolsinfra.SysEventManager.EventNameEnum import EventNameEnum
    from Marvell.pytoolsinfra.SysEventManager.SysEventManager import SysEventManager
    from Marvell.pytoolsinfra.PythonLoggerInfra.TestLogger.LoggerImpl.BaseTestLogger import BaseTestLogger
except Exception:
    from Marvell.CommunicationService.Common.ImportExternal import *
    import_external('pytoolsinfra')
    from Marvell.pytoolsinfra.SysEventManager.EventNameEnum import EventNameEnum
    from Marvell.pytoolsinfra.SysEventManager.SysEventManager import SysEventManager
    from Marvell.pytoolsinfra.PythonLoggerInfra.TestLogger.LoggerImpl.BaseTestLogger import BaseTestLogger

file_path = __file__
index = file_path.rfind("Python_Communication_Service") + "Python_Communication_Service".__len__() + 1
file_path = file_path[:index]

sys.path.insert(0, os.path.abspath(file_path))

import pytest
from ...PyBaseLayer.serialComm import *
import threading

from ....CommunicationService.CommunicationWrapper.ComWrapperImpl.ConnectionData import *
# import psutil
from ..UnitTest_config import *


logger = BaseTestLogger("TestLogger", ".\\Results\\", "sampleLog1")

connection_channel = None
e_handle_thread = threading.Event()


def InitConnection():
    global connection_channel

    logger.debug("Connecting to Serial port 10!!!")
    # For Serial
    from Marvell.CommunicationService.CommunicationWrapper.ComWrapperImpl.PySerialComWrapper import PySerialComWrapper
    comSettings = Serial(10, 115200)
    connection_channel = PySerialComWrapper(comSettings)
    # connection_channel.testlogger = logger
    connection_channel.Connect()
    connection_channel.SendCommandAndWaitForPattern("", ExpectedPrompt=SERIAL_INIT_PROMPT, timeOutSeconds=20.0)
    connection_channel.Disconnect()

    logger.debug("Connecting to Telnet port 12345!!!")
    # For Telnet
    from Marvell.CommunicationService.CommunicationWrapper.ComWrapperImpl.PyTelnetComWrapper import PyTelnetComWrapper
    telnetSetting = Telnet(TELNET_IP_ADDR, TELNET_PORT_NUM)
    connection_channel = PyTelnetComWrapper(telnetSetting)
    # connection_channel.testlogger = logger
    try:
        connection_channel.Connect()
    except ConnectionFailedException as e:
        connection_channel.Connect()

    connection_channel.SendCommandAndWaitForPattern("", ExpectedPrompt=CONSOLE_PROMPT, timeOutSeconds=20.0)
    connection_channel.SetDoReconnect(False)

    logger.debug("Init connection finished")

def ValidateConnectionTerm():
    if not TerminateSimulation():
        print("Can't kill the Simulation Process")
        assert False


def HandleConnectionLost(data):
    global e_handle_thread
    logger.debug("Got 'ConnectionLost' event")
    logger.debug(data)
    StartSimulation()
    InitConnection()
    e_handle_thread.set()



@pytest.fixture(scope='module', autouse=True)
def setUpClass():

    print("+++++++++++++++++++++ setup +++++++++++++++++++++++++++++")

    try:
        SysEventManager.Register(EventNameEnum.COMM_CONNECTION_LOST_EVENT, HandleConnectionLost, sync=True)
        TerminateSimulation()
        StartSimulation()
        InitConnection()
    except Exception as e:
        print(str(e))
        assert False

    print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n\n\n")

    yield
    tearDownClass()

def tearDownClass():
    global connection_channel
    logging.debug("++++++++++++++++++++ tearDown +++++++++++++++++++++++++++")

    connection_channel.Disconnect()
    assert connection_channel.is_connected() is False
    logging.debug("connection_channel Disconnected")

    logging.debug("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

@pytest.fixture(scope="function", autouse=True)
def setUp():
    global e_handle_thread

    logging.debug("======================= Test Case =============================\n")
    # logging.debug("Test Case : " + _testMethodName)

    e_handle_thread.clear()
    ValidateConnectionTerm()
    yield
    tearDown()

def tearDown():
    logging.debug("===============================================================\n\n\n")


def test_SendCommandAndWaitForPattern_when_connection_lost(setUpClass,setUp):
    connection_channel.SendCommandAndWaitForPattern("", ExpectedPrompt=CONSOLE_PROMPT, timeOutSeconds=20.0)
    event_is_set = e_handle_thread.wait(1)
    # if not event_is_set:
    #     raise Exception("Failed to handle the event")
    assert event_is_set


def test_GetBuffer_when_connection_lost(setUpClass,setUp):
    connection_channel.GetBuffer(timeOutSeconds=1)
    event_is_set = e_handle_thread.wait(1)
    # if not event_is_set:
    #     raise Exception("Failed to handle the event")
    assert event_is_set
