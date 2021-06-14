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

import array
import struct

from pypacker import pypacker, triggerlist,checksum
from pypacker.pypacker import FIELD_FLAG_AUTOUPDATE, FIELD_FLAG_IS_TYPEFIELD

LEFT_BIT = 0x8000
START_SHIFT = 0xF
GRE_CHECKSUM_POS = 0
GRE_KEY_POS = 2
GRE_SEQ_POS = 3
GRE_VER_POS = 0xF

GRE_CHECKSUM_SHIFT = START_SHIFT
GRE_CHECKSUM_MASK = LEFT_BIT
GRE_KEY_SHIFT = START_SHIFT-GRE_KEY_POS
GRE_KEY_MASK = LEFT_BIT >> GRE_KEY_POS
GRE_SEQ_SHIFT = START_SHIFT-GRE_SEQ_POS
GRE_SEQ_MASK = LEFT_BIT >> GRE_SEQ_POS
GRE_VER_SHIFT = START_SHIFT-GRE_VER_POS
GRE_VER_MASK = 0x111



class GRE(pypacker.Packet):

    __hdr__= (
        ("gre_flags","H",0,FIELD_FLAG_AUTOUPDATE),
        ("protocol_type", "H", 0x800,FIELD_FLAG_AUTOUPDATE),
        ("opts", None, triggerlist.TriggerList)
    )

    def __set_checksum_bit(self, value):
        self.gre_flags = self.gre_flags & ~GRE_CHECKSUM_MASK | (value << GRE_CHECKSUM_SHIFT)
    checksum_bit = property(None, __set_checksum_bit)

    def __set_key_bit(self, value):
        self.gre_flags = self.gre_flags & ~GRE_KEY_MASK | (value << GRE_KEY_SHIFT)
    key_bit = property(None, __set_key_bit)

    def __set_sequence_bit(self, value):
        self.gre_flags = self.gre_flags & ~GRE_SEQ_MASK | (value << GRE_SEQ_SHIFT)
    sequence_bit = property(None, __set_sequence_bit)

    def __set_version_bit(self, value):
        self.gre_flags = self.gre_flags & ~GRE_VER_MASK | (value << GRE_VER_SHIFT)
    version_number = property(None, __set_version_bit)


# class GREOption(pypacker.Packet):
#     __hdr__ = (
#         ("data", "H", 0),
#     )

class GREOptionChecksum(pypacker.Packet):
    __hdr__ = (
        ("checksum", "H", 0),
    )

class GREOptionReserve_1(pypacker.Packet):
    __hdr__ = (
        ("reserve_1", "H", 0),
    )

class GREOptionOffset (pypacker.Packet):
    __hdr__ = (
        ("offset", "H", 0),
    )

class GREOptionKey(pypacker.Packet):
    __hdr__ = (
        ("key", "I", 0),
    )

class GREOptionSequence(pypacker.Packet):
    __hdr__ = (
        ("sequence", "I", 0),
    )
class GREOptionRouting(pypacker.Packet):
    __hdr__ = (
        ("routing ", "I", 0),
    )



