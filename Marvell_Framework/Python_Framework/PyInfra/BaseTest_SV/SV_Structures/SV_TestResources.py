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

from PyInfraCommon.BaseTest.BaseTestStructures.BasetTestResources import Tg_URI, TGConnectionsTable, TestDataCommon
from collections import OrderedDict

import re

class SvTgURI(Tg_URI):
    """
    represents a TG unique resource identifier (URI)
    :type ID: int
    :type type: str
    :type ip: str
    :type card: str
    :type port: str
    :type dutport: str
    """

    def __init__(self, ID=None, ip=None, tgtype=None, card=None, resource_group=None, port=None, dutport=None, phy_mode=None, GeneratorClass=None):
        """
        :param GeneratorClass:
        :type GeneratorClass:TGMappingTableEntry
        """
        super(SvTgURI, self).__init__(ID, ip, tgtype, card, resource_group, port, GeneratorClass)
        self.dutport = dutport
        self.phy_mode = phy_mode

        if GeneratorClass:
            self.dutport = GeneratorClass.dut_port
            self.phy_mode = GeneratorClass.phy_mode

    def Tolist(self):
        """
        :return: current object values as list
        """
        if self.resource_group is None:
            return [self.id, self.ip, self.type, self.card, self.port, self.dutport]
        return [self.id, self.ip, self.type, self.card, self.resource_group, self.port, self.dutport]


class SV_TGMappingCollection(TGConnectionsTable):
    """
    represents the connection table of TG ports
    """

    def __init__(self, uridict):
        super(SV_TGMappingCollection, self).__init__(uridict)
        urinewdict = OrderedDict()
        if isinstance(uridict, list):
            urinewdict = OrderedDict((v.id, SvTgURI(GeneratorClass=v)) for v in uridict)
        elif isinstance(uridict, dict):
            urinewdict = uridict
        for k, v in list(urinewdict.items()):
            # cast float to int
            if not isinstance(k, (int, float)):
                if re.match("^\d+?\.\d+?$", k) is not None:
                    v1 = urinewdict.pop(k, None)
                    k = int(float(k))
                    urinewdict[k] = v1
        self.entries = urinewdict  # type: dict[int,SvTgURI]

    def Gen_Pretty_Table(self):
        """
        print the connection table as formatted table
        :return:
        """
        from prettytable import PrettyTable
        self._pretty_table = PrettyTable()
        if len(self.entries) > 0:
            if list(self.entries.values())[0].resource_group is None:
                self._pretty_table.field_names = ["ID", "IP Address", "TG Type", "Card", "Port", "Dut Port"]
            else:
                self._pretty_table.field_names = ["ID", "IP Address", "TG Type", "Card", "Resource Group", "Port", "Dut Port"]
            for connTblRow in list(self.entries.values()):  # type: SvTgURI
                self._pretty_table.add_row(connTblRow.Tolist())
            self._pretty_table.title = "TG Mapping Table"