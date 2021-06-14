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

class SetupInfoSheetData(object):
    def __init__(self):
        self.key = ""
        self.value = ""
        self.description = ""


class CommonSettings(object):
    def __init__(self):
        self.reboot_mode = SetupInfoSheetData()
        self.devicetype = SetupInfoSheetData()


class CommunicationSettings(object):
    def __init__(self):
        self.dut_commchannel1 = SetupInfoSheetData()
        self.dut_commchannel2 = SetupInfoSheetData()
        self.digi_commchannel1 = SetupInfoSheetData()


class Serial(object):
    def __init__(self):
        self.connection_mode = SetupInfoSheetData()
        self.com_number = SetupInfoSheetData()
        self.baudrate = SetupInfoSheetData()


class Telnet(object):
    def __init__(self):
        self.ip_address = SetupInfoSheetData()
        self.port = SetupInfoSheetData()


class UbootEnvironment(object):
    def __init__(self):
        self.ip_assignment_method = SetupInfoSheetData()
        self.ip_address = SetupInfoSheetData()
        self.netmask = SetupInfoSheetData()
        self.gateway_ip = SetupInfoSheetData()
        self.server_ip = SetupInfoSheetData()
        self.root_path = SetupInfoSheetData()
        self.z_image = SetupInfoSheetData()
        self.fdt_filename = SetupInfoSheetData()


class CPSSAppDemoProperties(object):
    def __init__(self):
        self.appdemo_version = SetupInfoSheetData()
        self.cpss_init_system_command_additional_args = SetupInfoSheetData()


class Debug(object):
    def __init__(self):
        self.pauseonfailedtest = SetupInfoSheetData()


class SetupInfo(object):
    def __init__(self):
        self.common_settings = CommonSettings()
        self.communication_settings = CommunicationSettings()
        self.serial1 = Serial()
        self.serial2 = Serial()
        self.telnet1 = Telnet()
        self.telnet2 = Telnet()
        self.uboot_environment = UbootEnvironment()
        self.cpss_app_demo_properties = CPSSAppDemoProperties()
        self.debug = Debug()


class TGConnectionTableEntry(object):
    def __init__(self):
        self.id = ""
        self.tg_ip = ""
        self.tg_type = ""
        self.tg_card = ""
        self.tg_port = ""
        self.dut_port = ""


class TGConnectionTable(object):
    def __init__(self):
        self.entries = [TGConnectionTableEntry]
        self.entries.pop()

    def __getitem__(self, item):
        return self.entries[item]

    def __iter__(self):
        for entry in self.entries:
            yield entry


class Table2Entry(object):
    def __init__(self):
        self.col1 = ""
        self.col2 = ""
        self.col3 = ""
        self.col3 = ""
        self.col4 = ""


class Table2(object):
    def __init__(self):
        self.entries = [Table2Entry]
        self.entries.pop()

    def __getitem__(self, item):
        return self.entries[item]

    def __iter__(self):
        for entry in self.entries:
            yield entry


class Table3Entry(object):
    def __init__(self):
        self.col1 = ""
        self.col2 = ""
        self.col3 = ""


class Table3(object):
    def __init__(self):
        self.entries = [Table3Entry]
        self.entries.pop()

    def __getitem__(self, item):
        return self.entries[item]

    def __iter__(self):
        for entry in self.entries:
            yield entry


class TGConnectionTableSheet(object):
    def __init__(self):
        self.tg_connection_table = TGConnectionTable()
        self.table2 = Table2()
        self.table3 = Table3()


class DutPortMappingSheetData(object):
    def __init__(self):
        self.logical_port_name = ""
        self.real_port_name = ""


class DutPortMapping(object):
    def __init__(self):
        self._1 = DutPortMappingSheetData()
        self._2 = DutPortMappingSheetData()
        self._3 = DutPortMappingSheetData()
        self._4 = DutPortMappingSheetData()
        self._5 = DutPortMappingSheetData()
        self._6 = DutPortMappingSheetData()
        self._7 = DutPortMappingSheetData()
        self._8 = DutPortMappingSheetData()
        self._9 = DutPortMappingSheetData()
        self._10 = DutPortMappingSheetData()
        self._11 = DutPortMappingSheetData()
        self._12 = DutPortMappingSheetData()
        self._13 = DutPortMappingSheetData()
        self._14 = DutPortMappingSheetData()
        self._15 = DutPortMappingSheetData()
        self._16 = DutPortMappingSheetData()
        self._17 = DutPortMappingSheetData()
        self._18 = DutPortMappingSheetData()
        self._19 = DutPortMappingSheetData()
        self._20 = DutPortMappingSheetData()
        self._21 = DutPortMappingSheetData()
        self._22 = DutPortMappingSheetData()
        self._23 = DutPortMappingSheetData()
        self._24 = DutPortMappingSheetData()
        self._25 = DutPortMappingSheetData()
        self._26 = DutPortMappingSheetData()
        self._27 = DutPortMappingSheetData()
        self._28 = DutPortMappingSheetData()
        self._29 = DutPortMappingSheetData()


class DutPortMapping(object):
    def __init__(self):
        self.dut_port_mapping = DutPortMapping()


class SetupCV(object):
    def __init__(self):
        self.setup_info = SetupInfo()
        self.tg_connection_table_sheet = TGConnectionTableSheet()
        self.dut_port_mapping = DutPortMapping()


