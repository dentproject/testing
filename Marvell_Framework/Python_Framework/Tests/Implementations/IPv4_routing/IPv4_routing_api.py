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

from time import sleep
from UnifiedTG.Unified import Port
from UnifiedTG.Unified.Packet import DATA_PATTERN
from UnifiedTG.Unified.TGEnums import TGEnums
import re
import time
import ipaddress
from CLI_GlobalFunctions.SwitchDev.Bridge.BridgeConfig import BridgeConfig
from CLI_GlobalFunctions.SwitchDev.IPv4.IPv4Config import IPv4Config
from PyInfra.BaseTest_SV import BaseTest_SV_API
from PyInfra.BaseTest_SV.SV_Enums.SwitchDevInterface import SwitchDevDutInterface
from PyInfra.BaseTest_SV.SV_Enums.SwitchDevDutPort import SwitchDevDutPort
from PyInfraCommon.GlobalFunctions.Utils.Function import GetFunctionName
from PyInfraCommon.Managers.QueryTools.Comparator import Comparator


class IPv4_routing_api(BaseTest_SV_API):

    def __init__(self, TestClass):
        super(IPv4_routing_api, self).__init__(TestClass)
        self._bridge = None  # type: BridgeConfig
        self._port_list = [] #type: list[IPv4Config]
        self._port_list_SwitchDevDutInterface = [] #type: list[SwitchDevDutInterface]
        self._dut_port_list = [None]
        self._valid_regex_ip = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"


    def initInterfaces(self):
        funcname = GetFunctionName(self.initInterfaces)
        #init ports
        for i in range(1,len(list(self._testClassref.TGDutLinks.values()))+1):
            self._port_list.append(IPv4Config(SwitchDevDutPort(self._testClassref.TGDutLinks[i].DutDevPort.name)))
        self._port_list_SwitchDevDutInterface.extend([x.switchdevInterface for x in self._port_list])
        self._dut_port_list = self.getPortList()

    def getPortList(self):
        return IPv4Config.getPortList()

    def configureIPv4Forwarding(self,v):
        """
        sets forwarding
        :return:
        """
        funcname = GetFunctionName(self.configureIPv4Forwarding)
        IPv4Config.setIpv4Forwarding(str(v))
        self.Add_Cleanup_Function_To_Stack(IPv4Config.setIpv4Forwarding, '0')

    def configureICMPecho(self,v):
        """
        sets forwarding
        :return:
        """
        funcname = GetFunctionName(self.configureICMPecho)
        IPv4Config.setICMPecho(str(v))
        self.Add_Cleanup_Function_To_Stack(IPv4Config.setICMPecho, '0')

    def configureIPaddr(self, dev, ip_addr='', mask='', vlan=''):
        funcname = GetFunctionName(self.configureIPaddr)
        if "class_A" in self._testClassref.testName:
            if self._port_list[0] == dev:
                ip_addrs = self._testClassref.TestCaseData["classes"]["class_A"]["ip1"]
                ip_mask = self._testClassref.TestCaseData["classes"]["class_A"]["mask"]
                ret = dev.setIP(ip_addrs, ip_mask)
                self.Add_Cleanup_Function_To_Stack(dev.delIP, ip_addrs, ip_mask)
            else:
                ip_addrs = self._testClassref.TestCaseData["classes"]["class_A"]["ip2"]
                ip_mask = self._testClassref.TestCaseData["classes"]["class_A"]["mask"]
                ret = dev.setIP(ip_addrs, ip_mask)
                self.Add_Cleanup_Function_To_Stack(dev.delIP, ip_addrs, ip_mask)
        elif "class_B" in self._testClassref.testName:
            if self._port_list[0] == dev:
                ip_addrs = self._testClassref.TestCaseData["classes"]["class_B"]["ip1"]
                ip_mask = self._testClassref.TestCaseData["classes"]["class_B"]["mask"]
                ret = dev.setIP(ip_addrs, ip_mask)
                self.Add_Cleanup_Function_To_Stack(dev.delIP, ip_addrs, ip_mask)
            else:
                ip_addrs = self._testClassref.TestCaseData["classes"]["class_B"]["ip2"]
                ip_mask = self._testClassref.TestCaseData["classes"]["class_B"]["mask"]
                ret = dev.setIP(ip_addrs, ip_mask)
                self.Add_Cleanup_Function_To_Stack(dev.delIP, ip_addrs, ip_mask)
        elif "class_C" in self._testClassref.testName:
            if self._port_list[0] == dev:
                ip_addrs = self._testClassref.TestCaseData["classes"]["class_C"]["ip1"]
                ip_mask = self._testClassref.TestCaseData["classes"]["class_C"]["mask"]
                ret = dev.setIP(ip_addrs, ip_mask)
                self.Add_Cleanup_Function_To_Stack(dev.delIP, ip_addrs, ip_mask)
            else:
                ip_addrs = self._testClassref.TestCaseData["classes"]["class_C"]["ip2"]
                ip_mask = self._testClassref.TestCaseData["classes"]["class_C"]["mask"]
                ret = dev.setIP(ip_addrs, ip_mask)
                self.Add_Cleanup_Function_To_Stack(dev.delIP, ip_addrs, ip_mask)
        elif "class_D" in self._testClassref.testName:
            if self._port_list[0] == dev:
                ip_addrs = self._testClassref.TestCaseData["classes"]["class_D"]["ip1"]
                ip_mask = self._testClassref.TestCaseData["classes"]["class_D"]["mask"]
                ret = dev.setIP(ip_addrs, ip_mask)
                self.Add_Cleanup_Function_To_Stack(dev.delIP, ip_addrs, ip_mask)
            else:
                ip_addrs = self._testClassref.TestCaseData["classes"]["class_D"]["ip2"]
                ip_mask = self._testClassref.TestCaseData["classes"]["class_D"]["mask"]
                ret = dev.setIP(ip_addrs, ip_mask)
                self.Add_Cleanup_Function_To_Stack(dev.delIP, ip_addrs, ip_mask)
        elif "class_E" in self._testClassref.testName:
            if self._port_list[0] == dev:
                ip_addrs = self._testClassref.TestCaseData["classes"]["class_E"]["ip1"]
                ip_mask = self._testClassref.TestCaseData["classes"]["class_E"]["mask"]
                ret = dev.setIP(ip_addrs, ip_mask)
                self.Add_Cleanup_Function_To_Stack(dev.delIP, ip_addrs, ip_mask)
            else:
                ip_addrs = self._testClassref.TestCaseData["classes"]["class_E"]["ip2"]
                ip_mask = self._testClassref.TestCaseData["classes"]["class_E"]["mask"]
                ret = dev.setIP(ip_addrs, ip_mask)
                self.Add_Cleanup_Function_To_Stack(dev.delIP, ip_addrs, ip_mask)
        elif "random_routing" in self._testClassref.testName:
            ip_addrs = ip_addr
            ip_mask = self._testClassref.TestCaseData["ip"]["mask"]
            ret = IPv4Config.setGlobIP(ip_addrs, ip_mask, dev)
            self.Add_Cleanup_Function_To_Stack(IPv4Config.delGlobIP, ip_addrs, ip_mask, dev)
        elif "IPv4_max_HOST_max_FDB" in self._testClassref.testName:
            ip_addrs = self._testClassref.TestCaseData["ip"]["1"]
            ip_mask = self._testClassref.TestCaseData["ip"]["mask"]
            ret = dev.setIP(ip_addrs, ip_mask)
            self.Add_Cleanup_Function_To_Stack(dev.delIP, ip_addrs, ip_mask)
        elif "route_between_vlans" in self._testClassref.testName:
            ip_addrs = self._testClassref.TestCaseData["ip"][str(vlan)[0]]
            ip_mask = self._testClassref.TestCaseData["ip"]["mask"]
            ret = dev.setIPVlanDev(ip_addrs, ip_mask, vlan)
        elif self._testClassref.TestData.TestInfo.Suite_Name == 'ECMP':
            ip_addrs = self._testClassref.TestCaseData["ip"][str(self._port_list.index(dev) + 1)]
            ip_mask = self._testClassref.TestCaseData["ip"][f"mask{str(self._port_list.index(dev) + 1)}"]
            ret = IPv4Config.setGlobIP(ip_addrs, ip_mask, dev)
            self.Add_Cleanup_Function_To_Stack(IPv4Config.delGlobIP, ip_addrs, ip_mask, dev)
        else:
            ip_addrs = self._testClassref.TestCaseData["ip"][str(self._port_list.index(dev) + 1)]
            ip_mask = self._testClassref.TestCaseData["ip"]["mask"]
            ret = dev.setIP(ip_addrs, ip_mask)
            self.Add_Cleanup_Function_To_Stack(dev.delIP, ip_addrs, ip_mask)
        if ret:
            self.FailTheTest(f"{funcname} {ret} {ip_addrs}/{ip_mask} unable to configure ip addr on {dev}!")

    def getIPaddr(self,port):
        funcname = GetFunctionName(self.getIPaddr)
        ret = IPv4Config.glblGetIPAddr(port)
        if not re.match(self._valid_regex_ip, ret):
            self.FailTheTest(f"{funcname} {ret} failed to get {port} addr!")
        return ret


    def configureDefGw(self, dev):
        funcname = GetFunctionName(self.configureDefGw)
        gw = self._testClassref.TestCaseData["def_gw"][str(self._port_list.index(dev)+1)]
        if 'not_connected' in self._testClassref.testName:
            gw = self._testClassref.TestCaseData["def_not_connected_gw"][str(self._port_list.index(dev)+1)]
            ret = dev.setDefGw(gw)
            if 'Network is unreachable' not in ret:
                self.FailTheTest(f"{funcname} {ret} unable to configure ip gw {gw} on {dev.switchdevInterface.name}!")
            self.Add_Cleanup_Function_To_Stack(dev.remDefGw, gw)
        else:
            ret = dev.setDefGw(gw)
            if ret:
                self.FailTheTest(f"{funcname} {ret} unable to configure ip gw {gw} on {dev.switchdevInterface.name}!")
            self.Add_Cleanup_Function_To_Stack(dev.remDefGw, gw)

    def checkDefGw(self, dev):
        funcname = GetFunctionName(self.checkDefGw)
        ret = IPv4Config.getRoute(dev)
        gw = self._testClassref.TestCaseData["def_gw"][str(self._port_list.index(dev)+1)]
        if f'default via {gw} dev {dev.switchdevInterface.name}' not in ret:
            self.FailTheTest(f"{funcname} {ret} default gw wasn't found for {dev.switchdevInterface.name}!")

    def configureStaticArpEntry(self, dev):
        funcname = GetFunctionName(self.configureStaticArpEntry)
        ip_arp_addr = self._testClassref.TestCaseData["ip_arp"][str(self._port_list.index(dev)+1)]
        mac_addr = self._testClassref.TestCaseData["macs"][str(self._port_list.index(dev)+1)]
        ret = dev.setARPEntry(ip_arp_addr, mac_addr)
        if ret:
            self.FailTheTest(f"{funcname} {ret} unable to config static {ip_arp_addr} {mac_addr} arp entry for {dev.switchdevInterface.name}!")
        #self.Add_Cleanup_Function_To_Stack(dev.remARPEntry, self._testClassref.TestCaseData["ip"][dev.switchdevInterface.name])

    def configurePermanentNeigh(self, dev):
        funcname = GetFunctionName(self.configurePermanentNeigh)
        ip_neigh_addr = self._testClassref.TestCaseData["ip_arp"][str(self._port_list.index(dev)+1)]
        mac_addr = self._testClassref.TestCaseData["ip_arp"][f"arp_mac{str(self._port_list.index(dev)+1)}"]
        ret = dev.setNEIGHEntry(ip_neigh_addr, mac_addr)
        if ret:
            self.FailTheTest(f"{funcname} {ret} unable to config static {ip_neigh_addr} {mac_addr} neigh entry for {dev.switchdevInterface.name}!")
        self.Add_Cleanup_Function_To_Stack(dev.remNEIGHEntry, ip_neigh_addr, mac_addr)

    def fillARPStaticEntries(self, dev, mask=22):
        funcname = GetFunctionName(self.configureStaticArpEntry)
        mac_addr = self._testClassref.TestCaseData["macs"][str(self._port_list.index(dev)+1)]
        net4 = ipaddress.ip_network(f'192.0.0.0/{mask}')
        for ip_arp_addr in net4.hosts():
            ret = dev.setNEIGHEntry(ip_arp_addr, mac_addr)
            if ret:
                self.FailTheTest(
                    f"{funcname} {ret} unable to config static {ip_arp_addr} {mac_addr} arp entry for {dev.switchdevInterface.name}!")

    def remStaticArpEntry(self, dev):
        funcname = GetFunctionName(self.configureStaticArpEntry)
        ip_arp_addr = self._testClassref.TestCaseData["ip_arp"][str(self._port_list.index(dev)+1)]
        ret = dev.remARPEntry(ip_arp_addr)
        if ret:
            self.FailTheTest(f"{funcname} {ret} unable to remove static arp entry for {dev.switchdevInterface.name}!")

    def checkArpEntry(self, dev):
        funcname = GetFunctionName(self.checkArpEntry)
        ret = dev.getPortArpEntries()
        ip_arp_addr = self._testClassref.TestCaseData["ip_arp"][str(self._port_list.index(dev)+1)]
        mac_entry = self._testClassref.TestCaseData["macs"][str(self._port_list.index(dev)+1)]
        if 'arp_aging' in self._testClassref.testName and ip_arp_addr in ret and mac_entry in ret:
            self.FailTheTest(f"{funcname} {ip_arp_addr} {mac_entry} Arp Entry was found after aging time expired for {dev.switchdevInterface.name}!")
        elif ip_arp_addr not in ret and mac_entry not in ret and 'arp_aging' not in self._testClassref.testName:
            self.FailTheTest(f"{funcname} {ip_arp_addr} {mac_entry} Arp Entry wasn't found for {dev.switchdevInterface.name}!")

    def checkArpEntryNotInTable(self, dev):
        funcname = GetFunctionName(self.checkArpEntry)
        ret = dev.getPortArpEntries()
        ip_arp_addr = self._testClassref.TestCaseData["ip_arp"][str(self._port_list.index(dev)+1)]
        mac_entry = self._testClassref.TestCaseData["macs"][str(self._port_list.index(dev)+1)]
        if "class_A" in self._testClassref.testName:
            if self._port_list[0] == dev:
                ip_arp_addr = self._testClassref.TestCaseData["classes"]["class_A"]["ip_arp1"]
                mac_entry = self._testClassref.TestCaseData["macs"][str(self._port_list.index(dev)+1)]
            else:
                ip_arp_addr = self._testClassref.TestCaseData["classes"]["class_A"]["ip_arp2"]
                mac_entry = self._testClassref.TestCaseData["macs"][str(self._port_list.index(dev)+1)]
        elif "class_B" in self._testClassref.testName:
            if self._port_list[0] == dev:
                ip_arp_addr = self._testClassref.TestCaseData["classes"]["class_B"]["ip_arp1"]
                mac_entry = self._testClassref.TestCaseData["macs"][str(self._port_list.index(dev)+1)]
            else:
                ip_arp_addr = self._testClassref.TestCaseData["classes"]["class_B"]["ip_arp2"]
                mac_entry = self._testClassref.TestCaseData["macs"][str(self._port_list.index(dev)+1)]
        elif "class_C" in self._testClassref.testName:
            if self._port_list[0] == dev:
                ip_arp_addr = self._testClassref.TestCaseData["classes"]["class_C"]["ip_arp1"]
                mac_entry = self._testClassref.TestCaseData["macs"][str(self._port_list.index(dev)+1)]
            else:
                ip_arp_addr = self._testClassref.TestCaseData["classes"]["class_C"]["ip_arp2"]
                mac_entry = self._testClassref.TestCaseData["macs"][str(self._port_list.index(dev)+1)]
        elif "class_D" in self._testClassref.testName:
            if self._port_list[0] == dev:
                ip_arp_addr = self._testClassref.TestCaseData["classes"]["class_D"]["ip_arp1"]
                mac_entry = self._testClassref.TestCaseData["macs"][str(self._port_list.index(dev)+1)]
            else:
                ip_arp_addr = self._testClassref.TestCaseData["classes"]["class_D"]["ip_arp2"]
                mac_entry = self._testClassref.TestCaseData["macs"][str(self._port_list.index(dev)+1)]
        elif "class_E" in self._testClassref.testName:
            if self._port_list[0] == dev:
                ip_arp_addr = self._testClassref.TestCaseData["classes"]["class_E"]["ip_arp1"]
                mac_entry = self._testClassref.TestCaseData["macs"][str(self._port_list.index(dev)+1)]
            else:
                ip_arp_addr = self._testClassref.TestCaseData["classes"]["class_E"]["ip_arp2"]
                mac_entry = self._testClassref.TestCaseData["macs"][str(self._port_list.index(dev)+1)]
        if ip_arp_addr in ret and mac_entry in ret:
            self.FailTheTest(f"{funcname} {ret} {mac_entry} {ip_arp_addr} Arp Entry was found for {dev.switchdevInterface.name}!")

    def countARPentries(self):
        funcname = GetFunctionName(self.countARPentries)
        ret = IPv4Config.getARPEntries()
        amount = self._testClassref.TestCaseData["arp_table"]["min_val"]
        if "IPv4_arp_overflow_static" in self._testClassref.testName:
            amount = self._testClassref.TestCaseData["arp_static_table"][self._testClassref.TestData.DutInfo.Board_Model]["size"]
        if int(ret) < amount:
            self.FailTheTest(f"{funcname} {ret} ARP num of entries didn't match expected {amount}!")

    def countRouteEntries(self):
        funcname = GetFunctionName(self.countRouteEntries)
        ret = IPv4Config.getRouteEntries()
        amount = self._testClassref.TestCaseData["route_table"][self._testClassref.TestData.DutInfo.Board_Model]["size"]
        if int(ret) < amount:
            self.FailTheTest(f"{funcname} {ret} route num of entries didn't match expected {amount}!")

    def configureArpReachableTimeout(self, dev, timeout):
        funcname = GetFunctionName(self.configureArpReachableTimeout)
        ret = dev.setReachableTimeout(timeout)
        if ret:
            self.FailTheTest(f"{funcname} {ret} unable to config are reachable {timeout} timeout for {dev.switchdevInterface.name}!")
        self.Add_Cleanup_Function_To_Stack(dev.setReachableTimeout, 30)

    def configureArpIntervalTimeout(self, timeout):
        funcname = GetFunctionName(self.configureArpIntervalTimeout)
        ret = IPv4Config.setIntervalTimeout(timeout)
        if ret:
            self.FailTheTest(f"{funcname} {ret} unable to config arp interval {timeout} timeout!")
        self.Add_Cleanup_Function_To_Stack(IPv4Config.setIntervalTimeout, 30)

    def configure_gc_thresh1(self, num):
        funcname = GetFunctionName(self.configure_gc_thresh1)
        ret = IPv4Config.setArpTableMinEntries(num)
        if ret:
            self.FailTheTest(f"{funcname} {ret} unable to configure arp table min {num} entries!")
        self.Add_Cleanup_Function_To_Stack(IPv4Config.setArpTableMinEntries, 128)

    def configure_gc_thresh2(self, num):
        funcname = GetFunctionName(self.configure_gc_thresh2)
        ret = IPv4Config.setArpTableSoftMaxEntries(num)
        if ret:
            self.FailTheTest(f"{funcname} {ret} unable to configure arp table min {num} entries!")
        self.Add_Cleanup_Function_To_Stack(IPv4Config.setArpTableSoftMaxEntries, 2048)

    def configure_gc_thresh3(self, num):
        funcname = GetFunctionName(self.configure_gc_thresh3)
        ret = IPv4Config.setArpTableHardMaxEntries(num)
        if ret:
            self.FailTheTest(f"{funcname} {ret} unable to configure arp table min {num} entries!")
        self.Add_Cleanup_Function_To_Stack(IPv4Config.setArpTableHardMaxEntries, 4096)

    def configureAgingTimeout(self, dev, timeout):
        funcname = GetFunctionName(self.configureAgingTimeout)
        ret = dev.setAgingTimeout(timeout)
        if ret:
            self.FailTheTest(f"{funcname} {ret} unable to config aging timeout {timeout} for {dev.switchdevInterface.name}!")
        self.Add_Cleanup_Function_To_Stack(dev.setAgingTimeout, 60)

    def checkArpEntryReachablity(self, dev, isReach=True):
        funcname = GetFunctionName(self.checkArpEntryReachablity)
        ret = dev.getNeigh()
        if 'REACHABLE' in ret and not isReach:
            self.FailTheTest(f"{funcname} {ret} {dev.switchdevInterface.name} is in reachable mode!")

    def configureEntityUp(self, dev):
        funcname = GetFunctionName(self.configureEntityUp)
        ret = dev.setState('up')
        if ret:
            self.FailTheTest(f"{funcname} {ret} unable to set {dev.switchdevInterface.name} up")

    def configurePortUp(self, port):
        funcname = GetFunctionName(self.configurePortUp)
        ret = IPv4Config.setPortUp(port, 'up')
        if ret:
            self.FailTheTest(f"{funcname} {ret} unable to set {port} up")

    def configureEntityDown(self, dev):
        funcname = GetFunctionName(self.configureEntityDown)
        ret = dev.setState('down')
        if ret:
            self.FailTheTest(f"{funcname} {ret} unable to set {dev.switchdevInterface.name} down")
        self.Add_Cleanup_Function_To_Stack(dev.setState, "up")

    def pingRequest(self, dev, count=1, size=0, interval=1):
        funcname = GetFunctionName(self.pingRequest)
        addr = self._testClassref.TestCaseData["ip"][str(self._port_list.index(dev) + 1)]
        if 'ping_static' in self._testClassref.testName or 'ping_size' in self._testClassref.testName or 'ping_count' in self._testClassref.testName:
            addr = self._testClassref.TestCaseData["ip_arp"][str(self._port_list.index(dev)+1)]
        elif 'def_gw' in self._testClassref.testName:
            addr = self._testClassref.TestCaseData["def_gw"][str(self._port_list.index(dev)+1)]
        ret = dev.ping(count, size, interval, addr)
        if f'from {addr}' not in ret:
            self.FailTheTest(f"{funcname} {ret} unable to ping {dev.switchdevInterface.name} with addr {addr}")

    def addRoute(self, dev, ip_addr='', mask=24):
        funcname = GetFunctionName(self.addRoute)
        ret = dev.addRouteNextHop(f"{ip_addr}/{mask}")
        if ret:
            self.FailTheTest(f"{funcname} {ret} unable to add route {ip_addr}/{mask} for {dev.switchdevInterface.name}")

    def addRouteNextHop(self, dev):
        funcname = GetFunctionName(self.addRouteNextHop)
        target = self._testClassref.TestCaseData["routes"][str(self._port_list.index(dev)+1)]
        target_mask = self._testClassref.TestCaseData["routes"][f"mask{str(self._port_list.index(dev)+1)}"]
        via = self._testClassref.TestCaseData["ip_arp"][str(self._port_list.index(dev)+1)]
        ret = dev.addRouteNextHop(routeTo=f"{target}/{target_mask}", via=via)
        if ret:
            self.FailTheTest(f"{funcname} {ret} unable to add route {target}/{target_mask} via {via}")

    def fillRoute(self, dev):
        funcname = GetFunctionName(self.addRoute)
        mask = self._testClassref.TestCaseData["route_table"][self._testClassref.TestData.DutInfo.Board_Model]["mask"]
        net4 = ipaddress.ip_network(f'192.0.0.0/{mask}')
        for addr in net4.hosts():
            ret = dev.addRoute(addr)
            if ret:
                self.FailTheTest(
                    f"{funcname} {ret} unable to add route {addr} for {dev.switchdevInterface.name}")

    def fillStaticRouteEntriesFromFile(self, dev):
        funcname = GetFunctionName(self.fillStaticRouteEntriesFromFile)
        index1 = self._testClassref.TestCaseData["route_table"][self._testClassref.TestData.DutInfo.Board_Model]["index1"]
        index2 = self._testClassref.TestCaseData["route_table"][self._testClassref.TestData.DutInfo.Board_Model][
            "index2"]
        ret = IPv4Config.fillStaticRouteEntries(index1=index1,index2=index2,
                                              dev=dev)
        if ret:
            self.FailTheTest(f"{funcname} {ret} error while trying to fill route table")

    def fillStaticArpEntriesFromFile(self, dev):
        funcname = GetFunctionName(self.fillStaticArpEntriesFromFile)
        index1 = self._testClassref.TestCaseData["arp_static_table"][self._testClassref.TestData.DutInfo.Board_Model]["index1"]
        index2 = self._testClassref.TestCaseData["arp_static_table"][self._testClassref.TestData.DutInfo.Board_Model][
            "index2"]
        mac = self._testClassref.TestCaseData["macs"][str(self._port_list.index(dev)+1)]
        ret = IPv4Config.fillStaticArpEntries(index1=index1,index2=index2, mac=mac,
                                              dev=dev)
        if ret:
            self.FailTheTest(f"{funcname} {ret} error while trying to fill arp table")

    def flushRouteTable(self):
        funcname = GetFunctionName(self.flushRouteTable)
        ret = IPv4Config.flushRouteEntries()
        if ret:
            self.FailTheTest(f"{funcname} {ret} there was a problem with flushing the route main table")


    def traceRoute(self, dev, max_ttl=30, nqueries=1):
        funcname = GetFunctionName(self.traceRoute)
        addr = self._testClassref.TestCaseData["ip_arp"][str(self._port_list.index(dev)+1)]
        ret = dev.traceroute(addr,max_ttl, nqueries)

    def setupStream(self, tx_port, rx_port, ttl=64, checksum=1,pktSize = 64, index=-1, vlan = 0, count=5, streamName="testStream"):
        # type: (object, object, object, object) -> object
        """
        :param tx_port:
        :param rx_port:
        :param vlan:
        :param count:
        :param pktSize:
        :return:
        """
        funcname = GetFunctionName(self.setupStream)
        self.logger.debug(funcname + "Setting up stream on tx port")
        data_pattern = DATA_PATTERN()
        data_pattern.type = TGEnums.DATA_PATTERN_TYPE.INCREMENT_BYTE

        TGTxPort = tx_port.TGPort  # type: Port
        TGRxPort = rx_port.TGPort


        #### ARP TX#####
        # protocol management
        # enable feature:
        TGTxPort.enable_protocol_managment = True
        TGTxPort.protocol_managment.enable_ARP = True
        TGTxPort.protocol_managment.enable_PING = True
        TGTxPort.protocol_managment.protocol_interfaces.auto_neighbor_discovery = True
        TGTxPort.protocol_managment.protocol_interfaces.auto_arp = True
        # protocol interfaces:
        # add interface
        p1_if_1 = TGTxPort.protocol_managment.protocol_interfaces.add_interface()
        # add v4
        TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].enable = True
        TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].description = 'P1'
        TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].mac_addr = self._testClassref.TestCaseData["macs"][str(tx_port.id)]

        if "class_A" in self._testClassref.testName:
            TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.address = \
            self._testClassref.TestCaseData["classes"]["class_A"]["ip_arp1"]
            TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.gateway = self._testClassref.TestCaseData["classes"]["class_A"]["ip1"]
            TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.mask = 8
        elif "class_B" in self._testClassref.testName:
            TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.address = \
            self._testClassref.TestCaseData["classes"]["class_B"]["ip_arp1"]
            TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.gateway = self._testClassref.TestCaseData["classes"]["class_B"]["ip1"]
            TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.mask = 16
        elif "class_C" in self._testClassref.testName:
            TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.address = \
            self._testClassref.TestCaseData["classes"]["class_C"]["ip_arp1"]
            TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.gateway = self._testClassref.TestCaseData["classes"]["class_C"]["ip1"]
            TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.mask = 24
        elif "class_D" in self._testClassref.testName:
            TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.address = \
            self._testClassref.TestCaseData["classes"]["class_D"]["ip_arp1"]
            TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.gateway = self._testClassref.TestCaseData["classes"]["class_D"]["ip1"]
            #TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.mask = 8
        elif "class_E" in self._testClassref.testName:
            TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.address = \
            self._testClassref.TestCaseData["classes"]["class_E"]["ip_arp1"]
            TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.gateway = self._testClassref.TestCaseData["classes"]["class_E"]["ip1"]
            #TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.mask = 8
        elif "random_routing" in self._testClassref.testName:
            TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.address = '.'.join(self.getIPaddr(tx_port.DutDevPort.name).split('.')[:-1]+['5'])
            TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.gateway = self.getIPaddr(tx_port.DutDevPort.name)
            TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.mask = 24
        elif "between_vlans" in self._testClassref.testName:
            TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].vlans.enable = True
            TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].vlans.vid = str(self._testClassref.TestCaseData["vlans"][f"vlan{tx_port.id}"])
            TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.address = \
            self._testClassref.TestCaseData["ip_arp"][str(tx_port.id)]
            TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.gateway = self._testClassref.TestCaseData["ip"][str(tx_port.id)]
            TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.mask = 24
        else:
            TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.address = \
            self._testClassref.TestCaseData["ip_arp"][str(tx_port.id)]
            TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.gateway = self._testClassref.TestCaseData["ip"][str(tx_port.id)]
            TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.mask = 24



        #### ARP RX#####
        # protocol management
        # enable feature:
        TGRxPort.enable_protocol_managment = True
        TGRxPort.protocol_managment.enable_ARP = True
        TGRxPort.protocol_managment.enable_PING = True
        TGRxPort.protocol_managment.protocol_interfaces.auto_neighbor_discovery = True
        TGRxPort.protocol_managment.protocol_interfaces.auto_arp = True

        # protocol interfaces:
        # add interface
        p2_if_2 = TGRxPort.protocol_managment.protocol_interfaces.add_interface()
        # add v4
        TGRxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].enable = True
        TGRxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].description = 'P2'
        TGRxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].mac_addr = self._testClassref.TestCaseData["macs"][str(rx_port.id)]
        if 'def_gw' in self._testClassref.testName:
            TGRxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].ipv4.address = \
            self._testClassref.TestCaseData["def_gw"][str(rx_port.id)]
        elif "class_A" in self._testClassref.testName:
            TGRxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].ipv4.address = self._testClassref.TestCaseData["classes"]["class_A"]["ip_arp2"]
            TGRxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].ipv4.gateway = self._testClassref.TestCaseData["classes"]["class_A"]["ip2"]
            TGRxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].ipv4.mask = 8
        elif "class_B" in self._testClassref.testName:
            TGRxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].ipv4.address = \
            self._testClassref.TestCaseData["classes"]["class_B"]["ip_arp2"]
            TGRxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].ipv4.gateway = self._testClassref.TestCaseData["classes"]["class_B"]["ip2"]
            TGRxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].ipv4.mask = 16
        elif "class_C" in self._testClassref.testName:
            TGRxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].ipv4.address = \
            self._testClassref.TestCaseData["classes"]["class_C"]["ip_arp2"]
            TGRxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].ipv4.gateway = self._testClassref.TestCaseData["classes"]["class_C"]["ip2"]
            TGRxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].ipv4.mask = 24
        elif "class_D" in self._testClassref.testName:
            TGRxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].ipv4.address = \
            self._testClassref.TestCaseData["classes"]["class_D"]["ip_arp2"]
            TGRxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].ipv4.gateway = self._testClassref.TestCaseData["classes"]["class_D"]["ip2"]
            #TGRxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].ipv4.mask = 8
        elif "class_E" in self._testClassref.testName:
            TGRxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].ipv4.address = \
            self._testClassref.TestCaseData["classes"]["class_E"]["ip_arp2"]
            TGRxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].ipv4.gateway = self._testClassref.TestCaseData["classes"]["class_E"]["ip2"]
            #TGRxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].ipv4.mask = 8
        elif "random_routing" in self._testClassref.testName:
            TGRxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].ipv4.address = '.'.join(self.getIPaddr(rx_port.DutDevPort.name).split('.')[:-1]+['5'])
            TGRxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].ipv4.gateway = self.getIPaddr(rx_port.DutDevPort.name)
            TGRxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].ipv4.mask = 24
        elif "between_vlans" in self._testClassref.testName:
            TGRxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].vlans.enable = True
            TGRxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].vlans.vid = str(self._testClassref.TestCaseData["vlans"][f"vlan{rx_port.id}"])
            TGRxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].ipv4.address = \
            self._testClassref.TestCaseData["ip_arp"][str(rx_port.id)]  # 2.2.2.5
            TGRxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].ipv4.gateway = \
            self._testClassref.TestCaseData["ip"][str(rx_port.id)]  # 2.2.2.2
            TGRxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].ipv4.mask = 24
        else:
            TGRxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].ipv4.address = \
            self._testClassref.TestCaseData["ip_arp"][str(rx_port.id)]  # 2.2.2.5
            TGRxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].ipv4.gateway = \
            self._testClassref.TestCaseData["ip"][str(rx_port.id)]  # 2.2.2.2
            TGRxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].ipv4.mask = 24

        #############STREAM SETTING#############
        TGTxPort.add_stream(streamName)
        TGTxPort.streams[streamName].packet.mac.da.mode = TGEnums.MODIFIER_MAC_MODE.FIXED
        TGTxPort.streams[streamName].frame_size.value = pktSize
        TGTxPort.streams[streamName].rate.mode = TGEnums.STREAM_RATE_MODE.UTILIZATION
        TGTxPort.streams[streamName].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
        if ttl == 0 or ttl == 1:
            TGTxPort.streams[streamName].control.mode = TGEnums.STREAM_TRANSMIT_MODE.ADVANCE_TO_NEXT_STREAM
        if checksum == 0:
            TGTxPort.streams[streamName].packet.ipv4.checksum_mode = TGEnums.CHECKSUM_MODE.INVALID
        TGTxPort.streams[streamName].rate.pps_value = 10
        TGTxPort.streams[streamName].control.packets_per_burst = 2
        TGTxPort.streams[streamName].rate.utilization_value = 100
        TGTxPort.streams[streamName].packet.ipv4.ttl = ttl
        TGTxPort.streams[streamName].packet.l3_proto = TGEnums.L3_PROTO.IPV4
        TGTxPort.streams[streamName].source_interface.enabled = True
        TGTxPort.streams[streamName].source_interface.description_key = p1_if_1
        TGTxPort.streams[streamName].packet.ipv4.destination_ip.value = self._testClassref.TestCaseData["ip_arp"][str(rx_port.id)]
        if 'icmp_unreachable' in self._testClassref.testName:
            TGTxPort.streams[streamName].packet.ipv4.destination_ip.value = self._testClassref.TestCaseData["def_gw"][
                str(rx_port.id)]
            TGTxPort.streams[streamName].control.packets_per_burst = 10
            #TGTxPort.streams["testStream"].control.mode = TGEnums.STREAM_TRANSMIT_MODE.CONTINUOUS_PACKET
        elif 'icmp_disabled' in self._testClassref.testName:
            TGTxPort.streams[streamName].packet.ipv4.destination_ip.value = self._testClassref.TestCaseData["ip"][
                str(tx_port.id)]
            TGTxPort.streams[streamName].packet.l4_proto = TGEnums.L4_PROTO.ICMP
            TGTxPort.streams[streamName].packet.icmp.icmp_type = TGEnums.ICMP_HEADER_TYPE.ECHO_REQUEST
        elif "random_routing" in self._testClassref.testName:
            TGTxPort.streams[streamName].packet.ipv4.destination_ip.value = '.'.join(self.getIPaddr(rx_port.DutDevPort.name).split('.')[:-1]+['5'])
        elif 'arp_overflow' in self._testClassref.testName or 'IPv4_max_HOST_max_FDB' in self._testClassref.testName:
            TGTxPort.streams[streamName].packet.l3_proto = TGEnums.L3_PROTO.ARP
            TGTxPort.streams[streamName].packet.arp.operation = TGEnums.ARP_OPERATION.ARP_REQUEST
            TGTxPort.streams[streamName].packet.arp.sender_hw.value = self._testClassref.TestCaseData["macs"][str(tx_port.id)]
            TGTxPort.streams[streamName].packet.arp.sender_hw.mode = TGEnums.MODIFIER_ARP_MODE.INCREMENT
            TGTxPort.streams[streamName].packet.arp.sender_hw.count = self._testClassref.TestCaseData["arp_table"]["size"]
            TGTxPort.streams[streamName].packet.arp.sender_ip.value = self._testClassref.TestCaseData["arp_table"]["init_addr"]
            TGTxPort.streams[streamName].packet.arp.sender_ip.mode = TGEnums.MODIFIER_ARP_MODE.INCREMENT
            TGTxPort.streams[streamName].packet.arp.sender_ip.count = self._testClassref.TestCaseData["arp_table"]["size"]
            TGTxPort.streams[streamName].packet.arp.target_hw.value = self._testClassref.TestCaseData["special_macs"]["broadcast"]
            TGTxPort.streams[streamName].packet.arp.target_hw.mode = TGEnums.MODIFIER_ARP_MODE.FIXED
            TGTxPort.streams[streamName].packet.arp.target_ip.value = self._testClassref.TestCaseData["ip"][str(tx_port.id)]
            TGTxPort.streams[streamName].packet.arp.target_ip.mode = TGEnums.MODIFIER_ARP_MODE.FIXED
            TGTxPort.streams[streamName].control.packets_per_burst = self._testClassref.TestCaseData["arp_table"]["size"]
            #TGTxPort.streams[streamName].rate.utilization_value = 1
            TGTxPort.streams[streamName].rate.mode = TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND
            TGTxPort.streams[streamName].rate.pps_value = 100


        ip_src_filter = " ".join(hex(int(i))[2:].rjust(2, "0") for i in
                                 self._testClassref.TestCaseData["ip_arp"][str(tx_port.id)].split('.'))
        ip_dst_filter = " ".join(hex(int(i))[2:].rjust(2, "0") for i in
                                 self._testClassref.TestCaseData["ip_arp"][str(rx_port.id)].split('.'))

        #IP CLASSES#
        if 'class_A' in self._testClassref.testName:
            TGTxPort.streams[streamName].packet.ipv4.destination_ip.value = self._testClassref.TestCaseData["classes"]["class_A"]["ip_arp2"]
            TGTxPort.streams[streamName].packet.ipv4.destination_ip.mode = TGEnums.MODIFIER_IPV4_ADDRESS_MODE.FIXED
            TGTxPort.streams[streamName].packet.ipv4.destination_ip.mask = "255.0.0.0"
            TGTxPort.streams[streamName].packet.ipv4.source_ip.mask = "255.0.0.0"
            ip_src_filter = " ".join(hex(int(i))[2:].rjust(2, "0") for i in
                                     self._testClassref.TestCaseData["classes"]["class_A"]["ip_arp1"].split('.'))
            ip_dst_filter = " ".join(hex(int(i))[2:].rjust(2, "0") for i in
                                     self._testClassref.TestCaseData["classes"]["class_A"]["ip_arp2"].split('.'))
        elif 'class_B' in self._testClassref.testName:
            TGTxPort.streams[streamName].packet.ipv4.destination_ip.value = \
            self._testClassref.TestCaseData["classes"]["class_B"]["ip_arp2"]
            TGTxPort.streams[streamName].packet.ipv4.destination_ip.mode = TGEnums.MODIFIER_IPV4_ADDRESS_MODE.FIXED
            TGTxPort.streams[streamName].packet.ipv4.destination_ip.mask = "255.255.0.0"
            TGTxPort.streams[streamName].packet.ipv4.source_ip.mask = "255.255.0.0"
            ip_src_filter = " ".join(hex(int(i))[2:].rjust(2, "0") for i in
                                     self._testClassref.TestCaseData["classes"]["class_B"]["ip_arp1"].split('.'))
            ip_dst_filter = " ".join(hex(int(i))[2:].rjust(2, "0") for i in
                                     self._testClassref.TestCaseData["classes"]["class_B"]["ip_arp2"].split('.'))
        elif 'class_C' in self._testClassref.testName:
            TGTxPort.streams[streamName].packet.ipv4.destination_ip.value = \
                self._testClassref.TestCaseData["classes"]["class_C"]["ip_arp2"]
            TGTxPort.streams[streamName].packet.ipv4.destination_ip.mode = TGEnums.MODIFIER_IPV4_ADDRESS_MODE.FIXED
            TGTxPort.streams[streamName].packet.ipv4.destination_ip.mask = "255.255.255.0"
            TGTxPort.streams[streamName].packet.ipv4.source_ip.mask = "255.255.255.0"
            ip_src_filter = " ".join(hex(int(i))[2:].rjust(2, "0") for i in
                                     self._testClassref.TestCaseData["classes"]["class_C"]["ip_arp1"].split('.'))
            ip_dst_filter = " ".join(hex(int(i))[2:].rjust(2, "0") for i in
                                     self._testClassref.TestCaseData["classes"]["class_C"]["ip_arp2"].split('.'))
        elif 'class_D' in self._testClassref.testName:
            TGTxPort.streams[streamName].packet.ipv4.destination_ip.value = \
                self._testClassref.TestCaseData["classes"]["class_D"]["ip_arp2"]
            TGTxPort.streams[streamName].packet.ipv4.destination_ip.mode = TGEnums.MODIFIER_IPV4_ADDRESS_MODE.FIXED
            #TGTxPort.streams["testStream"].packet.ipv4.destination_ip.mask = "0.0.0.0"
            #TGTxPort.streams["testStream"].packet.ipv4.source_ip.mask = "0.0.0.0"
            ip_src_filter = " ".join(hex(int(i))[2:].rjust(2, "0") for i in
                                     self._testClassref.TestCaseData["classes"]["class_D"]["ip_arp1"].split('.'))
            ip_dst_filter = " ".join(hex(int(i))[2:].rjust(2, "0") for i in
                                     self._testClassref.TestCaseData["classes"]["class_D"]["ip_arp2"].split('.'))
        elif 'class_E' in self._testClassref.testName:
            TGTxPort.streams[streamName].packet.ipv4.destination_ip.value = \
                self._testClassref.TestCaseData["classes"]["class_E"]["ip_arp2"]
            TGTxPort.streams[streamName].packet.ipv4.destination_ip.mode = TGEnums.MODIFIER_IPV4_ADDRESS_MODE.FIXED
            #TGTxPort.streams["testStream"].packet.ipv4.destination_ip.mask = "0.0.0.0"
            #TGTxPort.streams["testStream"].packet.ipv4.source_ip.mask = "0.0.0.0"
            ip_src_filter = " ".join(hex(int(i))[2:].rjust(2, "0") for i in
                                     self._testClassref.TestCaseData["classes"]["class_E"]["ip_arp1"].split('.'))
            ip_dst_filter = " ".join(hex(int(i))[2:].rjust(2, "0") for i in
                                     self._testClassref.TestCaseData["classes"]["class_E"]["ip_arp2"].split('.'))
        elif 'icmp_unreachable' in self._testClassref.testName:
            ip_dst_filter = " ".join(hex(int(i))[2:].rjust(2, "0") for i in
                                     self._testClassref.TestCaseData["def_gw"][str(rx_port.id)].split('.'))
        elif 'icmp_disabled' in self._testClassref.testName:
            ip_src_filter = " ".join(hex(int(i))[2:].rjust(2, "0") for i in
                                     self._testClassref.TestCaseData["ip"][str(tx_port.id)].split('.'))
            ip_dst_filter = " ".join(hex(int(i))[2:].rjust(2, "0") for i in
                                     self._testClassref.TestCaseData["ip_arp"][str(tx_port.id)].split('.'))
        elif "random_routing" in self._testClassref.testName:
            ip_src_filter = " ".join(hex(int(i))[2:].rjust(2, "0") for i in
                                     ('.'.join(self.getIPaddr(tx_port.DutDevPort.name).split('.')[:-1]+['5'])).split('.'))
            ip_dst_filter = " ".join(hex(int(i))[2:].rjust(2, "0") for i in
                                     ('.'.join(self.getIPaddr(rx_port.DutDevPort.name).split('.')[:-1]+['5'])).split('.'))
        elif 'ping_size' in self._testClassref.testName or 'ping_count' in self._testClassref.testName or 'traceroute_static' in self._testClassref.testName:
            ip_src_filter_1 = " ".join(hex(int(i))[2:].rjust(2, "0") for i in
                                     self._testClassref.TestCaseData["ip"][str(tx_port.id)].split('.'))
            ip_dst_filter_1 = " ".join(hex(int(i))[2:].rjust(2, "0") for i in
                                     self._testClassref.TestCaseData["ip_arp"][str(tx_port.id)].split('.'))
            ip_src_filter_2 = " ".join(hex(int(i))[2:].rjust(2, "0") for i in
                                     self._testClassref.TestCaseData["ip"][str(rx_port.id)].split('.'))
            ip_dst_filter_2 = " ".join(hex(int(i))[2:].rjust(2, "0") for i in
                                     self._testClassref.TestCaseData["ip_arp"][str(rx_port.id)].split('.'))

        if 'icmp_unreachable' in self._testClassref.testName:
            termDA_tx = TGTxPort.filter_properties.create_match_term(ip_dst_filter, 58)
            termSA_tx = TGTxPort.filter_properties.create_match_term(ip_src_filter, 54)

            myFilter_tx = TGTxPort.filter_properties.capture_filter
            myFilter_tx.enabled = True
            myFilter_tx.add_condition(termDA_tx)
            myFilter_tx.add_condition(termSA_tx)
            TGTxPort.apply_filters()
        elif 'icmp_disabled' in self._testClassref.testName:
            termDA_tx = TGTxPort.filter_properties.create_match_term(ip_dst_filter, 30)
            termSA_tx = TGTxPort.filter_properties.create_match_term(ip_src_filter, 26)

            myFilter_tx = TGTxPort.filter_properties.capture_filter
            myFilter_tx.enabled = True
            myFilter_tx.add_condition(termDA_tx)
            myFilter_tx.add_condition(termSA_tx)
            TGTxPort.apply_filters()
        elif 'ping_size' in self._testClassref.testName or 'ping_count' in self._testClassref.testName or 'traceroute_static' in self._testClassref.testName:
            myFilter_tx = TGTxPort.filter_properties.capture_filter
            myFilter_rx = TGRxPort.filter_properties.capture_filter
            myFilter_tx.enabled = True
            myFilter_rx.enabled = True

            if 'traceroute_static' in self._testClassref.testName:
                termProto_tx = TGTxPort.filter_properties.create_match_term('01', 22)
                termProto_rx = TGRxPort.filter_properties.create_match_term('01', 22)
                myFilter_tx.add_condition(termProto_tx)
                myFilter_rx.add_condition(termProto_rx)
            else:
                termSA_tx = TGTxPort.filter_properties.create_match_term(ip_src_filter_1, 26)
                termSA_rx = TGRxPort.filter_properties.create_match_term(ip_src_filter_2, 26)
                myFilter_tx.add_condition(termSA_tx)
                myFilter_rx.add_condition(termSA_rx)
                termDA_tx = TGTxPort.filter_properties.create_match_term(ip_dst_filter_1, 30)
                termDA_rx = TGRxPort.filter_properties.create_match_term(ip_dst_filter_2, 30)
                myFilter_tx.add_condition(termDA_tx)
                myFilter_rx.add_condition(termDA_rx)

            TGTxPort.apply_filters()
            TGRxPort.apply_filters()
        elif 'route_between_vlans' in self._testClassref.testName:
            termDA_rx = TGRxPort.filter_properties.create_match_term(ip_dst_filter, 34)
            termSA_rx = TGRxPort.filter_properties.create_match_term(ip_src_filter, 30)

            myFilter_rx = TGRxPort.filter_properties.capture_filter
            myFilter_rx.enabled = True
            myFilter_rx.add_condition(termDA_rx)
            myFilter_rx.add_condition(termSA_rx)
            TGRxPort.apply_filters()
        else:
            termDA_rx = TGRxPort.filter_properties.create_match_term(ip_dst_filter, 30)
            termSA_rx = TGRxPort.filter_properties.create_match_term(ip_src_filter, 26)

            myFilter_rx = TGRxPort.filter_properties.capture_filter
            myFilter_rx.enabled = True
            myFilter_rx.add_condition(termDA_rx)
            myFilter_rx.add_condition(termSA_rx)
            TGRxPort.apply_filters()

        # apply tx_port Ixroute config
        tx_port.TGPort.protocol_managment.apply()
        tx_port.TGPort.protocol_managment.arp_table.transmit()

        # apply rx_port Ixroute config
        rx_port.TGPort.protocol_managment.apply()
        rx_port.TGPort.protocol_managment.arp_table.transmit()

        # apply streams
        tx_port.TGPort.apply_streams()
        tx_port.TGPort.apply_port_config()
        time.sleep(30)
        tx_port.TGPort.apply_port_config()

    def setupRouteStream(self, tx_port, rx_port, ttl=64, pktSize = 64, streamName="testStream"):
        funcname = GetFunctionName(self.setupRouteStream)
        self.logger.debug(funcname + "Setting up stream on tx port")
        data_pattern = DATA_PATTERN()
        data_pattern.type = TGEnums.DATA_PATTERN_TYPE.INCREMENT_BYTE

        TGTxPort = tx_port.TGPort  # type: Portf
        TGRxPort = rx_port.TGPort

        TGTxPort.add_stream(streamName)
        TGTxPort.streams[streamName].packet.mac.sa.mode = TGEnums.MODIFIER_MAC_MODE.FIXED
        TGTxPort.streams[streamName].packet.mac.sa.value = self._testClassref.TestCaseData["ip_arp"][f"arp_mac{str(tx_port.id)}"]
        TGTxPort.streams[streamName].packet.mac.da.mode = TGEnums.MODIFIER_MAC_MODE.FIXED
        TGTxPort.streams[streamName].packet.mac.da.value = self.getPortMac(tx_port.DutDevPort.name)
        TGTxPort.streams[streamName].frame_size.value = pktSize
        TGTxPort.streams[streamName].rate.mode = TGEnums.STREAM_RATE_MODE.UTILIZATION
        TGTxPort.streams[streamName].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
        TGTxPort.streams[streamName].control.packets_per_burst = 2
        TGTxPort.streams[streamName].rate.utilization_value = 100
        TGTxPort.streams[streamName].packet.ipv4.ttl = ttl
        TGTxPort.streams[streamName].packet.l3_proto = TGEnums.L3_PROTO.IPV4
        TGTxPort.streams[streamName].packet.ipv4.destination_ip.value = self._testClassref.TestCaseData["routes"][f"dst{str(rx_port.id)}"]
        TGTxPort.streams[streamName].packet.ipv4.source_ip.value = self._testClassref.TestCaseData["ip_arp"][str(tx_port.id)]

        # apply streams
        tx_port.TGPort.apply_streams()
        tx_port.TGPort.apply_port_config()
        time.sleep(30)
        tx_port.TGPort.apply_port_config()

    def setupRouteFilter(self, tx_port, rx_port):
        funcname = GetFunctionName(self.setupRouteFilter)
        TGTxPort = tx_port.TGPort
        TGRxPort = rx_port.TGPort #type: Port

        ip_src_filter = " ".join(hex(int(i))[2:].rjust(2, "0") for i in
                                 self._testClassref.TestCaseData["ip_arp"][str(tx_port.id)].split('.'))
        termSA_ip = TGRxPort.filter_properties.create_match_term(ip_src_filter, 26)

        TGRxPort.filter_properties.filters[3].enabled = False
        myFilter = TGRxPort.filter_properties.capture_filter
        myFilter.enabled = True
        myFilter.add_condition(termSA_ip)

        TGRxPort.apply_filters()

    def changeStream(self, tx_port, stream="testStream", pktSize=64, checksum=1, ttl=64):
        funcname = GetFunctionName(self.changeStream)
        dbg = f'Changing stream {stream}'
        self.logger.debug(dbg)
        TGTxPort = tx_port.TGPort
        TGTxPort.streams[stream].frame_size.value = pktSize
        if 'checksum' in self._testClassref.testName and checksum == 1:
            TGTxPort.streams[stream].packet.ipv4.checksum_mode = TGEnums.CHECKSUM_MODE.VALID
        elif 'ttl' in self._testClassref.testName:
            TGTxPort.streams[stream].packet.ipv4.ttl = ttl
        #TGTxPort.apply_streams()
        #tx_port.TGPort.protocol_managment.apply()
        #tx_port.TGPort.protocol_managment.arp_table.transmit()
        tx_port.TGPort.apply_streams()
        tx_port.TGPort.apply_port_config()
        time.sleep(30)
        tx_port.TGPort.apply_port_config()

    def clearAllTGPortsCounters(self):
        """
        clears all TG ports counters
        :return:
        :rtype:
        """
        funcname = GetFunctionName(self.clearAllTGPortsCounters)
        dbg = funcname + "Clearing all TG ports counters"
        self.logger.debug(dbg)

        for port in list(self._testClassref.TGDutLinks.values()):
            port.TGPort.clear_all_statistics()
        sleep(2)

    def clearInterfaceRoute(self, tx_port, rx_port):
        funcname = GetFunctionName(self.clearInterfaceRoute)
        dbg = f'Clearing Ixroute interfaces'
        self.logger.debug(dbg)
        funcname = GetFunctionName(self.clearInterfaceRoute)
        TGTxPort = tx_port.TGPort  # type: Port
        TGRxPort = rx_port.TGPort
        TGTxPort.protocol_managment.protocol_interfaces.interfaces.clear()
        TGRxPort.protocol_managment.protocol_interfaces.interfaces.clear()
        #TGTxPort.apply()
        tx_port.TGPort.protocol_managment.apply()

        #TGRxPort.apply()
        rx_port.TGPort.protocol_managment.apply()



    def transmitTraffic(self, tx_port, not_continues = True):
        """
        :param tx_port:
        :param not_continues:
        :return:
        """
        funcname = GetFunctionName(self.transmitTraffic)
        dbg = funcname + "Transmitting traffic"
        self.logger.debug(dbg)
        self._testClassref.TGManager.chassis.start_traffic(tx_port.TGPort, blocking=False if not_continues else True,
                                                           wait_up=True)



    def verifyReceivedTrafficIsAsExpected(self, tx_port, rx_port, ip_fwd=1, isFrag=False, pingCount=1, checksum=1, pckt_expected=2):
        """
        verifies that the whole transmitted traffic was received and that no packet loss occurred nor errors
        :param tx_port: the transmitting port
        :param rx_port: the receiving port
        :return:
        """
        funcname = GetFunctionName(self.verifyReceivedTrafficIsAsExpected)
        dbg = funcname + "Verify received traffic on ports is as expected"
        self.logger.debug(dbg)
        status = self._verifyTrafficOnPorts(tx_port, rx_port, ip_fwd, isFrag, pingCount, checksum, pckt_expected)
        if status:
            if 'class' in self._testClassref.testName:
                dbg = funcname + "Passed! packet has been discarded"
            elif 'IPv4_mtu_oversized_counter' in self._testClassref.testName:
                dbg = funcname + "Passed! packet has been discarded due to mtu config"
            else:
                dbg = funcname + "Passed! No packet loss has occured"
            self.logger.debug(dbg)
        elif 'class_A' in self._testClassref.testName or 'class_E' in self._testClassref.testName:
            dbg = funcname + "Failed! packet haven't been discarded"
            self.FailTheTest(dbg)
        elif 'icmp_unreachable_host' in self._testClassref.testName:
            dbg = funcname + "Failed! ICMP unreachable host message have not been received!"
            self.FailTheTest(dbg)
        else:
            dbg = funcname + "Failed! a bad formatted stream might have been received or a packet loss might occured"
            self.FailTheTest(dbg)

    def _verifyTrafficOnPorts(self, tx_port, rx_port, ip_fwd, isFrag, pingCount, checksum, pckt_expected):

        tx_port.TGPort.get_stats()
        tx_port.TGPort.get_stats()
        rx_expected_counter = pckt_expected #tx_port.TGPort.statistics.frames_sent
        stats_tx = tx_port.TGPort.statistics

        rx_port.TGPort.get_stats()
        rx_port.TGPort.get_stats()
        stats_rx = rx_port.TGPort.statistics

        c_rx = Comparator(stats_rx)
        c_tx = Comparator(stats_tx)

        if 'checksum' in self._testClassref.testName and checksum == 0:
            rx_expected_counter = 0
        elif ip_fwd == 0 or 'class_A' in self._testClassref.testName or 'class_E' in self._testClassref.testName or\
                'IPv4_mtu_oversized_counter' in self._testClassref.testName:
            rx_expected_counter = 0
        elif isFrag:
            rx_expected_counter = rx_expected_counter*2 #tx_port.TGPort.statistics.frames_sent*2

        if 'icmp_unreachable' in self._testClassref.testName:
            tx_port.TGPort.get_stats()
            stats_tx = tx_port.TGPort.statistics
            c_tx.NotEqual(stats_tx.capture_filter, 0)
            c_tx.Equal(stats_tx.crc_errors, 0)
            return c_tx.Compare()
        elif 'icmp_disabled' in self._testClassref.testName:
            c_tx.Equal(stats_tx.capture_filter, 0)
            c_tx.Equal(stats_tx.crc_errors, 0)
            return c_tx.Compare()
        elif 'ping_size' in self._testClassref.testName:
            if isFrag:
                c_tx.NotEqual(stats_tx.capture_filter, pingCount)
            else:
                c_tx.Equal(stats_tx.capture_filter, pingCount)
            c_tx.Equal(stats_tx.crc_errors, 0)
            if isFrag:
                c_rx.NotEqual(stats_tx.capture_filter, pingCount)
            else:
                c_rx.Equal(stats_tx.capture_filter, pingCount)
            c_rx.Equal(stats_rx.crc_errors, 0)
            return c_tx.Compare() and c_rx.Compare()
        elif 'ping_count' in self._testClassref.testName:
            c_tx.Equal(stats_tx.capture_filter, pingCount)
            c_tx.Equal(stats_tx.crc_errors, 0)
            c_rx.Equal(stats_tx.capture_filter, pingCount)
            c_rx.Equal(stats_rx.crc_errors, 0)
            return c_tx.Compare() and c_rx.Compare()
        elif 'traceroute_static' in self._testClassref.testName:
            c_tx.Equal(stats_tx.capture_filter, 1)
            c_tx.Equal(stats_tx.crc_errors, 0)

            c_rx.Equal(stats_tx.capture_filter, 1)
            c_rx.Equal(stats_rx.crc_errors, 0)
            return c_tx.Compare() and c_rx.Compare()
        else:
            c_rx.Equal(stats_rx.capture_filter, rx_expected_counter)
            c_rx.Equal(stats_rx.crc_errors, 0)
            return c_rx.Compare()

    def pingDUT(self, tx_port, interface=0):
        funcname = GetFunctionName(self.pingDUT)
        TGTxPort = tx_port.TGPort
        p1_if_1 = list(TGTxPort.protocol_managment.protocol_interfaces.interfaces)[interface]
        TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].send_ping(self._testClassref.TestCaseData["ip"][str(tx_port.id)])
        time.sleep(1)
        TGTxPort.get_stats()
        if int(TGTxPort.statistics.rx_ping_reply) != 1:
            dbg = funcname + "Failed! No ping reply excepted"
            self.FailTheTest(dbg)

    def verifyPortStatistics(self, dev):
        funcname = GetFunctionName(self.verifyPortStatistics)
        ret = dev.getEthtoolPortStats()
        if 'IPv4_mtu_oversized_counter' in self._testClassref.testName:
            oversized = ret.split('\n')[20].lstrip()
            if int(ret.split()[41]) == 0:
                self.FailTheTest(f"{funcname} No oversized packets were dropped for {dev.switchdevInterface.name} {oversized}")

    def getPortMac(self, port):
        funcname = GetFunctionName(self.getPortMac)
        ret = IPv4Config.getPortMac(port)
        if ret is None:
            self.FailTheTest(f"{funcname} {ret} unable to get {port} mac addr")
        return ret

