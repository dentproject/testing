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


class DsaTag_forward_4(pypacker.Packet):

    __hdr__= (
        ("word0", "I", 0),
    )

    def __get_tag_command(self):
        return bitter(2, 30).get_calc(self.word0)
    def __set_tag_command(self, value):
        self.word0 = bitter(2, 30).set_calc(self.word0,value)
    Tag_Command = property(__get_tag_command, __set_tag_command)

    def __get_Tag0_Src_Tagged(self):
        return bitter(1, 29).get_calc(self.word0)
    def __set_Tag0_Src_Tagged(self, value):
        self.word0 = bitter(1, 29).set_calc(self.word0, value)
    Tag0_Src_Tagged = property(__get_Tag0_Src_Tagged, __set_Tag0_Src_Tagged)

    def __get_Tag0_Src_Dev_4_0(self):
        return bitter(5, 24).get_calc(self.word0)
    def __set_Src_Dev_4_0(self, value):
        self.word0 = bitter(5, 24).set_calc(self.word0, value)
    Src_Dev_4_0 = property(__get_Tag0_Src_Dev_4_0, __set_Src_Dev_4_0)

    def __get_Src_Trunk_ePort_4_0(self):
        return bitter(5, 19).get_calc(self.word0)
    def __set_Src_Trunk_ePort_4_0(self, value):
        self.word0 = bitter(5, 19).set_calc(self.word0, value)
    Src_Trunk_ePort_4_0 = property(__get_Src_Trunk_ePort_4_0, __set_Src_Trunk_ePort_4_0)

    def __get_Src_Is_Trunk(self):
        return bitter(1, 18).get_calc(self.word0)
    def __set_Src_Is_Trunk(self, value):
        self.word0 = bitter(1, 18).set_calc(self.word0, value)
    Src_Is_Trunk = property(__get_Src_Is_Trunk, __set_Src_Is_Trunk)

    def __get_Hash_0(self):
        return bitter(1, 17).get_calc(self.word0)
    def __set_Hash_0(self, value):
        self.word0 = bitter(1, 17).set_calc(self.word0, value)
    Hash_0 = property(__get_Hash_0, __set_Hash_0)

    def __get_CFI(self):
        return bitter(1, 16).get_calc(self.word0)
    def __set_CFI(self, value):
        self.word0 = bitter(1, 16).set_calc(self.word0, value)
    CFI = property(__get_CFI, __set_CFI)

    def __get_UP(self):
        return bitter(3, 13).get_calc(self.word0)
    def __set_UP(self, value):
        self.word0 = bitter(3, 13).set_calc(self.word0, value)
    UP = property(__get_UP, __set_UP)

    def __get_w0_Extend(self):
        return bitter(1, 12).get_calc(self.word0)
    def __set_w0_Extend(self, value):
        self.word0 = bitter(1, 12).set_calc(self.word0, value)
    w0_Extend = property(__get_w0_Extend, __set_w0_Extend)

    def __get_eVLAN_11_0(self):
        return bitter(12, 0).get_calc(self.word0)
    def __set_eVLAN_11_0(self, value):
        self.word0 = bitter(12, 0).set_calc(self.word0, value)
    eVLAN_11_0 = property(__get_eVLAN_11_0, __set_eVLAN_11_0)

class DsaTag_forward_8(DsaTag_forward_4):
    __hdr__= (
        ("word0", "I", 0),
        ("word1", "I", 0),
    )

    def __get_w1_Extend(self):
        return bitter(1, 31).get_calc(self.word1)
    def __set_w1_Extend(self, value):
        self.word1 = bitter(1, 31).set_calc(self.word1, value)
    w1_Extend = property(__get_w1_Extend, __set_w1_Extend)

    def __get_Src_Trunk_ePort_6_5(self):
        return bitter(2, 29).get_calc(self.word1)
    def __set_Src_Trunk_ePort_6_5(self, value):
        self.word1 = bitter(2, 29).set_calc(self.word1, value)
    Src_Trunk_ePort_6_5 = property(__get_Src_Trunk_ePort_6_5, __set_Src_Trunk_ePort_6_5)

    def __get_Egress_Filter_Registered(self):
        return bitter(1, 28).get_calc(self.word1)
    def __set_Egress_Filter_Registered(self, value):
        self.word1 = bitter(1, 28).set_calc(self.word1, value)
    Egress_Filter_Registered = property(__get_Egress_Filter_Registered, __set_Egress_Filter_Registered)

    def __get_Drop_On_Source(self):
        return bitter(1, 27).get_calc(self.word1)
    def __set_Drop_On_Source(self, value):
        self.word1 = bitter(1, 27).set_calc(self.word1, value)
    Drop_On_Source = property(__get_Drop_On_Source, __set_Drop_On_Source)

    def __get_Packet_Is_Looped(self):
        return bitter(1, 26).get_calc(self.word1)
    def __set_Packet_Is_Looped(self, value):
        self.word1 = bitter(1, 26).set_calc(self.word1, value)
    Packet_Is_Looped = property(__get_Packet_Is_Looped, __set_Packet_Is_Looped)

    def __get_Routed(self):
        return bitter(1, 25).get_calc(self.word1)
    def __set_Routed(self, value):
        self.word1 = bitter(1, 25).set_calc(self.word1, value)
    Routed = property(__get_Routed, __set_Routed)

    def __get_Src_ID(self):
        return bitter(5, 20).get_calc(self.word1)
    def __set_Src_ID(self, value):
        self.word1 = bitter(5, 20).set_calc(self.word1, value)
    Src_ID = property(__get_Src_ID, __set_Src_ID)

    def __get_Global_QoS_Profile(self):
        return bitter(7, 13).get_calc(self.word1)
    def __set_Global_QoS_Profile(self, value):
        self.word1 = bitter(7, 13).set_calc(self.word1, value)
    Global_QoS_Profile = property(__get_Global_QoS_Profile, __set_Global_QoS_Profile)

    def __get_use_eVIDX(self):
        return bitter(1, 12).get_calc(self.word1)
    def __set_use_eVIDX(self, value):
        self.word1 = bitter(1, 12).set_calc(self.word1, value)
    use_eVIDX = property(__get_use_eVIDX, __set_use_eVIDX)

    def __get_eVIDX(self):
        return bitter(12, 0).get_calc(self.word1)
    def __set_eVIDX(self, value):
        self.word1 = bitter(12, 0).set_calc(self.word1, value)
    eVIDX_11_0 = property(__get_eVIDX, __set_eVIDX)

    def __get_Trg_Phy_Port(self):
        return bitter(7, 5).get_calc(self.word1)
    def __set_Trg_Phy_Port(self, value):
        self.word1 = bitter(7, 5).set_calc(self.word1, value)
    Trg_Phy_Port_6_0 = property(__get_Trg_Phy_Port, __set_Trg_Phy_Port)

    def __get_Trg_Dev(self):
        return bitter(5, 0).get_calc(self.word1)
    def __set_Trg_Dev(self, value):
        self.word1 = bitter(5, 0).set_calc(self.word1, value)
    Trg_Dev = property(__get_Trg_Dev, __set_Trg_Dev)

class DsaTag_forward_16(DsaTag_forward_8):
    __hdr__= (
        ("word0", "I", 0),
        ("word1", "I", 0),
        ("word2", "I", 0),
        ("word3", "I", 0),
    )

    def __get_w2_Extend(self):
        return bitter(1, 31).get_calc(self.word2)
    def __set_w2_Extend(self, value):
        self.word2 = bitter(1, 31).set_calc(self.word2, value)
    w2_Extend = property(__get_w2_Extend, __set_w2_Extend)

    def __get_Skip_FDB(self):
        return bitter(1, 30).get_calc(self.word2)
    def __set_Skip_FDB(self, value):
        self.word2 = bitter(1, 30).set_calc(self.word2, value)
    Skip_FDB = property(__get_Skip_FDB, __set_Skip_FDB)

    def __get_Is_Trg_Phy_Port_Valid(self):
        return bitter(1, 29).get_calc(self.word2)
    def __set_Is_Trg_Phy_Port_Valid(self, value):
        self.word2 = bitter(1, 29).set_calc(self.word2, value)
    Is_Trg_Phy_Port_Valid = property(__get_Is_Trg_Phy_Port_Valid, __set_Is_Trg_Phy_Port_Valid)

    def __get_Trg_Phy_Port_7(self):
        return bitter(1, 28).get_calc(self.word2)
    def __set_Trg_Phy_Port_7(self, value):
        self.word2 = bitter(1, 28).set_calc(self.word2, value)
    Trg_Phy_Port_7 = property(__get_Trg_Phy_Port_7, __set_Trg_Phy_Port_7)

    def __get_Src_ID_11_5(self):
        return bitter(7, 21).get_calc(self.word2)
    def __set_Src_ID_11_5(self, value):
        self.word2 = bitter(7, 21).set_calc(self.word2, value)
    Src_ID_11_5 = property(__get_Src_ID_11_5, __set_Src_ID_11_5)

    def __get_Hash_3_2(self):
        return bitter(2, 19).get_calc(self.word2)
    def __set_Hash_3_2(self, value):
        self.word2 = bitter(2, 19).set_calc(self.word2, value)
    Hash_3_2 = property(__get_Hash_3_2, __set_Hash_3_2)

    def __get_Src_Dev_9_5(self):
        return bitter(5, 14).get_calc(self.word2)
    def __set_Src_Dev_9_5(self, value):
        self.word2 = bitter(5, 14).set_calc(self.word2, value)
    Src_Dev_9_5 = property(__get_Src_Dev_9_5, __set_Src_Dev_9_5)

    def __get_Hash_1(self):
        return bitter(1, 13).get_calc(self.word2)
    def __set_Hash_1(self, value):
        self.word2 = bitter(1, 13).set_calc(self.word2, value)
    Hash_1 = property(__get_Hash_1, __set_Hash_1)

    def __get_Src_Trunk_ePort_11_7(self):
        return bitter(9, 3).get_calc(self.word2)
    def __set_Src_Trunk_ePort_11_7(self, value):
        self.word2 = bitter(9, 3).set_calc(self.word2, value)
    Src_Trunk_ePort_11_7 = property(__get_Src_Trunk_ePort_11_7, __set_Src_Trunk_ePort_11_7)

    def __get_TPID_Index(self):
        return bitter(3, 0).get_calc(self.word2)
    def __set_TPID_Index(self, value):
        self.word2 = bitter(3, 0).set_calc(self.word2, value)
    TPID_Index = property(__get_TPID_Index, __set_TPID_Index)

#word3
    def __get_w3_Extend(self):
        return bitter(1, 31).get_calc(self.word3)
    def __set_w3_Extend(self, value):
        self.word3 = bitter(1, 31).set_calc(self.word3, value)
    w3_Extend = property(__get_w3_Extend, __set_w3_Extend)

    def __get_eVLAN_15_12(self):
        return bitter(4, 27).get_calc(self.word3)
    def __set_eVLAN_15_12(self, value):
        self.word3 = bitter(4, 27).set_calc(self.word3, value)
    eVLAN_15_12 = property(__get_eVLAN_15_12, __set_eVLAN_15_12)

    def __get_Tag1_Src_Tagged(self):
        return bitter(1, 26).get_calc(self.word3)
    def __set_Tag1_Src_Tagged(self, value):
        self.word3 = bitter(1, 26).set_calc(self.word3, value)
    Tag1_Src_Tagged = property(__get_Tag1_Src_Tagged, __set_Tag1_Src_Tagged)

    def __get_Src_Tag0_IsOuter_Tag(self):
        return bitter(1, 25).get_calc(self.word3)
    def __set_Src_Tag0_IsOuter_Tag(self, value):
        self.word3 = bitter(1, 25).set_calc(self.word3, value)
    Src_Tag0_IsOuter_Tag = property(__get_Src_Tag0_IsOuter_Tag, __set_Src_Tag0_IsOuter_Tag)

    def __get_eVIDX_15_12(self):
        return bitter(4, 20).get_calc(self.word3)
    def __set_eVIDX_15_12(self, value):
        self.word3 = bitter(4, 20).set_calc(self.word3, value)
    eVIDX_15_12 = property(__get_eVIDX_15_12, __set_eVIDX_15_12)

    def __get_Orig_Src_Phy_Is_Trunk(self):
        return bitter(1, 19).get_calc(self.word3)
    def __set_Orig_Src_Phy_Is_Trunk(self, value):
        self.word3 = bitter(1, 19).set_calc(self.word3, value)
    Orig_Src_Phy_Is_Trunk = property(__get_Orig_Src_Phy_Is_Trunk, __set_Orig_Src_Phy_Is_Trunk)

    def __get_Orig_Src_Phy_Port_Trunk(self):
        return bitter(12, 7).get_calc(self.word3)
    def __set_Orig_Src_Phy_Port_Trunk(self, value):
        self.word3 = bitter(12, 7).set_calc(self.word3, value)
    Orig_Src_Phy_Port_Trunk = property(__get_Orig_Src_Phy_Port_Trunk, __set_Orig_Src_Phy_Port_Trunk)

    def __get_Phy_Src_MC_Filter_Enable(self):
        return bitter(1, 6).get_calc(self.word3)
    def __set_Phy_Src_MC_Filter_Enable(self, value):
        self.word3 = bitter(1, 6).set_calc(self.word3, value)
    Phy_Src_MC_Filter_Enable = property(__get_Phy_Src_MC_Filter_Enable, __set_Phy_Src_MC_Filter_Enable)

    def __get_Hash_5_4_vidx1(self):
        return bitter(2, 4).get_calc(self.word3)
    def __set_Hash_5_4_vidx1(self, value):
        self.word3 = bitter(2, 4).set_calc(self.word3, value)
    Hash_5_4_vidx1 = property(__get_Hash_5_4_vidx1, __set_Hash_5_4_vidx1)

    def __get_Trg_Phy_Port_9_8(self):
        return bitter(2, 23).get_calc(self.word3)
    def __set_Trg_Phy_Port_9_8(self, value):
        self.word3 = bitter(2, 23).set_calc(self.word3, value)
    Trg_Phy_Port_9_8 = property(__get_Trg_Phy_Port_9_8, __set_Trg_Phy_Port_9_8)

    def __get_Trg_ePort_15_0(self):
        return bitter(16, 7).get_calc(self.word3)
    def __set_Trg_ePort_15_0(self, value):
        self.word3 = bitter(16, 7).set_calc(self.word3, value)
    Trg_ePort_15_0 = property(__get_Trg_ePort_15_0, __set_Trg_ePort_15_0)

    def __get_Hash_5_4_vidx0(self):
        return bitter(2, 5).get_calc(self.word3)
    def __set_Hash_5_4_vidx0(self, value):
        self.word3 = bitter(2, 5).set_calc(self.word3, value)
    Hash_5_4_vidx0 = property(__get_Hash_5_4_vidx0, __set_Hash_5_4_vidx0)

    def __get_Trg_Dev_9_5(self):
        return bitter(5, 0).get_calc(self.word3)
    def __set_Trg_Dev_9_5(self, value):
        self.word3 = bitter(5, 0).set_calc(self.word3, value)
    Trg_Dev_9_5 = property(__get_Trg_Dev_9_5, __set_Trg_Dev_9_5)

class DsaTag_From_CPU_4(pypacker.Packet):
    __hdr__= (
        ("word0", "I", 0),
    )

    def __get_tag_command(self):
        return bitter(2, 30).get_calc(self.word0)
    def __set_tag_command(self, value):
        self.word0 = bitter(2, 30).set_calc(self.word0,value)
    Tag_Command = property(__get_tag_command, __set_tag_command)

    def __get_Tag0_Src_Tagged(self):
        return bitter(1, 29).get_calc(self.word0)
    def __set_Tag0_Src_Tagged(self, value):
        self.word0 = bitter(1, 29).set_calc(self.word0,value)
    Tag0_Src_Tagged = property(__get_Tag0_Src_Tagged, __set_Tag0_Src_Tagged)

    def __get_eVIDX_9_0(self):
        return bitter(10, 19).get_calc(self.word0)
    def __set_eVIDX_9_0(self, value):
        self.word0 = bitter(10, 19).set_calc(self.word0,value)
    eVIDX_9_0 = property(__get_eVIDX_9_0, __set_eVIDX_9_0)

    def __get_Trg_Tagged(self):
        return bitter(1, 29).get_calc(self.word0)
    def __set_Trg_Tagged(self, value):
        self.word0 = bitter(1, 29).set_calc(self.word0,value)
    Trg_Tagged = property(__get_Trg_Tagged, __set_Trg_Tagged)

    def __get_Trg_Dev(self):
        return bitter(5, 24).get_calc(self.word0)
    def __set_Trg_Dev(self, value):
        self.word0 = bitter(5, 24).set_calc(self.word0,value)
    Trg_Dev = property(__get_Trg_Dev, __set_Trg_Dev)

    def __get_Trg_Phy_Port_4_0(self):
        return bitter(5, 19).get_calc(self.word0)
    def __set_Trg_Phy_Port_4_0(self, value):
        self.word0 = bitter(5, 19).set_calc(self.word0,value)
    Trg_Phy_Port_4_0 = property(__get_Trg_Phy_Port_4_0, __set_Trg_Phy_Port_4_0)

    def __get_use_eVIDX(self):
        return bitter(1, 18).get_calc(self.word0)
    def __set_use_eVIDX(self, value):
        self.word0 = bitter(1, 18).set_calc(self.word0,value)
    use_eVIDX = property(__get_use_eVIDX, __set_use_eVIDX)

    def __get_TC_0(self):
        return bitter(1, 17).get_calc(self.word0)
    def __set_TC_0(self, value):
        self.word0 = bitter(1, 17).set_calc(self.word0,value)
    TC_0 = property(__get_TC_0, __set_TC_0)

    def __get_CFI(self):
        return bitter(1, 16).get_calc(self.word0)
    def __set_CFI(self, value):
        self.word0 = bitter(1, 16).set_calc(self.word0,value)
    CFI = property(__get_CFI, __set_CFI)

    def __get_UP(self):
        return bitter(3, 15).get_calc(self.word0)
    def __set_UP(self, value):
        self.word0 = bitter(3, 15).set_calc(self.word0,value)
    UP = property(__get_UP, __set_UP)

    def __get_w0_Extend(self):
        return bitter(1, 12).get_calc(self.word0)
    def __set_w0_Extend(self, value):
        self.word0 = bitter(1, 12).set_calc(self.word0,value)
    w0_Extend = property(__get_w0_Extend, __set_w0_Extend)

    def __get_eVLAN_11_0(self):
        return bitter(12, 0).get_calc(self.word0)
    def __set_eVLAN_11_0(self, value):
        self.word0 = bitter(12, 0).set_calc(self.word0,value)
    eVLAN_11_0 = property(__get_eVLAN_11_0, __set_eVLAN_11_0)

class DsaTag_From_CPU_8(DsaTag_From_CPU_4):
    __hdr__= (
        ("word0", "I", 0),
        ("word1", "I", 0),
    )

    def __get_w1_Extend(self):
        return bitter(1, 31).get_calc(self.word1)
    def __set_w1_Extend(self, value):
        self.word1 = bitter(1, 31).set_calc(self.word1,value)
    w1_Extend = property(__get_w1_Extend, __set_w1_Extend)

    def __get_Egress_Filter_Enable(self):
        return bitter(1, 30).get_calc(self.word1)
    def __set_Egress_Filter_Enable(self, value):
        self.word1 = bitter(1, 30).set_calc(self.word1,value)
    Egress_Filter_Enable = property(__get_Egress_Filter_Enable, __set_Egress_Filter_Enable)

    def __get_Egress_Filter_Registered(self):
        return bitter(1, 28).get_calc(self.word1)
    def __set_Egress_Filter_Registered(self, value):
        self.word1 = bitter(1, 28).set_calc(self.word1,value)
    Egress_Filter_Registered = property(__get_Egress_Filter_Registered, __set_Egress_Filter_Registered)

    def __get_TC_2(self):
        return bitter(1, 27).get_calc(self.word1)
    def __set_TC_2(self, value):
        self.word1 = bitter(1, 27).set_calc(self.word1,value)
    TC_2 = property(__get_TC_2, __set_TC_2)

    def __get_Drop_On_Source(self):
        return bitter(1, 26).get_calc(self.word1)
    def __set_Drop_On_Source(self, value):
        self.word1 = bitter(1, 26).set_calc(self.word1,value)
    Drop_On_Source = property(__get_Drop_On_Source, __set_Drop_On_Source)

    def __get_Packet_Is_Looped(self):
        return bitter(1, 25).get_calc(self.word1)
    def __set_Packet_Is_Looped(self, value):
        self.word1 = bitter(1, 25).set_calc(self.word1,value)
    Packet_Is_Looped = property(__get_Packet_Is_Looped, __set_Packet_Is_Looped)

    def __get_Src_ID_4_0(self):
        return bitter(5, 20).get_calc(self.word1)
    def __set_Src_ID_4_0(self, value):
        self.word1 = bitter(5, 20).set_calc(self.word1,value)
    Src_ID_4_0 = property(__get_Src_ID_4_0, __set_Src_ID_4_0)

    def __get_Src_Dev_4_0(self):
        return bitter(5, 15).get_calc(self.word1)
    def __set_Src_Dev_4_0(self, value):
        self.word1 = bitter(5, 15).set_calc(self.word1,value)
    Src_Dev_4_0 = property(__get_Src_Dev_4_0, __set_Src_Dev_4_0)

    def __get_TC_1(self):
        return bitter(1, 14).get_calc(self.word1)
    def __set_TC_1(self, value):
        self.word1 = bitter(1, 14).set_calc(self.word1,value)
    TC_1 = property(__get_TC_1, __set_TC_1)

    def __get_eVIDX_11_10(self):
        return bitter(2, 12).get_calc(self.word1)
    def __set_eVIDX_11_10(self, value):
        self.word1 = bitter(2, 12).set_calc(self.word1,value)
    eVIDX_11_10 = property(__get_eVIDX_11_10, __set_eVIDX_11_10)

    def __get_Exclude_Is_Trunk(self):
        return bitter(1, 11).get_calc(self.word1)
    def __set_Exclude_Is_Trunk(self, value):
        self.word1 = bitter(1, 11).set_calc(self.word1,value)
    Exclude_Is_Trunk = property(__get_Exclude_Is_Trunk, __set_Exclude_Is_Trunk)

    def __get_Mirror_To_All_CPUs(self):
        return bitter(1, 10).get_calc(self.word1)
    def __set_Mirror_To_All_CPUs(self, value):
        self.word1 = bitter(1, 10).set_calc(self.word1,value)
    Mirror_To_All_CPUs = property(__get_Mirror_To_All_CPUs, __set_Mirror_To_All_CPUs)

    def __get_Excluded_Trunk_6_0(self):
        return bitter(1, 0).get_calc(self.word1)
    def __set_Excluded_Trunk_6_0(self, value):
        self.word1 = bitter(1, 0).set_calc(self.word1,value)
    Excluded_Trunk_6_0 = property(__get_Excluded_Trunk_6_0, __set_Excluded_Trunk_6_0)

    def __get_Excluded_Phy_Port_ePort_5_0(self):
        return bitter(6, 5).get_calc(self.word1)
    def __set_Excluded_Phy_Port_ePort_5_0(self, value):
        self.word1 = bitter(6, 5).set_calc(self.word1,value)
    Excluded_Phy_Port_ePort_5_0 = property(__get_Excluded_Phy_Port_ePort_5_0, __set_Excluded_Phy_Port_ePort_5_0)

    def __get_Excluded_Dev(self):
        return bitter(6, 0).get_calc(self.word1)
    def __set_Excluded_Dev(self, value):
        self.word1 = bitter(6, 0).set_calc(self.word1,value)
    Excluded_Dev = property(__get_Excluded_Dev, __set_Excluded_Dev)

    def __get_Mailbox_To_Neighbor_CPU(self):
        return bitter(1, 13).get_calc(self.word1)
    def __set_Mailbox_To_Neighbor_CPU(self, value):
        self.word1 = bitter(1, 13).set_calc(self.word1,value)
    Mailbox_To_Neighbor_CPU = property(__get_Mailbox_To_Neighbor_CPU, __set_Mailbox_To_Neighbor_CPU)

    def __get_Trg_Phy_Port_6_5(self):
        return bitter(2, 10).get_calc(self.word1)
    def __set_Trg_Phy_Port_6_5(self, value):
        self.word1 = bitter(2, 10).set_calc(self.word1,value)
    Trg_Phy_Port_6_5 = property(__get_Trg_Phy_Port_6_5, __set_Trg_Phy_Port_6_5)

class DsaTag_From_CPU_16(DsaTag_From_CPU_8):
    __hdr__= (
        ("word0", "I", 0),
        ("word1", "I", 0),
        ("word2", "I", 0),
        ("word3", "I", 0),
    )
    #word2
    def __get_w2_Extend(self):
        return bitter(1, 31).get_calc(self.word2)
    def __set_w2_Extend(self, value):
        self.word2 = bitter(1, 31).set_calc(self.word2,value)
    w2_Extend = property(__get_w2_Extend, __set_w2_Extend)

    def __get_Is_Trg_Phy_Port_Valid(self):
        return bitter(1, 29).get_calc(self.word2)
    def __set_Is_Trg_Phy_Port_Valid(self, value):
        self.word2 = bitter(1, 29).set_calc(self.word2,value)
    Is_Trg_Phy_Port_Valid = property(__get_Is_Trg_Phy_Port_Valid, __set_Is_Trg_Phy_Port_Valid)

    def __get_Trg_Phy_Port_7(self):
        return bitter(1, 28).get_calc(self.word2)
    def __set_Trg_Phy_Port_7(self, value):
        self.word2 = bitter(1, 28).set_calc(self.word2,value)
    Trg_Phy_Port_7 = property(__get_Trg_Phy_Port_7, __set_Trg_Phy_Port_7)

    def __get_Src_ID_11_5(self):
        return bitter(7, 21).get_calc(self.word2)
    def __set_Src_ID_11_5(self, value):
        self.word2 = bitter(7, 21).set_calc(self.word2,value)
    Src_ID_11_5 = property(__get_Src_ID_11_5, __set_Src_ID_11_5)

    def __get_Src_Dev_9_5(self):
        return bitter(5, 14).get_calc(self.word2)
    def __set_Src_Dev_9_5(self, value):
        self.word2 = bitter(5, 14).set_calc(self.word2,value)
    Src_Dev_9_5 = property(__get_Src_Dev_9_5, __set_Src_Dev_9_5)

    def __get_Excluded_Trunk_11_7(self):
        return bitter(5, 3).get_calc(self.word2)
    def __set_Excluded_Trunk_11_7(self, value):
        self.word2 = bitter(5, 3).set_calc(self.word2,value)
    Excluded_Trunk_11_7 = property(__get_Excluded_Trunk_11_7, __set_Excluded_Trunk_11_7)

    def __get_Excluded_Phy_Port_ePort_16_6(self):
        return bitter(11, 3).get_calc(self.word2)
    def __set_Excluded_Phy_Port_ePort_16_6(self, value):
        self.word2 = bitter(11, 3).set_calc(self.word2,value)
    Excluded_Phy_Port_ePort_16_6 = property(__get_Excluded_Phy_Port_ePort_16_6, __set_Excluded_Phy_Port_ePort_16_6)

    def __get_TPID_Index(self):
        return bitter(11, 3).get_calc(self.word2)
    def __set_TPID_Index(self, value):
        self.word2 = bitter(11, 3).set_calc(self.word2,value)
    TPID_Index = property(__get_TPID_Index, __set_TPID_Index)

    #word3
    def __get_w3_Extend(self):
        return bitter(1, 31).get_calc(self.word3)
    def __set_w3_Extend(self, value):
        self.word3 = bitter(1, 31).set_calc(self.word3,value)
    w3_Extend = property(__get_w3_Extend, __set_w3_Extend)

    def __get_eVLAN_15_12(self):
        return bitter(4, 27).get_calc(self.word3)
    def __set_eVLAN_15_12(self, value):
        self.word3 = bitter(4, 27).set_calc(self.word3,value)
    eVLAN_15_12 = property(__get_eVLAN_15_12, __set_eVLAN_15_12)

    def __get_Tag1_SrcTagged(self):
        return bitter(1, 26).get_calc(self.word3)
    def __set_Tag1_SrcTagged(self, value):
        self.word3 = bitter(1, 26).set_calc(self.word3,value)
    Tag1_SrcTagged = property(__get_Tag1_SrcTagged, __set_Tag1_SrcTagged)

    def __get_SrcTag0_Is_OuterTag(self):
        return bitter(1, 25).get_calc(self.word3)
    def __set_SrcTag0_Is_OuterTag(self, value):
        self.word3 = bitter(1, 25).set_calc(self.word3,value)
    SrcTag0_Is_OuterTag = property(__get_SrcTag0_Is_OuterTag, __set_SrcTag0_Is_OuterTag)

    def __get_eVIDX_15_12(self):
        return bitter(4, 20).get_calc(self.word3)
    def __set_eVIDX_15_12(self, value):
        self.word3 = bitter(4, 20).set_calc(self.word3,value)
    eVIDX_15_12 = property(__get_eVIDX_15_12, __set_eVIDX_15_12)

    def __get_Excluded_Is_PhyPort(self):
        return bitter(1, 19).get_calc(self.word3)
    def __set_Excluded_Is_PhyPort(self, value):
        self.word3 = bitter(1, 19).set_calc(self.word3,value)
    Excluded_Is_PhyPort = property(__get_Excluded_Is_PhyPort, __set_Excluded_Is_PhyPort)

    def __get_ExcludedDev_11_5(self):
        return bitter(7, 0).get_calc(self.word3)
    def __set_ExcludedDev_11_5(self, value):
        self.word3 = bitter(7, 0).set_calc(self.word3,value)
    ExcludedDev_11_5 = property(__get_ExcludedDev_11_5, __set_ExcludedDev_11_5)

    def __get_Trg_Phy_Port(self):
        return bitter(2, 23).get_calc(self.word3)
    def __set_Trg_Phy_Port(self, value):
        self.word3 = bitter(2, 23).set_calc(self.word3,value)
    Trg_Phy_Port = property(__get_Trg_Phy_Port, __set_Trg_Phy_Port)

    def __get_TRGePort_15_0(self):
        return bitter(15, 7).get_calc(self.word3)
    def __set_TRGePort_15_0(self, value):
        self.word3 = bitter(15, 7).set_calc(self.word3,value)
    TRGePort_15_0 = property(__get_TRGePort_15_0, __set_TRGePort_15_0)

    def __get_TrgDev_11_5(self):
        return bitter(7, 0).get_calc(self.word3)
    def __set_TrgDev_11_5(self, value):
        self.word3 = bitter(7, 0).set_calc(self.word3,value)
    TrgDev_11_5 = property(__get_TrgDev_11_5, __set_TrgDev_11_5)

class DsaTag_To_CPU_4(pypacker.Packet):
    __hdr__= (
        ("word0", "I", 0),
    )

    def __get_tag_command(self):
        return bitter(2, 30).get_calc(self.word0)
    def __set_tag_command(self, value):
        self.word0 = bitter(2, 30).set_calc(self.word0,value)
    Tag_Command = property(__get_tag_command, __set_tag_command)

    def __get_SrcTrg_Tagged(self):
        return bitter(1, 29).get_calc(self.word0)
    def __set_SrcTrg_Tagged(self, value):
        self.word0 = bitter(1, 29).set_calc(self.word0,value)
    SrcTrg_Tagged = property(__get_SrcTrg_Tagged, __set_SrcTrg_Tagged)

    def __get_SrcDev_TrgDev_4_0(self):
        return bitter(5, 24).get_calc(self.word0)
    def __set_SrcDev_TrgDev_4_0(self, value):
        self.word0 = bitter(5, 24).set_calc(self.word0,value)
    SrcDev_TrgDev_4_0 = property(__get_SrcDev_TrgDev_4_0, __set_SrcDev_TrgDev_4_0)

    def __get_SrcPhyPort_TrgPhyPort_4_0(self):
        return bitter(5, 19).get_calc(self.word0)
    def __set_SrcPhyPort_TrgPhyPort_4_0(self, value):
        self.word0 = bitter(5, 19).set_calc(self.word0,value)
    SrcPhyPort_TrgPhyPort_4_0 = property(__get_SrcPhyPort_TrgPhyPort_4_0, __set_SrcPhyPort_TrgPhyPort_4_0)

    def __get__w0_Reserved_16(self):
        return bitter(3, 16).get_calc(self.word0)
    def __set__w0_Reserved_16(self, value):
        self.word0 = bitter(3, 16).set_calc(self.word0,value)
    _w0_Reserved_16 = property(__get__w0_Reserved_16, __set__w0_Reserved_16)

    def __get_UP(self):
        return bitter(5, 19).get_calc(self.word0)
    def __set_UP(self, value):
        self.word0 = bitter(5, 19).set_calc(self.word0,value)
    UP = property(__get_UP, __set_UP)

    def __get__w0_Reserved_12(self):
        return bitter(1, 12).get_calc(self.word0)
    def __set__w0_Reserved_12(self, value):
        self.word0 = bitter(1, 12).set_calc(self.word0,value)
    w0_Extend = property(__get__w0_Reserved_12, __set__w0_Reserved_12)

    def __get_eVLAN_11_0(self):
        return bitter(12, 0).get_calc(self.word0)
    def __set_eVLAN_11_0(self, value):
        self.word0 = bitter(12, 0).set_calc(self.word0,value)
    eVLAN_11_0 = property(__get_eVLAN_11_0, __set_eVLAN_11_0)

class DsaTag_To_CPU_8(DsaTag_To_CPU_4):
    __hdr__= (
        ("word0", "I", 0),
        ("word1", "I", 0),
    )

    def __get_w1_Extend(self):
        return bitter(1, 31).get_calc(self.word1)
    def __set_w1_Extend(self, value):
        self.word1 = bitter(1, 31).set_calc(self.word1,value)
    w1_Extend = property(__get_w1_Extend, __set_w1_Extend)

    def __get_CFI(self):
        return bitter(1, 30).get_calc(self.word1)
    def __set_CFI(self, value):
        self.word1 = bitter(1, 30).set_calc(self.word1,value)
    CFI = property(__get_CFI, __set_CFI)

    def __get_Drop_On_Source(self):
        return bitter(1, 29).get_calc(self.word1)
    def __set_Drop_On_Source(self, value):
        self.word1 = bitter(1, 29).set_calc(self.word1,value)
    Drop_On_Source = property(__get_Drop_On_Source, __set_Drop_On_Source)

    def __get_Packet_Is_Looped(self):
        return bitter(1, 28).get_calc(self.word1)
    def __set_Packet_Is_Looped(self, value):
        self.word1 = bitter(1, 28).set_calc(self.word1,value)
    Packet_Is_Looped = property(__get_Packet_Is_Looped, __set_Packet_Is_Looped)

    def __get_Orig_Is_Trunk(self):
        return bitter(1, 27).get_calc(self.word1)
    def __set_Orig_Is_Trunk(self, value):
        self.word1 = bitter(1, 27).set_calc(self.word1,value)
    Orig_Is_Trunk = property(__get_Orig_Is_Trunk, __set_Orig_Is_Trunk)

    def __get_Truncated(self):
        return bitter(1, 26).get_calc(self.word1)
    def __set_Truncated(self, value):
        self.word1 = bitter(1, 26).set_calc(self.word1,value)
    Truncated = property(__get_Truncated, __set_Truncated)

    def __get_Timestamp_14_1_Pkt_Orig_BC(self):
        return bitter(14, 12).get_calc(self.word1)
    def __set_Timestamp_14_1_Pkt_Orig_BC(self, value):
        self.word1 = bitter(14, 12).set_calc(self.word1,value)
    Timestamp_14_1_Pkt_Orig_BC = property(__get_Timestamp_14_1_Pkt_Orig_BC, __set_Timestamp_14_1_Pkt_Orig_BC)

    def __get_SrcPhyPort_TrgPhyPort_6_5(self):
        return bitter(2, 10).get_calc(self.word1)
    def __set_SrcPhyPort_TrgPhyPort_6_5(self, value):
        self.word1 = bitter(2, 10).set_calc(self.word1,value)
    SrcPhyPort_TrgPhyPort_6_5 = property(__get_SrcPhyPort_TrgPhyPort_6_5, __set_SrcPhyPort_TrgPhyPort_6_5)

    def __get_Timestamp_0_Reserved(self):
        return bitter(1, 9).get_calc(self.word1)
    def __set_Timestamp_0_Reserved(self, value):
        self.word1 = bitter(1, 9).set_calc(self.word1,value)
    Timestamp_0_Reserved = property(__get_Timestamp_0_Reserved, __set_Timestamp_0_Reserved)

    def __get_Src_Trg(self):
        return bitter(1, 8).get_calc(self.word1)
    def __set_Src_Trg(self, value):
        self.word1 = bitter(1, 8).set_calc(self.word1,value)
    Src_Trg = property(__get_Src_Trg, __set_Src_Trg)

    def __get_Long_CPU_Code(self):
        return bitter(8, 0).get_calc(self.word1)
    def __set_Long_CPU_Code(self, value):
        self.word1 = bitter(8, 0).set_calc(self.word1,value)
    Long_CPU_Code = property(__get_Long_CPU_Code, __set_Long_CPU_Code)

class DsaTag_To_CPU_16(DsaTag_To_CPU_8):
    __hdr__= (
        ("word0", "I", 0),
        ("word1", "I", 0),
        ("word2", "I", 0),
        ("word3", "I", 0),
    )
    #word2
    def __get_w2_Extend(self):
        return bitter(1, 31).get_calc(self.word2)
    def __set_w2_Extend(self, value):
        self.word2 = bitter(1, 31).set_calc(self.word2,value)
    w2_Extend = property(__get_w2_Extend, __set_w2_Extend)

    def __get_Packet_Is_TT(self):
        return bitter(1, 25).get_calc(self.word2)
    def __set_Packet_Is_TT(self, value):
        self.word2 = bitter(1, 25).set_calc(self.word2,value)
    Packet_Is_TT = property(__get_Packet_Is_TT, __set_Packet_Is_TT)

    def __get_SrcPhyPort_TrgPhyPort_9_7(self):
        return bitter(3, 20).get_calc(self.word2)
    def __set_SrcPhyPort_TrgPhyPort_9_7(self, value):
        self.word2 = bitter(3, 20).set_calc(self.word2,value)
    SrcPhyPort_TrgPhyPort_9_7 = property(__get_SrcPhyPort_TrgPhyPort_9_7, __set_SrcPhyPort_TrgPhyPort_9_7)

    def __get_SrcePort_TrgePort_15_0_SrcTrunk_11_0(self):
        return bitter(16, 3).get_calc(self.word2)
    def __set_SrcePort_TrgePort_15_0_SrcTrunk_11_0(self, value):
        self.word2 = bitter(16, 3).set_calc(self.word2,value)
    SrcePort_TrgePort_15_0_SrcTrunk_11_0 = property(__get_SrcePort_TrgePort_15_0_SrcTrunk_11_0, __set_SrcePort_TrgePort_15_0_SrcTrunk_11_0)

    def __get_TPID_Index(self):
        return bitter(3, 0).get_calc(self.word2)
    def __set_TPID_Index(self, value):
        self.word2 = bitter(3, 0).set_calc(self.word2,value)
    TPID_Index = property(__get_TPID_Index, __set_TPID_Index)

    #word3
    def __get_w3_Extend(self):
        return bitter(1, 31).get_calc(self.word3)
    def __set_w3_Extend(self, value):
        self.word3 = bitter(1, 31).set_calc(self.word3,value)
    w3_Extend = property(__get_w3_Extend, __set_w3_Extend)

    def __get_eVLAN_15_12(self):
        return bitter(4, 27).get_calc(self.word3)
    def __set_eVLAN_15_12(self, value):
        self.word3 = bitter(4, 27).set_calc(self.word3,value)
    eVLAN_15_12 = property(__get_eVLAN_15_12, __set_eVLAN_15_12)

    def __get_Flow_ID_TT_Offset(self):
        return bitter(7, 20).get_calc(self.word3)
    def __set_Flow_ID_TT_Offset(self, value):
        self.word3 = bitter(7, 20).set_calc(self.word3,value)
    Flow_ID_TT_Offset = property(__get_Flow_ID_TT_Offset, __set_Flow_ID_TT_Offset)

    def __get_SrcDev_TrgDev_9_5(self):
        return bitter(5, 0).get_calc(self.word3)
    def __set_SrcDev_TrgDev_9_5(self, value):
        self.word3 = bitter(5, 0).set_calc(self.word3,value)
    SrcDev_TrgDev_9_5 = property(__get_SrcDev_TrgDev_9_5, __set_SrcDev_TrgDev_9_5)

class DsaTag_To_ANALYZER_4(pypacker.Packet):
    __hdr__= (
        ("word0", "I", 0),
    )

    def __get_tag_command(self):
        return bitter(2, 30).get_calc(self.word0)
    def __set_tag_command(self, value):
        self.word0 = bitter(2, 30).set_calc(self.word0,value)
    Tag_Command = property(__get_tag_command, __set_tag_command)

    def __get_SrcTrg_Tagged(self):
        return bitter(1, 29).get_calc(self.word0)
    def __set_SrcTrg_Tagged(self, value):
        self.word0 = bitter(1, 29).set_calc(self.word0,value)
    SrcTrg_Tagged = property(__get_SrcTrg_Tagged, __set_SrcTrg_Tagged)

    def __get_SrcDev_TrgDev_4_0(self):
        return bitter(5, 24).get_calc(self.word0)
    def __set_SrcDev_TrgDev_4_0(self, value):
        self.word0 = bitter(5, 24).set_calc(self.word0,value)
    SrcDev_TrgDev_4_0 = property(__get_SrcDev_TrgDev_4_0, __set_SrcDev_TrgDev_4_0)

    def __get_SrcPhyPort_TrgPhyPort_4_0(self):
        return bitter(5, 19).get_calc(self.word0)
    def __set_SrcPhyPort_TrgPhyPort_4_0(self, value):
        self.word0 = bitter(5, 19).set_calc(self.word0,value)
    SrcPhyPort_TrgPhyPort_4_0 = property(__get_SrcPhyPort_TrgPhyPort_4_0, __set_SrcPhyPort_TrgPhyPort_4_0)

    def __get_rx_sniff(self):
        return bitter(1, 18).get_calc(self.word0)
    def __set_rx_sniff(self, value):
        self.word0 = bitter(1, 18).set_calc(self.word0,value)
    rx_sniff = property(__get_rx_sniff, __set_rx_sniff)

    def __get_CFI(self):
        return bitter(1, 16).get_calc(self.word0)
    def __set_CFI(self, value):
        self.word0 = bitter(1, 16).set_calc(self.word0,value)
    CFI = property(__get_CFI, __set_CFI)

    def __get_UP(self):
        return bitter(3, 13).get_calc(self.word0)
    def __set_UP(self, value):
        self.word0 = bitter(3, 13).set_calc(self.word0,value)
    UP = property(__get_UP, __set_UP)

    def __get_w0_Extend(self):
        return bitter(1, 12).get_calc(self.word0)
    def __set_w0_Extend(self, value):
        self.word0 = bitter(1, 12).set_calc(self.word0,value)
    w0_Extend = property(__get_w0_Extend, __set_w0_Extend)

    def __get_eVLAN_11_0(self):
        return bitter(12, 0).get_calc(self.word0)
    def __set_eVLAN_11_0(self, value):
        self.word0 = bitter(12, 0).set_calc(self.word0,value)
    eVLAN_11_0 = property(__get_eVLAN_11_0, __set_eVLAN_11_0)

class DsaTag_To_ANALYZER_8(DsaTag_To_ANALYZER_4):
    __hdr__= (
        ("word0", "I", 0),
        ("word1", "I", 0),
    )

    def __get_w1_Extend(self):
        return bitter(1, 31).get_calc(self.word1)
    def __set_w1_Extend(self, value):
        self.word1 = bitter(1, 31).set_calc(self.word1,value)
    w1_Extend = property(__get_w1_Extend, __set_w1_Extend)

    def __get_Drop_On_Source(self):
        return bitter(1, 29).get_calc(self.word1)
    def __set_Drop_On_Source(self, value):
        self.word1 = bitter(1, 29).set_calc(self.word1,value)
    Drop_On_Source = property(__get_Drop_On_Source, __set_Drop_On_Source)

    def __get_Packet_Is_Looped(self):
        return bitter(1, 28).get_calc(self.word1)
    def __set_Packet_Is_Looped(self, value):
        self.word1 = bitter(1, 28).set_calc(self.word1,value)
    Packet_Is_Looped = property(__get_Packet_Is_Looped, __set_Packet_Is_Looped)

    def __get_Analyzer_Is_Trg_Phy_Port_Valid(self):
        return bitter(1, 27).get_calc(self.word1)
    def __set_Analyzer_Is_Trg_Phy_Port_Valid(self, value):
        self.word1 = bitter(1, 27).set_calc(self.word1,value)
    Analyzer_Is_Trg_Phy_Port_Valid = property(__get_Analyzer_Is_Trg_Phy_Port_Valid, __set_Analyzer_Is_Trg_Phy_Port_Valid)

    def __get_Analyzer_Use_eVIDX(self):
        return bitter(1, 26).get_calc(self.word1)
    def __set_Analyzer_Use_eVIDX(self, value):
        self.word1 = bitter(1, 26).set_calc(self.word1,value)
    Analyzer_Use_eVIDX = property(__get_Analyzer_Use_eVIDX, __set_Analyzer_Use_eVIDX)

    def __get_Analyzer_Trg_Dev(self):
        return bitter(12, 14).get_calc(self.word1)
    def __set_Analyzer_Trg_Dev(self, value):
        self.word1 = bitter(12, 14).set_calc(self.word1,value)
    Analyzer_Trg_Dev = property(__get_Analyzer_Trg_Dev, __set_Analyzer_Trg_Dev)

    def __get_SrcPhyPort_TrgPhyPort_5(self):
        return bitter(2, 10).get_calc(self.word1)
    def __set_SrcPhyPort_TrgPhyPort_5(self, value):
        self.word1 = bitter(2, 10).set_calc(self.word1,value)
    SrcPhyPort_TrgPhyPort_5 = property(__get_SrcPhyPort_TrgPhyPort_5, __set_SrcPhyPort_TrgPhyPort_5)

    def __get_Analyzer_Trg_Phy_Port(self):
        return bitter(10, 0).get_calc(self.word1)
    def __set_Analyzer_Trg_Phy_Port(self, value):
        self.word1 = bitter(10, 0).set_calc(self.word1,value)
    Analyzer_Trg_Phy_Port = property(__get_Analyzer_Trg_Phy_Port, __set_Analyzer_Trg_Phy_Port)

class DsaTag_To_ANALYZER_16(DsaTag_To_ANALYZER_8):
    __hdr__= (
        ("word0", "I", 0),
        ("word1", "I", 0),
        ("word2", "I", 0),
        ("word3", "I", 0),
    )
    #word2
    def __get_w2_Extend(self):
        return bitter(1, 31).get_calc(self.word2)
    def __set_w2_Extend(self, value):
        self.word2 = bitter(1, 31).set_calc(self.word2,value)
    w2_Extend = property(__get_w2_Extend, __set_w2_Extend)

    def __get_SrcPhyPort_TrgPhyPort_7(self):
        return bitter(3, 20).get_calc(self.word2)
    def __set_SrcPhyPort_TrgPhyPort_7(self, value):
        self.word2 = bitter(3, 20).set_calc(self.word2,value)
    SrcPhyPort_TrgPhyPort_7 = property(__get_SrcPhyPort_TrgPhyPort_7, __set_SrcPhyPort_TrgPhyPort_7)

    def __get_SrcePort_TrgePort_15_0(self):
        return bitter(16, 3).get_calc(self.word2)
    def __set_SrcePort_TrgePort_15_0(self, value):
        self.word2 = bitter(16, 3).set_calc(self.word2,value)
    SrcePort_TrgePort_15_0 = property(__get_SrcePort_TrgePort_15_0, __set_SrcePort_TrgePort_15_0)

    def __get_TPID_Index(self):
        return bitter(3, 0).get_calc(self.word2)
    def __set_TPID_Index(self, value):
        self.word2 = bitter(3, 0).set_calc(self.word2,value)
    TPID_Index = property(__get_TPID_Index, __set_TPID_Index)

    #word3
    def __get_w3_Extend(self):
        return bitter(1, 31).get_calc(self.word3)
    def __set_w3_Extend(self, value):
        self.word3 = bitter(1, 31).set_calc(self.word3,value)
    w3_Extend = property(__get_w3_Extend, __set_w3_Extend)

    def __get_eVLAN_15_12(self):
        return bitter(4, 27).get_calc(self.word3)
    def __set_eVLAN_15_12(self, value):
        self.word3 = bitter(4, 27).set_calc(self.word3,value)
    eVLAN_15_12 = property(__get_eVLAN_15_12, __set_eVLAN_15_12)

    def __get_Analyzer_ePort(self):
        return bitter(17, 7).get_calc(self.word3)
    def __set_Analyzer_ePort(self, value):
        self.word3 = bitter(17, 7).set_calc(self.word3,value)
    Analyzer_ePort = property(__get_Analyzer_ePort, __set_Analyzer_ePort)

    def __get_Analyzer_eVIDX(self):
        return bitter(16, 7).get_calc(self.word3)
    def __set_Analyzer_eVIDX(self, value):
        self.word3 = bitter(16, 7).set_calc(self.word3,value)
    Analyzer_eVIDX = property(__get_Analyzer_eVIDX, __set_Analyzer_eVIDX)

    def __get_SrcDev_TrgDev_9_5(self):
        return bitter(5, 0).get_calc(self.word3)
    def __set_SrcDev_TrgDev_9_5(self, value):
        self.word3 = bitter(5, 0).set_calc(self.word3,value)
    SrcDev_TrgDev_9_5 = property(__get_SrcDev_TrgDev_9_5, __set_SrcDev_TrgDev_9_5)


# obj = DsaTag_forward_16()
#
# #obj = DsaTag_forward_4()
# obj.tag_command = 3
# obj.Tag0_Src_Tagged = 1
#
# obj.w0_Extend = 0
# obj.Src_Dev_4_0 = 0xb
#
# obj.eVLAN_11_0 = 0x20F
#
# obj.w1_Extend = 1
#
#
#
# bin_headers = '0x' + binascii.hexlify(obj.bin()).decode('utf-8')
# print()