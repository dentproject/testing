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

from enum import Enum
from PyInfraCommon.ExternalImports.Communication import PyTelnetComWrapper,PySerialComWrapper,PySSHComWrapper,PyBaseComWrapper
from PyInfraCommon.Globals.Logger.GlobalTestLogger import GlobalLogger


class ConnectionType(Enum):
    UNKNOWN = -1
    SERIAL = 0
    TELNET = 1
    SSH = 2

class ConnectionData(object):
    """
    builds connection data structure based on relevant connection type
    this structure is uses by communication lib factory on Connect and thus has different attributes
    """
    class kv(object):
        def __init__(self):
            self.key = ""
            self.value = ""

    def __init__(self ,connection_type=ConnectionType.TELNET):
        if connection_type is ConnectionType.SERIAL:
            self.com_number = self.kv()
            self.baudrate = self.kv()
        elif connection_type in (ConnectionType.SSH,ConnectionType.TELNET):
            self.ip_address = self.kv()
            self.uname = self.kv()
            self.password = self.kv()
            self.timeout = self.kv()
            self.port = self.kv()



def InitChannelByType(connection_type = ConnectionType.UNKNOWN,
                      ip_address=None,port=None,user=None,
                      password=None,timeout=None,baudrate=115200,allow_multiple_connection=True):
    """
    create and return communication channel instance based on connection type info
    :param connection_type:the communication channel type
    :type connection_type:ConnectionType
    :param ip_address:
    :type ip_address:str
    :param port:tcp port or com port number (based on connection type)
    :type port:int
    :param user:username for ssh connections
    :type user:str
    :param password: password for ssh connection
    :type password:str
    :param timeout:timeout value for channel
    :type timeout:int
    :param baudrate:for serial connection
    :type baudrate:int
    :param allow_multiple_connection: if True will allow connecting to the same host + port in parallel, else will use same connection from all instances
    :type allow_multiple_connection:bool
    :return:the relevant Channel Instance
    :rtype:PyBaseComWrapper
    """
    connection_data = ConnectionData(connection_type)
    channel = None
    if connection_type is ConnectionType.SERIAL:
        connection_data.baudrate.value = baudrate
        connection_data.port.value = port
        channel = PySerialComWrapper(connection_data)
    elif connection_type in (ConnectionType.TELNET,ConnectionType.SSH):
        connection_data.port.value = port  # SSH has fixed port 22
        connection_data.ip_address.value = ip_address
        connection_data.timeout.value = timeout
        connection_data.uname.value = user
        connection_data.password.value = password
        if isinstance(password,int):
            connection_data.password.value = str(password)
        channel = PyTelnetComWrapper(connection_data) if connection_type is ConnectionType.TELNET else PySSHComWrapper(connection_data)
        channel.generate_uid = allow_multiple_connection
    channel.testlogger = GlobalLogger.logger
    return channel


