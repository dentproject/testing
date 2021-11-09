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

import time
from random import randint
import inspect
import re
import ipaddress
import trafficgenerator
from UnifiedTG.Unified import Stream
from UnifiedTG.Unified.TGEnums import TGEnums
from CLI_GlobalFunctions.SwitchDev.CLICommands.EntityConfig import GeneralEntityConfig
from CLI_GlobalFunctions.SwitchDev.CLICommands.Executer import GlobalGetterSetter
from CLI_GlobalFunctions.SwitchDev.IPv4.IPv4Config import IPv4Config
from CLI_GlobalFunctions.SwitchDev.Port.L1PortConfig import L1PortConfig
from CLI_GlobalFunctions.SwitchDev.Utils import getTGRep, cartesianProduct, nestedSetattr, expectedActualTable
from PyInfra.BaseTest_SV import BaseTest_SV_API
from PyInfra.BaseTest_SV.SV_Enums.SwitchDevInterface import SwitchDevDutInterface
from PyInfraCommon.BaseTest.BaseTest import BaseTest
from PyInfraCommon.GlobalFunctions.Random import Randomize
from PyInfraCommon.GlobalFunctions.Utils.Function import GetFunctionName
from PyInfraCommon.Managers.QueryTools.Comparator import Comparator


class _stat_member(object):

    def __init__(self, enable=True, return_type=int, default_val=-1):
        previous_frame = inspect.currentframe().f_back
        (filename, line_number,function_name, lines, index) = inspect.getframeinfo(previous_frame)
        self._name = lines[0].split()[0].replace("self._", "")
        self._value = 0
        self._default_val = default_val
        self._previous = 0
        self._enable = enable
        self._stats_return_type = return_type

    def _set_return_type(self,type):
        if type == int:
            self._stats_return_type = int
        elif type == str:
            self._stats_return_type = str

    def _clear(self):
        self._value = self._default_val

    @property
    def value(self):
        if self._stats_return_type == int:
            return int(float(self._value))
        elif self._stats_return_type == str:
            return str(self._value)

    @value.setter
    def value(self, v):
        if v is not 'None':
            # self._previous = self._value
            self._value = v

    @property
    def previous(self):
        return self._previous

    @previous.setter
    def previous(self, v):
        self._previous = v


class _port_stats(object):

    def __init__(self):
        self._stats_type = int
        self._good_octets_received = _stat_member()
        self._good_octets_sent = _stat_member()
        self._bad_octets_received = _stat_member()
        self._broadcast_frames_received = _stat_member()
        self._broadcast_frames_sent = _stat_member()
        self._multicast_frames_received = _stat_member()
        self._multicast_frames_sent = _stat_member()
        self._unicast_frames_received = _stat_member()
        self._unicast_frames_sent = _stat_member()

    @property
    def good_octets_received(self):
        return self._good_octets_received.value

    @good_octets_received.setter
    def good_octets_received(self, v):
        self._good_octets_received.value = v

    @property
    def good_octets_sent(self):
        return self._good_octets_sent.value

    @good_octets_sent.setter
    def good_octets_sent(self, v):
        self._good_octets_sent.value = v

    @property
    def bad_octets_received(self):
        return self._bad_octets_received.value

    @bad_octets_received.setter
    def bad_octets_received(self, v):
        self._bad_octets_received.value = v

    @property
    def broadcast_frames_received(self):
        return self._broadcast_frames_received.value

    @broadcast_frames_received.setter
    def broadcast_frames_received(self, v):
        self._broadcast_frames_received.value = v

    @property
    def broadcast_frames_sent(self):
        return self._broadcast_frames_sent.value

    @broadcast_frames_sent.setter
    def broadcast_frames_sent(self, v):
        self._broadcast_frames_sent.value = v

    @property
    def multicast_frames_received(self):
        return self._multicast_frames_received.value

    @multicast_frames_received.setter
    def multicast_frames_received(self, v):
        self._multicast_frames_received.value = v

    @property
    def multicast_frames_sent(self):
        return self._multicast_frames_sent.value

    @multicast_frames_sent.setter
    def multicast_frames_sent(self, v):
        self._multicast_frames_sent.value = v

    @property
    def unicast_frames_received(self):
        return self._unicast_frames_received.value

    @unicast_frames_received.setter
    def unicast_frames_received(self, v):
        self._unicast_frames_received.value = v

    @property
    def unicast_frames_sent(self):
        return self._unicast_frames_sent.value

    @unicast_frames_sent.setter
    def unicast_frames_sent(self, v):
        self._unicast_frames_sent.value = v

    def __str__(self):
        temp_str = ""
        allClassMembers = inspect.getmembers(self)
        for memberType, memberName in allClassMembers:
            if (str(memberType)[0] == "_" and str(memberType)[1] != "_" and str(memberType) != "_stats_type" and not inspect.ismethod(memberName)):
                temp_str += "\n{}:{}".format(memberName._name, memberName.value)
        return temp_str

    def _reset_stats(self, stat_type=str):
        allClassMembers = inspect.getmembers(self)
        for memberType, memberName in allClassMembers:
            if (str(memberType)[0] == "_" and str(memberType)[1] != "_" and str(memberType) != "_stats_type" and not inspect.ismethod(memberName)):
                memberName._clear()


class _dut_port(object):

    def __init__(self, name):
        self._get_stats_cmd = "ethtool -S {}".format(name)
        self.port_name = name
        self.stats = _port_stats()
        # self._get_port_stats()

    def get_stats(self, buff):
        self._get_port_stats(buff)

    def _get_port_stats(self, buff):
        # stats = IxePortsStats(self._port_driver_obj.session)
        self.stats.bad_octets_received = int(self.get_from_regex(buff, ["bad_octets_received:\s(\d+)"], 1)) - self.stats._bad_octets_received.previous
        self.stats.good_octets_received = int(self.get_from_regex(buff, ["good_octets_received:\s(\d+)"], 1)) - self.stats._good_octets_received.previous
        self.stats.good_octets_sent = int(self.get_from_regex(buff, ["good_octets_sent:\s(\d+)"], 1)) - self.stats._good_octets_sent.previous
        self.stats.broadcast_frames_received = int(self.get_from_regex(buff, ["broadcast_frames_received:\s(\d+)"], 1)) - self.stats._broadcast_frames_received.previous
        self.stats.broadcast_frames_sent = int(self.get_from_regex(buff, ["broadcast_frames_sent:\s(\d+)"], 1)) - self.stats._broadcast_frames_sent.previous
        self.stats.multicast_frames_received = int(self.get_from_regex(buff, ["multicast_frames_received:\s(\d+)"], 1)) - self.stats._multicast_frames_received.previous
        self.stats.multicast_frames_sent = int(self.get_from_regex(buff, ["multicast_frames_sent:\s(\d+)"], 1)) - self.stats._multicast_frames_sent.previous
        self.stats.unicast_frames_received = int(self.get_from_regex(buff, ["unicast_frames_received:\s(\d+)"], 1)) - self.stats._unicast_frames_received.previous
        self.stats.unicast_frames_sent = int(self.get_from_regex(buff, ["unicast_frames_sent:\s(\d+)"], 1)) - self.stats._unicast_frames_sent.previous

    def reset_port_stats(self, buff):
        self.stats._bad_octets_received.previous = int(self.get_from_regex(buff, ["bad_octets_received:\s(\d+)"], 1))
        self.stats._good_octets_received.previous = int(self.get_from_regex(buff, ["good_octets_received:\s(\d+)"], 1))
        self.stats._good_octets_sent.previous = int(self.get_from_regex(buff, ["good_octets_sent:\s(\d+)"], 1))
        self.stats._broadcast_frames_received.previous = int(self.get_from_regex(buff, ["broadcast_frames_received:\s(\d+)"], 1))
        self.stats._broadcast_frames_sent.previous = int(self.get_from_regex(buff, ["broadcast_frames_sent:\s(\d+)"], 1))
        self.stats._multicast_frames_received.previous = int(self.get_from_regex(buff, ["multicast_frames_received:\s(\d+)"], 1))
        self.stats._multicast_frames_sent.previous = int(self.get_from_regex(buff, ["multicast_frames_sent:\s(\d+)"], 1))
        self.stats._unicast_frames_received.previous = int(self.get_from_regex(buff, ["unicast_frames_received:\s(\d+)"], 1))
        self.stats._unicast_frames_sent.previous = int(self.get_from_regex(buff, ["unicast_frames_sent:\s(\d+)"], 1))

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



class _dut_ports(object):

    def __init__(self, ports):
        self.ports = {}
        self._chan = None
        for port in ports:
            self.ports[port] = _dut_port(port)

    def get_all_ports_stats(self):
        for port in self.ports.keys():
            buff = self.send_cmd(self.ports[port]._get_stats_cmd)
            self.ports[port].get_stats(buff)

    def reset_all_ports_stats(self):
        for port in self.ports.keys():
            buff = self.send_cmd(self.ports[port]._get_stats_cmd)
            self.ports[port].reset_port_stats(buff)

    def set_active_chan(self, chan):
        self.chan = chan

    def send_cmd(self, cmd="", timeout=30, exception_msg=None):
        try:
            res = self.chan.SendCommandAndWaitForPattern(cmd, timeOutSeconds=timeout)
            if res:
                return self.chan.lastBufferTillPrompt
            else:
                msg = "Can't send cmd:\n{}".format(res)
                if exception_msg:
                    msg = exception_msg
                raise Exception("{}\n{}".format(msg, res))
        except Exception as e:
            raise Exception("Can't send_cmd:\n{}".format(e))


class CommonTestAPI(BaseTest_SV_API):

    _portBadOctetsDb = {} # type: dict

    def __init__(self, testClassref):
        super(CommonTestAPI, self).__init__(testClassref)
        self.numOfPackets = 1000000
        self._packetSize = 64

    def verifyNoError(self, output, otherDut=False):
        if output:
            if otherDut:
                executer = GlobalGetterSetter().getterOtherDut
            else:
                executer = GlobalGetterSetter().getter
            retCode = executer.execute("echo $?")
            if retCode != '0':
                lastCommandAndErr = executer.execute("!-2")
                self.FailTheTest(f"FAIL: {lastCommandAndErr}")

    def waitUpTgPorts(self, ports):
        """
        Wait until TG ports operstate is up. Fails the test if one of the ports is not up before timeout.
        :param ports: the TG ports to verify operstate is   up
        """
        for port in ports:
            try:
                port.TGPort.wait_link_up()
            except trafficgenerator.tgn_utils.TgnError:
                self.FailTheTest(f'FAIL: Link state of port {getTGRep(port.TGPort)} is down')

    def pollTillLinkUp(self, port, timeout=60):
        cmd = f"bash -c 'for i in {{1..{timeout}}}; do x=$(ip -o link show {port} | grep -Eo \"state\s\w+\" | tr -d \"state \");" \
                      f" if [ $x == \"UP\" ]; then break; elif [ $i -eq {timeout} ]; then exit 1; fi; sleep 1; done'"
        GlobalGetterSetter().getter.execute(cmd, timeout=timeout*5)
        retCode = GlobalGetterSetter().getter.execute("echo $?")
        if retCode != '0':
            self.FailTheTest(f"FAIL: took more than {timeout} for port {port} to be up")

    @classmethod
    def doAllPortsExist(cls, totalPorts: int, timeout=15):
        """
        Poll till all ports are mapped of till timeout
        :param totalPorts: the total number of ports in board
        :param timeout: timeout the polling
        :return: True if all ports appear in board within <timeout> seconds; False otherwise.
        """
        import time
        while True:  # since Python doesn't have "do while loops"
            time.sleep(1)
            timeout -= 1
            numOfPorts = L1PortConfig.getNumberOfPorts()
            if numOfPorts.isdigit() and int(numOfPorts) == totalPorts:  # if all ports exist
                return True
            if not timeout:  # if timeout == 0
                return False

    def enslavePortsToSoftLink(self, tgDutLinks, softEntity=None):
        """
        Enslaves ports to the bridge entity
        """
        funcname = GetFunctionName(self.enslavePortsToSoftLink)
        self.logger.debug(funcname + 'set enslaved interfaces')
        if softEntity is None:
            softEntity = self._bridge
        tgDutLinksList = self._getListByInstance(tgDutLinks)
        if tgDutLinksList:
            self.verifyNoError(softEntity.setEnslavedInterfaces(*tgDutLinksList))
        else:
            err = f"Cannot pass an object of type {type(tgDutLinks[0])} to method setEnslavedInterfaces"
            self.FailTheTest('FAIL:' + err)

    def setLinkStateOnInterfaces(self, portsList=None, cleanupConfig=True, state='up', otherDut=False):
        """
        Sets link up on ports
        :param: portsList: List of ports to set link up on
        :param: cleanupConfig: True if to clean up configuration at the end of the test; False otherwise
        """
        funcname = GetFunctionName(self.setLinkStateOnInterfaces)
        self.logger.debug(funcname + 'set link up on ports')
        if portsList and not isinstance(list(portsList)[0], GeneralEntityConfig):
            portsList = [GeneralEntityConfig(port, otherDut) for port in self._getListByInstance(portsList)]
        for portConfig in portsList:
            self.verifyNoError(portConfig.setState(state))
            if cleanupConfig and state == 'up':
                self.Add_Cleanup_Function_To_Stack(portConfig.setState, 'down')

    def createAndSetSoftEntityUp(self, cleanupConfig=True, softEntity=None, **kwargs):
        """
        Creates bridge entity and sets link up on it
        :param: cleanupConfig: True if to clean up configuration at the end of the test; False otherwise
        """
        funcname = GetFunctionName(self.createAndSetSoftEntityUp)
        self.logger.debug(funcname + 'set link up on bridge entity')
        if softEntity is None:
            softEntity = self._bridge
        self.verifyNoError(softEntity.createL2Entity(**kwargs))
        if cleanupConfig:
            self.Add_Cleanup_Function_To_Stack(softEntity.deleteEntity)
        self.verifyNoError(softEntity.setState('up'))

    def configureIPv4Forwarding(self):
        msg = IPv4Config.setIpv4Forwarding(str(1))
        if not msg or msg != 'net.ipv4.ip_forward = 1':
            self.FailTheTest('Error: IP forwarding was not set')
        self.Add_Cleanup_Function_To_Stack(IPv4Config.setIpv4Forwarding, '0')

    def configureIPv4addr(self, dev, ip, mask=24, otherDut=False):
        if isinstance(dev, BaseTest._TG2DutPortLink):
            ipv4Config = IPv4Config(dev.DutDevPort, otherDutChannel=otherDut)
        elif isinstance(dev, SwitchDevDutInterface):
            ipv4Config = IPv4Config(dev, otherDutChannel=otherDut)
        self.verifyNoError(ipv4Config.setIP(ip, mask), otherDut=otherDut)
        self.Add_Cleanup_Function_To_Stack(ipv4Config.delIP, ip, mask)

    def configureIPv4Route(self, network, via, mask=randint(16, 32), otherDut=False):
        net = ipaddress.ip_network('{}/{}'.format(network, mask), strict=False)
        err = IPv4Config.setRoute(str(net.network_address), mask, via, otherDut=otherDut)
        if err:
            self.FailTheTest(err)
        self.Add_Cleanup_Function_To_Stack(IPv4Config.delRoute, str(net.network_address), mask, via, otherDut=otherDut)
        return net

    def addIPv4ProtocolInterface(self, port, srcIP, gateway, macAddress, mask=24):

        funcname = GetFunctionName(self.addIPv4ProtocolInterface)
        self.logger.debug(funcname + f"Setting up IPv4 protocol interface on port {getTGRep(port.TGPort)}")
        tgPort = port.TGPort
        tgPort.protocol_managment.enable_ARP = True
        portIntKey = tgPort.protocol_managment.protocol_interfaces.add_interface()
        portInt = tgPort.protocol_managment.protocol_interfaces.interfaces[portIntKey]
        portInt.enable = True
        portInt.mac_addr = macAddress
        portInt.description = str(port)
        portInt.ipv4.mask = mask
        portInt.ipv4.address = srcIP
        portInt.ipv4.gateway = gateway
        tgPort.protocol_managment.protocol_interfaces.auto_arp = True
        return portIntKey

    def verifyRateIsAsExpected(self, rxInterface, rate=0):
        """
        Verifies if the rate of the rx-port is as expected (~= "rate" )
        :param rxInterface: the receiving interface (e.g., port, bridge, bond...)
        :param rate: the expected rate.
        :return:
        """
        funcname = GetFunctionName(self.verifyRateIsAsExpected)
        self.logger.debug(funcname + 'Verify rate matches the configuration')
        stats = rxInterface.TGPort.statistics

        c = Comparator(stats, title=getTGRep(rxInterface.TGPort))
        c.GreaterThan(stats.frames_received_rate, rate - 20)
        c.LessOrEqual(stats.frames_received_rate, rate + 20)
        status = c.Compare()
        if not status:
            msg = 'FAIL: there may be a packet loss' if rate != 0 else 'FAIL: there may be a packet leak'
            self.FailTheTest(msg)
        else:
            self.logger.debug('PASS: receiving rate is as expected')

    def verifyRateIsGreaterThan(self, rxPort, rate=0):
        """
        Verify rxPort receiving rate is greater than rate
        :param rxPort:
        :param rate:
        :return:
        """

        stats = rxPort.TGPort.statistics
        c = Comparator(stats, title=getTGRep(rxPort.TGPort))
        c.GreaterThan(stats.bytes_received_rate, rate)
        status = c.Compare()
        if not status:
            err = f"FAIL: received rate is less than {rate}"
            self.FailTheTest(err)
        self.logger.debug(f"PASS: received rate is greater than {rate}")

    def transmitTraffic(self, tgManager, txPorts, rxPorts=None, continues:bool=False, packetGroups=False, delayTime=0,
                        transmitDuration:int=0):
        """
        Start traffic on tx ports
        :param rxPorts: the RX ports
        :param txPorts: the TX ports
        :param delayTime: The delay time before transmitting traffic (used for slow ports)
        :param packetGroups: True if packet group receiving mode is used; False if not.
        :param tgManager: the the TGManager of the test
        :type: tgManager: BaseTest._TGManager
        :param continues: if the stream control mode is continues
        :param transmitDuration: the transmission duration in seconds if traffic is continues (continues == True)
        """
        funcname = GetFunctionName(self.transmitTraffic)

        st = ""
        txTgPorts = list(map(lambda x: x.TGPort, txPorts))

        if rxPorts:

            # just some log print which prints
            for indx, row in cartesianProduct('Tx Port', 'Rx Port', txTgPorts, rxPorts).iterrows():
                if row['Tx Port'] != row['Rx Port'].TGPort:
                    st += f"{getTGRep(row['Tx Port'])} ----------> {getTGRep(row['Rx Port'].TGPort)}\n"

            self.waitUpTgPorts(rxPorts)

            if packetGroups: # configure packet groups mode if packetGroups == True
                for interface in rxPorts:
                    interface.TGPort.receive_mode.capture = False
                    interface.TGPort.receive_mode.wide_packet_group = True
                    interface.TGPort.receive_mode.automatic_signature.enabled = True
                    interface.TGPort.apply()
        else:
            # if rxPorts is None, print sending from TG port ----> DUT port
            for port in txPorts:
                st += f"{getTGRep(port.TGPort)} ----------> {port.DutDevPort.name}\n"

        if delayTime:
            self.logger.debug(f'wait {delayTime} seconds...')
            time.sleep(delayTime)

        self.logger.debug(f'{funcname}Transmitting traffic:\n{st}')
        tgManager.chassis.start_traffic(txTgPorts, blocking=not continues, wait_up=True, start_packet_groups=packetGroups)
        if continues and transmitDuration:
            self.logger.debug(f'{funcname}Transmitting traffic for {transmitDuration} time...')
            time.sleep(transmitDuration)
            tgManager.chassis.stop_traffic()

    def bridgedStream(self, port, protocol=None, dst_mac=None, src_mac=None, vlan_id=None, streamName: str = None,
                      **kwargs):
        """
        Create a L2 stream.
        Usage example:

                bridgedStream( port=self.TGDutLinks[1],
                               src_mac='00:00:00:00:00:01',
                               dst_mac='ff:ff:ff:ff:ff:ff',
                               **{
                                  'packet.mac.sa.mode': TGEnums.MODIFIER_MAC_MODE.INCREMENT,
                                  'packet.mac.sa.count': 15000,
                                  'rate.mode': TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND,
                                  'rate.pps_value': 3000
                                }
                             )

        :param port: the port to create the stream on
        :type port: BaseTest._TG2DutPortLink
        :param protocol: the ethertype of the packet(optional)
        :param dst_mac:  the destination MAC of the packet (optional)
        :param src_mac:  the source MAC of the packet (optional)
        :param vlan_id: the VID of the packet (optional)
        :param kwargs: additional stream attributes settings (optional).
                For example:
                    'packet.mac.sa.count': 15000
        :return:
        """
        if not streamName:
            streamName = f'test#{len(list(port.TGPort.streams.keys())) + 1}'
        port.TGPort.add_stream(streamName)
        stream = port.TGPort.streams[streamName]

        if protocol:
            stream.packet.ethertype = protocol
        if dst_mac:
            stream.packet.mac.da.value = dst_mac
        if src_mac:
            stream.packet.mac.sa.value = src_mac
        if vlan_id is not None:
            stream.packet.add_vlan('VID#{}'.format(vlan_id))
            stream.packet.vlans['VID#{}'.format(vlan_id)].vid.value = vlan_id
            if 'vid.mode' in kwargs:
                stream.packet.vlans['VID#{}'.format(vlan_id)].vid.mode = kwargs['vid.mode']

        if kwargs:
            self._addMoreStreamSettings({port: {streamName: kwargs}})

        self.logger.debug(stream)
        return stream

    def ipv4Stream(self, port, portIntKey=None, src_ip=None, dst_ip=None, dst_port=None, src_port=None, ip_proto=None,
                   streamName: str = None, dst_mac=None, src_mac=None, **kwargs):
        """
        Create L3 stream.
        Usage example:
                 ipv4Stream(self.TGDutLinks[1],
                            portInterfaceKey,
                            src_port="1.1.1.1",
                            ip_proto='tcp',
                            **{
                              'packet.ipv4.destination_ip.mode': TGEnums.MODIFIER_IPV4_ADDRESS_MODE.FIXED,
                              'packet.destination_ip.count': 150,
                              'rate.mode': TGEnums.STREAM_RATE_MODE.UTILIZATION
                               }
                            )

        :param port: the port to create the stream on
        :type port: BaseTest._TG2DutPortLink
        :param portIntKey: a key value representing the port interface.
                            This is actually the output of the function
                            port.TGPort.protocol_managment.protocol_interfaces.add_interface()
        :param dst_ip: the destination IP of the packet (optional)
        :param dst_port: a L4 destination port number (optional)
        :param src_port: a L4 source port number (optional)
        :param ip_proto: the L4 Layer protocol (possible options: tcp/udp)
        :param kwargs: additional stream attributes settings (optional).
                       For example:
                         'packet.mac.sa.count': 15000
        :return:
        """
        if not streamName:
            streamName = f'test#{len(list(port.TGPort.streams.keys())) + 1}'
        port.TGPort.add_stream(streamName)
        stream = port.TGPort.streams[streamName]
        stream.packet.l3_proto = TGEnums.L3_PROTO.IPV4
        if portIntKey:
            stream.source_interface.enabled = True
            stream.source_interface.description_key = portIntKey
        if src_ip:
            stream.packet.ipv4.source_ip.value = src_ip
        if dst_ip:
            stream.packet.ipv4.destination_ip.value = dst_ip
        if ip_proto:
            stream.packet.l4_proto = TGEnums.L4_PROTO.TCP if ip_proto == 'tcp' else TGEnums.L4_PROTO.UDP
        if dst_port:
            nestedSetattr(stream, f'packet.{ip_proto}.destination_port.value', dst_port)
        if src_port:
            nestedSetattr(stream, f'packet.{ip_proto}.source_port.value', src_port)
        if dst_mac:
            stream.packet.mac.da.value = dst_mac
        if src_mac:
            stream.packet.mac.sa.value = src_mac
        if kwargs:
            self._addMoreStreamSettings({port: {streamName: kwargs}})

        self.logger.debug(stream)
        return stream

    def arpStream(self, port, srcIp, targetIp, src_mac=Randomize().Mac(mask="CC:XX:XX:XX:XX:XX"), incHw=1, incIp=1,
                  utilization=5):
        return self.bridgedStream(port, src_mac=src_mac, dst_mac="FF:FF:FF:FF:FF:FF", **{
            'packet.l3_proto': TGEnums.L3_PROTO.ARP,
            'packet.arp.operation': TGEnums.ARP_OPERATION.ARP_REQUEST,
            'packet.arp.sender_hw.value': src_mac,
            'packet.arp.sender_hw.mode': TGEnums.MODIFIER_ARP_MODE.INCREMENT if incHw > 1 else TGEnums.MODIFIER_ARP_MODE.FIXED,
            'packet.arp.sender_hw.count': incHw,
            'packet.arp.sender_ip.mode': TGEnums.MODIFIER_ARP_MODE.INCREMENT if incIp > 1 else TGEnums.MODIFIER_ARP_MODE.FIXED,
            'packet.arp.sender_ip.value': srcIp,
            'packet.arp.sender_ip.count': incIp,
            'packet.arp.target_hw.value': "FF:FF:FF:FF:FF:FF",
            'packet.arp.target_ip.value': targetIp,
            'rate.utilization_value': utilization})

    def _addMoreStreamSettings(self, streamDits: dict):
        """
        Private method to dynamically set additional stream attributes.
        Usage examples:
                self.__addMoreStreamSettings(
                                                {port:
                                                    {'test':
                                                            **{
                                                              'packet.mac.sa.mode': TGEnums.MODIFIER_MAC_MODE.INCREMENT,
                                                              'packet.mac.sa.count': 15000,
                                                              'rate.mode': TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND,
                                                              'rate.pps_value': 3000,
                                                            }
                                                    }
                                                }
                                            )
                In this example, the function will set the following:
                  port.TGPort.streams['test'].packet.mac.sa.mode =  TGEnums.MODIFIER_MAC_MODE.INCREMENT
                  port.TGPort.streams['test'].packet.mac.sa.count = 15000
                  port.TGPort.streams['test'].rate.mode = TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND
                  port.TGPort.streams['test'].rate.pps_value = 3000

                if a stream named 'test' is not found in port.TGPort.streams, a new stream called 'test'
                will be created on port.TGPort

        :param streamDits:
        :return:
        """

        for txPort, dits in streamDits.items():
            self.logger.debug(f'Setting up more settings on stream: {txPort.TGPort}')
            for streamName, settings in dits.items():
                if streamName in txPort.TGPort.streams:
                    stream = txPort.TGPort.streams[streamName]
                else:
                    txPort.TGPort.add_stream(streamName)
                    stream = txPort.TGPort.streams[streamName]
                for k, v in settings.items():
                    nestedSetattr(stream, k, v)

    def setPacketGroupSettings(self, tgDutLinks):
        for txPort in tgDutLinks:
            txPort.TGPort.properties.transmit_mode = TGEnums.PORT_PROPERTIES_TRANSMIT_MODES.MANUAL_BASED
            streams = txPort.TGPort.streams.values()  # type: Port
            for i, stream in enumerate(streams):
                stream.frame_size.value = 100
                stream.instrumentation.automatic_enabled = True
                stream.instrumentation.sequence_checking_enabled = True
                stream.instrumentation.packet_group.enable_group_id = True
                stream.instrumentation.packet_group.group_id = i

    def setFixedPacketBurst(self, tgDutLinks, numOfPackets=None):
        for txPort in tgDutLinks:
            streams = txPort.TGPort.streams.values()  # type: Port
            for i, stream in enumerate(streams):
                stream.control.packets_per_burst = self.numOfPackets if not numOfPackets else numOfPackets
                stream.control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM if stream is list(streams)[
                    -1] else TGEnums.STREAM_TRANSMIT_MODE.ADVANCE_TO_NEXT_STREAM


    def verifyCountersOnPorts(self, rxPort, expected=None, stream: Stream = None):
        """

        :param rxPort:
        :param expected:
        :param stream:
        :return:
        """
        expected = self.numOfPackets if expected is None else expected
        actual = stream.statistics.rx_ports[rxPort.TGPort._port_name].total_frames
        status, table = expectedActualTable(title=f'Advance RX stats of {getTGRep(rxPort.TGPort)}',
                                            actual=actual, expected=expected,
                                            StreamName=stream._name)

        if not status:
            self.logger.debug('\n' + table)
            dbg = f"FAIL: counters on {rxPort}: expected: {expected}, actual {actual}"
            self.FailTheTest(dbg)

        self.logger.debug(f"PASS: No packet loss has occurred on port {rxPort}")


    def verifyNoBadOctets(self, portList):
        """
        Verify there are no bad octets for each port in portList
        :param portList:
        :return:
        """
        from PyInfra.BaseTest_SV.SV_Enums.SwitchDevInterface import SwitchDevDutInterface
        if not isinstance(portList[0], L1PortConfig) and isinstance(portList[0], GeneralEntityConfig):
            portList = [L1PortConfig(port.switchDevInterface) for port in portList]
        elif isinstance(portList[0], SwitchDevDutInterface):
            portList = [L1PortConfig(port) for port in portList]
        elif isinstance(portList[0], BaseTest._TG2DutPortLink):
            portList = [L1PortConfig(port.DutDevPort) for port in portList]
        L1PortConfig.getEthtoolStats(portList)
        for port in portList:
            if port.ethtoolStats.bad_octets_received > 0:
                if self._portBadOctetsDb.get(port.switchdevInterface.name) is None:
                    self._portBadOctetsDb[port.switchdevInterface.name] = port.ethtoolStats.bad_octets_received
                    portStats = port.ethtoolStats.bad_octets_received
                else:
                    portStats = port.ethtoolStats.bad_octets_received - self._portBadOctetsDb[port.switchdevInterface.name]
                if portStats:
                    self.FailTheTest(
                        f'FAIL: {portStats} bad octets received on port {port}', abort_Test=False)
            elif self._portBadOctetsDb.get(port.switchdevInterface.name) is not None:
                del self._portBadOctetsDb[port.switchdevInterface.name]



    def _getListByInstance(self, interfacesList):
        interfacesList = list(interfacesList)
        if isinstance(interfacesList[0], GeneralEntityConfig):
            return [port.switchdevInterface for port in interfacesList]
        elif isinstance(interfacesList[0], SwitchDevDutInterface):
            return interfacesList
        elif isinstance(interfacesList[0], BaseTest._TG2DutPortLink):
            return [port.DutDevPort for port in interfacesList]
        elif isinstance(interfacesList[0], str):
            return [SwitchDevDutInterface(port) for port in interfacesList]
