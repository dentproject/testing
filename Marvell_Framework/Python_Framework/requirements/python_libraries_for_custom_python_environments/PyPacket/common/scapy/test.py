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

from PyPacket.common import ScapyIPSec
from PyPacket.pcgen import Pcgen
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, UDP, Raw


def test_scapy_ipsec_functions(scapy_ipsec_obj):
    pkt = Pcgen()
    scapy_headers_tuple = (Ether(src='00:00:00:00:40:01', dst='00:00:00:00:80:01', type=0x0800),
                           IP(src='80.0.0.10', dst='60.0.0.11', ttl=0x40),
                           UDP(dport=0x889, sport=0x888),
                           Raw('000102030405060708090A0B0C0D0E0F1011'.decode('hex')))
    pkt.build_scapy_packet(scapy_headers_tuple)

    expected_enc = '4500004C000100004032EE6A5000000A3C00000B00000201000000055EB66511D938DC08E3C51C46E3F8154D36405' \
                   '8D1BCC2ECC6BD3D36F7F2CA43FAEF51128FB6DD741EE6B8276B1EEF4292'
    expected_dec = '4500002E000100004011EEA95000000A3C00000B08880889001A1A43000102030405060708090A0B0C0D0E0F1011'

    ip_pkt = pkt.scapy_packet[IP]
    encrypted_packet = scapy_ipsec_obj.get_encrypted_packet(ip_pkt=ip_pkt)
    print("test:\t\t\t\tget_encrypted_packet\t\t\t\t{}".format(
        Pcgen.scapy_pkt_2_byte_stream(encrypted_packet) == expected_enc))

    decrypted_packet = scapy_ipsec_obj.get_decrypted_packet(encrypted_packet)
    print("test:\t\t\t\tget_decrypted_packet\t\t\t\t{}".format(
        Pcgen.scapy_pkt_2_byte_stream(decrypted_packet) == expected_dec))

    full_pkt = Pcgen()
    full_pkt.build_scapy_packet((scapy_headers_tuple[0], decrypted_packet[IP]))
    print full_pkt.packet_byte_stream_with_crc


test = ScapyIPSec(spi=0x201, crypt_algo='AES-CBC', crypt_key='11112222333344445555666677778888', seq_num=5,
                  iv=b'5eb66511d938dc08e3c51c46e3f8154d')
test_scapy_ipsec_functions(test)
