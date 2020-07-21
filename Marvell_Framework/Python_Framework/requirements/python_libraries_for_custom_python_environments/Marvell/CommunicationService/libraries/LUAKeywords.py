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
from __future__ import absolute_import
from builtins import hex
from builtins import str
from builtins import range
from builtins import object
from .PythonWrapper import *
import re

class LUAKeywords(object):

    @classmethod
    def showtable(self, patternhead, pattern, command):
        resultHead = re.search(patternhead, command, re.MULTILINE)
        resultData = re.findall(pattern, command, re.MULTILINE)
        listRes = []
        for result in resultData:
            # do something with each found email string
            dict = {}
            for idx in range(resultHead.lastindex):
                #print (resultHead.group(idx + 1))
                #print (result)
                dict[resultHead.group(idx + 1)] = result[idx]
            listRes.append(dict)
        return listRes

    @staticmethod
    def connect(spId):
        CommonManagement.Connect(spId)

    @staticmethod
    def disconnect():
        CommonManagement.SendTerminalString("CLIexit", False)
        CommonManagement.Disconnect()

    @staticmethod
    def initialize(str):
        CommonManagement.SetShellPrompt("->")
        CommonManagement.SendCommandAndGetBuffer(str, 5)
        CommonManagement.SetShellPrompt("[cC]onsole[-()\w]*#.*")
        CommonManagement.SendCommandAndGetBuffer("luaCLI", 2)

    @staticmethod
    def refresh_MacAddress_Table(devId):

        patternhead = r'\s+(Index)\s+(Address)\s+(Vlan)\s+(VID1)\s+(Skip)\s+(Interface)\s+(Static)\s+(DA Route)' \
                      r'\s+(saCommand)\s+(daCommand)\s+(sp)\s+'

        pattern = r'(\d+)\s+((?:[0-9A-Fa-f]{2}[:]){5}[0-9A-Fa-f]{2})\s+(\d+)\s+(\d+)\s+(\w+)\s+(\w+\s\d+\/\d+)' \
                  r'\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+'

        response = ""
        response += CommonManagement.SendCommandAndGetBuffer("show mac address-table all device " + str(devId), 2)
        #CommonManagement.SendTerminalString("show mac address-table all device " + str(devId), 2)
        #response = ""
        #response += CommonManagement.GetSerialBuffer(1000)
        print ("\n................................. response ................................\n")

        print (response)

        fdbentries = LUAKeywords.showtable(patternhead, pattern, response)

        return fdbentries

    @staticmethod
    def verify_Mac_Address_Table(fdbentries):
        smac = "00:00:00:00:00:00"  # mac = FDB_entries[0]["Address"]

        """
        i = 1
        for entry in fdbentries:
            nhex = hex(i)
            str_hex = str(nhex)[2:]
            new_mac = smac[0:(len(smac) - len(str_hex))] + str_hex
            i += 1
            #assert (entry["Address"] == new_mac)
            if entry["Address"] != new_mac:
                return False

        return True
        """
        address = []
        for entry in fdbentries:
            address.append(entry["Address"])

        address.sort()

        for i in range(len(address)):
            nhex = hex(i)
            str_hex = str(nhex)[2:]
            new_mac = smac[0:(len(smac) - len(str_hex))] + str_hex

            if address[i] != new_mac:
                return False

        return True

    @staticmethod
    def refresh_Events_Table(devId):

        patternhead = r'\s+(event type)\s+(counter value)\s+'

        pattern = r'(\w+)\s+(\d+)\s+'

        CommonManagement.SendCommandAndGetBuffer("debug-mode", 2)

        response = CommonManagement.SendCommandAndGetBuffer('event-table show device ' +
                                                            str(devId) + ' eventType CPSS_PP_EVENTS', 2)


        eventsentries = LUAKeywords.showtable(patternhead, pattern, response)

        CommonManagement.SendCommandAndGetBuffer("exit", 2)

        return eventsentries


    @staticmethod
    def add_allports_2_allvlans(devId, vlancount):

        #show port smi-mapping device 0

        CommonManagement.SendCommandAndGetBuffer("configure", 2)

        CommonManagement.SendCommandAndGetBuffer("interface range ethernet " + str(devId) + "/0-31", 2)

        #remove default VLAN
        CommonManagement.SendCommandAndGetBuffer("switchport allowed vlan remove 1", 2)

        for idx in range(1, vlancount):
            CommonManagement.SendCommandAndGetBuffer("switchport pvid " + str(idx), 2)
            for portIdx in range (1, 32):
                CommonManagement.SendCommandAndGetBuffer("switchport allowed vlan add " + str(portIdx) + " tagged", 2)

        CommonManagement.SendCommandAndGetBuffer("exit", 2)

        CommonManagement.SendCommandAndGetBuffer("exit", 2)

    @staticmethod
    def refresh_Vlans_Table(devId):

        # response = "VLAN Ports Tag MAC-Learning fdb-lookup-mode" \
        #           "----- ----------------------------------------------------- -------- -------------- --------------" \
        #           "1 0/0-59,64-71,80-82 untagged Control fid"

        patternhead = patternhead = r'\s*(VLAN)\s+(Ports)\s+(Tag)\s+(MAC-Learning)\s+(FDB-mode)'

        pattern = r'(\d)+\s+([\d\/\-,]+)\s+(\w+)\s+(\w+)\s+(\w+)'

        #CommonManagement.SendCommandAndGetBuffer("config", 2)

        #response = CommonManagement.SendCommandAndGetBuffer('do show vlan device ' + str(devId), 10)
        CommonManagement.SendTerminalString('do show vlan device ' + str(devId), False)
        response = ""
        response += CommonManagement.GetSerialBuffer(1000)
        while(response.find("Console") == -1):
            CommonManagement.SendTerminalString('\n' + str(devId), False)
            response += CommonManagement.GetSerialBuffer(1000)

        print(response)

        eventsentries = LUAKeywords.showtable(patternhead, pattern, response)

        CommonManagement.SendCommandAndGetBuffer("exit", 2)

        return eventsentries
