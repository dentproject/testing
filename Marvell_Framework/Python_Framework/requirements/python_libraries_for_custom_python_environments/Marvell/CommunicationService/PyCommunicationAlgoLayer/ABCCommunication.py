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
from future.utils import with_metaclass

# === Basic Communication Layer ===

"""
This is an abstract class that define all the basic functions for our GCS application-
    Basic Layer API

this class is a base class for serial and telnet clasees:

1. **serialComm** - serial communication , see <a href="../PyBaseLayer/serialComm.html">serial</a>
2. **telnetComm** - telnet communication , see <a href="../PyBaseLayer/telnetComm.html">telnet</a>

None : for future basic communication , implement this API , add the type to the factory [[ChannelFactory]]

"""


class ABCCommunication(with_metaclass(ABCMeta, object)):
    do_reconnect = True

    def __init__(self):
        raise NotImplementedError('ERROR: Cant instantiate abstract class')

    @abstractmethod
    def Connect(self):
        """Opened port and Set communication parameters"""
        pass

    @abstractmethod
    def Disconnect(self):
        """Close port"""
        pass

    @abstractmethod
    def Read(self, prompt=None, timeout=None, max_bytes=4096):
        """Read all bytes from the  port."""
        pass

    @abstractmethod
    def Write(self, data):
        """Output the given string over the port."""
        pass