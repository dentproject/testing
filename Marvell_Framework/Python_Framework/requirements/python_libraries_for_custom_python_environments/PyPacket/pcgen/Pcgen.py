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

from scapy.all import *
from scapy.layers.l2 import Ether
from zlib import crc32
import struct


class Pcgen(object):
    def __init__(self):
        self.scapy_packet = None
        self.packet_byte_stream = None
        self.packet_byte_stream_with_crc = None
        pass

    @staticmethod
    def byte_stream_2_scapy_pkt(byte_stream):
        """
        :param byte_stream: Two assumptions: 1. The first header of the byte stream is Layer2
                                             2. The CRC is not included in the byte stream.
        :return: Scapy packet object.
        """
        return Ether(byte_stream.decode('hex'))

    @staticmethod
    def scapy_pkt_2_byte_stream(scapy_packet):
        """
        :param scapy_packet:
        :return: string of the packet byte stream
        """
        stream_bytes = ""
        for current_byte in str(scapy_packet):
            stream_bytes += "{:02X}".format(ord(current_byte))
        return stream_bytes

    @staticmethod
    def print_packet_hex_dump(scapy_packet):
        """
        print to console the packet in hex format
        :param scapy_packet:
        :return:
        """
        hexdump(scapy_packet)
        return

    @staticmethod
    def get_byte_stream_crc32(byte_stream):
        """
        :param byte_stream: string of packet bytes
        :return: tuple of CRC in little endian and big endian
        """
        crc = crc32(byte_stream.decode('hex'))
        crc_unsigned = crc & 0xFFFFFFFF
        crc_hex_string = "{:08X}".format(crc_unsigned)
        crc_bytes_list = [crc_hex_string[i:i+2] for i in range(0, len(crc_hex_string), 2)]
        crc_swap_bytes = ''.join(crc_bytes_list[::-1])
        crc_swap = int(crc_swap_bytes, 16)
        return crc_unsigned, crc_swap

    def build_scapy_packet(self, scapy_headers_ordered_tuple):
        self.scapy_packet = scapy_headers_ordered_tuple[0]
        for header in scapy_headers_ordered_tuple[1:]:
            self.scapy_packet /= header
        self.scapy_packet.build()
        self.packet_byte_stream = self.scapy_pkt_2_byte_stream(self.scapy_packet)
        crc = format(self.get_byte_stream_crc32(self.packet_byte_stream)[1], '08X')
        self.packet_byte_stream_with_crc = self.packet_byte_stream + crc
        return
