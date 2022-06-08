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
from HighCommunicationLayer.CommunicationManagement import *
from .DemoKeywords import *
from Common.Types import *
from robot.api import logger

class LUACommunication(object):
    commManager = None

    @classmethod
    def showtable(self, patternhead, pattern, command):
        resultHead = re.search(patternhead, command, re.MULTILINE)
        resultData = re.findall(pattern, command, re.MULTILINE)
        listRes = []
        for result in resultData:
            # do something with each found email string
            dict = {}
            for idx in range(resultHead.lastindex):
                # print (resultHead.group(idx + 1))
                # print (result)
                dict[resultHead.group(idx + 1)] = result[idx]
            listRes.append(dict)
        return listRes

    @staticmethod
    def connect(commType , port ,ipAddr=None, uname=None,password=None ,prompt=">"):
        tmpcommType = None
        commType = str(commType)

        if commType == "PyTelnet":
             tmpcommType = CommunicationType.PyTelnet
        elif commType == "PySerial":
             tmpcommType = CommunicationType.PySerial
        elif commType == "CoSTelnet":
             tmpcommType = CommunicationType.CoSTelnet
        elif commType == "CoSSerial":
             tmpcommType = CommunicationType.CoSSerial

        conn =  CommunicationManagement.Connect(tmpcommType, port, str(ipAddr), uname, password, prompt)
        logger.console(conn)
        return conn
    @staticmethod
    def disconnect(connAlias):
        CommunicationManagement.SendTerminalString(connAlias,"CLIexit", False)
        CommunicationManagement.Disconnect(connAlias)
    @staticmethod
    def initialize(connAlias,runAppDemo ,initSys):

        CommunicationManagement.SetShellPrompt(connAlias,"/ #")
        print(CommunicationManagement.GetBufferTillPrompt(connAlias,10))
        CommunicationManagement.SetShellPrompt(connAlias,"\n->")
        print(CommunicationManagement.SendCommandAndGetBufferTillPrompt(connAlias,str(runAppDemo) + "\n", 10))
        CommunicationManagement.SetShellPrompt(connAlias,"\nConsole#")
        print(CommunicationManagement.SendCommandAndGetBufferTillPrompt(connAlias,"luaCLI\n", 10))
        print(CommunicationManagement.SendCommandAndGetBufferTillPrompt(connAlias,str(initSys) + "\n", 10))



        # CommunicationManagement.SetShellPrompt("/ #")
        # CommunicationManagement.SendTerminalString("\n\n")
        # CommunicationManagement.SetShellPrompt("->")
        # CommunicationManagement.SendTerminalString("appDemo\n")
        # CommunicationManagement.SetShellPrompt("console#")
        # CommunicationManagement.SendCommandAndGetBufferTillPrompt("luaCLI\n", 2)
        # CommunicationManagement.SendCommandAndGetBufferTillPrompt(str, 5)


    @staticmethod
    def refresh_MacAddress_Table(connAlias, devId):

        patternhead = r'\s+(Index)\s+(Address)\s+(Vlan)\s+(VID1)\s+(Skip)\s+(Interface)\s+(Static)\s+(DA Route)' \
                      r'\s+(saCommand)\s+(daCommand)\s+(sp)\s+'

        pattern = r'(\d+)\s+((?:[0-9A-Fa-f]{2}[:]){5}[0-9A-Fa-f]{2})\s+(\d+)\s+(\d+)\s+(\w+)\s+(\w+\s\d+\/\d+)' \
                  r'\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+'

        response = ""
        response += CommunicationManagement.SendCommandAndGetBufferTillPrompt(connAlias, "show mac address-table all device " + str(devId), 10)

        print ("\n................................. response ................................\n")

        print (response)

        fdbentries = LUACommunication.showtable(patternhead, pattern, response)

        return fdbentries

    @staticmethod
    def verify_Mac_Address_Table(fdbentries):
        smac = "00:00:00:00:00:00"  # mac = FDB_entries[0]["Address"]

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
    def refresh_Events_Table(connAlias, devId):

        patternhead = r'\s+(event type)\s+(counter value)\s+'

        pattern = r'(\w+)\s+(\d+)\s+'

        CommunicationManagement.SendCommandAndGetBufferTillPrompt(connAlias, "debug-mode", 2)
        CommunicationManagement.SetShellPrompt(connAlias,'Console(debug)#')
        response = CommunicationManagement.SendCommandAndGetBufferTillPrompt(connAlias, 'event-table show device ' +
                                                            str(devId) + ' eventType CPSS_PP_EVENTS', 2)


        eventsentries = LUACommunication.showtable(patternhead, pattern, response)

        CommunicationManagement.SendCommandAndGetBufferTillPrompt(connAlias, "exit", 2)
        CommunicationManagement.SetShellPrompt(connAlias,'Console#')

        return eventsentries


    @staticmethod
    def add_allports_2_allvlans(connAlias, devId, vlancount):

        #show port smi-mapping device 0

        CommunicationManagement.SendCommandAndGetBufferTillPrompt(connAlias, "configure", 2)
        CommunicationManagement.SetShellPrompt(connAlias,'Console(config)#')

        CommunicationManagement.SendCommandAndGetBufferTillPrompt(connAlias, "interface range ethernet " + str(devId) + "/0-31", 2)
        CommunicationManagement.SetShellPrompt(connAlias, 'Console(config-if)#')
        #remove default VLAN
        CommunicationManagement.SendCommandAndGetBufferTillPrompt(connAlias, "switchport allowed vlan remove 1", 2)

        for idx in range(1, vlancount):
            CommunicationManagement.SendCommandAndGetBufferTillPrompt(connAlias, "switchport pvid " + str(idx), 2)
            for portIdx in range (1, 32):
                CommunicationManagement.SendCommandAndGetBufferTillPrompt(connAlias, "switchport allowed vlan add " + str(portIdx) + " tagged", 2)

        CommunicationManagement.SendCommandAndGetBufferTillPrompt(connAlias, "exit", 2)
        CommunicationManagement.SetShellPrompt(connAlias, 'Console(config)#')
        CommunicationManagement.SendCommandAndGetBufferTillPrompt(connAlias, "exit", 2)
        CommunicationManagement.SetShellPrompt(connAlias, 'Console#')


    @staticmethod
    def refresh_Vlans_Table(connAlias, devId):

        # response = "VLAN Ports Tag MAC-Learning fdb-lookup-mode" \
        #           "----- ----------------------------------------------------- -------- -------------- --------------" \
        #           "1 0/0-59,64-71,80-82 untagged Control fid"

        patternhead = patternhead = r'\s*(VLAN)\s+(Ports)\s+(Tag)\s+(MAC-Learning)\s+(FDB-mode)'

        pattern = r'(\d)+\s+([\d\/\-,]+)\s+(\w+)\s+(\w+)\s+(\w+)'

        #CommunicationManagement.SendCommandAndGetBufferTillPrompt("config", 2)

        #response = CommunicationManagement.SendCommandAndGetBufferTillPrompt('do show vlan device ' + str(devId), 10)
        CommunicationManagement.SendTerminalString(connAlias, 'do show vlan device ' + str(devId), False)
        response = ""
        #response += CommunicationManagement.GetBuffer(connAlias, 1000)
        response = CommunicationManagement.GetBufferTillPrompt(connAlias, 1000)
        while(response.find("Console") == -1):
            CommunicationManagement.SendTerminalString(connAlias, '\n' + str(devId), False)
            response += CommunicationManagement.GetBuffer(connAlias, 1000)

        print(response)

        eventsentries = LUACommunication.showtable(patternhead, pattern, response)

        CommunicationManagement.SendCommandAndGetBufferTillPrompt(connAlias, "exit", 2)

        return eventsentries


