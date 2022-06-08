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
from Tests.Implementations.IPv4_routing.IPv4_routing_api import IPv4_routing_api
from Tests.Implementations.ECMP.ECMP_api import ECMP_api

class ECMP_unicast_traffic_distribution_flow(BaseTest_SD):

    def __init__(self, testName=None, resource=None):
        # these lines must exist in every test !
        super(ECMP_unicast_traffic_distribution_flow, self).__init__(SuiteName="ECMP", resource=resource, useTG=True)
        self.APIs_IPv4_routing = IPv4_routing_api(self)
        self.APIs_ecmp = ECMP_api(self)
        self.testName = testName
        self.TestSteps.TestDescription.test_author = "David Meu"
        self.TestSteps.TestDescription.test_case_reference = ""
        self.TestSteps.TestDescription.test_purpose = \
            """This test comes to verify: 
            * Unicast traffic distribution 
            """
        # define all tests steps in this area
        ##################### Test Steps and Description ##############################################################
        self.TestSteps.Step[1] = "Init interfaces sw1p1 sw1p13 sw1p25 sw1p37"
        self.TestSteps.Step[2] = "Configure sw1p1 sw1p13 sw1p25 sw1p37 ports up"
        self.TestSteps.Step[3] = "Disabling IPv4 forwarding"
        self.TestSteps.Step[4] = "Configure IP addrs 1.1.1.1/24 on sw1p1 11.0.0.1/8 on sw1p13 12.0.0.1/16 on sw1p25 13.0.0.1/20 on sw1p37"
        self.TestSteps.Step[5] = "Configure permanent arp entries 11.0.0.2 lladdr 00:AD:20:B2:A7:75 dev sw1p13 12.0.0.2 lladdr 00:59:CD:1E:83:1B dev sw1p25 13.0.0.2 lladdr 00:76:69:89:E0:7B dev sw1p37"
        self.TestSteps.Step[6] = "Configure next hops 11.0.0.2 12.0.0.2 13.0.0.2 with dest network 100.0.0.0/8"
        self.TestSteps.Step[7] = "Adding dynamic arp entry 1.1.1.2 aa:bb:cc:dd:ee:11 for sw1p1"
        self.TestSteps.Step[8] = "Setup streams for sw1p13 sw1p25 sw1p37  routes"
        self.TestSteps.Step[9] = "Setup filter for sw1p13 sw1p25 sw1p37 "
        self.TestSteps.Step[10] = "Transmitting sw1p13 sw1p25 sw1p37 streams"
        self.TestSteps.Step[11] = "Verifying traffic excepted for all available hops"

    def TestProcedure(self):
        """Init interfaces sw1p1 sw1p13 sw1p25 sw1p37"""
        self.TestSteps.RunStep(1)
        self.APIs_IPv4_routing.initInterfaces()
        self.APIs_ecmp.initInterfaces()

        """Configure sw1p1 sw1p13 sw1p25 sw1p37 ports up"""
        self.TestSteps.RunStep(2)
        self.APIs_IPv4_routing.configureEntityUp(self.APIs_IPv4_routing._port_list[0])
        self.APIs_IPv4_routing.configureEntityUp(self.APIs_IPv4_routing._port_list[1])
        self.APIs_IPv4_routing.configureEntityUp(self.APIs_IPv4_routing._port_list[2])
        self.APIs_IPv4_routing.configureEntityUp(self.APIs_IPv4_routing._port_list[3])

        """Disabling IPv4 forwarding"""
        self.TestSteps.RunStep(3)
        self.APIs_IPv4_routing.configureIPv4Forwarding(1)

        """Configure IP addrs 1.1.1.1/24 on sw1p1 11.0.0.1/8 on sw1p13 12.0.0.1/16 on sw1p25 13.0.0.1/20 on sw1p37"""
        self.TestSteps.RunStep(4)
        self.APIs_IPv4_routing.configureIPaddr(self.APIs_IPv4_routing._port_list[0])
        self.APIs_IPv4_routing.configureIPaddr(self.APIs_IPv4_routing._port_list[1])
        self.APIs_IPv4_routing.configureIPaddr(self.APIs_IPv4_routing._port_list[2])
        self.APIs_IPv4_routing.configureIPaddr(self.APIs_IPv4_routing._port_list[3])

        """Configure permanent arp entries 11.0.0.2 lladdr 00:AD:20:B2:A7:75 dev sw1p13 12.0.0.2 lladdr 00:59:CD:1E:83:1B dev sw1p25 13.0.0.2 lladdr 00:76:69:89:E0:7B dev sw1p37"""
        self.TestSteps.RunStep(5)
        self.APIs_IPv4_routing.configurePermanentNeigh(self.APIs_IPv4_routing._port_list[1])
        self.APIs_IPv4_routing.configurePermanentNeigh(self.APIs_IPv4_routing._port_list[2])
        self.APIs_IPv4_routing.configurePermanentNeigh(self.APIs_IPv4_routing._port_list[3])

        """Configure next hops 11.0.0.2 12.0.0.2 13.0.0.2 with dest network 100.0.0.0/8"""
        self.TestSteps.RunStep(6)
        self.APIs_ecmp.configureNextHops()

        """Adding dynamic arp entry 1.1.1.2 aa:bb:cc:dd:ee:11 for sw1p1"""
        self.TestSteps.RunStep(7)
        self.APIs_ecmp.setupDynamicArpEntry(self.TGDutLinks[1])

        """Setup streams for sw1p13 sw1p25 sw1p37  routes"""
        self.TestSteps.RunStep(8)
        self.APIs_ecmp.setupStreams(self.TGDutLinks[1])

        """Setup filter for sw1p13 sw1p25 sw1p37 """
        self.TestSteps.RunStep(9)
        self.APIs_ecmp.setupFilter(self.TGDutLinks[2])
        self.APIs_ecmp.setupFilter(self.TGDutLinks[3])
        self.APIs_ecmp.setupFilter(self.TGDutLinks[4])

        """Transmitting sw1p13 sw1p25 sw1p37  streams"""
        self.TestSteps.RunStep(10)
        self.APIs_ecmp.clearAllTGPortsCounters()
        self.APIs_ecmp.transmitTraffic(self.TGDutLinks[1])

        """Verifying traffic excepted for all available hops"""
        self.TestSteps.RunStep(11)
        self.APIs_ecmp.verifyReceivedTrafficIsAsExpected(self.TGDutLinks[1], self.TGDutLinks[2])
        self.APIs_ecmp.verifyReceivedTrafficIsAsExpected(self.TGDutLinks[1], self.TGDutLinks[3])
        self.APIs_ecmp.verifyReceivedTrafficIsAsExpected(self.TGDutLinks[1], self.TGDutLinks[4])



