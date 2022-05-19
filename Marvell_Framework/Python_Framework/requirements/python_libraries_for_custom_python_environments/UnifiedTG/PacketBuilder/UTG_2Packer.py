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
import functools
import os
import sys

from pypacker import checksum
from pypacker.layer12.llc import LLC
from pypacker.layer12.ethernet import Ethernet, Dot1Q, ETH_TYPE_IP6,ETH_TYPE_IP
from pypacker.layer12.arp import ARP
from pypacker.layer3.ip6 import IP6
from pypacker.layer3.ip import IP
from pypacker.layer4.tcp import TCP
from pypacker.layer4.udp import UDP
from UnifiedTG.PacketBuilder.gre import GRE, GREOptionChecksum, GREOptionKey, GREOptionSequence, GREOptionReserve_1
from UnifiedTG.PacketBuilder.e_tag import eTag
from UnifiedTG.PacketBuilder.mpls import MPLS
from UnifiedTG.PacketBuilder.ptp import PTP_header
from UnifiedTG.PacketBuilder.dsa_tag import DsaTag_forward_4, DsaTag_forward_8, DsaTag_forward_16, DsaTag_From_CPU_4, \
    DsaTag_From_CPU_8, DsaTag_From_CPU_16, DsaTag_To_CPU_4, DsaTag_To_CPU_8, DsaTag_To_CPU_16, DsaTag_To_ANALYZER_4, \
    DsaTag_To_ANALYZER_8, DsaTag_To_ANALYZER_16
from UnifiedTG.PacketBuilder.Payload import payload
from UnifiedTG.Unified import Packet
from UnifiedTG.Unified.TGEnums import TGEnums
from UnifiedTG.Unified.Utils import Converter

PY3K = sys.version_info >= (3, 0)

class utg_2packer(object):

    @classmethod
    def create_packer_obj(cls,utg_obj):
        return utg_to_packer_dict[type(utg_obj)](utg_obj)

    @classmethod
    def _autoconvert(cls,src,dst):
        filedsList =  src.__dict__
        for fieldName in filedsList:
            setattr(dst, fieldName, filedsList.get(fieldName))

    @classmethod
    def create_mac_obj(cls,utg_mac):
        headerObj = Ethernet(src_s=utg_mac.sa.value)
        headerObj.dst_s = utg_mac.da.value
        l2_proto = utg_mac._l2_proto
        if l2_proto == TGEnums.L2_PROTO.ETHERNETII:
            if utg_mac._ethertype._current_val != utg_mac._ethertype._default_val:
                headerObj.type = int(utg_mac._ethertype._current_val, 16)
        else:
            headerObj.type = None
        return headerObj

    @classmethod
    def create_vlan_obj(cls,utg_vlan):
        vid = int(utg_vlan.vid.value)
        cfi = int(utg_vlan.cfi)
        prio = int(utg_vlan.priority)
        vlanObj = Dot1Q(vid=vid, cfi=cfi, prio=prio)
        return vlanObj

    @classmethod
    def create_mpls_obj(cls,utg_mpls):
        mpls_obj =MPLS(label=int(utg_mpls.label),ttl= int(utg_mpls.ttl))
        #if last - set flag #TODO
        mpls_obj.bottom_stack = 1
        mpls_obj.exp = utg_mpls.experimental
        return mpls_obj

    @classmethod
    def create_snap_obj(cls,utg_snap):
        snap_obj = LLC(dsap=0xAA, ssap=0xAA)
        return snap_obj

    @classmethod
    def create_PTP(cls,utg_ptp):
        ptp_obj = PTP_header()
        cls._autoconvert(utg_ptp, ptp_obj)
        return ptp_obj

    @classmethod
    def create_v4_obj(cls, utg_v4):
        # type: (Packet.IPV4) -> object
        headerObj = IP( # TODO FIX SHIFT ECN
                       id=int(utg_v4.identifier),
                       off=int(utg_v4.fragment_offset_decimal_value),
                       ttl=int(utg_v4.ttl),
                       p=int(utg_v4.protocol),
                       src_s=utg_v4.source_ip.value,
                       dst_s=utg_v4.destination_ip.value
                       )
        # handle automatic fields & options TODO
        # v_hl ,sum and opts
        if utg_v4.qos_type is TGEnums.QOS_MODE.DSCP:
            headerObj.tos = int(utg_v4.dscp_decimal_value, 10)
        else:
            tos = int(utg_v4.tos_precedence << 5)+(utg_v4.tos_delay << 4)+(utg_v4.tos_throughput << 3)
            headerObj.tos = tos #  hex(tos )
        return headerObj

    @classmethod
    def create_DsaTag_forward_4_obj(cls,utg_dsa):
        obj = DsaTag_forward_4()
        cls._autoconvert(utg_dsa, obj)
        return obj

    @classmethod
    def create_DsaTag_forward_8_obj(cls,utg_dsa):
        obj = DsaTag_forward_8()
        cls._autoconvert(utg_dsa, obj)
        return obj

    @classmethod
    def create_DsaTag_forward_16_obj(cls,utg_dsa):
        obj = DsaTag_forward_16()
        cls._autoconvert(utg_dsa, obj)
        return obj

    @classmethod
    def create_DsaTag_From_CPU_4_obj(cls,utg_dsa):
        obj = DsaTag_From_CPU_4()
        cls._autoconvert(utg_dsa,obj)
        return obj

    @classmethod
    def create_DsaTag_From_CPU_8_obj(cls,utg_dsa):
        obj = DsaTag_From_CPU_8()
        cls._autoconvert(utg_dsa,obj)
        return obj

    @classmethod
    def create_DsaTag_From_CPU_16_obj(cls,utg_dsa):
        obj = DsaTag_From_CPU_16()
        cls._autoconvert(utg_dsa,obj)
        return obj

    @classmethod
    def create_DsaTag_To_CPU_4_obj(cls,utg_dsa):
        obj = DsaTag_To_CPU_4()
        cls._autoconvert(utg_dsa,obj)
        return obj

    @classmethod
    def create_DsaTag_To_CPU_8_obj(cls,utg_dsa):
        obj = DsaTag_To_CPU_8()
        cls._autoconvert(utg_dsa,obj)
        return obj

    @classmethod
    def create_DsaTag_To_CPU_16_obj(cls,utg_dsa):
        obj = DsaTag_To_CPU_16()
        cls._autoconvert(utg_dsa,obj)
        return obj

    @classmethod
    def create_DsaTag_To_Analyzer_4_obj(cls,utg_dsa):
        obj = DsaTag_To_ANALYZER_4()
        cls._autoconvert(utg_dsa,obj)
        return obj

    @classmethod
    def create_DsaTag_To_Analyzer_8_obj(cls,utg_dsa):
        obj = DsaTag_To_ANALYZER_8()
        cls._autoconvert(utg_dsa,obj)
        return obj

    @classmethod
    def create_DsaTag_To_Analyzer_16_obj(cls,utg_dsa):
        obj = DsaTag_To_ANALYZER_16()
        cls._autoconvert(utg_dsa,obj)
        return obj

    @classmethod
    def create_etag_obj(cls,utg_etag):
        # type: (Packet.E_Tag) -> object
        obj = eTag()
        obj.e_pcp = utg_etag.E_PCP
        obj.e_dei = utg_etag.E_DEI
        obj.ingres_e_cid_base = utg_etag.Ingress_E_CID_base
        obj.Re = utg_etag.Reserved
        obj.GRP = utg_etag.GRP
        obj.e_cid_base= utg_etag.E_CID_base
        obj.Ingress_E_CID_ext = utg_etag.Ingress_E_CID_ext
        obj.E_CID_ext = utg_etag.E_CID_ext
        return obj

    @classmethod
    def create_gre_obj(cls, utg_gre):
        # type: (Packet.GRE) -> object
        obj = GRE()
        #bin_headers = '0x' + binascii.hexlify(obj.bin()).decode('utf-8')
        obj.version_number = utg_gre.version
        #bin_headers = '0x' + binascii.hexlify(obj.bin()).decode('utf-8')
        if utg_gre.use_checksum is True:
            obj.opts.append(GREOptionChecksum(checksum=0))
            obj.opts.append(GREOptionReserve_1())
            obj.checksum_bit = 1
        #bin_headers = '0x' + binascii.hexlify(obj.bin()).decode('utf-8')
        if utg_gre.key_field is not None:
            obj.opts.append(GREOptionKey(key=Converter.convertstring2int(utg_gre.key_field)))
            obj.key_bit = 1
        #bin_headers = '0x' + binascii.hexlify(obj.bin()).decode('utf-8')
        if utg_gre.sequence_number is not None:
            obj.opts.append(GREOptionSequence(sequence=Converter.convertstring2int(utg_gre.sequence_number)))
            obj.sequence_bit = 1
        #bin_headers = '0x' + binascii.hexlify(obj.bin()).decode('utf-8')
        if utg_gre.use_checksum is True:
            innerPacketData = obj.bin()
            if utg_gre.l3_proto is TGEnums.L3_PROTO.IPV4:
                obj.protocol_type = ETH_TYPE_IP
                packer_v4 = utg_gre.ipv4.to_packer()
                innerPacketData += packer_v4.bin()
            elif utg_gre.l3_proto is TGEnums.L3_PROTO.IPV6:
                obj.protocol_type = ETH_TYPE_IP6
                v6 = utg_gre.ipv6.to_packer()
                innerPacketData += v6.bin()
            else:
                proto = Converter.remove_non_hexa_sumbols(utg_gre.l3_proto)
                proto = Converter.hexaString2int(proto)
                obj.protocol_type = proto

            if utg_gre.l4_proto is TGEnums.L4_PROTO.UDP:
                packer_udp = utg_gre.udp.to_packer()
                innerPacketData += packer_udp.bin()
            elif utg_gre.l4_proto is TGEnums.L4_PROTO.TCP:
                packer_tcp = utg_gre.tcp.to_packer()
                innerPacketData += packer_tcp.bin()

            s = checksum.in_cksum(innerPacketData)
            obj.opts[0].checksum = s
        #bin_headers = '0x' + binascii.hexlify(obj.bin()).decode('utf-8')
        return obj

    @classmethod
    def create_v6_obj(cls,utg_v6):
        # type: (Packet.IPV6) -> object
        v6_s = v6_to_packer_format(utg_v6.source_ip.value)
        v6_d = v6_to_packer_format(utg_v6.destination_ip.value)
        obj = IP6(fc=int(utg_v6.traffic_class),
                  flow=int(utg_v6.flow_label),
                  hlim=int(utg_v6.hop_limit),
                  src_s=v6_s,
                  dst_s=v6_d
                 )
        #if utg_v6._next_header._current_val != utg_v6._next_header._default_val:
        obj.nxt = int(utg_v6.next_header)
        return obj

    @classmethod
    def create_tcp_obj(cls,utg_tcp):
        flags_list = [int(utg_tcp.flag_urgent_pointer_valid),
                      int(utg_tcp.flag_acknowledge_valid),
                      int(utg_tcp.flag_push_function),
                      int(utg_tcp.flag_reset_connection),
                      int(utg_tcp.flag_synchronize_sequence),
                      int(utg_tcp.flag_no_more_data_from_sender)]
        flags = functools.reduce(lambda out,x: (out<<1)+int(x),flags_list,0)

        header_obj = TCP(sport=int(utg_tcp.source_port.value),
                         dport=int(utg_tcp.destination_port.value),
                         seq=Converter.hexaString2int(utg_tcp.sequence_number),
                         ack=Converter.hexaString2int(utg_tcp.acknowledgement_number),
                         #off_x2 TODO
                         flags = flags,
                         win = Converter.hexaString2int(utg_tcp.window),
                         #sum TODO
                         urp=Converter.hexaString2int(utg_tcp.urgent_pointer)
                         #opts TODO
                         )
        return header_obj

    @classmethod
    def create_udp_obj(cls,utg_udp):

        header_obj = UDP(sport=int(utg_udp.source_port.value),
                         dport=int(utg_udp.destination_port.value)
                         #ulen= , TODO
                         #sum= ,TODO
                        )
        return header_obj

    @classmethod
    def create_pl_obj(cls,utg_pl):
        pl = utg_pl.value
        pl_size = utg_pl.size #*2
        if utg_pl.type is TGEnums.DATA_PATTERN_TYPE.FIXED:
            pl = str('{:0<' + str(pl_size*2) + '}').format(pl)
        elif utg_pl.type is TGEnums.DATA_PATTERN_TYPE.REPEATING:
            while len(pl) < (pl_size*2):
                pl +=pl
            pl = pl[:(pl_size*2)]
        elif utg_pl.type is TGEnums.DATA_PATTERN_TYPE.INCREMENT_BYTE:
            pl = ''
            for x in range(pl_size):
                pl += "%02X" % x
        elif utg_pl.type is TGEnums.DATA_PATTERN_TYPE.DECREMENT_BYTE:
            pl = ''
            for x in range(0xff, 0xff-pl_size,-1):
                pl += "%02X" % x
        elif utg_pl.type is TGEnums.DATA_PATTERN_TYPE.RANDOM:
            pl = binascii.b2a_hex(os.urandom(pl_size))
        p = pattern_to_ascii_chars(pl)
        obj = payload(body_bytes=p)
        return obj

utg_to_packer_dict = {
                      type(Packet.MAC()): utg_2packer.create_mac_obj,
                      type(Packet.IPV4()): utg_2packer.create_v4_obj,
                      type(Packet.IPV6()): utg_2packer.create_v6_obj,
                      type(Packet.GRE()): utg_2packer.create_gre_obj,
                      type(Packet.TCP()):utg_2packer.create_tcp_obj,
                      type(Packet.UDP()):utg_2packer.create_udp_obj,
                      type(Packet.E_Tag()): utg_2packer.create_etag_obj,
                      type(Packet.DSA_Forward()): utg_2packer.create_DsaTag_forward_4_obj,
                      type(Packet.extDSA_Forward_use_vidx_0()): utg_2packer.create_DsaTag_forward_8_obj,
                      type(Packet.extDSA_Forward_use_vidx_1()): utg_2packer.create_DsaTag_forward_8_obj,
                      type(Packet.EDSA_Forward_use_vidx_0()): utg_2packer.create_DsaTag_forward_16_obj,
                      type(Packet.EDSA_Forward_use_vidx_1()): utg_2packer.create_DsaTag_forward_16_obj,
                      type(Packet.DSA_From_CPU_use_vidx_0()): utg_2packer.create_DsaTag_From_CPU_4_obj,
                      type(Packet.DSA_From_CPU_use_vidx_1()): utg_2packer.create_DsaTag_From_CPU_4_obj,
                      type(Packet.extDSA_From_CPU_use_vidx_0()): utg_2packer.create_DsaTag_From_CPU_8_obj,
                      type(Packet.extDSA_From_CPU_use_vidx_1_exclude_is_trunk_0()): utg_2packer.create_DsaTag_From_CPU_8_obj,
                      type(Packet.extDSA_From_CPU_use_vidx_1_exclude_is_trunk_1()): utg_2packer.create_DsaTag_From_CPU_8_obj,
                      type(Packet.EDSA_From_CPU_use_vidx_0()): utg_2packer.create_DsaTag_From_CPU_16_obj,
                      type(Packet.EDSA_From_CPU_use_vidx_1_exclude_is_trunk_0()): utg_2packer.create_DsaTag_From_CPU_16_obj,
                      type(Packet.EDSA_From_CPU_use_vidx_1_exclude_is_trunk_1()): utg_2packer.create_DsaTag_From_CPU_16_obj,
                      type(Packet.DSA_To_CPU()): utg_2packer.create_DsaTag_To_CPU_4_obj,
                      type(Packet.extDSA_To_CPU()): utg_2packer.create_DsaTag_To_CPU_8_obj,
                      type(Packet.EDSA_To_CPU()): utg_2packer.create_DsaTag_To_CPU_16_obj,
                      type(Packet.DSA_To_ANALYZER()): utg_2packer.create_DsaTag_To_Analyzer_4_obj,
                      type(Packet.extDSA_To_ANALYZER()): utg_2packer.create_DsaTag_To_Analyzer_8_obj,
                      type(Packet.EDSA_To_ANALYZER_use_eVIDX_0()): utg_2packer.create_DsaTag_To_Analyzer_16_obj,
                      type(Packet.EDSA_To_ANALYZER_use_eVIDX_1()): utg_2packer.create_DsaTag_To_Analyzer_16_obj,
                      type(Packet.DATA_PATTERN()): utg_2packer.create_pl_obj,
                      type(Packet.VLAN()): utg_2packer.create_vlan_obj,
                      type(Packet.MPLS_Label()): utg_2packer.create_mpls_obj,
                      type(Packet.llc_snap()): utg_2packer.create_snap_obj,
                      type(Packet.PTP()):utg_2packer.create_PTP,
                      }


def pattern_to_ascii_chars( pattern):
    asci_chars = bytes() if PY3K else ""
    patternString = Converter.remove_non_hexa_sumbols(pattern[:])
    while patternString:
        tmp_char = chr(int(patternString[:2], 16))
        char = bytes(tmp_char, 'latin-1') if PY3K else tmp_char
        asci_chars += char
        patternString = patternString[2:]
    return bytes(asci_chars) if PY3K else asci_chars

def v6_to_packer_format(v6_addr):
    return pattern_to_ascii_chars(Converter.remove_non_hexa_sumbols(Converter.expand_ipv6(v6_addr)))