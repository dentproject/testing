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

import functools
import inspect
import time
from collections import OrderedDict
from UnifiedTG.Unified.TGEnums import TGEnums
from UnifiedTG.Unified.ProtocolManagement import protocolManagment, protocolInterfaces, protocolInterface, \
    learned_entry,arp_table
from UnifiedTG.Unified.Utils import attrWithDefault, Converter

class ixProtocolManagment(protocolManagment):
    _sentinel = object()
    def __init__(self):
        super(self.__class__, self).__init__()
        self.protocol_interfaces = IxProtocolInterfaces(self)
        self._debug_prints = None
        self.arp_table = Ix_arp_table()
        self.arp_table._parent = self

    def apply(self):
        super(self.__class__, self).apply()
        if self.active:
            self._update_field(self._enable_ARP, 'protocolServer.enableArpResponse')
            self._update_field(self._enable_PING, 'protocolServer.enablePingResponse')
        caller_name = inspect.stack()[1][3]
        need_write = False if caller_name is "apply" else True
        if need_write:
            try:
                rc = self._driver_obj.write()
            except Exception as e:
                raise Exception("Failed apply IxRouter: " + e.message)

    def _rsetattr(self, obj, attr, val):
        pre, _, post = attr.rpartition('.')
        return setattr(self._rgetattr(obj, pre) if pre else obj, post, val)

    def _rgetattr(self, obj, attr, default=_sentinel):
        if default is ixProtocolManagment._sentinel:
            _getattr = getattr
        else:
            def _getattr(obj, name):
                return getattr(obj, name, default)
        return functools.reduce(_getattr, [obj] + attr.split('.'))

    def _update_field(self, api_field=None, driver_field=None, value=None, exception_info=""):
        try:
            val = None
            # case 1 - field is hidden from api
            if api_field is None:
                if type(value) == attrWithDefault:
                    val = value.current_val
                else:
                    val = value
                # api_field._previous_val = api_field._current_val
                self._rsetattr(self._driver_obj, driver_field, val)
                if self._debug_prints: print ("updating " + driver_field)
            else:
                if not driver_field and api_field._driver_field:
                    driver_field = api_field._driver_field
                else:
                    api_field._driver_field = driver_field
                # case 2 - value was never updated in driver
                if not api_field._was_written_to_driver:
                    if value is None:
                        api_field._previous_val = api_field._current_val
                        val = api_field._current_val
                        self._rsetattr(self._driver_obj,driver_field, val)
                        if self._debug_prints: print ("updating " + driver_field)
                        api_field._was_written_to_driver = True
                    else:
                        if type(value) == attrWithDefault:
                            val = value.current_val
                        else:
                            val = value
                        api_field._previous_val = api_field._current_val
                        self._rsetattr(self._driver_obj, driver_field, val)
                        if self._debug_prints: print ("updating " + driver_field)
                        api_field._was_written_to_driver = True
                # case 3 - value is different than previous
                elif api_field._current_val != api_field._previous_val:
                    if value is None:
                        api_field._previous_val = api_field._current_val
                        val = api_field._current_val
                        self._rsetattr(self._driver_obj, driver_field, val)
                        if self._debug_prints: print ("updating " + driver_field)
                        api_field._was_written_to_driver = True
                    else:
                        if type(value) == attrWithDefault:
                            val = value.current_val
                        else:
                            val = value
                        self._rsetattr(self._driver_obj, driver_field, val)
                        if self._debug_prints: print ("updating " + driver_field)
                        api_field._was_written_to_driver = True
                else:
                    if self._debug_prints: print ("no update need for " + driver_field)
        except Exception as e:
            raise Exception("Error in update field.\nField name = " + driver_field +
                            "\nValue to set: " + str(val) +
                            "\n"+ exception_info +
                            "\n"+ str(self) +
                            "\nDriver Exeption:\n" + str(e))


class IxProtocolInterfaces(protocolInterfaces):
    def __init__(self, parent):
        super(self.__class__, self).__init__(parent)
        self.interfaces = OrderedDict()  # type: list[IxProtocolInterface]
        self._count = 0
        self._if_key_2local = OrderedDict()

    def add_interface(self):
        self._count+=1
        if_name = self._parent._parent._port_uri + '_IF_' + str(self._count)
        self.interfaces[if_name] = IxProtocolInterface()
        self.interfaces[if_name]._parent = self
        return if_name

    def remove_interface(self,if_name):
        del self.interfaces[if_name]

    def send_arp(self):
        self._driver_obj.interfaceTable.send_arp()

    def send_neighbor_solicitation(self):
        self._driver_obj.wait_for_up(20)
        self._driver_obj.interfaceTable.send_NS()

    def send_router_solicitation(self):
        self._driver_obj.wait_for_up(20)
        self._driver_obj.interfaceTable.send_RS()

    def clear_neigbors_table(self):
        self._driver_obj.interfaceTable.send_arp_clear()
        self._driver_obj.interfaceTable.send_NS_clear()
        self.discovered_neighbors = OrderedDict()

    def _clear_interface(self,if_name):
        self._driver_obj.interfaceTable.send_arp_clear(if_name)
        self.discovered_neighbors[if_name] = []

    def read_neigbors_table(self):
        self._driver_obj.wait_for_up(20)
        self._driver_obj.interfaceTable.send_arp_refresh()
        self._driver_obj.interfaceTable.send_NS_refresh()
        res_table = self._driver_obj.interfaceTable.read_port_neighbors()
        self.discovered_neighbors = OrderedDict()
        self._update_neighbors(res_table)

    def _update_neighbors(self,neighbor_table):
        for if_key in neighbor_table:
            iface_table = neighbor_table[if_key]
            local_key = self._if_key_2local[if_key]
            self.discovered_neighbors[local_key] = []
            for entry in iface_table:
                self.discovered_neighbors[local_key].append(learned_entry(entry[0], entry[1]))

    def apply(self):
        self._parent._driver_obj.interfaceTable.init()
        self._driver_obj.interfaceTable.enableAutoArp = self.auto_arp
        self._driver_obj.interfaceTable.enableTargetLinkLayerAddrOption = self.target_link_option
        self._driver_obj.interfaceTable.enableAutoNeighborDiscovery = self.auto_neighbor_discovery
        for if_name in self.interfaces:
            utg_if = self.interfaces[if_name]   # type: IxProtocolInterface
            if_obj = self._driver_obj.interfaceEntry
            if_obj.clear_all_items()
            if_obj.ix_set_default()
            if utg_if.ipv4.address:
                v4_obj = self._driver_obj.interfaceIpV4
                v4_obj.ix_set_default()
                v4_obj.ipAddress = utg_if.ipv4.address
                v4_obj.gatewayIpAddress = utg_if.ipv4.gateway
                v4_obj.maskWidth = utg_if.ipv4.mask
                if_obj.add_item()
            if utg_if.ipv6.address:
                v6_obj = self._driver_obj.interfaceIpV6
                v6_obj.ix_set_default()
                v6_obj.ipAddress = utg_if.ipv6.address
                v6_obj.maskWidth = utg_if.ipv6.mask
                if_obj.ipV6Gateway = utg_if.ipv6.gateway
                if_obj.add_item(v6=True)
                for utg_v6_entry in utg_if.ipv6.additional_v6_entries:
                    v6_obj.ix_set_default()
                    v6_obj.ipAddress = utg_v6_entry.address
                    v6_obj.maskWidth = utg_v6_entry.mask
                    if_obj.ipV6Gateway = utg_v6_entry.gateway
                    if_obj.add_item(v6=True)
            if utg_if.vlans.enable:
                if_obj.enableVlan = True
                if_obj.vlanId = str('{'+utg_if.vlans.vid+'}')
                if_obj.vlanPriority = str('{'+utg_if.vlans.priority+'}')
                if_obj.vlanTPID = str('{'+utg_if.vlans.tpid+'}')
            if_obj.enable = utg_if.enable
            if_obj.description = '{'+if_name + " ==>> " + utg_if.description+'}'
            utg_if._driver_if_key = '{'+if_name + " ==>> " + utg_if.description+'}'
            if_obj.macAddress = utg_if.mac_addr
            self._if_key_2local[utg_if._driver_if_key] = if_name
            self._driver_obj.interfaceTable.add_if()


class IxProtocolInterface(protocolInterface):
    def __init__(self):
        super(self.__class__, self).__init__()

    def clear_arp(self):
        self._parent._clear_interface(self._driver_if_key)

    def send_arp(self):
        self._parent._driver_obj.wait_for_up(20)
        self._parent._driver_obj.interfaceTable.send_arp(self._driver_if_key)

    def refresh_arp(self):
        self._parent._driver_obj.wait_for_up(20)
        self._parent._driver_obj.interfaceTable.send_arp_refresh(self._driver_if_key)
        res_table = self._parent._driver_obj.interfaceTable.read_port_neighbors(self._driver_if_key)
        self._parent._update_neighbors(res_table)

    def send_ping(self,ip_dest):
        self._parent._driver_obj.wait_for_up(20)
        self._parent._driver_obj.interfaceTable.send_ping(self._driver_if_key, ip_dest)


class Ix_arp_table(arp_table):

    def __init__(self):
        super(self.__class__, self).__init__()

    def clear(self):
        self._parent._driver_obj.wait_for_up(20)
        self.learned_table = []
        self._parent._driver_obj.interfaceTable.send_arp_clear()

    def refresh(self):
        self._parent._driver_obj.wait_for_up(20)
        self._parent._driver_obj.interfaceTable.send_arp_refresh()
        res_table = self._parent._driver_obj.interfaceTable.read_port_neighbors()
        self.learned_table = []
        for if_key in res_table:
            iface_table = res_table[if_key]
            for entry in iface_table:
                isIp4 = True if Converter.intIp2string(Converter.uc23(entry[1])) else False
                if isIp4:
                    self.learned_table.append(learned_entry(entry[0], entry[1]))

    def transmit(self):
        self._parent._driver_obj.wait_for_up(20)
        self._parent._driver_obj.interfaceTable.send_arp()

    def apply(self):
        self._parent._driver_obj.arpServer.mode = self.arp_for.value
        self._parent._driver_obj.arpServer.retries = self.retries
        self._parent._driver_obj.arpServer.requestRepeatCount = self.count