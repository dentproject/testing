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

from builtins import object
from abc import ABCMeta, abstractmethod
from Marvell.pytoolsinfra.DutCommands.DutCommandAbc.DutCommandAbc import DutCommandAbc
from future.utils import with_metaclass

"""
This is an abstract class that define all the APIs that ComWrappers should implement

"""


class ABCComWrapper(with_metaclass(ABCMeta, object)):
    def __init__(self):
        raise NotImplementedError('ERROR: Cant instantiate abstract class')

    @abstractmethod
    def Connect(self):
        """disconnect channel connection
        connectionAlias : connection Alias
        """
        pass

    @abstractmethod
    def Disconnect(self):
        """disconnect channel connection
        connectionAlias : connection Alias
        """
        pass

    @abstractmethod
    def SendTerminalString(self, command, waitForPrompt=True):
        """
        send terminal string to the device. if AppendNewLine is true , wait and return the buffer

        command: command to write to the device

        AppendNewLine: True in default

        connectionAlias : connection Alias

        return: None
        """
        pass

    @abstractmethod
    def SendCommand(self, command, AppendNewLine=True):
        """send terminal string to the device. if AppendNewLine is true , wait and return the buffer
    
         command: command to write to the device
    
         AppendNewLine: True in default
    
        connectionAlias : connection Alias
    
         return: None
        """
        pass

    @abstractmethod
    def GetBuffer(self, timeOutSeconds):
        """Read buffer

        param timeOutSeconds: timeout in seconds

        connectionAlias : connection Alias

        return: buffer content
        """
        pass

    @abstractmethod
    def SendCommandAndWaitForPattern(self, command, AppendNewLine=True, ExpectedPrompt=None, timeOutSeconds=10):
        """Sending given command , wait until reading prompt or timeout occurs.

        command: command to be executed

        timeOutSeconds: timeout in seconds

        connectionAlias : connection Alias

        return: buffer content
        :param AppendNewLine:
        :param ExpectedPrompt:
        """
        pass

    @abstractmethod
    def GetBufferTillPrompt(self, timeOutSeconds=10,shellPrompt=None):
        """read the buffer until prompt, or until timeout occurs.

         timeOutSeconds:  time out in second , default = 10

         return: buffer content
        """
        pass

    @abstractmethod
    def GetBufferTillPattern(self, ExpectedPrompt=None, timeOutSeconds=10, send_new_line_on_timeout=True):
        """
        :param ExpectedPrompt:
        :type ExpectedPrompt: String Or Regex
        :param timeOutSeconds:
        :type timeOutSeconds: float
        :return: bool

        this method tries to capture buffer till the termination sequence (prompt) is captured
        or until the timeout has passed, return True if succeeded to capture prompt and False if timeout has Passed
        it also flushes its also flushes it self history buffer and fills it with all info for this session
        """
        pass

    @abstractmethod
    def GetAllMatchedPatternsInBuffer(self , patterns_list , timeOutSeconds=10.0):
        """
        this method tries to capture buffer till any of the termination sequences(prompts) provided in patterns_list
        or until the timeout has passed, return True if succeeded to capture prompt and False if timeout has passed
        it also flushes its self history buffer and fills it with all info for this session
        :param patterns_list: list of patterns to search in the buffer
        :type patterns_list: list[str]
        :param timeOutSeconds: timeout for search
        :type timeOutSeconds: float
        :return: pattern list of found patterns or None if no pattern was found before timeout
        :rtype: list[str]
        """
        pass
    @abstractmethod
    def SetShellPrompt(self, prompt):
        """update shell prompt

        connectionAlias : connection Alias

         prompt: prompt

         return: None
        """
        pass

    @abstractmethod
    def SendCommandAndGetBufferTillPrompt(self, command, timeOutSeconds = 10):
        """Sending given command , wait until reading prompt or timeout occurs.

        command: command to be executed

        timeOutSeconds: timeout in seconds

        connectionAlias : connection Alias

        return: buffer content
        """

    @abstractmethod
    def SendCommandAndGetFoundPatterns(self, command, pattern_list, AppendNewLine =True, timeOutSeconds=10):
        """
        send command and return all found patterns or None if nothing was found
        :param command: the command to be sent
        :param pattern_list: a list of patterns
        :param AppendNewLine: if to append new line char to command before sending
        :param timeOutSeconds: timeout seconds before waiting for prompt
        :return:
        """
        pass

    @abstractmethod
    def is_connected(self):
        """
        :return: If the specified channel is still connected 
        """
        pass

    @abstractmethod
    def execute(self, cmd):
        """
        execute a command class on this channel
        each command should implement the following methods
        serialize()
        deserialize()
        execute()
        :param cmd:
        :return:
        :type cmd: DutCommandAbc
        """
        pass

    @abstractmethod
    def LogToTestLogger(self, msg, *args, **kwargs):
        """
        Log message into the given Logger.
        If we didn't assigned any logger the function shouldn't do anything

        :param msg: The message to Log
        :param args: Any args to format the message
        :param kwargs: Any args for the Logger
        :return:
        """
        pass
