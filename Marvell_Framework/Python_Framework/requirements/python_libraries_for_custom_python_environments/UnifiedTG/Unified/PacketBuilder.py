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
from scapy.layers.inet import IP,UDP,ICMP
from scapy.layers.dns import DNS
from scapy.layers.l2 import Ether ,Dot1Q

from UnifiedTG.Unified.Packet import *
from UnifiedTG.Unified.Utils import attrWithDefault



def build_packet(pkt):
    # type: (Packet) -> object

    utg2value = OrderedDict()
    utg2value[Ether] = {'dst': pkt.mac.sa.value, 'da': pkt.mac.da.value, 'type': pkt.ethertype}
    utg2value['vlan'] = {'protocolTagId': '', 'userPriority': 7, 'cfi': 1, 'vlanID': 5}
    utg2value['ip'] = {'headerLength': '', 'dscpValue': '', 'totalLength': '', 'identifier': '', 'fragmentOffset': '',
                       'ttl': '', 'ipProtocol': '', 'checksum': '', 'sourceIpAddr': '1.1.1.1', 'destIpAddr': '2.2.2.2',
                       'options': ''}

    utg2scapyFields = {'mac': {'obj': Ether, 'sa': 'src', 'da': 'dst', 'type': 'type'},
                       'ip': {'obj': IP, 'headerLength': 'ihl', 'dscpValue': 'tos', 'totalLength': 'len',
                              'identifier': 'id', 'fragmentOffset': 'frag', 'ttl': 'ttl',
                              'ipProtocol': 'proto', 'checksum': 'chksum', 'sourceIpAddr': 'src', 'destIpAddr': 'dst',
                              'options': 'options'}}
    utg2scapyFields['vlan'] = {'obj': Dot1Q, 'protocolTagId': 'type', 'userPriority': 'prio', 'cfi': 'id',
                               'vlanID': 'vlan'}

    #ETH
    scapet = Ether(dst=pkt.mac.da.value,src=pkt.mac.sa.value,type=pkt.ethertype)
    scapet.build_padding()
    #VLAN
    if len(pkt.vlans):
        for vid in pkt.vlans:
            vObj = pkt.vlans[vid]
            sVlan = Dot1Q(vlan=vObj.vid.value, prio=vObj.priority, id=vObj.cfi, type=vObj.proto)
            scapet /= sVlan
    #IP
    if pkt.l3_proto == TGEnums.L3_PROTO.IPV4:
        params = {}
        sl3Header = IP(ihl = pkt.ipv4.header_len_override_value )
    elif pkt.l3_proto == TGEnums.L3_PROTO.IPV6:
        proto_name = 'ipV6'  # todo find which value goes here
    elif pkt.l3_proto == TGEnums.L3_PROTO.ARP:
        pass
    elif pkt.l3_proto == TGEnums.L3_PROTO.NONE:
        pass
    scapet /= sl3Header