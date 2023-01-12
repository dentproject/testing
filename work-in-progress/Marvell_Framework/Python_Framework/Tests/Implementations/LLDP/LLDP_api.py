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
from CLI_GlobalFunctions.SwitchDev.Bridge.BridgeConfig import BridgeConfig
from CLI_GlobalFunctions.SwitchDev.IPv4.IPv4Config import IPv4Config
from CLI_GlobalFunctions.SwitchDev.LLDP.lldp_config import LLDP_config
from PyInfra.BaseTest_SV import BaseTest_SV_API
from PyInfra.BaseTest_SV.SV_Enums.SwitchDevInterface import SwitchDevDutInterface
from PyInfra.BaseTest_SV.SV_Enums.SwitchDevDutPort import SwitchDevDutPort
from PyInfraCommon.GlobalFunctions.Utils.Function import GetFunctionName
from PyInfraCommon.Managers.QueryTools.Comparator import Comparator



class LLDP_api(BaseTest_SV_API):

    def __init__(self, TestClass):
        super(LLDP_api, self).__init__(TestClass)
        self._port_list = [] #type: list[LLDP_config]
        self._port_list_SwitchDevDutInterface = [] #type: list[SwitchDevDutInterface]


    def initInterfaces(self):
        funcname = GetFunctionName(self.initInterfaces)
        #init ports
        for i in range(1,len(list(self._testClassref.TGDutLinks.values()))+1):
            self._port_list.append(LLDP_config(SwitchDevDutPort(self._testClassref.TGDutLinks[i].DutDevPort.name)))
        self._port_list_SwitchDevDutInterface.extend([x.switchdevInterface for x in self._port_list])


    def LLDPServiceStart(self):
        """
        set lldp service mode
        :param mode:
        :return:
        """
        funcname = GetFunctionName(self.LLDPServiceStart)
        ret = LLDP_config.LLDPserviceStart()
        if ret:
            self.FailTheTest(f"{funcname} {ret} unable to set start lldpd")
        self.Add_Cleanup_Function_To_Stack(LLDP_config.LLDPServiceKill)

    def LLDPServiceKill(self):
        """
        set lldp service mode
        :param mode:
        :return:
        """
        funcname = GetFunctionName(self.LLDPServiceKill)
        ret = LLDP_config.LLDPServiceKill()
        if ret:
            self.FailTheTest(f"{funcname} {ret} unable to kill lldpd service")

    def getPortMac(self, port):
        funcname = GetFunctionName(self.getPortMac)
        ret = LLDP_config.getPortMac(port)
        if ret is None:
            self.FailTheTest(f"{funcname} {ret} unable to get {port} mac addr")
        return ret


    def configurePortUp(self, port):
        funcname = GetFunctionName(self.configurePortUp)
        ret = LLDP_config.setPortlink(port, 'up')
        if ret:
            self.FailTheTest(f"{funcname} {ret} unable to set {port.switchdevInterface.name} up")

    def configurePortDown(self, port):
        funcname = GetFunctionName(self.configurePortDown)
        ret = LLDP_config.setPortlink(port, 'down')
        if ret:
            self.FailTheTest(f"{funcname} {ret} unable to set {port.switchdevInterface.name} down")
        self.Add_Cleanup_Function_To_Stack(LLDP_config.setPortlink, port, 'up')

    def configureLLDPInterval(self, interval):
        funcname = GetFunctionName(self.configureLLDPInterval)
        ret = LLDP_config.setLLDPTxInterval(interval)
        if ret:
            self.FailTheTest(f"{funcname} {ret} unable to set tx-interval {interval}")
        self.Add_Cleanup_Function_To_Stack(LLDP_config.setLLDPTxInterval, 30)

    def configureLLDPHold(self, hold):
        funcname = GetFunctionName(self.configureLLDPHold)
        ret = LLDP_config.setLLDPTxHold(hold)
        if ret:
            self.FailTheTest(f"{funcname} {ret} unable to set tx-hold {hold}")
        self.Add_Cleanup_Function_To_Stack(LLDP_config.setLLDPTxHold, 4)


    def configureInterfaceStat(self, port, status='rx-and-tx'):
        funcname = GetFunctionName(self.configureInterfaceStat)
        ret = LLDP_config.setInterfaceStat(port, status)
        if ret:
            self.FailTheTest(f"{funcname} {ret} unable to set status {status} for port {port.switchdevInterface.name}")
        sleep(3)

    def getLLDPPortStats(self, port, isPortDown=False):
        funcname = GetFunctionName(self.getLLDPPortStats)
        sleep(30)
        ret = LLDP_config.getPortStats(port)
        total_tx_trasmitted = ret.split('\n')[4]
        lldp_tx_pckts = re.sub('\D', '', total_tx_trasmitted)
        if 'LLDP_tx_disabled' in self._testClassref.testName:
            if int(lldp_tx_pckts) > 1:
                self.FailTheTest(f"{funcname} {total_tx_trasmitted} port {port.switchdevInterface.name} trasmitting lldp packets but tx disabled!")
        elif 'LLDP_tx_port_down_up' in self._testClassref.testName:
            if not isPortDown and int(lldp_tx_pckts) <= 1 :
                    self.FailTheTest(
                        f"{funcname} {total_tx_trasmitted} port {port.switchdevInterface.name}  not trasmitting lldp packets but port is up!")
            elif isPortDown and int(lldp_tx_pckts) > 1:
                    self.FailTheTest(
                        f"{funcname} {total_tx_trasmitted} port {port.switchdevInterface.name} trasmitting lldp packets but port is down!")
        elif 'LLDP_tx_interval' in self._testClassref.testName:
            sleep(30)
            ret = LLDP_config.getPortStats(port)
            total_tx_trasmitted = ret.split('\n')[4]
            lldp_tx_pckts = re.sub('\D', '', total_tx_trasmitted)
            if int(lldp_tx_pckts) <= 10:
                self.FailTheTest(
                    f"{funcname} {total_tx_trasmitted} port {port.switchdevInterface.name} trasmitting lldp packets not accordint to tx-interval!")


    def getTransmittedTLV(self, port):
        funcname = GetFunctionName(self.getTransmittedTLV)
        ret = LLDP_config.getTrasmittedTLV(port.switchdevInterface.name)
        if 'End of LLDPDU TLV' not in ret:
            self.FailTheTest(f"{funcname} {ret} unable to get port {port.switchdevInterface.name} trasmitted system description TLV ")
        return ret

    def configureBondSlaveSrcMac(self, value=''):
        funcname = GetFunctionName(self.configureBondSlaveSrcMac)
        ret = LLDP_config.setBondSlaveVal(value)
        if ret:
            self.FailTheTest(f"{funcname} {ret} Failed to config Bond slave value {value}")

    def getTLVNeighborInfo(self, port, isPortDown=False, sleepTime=0, stressMode=False):
        funcname = GetFunctionName(self.getTLVNeighborInfo)
        sleep(sleepTime)
        ret = LLDP_config.getTLVNeighborInfo(port)
        chasis_id = self._testClassref.TestCaseData["LLDP_packets"]["LLDP_pckt_chasis_id"]
        system_name = self._testClassref.TestCaseData["LLDP_packets"]["LLDP_pckt_system_name"]
        if 'LLDP_received' in self._testClassref.testName:
            if 'LLDP_received_mandatory_tlvs' in self._testClassref.testName:
                port_id = self._testClassref.TestCaseData["LLDP_packets"]["LLDP_pckt_Port_id"]
                port_des = self._testClassref.TestCaseData["LLDP_packets"]["LLDP_pckt_port_des"]
                system_desc = self._testClassref.TestCaseData["LLDP_packets"]["LLDP_pckt_system_des"]
                ttl = self._testClassref.TestCaseData["LLDP_packets"]["LLDP_pckt_ttl"]
                if chasis_id not in ret and system_name not in ret and system_desc not in ret\
                        and port_id not in ret and port_des not in ret and ttl not in ret:
                    self.FailTheTest(f"{funcname} {ret} unable to get port {port.switchdevInterface.name} neighbor correct tlvs info")
            elif 'LLDP_received_optional_tlvs' in self._testClassref.testName:
                port_des = self._testClassref.TestCaseData["LLDP_packets"]["LLDP_pckt_all_opt_port_des"]
                system_name = self._testClassref.TestCaseData["LLDP_packets"]["LLDP_pckt_all_opt_system_name"]
                system_desc = self._testClassref.TestCaseData["LLDP_packets"]["LLDP_pckt_all_opt_system_desc"]
                system_cap = self._testClassref.TestCaseData["LLDP_packets"]["LLDP_pckt_all_opt_system_cap"]
                mng_addr = self._testClassref.TestCaseData["LLDP_packets"]["LLDP_pckt_all_opt_mng_addr"]
                if port_des not in ret and system_name not in ret and system_desc not in ret\
                        and system_cap not in ret and port_des not in ret and mng_addr not in ret:
                    self.FailTheTest(f"{funcname} {ret} unable to get port {port.switchdevInterface.name} neighbor correct tlvs info")

            elif chasis_id not in ret and system_name not in ret:
                self.FailTheTest(f"{funcname} {ret} unable to get port {port.switchdevInterface.name} neighbor info")
        elif 'LLDP_rx_port_down_up' in self._testClassref.testName:
            if isPortDown and chasis_id in ret and system_name in ret:
                self.FailTheTest(f"{funcname} {ret} getting port {port.switchdevInterface.name} neighbor info but port is down")
            elif not isPortDown and chasis_id not in ret and system_name not in ret:
                self.FailTheTest(f"{funcname} {ret} unable to get port {port.switchdevInterface.name} neighbor info")
        elif 'LLDP_rx_disabled' in self._testClassref.testName:
            if chasis_id in ret and system_name in ret:
                self.FailTheTest(f"{funcname} {ret} getting port {port.switchdevInterface.name} neighbor info but rx disabled!")
        elif 'LLDP_max_frame_size' in self._testClassref.testName:
            chasis_id = self._testClassref.TestCaseData["LLDP_packets"]["LLDP_Max_frame_size_all_options_chasis_id"]
            mng_ip = self._testClassref.TestCaseData["LLDP_packets"]["LLDP_Max_frame_size_all_options_MgmtIP"]
            if chasis_id not in ret and mng_ip not in ret:
                self.FailTheTest( f"{funcname} {ret} failed to get Max frame size on {port.switchdevInterface.name}")
        elif 'LLDP_max_end_points' in self._testClassref.testName:
            max_end_points = len(self._testClassref.TestCaseData["LLDP_packets"]["LLDP_Max_END_POINTS"])
            if ret.count("RID") != max_end_points:
                self.FailTheTest(f"{funcname} {ret} failed Max end points aren't matching {max_end_points}")
        elif 'LLDP_ttl' in self._testClassref.testName:
            ttl = self._testClassref.TestCaseData["LLDP_packets"]["LLDP_ttl_pckt_ttl"]
            sleep(int(ttl))
            ret = LLDP_config.getTLVNeighborInfo(port)
            if ttl in ret:
                self.FailTheTest(f"{funcname} {ret} neighbor info still present after {ttl} ttl time")
        elif 'LLDP_cdp_negative' in self._testClassref.testName:
            if ret.count("RID") != 0:
                self.FailTheTest(f"{funcname} {ret} CDP neighbor info exist")
        elif 'LLDP_en_dis_diff_ports' in self._testClassref.testName or 'LLDP_stress' in self._testClassref.testName:
            if not stressMode:
                if self._port_list.index(port) % 2 == 0:
                    if ret.count("RID") != 0:
                        self.FailTheTest(f"{funcname} {ret} LLDP neighbor info exist and lldp is disabled on port {port}")
                elif ret.count("RID") == 0:
                    self.FailTheTest(f"{funcname} {ret} LLDP neighbor info not exist and lldp is enabled on port {port}")
            else:
                if self._port_list.index(port) % 2 == 1:
                    if ret.count("RID") != 0:
                        self.FailTheTest(f"{funcname} {ret} LLDP neighbor info exist and lldp is disabled on port {port}")
                elif ret.count("RID") == 0:
                    self.FailTheTest(f"{funcname} {ret} LLDP neighbor info not exist and lldp is enabled on port {port}")


    def configurePortTlvs(self, tlv_type = "IEEE 802.1"):
        funcname = GetFunctionName(self.setupFilter)
        if tlv_type == "IEEE 802.1":
            oui = self._testClassref.TestCaseData["LLDP_port_trasmitted_tlvs"]["IEEE802.1"]["oui"]
            subtype = self._testClassref.TestCaseData["LLDP_port_trasmitted_tlvs"]["IEEE802.1"]["subtype"]
            ouiinfo = self._testClassref.TestCaseData["LLDP_port_trasmitted_tlvs"]["IEEE802.1"]["oui-info"]
        else:
            oui = self._testClassref.TestCaseData["LLDP_port_trasmitted_tlvs"]["IEEE802.3"]["oui"]
            subtype = self._testClassref.TestCaseData["LLDP_port_trasmitted_tlvs"]["IEEE802.3"]["subtype"]
            ouiinfo = self._testClassref.TestCaseData["LLDP_port_trasmitted_tlvs"]["IEEE802.3"]["oui-info"]
        ret = LLDP_config.setTlvFields(oui, subtype, ouiinfo)
        if ret:
            self.FailTheTest(f"{funcname} {ret} unable to configure tlvs fields")


    def setupFilter(self, tx_port, ttl=120, tlv_type="IEEE 802.1"):
        funcname = GetFunctionName(self.setupFilter)
        TGTxPort = tx_port.TGPort #type: Port
        mac_src_addr = self.getPortMac(tx_port.DutDevPort.name)#self._testClassref.TestCaseData["LLDP_port_tlvs"]["enp3s4"]["mac"]
        termDA = TGTxPort.filter_properties.create_match_term(self._testClassref.TestCaseData["macs"]["multicast_lldp"], 0)
        termSA = TGTxPort.filter_properties.create_match_term(mac_src_addr, 6)
        ttl_to_hex = hex(ttl)[2:].rjust(4, "0")
        ttl_to_hex = f'{ttl_to_hex[:2]} {ttl_to_hex[2:]}'
        TTL_term = TGTxPort.filter_properties.create_match_term(ttl_to_hex, 34)
        if 'LLDP_transmitted_mandatory_tlvs' in self._testClassref.testName:
            if tlv_type == "IEEE 802.1":
                oui = "00 80 C2"
            else:
                oui = "00 12 0F"
            OUI_term = TGTxPort.filter_properties.create_match_term(oui, 211)
        TGTxPort.filter_properties.filters[3].enabled = False
        myFilter = TGTxPort.filter_properties.capture_filter
        myFilter.enabled = True
        myFilter.add_condition(termDA)
        myFilter.add_condition(termSA)
        myFilter.add_condition(TTL_term)
        if 'LLDP_transmitted_mandatory_tlvs' in self._testClassref.testName:
            myFilter.add_condition(OUI_term)
        TGTxPort.apply_filters()

    def setupStream(self, tx_port):
        TGTxPort = tx_port.TGPort #type: Port
        if 'LLDP_max_end_points' in self._testClassref.testName:
            for i in range(len(self._testClassref.TestCaseData["LLDP_packets"]["LLDP_Max_END_POINTS"])):
                TGTxPort.add_stream(f"endpoint{i}")
                TGTxPort.streams[f"endpoint{i}"].packet.mac.da.mode = TGEnums.MODIFIER_MAC_MODE.FIXED
                TGTxPort.streams[f"endpoint{i}"].packet.mac.da.value = self._testClassref.TestCaseData["macs"][
                    "multicast_lldp"]
                TGTxPort.streams[f"endpoint{i}"].packet.mac.sa.mode = TGEnums.MODIFIER_MAC_MODE.FIXED
                TGTxPort.streams[f"endpoint{i}"].packet.mac.sa.value = self._testClassref.TestCaseData["macs"][
                    str(tx_port.id)]
                TGTxPort.streams[f"endpoint{i}"].frame_size.value = 100
                TGTxPort.streams[f"endpoint{i}"].packet.data_pattern.value = self._testClassref.TestCaseData["LLDP_packets"]["LLDP_Max_END_POINTS"][f"{i}"]
                TGTxPort.streams[f"endpoint{i}"].packet.data_pattern.type = TGEnums.DATA_PATTERN_TYPE.FIXED
                TGTxPort.streams[f"endpoint{i}"].packet.l2_proto = TGEnums.L2_PROTO.NONE
                TGTxPort.streams[f"endpoint{i}"].rate.mode = TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND
                TGTxPort.streams[f"endpoint{i}"].control.mode = TGEnums.STREAM_TRANSMIT_MODE.ADVANCE_TO_NEXT_STREAM
                TGTxPort.streams[f"endpoint{i}"].rate.pps_value = 200
                TGTxPort.streams[f"endpoint{i}"].control.packets_per_burst = 2
            TGTxPort.streams[f"endpoint{i}"].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
        else:
            TGTxPort.add_stream("testStream")
            TGTxPort.streams["testStream"].packet.mac.da.mode = TGEnums.MODIFIER_MAC_MODE.FIXED
            TGTxPort.streams["testStream"].packet.mac.da.value = self._testClassref.TestCaseData["macs"][
                "multicast_lldp"]
            TGTxPort.streams["testStream"].packet.mac.sa.mode = TGEnums.MODIFIER_MAC_MODE.FIXED
            TGTxPort.streams["testStream"].packet.mac.sa.value = self._testClassref.TestCaseData["macs"][
                str(tx_port.id)]
            TGTxPort.streams["testStream"].frame_size.value = 1500
            if 'LLDP_max_frame_size' in self._testClassref.testName:
                TGTxPort.streams["testStream"].packet.data_pattern.value = \
                self._testClassref.TestCaseData["LLDP_packets"]["LLDP_Max_frame_size_all_options"]
            elif 'LLDP_ttl' in self._testClassref.testName:
                TGTxPort.streams["testStream"].packet.data_pattern.value = \
                self._testClassref.TestCaseData["LLDP_packets"]["LLDP_ttl_pckt"]
            elif 'LLDP_cdp_negative' in self._testClassref.testName:
                TGTxPort.streams["testStream"].packet.data_pattern.value = \
                self._testClassref.TestCaseData["LLDP_packets"]["LLDP_cdp_pckt"]
            elif 'LLDP_received_optional_tlvs' in self._testClassref.testName:
                TGTxPort.streams["testStream"].packet.data_pattern.value = \
                self._testClassref.TestCaseData["LLDP_packets"]["LLDP_pckt_all_opt"]
            else:
                TGTxPort.streams["testStream"].packet.data_pattern.value = \
                self._testClassref.TestCaseData["LLDP_packets"]["LLDP_pckt"]
            if 'LLDP_rx_port_down_up' in self._testClassref.testName:
                TGTxPort.properties.ignore_link_status = True
            TGTxPort.streams["testStream"].packet.data_pattern.type = TGEnums.DATA_PATTERN_TYPE.FIXED
            TGTxPort.streams["testStream"].packet.l2_proto = TGEnums.L2_PROTO.NONE
            TGTxPort.streams["testStream"].rate.mode = TGEnums.STREAM_RATE_MODE.UTILIZATION
            if 'LLDP_ttl' in self._testClassref.testName:
                TGTxPort.streams["testStream"].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
            else:
                TGTxPort.streams["testStream"].control.mode = TGEnums.STREAM_TRANSMIT_MODE.CONTINUOUS_PACKET
            TGTxPort.streams["testStream"].rate.utilization_value = 100
        #TGTxPort.apply_streams()
        TGTxPort.apply()

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

    def verifyCapturedOnPort(self, port):
        funcname = GetFunctionName(self.verifyCapturedOnPort)
        port.TGPort.start_capture()
        sleep(10)
        port.TGPort.stop_capture()
        single_lldp_pckt = ""
        lldp_multicast = self._testClassref.TestCaseData["macs"]["multicast_lldp"].replace(":","")
        for packet in port.TGPort.capture_buffer:
            if packet.startswith(lldp_multicast):
                single_lldp_pckt = packet
                break

        if 'LLDP_transmitted_mandatory_tlvs' in self._testClassref.testName:
            chasiss_id = single_lldp_pckt[34:46]
            port_id = single_lldp_pckt[52:64]
            ttl = single_lldp_pckt[68:72]
            chasiss_expected_id = "".join(self.getPortMac('eth0').split(':')).upper()
            port_expected_id = self._testClassref.TestCaseData["LLDP_packets"]["LLDP_trasmitted_mand_port_id"]
            ttl_expected = self._testClassref.TestCaseData["LLDP_packets"]["LLDP_trasmitted_mand_ttl"]
            if chasiss_id != chasiss_expected_id or port_id != port_expected_id \
                    or ttl != ttl_expected :
                self.FailTheTest(f"{funcname} tlv's didn't match expected")
        elif 'LLDP_transmitted_optional_tlvs' in self._testClassref.testName:
            port_des = single_lldp_pckt[356:366]
            system_name = single_lldp_pckt[76:94]
            system_des = single_lldp_pckt[98:116]
            system_cap = single_lldp_pckt[264:268]
            mng_addr = single_lldp_pckt[280:288]
            port_des_expected = self._testClassref.TestCaseData["LLDP_packets"]["LLDP_trasmitted_opt_port_des"]
            system_name_expected = self._testClassref.TestCaseData["LLDP_packets"]["LLDP_trasmitted_opt_system_name"]
            system_des_expected = self._testClassref.TestCaseData["LLDP_packets"]["LLDP_trasmitted_opt_system_des"]
            system_cap_expected = self._testClassref.TestCaseData["LLDP_packets"]["LLDP_trasmitted_opt_system_cap"]
            mng_addr_expected = "".join(hex(int(i))[2:].rjust(2, "0") for i in LLDP_config.getHostIP().split('.')).upper()
            if port_des != port_des_expected or system_name != system_name_expected or system_des != system_des_expected \
                    or system_cap != system_cap_expected or mng_addr != mng_addr_expected:
                self.FailTheTest(f"{funcname} tlv's didn't match expected")



    def verifyReceivedTrafficIsAsExpected(self, tx_port, stressMode=False, sleepTime=0):
        """
        verifies that the whole transmitted traffic was received and that no packet loss occurred nor errors
        :param tx_port: the transmitting port
        :param rx_port: the receiving port
        :return:
        """
        funcname = GetFunctionName(self.verifyReceivedTrafficIsAsExpected)
        dbg = funcname + "Verify received traffic on port is as expected"
        self.logger.debug(dbg)
        status = self._verifyTrafficOnPort(tx_port, stressMode, sleepTime)
        if status:
                dbg = funcname + "Passed! lldp trasmitted packet have been recieved"
                self.logger.debug(dbg)
        elif 'LLDP_trasmitted' in self._testClassref.testName:
                dbg = funcname + "Failed! lldp trasmitted packet has not been recieved"
                self.FailTheTest(dbg)
        elif 'LLDP_tx_hold' in self._testClassref.testName:
                dbg = funcname + "Failed! lldp trasmitted packet has not been recieved might be a problem with tx-hold"
                self.FailTheTest(dbg)
        elif 'LLDP_transmitted_mandatory_tlvs' in self._testClassref.testName:
                dbg = funcname + "Failed! lldp trasmitted packet has not been recieved with correct tlvs values"
                self.FailTheTest(dbg)
        elif 'LLDP_bridge_interface' in self._testClassref.testName:
                dbg = funcname + "Failed! lldp trasmitted packet from slaved interface has not been recieved"
                self.FailTheTest(dbg)
        elif 'LLDP_en_dis_diff_ports' in self._testClassref.testName or 'LLDP_stress' in self._testClassref.testName:
                dbg = funcname + f"Failed! lldp packet haven't been received\dropped for {tx_port.DutDevPort.name} port"
                self.FailTheTest(dbg)


    def _verifyTrafficOnPort(self, tx_port, stressMode, sleepTime=0):
        sleep(sleepTime)
        tx_port.TGPort.get_stats()
        tx_port.TGPort.get_stats()
        tx_stats = tx_port.TGPort.statistics
        tx_c = Comparator(tx_stats)
        if 'LLDP_en_dis_diff_ports' in self._testClassref.testName or 'LLDP_stress' in self._testClassref.testName:
            if not stressMode:
                if (tx_port.id - 1) % 2 == 0:
                    tx_c.Equal(tx_stats.capture_filter, 0)
                else:
                    tx_c.NotEqual(tx_stats.capture_filter, 0)
            else:
                if (tx_port.id - 1) % 2 == 1:
                    tx_c.Equal(tx_stats.capture_filter, 0)
                else:
                    tx_c.NotEqual(tx_stats.capture_filter, 0)
        else:
            tx_c.NotEqual(tx_stats.capture_filter, 0)
        return tx_c.Compare()

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






