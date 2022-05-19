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

# from time import sleep, time
from builtins import str
from copy import copy
from future.utils import PY3

from Marvell.pytoolsinfra.SysEventManager.EventNameEnum import EventNameEnum
from serial.serialutil import Timeout

from Marvell.pytoolsinfra.PythonLoggerInfra.CommonUtils.fileNameUtils import findCallerWithClassName
# from Marvell.pytoolsinfra.PythonLoggerInfra.TestLogger.LoggerInterface.ABCTestLogger import ABCTestLogger
from Marvell.CommunicationService.CommunicationExceptions.Exceptions import ConnectionLostException
from Marvell.CommunicationService.CommunicationWrapper.ComWrapperImpl.ExceptionEventData import ExceptionEventData
from Marvell.CommunicationService.HighCommunicationLayer.CommunicationManagement import \
    CommunicationManagement
from Marvell.CommunicationService.CommunicationWrapper import *
from Marvell.CommunicationService.CommunicationWrapper.ComWrapperInterface.ABCComWrapper import ABCComWrapper
from Marvell.pytoolsinfra.DutCommands.DutCommandAbc.DutCommandAbc import DutCommandAbc
# from Marvell.pytoolsinfra.SysEventManager.SysEventManager import SysEventManager
import re
from xmodem import XMODEM


logger = CommWrapper_logger


class PyBaseComWrapper(ABCComWrapper):
    # connAlias = ''
    reType = type(re.compile("hello"))  # save the type of any re object

    def __init__(self, connAlias, connectionData=None, logObj=None, shellPrompt=None, userPrompt=None, passPrompt=None):
        from Marvell.pytoolsinfra.SysEventManager.SysEventManager import SysEventManager
        self._is_inner_call = False
        self.connAlias = connAlias
        self._userPrompt = None
        self._passprompt = None
        self._shellPrompt = None
        self._lastBufferTillPrompt = None
        self._testlogger = None
        self.testlogger = logObj
        self.newlineChar = "\n"
        self.generate_uid = False
        self.retry_connect = True
        self.timeout_between_retries = 5
        self.nums_of_retries = 3
        self._testlogger_additional_kwargs = {}
        self._is_registered_object = SysEventManager.IsEventRegistered(EventNameEnum.COMM_CONNECTION_LOST_EVENT)
        self._userName = self._password = None
        self.login_after_connect = False # if True will try to login to target using input username and password
        self._max_login_recursive_calls = 6
        self._current_login_rec_call = 0

        if connectionData is not None:
            if hasattr(connectionData, "uname"):
                self._userName = connectionData.uname.value
            if hasattr(connectionData, "password"):
                self._password = connectionData.password.value

        self.get_buffer_till_pattern_interval = 0.1  # set none to read all buffer
        self.cli_print_mode = False # uses to indicate if working with a cli and reduces redundant prints


        # For Sending/Receiving Compressed data for LUA JSON commands
        self._xmodem = XMODEM(self.getc, self.putc)
        self._xmodem_buf = b''
        # #################################

        if shellPrompt is None:
            self.shellPrompt = re.compile(r".*[#>].*\Z", re.IGNORECASE)
        else:
            self.shellPrompt = shellPrompt

        if userPrompt is None:
            self.userPrompt = re.compile(r"(user\s*name.*|.*login.*)\s*\Z", re.IGNORECASE)
        else:
            self.userPrompt = userPrompt

        if passPrompt is None:
            self.passPrompt = re.compile(r"password.*\s*\Z", re.IGNORECASE)
        else:
            self.passPrompt = passPrompt
            # self.logger = test_log_class

    # For Sending/Receiving Compressed data for LUA JSON commands
    def getc(self, size, timeout=1):
        count = len(self._xmodem_buf)
        while count < size:
            temp = self.GetBuffer(timeout, size, False)
            if temp and len(temp) > 0:  # timeout reached
                self._xmodem_buf += temp
            else:
                return None

            count = len(self._xmodem_buf)
            if count == 0:
                return None

        d = self._xmodem_buf[:size]
        self._xmodem_buf = self._xmodem_buf[len(d):]
        return d

    def putc(self, data, timeout=1):
        return self.SendTerminalString(data, False)

    @property
    def XModem(self):
        return self._xmodem

####################################################################

    def Connect(self):
        # type: () -> bool
        raise NotImplementedError("ERROR: 'Connect' function isn't implemented")

    def LogToTestLogger(self, msg, *args, **kwargs):
        force_format = True if kwargs.get('force_format',None) is not None else False
        if force_format:
            kwargs.pop('force_format')
        if not self.cli_print_mode or force_format:
            fn, lno, funcName, className = findCallerWithClassName()
            funcname = "{}::{}: ".format(className,funcName)
        else:
            funcname = ""

        if self.testlogger and msg:
            if isinstance(msg, bytes):
                msg = msg.decode('utf-8')

            if kwargs.get('noFormat',None):
                funcname = ""

            final_kwargs = dict(kwargs)
            if self.cli_print_mode and not force_format:
                final_kwargs["noFormat"] = True

            if self._testlogger_additional_kwargs:
                final_kwargs.update(self._testlogger_additional_kwargs)

            self.testlogger.trace(funcname + msg, *args, **final_kwargs)

        # also optionally print to Resource Manager Logger
        if logger:
            logger.debug(funcname + msg, *args, **kwargs)  # , onlyConsole=True)

    @property
    def shellPrompt(self):
        return self._shellPrompt

    @shellPrompt.setter
    def shellPrompt(self, prompt):
        if type(prompt) is self.reType:
            self._shellPrompt = prompt
        elif isinstance(prompt, str):
            self._shellPrompt = re.compile(prompt, re.I)

    @property
    def userPrompt(self):
        return self._userPrompt

    @userPrompt.setter
    def userPrompt(self, prompt):
        if type(prompt) is self.reType:
            self._userPrompt = prompt
        else:
            self._userPrompt = re.compile(prompt, re.I)

    @property
    def passPrompt(self):
        return self._passprompt

    @passPrompt.setter
    def passPrompt(self, prompt):
        if type(prompt) is self.reType:
            self._passprompt = prompt
        else:
            self._passprompt = re.compile(prompt, re.I)

    @property
    def lastBufferTillPrompt(self):
        return self._lastBufferTillPrompt

    @lastBufferTillPrompt.setter
    def lastBufferTillPrompt(self, buff):
        self._lastBufferTillPrompt = buff

    @property
    def testlogger(self):
        if self._testlogger is not None:
            return self._testlogger

    @testlogger.setter
    def testlogger(self, logObj):
        # type logObj: ABCTestLogger
        self._testlogger = logObj

    def GetConnectedChannels(self):
        return CommunicationManagement.GetConnectedChannels()

    @classmethod
    def DisconnectAllChannels(cls):
        conArr = CommunicationManagement.GetConnectedChannels()

        for alias in conArr:
            CommunicationManagement.Disconnect(alias)

    def SendCommandAndGetFoundPatterns(self, command, patterns_list, AppendNewLine=True, timeOutSeconds=10.0):
        """
        Send the command to Dut and Get all matched patterns in patterns_list using re.findall
        :param AppendNewLine:
        :param command: the command to send
        :param patterns_list: list of possible patterns to search a match for
        :param timeOutSeconds: max timeout in seconds
        :type command:str
        :type patterns_list: list[str]
        :type timeOutSeconds: int
        :return: list of found matched pattern returned as string
        """
        self._is_inner_call = True
        try:
            self.SendCommand(command, AppendNewLine)
            return self.GetAllMatchedPatternsInBuffer(patterns_list, timeOutSeconds)
        except ConnectionLostException as e:
            if self._handle_connection_lost(True, e, cmd_str=command):
                # If the user handled the event we want to run the cmd again
                return self.SendCommandAndGetFoundPatterns(command, patterns_list, AppendNewLine, timeOutSeconds)
            else:
                raise
        finally:
            self._is_inner_call = False

    def GetBuffer(self, timeOutSeconds=1, max_bytes=4096, decode=True):
        try:
            buf = CommunicationManagement.GetBuffer(self.connAlias, timeOutSeconds, max_bytes=max_bytes)
            if decode and isinstance(buf, bytes):
                return buf.decode("utf-8", errors='ignore')
            else:
                return buf
        except ConnectionLostException as e:
            if self._handle_connection_lost(not self._is_inner_call, e):
                # If the user handled the event we want to run the cmd again
                return self.GetBuffer(timeOutSeconds, max_bytes)
            else:
                raise

    def Disconnect(self):
        if self.is_connected():
            CommunicationManagement.Disconnect(self.connAlias)

    def SendTerminalString(self, command, waitForPrompt=True):
        try:
            return CommunicationManagement.SendTerminalString(self.connAlias, command, waitForPrompt)
        except ConnectionLostException as e:
            if self._handle_connection_lost(not self._is_inner_call, e, cmd_str=command):
                # If the user handled the event we want to run the cmd again
                return self.SendTerminalString(command, waitForPrompt)
            else:
                raise

    def SendCommandAndGetBufferTillPrompt(self, command, timeOutSeconds=10):
        try:
            return CommunicationManagement.SendCommandAndGetBufferTillPrompt(self.connAlias, command, timeOutSeconds)
        except ConnectionLostException as e:
            if self._handle_connection_lost(True, e, cmd_str=command):
                # If the user handled the event we want to run the cmd again
                return self.SendCommandAndGetBufferTillPrompt(command, timeOutSeconds)
            else:
                raise

    def SendCommand(self, command, AppendNewLine=True):
        """
        send command to terminal
        :param command: the command to send
        :type command: str
        :param AppendNewLine: set to True to append new line
        :type AppendNewLine: bool
        :return: None
        :rtype: None
        """

        try:
            if AppendNewLine:
                command += self.newlineChar
            if not self.cli_print_mode:
                self.LogToTestLogger(" ==>CMD: \"{}\"".format(command))
            return CommunicationManagement.SendTerminalString(self.connAlias, command, False)
        except ConnectionLostException as e:
            if self._handle_connection_lost(not self._is_inner_call, e, cmd_str=command):
                # If the user handled the event we want to run the cmd again
                return self.SendCommand(command, AppendNewLine)
            else:
                raise

    def GetBufferTillPrompt(self, timeOutSeconds=10, shellPrompt = None):
        try:
            return CommunicationManagement.GetBufferTillPrompt(self.connAlias, timeOutSeconds, shellPrompt)
        except ConnectionLostException as e:
            if self._handle_connection_lost(not self._is_inner_call, e):
                # If the user handled the event we want to run the cmd again
                return self.GetBufferTillPrompt(timeOutSeconds, shellPrompt)
            else:
                raise

    def SendCommandAndWaitForPattern(self, command, AppendNewLine=True, ExpectedPrompt=None, timeOutSeconds=10.0):
        """
        :param command: the command to send
        :type command: str
        :param AppendNewLine: set to True to append new line
        :type AppendNewLine: bool
        :param ExpectedPrompt: Expected prompt to, defaults to enable context prompt
        :type ExpectedPrompt: str
        :param timeOutSeconds: max timeout in seconds to wait for expected pattern
        :type timeOutSeconds: float
        :return: True if Succeeded of False otherwise
        :rtype: bool
        """
        self._is_inner_call = True
        try:
            self.SendCommand(command, AppendNewLine)
            return self.GetBufferTillPattern(ExpectedPrompt, timeOutSeconds)
        except ConnectionLostException as e:
            if self._handle_connection_lost(True, e, cmd_str=command):
                # If the user handled the event we want to run the cmd again
                return self.SendCommandAndWaitForPattern(command, AppendNewLine, ExpectedPrompt, timeOutSeconds)
            else:
                raise
        finally:
            self._is_inner_call = False

    def GetBufferTillPattern(self, ExpectedPrompt=None, timeOutSeconds=10.0, send_new_line_on_timeout=True):
        """
        this method tries to capture buffer till the termination sequence (prompt) is captured
        or until the timeout has passed, return True if succeeded to capture prompt and False if timeout has passed
        it also flushes its also flushes it self history buffer and fills it with all info for this session
        :param ExpectedPrompt:
        :type ExpectedPrompt: String Or Regex
        :param timeOutSeconds:
        :type timeOutSeconds: float
        :return: bool
        :rtype: bool
        """
        if ExpectedPrompt is None:
            ExpectedPrompt = self.shellPrompt

        result = False
        try:
            getbufferTimeout = self.get_buffer_till_pattern_interval
            self.lastBufferTillPrompt = ""
            # type: (re, float) -> bool ,
            # handle case where expected prompt is str
            res_ExpectedPrompt = None

            if isinstance(ExpectedPrompt, str):
                # if PY3:
                #     res_ExpectedPrompt = re.compile(str(ExpectedPrompt).encode('utf-8'), re.IGNORECASE)
                # else:
                    res_ExpectedPrompt = re.compile(str(ExpectedPrompt), re.IGNORECASE)
            elif type(ExpectedPrompt) == self.reType:
                res_ExpectedPrompt = ExpectedPrompt

            # self.SetShellPrompt("Console#")
            # buff = CommunicationManagement.GetBufferTillPrompt(self.connAlias)
            timeout = Timeout(timeOutSeconds)
            while not result:
                buff = self.GetBuffer(getbufferTimeout)
                if buff is not None and buff != "":
                    self.lastBufferTillPrompt += buff
                    if not self.cli_print_mode:
                        self.LogToTestLogger(buff)
                    if re.search(res_ExpectedPrompt, buff):
                        result = True
                        if self.cli_print_mode:
                            self.LogToTestLogger(self.lastBufferTillPrompt)
                        break

                if timeout.expired():
                    if send_new_line_on_timeout:
                        # send newline char and try 1 final time, if still didn't succeed then give up
                        msg = "timeout expired\nsending newline char and trying 1 last time"
                        self.LogToTestLogger(msg,force_format=True)
                        self.SendCommand(self.newlineChar, AppendNewLine=False)
                        buff = self.GetBuffer(getbufferTimeout)
                        if buff is not None and buff != "":
                            if not self.cli_print_mode:
                                self.LogToTestLogger(buff)
                            self.lastBufferTillPrompt += buff
                            if re.search(res_ExpectedPrompt, self.lastBufferTillPrompt):
                                result = True
                    if self.cli_print_mode:
                        self.LogToTestLogger(self.lastBufferTillPrompt)

                    break

                # TODO:handle event of user prompt - implement login() function
                # got emtpy string
                # if not buff:
                #     self.SendCommand(self.newlineChar)

        except ConnectionLostException as e:
            if self._handle_connection_lost(not self._is_inner_call, e, cmd_str=ExpectedPrompt):
                # If the user handled the event we want to run the cmd again
                return self.GetBufferTillPattern(ExpectedPrompt, timeOutSeconds, send_new_line_on_timeout)
        except Exception as e:
            self.LogToTestLogger(str(e),force_format=True)
            # print str(e)

        finally:
            return result

    def GetAllMatchedPatternsInBuffer(self, patterns_list, timeOutSeconds=10.0, sendNewlineBetweenAttempts=False):
        """
        this method tries to capture buffer till any of the termination sequences(prompts) provided in patterns_list
       or until the timeout has passed, return True if succeeded to capture prompt and False if timeout has passed
       it also flushes its self history buffer and fills it with all info for this session
       :param patterns_list: list of patterns to search in the buffer
       :type patterns_list: list[str]
       :param timeOutSeconds: timeout for search
       :type timeOutSeconds: float
       :param sendNewlineBetweenAttempts: indicate if to send newline between attempts to capture expected pattern
       :type sendNewlineBetweenAttempts: bool
       :return: pattern list of found patterns or None if no pattern was found before timeout
       :rtype: list[str]
       """
        if type(patterns_list) is not list:
            raise TypeError("GetAllMatchedPatternsInBuffer: the type of patterns_list is not list but "
                            "type {}".format(str(type(patterns_list))))
        # inner function to search multiple patterns
        def search_all(listofpatterns, buffer):
            retlist = []
            if buffer:
                for pattern in listofpatterns:
                    if re.search(pattern,buffer):
                        retlist.append(pattern)
            return retlist

        result = None
        found_prompts = None
        try:
            getbufferTimeout = 0.1
            self.lastBufferTillPrompt = ""
            timeout = Timeout(timeOutSeconds)
            while not result:
                if sendNewlineBetweenAttempts:
                    self.SendCommand(self.newlineChar, AppendNewLine=False)
                buff = self.GetBuffer(getbufferTimeout)
                if buff is not None and buff != "":
                    if not self.cli_print_mode:
                        self.LogToTestLogger(buff)
                    self.lastBufferTillPrompt += buff
                    found_prompts = search_all(patterns_list, buff)
                    if found_prompts:
                        if self.cli_print_mode:
                            self.LogToTestLogger(self.lastBufferTillPrompt)
                        result = True
                        break
                if timeout.expired():
                    # send newline char and try 1 final time, if still didn't succeed then give up
                    msg = "timeout expired\nsending newline char and trying 1 last time"
                    self.LogToTestLogger(msg,force_format=True)
                    self.SendCommand(self.newlineChar,AppendNewLine=False)
                    buff = self.GetBuffer(getbufferTimeout)
                    if buff is not None and buff != "":
                        if not self.cli_print_mode:
                            self.LogToTestLogger(buff)
                        self.lastBufferTillPrompt += buff
                        found_prompts = search_all(patterns_list , buff)
                        if not not found_prompts:
                            if self.cli_print_mode:
                                self.LogToTestLogger(self.lastBufferTillPrompt)
                            result = True
                    break

                # got emtpy string
                # if not buff:
                #     self.SendCommand(self.newlineChar)

        except Exception as e:
            self.LogToTestLogger(str(e),force_format=True)
            # print str(e)

        finally:
            return found_prompts

    def WaitForPatternAndSendCommand(self,ExpectedPrompt,command, AppendNewLine=True, timeOutSeconds=10.0):
        """
        wait for pattern and send command if pattern matched,
        :param ExpectedPrompt: expected pattern
        :type ExpectedPrompt:str | re
        :param command:command to send when pattern matched
        :type command:str
        :param AppendNewLine: if True will append new line to sent command
        :type AppendNewLine:bool
        :param timeOutSeconds:max wait time in seconds for expected pattern
        :type timeOutSeconds:float
        :return: True if succeeded to capture prompt and False if timeout has passed
        :rtype:bool
        """
        self._is_inner_call = True
        res = None
        try:
            res = self.GetBufferTillPattern(ExpectedPrompt, timeOutSeconds)
            if res:
                self.SendCommand(command, AppendNewLine)
            else:
                self.LogToTestLogger("WARNING!: pattern did not match, thus not sending command",force_format=True)
            return res
        except ConnectionLostException as e:
            if res and self._handle_connection_lost(True, e, cmd_str=command):
                # If the user handled the event we want to run the cmd again
                return self.SendCommandAndWaitForPattern(command, AppendNewLine, ExpectedPrompt, timeOutSeconds)
            else:
                raise
        finally:
            self._is_inner_call = False

    def WaitForPatternsAndSendCommandPerPattern(self, ExpectedPatternsToCommandExpPromptDict, AppendNewLine=True, timeOutSeconds=10.0):
        """
        waits for any of the input prompts to match and send the command provided for that matched prompt
        :param ExpectedPatternsToCommandExpPromptDict: dict of pattern to dict of command:expected_prompt to send upon found patterns
        :type ExpectedPatternsToCommandExpPromptDict:dict[dict]]
        :param AppendNewLine:if True will append new line to sent command
        :type AppendNewLine:bool
        :param timeOutSeconds:max wait time in seconds for expected patterns
        :type timeOutSeconds:float
        :return:True if succeeded to capture prompt and False if timeout has passed
        :rtype:
        """
        self._is_inner_call = True
        command2send = ""
        ExpectedPrompt = ""
        result = True
        try:
            found_patterns = self.GetAllMatchedPatternsInBuffer(patterns_list=ExpectedPatternsToCommandExpPromptDict.keys(), timeOutSeconds=timeOutSeconds)
            if found_patterns:
                if len(found_patterns) >1:
                    msg = "WaitForPatternsAndSendCommandPerPattern: WARNING! found more then 1 matched patterns==>{}\n"\
                          "sending command  for all matched patterns according to order they are  found".format(found_patterns)
                    self.LogToTestLogger(msg,force_format=True)
                for pattern in found_patterns:
                    for command2send,ExpectedPrompt in ExpectedPatternsToCommandExpPromptDict.items():
                        if command2send:
                            result &= self.SendCommandAndWaitForPattern(command=command2send,ExpectedPrompt=ExpectedPrompt,timeOutSeconds=timeOutSeconds)

        except ConnectionLostException as e:
            if self._handle_connection_lost(True, e, cmd_str=command2send):
                # If the user handled the event we want to run the cmd again
                return self.SendCommandAndWaitForPattern(command2send, AppendNewLine, ExpectedPrompt, timeOutSeconds)
            else:
                raise
        finally:
            self._is_inner_call = False
            return result

    def SendCommandAndGetBufferTillPattern(self,command, AppendNewLine=True, ExpectedPrompt=None, timeOutSeconds=10.0,strip_command_and_pattern=True):
        """
        :param command: the command to send
        :type command: str
        :param AppendNewLine: set to True to append new line
        :type AppendNewLine: bool
        :param ExpectedPrompt: Expected prompt to, defaults to enable context prompt
        :type ExpectedPrompt: str
        :param timeOutSeconds: max timeout in seconds to wait for expected pattern
        :type timeOutSeconds: float
        :param strip_command_and_pattern:
        :type strip_command_and_pattern:
        :return: buffer found between command and pattern optionally strip the pattern and command from return buffer or None if timeout occurs
        :rtype: str
        """
        buff = None
        if self.SendCommandAndWaitForPattern(command,AppendNewLine,ExpectedPrompt,timeOutSeconds):
            buff = self.lastBufferTillPrompt
            if strip_command_and_pattern:
                prompt = ExpectedPrompt
                if ExpectedPrompt is None:
                    prompt = self.shellPrompt
                just_prompt = re.sub(r"(\\Z|\\|\(|\)|s\*)","",self.shellPrompt.pattern)
                prompt_2_clean = r"(.*{}.*)".format(just_prompt)
                buff = self._clean_dut_cli_buffer(self.lastBufferTillPrompt,[re.compile("^.*{}".format(command),re.M),prompt_2_clean])
            return buff

    def Login(self):
        """
        login to target device using input username,password and shell prompts
        the target is to get to shell prompt
        :return: True on success
        :rtype:bool
        """
        ret = True
        if self._current_login_rec_call < self._max_login_recursive_calls:
            self._current_login_rec_call +=1
        else:
            err = "failded to login, please check that user ({}) & password ({}) are correct:".format(self._userName,self._password)
            self.LogToTestLogger(err,force_format=True)
            self._current_login_rec_call = 0
            return False


        patterns_list = [self.userPrompt,self.passPrompt,self.shellPrompt]
        found_patterns = self.GetAllMatchedPatternsInBuffer(patterns_list=patterns_list,timeOutSeconds=3)
        if found_patterns:
            if len(found_patterns)> 1:
                err = "Login: ERROR found more then 1 matched pattern: {}, can't login".format(found_patterns)
                self.LogToTestLogger(err,force_format=True)
                ret = False
            else:
                # login according to found patter
                if self.userPrompt in found_patterns:
                    # send user and do recursive call
                    self.SendCommand(command=self._userName)
                    return self.Login()
                elif self.passPrompt in found_patterns:
                    self.SendCommand(command=self._password)
                    return self.Login()
                elif self.shellPrompt in found_patterns:
                    msg = "successfully logged in to device"
                    self.LogToTestLogger(msg,force_format=True)
                    self._current_login_rec_call = 0

        else:
            err = "failded to login, please check that user ({}) & password ({}) are correct:".format(self._userName,self._password)
            self.LogToTestLogger(err,force_format=True)

        return ret

    @staticmethod
    def _clean_dut_cli_buffer(buffer, clear_patterns_list, strip_empty_lines=True):
        """
        cleans a string
        :param buffer:  the dut buffer containing the response from CLI
        :param clear_patterns_list: list of patterns you wish to clear from the buffer
        :param strip_empty_lines: indicates if to also clear empty lines from buffer
        :type clear_patterns_list: list[str]
        :type buffer: str
        :return: a copy of original buffer cleared from input patterns and optionally stripped from empty lines
        :rtype: str
        """
        buff = copy(buffer)
        for ptrn in clear_patterns_list:
            # handle cases where the pattern contains re expression
            re_pattern = re.compile(ptrn)
            # strip the pattern from the buffer
            buff = re.sub(re_pattern, "", buff)
            if isinstance(ptrn, str) and ptrn in buff:
                buff = buff.replace(ptrn, "")
        if strip_empty_lines:
            # strip empty lines
            buff = "".join([s + "\n" for s in buff.splitlines(False) if re.sub(r"\s", "", s)]).strip()
        return buff

    def SetShellPrompt(self, prompt):
        CommunicationManagement.SetShellPrompt(self.connAlias, prompt)

    def is_connected(self):
        return CommunicationManagement.is_connected(self.connAlias)

    def SetDoReconnect(self, need_reconnect):
        """
        Alows the user to set if he wants the base layer to try reconnect when connection lost or not
        :param need_reconnect: bool parameter that indicates if we want to reconnect or not
        :return: void
        """
        CommunicationManagement.SetDoReconnect(self.connAlias, need_reconnect)

    def execute(self, cmd):
        """
        execute a command class on this channel
        each command should implement the following methods
        serialize()
        deserialize()
        execute()
        :param cmd: the command class to execute
        :type cmd: DutCommandAbc
        """

        self._is_inner_call = True
        try:
            return cmd._execute(self)
        except ConnectionLostException as e:
            if self._handle_connection_lost(True, e, api_data=cmd):
                # If the user handled the event we want to run the cmd again
                return self.execute(cmd)
            else:
                raise

        finally:
            self._is_inner_call = False

    def _handle_connection_lost(self, need_handle, e, **kwargs):
        from Marvell.pytoolsinfra.SysEventManager.SysEventManager import SysEventManager
        import inspect
        # Only if we know that there is a user that registered for this event
        # we won't raise it and let the user handle it
        if need_handle and self._is_registered_object:
            # we must remove it from the connected list so the user can reconnect
            CommunicationManagement.removeFromConnectionChannelDict(self.connAlias)

            exception_data = ExceptionEventData(inspect.stack()[0][3], e, self, **kwargs)
            SysEventManager.DispatchSysEvent(EventNameEnum.COMM_CONNECTION_LOST_EVENT, exception_data)
            return True
        else:
            return False

    def __hash__(self):
        return hash(self.connAlias)

    def __eq__(self, other):
        return self.connAlias == other.connAlias
# PyBaseComWrapper = Log_all_class_methods(PyBaseComWrapper, logger, show_func_parameters)


