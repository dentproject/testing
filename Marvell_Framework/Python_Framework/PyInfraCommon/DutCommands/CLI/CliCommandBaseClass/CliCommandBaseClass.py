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

from PyInfraCommon.ExternalImports.DutCommands import DutCommandAbc,DutCommandExecutorAbc
from PyInfraCommon.ExternalImports.Communication import PyBaseComWrapper
from ....DutCommands.DutCommandsEnums.DutCommandActionTypes import DutCommandActionTypes
from ....DutCommands.DutCommandsEnums.DutCommandTypes import DutCommandType


class CliCommandBase(DutCommandAbc):
    """
    Base Class for implementing all CLI Based Commands
    this is still a partial class and all Commands Deriving from It should implement
    1.serialize()
    2.desrialize()
    :type DutChannel: PyBaseComWrapper
    :type _DutChannel: PyBaseComWrapper
    :type _executor: DutCommandExecutorAbc

    """
    def __init__(self):
        """
        :param DutChannel: a Channel for Communication with the Dut
        """
        self._CommandType = DutCommandType.CLI
        self._CommandActionType = DutCommandActionTypes.Uninitilized
        self._sentCmd = ""
        self._ContextName = ""
        self._executor = None
        self.result = True
        self.result_msg = ""
        self._DutChannel = None
        self._strip_response_new_line = True

    @property
    def DutChannel(self):
        return self._DutChannel

    @DutChannel.setter
    def DutChannel(self,channel):
        self._DutChannel = channel

    def _execute(self , channel):
        """
        this method should pass it self to the executor class and ask to be executed
        :param channel: the dut channel
        :type channel:PyBaseComWrapper
        :return:
        """
        self._executor.execute(self , channel)