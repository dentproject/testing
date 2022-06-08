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

import os

from PyInfraCommon.BaseTest.BaseTestStructures.Types import TestDataCommon
from PyInfraCommon.BaseTest.BaseTestEnums.LogSeverityEnums import LogSeverityEnum
from PyInfraCommon.BaseTest.BaseTestEnums.TestReultTypeEnums import TestReultTypeEnums
from PyInfraCommon.BaseTest.BaseTestEnums.TestTypesEnums import TestTypesEnums,TestValidationGroup
from PyInfraCommon.BaseTest.BaseTestEnums.TestFamilyeEnums import TestFamilyeEnums
# from PyInfraCommon.BaseTest.BaseTestEnums.L1ConfigurationEnums import L1ConfigurationMethodEnum

class BaseTestInfo(TestDataCommon):
    """
    Class That holds all test relevant test information
    :type _TestType: TestTypesEnums
    :type _TestFamily: TestFamilyeEnums
    :type _RaiseExceptionOnFail: bool
    :type _PauseOnTestFail: bool
    :type LoggingLevel : str
    :type _TestResultEnum: TestReultTypeEnums
    :type _TestIntResult: bool
    :type _UseTG: bool

    """
    def __init__(self):
        super(BaseTestInfo,self).__init__(table_title="Test Information")
        self.Suite_Name = ""
        self.Test_Name = ""
        self.Result = ""
        self._Result_Message = ""
        self._Result_Short_Message = ""
        self._Result_Short_Message_Type = "FAIL"
        self.start_time = ""
        self.end_time = ""
        self.run_time = None
        self._TestType = TestTypesEnums.Unknown
        self._TestValidationGroup = TestValidationGroup.Unknown
        self._TestFamily = TestFamilyeEnums.tfe_Uninitilized
        self._RaiseExceptionOnFail = True
        self._PauseOnTestFail = False
        self._TestResultEnum = None
        self._TestIntResult = None
        self._UseTG = True
        self._start_time_unit = None
        self._end_time_unit = None
        self._TestExceptionCaught = False
        self._TestExceptionHandled = False
        self._TestExceptionObj = None
        pc_name = os.getenv('HOST', os.getenv('COMPUTERNAME'))  #Linux=Host Windows=Computername
        self.test_station_name = pc_name
        # self.PortConfigurationMethod = L1ConfigurationMethodEnum.Unknown