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
from __future__ import absolute_import
from builtins import bytes
from builtins import str
from builtins import range
from future.utils import PY3
import socket
from ..CommunicationExceptions.Exceptions import *
from .telnetLibWrapper import telnetLibWrapper
from ..PyCommunicationAlgoLayer.ABCCommunication import *
from time import sleep
# import re
DEFAULT_TELNET_PORT = 23


# class myMatchObject(object):
#     """
#     Comparison help class for improving the read operation
#     """
#     _s=''
#     def __init__(self,s):
#         self._s = s
#     def group(self,group=0):
#         if group > 1:
#             return None
#         return self._s
#     def start(self,group=0):
#         if group > 1:
#             return None
#         return 0
#     def end(self,group=0):
#         if group > 1:
#             return None
#         return len(self._s)
#
# class matchByte(object):
#     def search(self, s, flags=0):
#         if s == '':
#             return None
#         return myMatchObject(s)


# === Model for Base Communication Layer ===

# === Telnet ===
"""
it's a derived class , that inherits and implements [[ABCCommunication.py]]
"""
#socket._GLOBAL_DEFAULT_TIMEOUT
class telnetComm(ABCCommunication):

    def __init__(self, host=None, port=DEFAULT_TELNET_PORT, timeout=5, uname=None, password=None, **extraParameters):

        self._connection_name = "Telnet"
        """Initialize class with given parameters and/or default values"""
        self._telnet = None
        self.m_host = host
        self.m_port = port
        self.m_timeout = timeout
        self.m_userName = uname
        self.m_password = password
        self.is_connected = False

        self.retry_connect = True
        self.nums_of_retries = 3
        self.timeout_between_retries = 5

        if extraParameters.get("retry_connect") is not None:
            self.retry_connect = extraParameters["retry_connect"]
        if extraParameters.get("timeout_between_retries") is not None:
            self.timeout_between_retries = extraParameters["timeout_between_retries"]
        if extraParameters.get("nums_of_retries") is not None:
            self.nums_of_retries = extraParameters["nums_of_retries"]

    def Connect(self):
        """Connect to a host.
        This may throw a BaseCommException ,if the port cannot be opened or ip
        address not supported
        """
        if self.is_connected is False:

            if self.m_host is None:
                err = "telnet Connect failed !! , IP Address not supported ."
                raise ConnectionFailedException(self._connection_name, err)

            nums_of_retries = self.nums_of_retries if self.retry_connect else 1
            time_out_retries = self.timeout_between_retries
            for i in range(nums_of_retries):
                try:
                    #self._telnet.open(self._telnet.host, self._telnet.port, time_out_retries[i])
                    # self._telnet = telnetlib.Telnet(self.m_host, self.m_port, time_out_retries[i])
                    self._telnet = telnetLibWrapper(self.m_host, self.m_port, time_out_retries)

                    self.is_connected = True
                except socket.timeout as e:  # the connect timedout we will try again
                    if i == (nums_of_retries - 1):
                        err = "failed to connect after " + str(nums_of_retries) + " retries\n"
                        raise ConnectionFailedException(self._connection_name, err, e)
                    else:
                        print ("telnetComm.Connect() failed on try number " + str(i + 1) +
                               "try connection ...")
                        continue
                except socket.error as e:  # connection refused we will wait till the next retry
                    if i == (nums_of_retries - 1):
                        err = "failed to connect after " + str(nums_of_retries) + " retries\n"
                        raise ConnectionFailedException(self._connection_name, err, e)
                    else:
                        print ("telnetComm.Connect() failed on try number " + str(i + 1) +
                               "try connection ...")
                        print ("waiting 5 seconds before retry")
                        sleep(5)
                        continue
                except Exception as e:
                    if i == (nums_of_retries - 1):
                        err = "failed to connect after " + str(nums_of_retries) + " retries\n"
                        raise ConnectionFailedException(self._connection_name, err, e)
                    else:
                        print ("telnetComm.Connect() failed on try number " + str(i + 1) +
                              "Due to" + str(e) + "try connection ...")
                        continue
                break

    def Disconnect(self):

        """Close the connection.This may throw a BaseCommException
        if the port cannot be closed.
        """
        if self.is_connected is True:
            try:
                self._telnet.close()
                self.is_connected = False
            except Exception as e:
                raise DisconnectFailedException(self._connection_name, e)

    def Write(self, data):
        """Write a string to the socket, doubling any IAC characters.
        Can block if the connection is blocked.  May raise
        BaseCommException if socket failed.
        """
        if isinstance(data, str):
            data = data.encode('utf-8')

        if self.is_connected is True:
            try:
                #ret = self._telnet.sock.sendall(IAC + NOP)
                # sock = self._telnet.get_socket()
                # if not self.is_still_connected():
                #     raise socket.error()
                self._telnet.write(data)
                return len(data)
                # print (socket._GLOBAL_DEFAULT_TIMEOUT)
                # print (self.m_timeout)
                # x=5
            except socket.error: #networking disconnection-> reconnect
                self._reconnect()

                # reconnect succeeded now we will try to write the data
                try:
                    self._telnet.write(data)
                    return len(data)
                except Exception as e:
                    raise WriteFailedException(self._connection_name, e)

            # The write was failed
            except Exception as e:
                raise WriteFailedException(self._connection_name, e)

    def Read(self, prompt=None, timeout=None, max_bytes=4096):
        """
        Read until a given string is encountered or until timeout.
        When no match is found, return whatever is available instead,
        possibly the empty string.  Raise EOFError if the connection
        is closed and no cooked data is available.May raise
        BaseCommException if cant read buffer
        """
        if prompt is not None and isinstance(prompt, str):
            prompt = prompt.encode('utf-8')

        readfunc = ''
        data = b''
        if self.is_connected is True:
            try:

                if prompt is not None:
                    if timeout is not None:
                        self._telnet.timeout = timeout

                    readfunc = 'read_until'
                    data = self._telnet.read_until(prompt, timeout)
                    return data

                if timeout is not None:
                    self._telnet.timeout = timeout

                    """ read all available data """
                    if self._telnet.timeout == 0: # read all available data
                        data = self._telnet.read_very_eager()

                        return data

                    """
                    if buffer content > requested size => return requested size until timeout
                    if buffer content < requested size => return buffer content until timeout
                    """
                    re = r'^(\s|.){' + str(max_bytes) + '}'
                    if PY3:
                        re = bytes(re, 'utf-8')
                    (i, m, data) = self._telnet.expect([re], timeout)

                    return data

                data = self._telnet.read_very_eager()
                return data

            except socket.error: #networking disconnection-> reconnect
                self._handle_exception(readfunc, prompt, timeout)

            except EOFError:
                self._handle_exception(readfunc, prompt, timeout)

            # The Read was failed
            except Exception as e:
                raise ReadFailedException(self._connection_name, e)

    def _handle_exception(self, readfunc, prompt, timeout):
        self._reconnect()

        # reconnect succeeded now we will try to read the data
        try:
            if readfunc == 'read_until':
                return self._telnet.read_until(prompt, timeout)

            return self._telnet.read_very_eager()
        except Exception as e:
            raise ReadFailedException(self._connection_name, e)

    def _reconnect(self):
        if not self.do_reconnect:
            raise ConnectionLostException(self._connection_name)

        try:
            sleep(5)
            self.is_connected = False
            self.Connect()
        except Exception as e:
            raise ReconnectionFailedException(self._connection_name, e)

    # def is_still_connected(self):
    #
    #     # s = self._telnet.get_socket()
    #     # s.sendall('/n')
    #     # data = s.recv(16)
    #     # if not data:
    #     #     return False
    #     return True
