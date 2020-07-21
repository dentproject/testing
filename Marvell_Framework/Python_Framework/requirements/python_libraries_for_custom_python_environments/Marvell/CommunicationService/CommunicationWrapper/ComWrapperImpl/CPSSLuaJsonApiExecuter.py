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
from future import standard_library
standard_library.install_aliases()
from builtins import object
import io
import json
import re
from copy import deepcopy
from collections import OrderedDict

# only for the generator we need to mask this import
try:
    from Marvell.CommunicationService.CommunicationExceptions.Exceptions import WriteFailedException, ReadFailedException
except:
    print("The communication module isn't installed in this project.\nplease install it before using this module!!!\n")
    pass
# from CommonFuncs import *
# from CpssReturnCodeEnum import CpssReturnCodeEnum
# from DutCommandAbc import DutCommandAbc
import zlib
from enum import Enum
union_key_name = "union_type"


class CPSSLuaJsonApiExecuter(object):
    class OutputOptions(str, Enum):
        OUTONLY = "outonly"
        ALL = "all"
        ERRORONLY = "erroronly"
        NEVER = "never"

    def __init__(self, data_to_send, command_to_send="execGenWrapperC"):
        self.need_output = self.OutputOptions.OUTONLY
        self._sentCmd = data_to_send
        self._Error = ""
        self._dut_response = ""
        self._printDbg = False
        self._command_to_send = command_to_send
        self._channel = None

    def _deserialize(self, response):
        pass

    def _serialize(self):
        self._Error = ""
        return self._sentCmd

    def _execute(self, channel):
        """
        this method should pass it self to the executor class and ask to be executed
        :param channel:ABCComWrapper
        :type channel:ABCComWrapper
        :return:
        """
        self._channel = channel

        try:
            # disable printing to log file
            channel._testlogger_additional_kwargs = {"onlyConsole": True}
            self._send_cmd(channel)
            response = self._recv_cmd(channel)

            self._dut_response = response

            if self._printDbg:
                channel.LogToTestLogger("DUT Response:\n")
                channel.LogToTestLogger(response)
                channel.LogToTestLogger("\nEnd DUT Response:\n\n")

        except:
            raise
        finally:
            # restore printing to log file to default
            channel._testlogger_additional_kwargs = None

    def _send_cmd(self, channel):
        """
        This function sends the command to the DUT
        and if it fails it raises Exception
        :return:
        """
        command = self._serialize()

        if self._printDbg:
            channel.LogToTestLogger("Send command:\n")
            channel.LogToTestLogger(command)
            channel.LogToTestLogger("\nEnd Send command:\n\n")

        commandToSend = self._command_to_send
        sent_prompt = "\025\010\010\010\010" + commandToSend
        ret_len = channel.SendCommand(sent_prompt, AppendNewLine=True)

        if (len(sent_prompt) + 1) != ret_len:
            self._dut_response = ""
            errMsg = ("Problem sending command {}\n"
                      "Error: 'Real sent command length wasn't as the sent one'".format(commandToSend))
            raise Exception(errMsg)

        try:
            channel.GetBufferTillPrompt(5, shellPrompt=commandToSend)
        except Exception as e:
            self._dut_response = ""
            errMsg = ("Problem getting echo for {}\n"
                      "Error: {}".format(commandToSend, e.message))
            raise Exception(errMsg)

        # # Only because we have bug in the CPSS version
        ret_buf = ""
        while ret_buf != "\r":
            ret_buf = channel.GetBuffer(timeOutSeconds=1, max_bytes=1)
        while ret_buf != "\n":
            ret_buf = channel.GetBuffer(timeOutSeconds=1, max_bytes=1)

        data_compressed = io.StringIO(zlib.compress(command, 9))

        ret = channel.XModem.send(data_compressed, retry=20)
        data_compressed.close()
        if not ret:
            self._dut_response = ""
            errMsg = "Problem sending command {} to DUT".format(commandToSend)
            raise Exception(errMsg)

    def _recv_cmd(self, channel):
        """
            This function receives the response from the DUT
            and if it fails it raises Exception
            :return:
        """
        wait_for_more = True
        response = ""
        channel.lastBufferTillPrompt = ""

        while wait_for_more:
            stream = io.StringIO()
            channel.XModem.recv(stream, crc_mode=0, retry=20, timeout=30, quiet=True)
            if len(stream.getvalue()) > 0:
                response += zlib.decompress(stream.getvalue())
                channel.lastBufferTillPrompt += response
                if "ctrl_start_ret" in response:
                    if 'ctrl_end_ret' in response:
                        wait_for_more = False
                else:
                    wait_for_more = False

            elif response == "":
                errMsg = "Got empty response from DUT"
                raise ReadFailedException(channel.connAlias, Exception(errMsg))
            else:  # For backward compatibility
                wait_for_more = False
            stream.close()

        # We must send it to remove some control characters that was sent at the end
        # channel.SendCommand("\025\010\010\010\010", AppendNewLine=False)
        channel.SendCommand("", AppendNewLine=True)
        channel.GetBufferTillPrompt(3, shellPrompt="Console#")

        return response

    def _get_raw_dut_response(self):
        # return self.__CleanDutCmdResponse(self._dut_response)
        return self._dut_response


