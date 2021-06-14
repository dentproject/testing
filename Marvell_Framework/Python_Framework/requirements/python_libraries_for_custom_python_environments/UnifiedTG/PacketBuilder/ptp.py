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

import binascii

from pypacker import pypacker
from UnifiedTG.PacketBuilder.pb_helper import bitter


class PTP_header(pypacker.Packet):

    __hdr__= (
        ("transport_mType", "B", 0),
        ("reserved1_vPTP", "B", 2),
        ("messageLength", "H", 0),
        ("domainNumber", "B", 0),
        ("reserved2", "B", 0),
        ("Flags", "H", 0),
        ("correctionField", "Q", 0),
        ("reserved3", "I", 0),
        ("sourcePortIdentifyHi", "H", 0),
        ("sourcePortIdentify", "Q", 0),
        ("sequenceID", "H", 0),
        ("controlField", "B", 0),
        ("logMessageInterval", "B", 0x7F),
    )

    def __get_transport_command(self):
        return bitter(4, 4).get_calc(self.transport_mType)
    def __set_transport_command(self, value):
        self.transport_mType = bitter(4, 4).set_calc(self.transport_mType,value)
    transport = property(__get_transport_command, __set_transport_command)

    def __get_messageType_command(self):
        return bitter(4, 0).get_calc(self.transport_mType)
    def __set_messageType_command(self, value):
        self.transport_mType = bitter(4, 0).set_calc(self.transport_mType,value)
    messageType = property(__get_messageType_command, __set_messageType_command)

    def __get_reserved1_command(self):
        return bitter(4, 4).get_calc(self.reserved1_vPTP)
    def __set_reserved1_command(self, value):
        self.reserved1_vPTP = bitter(4, 4).set_calc(self.reserved1_vPTP,value)
    reserved1 = property(__get_reserved1_command, __set_reserved1_command)

    def __get_versionPTP_command(self):
        return bitter(4, 0).get_calc(self.reserved1_vPTP)
    def __set_versionPTP_command(self, value):
        self.reserved1_vPTP = bitter(4, 0).set_calc(self.reserved1_vPTP,value)
    versionPTP = property(__get_versionPTP_command, __set_versionPTP_command)



# obj = PTP_header()
# obj.transport = 4
# obj.messageType = 6
# obj.versionPTP = 2
# obj.domainNumber = 3
# obj.reserved2 = 5
# obj.Flags = 4
# obj.correctionField = 0x666
# obj.reserved3 = 7
# obj.sourcePortIdentify = 0x888
# obj.sequenceID = 9
# obj.logMessageInterval = 7
#
# bin_headers2 = binascii.hexlify(obj.bin()).decode('utf-8')
# sz = len(bin_headers2)/2
# print()