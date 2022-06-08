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
from .serialWrapper import *
from ..CommunicationExceptions.Exceptions import *
from ..PyCommunicationAlgoLayer.ABCCommunication import *
# === Model for Base Communication Layer ===

# === Serial ===


class serialComm(ABCCommunication):
    """
    it's a derived class , that inherits and implements [[ABCCommunication.py]]
    """
    def __init__(self, port, prompt="->", baudrate=115200, timeout=3, rtscts=False, dsrdtr=False):
        self._connection_name = "Serial"
        self._serial = serialWrapper()
        self._serial.baudrate = baudrate
        self._serial.timeout = timeout

        if prompt is not None and isinstance(prompt, str):
            prompt = prompt.encode('utf-8')

        self._prompt = prompt
        self._serial.port = port
        self._serial.rtscts = rtscts
        self._serial.dsrdtr = dsrdtr
        self._serial.break_condition = True

        self.is_connected = False


    def Connect(self):

        """\
        Open port with current settings. This may throw a BaseCommException
        if the port cannot be opened.
        """

        if self.is_connected is False:
            try:
                self._serial.open()
                self.is_connected = True
                self._serial.flushInput()
                self._serial.flushOutput()
            except SerialException as e:
                raise ConnectionFailedException(self._connection_name, "", e)

    def Disconnect(self):

        """Close port ,This may throw a BaseCommException
        if the port cannot be closed.
        """

        if self.is_connected is True:
            try:
                self._serial.close()
                self.is_connected = False
            except Exception as e:
                raise DisconnectFailedException(self._connection_name, e)

    def Write(self, command):

        """Output the given string over the serial port.
        This may throw a BaseCommException
        if the port cannot be opened.
        """
        if isinstance(command, str):
            command = command.encode('utf-8')

        if self.is_connected is True:
            try:
                bytes_num = self._serial.write(command)
                return bytes_num
            except Exception as e:
                raise WriteFailedException(self._connection_name, e)

    def Read(self, prompt=None, timeout=None, max_bytes=4096):

        """\
        Read until a termination sequence is found ('if prompt supported), the size
        is exceeded or until timeout occurs.
        This may throw a BaseCommException if the port cannot be opened.
        """
        if prompt is not None and not isinstance(prompt, bytes):
            prompt = prompt.encode('utf-8')

        if self.is_connected is True:
            try:
                data = b''
                if prompt is not None:
                    if timeout is not None:
                        # function call
                        self._serial.timeout = timeout
                    else:
                        """
                        longTime -> this to have same behavior with telnet - discuss with Chaim and Assaf
                        """
                        self._serial.timeout = sys.maxsize #long time , wait untill prompt

                    data = self._serial.read_until(terminator=prompt)
                    return data

                if timeout is not None:
                    data = b""
                    # Read all available bytes until max_bytes
                    if timeout != 0:
                        self._serial._timeout = 0
                        data = self._serial.read(size=max_bytes)

                    self._serial.timeout = timeout
                    # if bytes requested already readed , don't read more , else read the rest
                    if max_bytes > len(data):
                        data += self._serial.read(size=max_bytes - len(data))

                    return data

                data = self._serial.read_all()
                return data
            except Exception as e:
                raise ReadFailedException(self._connection_name, e)
