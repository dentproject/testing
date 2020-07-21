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

from Marvell.pytoolsinfra.SysEventManager.BaseSysEventData import BaseSysEventData


class ExceptionEventData(BaseSysEventData):
    def __init__(self, sender_name, exception_object, channel, api_data=None, cmd_str=None):
        BaseSysEventData.__init__(self, sender_name)
        self.exception_object = exception_object
        self.channel = channel
        self.api_data = api_data
        self.cmd_str = cmd_str

    def __str__(self):
        return "Sender = {}, Error message = {}, api_data = {},cmd_str = {}".format(self.sender_name,
                                                                                    str(self.exception_object),
                                                                                    self.api_data,
                                                                                    self.cmd_str)

