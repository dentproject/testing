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
from UnifiedTG.Unified.Packet import DATA_PATTERN
from UnifiedTG.Unified.TGEnums import TGEnums
from CLI_GlobalFunctions.SwitchDev.Bridge.BridgeConfig import BridgeConfig
from CLI_GlobalFunctions.SwitchDev.Bridge.Bridge1QConfig import Bridge1QConfig
from CLI_GlobalFunctions.SwitchDev.Port.L1PortConfig import L1PortConfig
from PyInfra.BaseTest_SV import BaseTest_SV_API
from PyInfra.BaseTest_SV.SV_Enums.SwitchDevInterface import SwitchDevDutInterface
from PyInfra.BaseTest_SV.SV_Enums.SwitchDevDutPort import SwitchDevDutPort
from PyInfraCommon.GlobalFunctions.Utils.Function import GetFunctionName
from PyInfraCommon.Managers.QueryTools.Comparator import Comparator


class Bridging_api(BaseTest_SV_API):

    def __init__(self, TestClass):
        super(Bridging_api, self).__init__(TestClass)
        self._bridge = None #type: BridgeConfig
        self._bridge1 = None  # type: BridgeConfig
        self._port_list = [] #type: list[L1PortConfig]
        self._port_list_SwitchDevDutInterface = [] #type: list[SwitchDevDutInterface]


    def initBridge(self):
        """
        creates bridge entity
        :return:
        """
        funcname = GetFunctionName(self.initBridge)
        self._bridge = BridgeConfig(SwitchDevDutInterface("br0"))
        if 'route_between_vlans' in self._testClassref.testName:
            self._bridge1 = BridgeConfig(SwitchDevDutInterface("br1"))
        #init ports
        for i in range(1,len(list(self._testClassref.TGDutLinks.values()))+1):
            self._port_list.append(L1PortConfig(SwitchDevDutPort(self._testClassref.TGDutLinks[i].DutDevPort.name)))
        self._port_list_SwitchDevDutInterface.extend([x.switchdevInterface for x in self._port_list])
        ret = self._bridge.createL2Entity()
        if 'route_between_vlans' in self._testClassref.testName:
            self._bridge1 = BridgeConfig(SwitchDevDutInterface("br1"))
            ret = self._bridge1.createL2Entity()
        if ret:
            self.FailTheTest(f"{funcname} {ret} Could not initiate bridge {self._bridge.switchdevInterface.name}")
        self.Add_Cleanup_Function_To_Stack(self._bridge.deleteEntity)
        if 'route_between_vlans' in self._testClassref.testName:
            self.Add_Cleanup_Function_To_Stack(self._bridge1.deleteEntity)

    def configureEntityUp(self, dev):
        funcname = GetFunctionName(self.configureEntityUp)
        ret = dev.setState('up')
        if ret:
            self.FailTheTest(f"{funcname} {ret} Could not config entity {dev.switchdevInterface.name} up")

    def configureEntityDown(self, dev):
        funcname = GetFunctionName(self.configureEntityDown)
        ret = dev.setState('down')
        if ret:
            self.FailTheTest(f"{funcname} {ret} Could not config entity {dev.switchdevInterface.name} down")
        self.Add_Cleanup_Function_To_Stack(dev.setState, "up")

    def configurePortMTU(self, dev, mtu=1500):
        funcname = GetFunctionName(self.configurePortMTU)
        ret = dev.setMTU(mtu)
        if ret:
            self.FailTheTest(f"{funcname} {ret} Could not config port {dev.switchdevInterface.name} MTU")
        self.Add_Cleanup_Function_To_Stack(dev.setMTU, 1500)

    def configureEntitiestUp(self):
        """
        sets port up
        :return:
        """
        funcname = GetFunctionName(self.configureEntitiestUp)
        for port in self._port_list:
            ret = port.setState('up')
            if ret:
                self.FailTheTest(f"{funcname} {ret} Could not config entity up")
        self._bridge.setState('up')
        if 'route_between_vlans' in self._testClassref.testName:
            self._bridge1.setState('up')

    def configureBridgeEntityDown(self):
        funcname = GetFunctionName(self.configureBridgeEntityDown)
        ret = self._bridge.setState('down')
        if ret:
            self.FailTheTest(f"{funcname} {ret} Could not config bridge entity up {self._bridge.switchdevInterface.name}")

    def configureBridgeEntityUp(self):
        funcname = GetFunctionName(self.configureBridgeEntityDown)
        ret = self._bridge.setState('up')
        if ret:
            self.FailTheTest(f"{funcname} {ret} Could not config bridge entity up {self._bridge.switchdevInterface.name}")

    def configureAging(self,age=30000):
        """
        sets aging
        :return:
        """
        funcname = GetFunctionName(self.configureAging)
        self._bridge.aging_time = str(age)


    def configureFiltering(self,v):
        """
        sets filtering
        :return:
        """
        funcname = GetFunctionName(self.configureAging)
        self._bridge.vlan_filtering = str(v)
        if 'route_between_vlans' in self._testClassref.testName:
            self._bridge1.vlan_filtering = str(v)


    def configurePortMaster(self):
        """
        sets ports master
        :return:
        """
        funcname = GetFunctionName(self.configurePortMaster)
        ret  = self._bridge.setEnslavedInterfaces(*self._port_list_SwitchDevDutInterface)
        if ret:
            self.FailTheTest(f"{funcname} {ret} Could not configure port master")

    def configureSinglePortMaster(self, bridge, port):
        """
        sets port master
        :return:
        """
        funcname = GetFunctionName(self.configureSinglePortMaster)
        ret  = bridge.setEnslavedInterfaces(port)
        if ret:
            self.FailTheTest(f"{funcname} {ret} Could not configure port master")

    def configurePortNonMaster(self, port):
        """
        unsets port master
        :return:
        """
        funcname = GetFunctionName(self.configurePortNonMaster)
        ret  = self._bridge.setNonSlaveInterface(port)
        if ret:
            self.FailTheTest(f"{funcname} {ret} Could not remove {port.switchdevInterface.name} from master")

    def configurePortsLearningOn(self):
        """
        sets port learning on
        :return:
        """
        funcname = GetFunctionName(self.configurePortsLearningOn)
        ret = self._bridge.setLearning('on')
        if ret:
            self.FailTheTest(f"{funcname} {ret} Could not set port learning on")

    def configurePortsLearningOff(self):
        """
        sets port learning off
        :return:
        """
        funcname = GetFunctionName(self.configurePortsLearningOff)
        ret = self._bridge.setLearning('off')
        if ret:
            self.FailTheTest(f"{funcname} {ret} Could not set port learning off")

    def configurePortsFloodOn(self):
        """
        sets port flood on
        :return:
        """
        funcname = GetFunctionName(self.configurePortsFloodOn)
        ret = self._bridge.setFloodAll('on')
        if ret:
            self.FailTheTest(f"{funcname} {ret} Could not set port flood on")

    def configurePortsFloodOff(self):
        """
        sets port flood off
        :return:
        """
        funcname = GetFunctionName(self.configurePortsFloodOff)
        ret = self._bridge.setFloodAll('off')
        if ret:
            self.FailTheTest(f"{funcname} {ret} Could not set port flood off")

    def addFdbEntry(self, tx_port, vlan=1):
        """
        sets FDB entry
        :return:
        """
        funcname = GetFunctionName(self.addFdbEntry)
        self._bridge.setBridgeEntry(self._testClassref.TestCaseData["macs"][str(tx_port.id)], tx_port.DutDevPort.name, str(vlan))

    def fillFdbStaticEntries(self, tx_port, vlan=1):
        """
        fillFdbStaticEntries
        :return:
        """
        funcname = GetFunctionName(self.fillFdbStaticEntries)
        mac = '00:00:00:00'
        index = self._testClassref.TestCaseData["mac_table"]["size"]
        start_index = self._testClassref.TestCaseData["mac_table"]["start_index"]
        for number in range(start_index, start_index + index):
            hex_num = hex(number)[2:].rjust(4, '0')
            entry = "{}:{}{}:{}{}".format(mac, *hex_num)
            self._bridge.setBridgeEntry(entry, tx_port.DutDevPort.name, str(vlan))

    def fillFdbStaticEntriesFromFile(self, dev):
        """
        fillFdbStaticEntries
        :return:
        """
        funcname = GetFunctionName(self.fillFdbStaticEntriesFromFile)
        self._bridge.fillBridgeStaticEntries(board_type_index=self._testClassref.TestCaseData["mac_table"][self._testClassref.TestData.DutInfo.Board_Model]["size"]
                                             ,start_index=self._testClassref.TestCaseData["mac_table"]["start_index"], dev=dev)

    def setupStream(self, tx_port, rx_port, index=-1, vlan = 0, count=-1, pktSize = 64, isFilter=True):
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

        TGTxPort = tx_port.TGPort #type: Port
        TGRxPort = rx_port.TGPort
        TGTxPort.add_stream("testStream")
        TGTxPort.streams["testStream"].packet.mac.da.mode = TGEnums.MODIFIER_MAC_MODE.FIXED
        TGTxPort.streams["testStream"].frame_size.value = 64
        TGTxPort.streams["testStream"].rate.mode = TGEnums.STREAM_RATE_MODE.UTILIZATION
        TGTxPort.streams["testStream"].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
        TGTxPort.streams["testStream"].rate.pps_value = 10
        TGTxPort.streams["testStream"].control.packets_per_burst = 2
        TGTxPort.streams["testStream"].rate.utilization_value = 100
        TGTxPort.streams["testStream"].packet.mac.da.value = self._testClassref.TestCaseData["macs"][
            str(rx_port.id)]
        TGTxPort.streams["testStream"].packet.mac.sa.value = self._testClassref.TestCaseData["macs"][
            str(tx_port.id)]
        termDA = TGRxPort.filter_properties.create_match_term(TGTxPort.streams["testStream"].packet.mac.da.value, 0)
        termSA = TGRxPort.filter_properties.create_match_term(TGTxPort.streams["testStream"].packet.mac.sa.value, 6)

        if 'illegal' in self._testClassref.testName:
            TGTxPort.streams["testStream"].packet.mac.da.value = self._testClassref.TestCaseData["illegal_macs"]["3"]
            TGTxPort.streams["testStream"].packet.mac.sa.value = self._testClassref.TestCaseData["illegal_macs"][str(index)]
        elif 'contin' in self._testClassref.testName:
            TGTxPort.streams["testStream"].control.mode = TGEnums.STREAM_TRANSMIT_MODE.CONTINUOUS_PACKET
            TGTxPort.streams["testStream"].packet.mac.da.value = self._testClassref.TestCaseData["macs"][
                str(rx_port.id)]
            TGTxPort.streams["testStream"].packet.mac.sa.value = self._testClassref.TestCaseData["macs"][
                str(tx_port.id)]
            #TGTxPort.streams["testStream"].rate.utilization_value = 10
        elif 'mac_table_size' in self._testClassref.testName or 'IPv4_max_HOST_max_FDB' in self._testClassref.testName:
            #TGTxPort.streams["testStream"].rate.utilization_value = 10
            if 'IPv4_max_HOST_max_FDB' in self._testClassref.testName:
                TGTxPort.streams["testStream"].control.mode = TGEnums.STREAM_TRANSMIT_MODE.ADVANCE_TO_NEXT_STREAM
            TGTxPort.streams["testStream"].packet.mac.sa.mode = TGEnums.MODIFIER_MAC_MODE.INCREMENT
            TGTxPort.streams["testStream"].packet.mac.sa.value = self._testClassref.TestCaseData["mac_table"]["init_addr"]
            TGTxPort.streams["testStream"].packet.mac.sa.count = self._testClassref.TestCaseData["mac_table"][self._testClassref.TestData.DutInfo.Board_Model]["size"]
            TGTxPort.streams["testStream"].packet.mac.sa.step = 1
            TGTxPort.streams["testStream"].rate.mode = TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND
            TGTxPort.streams["testStream"].rate.pps_value = 4000
            TGTxPort.streams["testStream"].control.packets_per_burst = self._testClassref.TestCaseData["mac_table"][self._testClassref.TestData.DutInfo.Board_Model]["size"]
        elif 'full_FDB_traffic' in self._testClassref.testName:
            #TGTxPort.streams["testStream"].rate.utilization_value = 10
            if tx_port.id != 1 and tx_port.id != 3:
                TGTxPort.streams["testStream"].packet.mac.da.value = self._testClassref.TestCaseData["mac_table"][
                    "init_addr"]
                TGTxPort.streams["testStream"].packet.mac.sa.value = self._testClassref.TestCaseData["macs"][
                    str(tx_port.id)]
                termDA = TGRxPort.filter_properties.create_match_term(TGTxPort.streams["testStream"].packet.mac.da.value, 0)
                termSA = TGRxPort.filter_properties.create_match_term(TGTxPort.streams["testStream"].packet.mac.sa.value, 6)
            else:
                # TGTxPort.streams["testStream"].control.mode = TGEnums.STREAM_TRANSMIT_MODE.CONTINUOUS_PACKET
                # TGTxPort.streams["testStream"].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
                TGTxPort.streams["testStream"].packet.mac.sa.mode = TGEnums.MODIFIER_MAC_MODE.INCREMENT
                TGTxPort.streams["testStream"].packet.mac.sa.value = self._testClassref.TestCaseData["mac_table"]["init_addr"]
                TGTxPort.streams["testStream"].packet.mac.sa.count = self._testClassref.TestCaseData["mac_table"][self._testClassref.TestData.DutInfo.Board_Model]["size"]
                TGTxPort.streams["testStream"].packet.mac.sa.step = 1
                TGTxPort.streams["testStream"].rate.mode = TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND
                TGTxPort.streams["testStream"].rate.pps_value = 4000
                TGTxPort.streams["testStream"].control.packets_per_burst = self._testClassref.TestCaseData["mac_table"][self._testClassref.TestData.DutInfo.Board_Model]["size"]

        elif 'backward_forwarding' in self._testClassref.testName:
            TGTxPort.streams["testStream"].control.mode = TGEnums.STREAM_TRANSMIT_MODE.ADVANCE_TO_NEXT_STREAM
            TGTxPort.streams["testStream"].packet.mac.da.value = self._testClassref.TestCaseData["illegal_macs"]["1"]
            TGTxPort.streams["testStream"].packet.mac.sa.value = self._testClassref.TestCaseData["macs"][str(tx_port.id)] #self._testClassref.TestCaseData["macs"][str(tx_port.id)]

            TGTxPort.add_stream("forwardBackStream")
            TGTxPort.streams["forwardBackStream"].packet.mac.da.mode = TGEnums.MODIFIER_MAC_MODE.FIXED
            TGTxPort.streams["forwardBackStream"].frame_size.value = 64
            TGTxPort.streams["forwardBackStream"].rate.mode = TGEnums.STREAM_RATE_MODE.UTILIZATION
            TGTxPort.streams["forwardBackStream"].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
            TGTxPort.streams["forwardBackStream"].rate.pps_value = 10
            TGTxPort.streams["forwardBackStream"].control.packets_per_burst = 2
            TGTxPort.streams["forwardBackStream"].rate.utilization_value = 100
            TGTxPort.streams["forwardBackStream"].packet.mac.da.value = self._testClassref.TestCaseData["macs"][str(tx_port.id)]
            TGTxPort.streams["forwardBackStream"].packet.mac.sa.value = self._testClassref.TestCaseData["macs"][str(rx_port.id)]

            termDA = TGTxPort.filter_properties.create_match_term(TGTxPort.streams["forwardBackStream"].packet.mac.da.value, 0)
            termSA = TGTxPort.filter_properties.create_match_term(TGTxPort.streams["forwardBackStream"].packet.mac.sa.value, 6)
        elif 'relearning' in self._testClassref.testName:
            TGTxPort.streams["testStream"].packet.mac.da.value = self._testClassref.TestCaseData["mac_table"]["init_addr"]
            TGTxPort.streams["testStream"].packet.mac.sa.value = self._testClassref.TestCaseData["macs"][str(tx_port.id)]

            if tx_port.DutDevPort.name == self._port_list_SwitchDevDutInterface[2].name:
                TGTxPort.streams["testStream"].packet.mac.sa.value = self._testClassref.TestCaseData["macs"]["1"] #running over 1 port learning
            TGTxPort.streams["testStream"].packet.add_vlan("vlanTested")
            TGTxPort.streams["testStream"].packet.vlans["vlanTested"].vid.value = str(vlan)
            TGTxPort.streams["testStream"].control.mode = TGEnums.STREAM_TRANSMIT_MODE.ADVANCE_TO_NEXT_STREAM
        elif 'remove_restore' in self._testClassref.testName:
            TGTxPort.streams["testStream"].packet.add_vlan("vlanTested")
            TGTxPort.streams["testStream"].packet.vlans["vlanTested"].vid.value = str(index)
        #FIXME: need to be checked --> bridge still learning stp packets
        elif 'over_stp' in self._testClassref.testName:
            TGTxPort.streams["testStream"].packet.mac.da.value = '01:80:c2:00:00:00'
            TGTxPort.streams["testStream"].packet.data_pattern.type = TGEnums.DATA_PATTERN_TYPE.FIXED
            TGTxPort.streams["testStream"].packet.l2_proto = TGEnums.L2_PROTO.RAW
        elif 'undersize' in self._testClassref.testName:
            TGTxPort.streams["testStream"].frame_size.mode = TGEnums.MODIFIER_FRAME_SIZE_MODE.INCREMENT
            TGTxPort.streams["testStream"].frame_size.min = "12"
            TGTxPort.streams["testStream"].frame_size.max = "63"
        elif 'oversize' in self._testClassref.testName:
            TGTxPort.streams["testStream"].frame_size.mode = TGEnums.MODIFIER_FRAME_SIZE_MODE.INCREMENT
            TGTxPort.streams["testStream"].frame_size.min = "1523"
            TGTxPort.streams["testStream"].frame_size.max = "6000"
        # FIXME: need to be checked if supported
        elif 'mini_jumbo' in self._testClassref.testName:
            TGTxPort.streams["testStream"].frame_size.mode = TGEnums.MODIFIER_FRAME_SIZE_MODE.INCREMENT
            TGTxPort.streams["testStream"].frame_size.min = "1500"
            TGTxPort.streams["testStream"].frame_size.max = "1500"
        elif 'max_jumbo' in self._testClassref.testName or 'learning_jumbo' in self._testClassref.testName:
            TGTxPort.streams["testStream"].frame_size.value = 1500
        elif 'wrong_FCS' in self._testClassref.testName:
            TGTxPort.streams["testStream"].packet.mac.fcs = TGEnums.FCS_ERRORS_MODE.BAD_CRC
        elif 'addr_rate' in self._testClassref.testName:
            TGTxPort.streams["testStream"].rate.mode = TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND
            TGTxPort.streams["testStream"].control.packets_per_burst = 1000
            TGTxPort.streams["testStream"].rate.pps_value = 1000
            if tx_port.DutDevPort.name == self._port_list_SwitchDevDutInterface[0].name:
                TGTxPort.streams["testStream"].packet.mac.sa.mode = TGEnums.MODIFIER_MAC_MODE.INCREMENT
                TGTxPort.streams["testStream"].packet.mac.sa.step = 1
                TGTxPort.streams["testStream"].packet.mac.sa.count = 1000
                TGTxPort.streams["testStream"].packet.mac.sa.value = self._testClassref.TestCaseData["mac_table"][
                "init_addr"]
            else:
                TGTxPort.streams["testStream"].packet.mac.da.mode = TGEnums.MODIFIER_MAC_MODE.INCREMENT
                TGTxPort.streams["testStream"].packet.mac.da.step = 1
                TGTxPort.streams["testStream"].packet.mac.da.count = 1000
                TGTxPort.streams["testStream"].packet.mac.da.value = self._testClassref.TestCaseData["mac_table"][
                "init_addr"]
        elif 'robustness_macs' in self._testClassref.testName:
            TGTxPort.streams["testStream"].packet.mac.sa.value = self._testClassref.TestCaseData["mac_table"][
                "init_addr"]
            TGTxPort.streams["testStream"].packet.mac.sa.mode = TGEnums.MODIFIER_MAC_MODE.INCREMENT
            TGTxPort.streams["testStream"].packet.mac.sa.step = 1
            TGTxPort.streams["testStream"].packet.mac.sa.count = count
            TGTxPort.streams["testStream"].rate.mode = TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND
            TGTxPort.streams["testStream"].rate.pps_value = count
            TGTxPort.streams["testStream"].control.packets_per_burst = count
            #TGTxPort.streams["testStream"].rate.utilization_value = 10

        if isFilter:
            myFilter_1 = TGRxPort.filter_properties.capture_filter
            if 'backward_forwarding' in self._testClassref.testName:
                myFilter_1 = TGTxPort.filter_properties.capture_filter
            myFilter_1.enabled = True
            myFilter_1.add_condition(termDA)
            myFilter_1.add_condition(termSA)

        TGTxPort.apply_streams()
        TGRxPort.apply_filters()
        if 'backward_forwarding' in self._testClassref.testName:
            TGTxPort.apply_filters()

    def changeStream(self, tx_port, stream , dstMac=None):
        TGTxPort = tx_port.TGPort
        mac = '00:00:00:00'
        if dstMac !=None:
            hex_num = hex(dstMac)[2:].rjust(4, '0')
            TGTxPort.streams[stream].packet.mac.da.value = '{}:{}{}:{}{}'.format(mac, *hex_num)
        TGTxPort.apply_streams()

    def changeFilter(self, tx_port, stream, dstMac=None):
        TGTxPort = tx_port.TGPort
        myFilter = TGTxPort.filter_properties.capture_filter
        mac = '00:00:00:00'
        if dstMac !=None:
            hex_num = hex(dstMac)[2:].rjust(4, '0')
            myFilter.conditions[0]._match_term.current_val._pattern = TGTxPort.streams[stream].packet.mac.da.value = '{}:{}{}:{}{}'.format(mac,*hex_num)
        TGTxPort.apply_filters()

    def deleteAllStreams(self):
        """
        delete all tg streams on ports
        :return:
        """
        funcname = GetFunctionName(self.deleteAllStreams)
        dbg = funcname + "Clearing all TG ports streams"
        self.logger.debug(dbg)

        for port in list(self._testClassref.TGDutLinks.values()):
            port.TGPort.del_all_streams(True)

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



    def verifyReceivedTrafficIsAsExpected(self, tx_port, rx_port):
        """
        verifies that the whole transmitted traffic was received and that no packet loss occurred nor errors
        :param tx_port: the transmitting port
        :param rx_port: the receiving port
        :return:
        """
        funcname = GetFunctionName(self.verifyReceivedTrafficIsAsExpected)
        dbg = funcname + "Verify received traffic on ports is as expected"
        self.logger.debug(dbg)
        status = self._verifyTrafficOnPorts(tx_port, rx_port)
        if status:
            if 'backward_forwarding' in self._testClassref.testName:
                dbg = funcname + "Passed! No backward forwarding has occured"
                self.logger.debug(dbg)
            elif 'addr_rate' in self._testClassref.testName:
                dbg = funcname + "Passed! No flooding to third port has occured all addr have been learned"
                self.logger.debug(dbg)
            else:
                dbg = funcname + "Passed! No packet loss has occured"
                self.logger.debug(dbg)
        elif 'backward_forwarding' in self._testClassref.testName:
            dbg = funcname + "Failed! backward forwarding has occured"
            self.FailTheTest(dbg)
        elif 'addr_rate' in self._testClassref.testName:
            dbg = funcname + "Failed! flooding to third port has occured"
            self.FailTheTest(dbg)
        else:
            dbg = funcname + "Failed! a bad formatted stream might have been received or a packet loss might occured"
            self.FailTheTest(dbg)

    def _verifyTrafficOnPorts(self, tx_port, rx_port):

        # while tx_port.TGPort.statistics.frames_sent_rate != 0:
        #     tx_port.TGPort.get_stats()
        #
        tx_port.TGPort.get_stats()
        tx_port.TGPort.get_stats()
        rx_expected_counter = tx_port.TGPort.statistics.frames_sent
        tx_stats = tx_port.TGPort.statistics

        # while rx_port.TGPort.statistics.frames_received_rate != 0:
        #     rx_port.TGPort.get_stats()
        rx_port.TGPort.get_stats()
        rx_port.TGPort.get_stats()
        rx_stats = rx_port.TGPort.statistics

        rx_c = Comparator(rx_stats)
        tx_c = Comparator(tx_stats)

        if 'backward_forwarding' in self._testClassref.testName:
            tx_c.Equal(tx_stats.capture_filter, 0)
        elif 'traffic_from_non_slave' in self._testClassref.testName:
            rx_c.Equal(rx_stats.capture_filter, 0)
        elif 'addr_rate' in self._testClassref.testName:
            if rx_expected_counter <= rx_stats.frames_received:
                return False
            else:
                return True
        else:
            rx_c.Equal(rx_stats.capture_filter, rx_expected_counter)
        rx_c.Equal(rx_stats.crc_errors, 0)
        if 'backward_forwarding' in self._testClassref.testName:
            return tx_c.Compare()
        else:
            return rx_c.Compare()

    def checkAddrInFDB(self, tx_port, index=0, vlan=0):
        funcname = GetFunctionName(self.checkAddrInFDB)
        ret = self._bridge.getPortEntries(tx_port.DutDevPort.name)
        entry = f'{self._testClassref.TestCaseData["macs"][str(tx_port.id)]} extern_learn'
        if 'illegal' in self._testClassref.testName:
            entry = self._testClassref.TestCaseData["illegal_macs"][str(index)]
            if f'{entry} extern_learn' in ret:
                self.FailTheTest(f"{funcname} {entry} Illegal Entry was found in Mac table for port {tx_port.DutDevPort.name}!")
        elif 'relearning' in self._testClassref.testName or 'remove_restore' in self._testClassref.testName:
            if tx_port.DutDevPort.name == self._port_list_SwitchDevDutInterface[2].name:
                index = 1 #self._port_list_SwitchDevDutInterface[0].name
            entry = '{} vlan {}'.format(self._testClassref.TestCaseData["macs"][str(index)], vlan)
            if entry not in ret:
                self.FailTheTest(f"{funcname} {entry} Entry wasn't found in Mac table for port {tx_port.DutDevPort.name}")
        elif 'robustness_macs' in self._testClassref.testName:
            mac = '00:00:00:00'
            start_index = self._testClassref.TestCaseData["mac_table"]["start_index"]
            for number in range(start_index, start_index+index):
                hex_num = hex(number)[2:].rjust(4, '0')
                entry = "{}:{}{}:{}{} extern_learn".format(mac, *hex_num)
                if entry not in ret:
                    self.FailTheTest(f"{funcname} {entry} Entry wasn't found in Mac table for port {tx_port.DutDevPort.name}")
        elif entry not in ret:
            self.FailTheTest(f"{funcname} {entry} Entry wasn't found in Mac table for port {tx_port.DutDevPort.name}")

    def checkAddrNotInFDB(self, tx_port, index=0, vlan=0):
        funcname = GetFunctionName(self.checkAddrNotInFDB)
        ret = self._bridge.getPortEntries(tx_port.DutDevPort.name)
        entry = f"{self._testClassref.TestCaseData['macs'][str(tx_port.id)]} extern_learn"
        if 'relearning' in self._testClassref.testName or 'remove_restore' in self._testClassref.testName:
            entry = f"{self._testClassref.TestCaseData['macs'][str(tx_port.id)]} vlan {vlan}"
            if entry in ret:
                self.FailTheTest(f"{funcname} {entry} Entry was found in Mac table for port {tx_port.DutDevPort.name}")
        elif 'robustness_macs' in self._testClassref.testName:
            mac = '00:00:00:00'
            start_index = self._testClassref.TestCaseData["mac_table"]["start_index"]
            for number in range(start_index, start_index+index):
                hex_num = hex(number)[2:].rjust(4, '0')
                entry = "{}:{}{}:{}{}".format(mac, *hex_num)
                if entry in ret:
                    self.FailTheTest(f"{funcname} {entry} Entry was found in Mac table for port {tx_port.DutDevPort.name}")
        elif entry in ret:
            self.FailTheTest(f"{funcname} {entry} Entry was found in Mac table for port {tx_port.DutDevPort.name}")

    def countFDBentries(self):
        funcname = GetFunctionName(self.countFDBentries)
        ret = self._bridge.getBridgeNumOfEntries(self._bridge.switchdevInterface.name)
        table_size = self._testClassref.TestCaseData["mac_table"][self._testClassref.TestData.DutInfo.Board_Model]["size"]
        # decrementing 3000 due to hash colisions
        if int(ret) < table_size - 3000:
            self.FailTheTest(f"{funcname} {ret} FDB num of entries didn't match expected {table_size} entries for bridge {self._bridge.switchdevInterface.name}")

    def countFDBStaticEntries(self):
        funcname = GetFunctionName(self.countFDBStaticEntries)
        ret = int(self._bridge.getStaticBridgeNumOfEntries(self._bridge.switchdevInterface.name))
        ret //= 2
        table_size = self._testClassref.TestCaseData["mac_table"][self._testClassref.TestData.DutInfo.Board_Model]["size"]
        # decrementing 3000 due to hash colisions
        if ret < table_size - 3000:
            self.FailTheTest(f"{funcname} {ret} FDB num of static entries didn't match expected {table_size} entries for bridge {self._bridge.switchdevInterface.name}")

    def addInterfaceToVlan(self,dev,vlan=1):
        funcname = GetFunctionName(self.addInterfaceToVlan)
        ret = Bridge1QConfig.addInterfaceToVlan(dev, str(vlan))
        if ret:
            self.FailTheTest(f"{funcname} {ret} Unable to add port {dev} to vlan")

    def removeInterfaceFromVlan(self,dev,vlan):
        funcname = GetFunctionName(self.removeInterfaceFromVlan)
        ret = Bridge1QConfig.removeInterfaceFromVlan(dev, str(vlan))
        if ret:
            self.FailTheTest(f"{funcname} {ret} Could not remove port {dev} from vlan")

    def setBridgeSTP(self, mode):
        funcname = GetFunctionName(self.setBridgeSTP)
        ret = self._bridge.setBridgeSTP(self._bridge.switchdevInterface.name, mode)
        if ret:
            self.FailTheTest(f"{funcname} {ret} Unable to set Bridge STP {mode}")

    def creatreBridgeVlanDev(self, bridge, vlan):
        """
        create bridge vlan dev
        :return:
        """
        funcname = GetFunctionName(self.creatreBridgeVlanDev)
        ret = bridge.addVlanDev(bridge.switchdevInterface.name, vlan)
        if ret:
            self.FailTheTest(f"{funcname} {ret} Could not create bridge vlan device {bridge.switchdevInterface.name}.{vlan}")

    def addBridgeToVlan(self, bridge, vlan):
        """
        add bridge to vlan
        :return:
        """
        funcname = GetFunctionName(self.addBridgeToVlan)
        ret = bridge.addBridgeToVlan(bridge.switchdevInterface.name, vlan)
        if ret:
            self.FailTheTest(f"{funcname} {ret} Could not create bridge vlan device {bridge.switchdevInterface.name}.{vlan}")

    def creatingSTPMaxInstances(self):
        """
        creatingSTPMaxInstances
        :return:
        """
        funcname = GetFunctionName(self.creatingSTPMaxInstances)
        max_instances = self._testClassref.TestCaseData["STP"]["max_instances"]
        ret = BridgeConfig.setMaxSTPInstances(max_instances)
        if ret:
            self.FailTheTest(f"{funcname} {ret} Could not set STP {max_instances} max instances ")
        self.Add_Cleanup_Function_To_Stack(self.deletingSTPMaxInstances)

    def deletingSTPMaxInstances(self):
        """
        deletingSTPMaxInstances
        :return:
        """
        funcname = GetFunctionName(self.deletingSTPMaxInstances)
        max_instances = self._testClassref.TestCaseData["STP"]["max_instances"]
        ret = BridgeConfig.removeMaxSTPInstances(max_instances)
        if ret:
            self.FailTheTest(f"{funcname} {ret} Could not delete STP {max_instances} max instances ")


    def veryfingSTPMaxInstances(self):
        """
        veryfingSTPMaxInstances
        :return:
        """
        funcname = GetFunctionName(self.creatingSTPMaxInstances)
        max_instances = self._testClassref.TestCaseData["STP"]["max_instances"]
        ret = BridgeConfig.getMaxSTPInstances()
        if int(ret) < max_instances:
            self.FailTheTest(f"{funcname} {ret} STP max instances didn't match expected {max_instances}")

    def addingMaxVlans(self):
        """
        addingMaxVlans
        :return:
        """
        funcname = GetFunctionName(self.addingMaxVlans)
        max_vlans1 = self._testClassref.TestCaseData["vlans_sizes"][self._testClassref.TestData.DutInfo.Board_Model]["index1"]
        max_vlans2 = self._testClassref.TestCaseData["vlans_sizes"][self._testClassref.TestData.DutInfo.Board_Model][
            "index2"]
        dev1 = self._testClassref.TGDutLinks[1].DutDevPort.name
        dev2 = self._testClassref.TGDutLinks[2].DutDevPort.name
        ret = self._bridge.maxVLANSFromFile(index1=max_vlans1, index2=max_vlans2, dev1=dev1, dev2=dev2)
        if ret:
            self.FailTheTest(f"{funcname} {ret} Could not set vlans {max_vlans1+max_vlans2} on {dev1} {dev2}")

    def verifyingMaxVlans(self):
        funcname = GetFunctionName(self.verifyingMaxVlans)
        max_vlans1 = self._testClassref.TestCaseData["vlans_sizes"][self._testClassref.TestData.DutInfo.Board_Model]["index1"]
        max_vlans2 = self._testClassref.TestCaseData["vlans_sizes"][self._testClassref.TestData.DutInfo.Board_Model][
            "index2"]
        total = max_vlans1 + max_vlans2
        max_instances = self._testClassref.TestCaseData["STP"]["max_instances"]
        ret = len(Bridge1QConfig.getVIDs(self._testClassref.TGDutLinks[1].DutDevPort)) + len(Bridge1QConfig.getVIDs(self._testClassref.TGDutLinks[2].DutDevPort))
        if ret < total:
            self.FailTheTest(f"{funcname} {ret} max vlans didn't match expected {total} amount")