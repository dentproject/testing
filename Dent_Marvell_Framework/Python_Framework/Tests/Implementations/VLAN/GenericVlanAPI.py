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

import random
import math
from builtins import str, range
from collections import Counter
from itertools import chain
from UnifiedTG.Unified import Port
from UnifiedTG.Unified.TGEnums import TGEnums
from CLI_GlobalFunctions.SwitchDev.Bridge.Bridge1QConfig import Bridge1QConfig
from CLI_GlobalFunctions.SwitchDev.CLICommands.Executer import GlobalGetterSetter
from CLI_GlobalFunctions.SwitchDev.Utils import getTGRep
from PyInfraCommon.GlobalFunctions.Utils import MAC
from PyInfraCommon.GlobalFunctions.Utils.Function import GetFunctionName
from PyInfraCommon.Managers.QueryTools.Comparator import Comparator
from Tests.Implementations.CommonTestAPI import CommonTestAPI


class GenericVlanAPI(CommonTestAPI):

    def __init__(self, testClass):
        super(GenericVlanAPI, self).__init__(testClass)
        self._bridge = Bridge1QConfig()
        self._interfaceToVlanMapping = []
        self._txInterfaces = {}
        self._rxInterfaces = {}
        self._nonRxPorts = []

    @property
    def rxInterfaces(self):
        return self._rxInterfaces

    def createAndSetSoftEntityUp(self, **kwargs):
        super(GenericVlanAPI, self).createAndSetSoftEntityUp(vlan_default_pvid=0)

    """""""""""""""""""""""""""""""""" PUBLIC FUNCTIONS """""""""""""""""""""""""""""""""""""""

    def initTestParams(self, testParams=None):
        """
        Initiate all test params
        :param testParams: the test parameters
        """
        funcname = GetFunctionName(self.initTestParams)
        self.logger.debug(funcname + 'Initiate all relevant test parameters')
        self.Add_Cleanup_Function_To_Stack(GlobalGetterSetter().setter.execute)
        self._txInterfaces = dict(testParams['tx_interfaces'])
        self._interfaceToVlanMapping = [v for k, v in testParams.items() if str(k).startswith('group')]
        for k in self._txInterfaces.keys():
            packetVIDs = [str(x) for x in self._txInterfaces[k]['packet_vids'] if x != 'X']
            self._txInterfaces[k]['vlan_tested'] = packetVIDs

    def configureVlans(self, tgDutLinks):
        """
        Insert ports to VLAN according to port connection list
        :param tgDutLinks: BastTest.TGDutLinks dict
        """
        funcname = GetFunctionName(self.configureVlans)
        self.logger.debug(funcname + 'Insert ports to VLAN according to port connection list')
        for group in self._interfaceToVlanMapping:
            for interface in group['ports']:
                interfaceName = tgDutLinks[interface].DutDevPort.name
                self._bridge.addInterfaceToVlan(interfaceName, group['vid'], *group['more_settings'])

    def setRxAndNonRxPorts(self, tgDutLinks):
        """
        Maps all expected receiving ports and non-rx ports
        :param tgDutLinks: BastTest.TGDutLinks dict
        """
        Bridge1QConfig.getVlanSettings()
        vlanConf = Bridge1QConfig.interfaceVlanSettings()
        TGPorts2DutPorts = {tgDutLinks[int(tgPort)].DutDevPort.name: tgPort for tgPort in self._txInterfaces}
        for port in TGPorts2DutPorts:
            dits = self._txInterfaces[TGPorts2DutPorts[port]]
            for _ in range(dits['packet_vids'].count('X') + dits['packet_vids'].count(0)):
                try:
                    if vlanConf[port]['pvid']:
                        dits['vlan_tested'].append(vlanConf[port]['pvid'])
                except TypeError:
                    continue

        for port in self._txInterfaces:
            self._txInterfaces[port]['vlan_tested'] = Counter(self._txInterfaces[port]['vlan_tested'])

        return \
            [[int(t) for t in Bridge1QConfig.getVIDs(x) if
              int(t) in self._txInterfaces[TGPorts2DutPorts[x]]['packet_vids']
              or t == Bridge1QConfig.getPVID(x)] for x, v in vlanConf.items() if
             x in TGPorts2DutPorts][0]

    def setupStream(self, tgDutLinks, srcMac='AA:AA:AA:AA:AA:00', dstMac='ff:ff:ff:ff:ff:ff'):
        """
        :param tgDutLinks: BastTest.TGDutLinks dict
        :param srcMac: the source mac address
        :param dstMac: the destination mac address
        """
        funcname = GetFunctionName(self.setupStream)
        for txPort, txDits in self._txInterfaces.items():
            TGTxPort = tgDutLinks[int(txPort)].TGPort  # type: Port
            self.logger.debug(funcname + 'Setting up stream on: ' + getTGRep(TGTxPort))
            for vlanTested in txDits['packet_vids']:
                TGTxPort.add_stream(f'testPacketVID#{vlanTested}')
                stream = TGTxPort.streams[f'testPacketVID#{vlanTested}']
                stream.packet.mac.da.value = dstMac
                stream.packet.l2_proto = TGEnums.L2_PROTO.RAW
                stream.packet.mac.sa.value = srcMac
                stream.control.packets_per_burst = self.numOfPackets
                stream.control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM if \
                    vlanTested is txDits['packet_vids'][-1] else TGEnums.STREAM_TRANSMIT_MODE.ADVANCE_TO_NEXT_STREAM

            srcMac = srcMac[:-1] + txPort

    def applyTGSettings(self, tgDutLinks):
        """
        :param tgDutLinks: BastTest.TGDutLinks dict
        """
        for indx, port in tgDutLinks.items():
            port.TGPort.apply_filters()
            if str(indx) in self._txInterfaces:
                port.TGPort.apply_streams()

    def verifyNoTrafficOnOtherVlans(self):
        """
        Verifies no VLANs other than the VLANs for which the tx interfaces belongs to have received traffic
        """
        funcname = GetFunctionName(self.verifyNoTrafficOnOtherVlans)
        self.logger.debug(funcname + 'Verify no traffic leak')
        status = True
        for nonRxPort in self._nonRxPorts:
            status = self.verifyCountersOnPorts(nonRxPort)
            if not status:
                break
        return status, funcname

    def calculateExpectedTraffic(self, tgDutLinks):
        """
        Verifies that the whole transmitted traffic was received and no packet loss occurred nor errors
        :param tgDutLinks: BastTest.TGDutLinks dict
        """
        funcname = GetFunctionName(self.calculateExpectedTraffic)
        self.logger.debug(funcname + 'Verify received traffic on ports is as expected')
        rxPortsExpectedCounters = {v: 0 for v in set(chain(*self._rxInterfaces.values()))}
        acceptablePrecentLoss = 0.045
        for txNum, txDits in self._txInterfaces.items():
            for vlanTested in txDits['vlan_tested']:
                try:
                    for rxPort in self._rxInterfaces[str(vlanTested)]:
                        rxDutPort = tgDutLinks[int(rxPort)].DutDevPort
                        rxPvid = Bridge1QConfig.getPVID(rxDutPort)
                        isTagged = Bridge1QConfig.isTagged(rxDutPort, vlanTested)

                        if rxPvid and rxPvid == vlanTested and isTagged and 'X' in txDits['packet_vids']:
                            rxPortsExpectedCounters[rxPort] += (txDits['vlan_tested'][vlanTested] - 1) \
                                                               * self.numOfPackets + \
                                                               self.numOfPackets * (1 - acceptablePrecentLoss)
                        else:
                            rxPortsExpectedCounters[rxPort] += txDits['vlan_tested'][vlanTested] * self.numOfPackets
                except KeyError:
                    continue

        return rxPortsExpectedCounters

    def addTriggers(self, tgDutLinks, srcMac='AA:AA:AA:AA:AA:00', mask=None):
        """
        :param tgDutLinks: BastTest.TGDutLinks dict
        :param srcMac: srcMac: the source MAC of the packet
        :param mask:
        :return:
        """

        def addTriggers(vlanTested):
            for port in self._rxInterfaces[vlanTested]:
                rxPort = self._testClassref.TGDutLinks[port].TGPort
                self._addTriggers(rxPort, mac.sa.value, mask, mac.da.value)

        for port in self._nonRxPorts:
            self._addTriggers(port.TGPort, srcMac, '00 00 00 00 00 FF')

        for txPort, txDits in self._txInterfaces.items():
            txTGDutLinkPort = tgDutLinks[int(txPort)]
            for vlanTested in txDits['packet_vids']:
                mac = txTGDutLinkPort.TGPort.streams[f'testPacketVID#{vlanTested}'].packet.mac
                try:
                    addTriggers(str(vlanTested))
                except KeyError as e:
                    if e.args[0] in ('X', 0):
                        pvid = Bridge1QConfig.getPVID(txTGDutLinkPort.DutDevPort)
                        if pvid:
                            addTriggers(pvid)
            srcMac = srcMac[:-1] + txPort

    """""""""""""""""""""""""""""""""" PACKAGE FUNCTIONS """""""""""""""""""""""""""""""""""""""

    @staticmethod
    def _addTriggers(port, src, srcMask=None, dst=None):
        """

        :param port:
        :param src:
        :param srcMask:
        :param dst:
        :return:
        """
        myFilter = port.filter_properties.capture_filter
        myFilter.enabled = True
        if src not in map(lambda x: x.match_term.pattern[1:-1], port.filter_properties.capture_filter.conditions):
            termSA = port.filter_properties.create_match_term(src, mask=srcMask, offset=6)
            myFilter.add_condition(termSA)
            if dst:
                termDA = port.filter_properties.create_match_term(dst, mask=srcMask, offset=0)
                myFilter.add_condition(termDA)

    def verifyCountersOnPorts(self, rxInterface, numOfPackets=0):
        """
        Verifies if the received traffic on rxInterface is as expected
        :param rxInterface: the receiving interface
        :param numOfPackets: the expected number of packets
        """
        stats = rxInterface.TGPort.statistics
        c = Comparator(stats, title=getTGRep(rxInterface.TGPort))
        numOfPackets = int(numOfPackets)
        if (numOfPackets % self.numOfPackets) != 0:
            c.LessOrEqual(stats.capture_filter, int(self.numOfPackets *
                                                    (math.ceil(numOfPackets / self.numOfPackets) - 1)
                                                    + (self.numOfPackets * (1 + 0.04537))))
            c.GreaterOrEqual(stats.capture_filter, int(self.numOfPackets *
                                                       (math.ceil(numOfPackets / self.numOfPackets) - 1)
                                                       + (self.numOfPackets * (1 - 0.046))))
        else:
            c.Equal(stats.capture_filter, numOfPackets)

        return c.Compare()


########################################################################################################################


class GenericVlanBroadMultiCastAPI(GenericVlanAPI):

    def setRxAndNonRxPorts(self, tgDutLinks):
        """
        :param tgDutLinks: BastTest.TGDutLinks dict
        """
        receivingVlans = super(GenericVlanBroadMultiCastAPI, self).setRxAndNonRxPorts(tgDutLinks)
        for group in [x for x in self._interfaceToVlanMapping if x['vid'] in receivingVlans]:
            temp = [x for x in group['ports'] if str(x) not in self._txInterfaces]
            try:
                self._rxInterfaces[str(group['vid'])].extend(temp)
            except KeyError:
                self._rxInterfaces[str(group['vid'])] = temp

        self._nonRxPorts = [v for k, v in tgDutLinks.items() if k not in set(chain(*self._rxInterfaces.values()))]


########################################################################################################################


class GenericVlanUnicastAPI(GenericVlanAPI):

    def setupStream(self, tgDutLinks, srcMac='AA:AA:AA:AA:AA:00', dstMac='ff:ff:ff:ff:ff:ff'):
        """
        :param tgDutLinks: BastTest.TGDutLinks dict
        :param srcMac: the source MAC of the packet
        :param dstMac: the destination MAC of the packet
        """
        super(GenericVlanUnicastAPI, self).setupStream(tgDutLinks, srcMac, dstMac)
        for vlan, learningPortNum in self._rxInterfaces.items():
            learningPort = tgDutLinks[learningPortNum[-1]].TGPort
            if f'learningPacket#{vlan}' not in learningPort.streams:
                learningPort.add_stream(f'learningPacket#{vlan}')
                stream = learningPort.streams[f'learningPacket#{vlan}']
                stream.packet.mac.da.value = dstMac
                stream.packet.mac.sa.value = '00' + MAC.MacManager().GenerateRandomMac()[2:]
                stream.control.packets_per_burst = 1
                stream.control.mode = TGEnums.STREAM_TRANSMIT_MODE.ADVANCE_TO_NEXT_STREAM
                if Bridge1QConfig.isTagged(tgDutLinks[learningPortNum[-1]].DutDevPort, vlan):
                    stream.packet.add_vlan(f'VID#{vlan}')
                    stream.packet.vlans[f'VID#{vlan}'].vid.value = vlan
                    stream.packet.size = self._packetSize + 4

        def setMacDest(vlanTested):
            stream.packet.mac.da.value = \
                tgDutLinks[self._rxInterfaces[vlanTested][-1]].TGPort.streams[
                    f'learningPacket#{vlanTested}'].packet.mac.sa.value

        for txPort, txDits in self._txInterfaces.items():
            for vlanTested in txDits['packet_vids']:
                stream = tgDutLinks[int(txPort)].TGPort.streams[f'testPacketVID#{vlanTested}']
                try:
                    setMacDest(str(vlanTested))
                except KeyError as e:
                    if e.args[0] in ('X', '0'):
                        vlanTested = Bridge1QConfig.getPVID(tgDutLinks[int(txPort)].DutDevPort)
                        setMacDest(vlanTested)

    def setRxAndNonRxPorts(self, tgDutLinks):
        """
        :param tgDutLinks: BastTest.TGDutLinks dict
        """
        receivingVlans = super(GenericVlanUnicastAPI, self).setRxAndNonRxPorts(tgDutLinks)
        for group in [x for x in self._interfaceToVlanMapping if x['vid'] in receivingVlans]:
            try:
                rxPort = random.choice([x for x in group['ports'] if str(x) not in self._txInterfaces and x
                                        not in chain(*self._rxInterfaces.values())])
                self._rxInterfaces[str(group['vid'])] = [rxPort]
            except IndexError:
                pass

        self._nonRxPorts = [v for k, v in tgDutLinks.items() if k not in chain(*self._rxInterfaces.values())]

    def applyTGSettings(self, tgDutLinks):
        """
        apply all TG settings
        :param tgDutLinks: BastTest.TGDutLinks dict
        :return:
        """
        super(GenericVlanUnicastAPI, self).applyTGSettings(tgDutLinks)
        for port in chain(*self._rxInterfaces.values()):
            tgDutLinks[port].TGPort.apply_streams()

    def transmitTraffic(self, tgManager, txPorts, rxPorts=None, continues=False):
        """

        :param tgManager: BastTest.TGManger dict
        :param txPorts: BastTest.TGDutLinks dict
        :param rxPorts: the receiving ports
        :param continues: True if traffic is continues; False otherwise
        :return:
        """
        # transmit traffic for learning
        tgManager.chassis.start_traffic([port.TGPort for port in rxPorts], blocking=not continues, wait_up=True,
                                        start_packet_groups=False)

        # turn off flooding in case bridging is not working properly
        for port in [x.DutDevPort.name for x in txPorts]:
            self._bridge.setFlood(port, 'off')
        err = GlobalGetterSetter().setter.execute()
        if err:
            self.FailTheTest(err)
        super(GenericVlanUnicastAPI, self).transmitTraffic(tgManager, txPorts, rxPorts, continues)
