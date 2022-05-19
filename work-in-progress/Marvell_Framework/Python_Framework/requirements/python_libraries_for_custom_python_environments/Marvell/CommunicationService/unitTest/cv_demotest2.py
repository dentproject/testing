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

from __future__ import print_function
import sys
from DemoKeywords import *
from LUACommunication import *
from Common.Types import *
import time

def main():

     try:
        num = 20
        numVlans = 5
        numPorts = 32
        resTest = True

        DemoKeywords.initialize_system()

        # TG Connect according to con file
        port_list_dic = DemoKeywords.connect_to_tg('test1.con')

        #connect to the board and run cpss init
        #aliasTelnet = LUACommunication.connect(CommunicationType.PyTelnet, 23, ipAddr = '10.4.48.2', prompt = "->")
        aliasTelnet = LUACommunication.connect("PyTelnet", 23, ipAddr = '10.4.48.2', prompt = "->")
        #aliasTelnet = LUACommunication.connect("PyTelnet", 23)
        LUACommunication.initialize(aliasTelnet, "appDemo -tty", "cpssInitSystem 29,1")



        #Test 1

        # TG Configuration
        portId1 = port_list_dic['port0']

        pkt = V2Vlan()
        pkt.SetSize(128)
        pkt.mac.da = "00:00:22:22:22:22"
        pkt.vlan.VlanID = 1
        pkt.ethType.type = 0x600

        sid = DemoKeywords.create_stream(portId1, pkt, 'next', 'PPS', 1, num)

        DemoKeywords.set_SMAC_modifier_on_stream(portId1, sid, num, 1)

        DemoKeywords.confirm_all(portId1)

        DemoKeywords.start_Tx(portId1)

        DemoKeywords.stop_Tx(portId1)

        # Board ....
        fdbentries = LUACommunication.refresh_MacAddress_Table(aliasTelnet, devId=0)
        res = LUACommunication.verify_Mac_Address_Table(fdbentries)
        if (res != True):
            resTest = res

        eventsentries = LUACommunication.refresh_Events_Table(aliasTelnet, devId=0)
        for entry in eventsentries:
            print(entry)


        #Test 2
        LUACommunication.add_allports_2_allvlans(aliasTelnet, 0, numVlans, numPorts)

        vlanentries = LUACommunication.refresh_Vlans_Table(aliasTelnet, 0)
        for entry in vlanentries:
            print(entry)

        LUACommunication.disconnect(aliasTelnet)

        DemoKeywords.uninitialize_system()

        strTestResult = 'Test passed'
        if resTest != True:
            strTestResult = 'Test Failed'
        print(strTestResult)

     except Exception as e:
         print(e.message)

if __name__ == "__main__":
    sys.exit(int(main() or 0))
