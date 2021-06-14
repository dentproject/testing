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
        self.apptype = SetupInfoSheetData()
        self._board_reboot_mode = SetupInfoSheetData()
        self.devicetype = SetupInfoSheetData()
        self.board_type = SetupInfoSheetData()
        self.runmode = SetupInfoSheetData()


class CommunicationSettings(object):
    def __init__(self):
        self.dutmainchannel = SetupInfoSheetData()
        self.dutsecondaychannel = SetupInfoSheetData()
        self.otherchannel = SetupInfoSheetData()

class Serial(object):
    def __init__(self):
        self.com_number = SetupInfoSheetData()

class Telnet(object):
    def __init__(self):
        self.ip_address = SetupInfoSheetData()
        self.port = SetupInfoSheetData()

class SSH1(object):
    def __init__(self):
        self.ip_address = SetupInfoSheetData()
        self.port = SetupInfoSheetData()
        self.uname = SetupInfoSheetData()
        self.password = SetupInfoSheetData()
        self.timeout = SetupInfoSheetData()

class PDUSettings(object):
    def __init__(self):
        self.snmp_version = SetupInfoSheetData()
        self.ip_address = SetupInfoSheetData()
        self.outlet_name = SetupInfoSheetData()
        self.community_rw = SetupInfoSheetData()
        self.username_rw = SetupInfoSheetData()
        self.password_rw = SetupInfoSheetData()
        self.privacy_protocol_rw = SetupInfoSheetData()
        self.auth_protocol_rw = SetupInfoSheetData()

class TestEnvironment(object):
    def __init__(self):
        self.pauseonfailedtest = SetupInfoSheetData()
        self.log_severity = SetupInfoSheetData()
        self.log_file_format = SetupInfoSheetData()


class TGSettings(object):
    def __init__(self):
        self.ixia_tcl_server_mode = SetupInfoSheetData()
        self.remote_tcl_server = SetupInfoSheetData()
        self.tg_client_path = SetupInfoSheetData()


class MaxTCSettings(object):
    def __init__(self):
        self.ip_address = SetupInfoSheetData()
        self.device_id = SetupInfoSheetData()


class SetupInfo(object):
    def __init__(self):
        self.serial2 = Serial()
        self.serial1 = Serial()
        self.test_environment = TestEnvironment()
        self.telnet2 = Telnet()
        self.telnet1 = Telnet()
        self.ssh1 = SSH1()
        self.ssh2 = SSH1()
        self.tg_settings = TGSettings()
        self.pdu_settings = PDUSettings()
        self.maxtc_settings = MaxTCSettings()
        self.common_settings = CommonSettings()
        self.communication_settings = CommunicationSettings()


