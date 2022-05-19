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

from collections import OrderedDict

from Marvell.ResourceManagement.ResourceManagerLayer.TG_Settings import TGConnectionTableEntry, TG_ConnectionTable
from UnifiedTG.Unified.TGEnums import TGEnums

from PyInfra.BaseTest_SV.SV_Enums.AppTypes import AppType
from PyInfra.BaseTest_SV.SV_Enums.BoardRebootMode import BoardRebootMode
from PyInfra.BaseTest_SV.SV_Setup.SV_Setup import SetupInfo
from PyInfra.DutManagers.SvDut import BaseSvDutManager
from PyInfra.Globals.AppType.AppType import AppTypeGlobal
from PyInfraCommon.BaseTest.BaseTest import BaseTest
from PyInfraCommon.BaseTest.BaseTestEnums.TestTypesEnums import TestValidationGroup
from PyInfraCommon.BaseTest.BaseTestExceptions import TestCrashedException
from PyInfraCommon.BaseTest.BaseTestStructures.BasetTestResources import PDUSettings
from PyInfraCommon.ExternalImports.Communication import PyBaseComWrapper
from PyInfraCommon.ExternalImports.ResourceManager import ConfigManager, ResourceManager
from PyInfraCommon.GlobalFunctions.Utils.Exception import GetStackTraceOnException
from PyInfraCommon.GlobalFunctions.Utils.Function import GetFunctionName
from PyInfraCommon.Managers.SNMP.SNMPTools import SnmpProtocolVersion

from PyInfraCommon.Globals.Logger.GlobalTestLogger import GlobalLogger

class BaseTest_SV(BaseTest):
    """
    BaseTest for SwitchDev Validation Tests
    """

    def __init__(self, SuiteName, useTG=True):
        super(BaseTest_SV, self).__init__()
        from PyInfra.BaseTest_SV.SV_Enums.AppTypes import AppType
        from PyInfra.Globals.AppType.AppType import AppTypeGlobal
        AppTypeGlobal.type = AppType.Undefined
        self.TestData.TestInfo.Suite_Name = SuiteName
        self.TestData.TestInfo._UseTG = useTG
        self.DutMainChannelStr = ""
        self.DutSecondayChannelStr = ""
        self.DutMainChannel = None  # type: PyBaseComWrapper
        self.DutSecondayChannel = None
        self.OtherDutChannel = None
        self.SetupXlsPath = ''
        self.DutManager = None  # type: BaseSvDutManager
        self.OtherDutManager = None  # type: BaseSvDutManager
        self.DutSecondayManager = None # type: BaseSvDutManager
        self._forced_setup_path = None
        self._forced_setup_list_path = None
        self._HandleCommandLineArgs()
        self.setup_sheet_name = ''

    def _SetTestType(self):
        """
        sets the test type and validation group client that uses this class
        :return:
        """
        self.TestData.TestInfo._TestValidationGroup = TestValidationGroup.SV

    def _UpdatedPDUSettings(self, ExcelSetupRef):
        """
        Fills PDU settings from Excel Sheet Setup reference
        :param ExcelSetupRef: SetupInfo generated class
        :type ExcelSetupRef:SetupInfo
        :return:dict of pdu settings
        :rtype:dict
        """
        key_prefix = "pdu_settings"
        pdu_settings_keys = [k for k in ExcelSetupRef.__dict__.keys() if key_prefix in k]
        pdu_settings_parsed = OrderedDict()
        for pdu_settings_key in pdu_settings_keys:
            pdu_settings_obj = PDUSettings()
            if ExcelSetupRef.__dict__[pdu_settings_key].ip_address.value:
                pdu_settings_obj.ip_address = ExcelSetupRef.__dict__[pdu_settings_key].ip_address.value
                pdu_settings_obj.outlet = ExcelSetupRef.__dict__[pdu_settings_key].outlet_name.value
            pdu_settings_obj._community_rw = ExcelSetupRef.__dict__[pdu_settings_key].community_rw.value
            if "snmpv1" in ExcelSetupRef.__dict__[pdu_settings_key].snmp_version.value.lower():
                pdu_settings_obj._snmp_version = SnmpProtocolVersion.v1
            elif "snmpv2" in ExcelSetupRef.__dict__[pdu_settings_key].snmp_version.value.lower():
                pdu_settings_obj._snmp_version = SnmpProtocolVersion.v2
            elif "snmpv3" in ExcelSetupRef.__dict__[pdu_settings_key].snmp_version.value.lower():
                pdu_settings_obj._snmp_version = SnmpProtocolVersion.v3
            pdu_settings_obj._auth_protocol_rw = \
                ExcelSetupRef.__dict__[pdu_settings_key].auth_protocol_rw.value
            pdu_settings_obj._password_rw = \
                ExcelSetupRef.__dict__[pdu_settings_key].password_rw.value
            pdu_settings_obj._privacy_protocol_rw = \
                ExcelSetupRef.__dict__[pdu_settings_key].privacy_protocol_rw.value
            pdu_settings_obj._username_rw = ExcelSetupRef.__dict__[pdu_settings_key].username_rw.value
            # strip key prefix and leave only unique key
            stripped_key = "".join(pdu_settings_key.split(key_prefix))
            stripped_key = stripped_key.replace("_","")
            if not stripped_key:
                stripped_key = "1" # for single PDU
            if stripped_key.isdigit():
                stripped_key= int(stripped_key)
            pdu_settings_parsed[stripped_key]= pdu_settings_obj

        if len(pdu_settings_parsed) == 1:
            # for backward compatibility
            self.TestData.Resources.Settings.PduSettings = list(pdu_settings_parsed.values())[0]
        elif len(pdu_settings_parsed) > 1:
            for i,k in enumerate(sorted(list(pdu_settings_parsed.keys()))):
                if i == 0:
                    self.TestData.Resources.Settings.PduSettings = pdu_settings_parsed[k]
                self.TestData.Resources.Settings.MultiplePDUSettings[k] = pdu_settings_parsed[k]

    def DiscoverTestResources(self):
        """
        this method discovers all Test Data and Resources and registers them
        in the parent base class TestData Member which in turn Acquires the resources
        :return:
        """
        funcname = GetFunctionName(self.DiscoverTestResources)
        self.SetupXlsPath = self.GetSetupXLSPath()
        manager = ConfigManager()
        setup_sheet_name = "SetupInfo"
        tg_sheet_name = "TG_ConnectionTable"
        self.setup_sheet_name = setup_sheet_name
        self.tg_sheet_name = tg_sheet_name
        SvSetup = SetupInfo()
        ####################TG Settings###########################
        TGConTable = TG_ConnectionTable()
        try:
            TGConTable = manager.get_obj(tg_sheet_name, self.SetupXlsPath, ret_obj=TGConTable)
        except Exception as ex:
            e = GetStackTraceOnException(ex)
            raise TestCrashedException(
                funcname + "failed to read {s} sheet from {p}:\n{e}".format(s=tg_sheet_name, p=self.SetupXlsPath, e=e))
        try:
            SvSetup = manager.get_obj(setup_sheet_name, self.SetupXlsPath, ret_obj=None)  # type: SetupInfo
        except Exception as ex:
            e = GetStackTraceOnException(ex)
            raise TestCrashedException(
                funcname + "failed to read {s} sheet from {p}:\n{e}".format(s=setup_sheet_name, p=self.SetupXlsPath,
                                                                            e=e))

        if TGConTable:
            from PyInfra.BaseTest_SV.SV_Structures.SV_TestResources import SV_TGMappingCollection
            self.TGManager.connection_table = SV_TGMappingCollection(TGConTable.tg_connection_table.entries)
            # Update TG Reset and Polling Settings - we dont reset L1 settings between tests to avoid L1 missing configuration
            if self.TG.settings.port_cleanup_settings.clear_all_streams is None:
                self.TG.settings.port_cleanup_settings.clear_all_streams = True
            self.TG.settings.tcl_server_mode = SvSetup.tg_settings.ixia_tcl_server_mode.value
            if self.TG.settings.tcl_server_mode == "Remote" and SvSetup.tg_settings.remote_tcl_server.value:
                self.TG.settings.tcl_server_ip = SvSetup.tg_settings.remote_tcl_server.value
            if SvSetup.tg_settings.tg_client_path.value:
                self.TG.settings.tg_client_path = SvSetup.tg_settings.tg_client_path.value

        elif TGConTable is None and self.TestData.TestInfo._UseTG:
            col_names = [k for k in list(TGConnectionTableEntry.__dict__.keys()) if not k.startswith("_")]
            err = funcname + "failed to read TG Connection Table sheet from excel {}, please check that TG Connection " \
                             "Table column names match to {}".format(self.SetupXlsPath, col_names)
            raise TestCrashedException(err)
        # Setup Info Tab
        if SvSetup:
            self._SvSetup = SvSetup
            ##########################Communication Settings#################################

            from PyInfraCommon.BaseTest.BaseTestStructures.BasetTestResources import CommunicationSettings
            a = CommunicationSettings()
            a.auto_connect_channel = False
            #  Register Communication Settings Keys , the actual channel will be acquired in CliCommandBaseClass
            if SvSetup.communication_settings.dutmainchannel.value:
                self.DutMainChannelStr = SvSetup.communication_settings.dutmainchannel.key
                self.TestData.Resources.Settings.CommunicationSetting[self.DutMainChannelStr] = a
            if SvSetup.communication_settings.dutsecondaychannel.value:
                self.DutSecondayChannelStr = SvSetup.communication_settings.dutsecondaychannel.key
                self.TestData.Resources.Settings.CommunicationSetting[self.DutSecondayChannelStr] = a
            if SvSetup.communication_settings.otherchannel.value:
                self.OtherDutChannelStr = SvSetup.communication_settings.otherchannel.key
                self.TestData.Resources.Settings.CommunicationSetting[self.OtherDutChannelStr] = a

            #################################PDU Settings#######################################
            self._UpdatedPDUSettings(self._SvSetup)


    def _UpdateDutManagerInfo(self, DutManagerRef, ExcelSetupRef, pduNum = None):
        """
        updates input Dut Manager Info
        :param DutManagerRef:BaseSvDutManager reference
        :type DutManagerRef:BaseSvDutManager
        :param ExcelSetupRef: SetupInfo generated class
        :type ExcelSetupRef:SetupInfo
        :return:
        :rtype:
        """

        funcname = GetFunctionName(self._UpdateDutManagerInfo)
        # update dut manager environment
        if ExcelSetupRef.common_settings.reboot_mode.value:
            if "hardware" in ExcelSetupRef.common_settings.reboot_mode.value.lower():
                DutManagerRef._board_reboot_mode = BoardRebootMode.Hardware
            elif "software" in ExcelSetupRef.common_settings.reboot_mode.value.lower():
                DutManagerRef._board_reboot_mode = BoardRebootMode.Software

        if ExcelSetupRef.common_settings.apptype.value:
            if "xps" in ExcelSetupRef.common_settings.apptype.value.lower():
                DutManagerRef.appType = AppType.XPS
                AppTypeGlobal.type = AppType.XPS
            elif "sai" in ExcelSetupRef.common_settings.apptype.value.lower():
                DutManagerRef.appType = AppType.SAI
                AppTypeGlobal.type = AppType.SAI
            elif "switchdev" in ExcelSetupRef.common_settings.apptype.value.lower():
                DutManagerRef.appType = AppType.SwitchDev

        if ExcelSetupRef.common_settings.devicetype.value:
            self.TestData.DutInfo.ASIC = ExcelSetupRef.common_settings.devicetype.value

        if pduNum:
            DutManagerRef.PDU = self.MultiplePDU_dict.get(pduNum)
        elif self.PDU:
            DutManagerRef.PDU = self.PDU

    def SpecificTestInit(self):
        """
        This method is called before the test is run by _TestInit()
        it runs after _BasicTestInit() in Parent class
        It should initialize any specific test required resources and
        execute specific test init actions
        :return:
        """

        GlobalLogger.logger = self.logger  # copy test logger to Global Logger object


class BaseTest_SV_API(BaseTest_SV):
    """
    :param testClass
    :type testClass: BaseTest_SV
    """

    def __init__(self, testClass):
        self._testClassref = testClass

    def TestPreRunConfig(self):
        pass

    def InitTestParams(self, testparams_class):
        """
        saves the specific testparams class you implement in each test case flow in APIs
        if some params requires additional parsing then you need to ovveride this method in Test APIs
        call to super and add your logic there that parses the params
        :param testparams_class:
        :type testparams_class:
        :return:
        :rtype:
        """
        self.TestParams = testparams_class

    def TestProcedure(self):
        pass

    def FailTheTest(self, errmsg, abort_Test=True):
        self._testClassref.FailTheTest(errmsg, abort_Test)

    def Add_Cleanup_Function_To_Stack(self, func, *args, **kwargs):
        self._testClassref.Add_Cleanup_Function_To_Stack(func, *args, **kwargs)

    def Add_Debug_Function_To_Stack_Per_Step(self, step_num, func, *args, **kwargs):
        self._testClassref.Add_Debug_Function_To_Stack_Per_Step(step_num, func, *args, **kwargs)

    @property
    def logger(self):  # type: () -> BaseTestLogger
        return self._testClassref.logger
