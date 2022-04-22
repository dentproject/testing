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

from __future__ import division
from builtins import hex
from builtins import range
from builtins import object
from past.utils import old_div
import binascii


class GetPacketCRC(object):
    """
    verify parameters from Excel
    """

    @staticmethod
    def Get_Packet_CRC(self,packet):
        """
        Receive packet as string and retrun string of CRC (32bit.
        For example:
        packet='00000000000100000000000200000000'
        CRC=f5c7f557
        :param packet: packet
        :type: string
        :return: string
        """
        int_Temp=binascii.crc32(binascii.a2b_hex(packet))
        if int_Temp>0:
            temp=hex(int_Temp)
        else:
            pos_temp=int_Temp&0xffffffff
            temp=hex(pos_temp)
        crc=temp[2:]
        if len(crc)<8:
            crc='0'*(8-len(crc))+crc
        if crc[len(crc)-1]=='L':
            crc=crc[:len(crc)-1]
        h=list(crc)
        for i in range(old_div(len(crc), 2)):
            h[2 * i] = crc[(len(crc) - 1) - (2 * i + 1)]
            h[2 * i + 1] = crc[(len(crc) - 1) - (2 * i)]

        return "".join(h)