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
from UnifiedTG.IxNetworkRestPy.IxNetworkRestPyEnums import ixNetworkRestPyEnums
from UnifiedTG.IxNetworkRestPy.IxNetworkRestPyImport import TrafficItem
from UnifiedTG.IxNetworkRestPy.IxNetworkRestPyPort import ixnRestpyPort



class TgHelper(object):
    def __init__(self,tg):
        from UnifiedTG.IxNetworkRestPy.IxNetworkRestPyTG import ixNetworkRestPyTG
        self._tg = tg  # type: ixNetworkRestPyTG

    def _get_proto_template(self, protocol_type):
        return self._tg.ixnetwork.Traffic.ProtocolTemplate.find(StackTypeId=protocol_type.value)

    def add_traffic_header(self, trafficItem, headerTypeToAdd, afterHeader):
        appendToStackObj = self.get_traffic_header(trafficItem, afterHeader)
        temp_header = self._get_proto_template(headerTypeToAdd)
        appendToStackObj.Append(Arg2=temp_header)
        return self.get_traffic_header(trafficItem, headerTypeToAdd)

    def get_traffic_header(self, trafficItem, header_type):
        stackObj = self._tg.traffic_items[trafficItem].ConfigElement.find().Stack.find()
        stackHeaderObj = stackObj.find(StackTypeId=header_type.value)
        return stackHeaderObj

    def add_topology(self, topology_name, ports=None):
        self._tg.topology[topology_name] = self._tg.ixnetwork.Topology.add(topology_name)
        is_object = True if isinstance(ports[0], ixnRestpyPort) else False
        if ports:
            vports = \
                [p._port_driver_obj for p in ports] if is_object else [self._tg.ports[p]._port_driver_obj for p in ports]
            self._tg.topology[topology_name].Vports = vports

    def add_device_group(self,topology_name,device_group_name ):
        self._tg.device_group[device_group_name] = self._tg.topology[topology_name].DeviceGroup.add(1,device_group_name)

    def create_scenario(self, topologies):
        for tp in topologies:
            self.add_topology(tp[0], tp[1])
            for dg in tp[2]:
                self.add_device_group(tp[0], dg)

    def clear_scenario(self):
        #self._tg.ixnetwork.NewConfig()
        for tp in self._tg.topology:
            self._tg.topology[tp].remove()
        self._tg.topology = OrderedDict() # type: list[Topology]
        self._tg.device_group = OrderedDict()

    def clear_traffic(self):
        for tItem in self._tg.traffic_items:
            self._tg.traffic_items[tItem].remove()
        self._tg.traffic_items = OrderedDict()
        self._tg.endpoints = OrderedDict()


    def add_L4_7(self, name, endpoints, traffic_type=ixNetworkRestPyEnums.Traffic_Type.ipv6Application,
                 objective_type=ixNetworkRestPyEnums.AppLib_ObjectiveType.throughputMbps, objective_value=20,
                 flow_list=['7SHIFTS_Manager_Access'], generate=False):
        if name not in self._tg.traffic_items:
            self._tg.traffic_items[name] = self._tg.ixnetwork.Traffic.TrafficItem.add(Name=name,
                                                                                      TrafficItemType='applicationLibrary',
                                                                                      TrafficType=traffic_type.value)
            self._tg.ixnetwork.Traffic.TrafficItem.find().AppLibProfile.add()
            app_flow = self._tg.ixnetwork.Traffic.TrafficItem.find().AppLibProfile.find()
            app_flow.AddAppLibraryFlow(flow_list)
            app_flow.ObjectiveType = objective_type.value
            app_flow.ObjectiveValue = objective_value
        for ep in endpoints:
            self._tg.endpoints[ep[0]] = \
                self._tg.traffic_items[name].EndpointSet.add(Sources=self._tg.topology[ep[1]],
                                                             Destinations=self._tg.topology[ep[2]])
        if generate:
            self._tg.traffic_items[name].Generate()
        return self._tg.traffic_items[name]  # type: TrafficItem

    def add_L2_3(self, name, traffic_type, endpoints, generate=False):
        if name not in self._tg.traffic_items:
            self._tg.traffic_items[name] = self._tg.ixnetwork.Traffic.TrafficItem.add(Name=name, TrafficType=traffic_type.value)
        for ep in endpoints:
            src = self._tg.topology[ep[1]].Vports[0].Protocols.find() if traffic_type is traffic_type.Raw else self._tg.topology[ep[1]]
            dst = self._tg.topology[ep[2]].Vports[0].Protocols.find() if traffic_type is traffic_type.Raw else self._tg.topology[ep[2]]
            self._tg.endpoints[ep[0]] = \
                self._tg.traffic_items[name].EndpointSet.add(Sources=src, Destinations=dst)
            self._tg.traffic_items[name].EndpointSet
        if generate:
            self._tg.traffic_items[name].Generate()
        return self._tg.traffic_items[name]  # type: TrafficItem
