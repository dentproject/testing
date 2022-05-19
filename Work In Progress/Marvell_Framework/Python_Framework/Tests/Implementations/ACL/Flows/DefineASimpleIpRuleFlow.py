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

from PyInfra.BaseTest_SV.BaseTest_SD import BaseTest_SD
from Tests.Implementations.ACL.APIs.RoutedAclAPI import RoutedAclAPI


class DefineASimpleIpRuleFlow(BaseTest_SD):

    def __init__(self):
        super(DefineASimpleIpRuleFlow, self).__init__(SuiteName="ACL")
        self.APIs = RoutedAclAPI(self)
        self.TestSteps.TestDescription.test_author = "Maya Peretz"
        self.TestSteps.TestDescription.test_case_reference = "1.2.3"
        self.TestSteps.TestDescription.test_purpose = \
            """This test comes to verify:
            * Simple pass IPv4 acl functionality
            """
        # define all tests steps in this area
        ##################### Test Steps and Description ##############################################################
        self.TestSteps.Step[1] = "Initiate test params"
        self.TestSteps.Step[2] = "Set link up on interfaces"
        self.TestSteps.Step[3] = "Set IP forwarding = 1"
        self.TestSteps.Step[4] = "Configure default gateway 1.1.1.1 on one port and 2.2.2.2 on second port\n" \
                                 "and configure routing of 10.1.1.0 via 2.2.2.3"
        self.TestSteps.Step[5] = "Set up host 1.1.1.2 on first TG port and host 2.2.2.3 on second TG port.\n" \
                                 "Set up streams on first TG port:\n" \
                                 "source ip = 1.1.1.2, destination ip = 10.1.1.1\n" \
                                 "source ip = 1.1.1.2, destination ip = 2.2.2.3\n"
        self.TestSteps.Step[6] = "Create ingress qdisc"
        self.TestSteps.Step[7] = "Configure the following rule\n" \
                                 "drop all\n" \
                                 "pass src_ip 1.1.1.2 dst_ip 10.1.1.1"
        self.TestSteps.Step[8] = "Send Traffic from each of the transmitting interfaces according to the test case"
        self.TestSteps.Step[9] = "Verify no packet loss nor packet leak occurred and all transmitted traffic received"

    def TestProcedure(self):
        action = 'drop' if isinstance(self, SimpleDropIPv4RuleFlow) else 'pass'

        tg1SrcIp = '1.1.1.2'
        tg2SrcIp = '2.2.2.3'
        ruleMatchedDstIp = '10.1.1.1'
        tg1DefaultGW = '1.1.1.1'
        tg2DefaultGW = '2.2.2.2'

        # -------------------------------------------------------------------------------------------------------------
        # STEP 1 - Init test params
        self.TestSteps.RunStep(1)
        self.APIs.initTestParams(txInterfaces=[self.TGDutLinks[1]])

        # -------------------------------------------------------------------------------------------------------------
        # STEP 2 - Set link up on ports
        self.TestSteps.RunStep(2)
        self.APIs.setLinkStateOnInterfaces([self.TGDutLinks[1], self.TGDutLinks[2]])

        # -------------------------------------------------------------------------------------------------------------
        # STEP 3 - Enable IPv4 forwarding
        self.TestSteps.RunStep(3)
        self.APIs.configureIPv4Forwarding()

        # -------------------------------------------------------------------------------------------------------------
        # STEP 4 - Configure ip address 1.1.1.1 on first TGDutLink port and 2.2.2.2 on second TGDutLink port
        #          and configure route 10.1.1.0/24 via 2.2.2.3
        self.TestSteps.RunStep(4)
        self.APIs.configureIPv4addr(self.TGDutLinks[1], tg1DefaultGW)
        self.APIs.configureIPv4addr(self.TGDutLinks[2], tg2DefaultGW)
        self.APIs.configureIPv4Route('10.1.1.0', tg2SrcIp, 24)

        # -------------------------------------------------------------------------------------------------------------
        # STEP 5 - Configure hosts on Ixia ports and create rule-unmatched streams (one unmatched stream for each selector)
        self.TestSteps.RunStep(5)
        # FIXME: need to insert it into "addIPv4ProtocolInterface" after Oleg will fix the issue with it
        self.TGDutLinks[1].TGPort.enable_protocol_managment = True
        self.TGDutLinks[2].TGPort.enable_protocol_managment = True
        portIntKey = self.APIs.addIPv4ProtocolInterface(self.TGDutLinks[1], tg1SrcIp, tg1DefaultGW, "AA:00:00:00:00:01")
        self.APIs.addIPv4ProtocolInterface(self.TGDutLinks[2], tg2SrcIp, tg2DefaultGW, "AA:00:00:00:00:02")
        # matched acl stream
        matchedStream = self.APIs.ipv4Stream(self.TGDutLinks[1], portIntKey, dst_ip=ruleMatchedDstIp)
        # unmatched acl stream
        unmatchedStream = self.APIs.ipv4Stream(self.TGDutLinks[1], portIntKey, dst_ip=tg2SrcIp)
        self.APIs.setUpFixedStreamSettings([self.TGDutLinks[1]], packetGroupSettings=True)
        self.APIs.applyTGSettings([self.TGDutLinks[1]], [self.TGDutLinks[2]])

        # -------------------------------------------------------------------------------------------------------------
        # STEP 6 - Configure ingress qdisc
        self.TestSteps.RunStep(6)
        self.APIs.configureQdisc()

        # -------------------------------------------------------------------------------------------------------------
        # STEP 7 - set up a rule with src_ip and dst_ip selectors
        self.TestSteps.RunStep(7)
        if not isinstance(self, SimpleDropIPv4RuleFlow):
            self.APIs.addTCFilterFlowers(self.TGDutLinks[1], action='drop')
        self.APIs.addTCFilterFlowers(self.TGDutLinks[1],
                                     protocol='ip',
                                     src_ip=tg1SrcIp,
                                     dst_ip=ruleMatchedDstIp,
                                     action=action)

        # -------------------------------------------------------------------------------------------------------------
        # STEP 8 - Transmit traffic TG1 --> TG2
        self.TestSteps.RunStep(8)
        self.TGManager.chassis.clear_all_stats()
        self.TGDutLinks[1].TGPort.protocol_managment.arp_table.transmit()
        self.APIs.transmitTraffic(self.TGManager, [self.TGDutLinks[1]], [self.TGDutLinks[2]], packetGroups=True, delayTime=15)
        # -------------------------------------------------------------------------------------------------------------
        # STEP 9 - Verify "pass" traffic was forwarded and "drop" was dropped
        self.TestSteps.RunStep(9)
        self.TGManager.chassis.get_advanced_stats(['totalFrames'])
        passStream = matchedStream if action == 'pass' else unmatchedStream
        dropStream = matchedStream if action != 'pass' else unmatchedStream
        self.APIs.verifyCountersOnPorts(self.TGDutLinks[2], stream=passStream)
        self.APIs.verifyCountersOnPorts(self.TGDutLinks[2], expected=-1, stream=dropStream)


class SimpleDropIPv4RuleFlow(DefineASimpleIpRuleFlow):

    def __init__(self):
        super(SimpleDropIPv4RuleFlow, self).__init__()
        self.TestSteps.TestDescription.test_purpose = \
            """This test comes to verify:
            * Simple pass IPv4 acl functionality
            """
        self.TestSteps.Step[6] = "Configure the following ACL/s:\n" \
                                 "drop src_ip 1.1.1.2 dst_ip 10.1.1.1"
        self.TestSteps.TestDescription.test_case_reference = "1.2.1"
