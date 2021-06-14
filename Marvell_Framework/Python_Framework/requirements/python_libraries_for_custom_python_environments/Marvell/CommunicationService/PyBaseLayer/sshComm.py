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

from __future__ import absolute_import
from .sshWrapper import *
import sys
from ..CommunicationExceptions.Exceptions import *
from ..PyCommunicationAlgoLayer.ABCCommunication import *
import socket
from time import sleep
# === Model for Base Communication Layer ===

# === SSH ===
DEFAULT_SSH_PORT = 22


class sshComm(ABCCommunication):
    """
    it's a derived class , that inherits and implements [[ABCCommunication.py]]
    """
    def __init__(self, host=None, port=DEFAULT_SSH_PORT, username=None, password=None, timeout=10, **extraParameters):
        self._connection_name = "SSH"
        self._ssh_channel = sshWrapper(host, port, username, password, timeout, **extraParameters)
        self.is_connected = False

    def Connect(self):

        """\
        Open port with current settings. This may throw a BaseCommException
        if the port cannot be opened.
        """

        if self.is_connected is False:
            try:
                self._ssh_channel.open()
                self.is_connected = True
            except Exception as e:
                raise ConnectionFailedException(self._connection_name, "", e)

    def Disconnect(self):

        """Close port ,This may throw a BaseCommException
        if the port cannot be closed.
        """

        if self.is_connected is True:
            try:
                self._ssh_channel.close()
                self.is_connected = False
            except Exception as e:
                raise DisconnectFailedException(self._connection_name, e)

    def Write(self, command):

        """Output the given string over the SSH port.
        This may throw a BaseCommException
        if the port cannot be opened.
        """
        if isinstance(command, str):
            command = command.encode('utf-8')

        if self.is_connected is True:
            try:
                bytes_num = self._ssh_channel.write(command)
                return bytes_num
            except socket.error:  # networking disconnection-> reconnect
                self._reconnect()

                # reconnect succeeded now we will try to write the data
                try:
                    bytes_num = self._ssh_channel.write(command)
                    return bytes_num
                except Exception as e:
                    raise WriteFailedException(self._connection_name, e)

            # The write was failed
            except Exception as e:
                raise WriteFailedException(self._connection_name, e)

    def Read(self, prompt=None, timeout=None, max_bytes=4096):

        """\
        Read until a termination sequence is found ('if prompt supported), the size
        is exceeded or until timeout occurs.
        This may throw a BaseCommException if the port cannot be opened.
        """
        if prompt is not None and isinstance(prompt, str):
            prompt = prompt.encode('utf-8')

        readfunc = ''
        if self.is_connected is True:
            try:
                data = ''
                if prompt is not None:
                    if timeout is not None:
                        self._ssh_channel.set_timeout(timeout)
                    else:
                        """
                        longTime -> this to have same behavior with telnet - discuss with Chaim and Assaf
                        """
                        self._ssh_channel.set_timeout(sys.maxsize) #long time , wait untill prompt

                    readfunc = 'read_until'
                    data = self._ssh_channel.read_until(prompt=prompt)
                    return data

                if timeout is not None:
                    data = b""
                    # Read all available bytes until max_bytes
                    if timeout != 0:
                        self._ssh_channel.set_timeout(0)
                        data = self._ssh_channel.read(nbyts=max_bytes)

                    self._ssh_channel.set_timeout(timeout)
                    # if bytes requested already readed , don't read more , else read the rest
                    if max_bytes > len(data):
                        data += self._ssh_channel.read(nbyts=max_bytes - len(data))

                    return data

                data = self._ssh_channel.read_all()
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
                return self._ssh_channel.read_until(prompt=prompt)

            return self._ssh_channel.read_all()
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