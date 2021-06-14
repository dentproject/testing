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
import inspect
import json
import os
import re
import time
from collections import OrderedDict
from prettytable import PrettyTable
from CLI_GlobalFunctions.SwitchDev.Bridge.BridgeConfig import BridgeConfig
from CLI_GlobalFunctions.SwitchDev.IPv4.IPv4Config import IPv4Config
from PyInfra.BaseTest_SV import BaseTest_SV_API
from PyInfra.BaseTest_SV.SV_Enums.SwitchDevInterface import SwitchDevDutInterface
from PyInfra.BaseTest_SV.SV_Enums.SwitchDevDutPort import SwitchDevDutPort
from PyInfraCommon.GlobalFunctions.Utils.Function import GetFunctionName
from PyInfraCommon.Managers.QueryTools.Comparator import Comparator
from UnifiedTG.Unified import Port, Stream
from UnifiedTG.Unified.Port import trafficFilter
from UnifiedTG.Unified.Packet import DATA_PATTERN
from UnifiedTG.Unified.TGEnums import TGEnums
from PyInfraCommon.GlobalFunctions.Utils.Exception import GetStackTraceOnException
from Tests.Implementations.CommonTestAPI import _dut_ports


class LAG_api(BaseTest_SV_API):


    def __init__(self, TestClass):
        super(LAG_api, self).__init__(TestClass)
        # self.lag_resource = json.load(self._testClassref.resource)
        self._bridge = None  # type: BridgeConfig
        self._port_list = [] #type: list[IPv4Config]
        self._tg_port_list = []  # type: list[Port]
        self._tg_port_default_phy = None
        self._tg = self._testClassref.TG.chassis
        self._port_list_SwitchDevDutInterface = [] #type: list[SwitchDevDutInterface]
        self._dut_port_list = [None]
        self._valid_regex_ip = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"

        self._lag_1 = "bond_1"
        self._lag_2 = "bond_2"
        self._router_interface_1 = None
        self._router_interface_2 = None
        # self._router_interface_3 = None
        # self._router_interface_4 = None
        self._lag_interface_list = [self._lag_1, self._lag_2]
        self._lags_created_dict = {}
        self._lag1_members = None
        self._lag2_members = None
        self.dut_active_ports = None


    def send_cmd(self, cmd="", timeout=30, exception_msg=None):
        try:
            res = self._testClassref.DutMainChannel.SendCommandAndWaitForPattern(cmd,
                                                                            timeOutSeconds=timeout)
            if res:
                return self._testClassref.DutMainChannel.lastBufferTillPrompt
            else:
                msg = "Can't send cmd:\n{}".format(res)
                if exception_msg:
                    msg = exception_msg
                raise Exception("{}\n{}".format(msg, res))
        except Exception as e:
            raise Exception("Can't send_cmd:\n{}".format(e))


    def get_from_regex(self, buff, ListOfRegx = [], GroupNum = None):

        RetVal = "Param not found !"
        if type(GroupNum) != list:
            GroupNum = [GroupNum]

        if type(ListOfRegx) != list:
            ListOfRegx = [ListOfRegx]

        tmp = buff

        for idx, elem in enumerate(ListOfRegx):
            # TmpElem = elem.decode('string_escape')
            TmpElem = str(elem)
            tmp = str(tmp)
            mo = re.search(str(TmpElem), tmp, flags=re.MULTILINE)
            match_list = re.findall(str(TmpElem), tmp, flags=re.MULTILINE)
            if mo:
                # if idx == (len(ListOfRegx) - 1):
                if GroupNum[idx] == None or GroupNum[idx] == "":
                    tmp = mo.group(0)  # full match

                elif GroupNum[idx] == 'all':
                    tmp = match_list  # update tmp for next iteration
                else:
                    tmp = mo.group(GroupNum[idx]) #
            else:
                tmp = ""

        RetVal = tmp

        return RetVal


    def load_tg_conf_json(self, file_name):
        tg_dict = {}
        try:
            caller_full_folder_path = inspect.stack()[1][1]
            path = "{}{}{}".format(os.path.dirname(caller_full_folder_path), os.sep, file_name)
            with open(path) as json_file:
                tg_dict = json.load(json_file)
        finally:
            return tg_dict


    def configTgFromJson(self, config_path, tg_port, override_da_mac="", override_dip_incr_count=""):
        tg_p1_json = config_path
        tg_dict = self.load_tg_conf_json(tg_p1_json)
        if len(override_da_mac) > 0:
            for stream in tg_dict['streams']:
                stream['packet']['mac']['da']['value'] = override_da_mac
        if len(str(override_dip_incr_count)) > 0:
            for stream in tg_dict['streams']:
                stream['packet']['ipv4']['destination_ip']['count'] = override_dip_incr_count
        tg_port.dict_to_port(tg_dict)
        temp = 3
        # tg.ports["my_port1"].dict_to_port(tg_dict)


    def dummy(self, traffic_intrrup_callback=None):
        if traffic_intrrup_callback:
            traffic_intrrup_callback()


    def getPortList(self):
        ret = self.send_cmd('ls /sys/class/net/ | grep sw1p* | sort -t p -k 2 -g')
        self._portList = ret.split("\r\n")[1:-1]
        return self._portList


    def initTest(self):
        """
        init test
        :return:
        """
        self._testClassref.DutMainChannel.shellPrompt = self._testClassref.DutManager.dut_prompt

        # self.dut_active_ports.get_all_ports_stats()
        # self.dut_active_ports.reset_all_ports_stats()
        self.initInterfaces()
        self._lag1_members = list(self._testClassref.TestCaseData['lag1_members'].values())
        self._lag2_members = list(self._testClassref.TestCaseData['lag2_members'].values())
        if self._testClassref.TestData.TestInfo._UseTG:
            self.dut_active_ports = _dut_ports(ports=self._lag1_members + self._lag2_members + [self._port_list_SwitchDevDutInterface[0], self._port_list_SwitchDevDutInterface[1]])
        else:
            self.dut_active_ports = _dut_ports(ports=self._lag1_members + self._lag2_members)

        self.dut_active_ports.set_active_chan(self._testClassref.DutMainChannel)


    def initInterfaces(self):
        funcname = GetFunctionName(self.initInterfaces)
        #init ports
        if self._testClassref.TestData.TestInfo._UseTG:
            for i in range(1, len(list(self._testClassref.TGDutLinks.values()))+1):
                self._port_list.append(IPv4Config(SwitchDevDutPort(self._testClassref.TGDutLinks[i].DutDevPort.name)))
                self._tg_port_list.append(self._testClassref.TGDutLinks[i].TGPort)
            self._port_list_SwitchDevDutInterface.extend([x.switchdevInterface for x in self._port_list])
            self._dut_port_list = self.getPortList()
            self._router_interface_1 = self._port_list_SwitchDevDutInterface[0]
            self._router_interface_2 = self._port_list_SwitchDevDutInterface[1]
            # self._router_interface_3 = self._port_list_SwitchDevDutInterface[2]
            # self._router_interface_4 = self._port_list_SwitchDevDutInterface[3]
            self._tg_port_default_phy = self._tg_port_list[0].properties.media_type
            self._tg = self._testClassref.TG.chassis
        else:
            self._port_list_SwitchDevDutInterface.extend([x.switchdevInterface for x in self._port_list])
            self._dut_port_list = self.getPortList()
            self._router_interface_1 = self._dut_port_list[0]
            self._router_interface_2 = self._dut_port_list[1]
            # self._router_interface_3 = self._dut_port_list[2]
            # self._router_interface_4 = self._dut_port_list[3]


    def deleteLAGInterface(self, name):
        """
        delete LAG interface
        :return:
        """
        funcname = GetFunctionName(self.deleteLAGInterface)
        cmd = "ip link delete {}".format(name)
        buff = self.send_cmd(cmd, timeout=10)
        return buff


    def deleteBRInterface(self, name):
        """
        delete bridge interface
        :return:
        """
        funcname = GetFunctionName(self.deleteBRInterface)
        cmd = "ip link delete {}".format(name)
        buff = self.send_cmd(cmd, timeout=10)
        return buff


    def createBRInterface(self, name, vlan_filtering="1"):
        """
        creates bridge interface
        :return:
        """
        funcname = GetFunctionName(self.createBRInterface)
        cmd = "ip link add name {} type bridge vlan_filtering {}".format(name, vlan_filtering)
        buff = self.send_cmd(cmd, timeout=10)
        self.Add_Cleanup_Function_To_Stack(LAG_api.deleteBRInterface, self, name)
        return buff


    def createLAGInterface(self, name, mode="802.3ad"):
        """
        creates LAG interface
        :return:
        """
        funcname = GetFunctionName(self.createLAGInterface)
        cmd = "ip link add name {} type bond mode {}".format(name, mode)
        buff = self.send_cmd(cmd, timeout=10)
        self.Add_Cleanup_Function_To_Stack(LAG_api.deleteLAGInterface, self, name)
        self._addLAGToDict(name)
        return buff


    def _addLAGToDict(self, name):
        self._updateLAGInfo(name)


    def setInterfaceAdminState(self, name, state="up"):
        """
        set interface link status
        :return:
        """
        funcname = GetFunctionName(self.setInterfaceAdminState)
        cmd = "ip link set dev {} {}".format(name, state)
        buff = self.send_cmd(cmd, timeout=10)
        return buff


    def verifyLAGCreated(self, buff, name):
        """
        Verify LAG interface created
        :return:
        """
        funcname = GetFunctionName(self.verifyLAGCreated)
        if "file exist" in str(buff).lower():
            raise Exception("Can't create LAG interface with name {} - already exist:\n{}".format(name, buff))
        # cmd = "ip link delete {}".format(name)
        # buff = self.send_cmd(cmd, timeout=10)
        return buff


    def _updateLAGInfo(self, name):
        cmd = "ip link show type bond {}".format(name)
        buff = self.send_cmd(cmd, timeout=10)
        name = self.get_from_regex(buff, ["\d+:\s+(.*):"], 1)
        mtu = self.get_from_regex(buff, ["mtu\s+(\d+)"], 1)
        qdisc = self.get_from_regex(buff, ["qdisc\s+(.*?)\s+"], 1)
        state = self.get_from_regex(buff, ["state\s+(.*?)\s+"], 1)
        group = self.get_from_regex(buff, ["group\s+(.*?)\s+"], 1)
        qlen = self.get_from_regex(buff, ["qlen\s+(.*?)\s+"], 1)
        mac = self.get_from_regex(buff, ["link/ether\s+(.*?)\s+"], 1)
        brd = self.get_from_regex(buff, ["brd\s+(.*)\s*"], 1)
        self._lags_created_dict[name] = {
            "name": name,
            "mtu": mtu,
            "qdisc": qdisc,
            "state": state,
            "group": group,
            "qlen": qlen,
            "mac": mac,
            "brd": str(brd).replace("\r", ""),

        }


    def unslaveInterfaceFromBridge(self, if_name):
        """
        unenslave interface from bridge
        :return:
        """
        funcname = GetFunctionName(self.unslaveInterfaceFromBridge)

        cmd = "ip link set {} nomaster".format(if_name)
        buff = self.send_cmd(cmd, timeout=10)
        return buff


    def unslaveInterfaceFromLAG(self, if_name):
        """
        unenslave interface from LAG
        :return:
        """
        funcname = GetFunctionName(self.unslaveInterfaceFromLAG)

        cmd = "ip link set {} nomaster".format(if_name)
        buff = self.send_cmd(cmd, timeout=10)
        return buff


    def verifyInterfaceNotEnslavedToLAG(self, if_name, lag_name):
        """
        verify interface is not enslaved in LAG
        :return:
        """
        funcname = GetFunctionName(self.verifyInterfaceNotEnslavedToLAG)
        cmd = "ip link show {}".format(if_name)
        buff = self.send_cmd(cmd, timeout=10)
        master = self.get_from_regex(buff, ["master\s+(.*?)\s+"], 1)
        if str(master).lower() == str(lag_name).lower():
            raise Exception("Interface {} enslaved to LAG {}:\n{}".format(if_name, lag_name, buff))

        return buff


    def verifyInterfaceEnslavedToBridge(self, if_name, br_name, prev_buff=None):
        """
        verify interface is enslaved in bridge
        :return:
        """
        funcname = GetFunctionName(self.verifyInterfaceEnslavedToBridge)
        if prev_buff != None:
            known_errors = ["file exist", "error", "invalid", "wrong"]
            res = [i for i in known_errors if i in str(prev_buff).lower()]
            if len(res) > 0:
                raise Exception("interface with name {} couldn't be enslaved to Bridge {}:\n{}".format(if_name, br_name, prev_buff))
        cmd = "ip link show {}".format(if_name)
        buff = self.send_cmd(cmd, timeout=10)
        master = self.get_from_regex(buff, ["master\s+(.*?)\s+"], 1)
        if str(master).lower() != str(br_name).lower():
            raise Exception("Can't enslave interface {} to Bridge {}:\n{}".format(if_name, br_name, buff))


        return buff


    def verifyInterfaceEnslavedToLAG(self, if_name, lag_name, prev_buff=None, negative=False):
        """
        verify interface is enslaved in LAG
        :return:
        """
        funcname = GetFunctionName(self.verifyInterfaceEnslavedToLAG)
        if prev_buff != None:
            known_errors = ["file exist", "error", "invalid", "wrong"]
            res = [i for i in known_errors if i in str(prev_buff).lower()]
            if not negative:
                if len(res) > 0:
                    raise Exception("interface with name {} couldn't be enslaved to LAG {}:\n{}".format(if_name, lag_name, prev_buff))
        cmd = "ip link show {}".format(if_name)
        buff = self.send_cmd(cmd, timeout=10)
        master = self.get_from_regex(buff, ["master\s+(.*?)\s+"], 1)
        if str(master).lower() != str(lag_name).lower():
            if negative:
                pass
            else:
                raise Exception("Can't enslave interface {} to LAG {}:\n{}".format(if_name, lag_name, buff))
        return buff

    def verifyLAGMemberIsUp(self, if_name, lag_name):
        """
        verify interface is enslaved in LAG
        :return:
        """
        funcname = GetFunctionName(self.verifyInterfaceEnslavedToLAG)
        cmd = "ip link show {}".format(if_name)
        buff = self.send_cmd(cmd, timeout=10)
        if "lower_up" not in str(buff).lower():
            raise Exception("Interface {} in LAG {} not in up state:\n{}".format(if_name, lag_name, buff))
        return buff


    def enslaveInterfaceToBridge(self, if_name, br_name):
        """
        enslave interface to bridge
        :return:
        """
        funcname = GetFunctionName(self.enslaveInterfaceToBridge)

        cmd = "ip link set {} master {}".format(if_name, br_name)
        buff = self.send_cmd(cmd, timeout=10)
        self.Add_Cleanup_Function_To_Stack(LAG_api.unslaveInterfaceFromBridge, self, if_name)
        return buff


    def enslaveInterfaceToLAG(self, if_name, lag_name):
        """
        enslave interface to LAG
        :return:
        """
        funcname = GetFunctionName(self.enslaveInterfaceToLAG)

        cmd = "ip link set {} master {}".format(if_name, lag_name)
        buff = self.send_cmd(cmd, timeout=10)
        self.Add_Cleanup_Function_To_Stack(LAG_api.unslaveInterfaceFromLAG, self, if_name)
        return buff


    def removeIPFromInterface(self, if_name, address, mask):
        """
        delete IP address from interface
        :return:
        """
        funcname = GetFunctionName(self.removeIPFromInterface)
        cmd = "ip addr delete {}/{} dev {}".format(address, mask, if_name)
        buff = self.send_cmd(cmd, timeout=10)
        return buff


    def assignIPOnInterface(self, if_name, address, mask):
        """
        assign IP address on interface
        :return:
        """
        funcname = GetFunctionName(self.assignIPOnInterface)

        cmd = "ip addr add dev {} {}/{}".format(if_name, address, mask)
        buff = self.send_cmd(cmd, timeout=10)
        cmd = "ifconfig {} up".format(if_name)
        buff = self.send_cmd(cmd, timeout=10)

        # buff = self.send_cmd(cmd, timeout=10)  #todo check why only twice is needed
        self.Add_Cleanup_Function_To_Stack(LAG_api.removeIPFromInterface, self, if_name, address, mask)
        return buff


    def verifyIPOnInterface(self, if_name, address, mask):
        """
        verify IP address on interface
        :return:
        """
        funcname = GetFunctionName(self.verifyIPOnInterface)
        cmd = "ip addr show {}".format(if_name)
        buff = self.send_cmd(cmd, timeout=10)
        inet = self.get_from_regex(buff, ["inet\s+(.*)/"], 1)
        mask_get = self.get_from_regex(buff, ["inet\s+.*/(.*?)\s"], 1)
        if str(inet).lower() != str(address).lower() and str(mask).lower() != str(mask_get).lower():
            raise Exception("IP address {}/{} not configured properly on {}:\n{}".format(address, mask, if_name, buff))

        return buff


    def removeRoute(self, address, mask, dev):
        """
        delete route
        :return:
        """
        funcname = GetFunctionName(self.removeRoute)
        cmd = "ip route del {}/{} dev {}".format(address, mask, dev)
        buff = self.send_cmd(cmd, timeout=10)
        return buff


    def addRoute(self, address, mask, dev):
        """
        add route on interface
        :return:
        """
        funcname = GetFunctionName(self.addRoute)

        cmd = "ip route add {}/{} dev {}".format(address, mask, dev)
        buff = self.send_cmd(cmd, timeout=10)
        self.Add_Cleanup_Function_To_Stack(LAG_api.removeRoute, self, address, mask, dev)
        return buff


    def removeStaticARP(self, if_name, ip):
        """
        delete static ARP
        :return:
        """
        funcname = GetFunctionName(self.removeStaticARP)
        cmd = "arp -i {} -d {}".format(if_name, ip)
        buff = self.send_cmd(cmd, timeout=10)
        return buff


    def verifyStaticARP(self, if_name, ip, mac):
        """
        verify static ARP entry
        :return:
        """
        funcname = GetFunctionName(self.verifyStaticARP)

        cmd = "ip neigh show dev {}".format(if_name)
        buff = self.send_cmd(cmd, timeout=10)
        search_str = "{} lladdr {}".format(ip, mac)
        if str(search_str).lower() not in str(buff).lower():
            raise Exception("Static ARP not configured properly on {}:\n{}".format(if_name, buff))

        return buff


    def addStaticARP(self, if_name, ip, mac):
        """
        add static ARP on interface
        :return:
        """
        funcname = GetFunctionName(self.addStaticARPs)

        cmd = "arp -i {} -s {} {}".format(if_name, ip, mac)
        buff = self.send_cmd(cmd, timeout=10)
        # buff = self.send_cmd(cmd, timeout=10)  #todo check why only twice is needed
        self.Add_Cleanup_Function_To_Stack(LAG_api.removeStaticARP, self, if_name, ip)
        return buff


    def verifyLAGLinkStatus(self, name, state="up"):
        """
        verify LAG interface in UP state
        :return:
        """
        funcname = GetFunctionName(self.verifyLAGLinkStatus)
        if str(self._lags_created_dict[name]["state"]).lower() != state.lower():
            raise Exception("LAG interface with name {} state is not in requested state: {}:\n{}".format(name,
                                                                                                         state,
                                                                                                         self._lags_created_dict[name]))
    def enslaveInterfaceToUnsupportedLAGs(self):
        funcname = GetFunctionName(self.enslaveInterfaceToUnsupportedLAGs)
        unsupported_lags = ["bond_1", "bond_2", "bond_3", "bond_4", "bond_5"]
        self.setLinkStateInterfaces([self._lag1_members[0]], state="down")
        for name in unsupported_lags:
            buff = self.enslaveInterfaceToLAG(self._lag1_members[0], name)
            if "Unsupported LAG Tx type" not in buff:
                cmd = "cat /proc/net/bonding/{}".format(name)
                buff = self.send_cmd(cmd, timeout=10)
                self.FailTheTest("It was possible to enslave port {} to LAG {} with unsupported mode:\n{}".format(self._lag1_members[0], name, buff), abort_Test=False)

    def createUnsupportedLAGs(self):
        funcname = GetFunctionName(self.createUnsupportedLAGs)
        #"balance-xor" removed due to SDD change
        unsupported_modes = ["balance-rr", "active-backup", "broadcast", "balance-tlb", "balance-alb"]
        for index in range(1, len(unsupported_modes)+1):
            name = "bond_{}".format(index)
            result = self.createLAGInterface(name, mode=unsupported_modes[index-1])
            self.verifyLAGCreated(result, name)
            self.setInterfaceAdminState(name)
            self.verifyLAGLinkStatus(name, state="down")


    def createLAGInterfaces(self, start, stop, verify=True):
        funcname = GetFunctionName(self.createLAGInterfaces)
        for index in range(start, stop+1):
            name = "bond_{}".format(index)
            result = self.createLAGInterface(name)
            if verify:
                self.verifyLAGCreated(result, name)
            self.setInterfaceAdminState(name)
            self.verifyLAGLinkStatus(name, state="down")


    def verifyLAGNotCreated(self, buff, name):
        """
        verify LAG interface doesn't exist
        :return:
        """
        funcname = GetFunctionName(self.verifyLAGNotCreated)
        known_errors = ["file exist", "error", "invalid", "wrong"]
        res = [i for i in known_errors if i in str(buff).lower()]
        if len(res) < 1:
            raise Exception("LAG interface with name {} created while it shouldn't:\n{}".format(name, buff))
        return buff


    def createInvalidLAGInterface(self, name, index):
        funcname = GetFunctionName(self.createInvalidLAGInterface)
        result = self.createLAGInterface(name)
        self.verifyLAGNotCreated(result, name)


    def enslaveInterfaceToLAGsUsingBash(self, start, stop, interface):
        """
        enslave interface to lags interfaces in bash loop
        :return:
        """
        funcname = GetFunctionName(self.enslaveInterfaceToLAGsUsingBash)
        tried = int(stop) - int(start)
        lag_range = "{}..{}".format(start, stop)
        cmd = "time for i in {{{}}}; do ip link set {} master bond_$i; done".format(lag_range, interface)
        buff = self.send_cmd(cmd, timeout=4000)
        self.Add_Cleanup_Function_To_Stack(LAG_api.unslaveInterfaceFromLAG, self, interface)


    def createLAGInterfacesUsingBash(self, start, stop):
        """
        add lag interfaces in bash loop
        :return:
        """
        funcname = GetFunctionName(self.createLAGInterfacesUsingBash)
        tried = int(stop) - int(start)
        lag_range = "{}..{}".format(start, stop)
        cmd = "time for i in {{{}}}; do ip link add bond_$i type bond; done".format(lag_range)
        buff = self.send_cmd(cmd, timeout=300)
        self.Add_Cleanup_Function_To_Stack(LAG_api.deleteLAGInterfacesUsingBash, self, start, stop)
        lags = self.getNumOfLAGInterface()
        if int(lags) < tried:
            self.FailTheTest("Couldn't add all LAG interfaces - tried: {}, successeed: {}\n".format(tried, lags, buff), abort_Test=True)


    def setLAGInterfacesLinkStateUsingBash(self, start, stop, state="up", disable_cleanup=False):
        """
        set link status for lag interfaces in bash loop
        :return:
        """
        funcname = GetFunctionName(self.setLAGInterfacesLinkStateUsingBash)
        tried = int(stop) - int(start)
        lag_range = "{}..{}".format(start, stop)
        cmd = "time for i in {{{}}}; do ip link set dev bond_$i up; done".format(lag_range)
        buff = self.send_cmd(cmd, timeout=300)
        if not disable_cleanup:
            self.Add_Cleanup_Function_To_Stack(LAG_api.setLAGInterfacesLinkStateUsingBash, self, start, stop, "down", True)
        # vrfs = self.getNumOfVrfInterface()
        # if int(vrfs) < tried:
        #     self.FailTheTest("Couldn't add all VRF interfaces - tried: {}, successeed: {}\n".format(tried, vrfs, buff), abort_Test=True)


    def getNumOfLAGInterface(self):
        """
        count number of lag interfaces
        :return:
        """
        funcname = GetFunctionName(self.getNumOfLAGInterface)
        cmd = "ip link show | grep bond | wc -l"
        buff = self.send_cmd(cmd, timeout=10)
        res = self.get_from_regex(buff, ["(^\d+)"], 1)
        return res


    def assignInterfacesToBridge(self, interface_list, br_name):
        funcname = GetFunctionName(self.assignInterfacesToBridge)
        for interface in interface_list:
            buff = self.enslaveInterfaceToBridge(interface, br_name)
            self.verifyInterfaceEnslavedToBridge(interface, br_name, buff)


    def setLinkStateInterfacesDown(self, interface_list):
        funcname = GetFunctionName(self.setLinkStateInterfacesDown)
        for interface in interface_list:
            self.setInterfaceAdminState(interface, "down")

    def setLinkStateInterfaces(self, interface_list, state="up"):
        funcname = GetFunctionName(self.setLinkStateInterfaces)
        for interface in interface_list:
            self.setInterfaceAdminState(interface, state)
            self.Add_Cleanup_Function_To_Stack(LAG_api.setLinkStateInterfacesDown, self, [interface])


    def isDUTPortTenGiga(self, if_name):
        funcname = GetFunctionName(self.isDUTPortTenGiga)
        cmd = "ethtool {}".format(if_name)
        buff = self.send_cmd(cmd, timeout=10)
        if "10000baseSR/Full" in str(buff):
            return True
        return False




    def setLinksToGiga(self):
        funcname = GetFunctionName(self.setLinksToGiga)
        isTenGiga = self.isDUTPortTenGiga(self._lag1_members[0])
        if isTenGiga:
            self.setLinkSpeedInterfaces(self._lag1_members)
            self.setLinkSpeedInterfaces(self._lag2_members)
            for if_name in self._lag1_members:
                self.Add_Cleanup_Function_To_Stack(LAG_api.setLinkSpeedInterfaces, self, [if_name], "10000")
            for if_name in self._lag2_members:
                self.Add_Cleanup_Function_To_Stack(LAG_api.setLinkSpeedInterfaces, self, [if_name], "10000")


    def setLinkSpeedInterfaces(self, interface_list, speed="1000"):
        funcname = GetFunctionName(self.setLinkSpeedInterfaces)
        for interface in interface_list:
            self.setDutPortSpeed(interface, speed)


    def verifyAllLAGMemberInUpState(self, interface_list, lag_name):
        funcname = GetFunctionName(self.verifyAllLAGMemberInUpState)
        # set delay to let link set in up state
        sleep(10)

        for interface in interface_list:
            self.verifyLAGMemberIsUp(interface, lag_name)

    def assignInterfacesToLAGs(self, interface_list, lag_name, negative=False):
        funcname = GetFunctionName(self.assignInterfacesToLAGs)
        for interface in interface_list:
            self.setInterfaceAdminState(interface, "down")
            buff = self.enslaveInterfaceToLAG(interface, lag_name)
            self.verifyInterfaceEnslavedToLAG(interface, lag_name, buff, negative=negative)
            self.setInterfaceAdminState(interface, "up")


    def assignIPOnInterfaces(self):
        funcname = GetFunctionName(self.assignIPOnInterfaces)
        dc_address_1 = "1.1.1.1"
        dc_address_2 = "1.1.1.2"
        mask = "24"

        self.assignIPOnInterface(self._router_interface_1, dc_address_1, mask)
        self.verifyIPOnInterface(self._router_interface_1, dc_address_1, mask)

        self.assignIPOnInterface(self._router_interface_2, dc_address_2, mask)
        self.verifyIPOnInterface(self._router_interface_2, dc_address_2, mask)

        self.assignIPOnInterface(self._router_interface_3, dc_address_1, mask)
        self.verifyIPOnInterface(self._router_interface_3, dc_address_1, mask)

        self.assignIPOnInterface(self._router_interface_4, dc_address_2, mask)
        self.verifyIPOnInterface(self._router_interface_4, dc_address_2, mask)


    def assignIPOnInterfacesForNormalRouting(self):
        funcname = GetFunctionName(self.assignIPOnInterfaces)
        dc_address_1 = "1.1.1.1"
        dc_address_2 = "1.1.1.2"
        mask = "24"

        self.assignIPOnInterface(self._router_interface_1, dc_address_1, mask)
        self.verifyIPOnInterface(self._router_interface_1, dc_address_1, mask)

        self.assignIPOnInterface(self._router_interface_2, dc_address_2, mask)
        self.verifyIPOnInterface(self._router_interface_2, dc_address_2, mask)

        self.setInterfaceAdminState(self._router_interface_3)
        self.setInterfaceAdminState(self._router_interface_4)


    def addRoutes(self):
        funcname = GetFunctionName(self.addRoutes)
        self.addDefaultRouteVRF(self._lag_1)
        self.verifyDefaultRouteVRF(self._lag_1)
        self.addRouteVRF(self._lag_1, "192.168.1.0", "24", self._router_interface_2)
        self.addRouteVRF(self._lag_1, "1.1.1.0", "24", self._router_interface_2)

        self.addDefaultRouteVRF(self._lag_2)
        self.verifyDefaultRouteVRF(self._lag_2)
        self.addRouteVRF(self._lag_2, "192.168.1.0", "24", self._router_interface_4)
        self.addRouteVRF(self._lag_2, "1.1.1.0", "24", self._router_interface_4)


    def addRoutesForNormalRouting(self):
        funcname = GetFunctionName(self.addRoutes)
        # self.addDefaultRouteVRF(self._lag_1)
        # self.verifyDefaultRouteVRF(self._lag_1)
        self.addRoute("192.168.1.0", "24", self._router_interface_2)
        self.addRoute("1.1.1.0", "24", self._router_interface_2)


    def addStaticARPs(self):
        funcname = GetFunctionName(self.addStaticARPs)
        # VRF 1
        # tg1 -> tg2 dc: 1.1.1.100(00:AA:00:00:00:01) -> 1.1.1.200(mac of self._router_interface_1)
        # tg1 -> tg2 rc: 1.1.1.100(00:AA:00:00:00:01) -> 192.168.1.200(mac of self._router_interface_1)
        # tg2 -> tg1 dc: 1.1.1.200(00:AA:00:00:00:02) -> 1.1.1.100(mac of self._router_interface_2)
        # tg2 -> tg1 rc: 192.168.1.200(00:AA:00:00:00:02)(mac of self._router_interface_2)
        vrf_1_dc_host_ip = "1.1.1.100"  # ixia port 1 src ip
        vrf_1_dc_host_mac = "00:AA:00:00:00:01"  # ixia port 1 src mac
        vrf_1_rc_host_ip = "192.168.1.100"  # ixia port 2 src ip
        vrf_1_rc_host_mac = "00:AA:00:00:11:01"  # ixia port 2 src mac

        self.addStaticARP(self._router_interface_1, vrf_1_dc_host_ip, vrf_1_dc_host_mac)
        self.verifyStaticARP(self._router_interface_1, vrf_1_dc_host_ip, vrf_1_dc_host_mac)
        self.addStaticARP(self._router_interface_1, vrf_1_rc_host_ip, vrf_1_rc_host_mac)
        self.verifyStaticARP(self._router_interface_1, vrf_1_rc_host_ip, vrf_1_rc_host_mac)

        vrf_2_dc_host_ip = "1.1.1.200"  # ixia port 2 src ip
        vrf_2_dc_host_mac = "00:AA:00:00:00:02"  # ixia port 2 src mac
        vrf_2_rc_host_ip = "192.168.1.200"  # ixia port 1 src ip
        vrf_2_rc_host_mac = "00:AA:00:00:22:02"  # ixia port 1 src mac
        self.addStaticARP(self._router_interface_2, vrf_2_dc_host_ip, vrf_2_dc_host_mac)
        self.verifyStaticARP(self._router_interface_2, vrf_2_dc_host_ip, vrf_2_dc_host_mac)
        self.addStaticARP(self._router_interface_2, vrf_2_rc_host_ip, vrf_2_rc_host_mac)
        self.verifyStaticARP(self._router_interface_2, vrf_2_rc_host_ip, vrf_2_rc_host_mac)

        # VRF 2
        # tg3 -> tg4 dc: 1.1.1.100(00:AA:00:00:00:03) -> 1.1.1.200(mac of self._router_interface_3)
        # tg3 -> tg4 rc: 1.1.1.100(00:AA:00:00:00:03) -> 192.168.1.200(mac of self._router_interface_3)
        # tg4 -> tg3 dc: 1.1.1.200(00:AA:00:00:00:04) -> 1.1.1.100(mac of self._router_interface_4)
        # tg4 -> tg3 rc: 192.168.1.200(00:AA:00:00:00:04) -> 1.1.1.100(mac of self._router_interface_4)

        vrf_3_dc_host_ip = "1.1.1.100"  # ixia port 3 src ip
        vrf_3_dc_host_mac = "00:AA:00:00:00:03"  # ixia port 3 src mac
        vrf_3_rc_host_ip = "192.168.1.100"  # ixia port 1 src ip
        vrf_3_rc_host_mac = "00:AA:00:00:33:03"  # ixia port 1 src mac

        self.addStaticARP(self._router_interface_3, vrf_3_dc_host_ip, vrf_3_dc_host_mac)
        self.verifyStaticARP(self._router_interface_3, vrf_3_dc_host_ip, vrf_3_dc_host_mac)
        self.addStaticARP(self._router_interface_3, vrf_3_rc_host_ip, vrf_3_rc_host_mac)
        self.verifyStaticARP(self._router_interface_3, vrf_3_rc_host_ip, vrf_3_rc_host_mac)

        vrf_4_dc_host_ip = "1.1.1.200"  # ixia port 4 src ip
        vrf_4_dc_host_mac = "00:AA:00:00:00:04"  # ixia port 4 src mac
        vrf_4_rc_host_ip = "192.168.1.200"  # ixia port 1 src ip
        vrf_4_rc_host_mac = "00:AA:00:00:44:04"
        self.addStaticARP(self._router_interface_4, vrf_4_dc_host_ip, vrf_4_dc_host_mac)
        self.verifyStaticARP(self._router_interface_4, vrf_4_dc_host_ip, vrf_4_dc_host_mac)
        self.addStaticARP(self._router_interface_4, vrf_4_rc_host_ip, vrf_4_rc_host_mac)
        self.verifyStaticARP(self._router_interface_4, vrf_4_rc_host_ip, vrf_4_rc_host_mac)


    def addStaticARPsForNormalRouting(self):
        funcname = GetFunctionName(self.addStaticARPs)
        # tg1 -> tg2 dc: 1.1.1.100(00:AA:00:00:00:01) -> 1.1.1.200(mac of self._router_interface_1)
        # tg1 -> tg2 rc: 1.1.1.100(00:AA:00:00:00:01) -> 192.168.1.200(mac of self._router_interface_1)
        # tg2 -> tg1 dc: 1.1.1.200(00:AA:00:00:00:02) -> 1.1.1.100(mac of self._router_interface_2)
        # tg2 -> tg1 rc: 192.168.1.200(00:AA:00:00:00:02)(mac of self._router_interface_2)
        vrf_1_dc_host_ip = "1.1.1.100"  # ixia port 1 src ip
        vrf_1_dc_host_mac = "00:AA:00:00:00:01"  # ixia port 1 src mac
        vrf_1_rc_host_ip = "192.168.1.100"  # ixia port 2 src ip
        vrf_1_rc_host_mac = "00:AA:00:00:11:01"  # ixia port 2 src mac

        self.addStaticARP(self._router_interface_1, vrf_1_dc_host_ip, vrf_1_dc_host_mac)
        self.verifyStaticARP(self._router_interface_1, vrf_1_dc_host_ip, vrf_1_dc_host_mac)
        self.addStaticARP(self._router_interface_1, vrf_1_rc_host_ip, vrf_1_rc_host_mac)
        self.verifyStaticARP(self._router_interface_1, vrf_1_rc_host_ip, vrf_1_rc_host_mac)

        vrf_2_dc_host_ip = "1.1.1.200"  # ixia port 2 src ip
        vrf_2_dc_host_mac = "00:AA:00:00:00:02"  # ixia port 2 src mac
        vrf_2_rc_host_ip = "192.168.1.200"  # ixia port 1 src ip
        vrf_2_rc_host_mac = "00:AA:00:00:22:02"  # ixia port 1 src mac
        self.addStaticARP(self._router_interface_2, vrf_2_dc_host_ip, vrf_2_dc_host_mac)
        self.verifyStaticARP(self._router_interface_2, vrf_2_dc_host_ip, vrf_2_dc_host_mac)
        self.addStaticARP(self._router_interface_2, vrf_2_rc_host_ip, vrf_2_rc_host_mac)
        self.verifyStaticARP(self._router_interface_2, vrf_2_rc_host_ip, vrf_2_rc_host_mac)


    def callCleanupStack(self):
        funcname = GetFunctionName(self.callCleanupStack)
        if self._testClassref._cleanup_stack:
            # begin calling to cleanup functions
            self.logger.trace(funcname + " starting to call to cleanup functions of test")
            while len(self._testClassref._cleanup_stack):
                func_params = self._testClassref._cleanup_stack.pop()
                this_func_name = GetFunctionName(func_params.func)

                # call the function
                try:
                    res = func_params()
                    if res is not None and not res:
                        # we got a False return result from some cleanup function
                        err = funcname + " received {} result from cleanup function {} !\n".format(res, this_func_name)
                        self.logger.error(err)
                        result = False
                except Exception as e:
                    exc_data = GetStackTraceOnException(e)
                    err = funcname + " caught exception from cleanup function {}, exception info:{}\n".format(
                        this_func_name, exc_data)
                    # try to recover from cleanup failure
                    self.logger.error(err)
                    # Run_Cleanup_Recovery(self)
                    raise e.__class__(err)


    def getTgPortDAMac(self, name):
        funcname = GetFunctionName(self.getTgPortDAMac)
        cmd = "ip link show {}".format(name)
        buff = self.send_cmd(cmd, timeout=10)
        mac = self.get_from_regex(buff, ["link\/ether\s+(.*?)\s+"], 1)
        if len(str(mac)) < 1:
            raise Exception("Can't get MAC of interface {}:\n{}".format(name, buff))

        return mac


    def setTGStreamsUtilRate(self, rate):
        p1_s1 = list(self._tg_port_list[0].streams.items())[0][1]
        p2_s1 = list(self._tg_port_list[1].streams.items())[0][1]
        p1_s1.rate.utilization_value = rate
        p2_s1.rate.utilization_value = rate
        p1_s1.apply(apply_to_hw=True)
        p2_s1.apply(apply_to_hw=True)

    def configTgPortsBasicFlow(self):
        funcname = GetFunctionName(self.configTgPortsBasicFlow)
        # port1DAMac = self.getTgPortDAMac(name=self._router_interface_1)
        # port2DAMac = self.getTgPortDAMac(name=self._router_interface_2)
        # port3DAMac = self.getTgPortDAMac(name=self._router_interface_3)
        # port4DAMac = self.getTgPortDAMac(name=self._router_interface_4)
        self.logger.info("Setting DIP increment count to {}".format(self._testClassref.TestCaseData['dip_incr_count']))
        self.configTgFromJson("resources/tc1_tg_p1.json", self._tg_port_list[0], override_dip_incr_count=self._testClassref.TestCaseData['dip_incr_count'])
        self.configTgFromJson("resources/tc1_tg_p2.json", self._tg_port_list[1], override_dip_incr_count=self._testClassref.TestCaseData['dip_incr_count'])
        # self.configTgFromJson("resources/tc1_tg_p3.json", self._tg_port_list[2], override_da_mac=port3DAMac)
        # self.configTgFromJson("resources/tc1_tg_p4.json", self._tg_port_list[3], override_da_mac=port4DAMac)
        # todo add the below media_type to the UTG dict_to_port function to save the time of two apply
        self._tg_port_list[0].properties.media_type = self._tg_port_default_phy
        self._tg_port_list[0].apply()
        self._tg_port_list[1].properties.media_type = self._tg_port_default_phy
        self._tg_port_list[1].apply()
        # self._tg_port_list[2].properties.media_type = self._tg_port_default_phy
        # self._tg_port_list[2].apply()
        # self._tg_port_list[3].properties.media_type = self._tg_port_default_phy
        # self._tg_port_list[3].apply()


    def prepareCurrentStreamForTx(self, tx_port, tx_stream_id):
        funcname = GetFunctionName(self.prepareCurrentStreamForTx)

        current_sip = ""
        p1_s1 = list(self._tg_port_list[tx_port].streams.items())[0][1]
        p1_s2 = list(self._tg_port_list[tx_port].streams.items())[1][1]
        if tx_stream_id == 1:
            p1_s1.enabled = True
            p1_s2.enabled = False
            current_sip = p1_s1.packet.ipv4.source_ip.value
        elif tx_stream_id == 2:
            p1_s1.enabled = False
            p1_s2.enabled = True
            current_sip = p1_s2.packet.ipv4.source_ip.value
        p1_s1.apply(apply_to_hw=True)
        p1_s2.apply(apply_to_hw=True)

        return current_sip


    def verifyNotMoreThanMaxLag(self):
        create_lag_res = True
        try:
            self.createLAGInterfaces(65, 65)
            br_name = "br_65"
            self.createBRInterface(br_name, vlan_filtering="0")
            self.assignInterfacesToLAGs([br_name], "bond_65")
        except Exception as e:
            create_lag_res = False

        if create_lag_res:
            self.FailTheTest("It's possible to add more LAG than maximum (64)", abort_Test=True)



    def clearDUTStats(self):
        funcname = GetFunctionName(self.clearDUTStats)
        self.dut_active_ports.get_all_ports_stats()
        self.dut_active_ports.reset_all_ports_stats()


    def playTrafficForMACLearn(self):
        funcname = GetFunctionName(self.playTrafficForMACLearn)
        ports_list = [self._tg_port_list[0], self._tg_port_list[1]]
        self._tg.start_traffic(port_or_port_list=ports_list, blocking=False, start_packet_groups=False, wait_up=True)
        sleep(1)
        self._tg.stop_traffic(port_or_port_list=ports_list)


    def getDutPortSpeed(self, if_name):
        """
        get port speed from ethtool in Mbps
        :return:
        """
        funcname = GetFunctionName(self.getDutPortSpeed)

        cmd = "ethtool {}".format(if_name)
        buff = self.send_cmd(cmd, timeout=10)
        mbps = 0
        mbps = int(self.get_from_regex(buff, ["Speed:\s+(\d+)"], 1))
        return mbps


    def setDutPortSpeed(self, if_name, speed):
        """
        set port speed from ethtool in Mbps
        :return:
        """
        funcname = GetFunctionName(self.getDutPortSpeed)

        cmd = "ethtool -s {} autoneg off speed {} duplex full".format(if_name, speed)
        buff = self.send_cmd(cmd, timeout=10)
        return buff


    def replaceLAGMember(self):
        # self.setLinkStateInterfaces([self._lag2_members[-1]])
        # self.setLinkStateInterfaces([self._lag2_members[0]], "down")
        # LAG 1
        self.setLinkStateInterfaces([self._lag1_members[0]], "down")
        self.unslaveInterfaceFromLAG(self._lag1_members[0])
        self.unslaveInterfaceFromBridge(self._lag_1)

        self.setLinkStateInterfaces([self._lag1_members[-1]], "down")
        self.assignInterfacesToLAGs([self._lag1_members[-1]], self._lag_1)
        self.setLinkStateInterfaces([self._lag1_members[-1]])
        self.assignInterfacesToBridge([self._lag_1], "br1")

        # LAG 2
        self.setLinkStateInterfaces([self._lag2_members[0]], "down")
        self.unslaveInterfaceFromLAG(self._lag2_members[0])
        self.unslaveInterfaceFromBridge(self._lag_2)

        self.setLinkStateInterfaces([self._lag2_members[-1]], "down")
        self.assignInterfacesToLAGs([self._lag2_members[-1]], self._lag_2)
        self.setLinkStateInterfaces([self._lag2_members[-1]])
        self.assignInterfacesToBridge([self._lag_2], "br2")

    def verifyLAGThroughput(self, members_count, port_speed):
        funcname = GetFunctionName(self.verifyLAGThroughput)
        ports_list = [self._tg_port_list[0], self._tg_port_list[1]]
        self._tg.start_traffic(port_or_port_list=ports_list, blocking=False, start_packet_groups=False, wait_up=True)
        sleep(10)
        self._tg.get_all_ports_stats()
        self._tg.stop_traffic(port_or_port_list=ports_list)
        frame_size = int(list(ports_list[0].streams.items())[0][1].frame_size.value)
        port1_frame_rate = int(ports_list[0].statistics.frames_received_rate)
        port2_frame_rate = int(ports_list[1].statistics.frames_received_rate)
        total_l1_rate = (int(frame_size) + 20) * (port1_frame_rate + port2_frame_rate) * 8
        if members_count > 0:
            l1_mbps_rate_per_port = float(total_l1_rate / members_count / 1000 / 1000)
        else:
            l1_mbps_rate_per_port = 0.0
        result_msg_fail = "per port rate didn't reach the port rate + 50 Mbps - LAG members port speed is {}, and l1_mbps_rate_per_port is {}, total l1 rate is {} for {} LAG members".format(port_speed, l1_mbps_rate_per_port, total_l1_rate/1000000, members_count)
        result_msg_pass = "per port rate reached the port rate + 50 Mbps - LAG members port speed is {}, and l1_mbps_rate_per_port is {}, total l1 rate is {} for {} LAG members".format(port_speed, l1_mbps_rate_per_port, total_l1_rate/1000000, members_count)
        if members_count > 0:
            if l1_mbps_rate_per_port + 50.0 < port_speed:
                self.FailTheTest(result_msg_fail, abort_Test=False)
            else:
                self.logger.info(result_msg_pass)
        else:
            if l1_mbps_rate_per_port != 0.0:
                self.FailTheTest("All LAG members are down but rate > 0", abort_Test=False)
            else:
                self.logger.info("All LAG members are down and rate == 0")



    def playTrafficBiDiAndVerifyResult(self, loss_is_expected=False, traffic_intrrup_callback=None):
        funcname = GetFunctionName(self.playTrafficBiDiAndVerifyResult)
        ports_list = [self._tg_port_list[0], self._tg_port_list[1]]
        p1_s1 = list(self._tg_port_list[0].streams.items())[0][1]
        p2_s1 = list(self._tg_port_list[1].streams.items())[0][1]
        port_1_sip = p1_s1.packet.ipv4.source_ip.value
        port_2_sip = p2_s1.packet.ipv4.source_ip.value
        port_1_ip_src_filter = " ".join(hex(int(i))[2:].rjust(2, "0") for i in port_1_sip.split('.'))
        port_2_ip_src_filter = " ".join(hex(int(i))[2:].rjust(2, "0") for i in port_2_sip.split('.'))

        # in order not to append match terms between cases need to reset them
        self._tg_port_list[0].filter_properties.capture_filter = trafficFilter(default=True)
        self._tg_port_list[1].filter_properties.capture_filter = trafficFilter(default=True)
        self._tg_port_list[0].apply_filters()
        self._tg_port_list[1].apply_filters()
        termSA1_rx = self._tg_port_list[0].filter_properties.create_match_term(port_2_ip_src_filter, 26, '00 FF FF FF')
        termSA2_rx = self._tg_port_list[1].filter_properties.create_match_term(port_1_ip_src_filter, 26, '00 FF FF FF')
        myFilter1_rx = self._tg_port_list[0].filter_properties.capture_filter
        myFilter2_rx = self._tg_port_list[1].filter_properties.capture_filter
        myFilter1_rx.enabled = True
        myFilter2_rx.enabled = True
        myFilter1_rx.add_condition(termSA1_rx)
        myFilter2_rx.add_condition(termSA2_rx)
        self._tg_port_list[0].apply_filters()
        self._tg_port_list[1].apply_filters()

        tx_duration = float(self._testClassref.TestCaseData['tx_duration'])
        self._tg.clear_all_stats()

        self._tg.start_traffic(port_or_port_list=ports_list, blocking=False, start_packet_groups=False, wait_up=True)
        # tx_tg_port = self._tg_port_list[tx_port]
        # tx_tg_port.start_traffic(wait_up=True)
        # self.logger.info(
        #     "Sending traffic from ports {}".format([ports_list[item]._port_uri for item in ports_list]._port_uri))
        self.logger.info("Now transmitting traffic for {}".format(tx_duration))
        sleep(tx_duration)
        if traffic_intrrup_callback:
            traffic_intrrup_callback()
        # tx_tg_port.stop_traffic()
        self._tg.stop_traffic(port_or_port_list=ports_list)
        sleep(2)
        self._tg.get_all_ports_stats()

        rx_ok = True
        result_msg_fail = ""
        result_msg_pass = ""
        tolerance_percent = float(self._testClassref.TestCaseData['losses_tolerance_percent'])
        tolerance1 = int(ports_list[1].statistics.frames_sent * tolerance_percent)
        tolerance2 = int(ports_list[0].statistics.frames_sent * tolerance_percent)
        # if ports_list[0].statistics.capture_filter + tolerance1 < ports_list[1].statistics.frames_sent:
        if ports_list[0].statistics.capture_filter != ports_list[1].statistics.frames_sent:
            rx_ok = False
            "Test failed - traffic wasn't received correctly on rx port: {}\n".format(ports_list[1]._port_uri)
            result_msg_fail += "tx port {} tx_frames: {} != rx_port {} rx frames {}\n".format(ports_list[1]._port_uri, ports_list[1].statistics.frames_sent, ports_list[0]._port_uri, ports_list[0].statistics.capture_filter)
        else:
            result_msg_pass += "tx port {} tx_frames: {} == rx_port {} rx frames {}\n".format(ports_list[1]._port_uri, ports_list[1].statistics.frames_sent, ports_list[0]._port_uri, ports_list[0].statistics.capture_filter)

        # if ports_list[1].statistics.capture_filter + tolerance2 < ports_list[0].statistics.frames_sent:
        if ports_list[1].statistics.capture_filter != ports_list[0].statistics.frames_sent:
            rx_ok = False
            "Test failed - traffic wasn't received correctly on rx port: {}\n".format(ports_list[0]._port_uri)
            result_msg_fail += "tx port {} tx_frames: {} != rx_port {} rx frames {}\n".format(ports_list[0]._port_uri, ports_list[0].statistics.frames_sent, ports_list[1]._port_uri, ports_list[1].statistics.capture_filter)
        else:
            result_msg_pass += "tx port {} tx_frames: {} == rx_port {} rx frames {}\n".format(ports_list[0]._port_uri, ports_list[0].statistics.frames_sent, ports_list[1]._port_uri, ports_list[1].statistics.capture_filter)



        if not loss_is_expected:
            if not rx_ok:
                self.FailTheTest(result_msg_fail, abort_Test=False)
            else:
                self.logger.info(result_msg_pass)
        # else:
        #     if not rx_ok:
        #         result_msg_pass += "\nLosses expected and occurred:"
        #         if ports_list[1].statistics.capture_filter != ports_list[0].statistics.frames_sent:
        #                 result_msg_pass += "tx port {} tx_frames: {} != port_exp_rx {} rx frames {}\n".format(ports_list[0]._port_uri, ports_list[0].statistics.frames_sent, ports_list[1]._port_uri, ports_list[1].statistics.capture_filter)
        #         if ports_list[0].statistics.capture_filter != ports_list[1].statistics.frames_sent:
        #                 result_msg_pass += "tx port {} tx_frames: {} != port_exp_rx {} rx frames {}\n".format(ports_list[1]._port_uri, ports_list[1].statistics.frames_sent, ports_list[0]._port_uri, ports_list[0].statistics.capture_filter)
        #         self.logger.info(result_msg_pass)
        #     else:
        #         result_msg_fail += "\nLosses expected and didn't occur:"
        #         # for port_exp_rx in exp_rx_ports_list:
        #         #     if port_exp_rx.statistics.frames_received != tx_port_tx_frames:
        #         #         result_msg_fail += "tx port {} tx_frames: {} == port_exp_rx {} rx frames {}\n".format(tx_tg_port._port_uri, tx_port_tx_frames, port_exp_rx._port_uri, port_exp_rx.statistics.capture_filter)
        #         self.FailTheTest(result_msg_fail, abort_Test=False)


    def verifyDUTStats(self, lag_members_list1, tg_tx_port1, lag_members_list2, tg_tx_port2):
        funcname = GetFunctionName(self.verifyDUTStats)
        self.dut_active_ports.get_all_ports_stats()
        rx_frames1 = tg_tx_port2.statistics.capture_filter
        per_port_rx_frames1 = int(rx_frames1/len(lag_members_list1))
        balance_tolerance_percent = 0.01
        accepted_diff_in_frames = int(per_port_rx_frames1 * balance_tolerance_percent)
        fail_message = ""
        pass_message = ""
        lag_1_tx_frames = {}
        lag_1_tx_frames["total_for_lag"] = 0
        lag_2_tx_frames = {}
        lag_2_tx_frames["total_for_lag"] = 0

        total_pass = True
        for lag_member in lag_members_list1:
            sent = self.dut_active_ports.ports[lag_member].stats.unicast_frames_sent
            lag_1_tx_frames[lag_member] = sent
            lag_1_tx_frames["total_for_lag"] += sent
            if abs(sent - per_port_rx_frames1) > accepted_diff_in_frames:
                total_pass = False
                fail_message += "Lag member {} tx frames {} is out of range!!! of accepted diff in frames {} for RX port {} (should be 1/{} * {})\n".format(lag_member, sent, accepted_diff_in_frames, tg_tx_port2._port_uri, len(lag_members_list1), rx_frames1)
            else:
                pass_message += "Lag member {} tx frames {} is in range of accepted diff in frames {} for TX port {}\n".format(lag_member, sent, accepted_diff_in_frames, tg_tx_port2._port_uri)

        rx_frames2 = tg_tx_port1.statistics.capture_filter
        per_port_rx_frames2 = int(rx_frames2 / len(lag_members_list2))
        accepted_diff_in_frames = per_port_rx_frames2 * balance_tolerance_percent
        for lag_member in lag_members_list2:
            sent = self.dut_active_ports.ports[lag_member].stats.unicast_frames_sent
            lag_2_tx_frames[lag_member] = sent
            lag_2_tx_frames["total_for_lag"] += sent
            if abs(sent - per_port_rx_frames2) > accepted_diff_in_frames:
                total_pass = False
                fail_message += "Lag member {} tx frames {} is out of range!!! of accepted diff in frames {} for TX port {} (should be 1/{} * {})\n".format(lag_member, sent, accepted_diff_in_frames, tg_tx_port1._port_uri, len(lag_members_list2), rx_frames2)
            else:
                pass_message += "Lag member {} tx frames {} is in range of accepted diff in frames {} for TX port {}\n".format(lag_member, sent, accepted_diff_in_frames, tg_tx_port1._port_uri)
        self.logger.info("Lag1 tx frames per member:\n{}".format(lag_1_tx_frames))
        self.logger.info("Lag2 tx frames per member:\n{}".format(lag_2_tx_frames))

        x = PrettyTable()
        x.field_names = ["switchport", "actual tx", "actual distribution %", "expected distribution in frames",
                         "distribution diff from expected in frames", "accepted distribution in frames"]
        sum_actual_distribution = 0
        sum_expected_distribution_in_frames = 0
        sum_distribution_diff_from_expected_in_frames = 0
        for lag_member in lag_members_list1:
            x.add_row([lag_member,
                       lag_1_tx_frames[lag_member],
                       (lag_1_tx_frames[lag_member] / rx_frames1),
                       (rx_frames1 * (1/len(lag_members_list1))),
                       ((rx_frames1 * (1/len(lag_members_list1))) - lag_1_tx_frames[lag_member]), accepted_diff_in_frames])
            sum_actual_distribution += (lag_1_tx_frames[lag_member] / rx_frames1)
            sum_expected_distribution_in_frames += (rx_frames1 * (1/len(lag_members_list1)))
            sum_distribution_diff_from_expected_in_frames += ((rx_frames1 * (1/len(lag_members_list1))) - lag_1_tx_frames[lag_member])
        x.add_row(["", "", "", "", "", ""])
        x.add_row(["", lag_1_tx_frames["total_for_lag"], sum_actual_distribution, sum_expected_distribution_in_frames, sum_distribution_diff_from_expected_in_frames, ""])
        self.logger.info("LAG1 calcs")
        self.logger.info(x)

        y = PrettyTable()
        y.field_names = ["switchport", "actual tx", "actual distribution %", "expected distribution in frames",
                         "distribution diff from expected in frames", "accepted distribution in frames"]
        sum_actual_distribution = 0
        sum_expected_distribution_in_frames = 0
        sum_distribution_diff_from_expected_in_frames = 0
        for lag_member in lag_members_list2:
            y.add_row([lag_member,
                       lag_2_tx_frames[lag_member],
                       (lag_2_tx_frames[lag_member] / rx_frames2),
                       (rx_frames2 * (1 / len(lag_members_list2))),
                       ((rx_frames2 * (1 / len(lag_members_list2))) - lag_2_tx_frames[lag_member]), accepted_diff_in_frames])
            sum_actual_distribution += (lag_2_tx_frames[lag_member] / rx_frames2)
            sum_expected_distribution_in_frames += (rx_frames2 * (1 / len(lag_members_list2)))
            sum_distribution_diff_from_expected_in_frames += ((rx_frames2 * (1 / len(lag_members_list2))) - lag_2_tx_frames[lag_member])
        y.add_row(["", "", "", "", "", ""])
        y.add_row(["", lag_2_tx_frames["total_for_lag"], sum_actual_distribution, sum_expected_distribution_in_frames, sum_distribution_diff_from_expected_in_frames, ""])

        self.logger.info("LAG2 calcs")
        self.logger.info(y)

        if total_pass:
            self.logger.info(pass_message)
        else:
            self.FailTheTest(fail_message, abort_Test=False)
