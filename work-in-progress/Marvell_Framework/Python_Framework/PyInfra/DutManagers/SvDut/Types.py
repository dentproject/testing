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
from datetime import datetime

from enum import Enum

from PyInfraCommon.BaseTest.BaseTestStructures.Types import TestDataCommon
from PyInfraCommon.GlobalFunctions.Serialize import JSONSerializable


class DutAppMode(Enum):
    """
    Run Mode of the Board -
    """
    Undefined = -1
    WhiteMode = 0 # indicate a simulation environment
    BlackMode = 1 # indicate that we are using a real board


class ASICType(Enum):
    """
    this class represents all ASIC (PP) Family Types of Marvell
    class 0200 of PCI on linux
    """
    Unset = -1
    Pipe = 0
    AC3 = 1
    PonCat3 = 1
    Lion2 = 2
    Hooper = 3
    BC2 = 4
    BC3 = 5
    Cetus = 6
    Caelum = 7
    Aldrin = 8
    Armstrong = 9
    Aldrin2 = 10
    Falcon = 11
    AC3X = 12
    XCat3Plus = 13
    BV = 14
    Falcon2 = 15
    Aldrin3 = 16
    Pipe_AC3X = 17  # mixed board type
    Raven = 18
    Hawk = 19
    AC5 = 20
    AC5X = 21

class DutChannelType(Enum):
    UNSET = -1
    TELNET = 0
    SERIAL = 1
    SSH = 2


class SvBoard(JSONSerializable):
    """
    represents a CPSS Board with all relevant applications
    this class gets serialized to file and de-serialized from file
    :type pplist: list[CpssPP]
    :type
    """
    def __init__(self, asic_type=None,boardType=None):
        """
        :param PP: represents a PP (ASIC) device instance
        :type PP: list[CpssPP]
        :param boardType:  the board type
        :type boardType: CpssBoardType
        """
        self.setup_excel_path = ""
        self.linux_version = None  # TODO: get this when init linux dut?
        self.AppSwVersion = ""  # the relevant app version
        self.uboot_version = ""
        self.appMode = DutAppMode.Undefined
        self.board_type = None # each project will set this value according to it own convention
        self.asic_type = asic_type  # type: ASICType
        self._is_detected = False  # indicates if this board was already detected or not
        self._dut_info_file_path = None  # if specified will return this path instead of the default path
        self._dut_info_file_max_lifetime_seconds = 60 * 60 * 24 * 3  # 3 days in seconds

    @property
    def is_detected(self):
        return self._is_detected

    @is_detected.setter
    # if this flag was changed frmo False to True then we trigger saving this class to json file
    def is_detected(self, detected):

        if detected and not self._is_detected:
            self.save_to_file()
        self._is_detected = detected

    def save_to_file(self):
        self.toJSON(self._get_dutinfo_file_path())

    def _get_dutinfo_file_path(self):
        """
        returns the default file path to use (if _serialize_path is not set) to save serialized data of this class
        :return: file name with path  in %APPDATA%
        :rtype:str
        """
        if self._dut_info_file_path:
            return self._dut_info_file_path
        # build file name base on the file path so it will be always be uniqe per each path
        tmp = os.path.split(self.setup_excel_path)
        filename = "cv_dut_info.json"
        if tmp:
            setup_file_name = tmp[1].split(".")[0]
            setup_file_dir = os.path.basename(tmp[0])
            filename = "{a}_{b}_cv_dut_info.json".format(a=setup_file_dir, b=setup_file_name)
        self._dut_info_file_path = os.path.join(os.getenv('APPDATA', '/tmp'), filename)
        return self._dut_info_file_path

    def restore_class_from_file(self, path=None, validate=True):
        """
        restores the class data from json file (deserialize)
        :param path: if specified will try to restore from this path, else will use default path
        :type path: str
        :return: True on success or False otherwise
        :rtype: bool
        """
        ret = True
        if path:
            if validate:
                if self.is_dut_info_file_valid(path):
                    ret = self.fromJson(self._dut_info_file_path)
                else:
                    ret = False
            else:
                ret = self.fromJson(self._dut_info_file_path)
        else:
            self._get_dutinfo_file_path()
            if validate:
                if self.is_dut_info_file_valid():
                    ret = self.fromJson(self._dut_info_file_path)
                else:
                    ret = False
            else:
                ret = self.fromJson(self._dut_info_file_path)
        self._is_detected = ret
        return ret

    def is_dut_info_file_valid(self, path=None):
        """
        :return: TRUE if  self._dut_info_file_path exists and is under the max lifetime limit
        and it passed all validations
        """
        ret = True
        self._get_dutinfo_file_path()
        res_path = path if path else self._dut_info_file_path
        if os.path.isfile(res_path):
            modified_time = datetime.fromtimestamp(os.path.getmtime(self._dut_info_file_path))
            day_diff = (datetime.now() - modified_time).days
            lifetime_sec = (datetime.now() - modified_time).seconds
            if lifetime_sec > self._dut_info_file_max_lifetime_seconds:
                ret = False
            # test if excel path has changed since last time
            if ret and self.setup_excel_path:
                current = self.setup_excel_path
                from copy import deepcopy
                copied_obj = deepcopy(self)
                ret &= copied_obj.restore_class_from_file(path=res_path, validate=False)
                if copied_obj.setup_excel_path != current:
                    ret = False
        else:
            ret = False
        return ret

    def save_class_to_file(self, path=None):
        """
        save the class data to file for later restore (serialize)
        :param path: if specified will try to save to this path, else will use default path
        :type path: str
        :return: True on success or False otherwise
        :rtype: bool
        """
        ret = True
        if path:
            ret = self.toJSON(path)
        else:
            ret = self.toJSON(self._get_dutinfo_file_path())
        return ret


class SvDutinfo(TestDataCommon):
    """
    represents all relevant cpss dut info that can be used to apply various logic
    or for test summary data
    :type asic_info: CpssPP
    """

    def __init__(self):
        super(SvDutinfo,self).__init__(table_title="Dut Information")
        self.appMode = DutAppMode.Undefined
        self.board_type = None  # each application will set this according to its own convention (MTS | SwitchDev)
        self.AppSwVersion = ""  # the relevant app version
        self.uboot_version = ""
        self.board_type = None # each project will set this value according to it own convention
        self.asic_type = ASICType.Unset
        self._is_detected = False  # indicates if this board was already detected or not


