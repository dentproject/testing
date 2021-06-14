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

from scapy.layers.ipsec import ESP, SecurityAssociation


class ScapyIPSec(object):
    def __init__(self, spi=0x11111111, crypt_algo='AES-CBC', crypt_key='26272829303132333435363738394041',
                 tunnel_header=None, seq_num=1145324612, iv=b'1A8D7EADDB387381BE07F92C0012A213',
                 auth_algo=None, auth_key=None):
        """
        spi             -   In integer (or hex), not in str
        crypt_algo      -   'AES-CBC', 'AES-CTR', 'AES-GCM', 'AES-CCM', 'Blowfish', 'DES', '3DES', 'CAST'
        crypt_key       -   In bytes (str)
        auth_algo       -   'HMAC-SHA1-96', 'SHA2-256-128', 'SHA2-384-192', 'SHA2-512-256', 'HMAC-MD5-96', 'AES-CMAC-96'
        auth_key        -   In bytes (str)
        tunnel_header   -   IP header with object IP (in case Tunnel mode is required)
        :return:
        """
        self.spi = spi
        self.crypt_algo = crypt_algo
        self.crypt_key = crypt_key.decode('hex')
        self.tunnel_header = tunnel_header
        self.seq_num = seq_num
        self.iv = iv.decode('hex')
        self.auth_algo = auth_algo
        self.auth_key = auth_key if auth_key is None else auth_key.decode('hex')
        self.sa = self.get_scapy_security_association()
        return

    def get_scapy_security_association(self):
        if self.tunnel_header is not None:
            # in case of Tunnel mode
            return SecurityAssociation(proto=ESP, spi=self.spi, crypt_algo=self.crypt_algo, crypt_key=self.crypt_key,
                                       tunnel_header=self.tunnel_header, auth_algo=self.auth_algo,
                                       auth_key=self.auth_key)
        else:
            # in case of Transport mode
            return SecurityAssociation(proto=ESP, spi=self.spi, crypt_algo=self.crypt_algo, crypt_key=self.crypt_key,
                                       auth_algo=self.auth_algo, auth_key=self.auth_key)

    def get_encrypted_packet(self, ip_pkt):
        """
        :param ip_pkt: scapy packet without layer2, without crc
        :return:
        """
        return self.sa.encrypt(pkt=ip_pkt, seq_num=self.seq_num, iv=self.iv)

    def get_decrypted_packet(self, encrypted_packet):
        """
        :param encrypted_packet: scapy packet, without layer2, without crc, with ESP header and encrypted data
        :return:
        """
        return self.sa.decrypt(pkt=encrypted_packet)
