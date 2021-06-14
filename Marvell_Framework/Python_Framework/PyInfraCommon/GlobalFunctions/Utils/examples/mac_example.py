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
from PyInfraCommon.GlobalFunctions.Utils.MAC import MacManager, MacFormat

def main():
    macM = MacManager()
    print(MacManager.GenerateRandomMac(mask="00:AA:BB:XX:XX:XX"))

    mac_1 = "00:AA:4B:07:D4:12"
    print("MAC BARE: {}\n".format(MacManager.Format(mac_1, MacFormat.MAC_BARE)))
    print("MAC EUI 48 Upper: {}\n".format(MacManager.Format(mac_1, MacFormat.MAC_EUI_48_COLUMN_UPPER)))
    print("MAC Unix Expanded: {}\n".format(MacManager.Format(mac_1, MacFormat.MAC_UNIX_EXPANDED)))
    print("MAC Microsoft: {}\n".format(MacManager.Format(mac_1, MacFormat.MAC_MICROSOFT)))
    print("MAC Cisco: {}\n".format(MacManager.Format(mac_1, MacFormat.MAC_CISCO)))

    #
    # print int("0xffffffffffff", 0)
    # int_1 = 42
    # print "{0:0{1}X}".format(42,12)
    print(MacManager.GetMacIncremented(mac_1, 5))
if __name__ == "__main__":
    main()