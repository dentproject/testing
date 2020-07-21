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
from future.utils import iteritems


try:
    from Marvell.pytoolsinfra.PythonLoggerInfra.CommonUtils.fileNameUtils import findCallerWithClassName
    from Marvell.pytoolsinfra.PythonLoggerInfra import LoggerManager
    from Marvell.CommunicationService.PyBaseLayer.ChannelReader import ChannelReader
except Exception as e:
    from Marvell.CommunicationService.Common.ImportExternal import import_external
    import_external('pytoolsinfra')
    from Marvell.pytoolsinfra.PythonLoggerInfra.CommonUtils.fileNameUtils import findCallerWithClassName
    from Marvell.pytoolsinfra.PythonLoggerInfra import LoggerManager
    from Marvell.CommunicationService.PyBaseLayer.ChannelReader import ChannelReader

from ..HighCommunicationLayer.ABCCommunicationAlgo import *
from ..PyCommunicationAlgoLayer.ChannelFactory import *
from ..CommunicationExceptions.Exceptions import PythonComException
import time
import re


# === Python Communication Algo impl ===
class CommunicationMode(Enum):
    REGULAR_MODE = "REST-API"
    CONSOLE_MODE = "WEB-SOCKET"


class PyCommunicationAlgo(ABCCommunicationAlgo):
    """inherent ABCCommunicationAlgo , and implement algorithms API in python,
    based on PyBaseLayer implementation
    """
    m_channel = None
    m_channelDataReader = None
    m_connAlias = None
    m_prompt = None
    m_IsConnected = False

    def __init__(self, prompt):
        if not isinstance(prompt, bytes):
            prompt = prompt.encode('utf-8')
        self.m_prompt = prompt
        self._comm_logger = None
        self._default_logger = None
        self._connectionEventsCallBack = None
        self.m_communication_mode = CommunicationMode.REGULAR_MODE
        self.m_channelDataReader = None

    @property
    def _get_default_logger(self):
        if self._default_logger:
            return self._default_logger

        self._default_logger = LoggerManager.GetLogger("CommunicationDefaultLogger", ".\\Results\\", "CommDefaultLog",
                                       # logger_type=LoggerManager.LogType.TEST_LOGGER)
                                       logger_type=LoggerManager.LogType.HTML_LOGGER)

    def SetCommunicationLogger(self, comm_logger):
        self._comm_logger = comm_logger

    def LogToTestLogger(self, msg, *args, **kwargs):
        fn, lno, funcName, className = findCallerWithClassName()
        funcname = className + "::" + funcName + ": "

        if self._comm_logger and msg:
            if kwargs.get('noFormat', None):
                funcname = ""

            self._comm_logger.debug(funcname + "\n" + msg, *args, **kwargs)
        else:
            # print to default Logger
            self._get_default_logger.debug(funcname + msg, *args, **kwargs)  # , onlyConsole=True)

    def SetDoReconnect(self, need_reconnect):
        self.m_channel.do_reconnect = need_reconnect

    def Connect(self, channeltype, portId, baudRate=115200, parity="N", dataBits=8, stopBits=1,
                ipAddr=None, uname=None, password=None, **extraParameters):
        try:
            self.m_connAlias, self.m_channel = ChannelFactory.Create(channeltype, portId, ipAddr,
                                                                     self.m_prompt, uname, password, **extraParameters)

            self.m_channel.Connect()
            self.m_IsConnected = True
            self.m_channelDataReader = ChannelReader(self.m_channel)
            return self.m_connAlias
        except ConnectionFailedException as e:
            raise
        except Exception as e:
            raise ConnectionFailedException(channeltype, "{} Connection Failed!!\n".format(channeltype.name) + str(e))
            #return None  --> Uncreachble Code

    def registerChannelEventsCallBack(self, callBackId, channelEventsCallBack):
        self.m_channelDataReader.registerChannelEventsCallBack(callBackId, channelEventsCallBack)

    def unregisterChannelEventsCallback(self, callBackId):
        self.m_channelDataReader.unregisterChannelEventsCallback(callBackId)

    def unregisterChannelEventsAllCallback(self):
        self.m_channelDataReader.unregisterChannelEventsAllCallback()

    def Disconnect(self):
        self.unregisterChannelEventsAllCallback()
        self.m_channelDataReader.stopReadPolling()
        self.disconnect = self.m_channel.Disconnect()
        self.m_IsConnected = False
        self.mode = self._SetRegularMode()
        self._connectionEventsCallBack = None
        self.m_connAlias = None

    def SetMode(self, comm_mode):
        self.m_communication_mode = comm_mode

        if comm_mode == CommunicationMode.REGULAR_MODE:
            self._SetRegularMode()
        elif comm_mode == CommunicationMode.CONSOLE_MODE:
            self._SetConsoleMode()

    def _SetConsoleMode(self):
        self.m_channelDataReader.startReadPolling()

    def _SetRegularMode(self):
        self.m_channelDataReader.stopReadPolling()

    def SendTerminalString(self, command, waitForPrompt=True):
        if self.m_IsConnected is False:
            err = "'pyCommunicationALgo.SendTerminalString' Failed!!\n" + \
                  "You must connect first using 'pyCommunicationALgo.Connect()'"
            raise PythonComException(err)
        if command is None:
            err = "'pyCommunicationALgo.SendTerminalString' Failed!!\n" + \
                  "Cannot Send None command ! "
            raise PythonComException(err)

        if isinstance(command, str):
            command = command.encode('utf-8')
        numWriteChars = self.m_channel.Write(command)

        if waitForPrompt:
            self.GetBufferTillPrompt()

        return numWriteChars

    def SendCommandAndGetBufferTillPrompt(self, command, timeOutSeconds=10):

        if self.m_IsConnected is False:
            err = "'pyCommunicationALgo.SendCommandAndGetBufferTillPrompt' Failed!!\n" + \
                  "You must connected using 'pyCommunicationALgo.Connect()'"
            raise PythonComException(err)

        if not isinstance(command, bytes):
            command = command.encode('utf-8')
        
        errors_pattern = b"([Uu]nknown\s+command)|(input\s+overrun)|([Cc]ommand\s+not\s+found)"
        nums_of_retries = 3
        output = ""
        for i in range(nums_of_retries):
            self.SendTerminalString(command, False)
            output = self.GetBufferTillPrompt(timeOutSeconds)

            try:
                if re.search(errors_pattern, output, re.MULTILINE):
                    raise PythonComException(output)

            except Exception as e:
                if i == (nums_of_retries-1):
                    err = "SendCommandAndGetBuffer failed ! \n try to send :"+command + \
                          "\nfailed after "+str(nums_of_retries)+"retries\n" + \
                          "timeOutValue : " + str(timeOutSeconds) + \
                          "Current Buffer :" + str(e)
                    raise PythonComException(err)
                else:
                    self.LogToTestLogger("SendCommandAndGetBuffer failed on try to send " +
                                         command + "try number " + str(i+1), onlyConsole=True)
                    self.SendTerminalString("", False)
                    self.GetBuffer(0.2)
                    continue
            break

        return output

    def _read(self, prompt=None, timeOutSeconds=None, max_bytes=4096):
        if self.m_communication_mode == CommunicationMode.CONSOLE_MODE:
            raise PythonComException("Explicit request for reading data from channel while CONSOLE mode")
        data = self.m_channelDataReader.read(prompt=prompt, timeout=timeOutSeconds, max_bytes=max_bytes)
        return data

    def GetBuffer(self, timeOutSeconds, max_bytes=4096):

        if self.m_IsConnected is False:
            err = "'pyCommunicationALgo.GetSerialBuffer' Failed!!\n" + \
                  "You must connected using 'pyCommunicationALgo.Connect()'"
            raise PythonComException(err)

        Outputbuffer = self._read(timeOutSeconds=timeOutSeconds, max_bytes=max_bytes)
        return Outputbuffer

    def GetBufferTillPrompt(self, timeOutSeconds=10, shellPrompt=None):
        if self.m_IsConnected is False:
            err = "'pyCommunicationALgo.GetSerialBufferTillPrompt' Failed!!\n" + \
                  "You must connected using 'pyCommunicationALgo.Connect()'"
            raise PythonComException(err)

        if not shellPrompt:
            shellPrompt = self.m_prompt
        else:
            if isinstance(shellPrompt, str):
                shellPrompt = shellPrompt.encode('utf-8')


        if not shellPrompt or shellPrompt.isspace():
        #if not self.m_prompt.isEmpty():
            err = "'pyCommunicationALgo.GetBufferTillPrompt' failed!! prompt is unintialized!!"
            raise PythonComException(err)
        start_time = time.time()

        output = self._read(prompt=shellPrompt, timeOutSeconds=timeOutSeconds)
        end_time = time.time()
        is_till_prompt = False
        if output:
            is_till_prompt = output.endswith(shellPrompt)
        if not is_till_prompt:
            CONST_DIFF = 0.1 # variance between timeout parameter to actual timeout
            read_time = end_time - start_time
            if (read_time + CONST_DIFF) >= timeOutSeconds: #taken the time quota
                err = "GetBufferTillPrompt failed!!, Can't Read until prompt \n" \
                      "Approximate time was: " + str(read_time + CONST_DIFF) + " seconds\n" \
                      "Buffer content : " + output.decode('utf-8')

                raise PythonComException(err)

        return output


    # def GetSerialBufferTillIdle(self, idleTimeMili=250, timeOutSec=5):
    #     pass

    def SendCommandAndGetBufferTillPromptDic(self, command, dicPattern, timeOutSeconds=10):
        if not isinstance(command, bytes):
            command = command.encode('utf-8')

        startTime = time.time()
        self.SendTerminalString(command, False)
        # output = self.GetBufferTillPrompt(timeOutSeconds)
        output = b""
        try:
            while (True):
                output += self.GetBuffer(timeOutSeconds=0, max_bytes=2048)
                for key, pattern in iteritems(dicPattern):
                    match = re.search(pattern, output, re.MULTILINE)
                    if match:
                        return output
                exe_time = time.time() - startTime
                if exe_time >= timeOutSeconds:
                    raise Exception("Can't read till any prompt, timeout exception " + str(exe_time) +
                                    " seconds. \n" + "Current buffer: " + output)
                time.sleep(0.1)

        except Exception as e:
            err = "'SendCommandAndGetBufferTillPromptDic' Failed ! " + str(e)
            raise PythonComException(err)

    def SetShellPrompt(self, prompt):
        if self.m_IsConnected is False:
            err = "'pyCommunicationALgo.SetShellPrompt' Failed!!\n" + \
                  "You must connected using 'pyCommunicationALgo.Connect()'"
            raise PythonComException(err)

        if not isinstance(prompt, bytes):
            prompt = prompt.encode('utf-8')

        self.m_prompt = prompt

