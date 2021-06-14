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

from pypacker import pypacker

MPLS_LABEL_MASK = 0xfffff000
MPLS_QOS_MASK = 0x00000e00
MPLS_TTL_MASK = 0x000000ff
MPLS_STACK_BOTTOM_MASK = 0x0100
MPLS_LABEL_SHIFT = 12
MPLS_QOS_SHIFT = 9
MPLS_TTL_SHIFT = 0
MPLS_STACK_BOTTOM_SHIFT = 8

class MPLS(pypacker.Packet):

    __hdr__= (
        ("label_flag_ttl","I",64),
    )

    def __get_label(self):
        return self.label_flag_ttl >> MPLS_LABEL_SHIFT

    def __set_label(self, value):
        self.label_flag_ttl = (self.label_flag_ttl & ~MPLS_LABEL_MASK) | (value << MPLS_LABEL_SHIFT)
    label = property(__get_label, __set_label)

    def __get_stack_bottom(self):
        return (self.label_flag_ttl >> MPLS_STACK_BOTTOM_SHIFT) & 1

    def __set_stack_bottom(self, value):
        self.label_flag_ttl = self.label_flag_ttl & ~MPLS_STACK_BOTTOM_MASK | (value << MPLS_STACK_BOTTOM_SHIFT)
    bottom_stack = property(__get_stack_bottom, __set_stack_bottom)

    def __get_ttl(self):
        return self.label_flag_ttl & MPLS_TTL_MASK

    def __set_ttl(self, value):
        self.label_flag_ttl = (self.label_flag_ttl & ~MPLS_TTL_MASK) | value
    ttl = property(__get_ttl, __set_ttl)


    def __get_exp(self):
        return self.label_flag_ttl >> MPLS_QOS_SHIFT

    def __set_exp(self, value):
        self.label_flag_ttl = (self.label_flag_ttl & ~MPLS_QOS_MASK) | (value << MPLS_QOS_SHIFT)
    exp = property(__get_exp, __set_exp)
