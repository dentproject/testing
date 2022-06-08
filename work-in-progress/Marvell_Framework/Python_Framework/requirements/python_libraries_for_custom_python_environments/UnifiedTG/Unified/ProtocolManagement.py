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


from collections import OrderedDict
from UnifiedTG.Unified.TGEnums import TGEnums
from UnifiedTG.Unified.Utils import attrWithDefault,Converter

class protocolManagment(object):
    def __init__(self):
        self._driver_obj = None
        self._parent = None
        self.active = True
        self._enable_ARP = attrWithDefault(True)
        self._enable_PING = attrWithDefault(False)
        self.protocol_interfaces = protocolInterfaces(self)
        self.arp_table = arp_table()


    @property
    def enable_ARP(self):
        return self._enable_ARP.current_val

    @enable_ARP.setter
    def enable_ARP(self,v):
        self._enable_ARP.current_val = v

    @property
    def enable_PING(self):
        return self._enable_PING.current_val

    @enable_PING.setter
    def enable_PING(self,v):
        self._enable_PING.current_val = v


    def apply(self):
        self.protocol_interfaces.apply()
        self.arp_table.apply()

class protocolInterfaces(object):
    def __init__(self, parent):
        self.interfaces = OrderedDict()  # type: list[protocolInterface]
        self._parent = parent
        self._driver_obj = None
        self.target_link_option = False
        self.auto_neighbor_discovery = False
        self.auto_arp = False
        self.discovered_neighbors = OrderedDict()  # type: list[learned_entry]


    def add_interface(self):
        pass

    def remove_interface(self):
        pass

    def apply(self):
        pass

    def send_arp(self):
        pass

    def send_neighbor_solicitation(self):
        pass

    def send_router_solicitation(self):
        pass

    def read_neigbors_table(self):
        pass

    def clear_neigbors_table(self):
        pass

class protocolInterface(object):
    def __init__(self):
        self.description = ''
        self.enable = False
        self.mac_addr = '00:00:00:00:00:01'
        self.mtu = 1500
        self.ipv4 = protocol_ipv4()
        self.ipv6 = protocol_ipv6()
        self.vlans = protocol_vlans()
        self._driver_if_key = None
        self._parent = None

    def clear_arp(self):
        pass

    def transmit_arp(self):
        pass

    def refresh_arp(self):
        pass

    def send_ping(self,dest_ip):
        pass


class arp_table(object):
    def __init__(self):
        self.learned_table = []  # type: list[learned_entry]
        self._parent = None
        self.arp_for = TGEnums.ARP_For.BOTH
        self.retries = 3
        self.count = 3

    def clear(self):
        pass

    def refresh(self):
        pass

    def transmit(self):
        pass

    def apply(self):
        pass

class protocol_ipv4(object):
    def __init__(self):
        self.address = None
        self.mask = 24
        self.gateway = '0.0.0.0'

class protocol_ipv6_entry(object):
    def __init__(self, address=None, mask=64, gateway='0.0.0.0.0.0.0.0'):
        self.address = address
        self.mask = mask
        self.gateway = gateway

class protocol_ipv6(protocol_ipv6_entry):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.additional_v6_entries = []

    def add_v6(self,address,mask,gateway):
        self.additional_v6_entries.append(protocol_ipv6_entry(address,mask,gateway))

class learned_entry(object):
    def __init__(self,mac,ip):
        self.ip = ip
        self.mac = mac

    def __str__(self):
        return self.mac + ' : ' + self.ip

class protocol_vlans(object):
    def __init__(self):
        self.enable = False
        self.vid = '0'
        self.priority = '0'
        self.tpid = '0x8100'

