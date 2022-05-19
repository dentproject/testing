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

from builtins import bytes
from builtins import object

class sshWrapper(object):
    """
    it's a wrapper class , that wrapps the paramiko channel class
    """

    def __init__(self, host, port, username, password, timeout=10, **extraParameters):
        """
        :param host:
        :param port:
        :param username:
        :param password:
        :param timeout:
        :param extraParameters: dict of parameters for the 'invoke_shell' api {'width': <int>, 'height':<int>}
        """
        import paramiko

        if host is not None and isinstance(host, str):
            host = host.encode('utf-8')
        self._host = host

        if username is not None and isinstance(username, str):
            username = username.encode('utf-8')
        self._username = username
        self._shell_width = 80
        self._shell_height = 24
        if password is not None and isinstance(password, str):
            password = password.encode('utf-8')

        self._password = password
        if extraParameters.get("width"):
            self._shell_width = extraParameters["width"]
        if extraParameters.get("height"):
            self._shell_height = extraParameters["height"]

        self._port = port
        self._timeout = timeout
        self._client = paramiko.client.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
        # self._transport = None
        self._shell = None
        self._SSH_READ_BUFF = 4096

    def open(self):
        # import paramiko
        self._client.connect(hostname=self._host,
                             port=self._port,
                             username=self._username,
                             password=self._password,
                             look_for_keys=False,
                             timeout=self._timeout)
        # self._transport = paramiko.Transport((self._host, self._port))
        # self._transport.connect(username=self._username, password=self._password)
        self._shell = self._client.invoke_shell(width=self._shell_width, height=self._shell_height)  # self.print_data()
        self.read_all()  # to clear the buffer if there is something there

    def close(self):
        if self._client is not None:
            self._client.close()
            # self._transport.close()
            self._client = None
            # self._transport = None
            self._shell = None

    def set_timeout(self, timeout):
        self._timeout = timeout
        if self._shell is not None:
            self._shell.settimeout(self._timeout)

    def write(self, cmd):
        if self._shell:
            return self._shell.send(cmd)  # else:  #     print("Shell not opened.")

    def read_until(self, prompt):
        import time
        import select
        line = bytearray()
        if self._shell:
            lenterm = len(prompt)
            time_start = time.time()
            # t_end = time.time() + self._timeout
            reply_tuple = ([self._shell], [], [])
            args_tuple = reply_tuple
            if self._timeout is not None:
                args_tuple = args_tuple + (self._timeout,)

            while select.select(*args_tuple) == reply_tuple:
                c = self._shell.recv(1)
                if c:
                    line += c
                    if len(line) >= lenterm and line[-lenterm:] == prompt:
                        break

                if self._timeout is not None:
                    elapsed = time.time() - time_start
                    if elapsed >= self._timeout:
                        break
                    args_tuple = reply_tuple + (self._timeout - elapsed,)

        return bytes(line)

    def read(self, nbyts):
        import time
        import select
        ret_str = b""
        if self._shell:
            if self._timeout == 0:  # Read all in buffer
                while self._shell.recv_ready() and len(ret_str) < nbyts:
                    ret_str += self._shell.recv(nbyts - len(ret_str))
            else:
                time_start = time.time()
                reply_tuple = ([self._shell], [], [])
                args_tuple = reply_tuple
                if self._timeout is not None:
                    args_tuple = args_tuple + (self._timeout,)

                while len(ret_str) < nbyts and select.select(*args_tuple) == reply_tuple:
                    ret_str += self._shell.recv(nbyts - len(ret_str))
                    if self._timeout is not None:
                        elapsed = time.time() - time_start
                        if elapsed >= self._timeout:
                            break
                        args_tuple = reply_tuple + (self._timeout - elapsed,)

        return ret_str

    def read_all(self):
        ret_str = b""
        if self._shell:
            while self._shell.recv_ready():
                ret_str += self._shell.recv(self._SSH_READ_BUFF)

        return ret_str
