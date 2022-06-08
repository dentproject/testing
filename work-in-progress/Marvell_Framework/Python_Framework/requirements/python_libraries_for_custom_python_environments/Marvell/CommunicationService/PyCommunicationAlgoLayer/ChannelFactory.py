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
from builtins import object
from ..PyBaseLayer.serialComm import *
from ..PyBaseLayer.telnetComm import *
from ..PyBaseLayer.sshComm import *
from ..Common.Types import *
import uuid

# === Python Communication  Chanel Factory ===

class ChannelFactory(object):
    """Factory to create python communication channel , PySerial/PyTelnet channel"""
    @staticmethod
    def Create(commType, port, ipAddr, prompt,uname, password, **extraParameters):

        if port is not None and isinstance(port, str):
            port = port.encode('utf-8')

        if ipAddr is not None and isinstance(ipAddr, str):
            ipAddr = ipAddr.encode('utf-8')

        if uname is not None and isinstance(uname, str):
            uname = uname.encode('utf-8')


        if commType.value == CommunicationType.PySerial.value:
            com_port = "COM" + str(port)
            return com_port, serialComm(com_port, prompt)

        if commType.value == CommunicationType.PyTelnet.value:
            if extraParameters.get("uid") and extraParameters["uid"]:
                aliasipAddr = str(ipAddr) + ":" + str(port) + ":" + str(uuid.uuid4())
            else:
                aliasipAddr = str(ipAddr) + ":" + str(port)
            return aliasipAddr, telnetComm(ipAddr, port, uname=uname, password=password, **extraParameters)

        if commType.value == CommunicationType.PySSH.value:
            if extraParameters.get("uid") and extraParameters["uid"]:
                aliasipAddr = str(ipAddr) + ":" + uname.decode('utf-8') + ":" + str(port) + ":" + str(uuid.uuid4())
            else:
                aliasipAddr = str(ipAddr) + ":" + uname.decode('utf-8') + ":" + str(port)
            return aliasipAddr, sshComm(host=ipAddr, port=port, username=uname, password=password, **extraParameters)


