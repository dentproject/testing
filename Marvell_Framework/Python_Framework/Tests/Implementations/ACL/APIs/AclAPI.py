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

from builtins import str
from collections import ChainMap
from random import choice, randint
from UnifiedTG.Unified import Port
from UnifiedTG.Unified.Stream import Stream
from UnifiedTG.Unified.TGEnums import TGEnums
from pandas import DataFrame

from CLI_GlobalFunctions.SwitchDev.CLICommands.Executer import GlobalGetterSetter
from CLI_GlobalFunctions.SwitchDev.QoS.ACLConfig import ACLConfig
from CLI_GlobalFunctions.SwitchDev.Utils import getTGRep, expectedActualTable, powerset
from PyInfraCommon.GlobalFunctions.Random import Randomize
from PyInfraCommon.GlobalFunctions.Utils.Function import GetFunctionName
from PyInfraCommon.Managers.QueryTools.Comparator import Comparator
from Tests.Implementations.CommonTestAPI import CommonTestAPI


class AclAPI(CommonTestAPI):

    def __init__(self, testClass):
        super(AclAPI, self).__init__(testClass)
        self._aclConfig = {}  # type: dict[BaseTest._TG2DutPortLink, ACLConfig]
        self._nonRxPorts = []

        # FIXME: set this value since MLNX has unexplained packet loss
        self.numOfPackets = 6000

    """""""""""""""""""""""""""""""""" PUBLIC FUNCTIONS """""""""""""""""""""""""""""""""""""""

    @property
    def aclConfig(self):
        return self._aclConfig

    def initTestParams(self, txInterfaces):
        """
        Initiate all relevant test parameters
        """
        funcname = GetFunctionName(self.initTestParams)
        self.logger.debug(funcname + "Initiate all relevant test parameters")
        for port in txInterfaces:
            self._aclConfig[port] = ACLConfig(switchDevDutInterface=port.DutDevPort)

    def configureQdisc(self, ingressBlock=None, addToCleanup=True):
        """
        Create ingress qdisc
        """
        funcname = GetFunctionName(self.configureQdisc)
        self.logger.debug(funcname + "configure ingress qdisc")
        for interface in list(self._aclConfig.values()):
            err = interface.addQdisq(ingress_block=ingressBlock)
            if err:
                self.FailTheTest('FAIL: ' + err)
            if addToCleanup:
                self.Add_Cleanup_Function_To_Stack(interface.deleteQdisc, timeout=600)

    def deleteQdisc(self):
        """
        Delete ingress qdisc
        """
        funcname = GetFunctionName(self.configureQdisc)
        self.logger.debug(funcname + "configure ingress qdisc")
        for interface in self._aclConfig.values():
            err = interface.deleteQdisc(timeout=120)
            if err:
                self.FailTheTest(f'FAIL: {interface}: {err}')

    def addTCFilterFlowers(self, portOrBlock, expectedErrMsg=False, **selectors):
        if selectors is None:
            selectors = {}
        if isinstance(portOrBlock, int):
            err = ACLConfig.addFilterSharedBlock(block=portOrBlock, **selectors)
        else:
            err = self._aclConfig[portOrBlock].addTCFilterFlower(**selectors)
        if err and not expectedErrMsg:
            self.FailTheTest('FAIL: ' + err)
        elif expectedErrMsg and not err:
            self.FailTheTest('FAIL: An error message should be returned')

    def getMatchedAces(self, port, pref, handle=None, getAces=False):
        if getAces:
            filters = self._aclConfig[port].getTCFilters()
            self.logger.debug(filters)
        return self._aclConfig[port].getMatchedRule(pref, handle)

    def setUpFixedStreamSettings(self, tgDutLinks, packetGroupSettings=False, numOfPackets=None):

        funcname = GetFunctionName(self.setUpFixedStreamSettings)
        for txPort in tgDutLinks:
            self.logger.debug(f"{funcname} Setting up fixed settings on all streams of port: {getTGRep(txPort.TGPort)}")
        if packetGroupSettings:
            self.setPacketGroupSettings(tgDutLinks)
        self.setFixedPacketBurst(tgDutLinks, numOfPackets)

    def applyStreams(self, txPorts):
        for port in txPorts:
            port.TGPort.apply_streams()

    def applyTGSettings(self, txPorts, rxPorts=None):
        if rxPorts is None:
            rxPorts = []

        self.waitUpTgPorts(txPorts + rxPorts)
        self.applyStreams(txPorts)

    def generateRandomSelectors(self):
        protocol = choice(['ip', f"0x9{randint(1, 3)}00", "0x8100", "0x88a8", None])

        # randomly select src_port or dst_port or both
        selectors = {}
        if protocol == 'ip':
            selectors = dict(ChainMap(*choice(powerset([
                {'src_ip': Randomize().IPv4()},
                {'dst_ip': Randomize().IPv4()},
                {'src_mac': Randomize().Mac()},
                {'dst_mac': Randomize().Mac()},
                {'ip_proto': choice(["tcp", "udp"])},
                {'ip_proto': choice(["tcp", "udp"]), 'src_port': randint(1, 65535)},
                {'ip_proto': choice(["tcp", "udp"]), 'dst_port': randint(1, 65535)}
            ]))))
        elif protocol == '0x8100':
            selectors = dict(ChainMap(*choice(powerset([
                {'vlan_id': randint(1, 4094)}
            ]))))

        return {'protocol': protocol, 'flower': selectors}

    def overflowTable(self, devOrBlock, incStep=1):
        if isinstance(devOrBlock, int):
            devOrBlockSelector = f"block {devOrBlock}"
        else:
            devOrBlockSelector = f"dev {devOrBlock.DutDevPort.name} ingress"
        listOfRules = []
        for _ in range(incStep + 1):
            selectors = self.generateRandomSelectors()
            protocol = f"protocol {selectors['protocol']} " if selectors['protocol'] else ''
            listOfRules.append(f"tc filter add {devOrBlockSelector} {protocol}flower "
                               f"{' '.join(list('%s %s' % x for x in selectors['flower'].items()))}"
                               f" action {choice(['pass', 'drop', 'trap'])}")

        strOfAllRules = '\n'.join(listOfRules)
        from CLI_GlobalFunctions.SwitchDev.CLICommands.Executer import GlobalGetterSetter
        err = GlobalGetterSetter().getter.execAsFile(strOfAllRules)
        if err:
            self.FailTheTest(err)

    def deleteRule(self, devOrBlock, pref, handle=None):
        if isinstance(devOrBlock, int):
            err = ACLConfig.deleteTCFilterSharedBlock(devOrBlock, pref, handle=handle)
        else:
            err = self._aclConfig[devOrBlock].deleteTCFilterFlower(pref, handle=handle)
        if err:
            self.FailTheTest('FAIL' + err)

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
            self.verifyNoBadOctets(list(self._aclConfig.keys()))
            dbg = f"FAIL: counters on {rxPort}: expected: {expected}, actual {actual}"
            self.FailTheTest(dbg)

        self.logger.debug(f"PASS: No packet loss has occurred on port {rxPort}")

    def verifyRateIsGreaterThan(self, rxPort, rate=0):
        stats = rxPort.TGPort.statistics
        c = Comparator(stats, title=getTGRep(rxPort.TGPort))
        c.GreaterThan(stats.bytes_received_rate, rate)
        status = c.Compare()
        if not status:
            self.verifyNoBadOctets(list(self._aclConfig.keys()))
            err = f"FAIL: received rate is less than {rate}"
            self.FailTheTest(err)
        self.logger.debug(f"PASS: received rate is greater than {rate}")

    def verifyRateIsEqualsTo(self, rxPort, rate=0):
        stats = rxPort.TGPort.statistics
        c = Comparator(stats, title=getTGRep(rxPort.TGPort))
        c.Equal(stats.bytes_received_rate, rate)
        status = c.Compare()
        if not status:
            self.verifyNoBadOctets(list(self._aclConfig.keys()))
            dbg = f"FAIL: rx byte rate on port {rxPort}: expected: {rate}, actual: {stats.bytes_received_rate}"
            self.FailTheTest(dbg)
        self.logger.debug("PASS: No packet leak has occurred")

    def verifyTrappedTraffic(self, port, count=10, protocol: str = None, dst_mac=None, src_mac=None, vlan_id=None,
                             dst_ip=None, src_ip=None, ip_proto=None, dst_port=None, src_port=None, timeout=20,
                             **kwargs):
        args = []
        if dst_mac:
            args.append('ether dst ' + dst_mac)
        if src_mac:
            args.append('ether host ' + src_mac)
        if protocol:
            if protocol.startswith('0x'):
                protocol = 'ether proto ' + protocol
            args.append(protocol)
        if src_ip:
            args.append('src host ' + src_ip)
        if dst_ip:
            args.append('dst host ' + dst_ip)
        if ip_proto:
            args.append(ip_proto)
        if dst_port:
            args.append(f'dst port {dst_port}')
        if src_port:
            args.append(f'src port {src_port}')
        if vlan_id:
            args.append(f'vlan {vlan_id}')
        argsString = ' and '.join(args)
        res = GlobalGetterSetter().getter.tcpdump('-c', count, '-i', port.DutDevPort.name, argsString, timeout=timeout)

        if f'{count} packets captured' not in res:
            # send '^C' since the prompt is stuck by tcmpdump
            GlobalGetterSetter().getter.execute('\x03')
            return None, 'CPU might have not trapped all packets'

        return res, None

    def verifyTCStats(self, port, pref, expectedDict, handle=1):
        stats = self._aclConfig[port].getSpecificStats(pref, handle)
        if stats:
            status = True
            for k, v in stats[pref][handle].items():
                if k not in expectedDict:
                    expectedDict[k] = v

                status &= expectedDict[k] == v
                if expectedDict[k] != v:
                    field, expected, actual = k, expectedDict[k], v

            if not status:
                actualT = DataFrame({'Field': list(stats[pref][handle].keys()), 'Actual': list(stats[pref][handle].values())})
                expectedT = DataFrame({'Field': list(expectedDict.keys()), 'Expected': list(expectedDict.values())})
                self.logger.debug('\n' + str(actualT.set_index('Field').join(expectedT.set_index('Field'))))
                self.FailTheTest(f'FAIL: field {field} - actual: {actual}, expected: {expected}')

        else:
            self.FailTheTest(f'rule with pref {pref} and handle {handle} not found')
