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

from builtins import object
from collections import OrderedDict
import re

import prettytable
from prettytable import PrettyTable

from PyInfraCommon.BaseTest.BaseTestStructures.Types import TestDataCommon
from PyInfraCommon.BaseTest.BaseTestStructures.TGConnectionTable_Excel import TGConnectionTableEntry
from PyInfraCommon.BaseTest.BaseTestStructures.Setup_TGMapping import TGMappingTableEntry
from PyInfraCommon.GlobalFunctions.Utils.IP import IpUtils
from PyInfraCommon.Managers.PowerDistributionUnit.PDUSocket import PduSocket
from PyInfraCommon.ExternalImports.Communication import PySerialComWrapper , PyTelnetComWrapper , PyBaseComWrapper
from PyInfraCommon.ExternalImports.TG import TGPort,utg
# from PyInfraCommon.Managers.MaxTcManager import MaxTC

class LinkPartnerTG(object):
    # def __init__(self, tg_id=None, tg_port=None, tg_uri=None):
    def __init__(self, tg_id=None, tg_uri=None, tg_port=None):
        """
        :param tg_id: TG identifier
        :type tg_id: int
        :param tg_uri: TG uri
        :type tg_uri: Tg_URI
        :param tg_port: TGPort object
        :type tg_port: TGPort

        """
        self.TgID = tg_id
        self.TgURI = tg_uri
        self.TGPort = tg_port

    def __str__(self):
        return "TG-{id} {info}".format(id=self.TgID, info="({type}-{uri})".format(type=self.TgURI.type, uri=self.TgURI.frindley_str()))

    def __eq__(self, other):
        return self.TGPort._port_name == other.TGPort._port_name

class BaseTestResourcesSettings(object):
    """
    :type TG: TG_Configuration
    :type CommunicationSetting: OrderedDict[str,CommunicationSettings]
    """
    def __init__(self):
        self.CommunicationSetting = OrderedDict()   # type: OrderedDict[str,CommunicationSettings]
        self.PduSettings = PDUSettings()
        self.MultiplePDUSettings = MultiplePDUSettings()
        self.LogSettings = LogSettings()
        self.TG = TG_setup()
        self.MaxTCSettings = MaxTcSettings()


class TG_setup(object):
    def __init__(self):
        self.ResetTGPortsOnConnect = False
        self.PollTGPortsOnConnect = False
        self.IxiaTclServerMode = "Chassis"
        self.ConnectionTable = None  # type: TGConnectionsTable


class Tg_URI(object):
    """
    represents a TG unique resource identifier (URI)
    :type ID: int
    :type type: str
    :type ip: str
    :type card: str
    :type port: str
    :type dutport: str
    """

    def __init__(self, ID=None, ip=None, tgtype=None, card=None, resource_group=None, port=None, GeneratorClass=None):
        """
        :param GeneratorClass:
        :type GeneratorClass:TGMappingTableEntry
        """
        self.id = ID
        self.type = tgtype
        self.ip = ip
        self.card = card
        self.resource_group = resource_group
        self.port = port

        if self.type and "ostinato" in self.type.lower():
            if IpUtils.IsValidIP(port):
                self.port = port

        if GeneratorClass:
            self.id = GeneratorClass.id
            if not isinstance(GeneratorClass.id,(int,float)):
                self.id = int(GeneratorClass.id.split(".")[0])
            self.type = GeneratorClass.tg_type
            self.ip = GeneratorClass.tg_ip
            self.card = GeneratorClass.tg_card
            if not isinstance(GeneratorClass.tg_card, (int, float)):
                self.card = GeneratorClass.tg_card.split(".")[0]
            if hasattr(GeneratorClass,"resource_group"):
                self.resource_group = GeneratorClass.resource_group
                if not isinstance(GeneratorClass.resource_group, (int, float)):
                    self.resource_group = GeneratorClass.resource_group.split(".")[0]
            self.port = GeneratorClass.tg_port
            if not isinstance(GeneratorClass.tg_port, (int, float)):
                self.port = GeneratorClass.tg_port.split(".")[0]
            if "ostinato" in self.type.lower():
                if IpUtils.IsValidIP(GeneratorClass.tg_port):
                    self.port = GeneratorClass.tg_port


    def __str__(self):
        ret = ""
        if self.type is not None:
            if "ostinato" not in self.type.lower():
                card_Str = self.card  # if self.resource_group is None else "RG{}/{}".format(self.resource_group,self.card)
                ret = "{}:{}/{}/{}".format(self.id, self.ip, card_Str, self.port)
            else:
                ret = "{}:{}/{}/{}".format(self.id, 0, 0, self.port)
        return ret
    
    def frindley_str(self):
        ret = ""
        if self.type is not None:
            ret = "{}:{}.{}".format(self.ip, self.card, self.port)
        return ret

    
    def Tolist(self):
        """
        :return: current object values as list
        """
        if self.resource_group is None:
            return [self.id, self.ip, self.type, self.card, self.port]
        return [self.id, self.ip, self.type, self.card, self.resource_group, self.port]

class TGMappingCollection(TestDataCommon):
    """
    represents the connection table of TG ports
    """

    def __init__(self, uridict):
        super(TGMappingCollection, self).__init__()
        urinewdict = OrderedDict()
        if isinstance(uridict, list):
            urinewdict = OrderedDict((v.id, Tg_URI(GeneratorClass=v)) for v in uridict)
        elif isinstance(uridict, dict):
            urinewdict = uridict
        for k, v in list(urinewdict.items()):
            # cast float to int
            if not isinstance(k, (int, float)):
                if re.match("^\d+?\.\d+?$", k) is not None:
                    v1 = urinewdict.pop(k, None)
                    k = int(float(k))
                    urinewdict[k] = v1
        self.entries = urinewdict  # type: dict[int,Tg_URI]

    def Gen_Pretty_Table(self):
        """
        print the connection table as formatted table
        :return:
        """
        from prettytable import PrettyTable
        self._pretty_table = PrettyTable()
        if len(self.entries) > 0:
            if list(self.entries.values())[0].resource_group is None:
                self._pretty_table.field_names = ["ID", "IP Address", "TG Type", "Card", "Port"]
            else:
                self._pretty_table.field_names = ["ID", "IP Address", "TG Type", "Card", "Resource Group", "Port"]
            for connTblRow in list(self.entries.values()):  # type: Tg_URI
                self._pretty_table.add_row(connTblRow.Tolist())
            self._pretty_table.title = "TG Mapping Table"

class TGConnectionsTable(TestDataCommon):
    """
    represents the connection table of TG ports
    """
    def __init__(self, uridict):
        super(TGConnectionsTable, self).__init__()
        urinewdict = OrderedDict()
        if isinstance(uridict,list):
            urinewdict = OrderedDict((v.id,Tg_URI(GeneratorClass=v)) for v in uridict)
        elif isinstance(uridict,dict):
            urinewdict = uridict
        for k,v in list(urinewdict.items()):
            # cast float to int
            if not isinstance(k,(int,float)):
                if re.match("^\d+?\.\d+?$", k) is not None:
                    v1 = urinewdict.pop(k, None)
                    k = int(float(k))
                    urinewdict[k] = v1
        self.entries = urinewdict # type: dict[int,Tg_URI]
        
    def Gen_Pretty_Table(self):
        """
        print the connection table as formatted table
        :return:
        """
        from prettytable import PrettyTable
        self._pretty_table = PrettyTable()
        if len(self.entries) > 0:
            # l1_titles = ["Port Speed","Port Mode","Port Fec Mode","Use PortManager"] if self.entries.values()[0].l1_port_speed else []
            l1_titles = ["Port Speed","Port Mode","Port Fec Mode"] if list(self.entries.values())[0].l1_port_speed else []
            if list(self.entries.values())[0].resource_group is None:
                self._pretty_table.field_names = ["ID","IP Address","TG Type","Card","Port","Dut Port"] +l1_titles
            else:
                self._pretty_table.field_names = ["ID","IP Address","TG Type","Card","Resource Group","Port","Dut Port"] + l1_titles
            for connTblRow in list(self.entries.values()):  # type: Tg_URI
                # use_pm =  True if self.TestData.TestInfo.PortConfigurationMethod == ConfigurationMethodEnum.PM else False
                # row_elements = connTblRow.Tolist().extend()
                self._pretty_table.add_row(connTblRow.Tolist())
            self._pretty_table.title = "TG Connection Table"


class SerialSettings(TestDataCommon):
    def __init__(self):
        super(SerialSettings, self).__init__(table_title= "Communication Settings")
        self.com_number = None
        self.baud_rate = None

class TelnetSettings(TestDataCommon):
    def __init__(self):
        super(TelnetSettings, self).__init__(table_title="Communication Settings")
        self.ip_address = ""
        self.telnet_port = 23


class CommunicationSettings(object):
    """
    :type Channel: PyComWrapper
    """
    def __init__(self, comm_channel=None):
        # type: (PyBaseComWrapper) -> None
        self.settings = None
        self.auto_connect_channel = True
        if comm_channel:
            self.UpdateSettings(comm_channel)

    def UpdateSettings(self,Channel = None):
        # type: (PyBaseComWrapper) -> None
        # update new channel
        if Channel:
            self.Channel = Channel
        # if current used channel is not None
        if self.Channel:
            if isinstance(self.Channel,PySerialComWrapper):
                self.settings = SerialSettings()
                self.settings = SerialSettings ( )
                if hasattr ( self.Channel , "_commType" ):
                    self.settings.commType = self.Channel._commType
                if hasattr ( self.Channel , "_baudrate" ):
                    self.settings.baud_rate = self.Channel._baudrate
                if hasattr ( self.Channel , "_port" ):
                    self.settings.com_number = self.Channel._port
            elif isinstance(self.Channel,PyTelnetComWrapper):
                self.settings = TelnetSettings ( )
                if hasattr ( self.Channel , "_commType" ):
                    self.settings.commType = self.Channel._commType
                if hasattr ( self.Channel , "_host" ):
                    self.settings.ip_address = self.Channel._host
                if hasattr ( self.Channel , "_port" ):
                    self.settings.telnet_port = self.Channel._port


class BaseTestResources(object):
    """
    :type logger: BaseTestLogger
    :type Settings: BaseTestResourcesSettings
    :type Channels: dict[str,PyBaseComWrapper]
    :type PDU: PduSocket
    :type MaxTC: MaxTC
    """
    def __init__(self):
        from PyInfraCommon.BaseTest.BaseTest import BaseTest
        self.TG = None  # type: BaseTest._TGManager
        self.logger = None
        self.Settings = BaseTestResourcesSettings()
        self.Channels = {}
        self.PDU = None
        self.MaxTC = None


class PDUSettings(TestDataCommon):
    """
    Represents Power Distribution Unit Settings (PDU)
    :type _snmp_version: SnmpProtocolVersion
    """
    def __init__(self):
        super(PDUSettings, self).__init__(table_title ="PDU Settings")
        from PyInfraCommon.Managers.SNMP.SNMPTools import SnmpProtocolVersion, USMAuthProtocol, USMPrivProtocol
        self.Connect_To_PDU = True
        self._snmp_version = None
        self.ip_address = ""
        self.outlet = ""
        self._community_rw = ""
        self._username_rw = ""  # for SNMPv3 only
        self._password_rw = ""  # for SNMPv3 only
        self._privacy_protocol_rw = USMAuthProtocol.usm_NoAuth  # for SNMPv3 only
        self._auth_protocol_rw = USMPrivProtocol.usm_3DES    # for SNMPv3 only


class MultiplePDUSettings(object):

    def __init__(self):
        self.__odict = OrderedDict()  # type: dict[int,TGPort]
        self._pretty_table = PrettyTable()
        self._pretty_table_keys = [k for k in PDUSettings().__dict__.keys() if not k.startswith("_")]

    def is_pretty_table_generated(self):
        """
        :return: TRUE if self pretty table object was already generated
        """
        return self._pretty_table and self._pretty_table._rows


    def Gen_Pretty_Table(self):
        self._pretty_table = PrettyTable()
        for k,v in self.__odict.items():
            row = [k]
            for key in self._pretty_table_keys:
                row.append(v.__dict__.get(key))
            self._pretty_table.add_row(row)

        self._pretty_table.field_names = ["id"]+ self._pretty_table_keys
        self._pretty_table.hrules = prettytable.ALL
        self._pretty_table.align = "l"
        self._pretty_table.title = "PDU Settings"

    def __str__(self):
        ret = ""
        if not self.is_pretty_table_generated():
            self.Gen_Pretty_Table()
        ret = self._pretty_table.get_string()
        return ret

    def To_HTML_Table(self):
        """
        generate self attributes representation in HTML Table format
        :return: HTML string of a table of self attributes
        :rtype: str
        """
        ret = ""
        if not self.is_pretty_table_generated():
            self.Gen_Pretty_Table()
        ret = self._pretty_table.get_html_string(format=True)
        return ret
    def __getitem__(self, item):
        # type:(object)->TGPort
        if isinstance(item, int):
            return self.__odict[str(item)]
        elif isinstance(item, str):
            return self.__odict[item]

    def __setitem__(self, key, value):
            self.__odict[key] = value

    def __len__(self):
        return len(self.__odict)

    def items(self):
        return self.__odict.items()

    def keys(self):
        return self.__odict.keys()

    def values(self):
        return self.__odict.values()

    def get(self, k):
        return self.__odict.get(k)



class LogSettings(object):
    """
    Log file settings for BaseTest to use before init log
    :type LoggingFormat:
    """
    def __init__(self):
        self.logging_format = None
        self.logging_level = None

class MaxTcSettings(TestDataCommon):
    """
    Max TC Settings
    """
    def __init__(self):
        super(MaxTcSettings, self).__init__(table_title="Max TC Settings")
        self.ip_address = ""
        self.device_id = 0
        self.auto_connect = False

