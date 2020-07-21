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
from VlanTable import *
import time

def main():

     try:
        num = 20
        numVlans = 5
        numPorts = 32
        resTest = True
        IsCPSSVlanRefreshTableUsingDC = True

        print("initialize_system")
        DemoKeywords.initialize_system()

        #connect to the board and run cpss init
        print("# Connect to Chanel and initialize CPSS")
        aliasTelnet = LUACommunication.connect("PyTelnet", 23, ipAddr = '10.4.48.2', prompt = "->")
        LUACommunication.initialize(aliasTelnet, "appDemoJSON -tty -noconfig", "cpssInitSystem 29,1")

        # TG Connect according to con file
        print("Connect To TG")
        port_list_dic = DemoKeywords.connect_to_tg('test1.con')

        #Test 1

        # TG Configuration
        portId1 = port_list_dic['port0']

        pkt = V2Vlan()
        pkt.SetSize(128)
        pkt.mac.da = "00:00:22:22:22:22"
        pkt.vlan.VlanID = 1
        pkt.ethType.type = 0x600

        print("#Create Streams")
        sid = DemoKeywords.create_stream(portId1, pkt, 'next', 'PPS', 250, 100)

        print("set_SMAC_modifier_on_stream")
        DemoKeywords.set_SMAC_modifier_on_stream(portId1, sid, num, 1)

        print("apply per port")
        DemoKeywords.confirm_all(portId1)

        print("start_Tx")
        DemoKeywords.start_Tx(portId1)

        print("stop_Tx")
        DemoKeywords.stop_Tx(portId1)

        print("Verify Counters of Rx Port")
        portId2 = port_list_dic['port1']
        rx_frames = DemoKeywords.get_Rx_counter(portId2)
        if(rx_frames != 100):
            resTest = False

        # Board ....
        print("refresh_MacAddress_Table")
        fdbentries = LUACommunication.refresh_MacAddress_Table(aliasTelnet, devId=0)
        print("verify_Mac_Address_Table")
        res = LUACommunication.verify_Mac_Address_Table(fdbentries)
        if (res != True):
            resTest = False

        print("refresh_Events_Table")
        eventsentries = LUACommunication.refresh_Events_Table(aliasTelnet, devId=0)
        for entry in eventsentries:
            print(entry)


        #Test 2
        print("create_allvlans_and_add_allports_2_allvlans")
        LUACommunication.create_allvlans_and_add_allports_2_allvlans(aliasTelnet, 0, numVlans, numPorts)

        print("refresh_Vlans_Table")
        if(IsCPSSVlanRefreshTableUsingDC == False):
            vlanentries = LUACommunication.refresh_Vlans_Table(aliasTelnet, 0)
            for entry in vlanentries:
                print(entry)
        else:
            vt = VlanTable()
            vt.devId = 0
            vt.refresh(aliasTelnet)
            for ve in vt.entries:
                print(ve.info.fidValue)

        print("Disconnect from the board")
        LUACommunication.disconnect(aliasTelnet)

        print("uninitialize_system")
        DemoKeywords.uninitialize_system()

        strTestResult = 'Test passed'
        if resTest != True:
            strTestResult = 'Test Failed'
        print(strTestResult)

     except Exception as e:
         print(e.message)

if __name__ == "__main__":
    sys.exit(int(main() or 0))
