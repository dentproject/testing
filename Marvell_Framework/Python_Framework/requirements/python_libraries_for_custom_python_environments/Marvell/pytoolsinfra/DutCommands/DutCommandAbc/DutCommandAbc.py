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
from abc import *
from future.utils import with_metaclass


class DutCommandAbc(with_metaclass(ABCMeta, object)):
    """
    Abstract class the defines a Dut Command
    1.all types of bases deriving from it should implement execute()
    2.all command deriving from their base should implement serialize() and deserialize()
    3.all the commands are actually implemented in the Validation Group Test Project
    """

    @abstractmethod
    def __init__(self):
        raise NotImplementedError('ERROR: Cant instantiate abstract class')

    @abstractmethod
    def _serialize(self):
        """
        this method meant for sending
        the command to the Dut by serializing it from the class
        """
        pass

    @abstractmethod
    def _deserialize(self, response):
        """
        this method meant for processing the received response from the Dut
        and deserialize the data to the class
        """
        pass

    @abstractmethod
    def _execute(self,channel):
        """
        this method should pass it self to the executor class and ask to be executed
        :param channel:ABCComWrapper
        :type channel:ABCComWrapper
        :return:
        """