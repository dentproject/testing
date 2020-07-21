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
from Tests.Implementations.LAG.LAG_api import LAG_api


class LAG_LACP_Throughput_and_balancing_flow(BaseTest_SD):

    def __init__(self, testName=None, resource=None):
        # these lines must exist in every test !
        super(LAG_LACP_Throughput_and_balancing_flow, self).__init__(SuiteName="LAG", resource=resource, useTG=True)
        self.APIs = LAG_api(self)
        self.testName = testName
        self.TestSteps.TestDescription.test_author = "Shay Daniel"
        self.TestSteps.TestDescription.test_case_reference = ""
        self.TestSteps.TestDescription.test_purpose = \
            """This test comes to verify: 
            * It is possible to bring up LAG with maximum members, verify throughput and balance between members.
            
            """
        # define all tests steps in this area
        ##################### Test Steps and Description ##############################################################
        self.TestSteps.Step[1] = "Create LAG interfaces"
        self.TestSteps.Step[2] = "Create two bridge interfaces"
        self.TestSteps.Step[3] = "Enslave 8 switch ports to LAG1"
        self.TestSteps.Step[4] = "Enslave switch port with traffic and LAG1 to br1"
        self.TestSteps.Step[5] = "Link up 9 ports, LAG1, and br1"
        self.TestSteps.Step[6] = "Enslave 8 switch ports to LAG2"
        self.TestSteps.Step[7] = "Enslave switch port with traffic and LAG2 to br2"
        self.TestSteps.Step[8] = "Link up 9 ports, LAG2, and br2"
        self.TestSteps.Step[9] = "Configure 2 TG ports to bridging bi-dir traffic with IP source increment"
        self.TestSteps.Step[10] = "Clear DUT LAG members counters"
        self.TestSteps.Step[11] = "Send bi-dir traffic with rate near 8G and verify no losses on both sides"
        self.TestSteps.Step[12] = "Verify by DUT counters per LAG that traffic distribution is even among LAG members"


    def TestProcedure(self):

        """Init test"""
        self.APIs.initTest()
        "Configure basic LAG configuration"
        self.TestSteps.RunStep(1)
        self.APIs.createLAGInterfaces(1, 2)
        self.TestSteps.RunStep(2)
        self.APIs.createBRInterface("br1", vlan_filtering="0")
        self.APIs.createBRInterface("br2", vlan_filtering="0")
        self.TestSteps.RunStep(3)
        self.APIs.setLinksToGiga()
        self.APIs.assignInterfacesToLAGs(self.APIs._lag1_members, self.APIs._lag_1)
        self.TestSteps.RunStep(4)
        self.APIs.assignInterfacesToBridge([self.APIs._port_list_SwitchDevDutInterface[0], self.APIs._lag_1], "br1")
        self.TestSteps.RunStep(5)
        self.APIs.setLinkStateInterfaces(self.APIs._lag1_members + [self.APIs._port_list_SwitchDevDutInterface[0], self.APIs._lag_1, "br1"])
        self.TestSteps.RunStep(6)
        self.APIs.assignInterfacesToLAGs(self.APIs._lag2_members, self.APIs._lag_2)
        self.TestSteps.RunStep(7)
        self.APIs.assignInterfacesToBridge([self.APIs._port_list_SwitchDevDutInterface[1], self.APIs._lag_2], "br2")
        self.TestSteps.RunStep(8)
        self.APIs.setLinkStateInterfaces(self.APIs._lag2_members + [self.APIs._port_list_SwitchDevDutInterface[1], self.APIs._lag_2, "br2"])
        self.TestSteps.RunStep(9)
        self.APIs.configTgPortsBasicFlow()
        self.TestSteps.RunStep(10)
        self.APIs.playTrafficForMACLearn()
        self.APIs.clearDUTStats()
        self.TestSteps.RunStep(11)
        self.APIs.playTrafficBiDiAndVerifyResult()
        self.TestSteps.RunStep(12)
        self.APIs.verifyDUTStats(self.APIs._lag1_members, self.APIs._tg_port_list[0],
                                 self.APIs._lag2_members, self.APIs._tg_port_list[1])
