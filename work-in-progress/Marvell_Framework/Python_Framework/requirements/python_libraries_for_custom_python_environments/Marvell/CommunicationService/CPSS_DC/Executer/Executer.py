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

from __future__ import print_function

from builtins import object
import os
import sys
import re
import json

from Common.Types import *
from HighCommunicationLayer.CommunicationManagement import *

class Executer(object):

    @staticmethod
    def is_json_valid(myjson):
        try:
            json_object = json.loads(myjson)
        except ValueError as e:
            return False
        return True

    @staticmethod
    def execute(alias, serializer):
        request = 'execGenWrapper'
        CommunicationManagement.SendTerminalString(alias, request, False)
        print(request)
        request = serializer.Serialize()
        response = CommunicationManagement.SendCommandAndGetBufferTillPrompt(alias, request, 10)
        print(response)
        result = response[response.find('execGenWrapper') + len('execGenWrapper'):response.rfind('Console#')]
        return serializer.Deserialize(result.strip())