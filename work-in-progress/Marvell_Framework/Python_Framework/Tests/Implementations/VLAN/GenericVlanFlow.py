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
from Tests.Implementations.VLAN.GenericVlanAPI import GenericVlanAPI


class GenericVlanFlow(BaseTest_SD):

    def __init__(self, testName=None):
        super(GenericVlanFlow, self).__init__(SuiteName="VLAN", resource=r'VLAN/Resources/GenericVlanData')
        self.testName = testName
        self.APIs = None  # type: GenericVlanAPI
        self.TestSteps.TestDescription.test_author = "Maya Peretz"
        self.TestSteps.TestDescription.test_case_reference = ""
        self.TestSteps.TestDescription.test_purpose = \
            """This test comes to verify:
            * VLANS setting and verification
            """
        # define all tests steps in this area
        ##################### Test Steps and Description ##############################################################
        self.TestSteps.Step[1] = "Initiate test params"
        self.TestSteps.Step[2] = "Set link up on interfaces"
        self.TestSteps.Step[3] = "Create bridge entity and set link up on it"
        self.TestSteps.Step[4] = "Enslave interfaces to the created bridge entity"
        self.TestSteps.Step[5] = "Insert interfaces to VLAN as specified by the test case"
        self.TestSteps.Step[6] = "Define RX and non-RX ports according to the VLAN configuration"
        self.TestSteps.Step[7] = "Set up streams as specified by the test case"
        self.TestSteps.Step[8] = "Send Traffic from each of the transmitting interfaces according to the test case"
        self.TestSteps.Step[9] = "Verify no packet loss nor packet leak occurred and all transmitted traffic received"

    def TestProcedure(self):
        tgDutLinks = list(self.TGDutLinks.values())
        self.TestSteps.RunStep(1)
        self.APIs.initTestParams(self.TestCaseData['Tests'][self.testName])

        self.TestSteps.RunStep(2)
        self.APIs.setLinkStateOnInterfaces(tgDutLinks)
        self.TestSteps.RunStep(3)
        self.APIs.createAndSetSoftEntityUp()

        self.TestSteps.RunStep(4)
        self.APIs.enslavePortsToSoftLink(tgDutLinks)

        self.TestSteps.RunStep(5)
        self.APIs.configureVlans(self.TGDutLinks)

        self.TestSteps.RunStep(6)
        self.APIs.setRxAndNonRxPorts(self.TGDutLinks)

        self.TestSteps.RunStep(7)
        self.APIs.setupStream(self.TGDutLinks)
        self.APIs.addTriggers(self.TGDutLinks)
        self.APIs.applyTGSettings(self.TGDutLinks)

        self.TestSteps.RunStep(8)

        # clear all tgPortCounters
        tgPorts = [port.TGPort for port in self.TGDutLinks.values()]
        self.TGManager.chassis.clear_all_stats(tgPorts)
        txPorts = [self.TGDutLinks[int(port)] for port in self.TestCaseData['Tests'][self.testName]['tx_interfaces']]
        rxPorts = [self.TGDutLinks[int(port)] for port in
                   [item for sublist in self.APIs.rxInterfaces.values() for item in sublist]]
        self.APIs.transmitTraffic(self.TGManager, txPorts, rxPorts)


class VlanFlow(GenericVlanFlow):

    def __init__(self, testName=None):
        super(VlanFlow, self).__init__(testName=testName)
        self.TestSteps.Step[9] = "Verify no packet loss nor packet leak occurred and all transmitted traffic received"

    def TestProcedure(self):
        super(VlanFlow, self).TestProcedure()
        self.TestSteps.RunStep(9)
        self.TGManager.chassis.get_all_ports_stats()
        rxPortsExpectedCounters = self.APIs.calculateExpectedTraffic(self.TGDutLinks)
        for rxPort, portCounter in rxPortsExpectedCounters.items():
            status = self.APIs.verifyCountersOnPorts(self.TGDutLinks[rxPort], portCounter)
            if not status:
                self.APIs.verifyNoBadOctets([port.DutDevPort for port in self.TGDutLinks.values()])
                dbg = 'Failed! a bad formatted stream might have been received or a packet loss might might occurred'
                self.FailTheTest(dbg)
        else:
            self.logger.debug('Passed! No traffic loss has occurred')

        status, funcname = self.APIs.verifyNoTrafficOnOtherVlans()
        if not status:
            dbg = funcname + \
                  'Failed: a bad formatted stream might have been received or a packet loss might might occurred'
            self.FailTheTest(dbg)
        else:
            self.logger.debug(funcname + 'Passed: No traffic has leaked')
