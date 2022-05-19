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
from Marvell.pytoolsinfra.DutCommands.DutCommandAbc.DutCommandAbc import DutCommandAbc
from future.utils import with_metaclass


class DutCommandExecutorAbc(with_metaclass(ABCMeta, object)):
    """
    Abstract base class for implementing a Dut Command Executor
    that handles sending commands to device and receiving output from device
    """

    @abstractmethod
    def execute(self, cmd, channel):
        """
        Algorithm for sending the command and process the response
        the pattern of this algo should be:
        1.serialize the command
        2.send the command on the command channel
        3.receive the response and process it for no errors
        4.deserialize the response in the command (fill the class data)
        :param cmd: DutCommandAbc_Old
        :param channel :ABCComWrapper
        :return: executor result
        :type cmd:DutCommandAbc
        :type channel:ABCComWrapper
        """
        pass

    @abstractmethod
    def validate_response(self, response, cmd):
        """
        validate the reponse
        :param response: the response received from dut
        :param cmd: the dut command class that is being executed
        :type cmd:DutCommandAbc
        :rtype: bool
        :return:
        """
        pass
