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
import re
from UnifiedTG.Unified.Packet import DATA_PATTERN
from UnifiedTG.Unified.TGEnums import TGEnums
from CLI_GlobalFunctions.SwitchDev.IPv4.IPv4Config import IPv4Config
from CLI_GlobalFunctions.SwitchDev.ECMP.ecmp_config import ECMP_config
from PyInfra.BaseTest_SV import BaseTest_SV_API
from PyInfra.BaseTest_SV.SV_Enums.SwitchDevInterface import SwitchDevDutInterface
from PyInfra.BaseTest_SV.SV_Enums.SwitchDevDutPort import SwitchDevDutPort
from PyInfraCommon.GlobalFunctions.Utils.Function import GetFunctionName
from PyInfraCommon.Managers.QueryTools.Comparator import Comparator



class ECMP_api(BaseTest_SV_API):

    def __init__(self, TestClass):
        super(ECMP_api, self).__init__(TestClass)
        self._port_list = [] #type: list[ECMP_config]
        self._port_list_SwitchDevDutInterface = [] #type: list[SwitchDevDutInterface]


    def initInterfaces(self):
        funcname = GetFunctionName(self.initInterfaces)
        #init ports
        for i in range(1,len(list(self._testClassref.TGDutLinks.values()))+1):
            self._port_list.append(ECMP_config(SwitchDevDutPort(self._testClassref.TGDutLinks[i].DutDevPort.name)))
        self._port_list_SwitchDevDutInterface.extend([x.switchdevInterface for x in self._port_list])

    def configureIPv4IgnoreLinkDown(self,v):
        """
        sets Ignore link down
        :return:
        """
        funcname = GetFunctionName(self.configureIPv4IgnoreLinkDown)
        ECMP_config.setIgnoreRoutesWithLinkdown(str(v))
        self.Add_Cleanup_Function_To_Stack(ECMP_config.setIgnoreRoutesWithLinkdown, '0')

    def configureHashPolicy(self,v):
        """
        sets Ignore link down
        :return:
        """
        funcname = GetFunctionName(self.configureIPv4IgnoreLinkDown)
        ECMP_config.setFibMultipathHashPolicy(str(v))
        self.Add_Cleanup_Function_To_Stack(ECMP_config.setFibMultipathHashPolicy, '0')

    def configureNextHops(self):
        funcname = GetFunctionName(self.configureNextHops)
        self.logger.debug(funcname + f"Adding ECMP route")
        dest_ip = self._testClassref.TestCaseData["ip_dst"]["network"]
        dest_mask = self._testClassref.TestCaseData["ip_dst"]["mask"]
        dest_net = f"{dest_ip}/{dest_mask}"
        next_hop2 = self._testClassref.TestCaseData["ip_arp"]["2"]
        next_hop3 = self._testClassref.TestCaseData["ip_arp"]["3"]
        next_hop4 = self._testClassref.TestCaseData["ip_arp"]["4"]
        ret = ECMP_config.setECMPRoute(dest_net, next_hop2, next_hop3, next_hop4)
        if ret:
            self.FailTheTest(
                f"{funcname} {ret} unable to config route for {dest_net}")

    def setupDynamicArpEntry(self, tx_port):
        funcname = GetFunctionName(self.setupDynamicArpEntry)
        self.logger.debug(funcname + f"Adding dynamic arp entry for {tx_port.DutDevPort.name}")
        TGTxPort = tx_port.TGPort

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
        TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].description = f'P{tx_port.id}'
        TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].mac_addr = self._testClassref.TestCaseData["ip_arp"][f"arp_mac{tx_port.id}"]
        TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.address = self._testClassref.TestCaseData["ip_arp"][str(tx_port.id)]
        TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.gateway = self._testClassref.TestCaseData["ip"][str(tx_port.id)]
        TGTxPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.mask = self._testClassref.TestCaseData["ip"][f"mask{tx_port.id}"]

        # apply tx_port Ixroute config
        tx_port.TGPort.protocol_managment.apply()
        tx_port.TGPort.protocol_managment.arp_table.transmit()

    def setupStreams(self, tx_port):
        funcname = GetFunctionName(self.setupStreams)
        self.logger.debug(funcname + "Setup streams")
        TGTxPort = tx_port.TGPort  # type: Port
        TGTxPort.add_stream("testStream1")
        TGTxPort.streams["testStream1"].control.packets_per_burst = 2
        TGTxPort.streams["testStream1"].rate.utilization_value = 20
        TGTxPort.streams["testStream1"].packet.l3_proto = TGEnums.L3_PROTO.IPV4
        TGTxPort.streams["testStream1"].source_interface.enabled = True
        TGTxPort.streams["testStream1"].packet.data_pattern.type = TGEnums.DATA_PATTERN_TYPE.FIXED
        TGTxPort.streams["testStream1"].packet.l2_proto = TGEnums.L2_PROTO.NONE
        TGTxPort.streams["testStream1"].rate.mode = TGEnums.STREAM_RATE_MODE.UTILIZATION
        TGTxPort.streams["testStream1"].control.mode = TGEnums.STREAM_TRANSMIT_MODE.ADVANCE_TO_NEXT_STREAM
        p1_if_1 = list(TGTxPort.protocol_managment.protocol_interfaces.interfaces.items())[0][0]
        TGTxPort.streams["testStream1"].source_interface.description_key = p1_if_1
        TGTxPort.streams["testStream1"].packet.ipv4.destination_ip.value = self._testClassref.TestCaseData["ip_dst"]["2"]
        if self._testClassref.TestData.DutInfo.Board_Model == "TN4810M":
            TGTxPort.streams["testStream1"].packet.ipv4.destination_ip.value = \
            self._testClassref.TestCaseData["ip_dst"]["TN4810M"]["2"]
        if 'ECMP_multipath_hash_policy' in self._testClassref.testName:
            TGTxPort.streams["testStream1"].packet.l4_proto = TGEnums.L4_PROTO.TCP
            TGTxPort.streams["testStream1"].packet.tcp.source_port.value = self._testClassref.TestCaseData["ports"]["src2"]
            TGTxPort.streams["testStream1"].packet.tcp.destination_port.value = self._testClassref.TestCaseData["ports"]["dst2"]
            if self._testClassref.TestData.DutInfo.Board_Model == "TN4810M":
                TGTxPort.streams["testStream1"].packet.tcp.source_port.value = self._testClassref.TestCaseData["ports"]["TN4810M"][
                    "src2"]
                TGTxPort.streams["testStream1"].packet.tcp.destination_port.value = \
                self._testClassref.TestCaseData["ports"]["TN4810M"]["dst2"]

        TGTxPort.add_stream("testStream2")
        TGTxPort.streams["testStream2"].control.packets_per_burst = 2
        TGTxPort.streams["testStream2"].rate.utilization_value = 30
        TGTxPort.streams["testStream2"].packet.l3_proto = TGEnums.L3_PROTO.IPV4
        TGTxPort.streams["testStream2"].source_interface.enabled = True
        TGTxPort.streams["testStream2"].packet.data_pattern.type = TGEnums.DATA_PATTERN_TYPE.FIXED
        TGTxPort.streams["testStream2"].packet.l2_proto = TGEnums.L2_PROTO.NONE
        TGTxPort.streams["testStream2"].rate.mode = TGEnums.STREAM_RATE_MODE.UTILIZATION
        TGTxPort.streams["testStream2"].control.mode = TGEnums.STREAM_TRANSMIT_MODE.ADVANCE_TO_NEXT_STREAM
        TGTxPort.streams["testStream2"].source_interface.description_key = p1_if_1
        TGTxPort.streams["testStream2"].packet.ipv4.destination_ip.value = self._testClassref.TestCaseData["ip_dst"]["3"]
        if self._testClassref.TestData.DutInfo.Board_Model == "TN4810M":
            TGTxPort.streams["testStream2"].packet.ipv4.destination_ip.value = \
            self._testClassref.TestCaseData["ip_dst"]["TN4810M"]["3"]
        if 'ECMP_multipath_hash_policy' in self._testClassref.testName:
            TGTxPort.streams["testStream2"].packet.ipv4.destination_ip.value = self._testClassref.TestCaseData["ip_dst"]["2"]
            TGTxPort.streams["testStream2"].packet.l4_proto = TGEnums.L4_PROTO.TCP
            TGTxPort.streams["testStream2"].packet.tcp.source_port.value = self._testClassref.TestCaseData["ports"]["src3"]
            TGTxPort.streams["testStream2"].packet.tcp.destination_port.value = self._testClassref.TestCaseData["ports"]["dst3"]
            if self._testClassref.TestData.DutInfo.Board_Model == "TN4810M":
                TGTxPort.streams["testStream2"].packet.tcp.source_port.value = self._testClassref.TestCaseData["ports"]["TN4810M"][
                    "src3"]
                TGTxPort.streams["testStream2"].packet.tcp.destination_port.value = \
                self._testClassref.TestCaseData["ports"]["TN4810M"]["dst3"]

        TGTxPort.add_stream("testStream3")
        TGTxPort.streams["testStream3"].control.packets_per_burst = 2
        TGTxPort.streams["testStream3"].rate.utilization_value = 49
        TGTxPort.streams["testStream3"].packet.l3_proto = TGEnums.L3_PROTO.IPV4
        TGTxPort.streams["testStream3"].source_interface.enabled = True
        TGTxPort.streams["testStream3"].packet.data_pattern.type = TGEnums.DATA_PATTERN_TYPE.FIXED
        TGTxPort.streams["testStream3"].packet.l2_proto = TGEnums.L2_PROTO.NONE
        TGTxPort.streams["testStream3"].rate.mode = TGEnums.STREAM_RATE_MODE.UTILIZATION
        TGTxPort.streams["testStream3"].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
        TGTxPort.streams["testStream3"].source_interface.description_key = p1_if_1
        TGTxPort.streams["testStream3"].packet.ipv4.destination_ip.value = self._testClassref.TestCaseData["ip_dst"]["4"]
        if self._testClassref.TestData.DutInfo.Board_Model == "TN4810M":
            TGTxPort.streams["testStream3"].packet.ipv4.destination_ip.value = \
            self._testClassref.TestCaseData["ip_dst"]["TN4810M"]["4"]
        if 'ECMP_multipath_hash_policy' in self._testClassref.testName:
            TGTxPort.streams["testStream3"].packet.ipv4.destination_ip.value = self._testClassref.TestCaseData["ip_dst"]["2"]
            TGTxPort.streams["testStream3"].packet.l4_proto = TGEnums.L4_PROTO.TCP
            TGTxPort.streams["testStream3"].packet.tcp.source_port.value = self._testClassref.TestCaseData["ports"]["src4"]
            TGTxPort.streams["testStream3"].packet.tcp.destination_port.value = self._testClassref.TestCaseData["ports"]["dst4"]
            if self._testClassref.TestData.DutInfo.Board_Model == "TN4810M":
                TGTxPort.streams["testStream3"].packet.tcp.source_port.value = self._testClassref.TestCaseData["ports"]["TN4810M"][
                    "src4"]
                TGTxPort.streams["testStream3"].packet.tcp.destination_port.value = \
                self._testClassref.TestCaseData["ports"]["TN4810M"]["dst4"]

        # apply streams
        tx_port.TGPort.apply_streams()
        tx_port.TGPort.apply_port_config()
        sleep(30)
        tx_port.TGPort.apply_port_config()

    def setupFilter(self, rx_port):
        funcname = GetFunctionName(self.setupFilter)
        TGRxPort = rx_port.TGPort #type: Port

        ip_src_filter = " ".join(hex(int(i))[2:].rjust(2, "0") for i in
                                 self._testClassref.TestCaseData["ip_arp"]["1"].split('.'))
        #ip_dst_filter = " ".join(hex(int(i))[2:].rjust(2, "0") for i in
                                 #self._testClassref.TestCaseData["ip_dst"][str(rx_port.id)].split('.'))
        #termDA_ip = TGRxPort.filter_properties.create_match_term(ip_dst_filter, 30)
        termSA_ip = TGRxPort.filter_properties.create_match_term(ip_src_filter, 26)

        TGRxPort.filter_properties.filters[3].enabled = False
        myFilter = TGRxPort.filter_properties.capture_filter
        myFilter.enabled = True
        #myFilter.add_condition(termDA_ip)
        myFilter.add_condition(termSA_ip)

        TGRxPort.apply_filters()


    def transmitTraffic(self, tx_port, not_continues = True, wait_up=True):
        """
        :param tx_port:
        :param not_continues:
        :return:
        """
        funcname = GetFunctionName(self.transmitTraffic)
        dbg = funcname + "Transmitting traffic"
        self.logger.debug(dbg)
        self._testClassref.TGManager.chassis.start_traffic(tx_port.TGPort, blocking=False if not_continues else True,
                                                           wait_up=wait_up)

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


    def verifyReceivedTrafficIsAsExpected(self, tx_port, rx_port):
        """
        verifies that the whole transmitted traffic was received and that no packet loss occurred nor errors
        :param tx_port: the transmitting port
        :param rx_port: the receiving port
        :return:
        """
        funcname = GetFunctionName(self.verifyReceivedTrafficIsAsExpected)
        dbg = funcname + "Verify received traffic on port is as expected"
        self.logger.debug(dbg)
        status = self._verifyTrafficOnPort(tx_port, rx_port)
        if status:
            if 'ECMP_unicast_traffic_distribution_remaining_paths' in self._testClassref.testName:
                if rx_port.id == 2:
                    dbg = funcname + f"Passed! packet not went through Ecmp nexthop {rx_port.DutDevPort.name}"
                    self.logger.debug(dbg)
                else:
                    dbg = funcname + f"Passed! packet been received for Ecmp nexthop {rx_port.DutDevPort.name}"
                    self.logger.debug(dbg)
            elif 'ECMP_link_down_nexthops' in self._testClassref.testName:
                dbg = funcname + f"Passed! packet not went through Ecmp nexthop {rx_port.DutDevPort.name}"
                self.logger.debug(dbg)
            else:
                dbg = funcname + f"Passed! packet been received for Ecmp nexthop {rx_port.DutDevPort.name}"
                self.logger.debug(dbg)
        else:
                dbg = funcname + f"Failed! Ecmp nexthop {rx_port.DutDevPort.name} didn't receive any packets"
                self.FailTheTest(dbg)


    def _verifyTrafficOnPort(self, tx_port, rx_port):
        tx_port.TGPort.get_stats()
        tx_port.TGPort.get_stats()
        rx_expected_counter = tx_port.TGPort.statistics.frames_sent//3

        rx_port.TGPort.get_stats()
        rx_port.TGPort.get_stats()
        rx_stats = rx_port.TGPort.statistics

        rx_c = Comparator(rx_stats)
        if 'ECMP_unicast_traffic_distribution_remaining_paths' in self._testClassref.testName \
                or 'ECMP_ignore_link_down_nexthops' in self._testClassref.testName:
            if rx_port.id == 2:
                rx_expected_counter = 0
            else:
                rx_expected_counter = 2
                rx_c.GreaterOrEqual(rx_stats.capture_filter, rx_expected_counter)
                return rx_c.Compare()
        elif 'ECMP_link_down_nexthops' in self._testClassref.testName:
            rx_expected_counter = 0
        rx_c.Equal(rx_stats.capture_filter, rx_expected_counter)
        return rx_c.Compare()

    def verifyReceivedTrafficIsAsExpectedOnAllPorts(self):
        funcname = GetFunctionName(self.verifyReceivedTrafficIsAsExpectedOnAllPorts)
        dbg = funcname + "Verify received traffic on all ports together is as expected"
        self.logger.debug(dbg)
        counter = 0
        rx_expected_counter = 6
        for rx_port in list(self._testClassref.TGDutLinks)[1:]:
            self._testClassref.TGDutLinks[rx_port].TGPort.get_stats()
            self._testClassref.TGDutLinks[rx_port].TGPort.get_stats()
            rx_stats = self._testClassref.TGDutLinks[rx_port].TGPort.statistics
            counter += rx_stats.capture_filter

        if counter == rx_expected_counter:
            dbg = funcname + f"Passed! Total traffic amount recieved"
            self.logger.debug(dbg)
        else:
            dbg = funcname + f"Failed! Not all traffic has been recieved expected {rx_expected_counter} recieved {counter}"
            self.FailTheTest(dbg)

