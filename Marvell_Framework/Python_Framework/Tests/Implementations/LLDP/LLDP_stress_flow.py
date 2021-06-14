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
from Tests.Implementations.LLDP.LLDP_api import LLDP_api
from time import sleep


class LLDP_stress_flow(BaseTest_SD):

    def __init__(self, testName=None, resource=None):
        # these lines must exist in every test !
        super(LLDP_stress_flow, self).__init__(SuiteName="LLDP", resource=resource, useTG=True)
        self.APIs = LLDP_api(self)
        self.testName = testName
        self.TestSteps.TestDescription.test_author = "David Meu"
        self.TestSteps.TestDescription.test_case_reference = ""
        self.TestSteps.TestDescription.test_purpose = \
            """This test comes to verify: 
            * LLDP stress test en\dis on diff ports several times
            """
        # define all tests steps in this area
        ##################### Test Steps and Description ##############################################################
        self.TestSteps.Step[1] = "Init interfaces swp1p sw1p13 sw1p25 sw1p37"
        self.TestSteps.Step[2] = "Start lldp service"
        self.TestSteps.Step[3] = "Set ports sw1p1 sw1p13 sw1p25 sw1p37 up"
        self.TestSteps.Step[4] = "Configure tx-interval to 2 sec"
        self.TestSteps.Step[5] = "Filter lldp packet for sw1p1 sw1p13 sw1p25 sw1p37"
        self.TestSteps.Step[6] = "Disable lldp for sw1p1 enable for sw1p13 disable for sw1p25 enable for sw1p37"
        self.TestSteps.Step[7] = "Setup LLDP packet for trasmitting to sw1p1"
        self.TestSteps.Step[8] = "Transmitting LLDP packet to sw1p1 sw1p13 sw1p25 sw1p37"
        self.TestSteps.Step[9] = "Verifying LLDP packet received\dropped for sw1p1 sw1p13 sw1p25 sw1p37"
        self.TestSteps.Step[10] = "Clear all ports counters"
        self.TestSteps.Step[11] = "Verifying LLDP packet captured for sw1p1 sw1p13 sw1p25 sw1p37"
        self.TestSteps.Step[12] = "Enable lldp for sw1p1 disable for sw1p13 enable for sw1p25 disable for sw1p37"
        self.TestSteps.Step[13] = "Setting port down-up in order to clear neighbors info"
        self.TestSteps.Step[14] = "Verifying LLDP packet received\dropped for sw1p1 sw1p13 sw1p25 sw1p37"
        self.TestSteps.Step[15] = "Retransmitting LLDP packet to sw1p1 sw1p13 sw1p25 sw1p37"
        self.TestSteps.Step[16] = "Clear all ports counters"
        self.TestSteps.Step[17] = "Verifying LLDP packet captured for sw1p1 sw1p13 sw1p25 sw1p37"


    def TestProcedure( self ):

        """Init interfaces swp1p sw1p13 sw1p25 sw1p37"""
        self.TestSteps.RunStep(1)
        self.APIs.initInterfaces()

        """Start lldp service"""
        self.TestSteps.RunStep(2)
        self.APIs.LLDPServiceStart()

        """Set ports sw1p1 sw1p13 sw1p25 sw1p37 up"""
        self.TestSteps.RunStep(3)
        self.APIs.configurePortUp(self.APIs._port_list[0])
        self.APIs.configurePortUp(self.APIs._port_list[1])
        self.APIs.configurePortUp(self.APIs._port_list[2])
        self.APIs.configurePortUp(self.APIs._port_list[3])
        sleep(5)

        """Configure tx-interval to 2 sec"""
        self.TestSteps.RunStep(4)
        self.APIs.configureLLDPInterval(2)

        """Filter lldp packet for sw1p1 sw1p13 sw1p25 sw1p37"""
        self.TestSteps.RunStep(5)
        self.APIs.setupFilter(self.TGDutLinks[1], ttl=8)
        self.APIs.setupFilter(self.TGDutLinks[2], ttl=8)
        self.APIs.setupFilter(self.TGDutLinks[3], ttl=8)
        self.APIs.setupFilter(self.TGDutLinks[4], ttl=8)

        """Disable lldp for sw1p1 enable for sw1p13 disable for sw1p25 enable for sw1p37"""
        self.TestSteps.RunStep(6)
        self.APIs.configureInterfaceStat(self.APIs._port_list[0], status='disabled')
        self.APIs.configureInterfaceStat(self.APIs._port_list[1], status='rx-and-tx')
        self.APIs.configureInterfaceStat(self.APIs._port_list[2], status='disabled')
        self.APIs.configureInterfaceStat(self.APIs._port_list[3], status='rx-and-tx')

        """Setup LLDP packet for trasmitting to sw1p1 sw1p13 sw1p25 sw1p37"""
        self.TestSteps.RunStep(7)
        self.APIs.setupStream(self.TGDutLinks[1])
        self.APIs.setupStream(self.TGDutLinks[2])
        self.APIs.setupStream(self.TGDutLinks[3])
        self.APIs.setupStream(self.TGDutLinks[4])

        """Transmitting LLDP packet to sw1p1 sw1p13 sw1p25 sw1p37"""
        self.TestSteps.RunStep(8)
        self.APIs.transmitTraffic(self.TGDutLinks[1])
        self.APIs.transmitTraffic(self.TGDutLinks[2])
        self.APIs.transmitTraffic(self.TGDutLinks[3])
        self.APIs.transmitTraffic(self.TGDutLinks[4])

        """Verifying LLDP packet received\dropped for sw1p1 sw1p13 sw1p25 sw1p37"""
        self.TestSteps.RunStep(9)
        self.APIs.getTLVNeighborInfo(self.APIs._port_list[0])
        self.APIs.getTLVNeighborInfo(self.APIs._port_list[1])
        self.APIs.getTLVNeighborInfo(self.APIs._port_list[2])
        self.APIs.getTLVNeighborInfo(self.APIs._port_list[3])

        """Clear all ports counters"""
        self.TestSteps.RunStep(10)
        self.APIs.clearAllTGPortsCounters()

        """Verifying lldp packet captured for sw1p1 sw1p13 sw1p25 sw1p37"""
        self.TestSteps.RunStep(11)
        self.APIs.verifyReceivedTrafficIsAsExpected(self.TGDutLinks[1])
        self.APIs.verifyReceivedTrafficIsAsExpected(self.TGDutLinks[2])
        self.APIs.verifyReceivedTrafficIsAsExpected(self.TGDutLinks[3])
        self.APIs.verifyReceivedTrafficIsAsExpected(self.TGDutLinks[4])

        """Enable lldp for sw1p1 disable for sw1p13 enable for sw1p25 disable for sw1p37"""
        self.TestSteps.RunStep(12)
        self.APIs.configureInterfaceStat(self.APIs._port_list[0], status='rx-and-tx')
        self.APIs.configureInterfaceStat(self.APIs._port_list[1], status='disable')
        self.APIs.configureInterfaceStat(self.APIs._port_list[2], status='rx-and-tx')
        self.APIs.configureInterfaceStat(self.APIs._port_list[3], status='disable')

        """Setting port down-up in order to clear neighbors info"""
        self.TestSteps.RunStep(13)
        self.APIs.configurePortDown(self.APIs._port_list[1])
        self.APIs.configurePortDown(self.APIs._port_list[3])
        sleep(5)
        self.APIs.configurePortUp(self.APIs._port_list[1])
        self.APIs.configurePortUp(self.APIs._port_list[3])
        sleep(5)

        """Verifying LLDP packet received\dropped for sw1p1 sw1p13 sw1p25 sw1p37"""
        self.TestSteps.RunStep(14)
        self.APIs.getTLVNeighborInfo(self.APIs._port_list[0], stressMode=True)
        self.APIs.getTLVNeighborInfo(self.APIs._port_list[1], stressMode=True)
        self.APIs.getTLVNeighborInfo(self.APIs._port_list[2], stressMode=True)
        self.APIs.getTLVNeighborInfo(self.APIs._port_list[3], stressMode=True)

        """Retransmitting LLDP packet to sw1p1 sw1p13 sw1p25 sw1p37"""
        self.TestSteps.RunStep(15)
        self.APIs.transmitTraffic(self.TGDutLinks[1])
        self.APIs.transmitTraffic(self.TGDutLinks[2])
        self.APIs.transmitTraffic(self.TGDutLinks[3])
        self.APIs.transmitTraffic(self.TGDutLinks[4])

        """Clear all ports counters"""
        self.TestSteps.RunStep(16)
        self.APIs.clearAllTGPortsCounters()

        """Verifying lldp packet captured for sw1p1 sw1p13 sw1p25 sw1p37"""
        self.TestSteps.RunStep(17)
        self.APIs.verifyReceivedTrafficIsAsExpected(self.TGDutLinks[1], stressMode=True)
        self.APIs.verifyReceivedTrafficIsAsExpected(self.TGDutLinks[2], stressMode=True)
        self.APIs.verifyReceivedTrafficIsAsExpected(self.TGDutLinks[3], stressMode=True)
        self.APIs.verifyReceivedTrafficIsAsExpected(self.TGDutLinks[4], stressMode=True)




