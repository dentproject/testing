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

import logging


class SysLogFormatter(logging.Formatter):
    """
    Adding the source on the message name to each record
    """

    def __init__(self, source_name, fmt):
        super(SysLogFormatter, self).__init__(fmt)
        self._source_name = source_name

    def format(self, record):

        message = record.getMessage()
        ret_msg = super(SysLogFormatter, self).format(record)
        index_of_start_msg = ret_msg.index(message)
        new_msg = ret_msg[:index_of_start_msg] + self._source_name + ":" + ret_msg[index_of_start_msg:]

        return new_msg
