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

from UnifiedTG.Unified.TGEnums import TGEnums
from CLI_GlobalFunctions.SwitchDev.Bridge.Bridge1QConfig import Bridge1QConfig
from PyInfra.BaseTest_SV.SV_Enums.SwitchDevInterface import SwitchDevDutInterface
from Tests.Implementations.ACL.APIs.AclAPI import AclAPI


class RoutedAclAPI(AclAPI):

    def __init__(self, testClass):
        super(RoutedAclAPI, self).__init__(testClass)
        self._bridge = Bridge1QConfig(SwitchDevDutInterface('br0'))

    def addIPv6ProtocolInterface(self, port, streamDits):
        tgPort = port.TGPort
        portIntKey = tgPort.protocol_managment.protocol_interfaces.add_interface()
        portInt = tgPort.protocol_managment.protocol_interfaces.interfaces[portIntKey]
        portInt.enable = True
        portInt.description = str(port)
        portInt.ipv6.mask = 64
        portInt.ipv6.address = streamDits['src_ip']
        portInt.ipv6.gateway = streamDits['gw']
        tgPort.protocol_managment.protocol_interfaces.auto_neighbor_discovery = True
        return portIntKey

    def ipv6Stream(self, port, dst_ip, src_ip=None, ip_proto=None, dst_port=None, src_port=None, streamName: str = None,
                   portIntKey=None,  **kwargs):
        if not streamName:
            streamName = f'test#{len(list(port.TGPort.streams.keys())) + 1}'
        port.TGPort.add_stream(streamName)
        stream = port.TGPort.streams[streamName]
        stream.packet.l2_proto = TGEnums.L2_PROTO.ETHERNETII
        stream.packet.l3_proto = TGEnums.L3_PROTO.IPV6
        stream.packet.ipv6.destination_ip.value = dst_ip
        stream.control.packets_per_burst = self.numOfPackets
        if dst_port:
            stream.packet.udp.destination_port.value = dst_port
        if src_port:
            stream.packet.udp.source_port.value = src_port
        if ip_proto:
            stream.packet.l4_proto = TGEnums.L4_PROTO.TCP if ip_proto == 'tcp' else TGEnums.L4_PROTO.UDP

        if portIntKey:
            stream.source_interface.enabled = True
            stream.source_interface.description_key = portIntKey
        elif src_ip:
            stream.packet.ipv6.source_ip.value = src_ip

        if kwargs:
            self._addMoreStreamSettings({port: {streamName: kwargs}})
        self.logger.debug(stream)

    def applyTGSettings(self, txPorts, rxPorts=None):
        if rxPorts is None:
            rxPorts = []
        for port in txPorts + rxPorts:
            port.TGPort.protocol_managment.apply()
            port.TGPort.protocol_managment.arp_table.transmit()
        super(RoutedAclAPI, self).applyTGSettings(txPorts, rxPorts)

    def overflowTable(self, devOrBlock, selector='src_ip', action='pass', startAddress='', incStep=1):

        listOfRules = []
        if isinstance(devOrBlock, int):
            devOrBlockSelector = f"block {devOrBlock}"
        else:
            devOrBlockSelector = f"dev {devOrBlock.DutDevPort.name} ingress"
        if selector in ('src_ip', 'dst_ip'):  # ipv4 overflowing
            import ipaddress
            ipAddr = ipaddress.ip_address(startAddress)
            for i in range(incStep):
                listOfRules.append(
                    f"tc filter add {devOrBlockSelector} protocol ip flower skip_sw {selector} {ipAddr + i} action {action}")

        strOfAllRules = '\n'.join(listOfRules)
        self.logger.debug(strOfAllRules)
        from CLI_GlobalFunctions.SwitchDev.CLICommands.Executer import GlobalGetterSetter
        err = GlobalGetterSetter().getter.execAsFile(strOfAllRules)
        if err:
            self.FailTheTest(err)

    def applyStreams(self, txPorts):
        super(RoutedAclAPI, self).applyStreams(txPorts)
        # For some reason, the following lines are needed to apply streams in Ixia card NOVUS10
        for port in txPorts:
            port.TGPort.apply_port_config()
            import time
            time.sleep(40)
            port.TGPort.apply_port_config()