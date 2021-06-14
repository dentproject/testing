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
class SetupInfoSheetData(object):
    def __init__(self):
        self.key = ""
        self.value = ""
        self.description = ""


class CommonSettings(object):
    def __init__(self):
        self.reboot_mode = SetupInfoSheetData()
        self.device_type = SetupInfoSheetData()


class CommunicationSettings(object):
    def __init__(self):
        self.com_external_cpu = SetupInfoSheetData()
        self.com_internal_cpu = SetupInfoSheetData()


class TGInfo(object):
    def __init__(self):
        self.tg_section_name = SetupInfoSheetData()


class Serial(object):
    def __init__(self, comNum=10, baudrate=115200):
        self.connection_mode = SetupInfoSheetData()
        self.com_number = SetupInfoSheetData()
        self.baudrate = SetupInfoSheetData()
        self.com_number.value = comNum
        self.baudrate.value = baudrate


class Telnet(object):
    def __init__(self, ipAddr, port, timeout=10, uname="", password=""):
        self.ip_address = SetupInfoSheetData()
        self.port = SetupInfoSheetData()
        self.timeout = SetupInfoSheetData()
        self.uname = SetupInfoSheetData()
        self.password = SetupInfoSheetData()
        self.ip_address.value = ipAddr
        self.port.value = port
        self.timeout.value = timeout
        self.uname.value = uname
        self.password.value = password


class Digi_Telnet(object):
    def __init__(self):
        self.connection_mode = SetupInfoSheetData()
        self.digi__ip_address = SetupInfoSheetData()
        self.digi_telnet_port = SetupInfoSheetData()
        self.digi_com__port = SetupInfoSheetData()


class Tgsettings(object):
    def __init__(self):
        self.tg_type = SetupInfoSheetData()
        self.tg_ip = SetupInfoSheetData()
        self.tg_ports = SetupInfoSheetData()


class CPSSUbootEnvironment(object):
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
        self.app_demo_version = SetupInfoSheetData()
        self.cpss_init_system_command_additional_args = SetupInfoSheetData()


class MicroInitProperties(object):
    def __init__(self):
        self.file_path = SetupInfoSheetData()
        self.boot_file_name = SetupInfoSheetData()
        self.super_image_file_name = SetupInfoSheetData()
        self.fast_boot_maximum_configuration_time_seconds = SetupInfoSheetData()


class FileLocationTest(object):
    def __init__(self):
        self.dut_params_path = SetupInfoSheetData()
        self.generic_feature_tables_xls_path = SetupInfoSheetData()
        self.x_modem_app_path = SetupInfoSheetData()


class Debug(object):
    def __init__(self):
        self.pause_onfailed_test = SetupInfoSheetData()
        self.test_log_severity_level = SetupInfoSheetData()


class SetupInfo(object):
    def __init__(self):
        self.serial2 = Serial()
        self.serial1 = Serial()
        self.digi1 = Digi_Telnet()
        self.micro_init_properties = MicroInitProperties()
        self.test_file_location = FileLocationTest()
        self.tg_settings = Tgsettings()
        self.cpss_app_demo_properties = CPSSAppDemoProperties()
        self.common_settings = CommonSettings()
        self.tg_info = TGInfo()
        self.cpss_uboot_environment = CPSSUbootEnvironment()
        self.debug = Debug()
        self.communication_settings = CommunicationSettings()
