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


class IPv4_dynamic_arp_flow(BaseTest_SD):

    def __init__(self, testName=None, resource=None):
        # these lines must exist in every test !
        super(IPv4_dynamic_arp_flow, self).__init__(SuiteName="IPv4_routing", resource=resource, useTG=True)
        self.APIs = IPv4_routing_api(self)
        self.testName = testName
        self.TestSteps.TestDescription.test_author = "David Meu"
        self.TestSteps.TestDescription.test_case_reference = ""
        self.TestSteps.TestDescription.test_purpose = \
            """This test comes to verify: 
            * Adding dynamic entry to arp table
            """
        # define all tests steps in this area
        ##################### Test Steps and Description ##############################################################
        self.TestSteps.Step[1] = "Init interfaces sw1p1 sw1p13 sw1p25 sw1p37"
        self.TestSteps.Step[2] = "Configure sw1p1 sw1p13 sw1p25 sw1p37 ports up"
        self.TestSteps.Step[3] = "Disabling IPv4 forwarding"
        self.TestSteps.Step[4] = "Configure IP addrs 1.1.1.1/24 on sw1p1 2.2.2.2/24 on sw1p13 3.3.3.3/24 on sw1p25 4.4.4.4/24 on sw1p37"
        self.TestSteps.Step[5] = "Adding dynamic arp entries 1.1.1.5 for sw1p1 2.2.2.5 for sw1p13 3.3.3.5 for sw1p25 4.4.4.5 for sw1p37" \
                                 "and generating traffic and verifying reception"
        self.TestSteps.Step[6] = "Checking added arp entries 1.1.1.5 for sw1p1 2.2.2.5 for sw1p13 3.3.3.5 for sw1p25 4.4.4.5 for sw1p37"
        self.TestSteps.Step[7] = "Removing added arp entries 1.1.1.5 for sw1p1 2.2.2.5 for sw1p13 3.3.3.5 for sw1p25 4.4.4.5 for sw1p37"
        self.TestSteps.Step[8] = "Checking arp entries 1.1.1.5 for sw1p1 2.2.2.5 for sw1p13 3.3.3.5 for sw1p25 4.4.4.5 for sw1p37 have been removed"




    def TestProcedure( self ):

        """Init interfaces sw1p1 sw1p13 sw1p25 sw1p37"""
        self.TestSteps.RunStep(1)
        self.APIs.initInterfaces()

        """Configure sw1p1 sw1p13 sw1p25 sw1p37 ports up"""
        self.TestSteps.RunStep(2)
        for i in range(len(list(self.APIs._port_list))):
            self.APIs.configureEntityUp(self.APIs._port_list[i])

        """Disabling IPv4 forwarding"""
        self.TestSteps.RunStep(3)
        self.APIs.configureIPv4Forwarding(0)

        """Configure IP addrs 1.1.1.1/24 on sw1p1 2.2.2.2/24 on sw1p13 3.3.3.3/24 on sw1p25 4.4.4.4/24 on sw1p37"""
        self.TestSteps.RunStep(4)
        for i in range(len(list(self.APIs._port_list))):
            self.APIs.configureIPaddr(self.APIs._port_list[i])

        """Adding dynamic arp entries 1.1.1.5 for sw1p1 2.2.2.5 for sw1p13 3.3.3.5 for sw1p25 4.4.4.5 for sw1p37 
        and generating traffic and verifying reception"""
        self.TestSteps.RunStep(5)
        for i in range(1, len(list(self.TGDutLinks.values())), 2):
            self.APIs.setupStream(self.TGDutLinks[i], self.TGDutLinks[i+1])
            self.APIs.clearAllTGPortsCounters()
            self.APIs.transmitTraffic(self.TGDutLinks[i])
            self.APIs.verifyReceivedTrafficIsAsExpected(self.TGDutLinks[i], self.TGDutLinks[i+1])


        """Checking added arp entries 1.1.1.5 for sw1p1 2.2.2.5 for sw1p13 3.3.3.5 for sw1p25 4.4.4.5 for sw1p37"""
        self.TestSteps.RunStep(6)
        for i in range(len(list(self.APIs._port_list))):
            self.APIs.checkArpEntry(self.APIs._port_list[i])

        """Removing added arp entries 1.1.1.5 for sw1p1 2.2.2.5 for sw1p13 3.3.3.5 for sw1p25 4.4.4.5 for sw1p37"""
        self.TestSteps.RunStep(7)
        for i in range(len(list(self.APIs._port_list))):
            self.APIs.remStaticArpEntry(self.APIs._port_list[i])

        """Checking arp entries 1.1.1.5 for sw1p1 2.2.2.5 for sw1p13 3.3.3.5 for sw1p25 4.4.4.5 for sw1p37 have been removed"""
        self.TestSteps.RunStep(8)
        for i in range(len(list(self.APIs._port_list))):
            self.APIs.checkArpEntryNotInTable(self.APIs._port_list[i])













