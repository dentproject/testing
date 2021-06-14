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

from builtins import range
from PyInfra.BaseTest_SV.BaseTest_SD import BaseTest_SD
from Tests.Implementations.Bridging.Bridging_api import Bridging_api


class Bridging_learning_addr_flow(BaseTest_SD):

    def __init__(self, testName=None, resource=None):
        # these lines must exist in every test !
        super(Bridging_learning_addr_flow, self).__init__(SuiteName="Bridging", resource=resource, useTG=True)
        self.APIs = Bridging_api(self)
        self.testName = testName
        self.TestSteps.TestDescription.test_author = "David Meu"
        self.TestSteps.TestDescription.test_case_reference = ""
        self.TestSteps.TestDescription.test_purpose = \
            """This test comes to verify: 
            * bridge dynamic entries learning 
            """
        # define all tests steps in this area
        ##################### Test Steps and Description ##############################################################
        self.TestSteps.Step[1] = "Init bridge entity br0"
        self.TestSteps.Step[2] = "Set ports sw1p1 sw1p13 sw1p25 sw1p37 master br0"
        self.TestSteps.Step[3] = "Set ports sw1p1 sw1p13 sw1p25 sw1p37 learning on"
        self.TestSteps.Step[4] = "Set ports sw1p1 sw1p13 sw1p25 sw1p37 flood off"
        self.TestSteps.Step[5] = "Set entities sw1p1 sw1p13 sw1p25 sw1p37 br0 up"
        self.TestSteps.Step[6] = "Traffic Sending to sw1p1 sw1p13 sw1p25 sw1p37" \
                                 "with src macs aa:bb:cc:dd:ee:11 aa:bb:cc:dd:ee:12 aa:bb:cc:dd:ee:13 aa:bb:cc:dd:ee:14 accordingly and verifying addrs have been learned"




    def TestProcedure( self ):

        """Init bridge entity br0"""
        self.TestSteps.RunStep(1)
        self.APIs.initBridge()

        """Set ports sw1p1 sw1p13 sw1p25 sw1p37 master br0"""
        self.TestSteps.RunStep(2)
        self.APIs.configurePortMaster()

        """Set ports sw1p1 sw1p13 sw1p25 sw1p37 learning on"""
        self.TestSteps.RunStep(3)
        self.APIs.configurePortsLearningOn()

        """Set ports sw1p1 sw1p13 sw1p25 sw1p37 flood off"""
        self.TestSteps.RunStep(4)
        self.APIs.configurePortsFloodOff()

        """Set entities sw1p1 sw1p13 sw1p25 sw1p37 br0 up"""
        self.TestSteps.RunStep(5)
        self.APIs.configureEntitiestUp()

        """Traffic Sending to sw1p1 sw1p13 sw1p25 sw1p37
        with src macs aa:bb:cc:dd:ee:11 aa:bb:cc:dd:ee:12 aa:bb:cc:dd:ee:13 aa:bb:cc:dd:ee:14 accordingly and verifying addrs have been learned"""
        self.TestSteps.RunStep(6)
        for i in range(1,len(list(self.TGDutLinks.values())),2):
            self.APIs.setupStream(self.TGDutLinks[i], self.TGDutLinks[i+1])
            self.APIs.clearAllTGPortsCounters()
            self.APIs.transmitTraffic(self.TGDutLinks[i])
            self.APIs.checkAddrInFDB(self.TGDutLinks[i])
        for i in range(len(list(self.TGDutLinks.values())),1,-2):
            self.APIs.setupStream(self.TGDutLinks[i], self.TGDutLinks[i-1])
            self.APIs.clearAllTGPortsCounters()
            self.APIs.transmitTraffic(self.TGDutLinks[i])
            self.APIs.checkAddrInFDB(self.TGDutLinks[i])







