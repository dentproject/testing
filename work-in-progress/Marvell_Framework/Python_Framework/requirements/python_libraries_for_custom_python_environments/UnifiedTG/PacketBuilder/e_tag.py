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
from UnifiedTG.PacketBuilder.pb_helper import bitter

class eTag(pypacker.Packet):

    __hdr__= (
        ("PCP","H",0),#e-pcp(3 bits),e-dei(1 bit),ingres_e_cid_base(12 bits)
        ("re_GRP", "H", 0),#re(2 bits),GRP(2 bits),e_cid_base(12 bits)
        ("Ingress_E_CID_ext", "B", 0),
        ("E_CID_ext", "B", 0),
    )

    def __get_epcp(self):
        return bitter(3, 13).get_calc(self.PCP)
    def __set_epcp(self, value):
        self.PCP = bitter(3, 13).set_calc(self.PCP, value)
    e_pcp = property(__get_epcp, __set_epcp)

    def __get_edei(self):
        return bitter(1, 12).get_calc(self.PCP)
    def __set_edei(self, value):
        self.PCP = bitter(1, 12).set_calc(self.PCP, value)
    e_dei = property(__get_edei, __set_edei)

    def __get_ingres_e_cid_base(self):
        return bitter(12, 0).get_calc(self.PCP)
    def __set_ingres_e_cid_base(self, value):
        self.PCP = bitter(12, 0).set_calc(self.PCP, value)
    ingres_e_cid_base = property(__get_ingres_e_cid_base, __set_ingres_e_cid_base)
#####################################
    def __get_re(self):
        return bitter(2, 14).get_calc(self.re_GRP)
    def __set_re(self, value):
        self.re_GRP = bitter(2, 14).set_calc(self.re_GRP, value)
    Re = property(__get_re, __set_re)

    def __get_grp(self):
        return bitter(2, 12).get_calc(self.re_GRP)
    def __set_grp(self, value):
        self.re_GRP = bitter(2, 12).set_calc(self.re_GRP, value)
    GRP = property(__get_grp, __set_grp)

    def __get_e_cid_base(self):
        return bitter(12, 0).get_calc(self.re_GRP)
    def __set_e_cid_base(self, value):
        self.re_GRP = bitter(12, 0).set_calc(self.re_GRP, value)
    e_cid_base = property(__get_e_cid_base, __set_e_cid_base)



