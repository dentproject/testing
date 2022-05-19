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
from CLI_GlobalFunctions.SwitchDev.SpanningTree.AbstractSpanningTreeConfig import AbstractSpanningTreeConfig
from CLI_GlobalFunctions.SwitchDev.SpanningTree.RapidSpanningTreeConfig import RapidSpanningTreeConfig
from CLI_GlobalFunctions.SwitchDev.SpanningTree.StandardSpanningTreeConfig import StandardSpanningTreeConfig
from PyInfra.BaseTest_SV.BaseTest_SD import BaseTest_SD
from PyInfra.BaseTest_SV.SV_Enums.SwitchDevInterface import SwitchDevDutInterface
from PyInfraCommon.GlobalFunctions.Random import Randomize
from Tests.Implementations.SpanningTree.APIs.SpanningTreeAPI import SpanningTreeAPI

br0 = None  # type: AbstractSpanningTreeConfig
br1 = None  # type: AbstractSpanningTreeConfig
br2 = None  # type: AbstractSpanningTreeConfig


class SelectingTheRootBridgeUsingBridgePrioFlow(BaseTest_SD):

    def __init__(self):
        super(SelectingTheRootBridgeUsingBridgePrioFlow, self).__init__(SuiteName="STP_RSTP", resource="SpanningTree/SpanningTreeData")
        self.TestSteps.TestDescription.test_author = "Maya Peretz"
        self.TestSteps.TestDescription.test_case_reference = ""
        self.TestSteps.TestDescription.test_purpose = \
            """
            Verify the root bridge is selected by the lowest priority number.
            """
        # define all tests steps in this area
        self.APIs = SpanningTreeAPI(self)
        self.TestSteps.Step[1] = "Create 3 bridge entities: br0, br1, br2 and set link up on them"
        self.TestSteps.Step[2] = "Enslave ports according to the test's setup topology"
        self.TestSteps.Step[3] = "Change the MAC addresses for all bridges; change the priority for all bridges."
        self.TestSteps.Step[4] = "Set link up on all participant ports"
        self.TestSteps.Step[5] = "Wait ~40 seconds until topology fully converges"
        self.TestSteps.Step[6] = "Verify the bridge root is br1 by the lowest MAC rule; verify other bridges" \
                                 " do not consider themselves as root-bridge"
        self.TestSteps.Step[7] = "Verify br2 has a blocking port."
        self.TestSteps.Step[8] = "Verify br1 doesn’t have any blocking port."
        self.TestSteps.Step[9] = "Change the highest bridge priority to a priority with lower value then the root bridge."
        self.TestSteps.Step[10] = "Wait ~40 seconds for topology to re-build."
        self.TestSteps.Step[11] = "Verify it has become the new root bridge."
        self.TestSteps.Step[12] = "Verify br2 has a blocking port."
        self.TestSteps.Step[13] = "Verify br1 doesn’t have any blocking port."

    def TestProcedure(self):

        # -------------------------------------------------------------------------------------------------------------
        # STEP 1 - Create 3 bridge entities: br0, br1, br2 and set link up on them
        self.TestSteps.RunStep(1)
        self.APIs.createAndSetSoftEntityUp(softEntity=br0)
        self.APIs.createAndSetSoftEntityUp(softEntity=br1)
        self.APIs.createAndSetSoftEntityUp(softEntity=br2)

        # -------------------------------------------------------------------------------------------------------------
        # STEP 2 - Enslave ports according to the test's setup topology
        self.TestSteps.RunStep(2)
        self.APIs.enslavePortsToSoftLink(self.TestCaseData["Topology#1"][str(br0)], br0)
        self.APIs.enslavePortsToSoftLink(self.TestCaseData["Topology#1"][str(br1)], br1)
        self.APIs.enslavePortsToSoftLink(self.TestCaseData["Topology#1"][str(br2)], br2)

        # -------------------------------------------------------------------------------------------------------------
        # STEP 3 - Change the MAC addresses for all bridges; change the priority for all bridges.
        self.TestSteps.RunStep(3)
        self.APIs.verifyNoError(br0.changeSelfMac(Randomize().Mac("44:XX:XX:XX:XX:XX")))
        self.APIs.verifyNoError(br1.changeSelfMac(Randomize().Mac("22:XX:XX:XX:XX:XX")))
        self.APIs.verifyNoError(br2.changeSelfMac(Randomize().Mac("00:XX:XX:XX:XX:XX")))

        self.APIs.verifyNoError(br0.setBridgePrio(2))
        self.APIs.verifyNoError(br1.setBridgePrio(3))
        self.APIs.verifyNoError(br2.setBridgePrio(4))

        # -------------------------------------------------------------------------------------------------------------
        # STEP 4 - Set link up on all participant ports
        self.TestSteps.RunStep(4)
        self.APIs.setLinkStateOnInterfaces(br0.enslavedInterfaces + br1.enslavedInterfaces + br2.enslavedInterfaces)

        # -------------------------------------------------------------------------------------------------------------
        # STEP 5 - Wait until topology converges
        self.TestSteps.RunStep(5)
        time.sleep(40)
        self.APIs.verifyNoError(br0.getStpDetails())
        # -------------------------------------------------------------------------------------------------------------
        # STEP 6 - Verify the bridge root is br1 by the lowest MAC rule; verify other bridges
        # do not consider themselves as root-bridge
        self.TestSteps.RunStep(6)
        if not br0.isRootBridge():
            self.FailTheTest('FAIL: br0 is not the root-bridge')

        if br1.isRootBridge() or br2.isRootBridge():
            self.FailTheTest('FAIL: STP topology has not been converged')

        # -------------------------------------------------------------------------------------------------------------
        # STEP 7 - Verify br2 has a blocking port
        self.TestSteps.RunStep(7)
        if not br2.getDirectPort():
            self.FailTheTest("FAIL: br2 doesn't have a blocking port")

        # -------------------------------------------------------------------------------------------------------------
        # STEP 8 - Verify br1 doesn’t have any blocking port.
        self.TestSteps.RunStep(8)
        if not br1.getIndirectPort():
            self.FailTheTest("FAIL: br1 has a blocking port or it's not part of the topology")

        # -------------------------------------------------------------------------------------------------------------
        # STEP 9 - Change the highest bridge priority to a priority with lower value then the root bridge.
        self.TestSteps.RunStep(9)
        self.APIs.verifyNoError(br2.setBridgePrio(1))

        # -------------------------------------------------------------------------------------------------------------
        # STEP 10 - Wait ~40 seconds for topology to re-build.
        self.TestSteps.RunStep(10)
        time.sleep(40)

        # -------------------------------------------------------------------------------------------------------------
        # STEP 11 - Verify it has become the new root bridge.
        self.TestSteps.RunStep(11)
        self.APIs.verifyNoError(br0.getStpDetails())

        if not br2.isRootBridge():
            self.FailTheTest('FAIL: br2 is not the root-bridge')

        if br0.isRootBridge() or br1.isRootBridge():
            self.FailTheTest('FAIL: STP topology has not been converged')

        # -------------------------------------------------------------------------------------------------------------
        # STEP 12 - Verify br2 has a blocking port
        self.TestSteps.RunStep(12)
        if not br1.getDirectPort():
            self.FailTheTest("FAIL: br1 doesn't have a blocking port")

        # -------------------------------------------------------------------------------------------------------------
        # STEP 13 - Verify br1 doesn’t have any blocking port.
        self.TestSteps.RunStep(13)
        if not br0.getIndirectPort():
            self.FailTheTest("FAIL: br1 has a blocking port or it's not part of the topology")


class StpSelectingTheRootBridgeUsingBridgePrioFlow(SelectingTheRootBridgeUsingBridgePrioFlow):

    def TestProcedure(self):
        global br0, br1, br2
        br0 = StandardSpanningTreeConfig(SwitchDevDutInterface('br0'))
        br1 = StandardSpanningTreeConfig(SwitchDevDutInterface('br1'))
        br2 = StandardSpanningTreeConfig(SwitchDevDutInterface('br2'))
        super(StpSelectingTheRootBridgeUsingBridgePrioFlow, self).TestProcedure()


class RstpSelectingTheRootBridgeUsingBridgePrioFlow(SelectingTheRootBridgeUsingBridgePrioFlow):

    def TestProcedure(self):
        global br0, br1, br2
        br0 = RapidSpanningTreeConfig(SwitchDevDutInterface('br0'))
        br1 = RapidSpanningTreeConfig(SwitchDevDutInterface('br1'))
        br2 = RapidSpanningTreeConfig(SwitchDevDutInterface('br2'))
        super(RstpSelectingTheRootBridgeUsingBridgePrioFlow, self).TestProcedure()

