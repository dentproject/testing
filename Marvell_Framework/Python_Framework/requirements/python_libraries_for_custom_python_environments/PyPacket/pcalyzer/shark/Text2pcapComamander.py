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

import re
import platform

from PyPacket.pcalyzer.shark.SharkCommander import sharkCommandBuilder

noSeparators = re.compile('[\s:]')

class tex2PcapCommandBuilder(sharkCommandBuilder):
    def __init__(self):
        system = platform.system()
        text2pcap = "text2pcap.exe"
        # print("system is: {}".format(system))
        if system == "Linux":
            text2pcap = "/text2pcap"
        super(self.__class__, self).__init__(text2pcap)


def create_text2pcap_input_format(hexa_string_input):

    hexa_string_input = noSeparators.sub("",hexa_string_input)
    out = '000000 '
    while hexa_string_input:
        octet = hexa_string_input[:2] + " "
        out += octet
        hexa_string_input = hexa_string_input[2:]
    return out
