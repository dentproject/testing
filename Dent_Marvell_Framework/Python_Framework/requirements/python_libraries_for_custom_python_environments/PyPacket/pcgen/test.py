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

from PyPacket.pcgen import Pcgen
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, UDP, Raw


def test_pcgen_functions(pcgen_obj):
    expected_byte_stream = '00000000800100000000400108004500002E000100004011EEA95000000A3C00000B08880889001A1A43' \
                           '000102030405060708090A0B0C0D0E0F1011'
    scapy_headers_tuple = (Ether(src='00:00:00:00:40:01', dst='00:00:00:00:80:01', type=0x0800),
                           IP(src='80.0.0.10', dst='60.0.0.11', ttl=0x40),
                           UDP(dport=0x889, sport=0x888),
                           Raw('000102030405060708090A0B0C0D0E0F1011'.decode('hex')))
    expected_crc = (366757237, 1967512597)

    pcgen_obj.build_scapy_packet(scapy_headers_tuple)
    print("test:\t\t\t\tbuild_scapy_packet\t\t\t\t\t{}".format(
        Pcgen.scapy_pkt_2_byte_stream(pcgen_obj.scapy_packet) == expected_byte_stream))

    pkt = Pcgen.byte_stream_2_scapy_pkt(expected_byte_stream)
    print("test:\t\t\t\tbyte_stream_2_scapy_pkt\t\t\t\t{}".format(
        pkt.show2(dump=True) == pcgen_obj.scapy_packet.show2(dump=True)))

    stream = Pcgen.scapy_pkt_2_byte_stream(pcgen_obj.scapy_packet)
    print("test:\t\t\t\tscapy_pkt_2_byte_stream\t\t\t\t{}".format(expected_byte_stream == stream))

    crc = Pcgen.get_byte_stream_crc32(expected_byte_stream)
    print("test:\t\t\t\tget_byte_stream_crc32\t\t\t\t{}".format(expected_crc == crc))


test = Pcgen()
test_pcgen_functions(test)
