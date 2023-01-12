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
from .DataFileHandlers.Excel import ExcelServices
from .DataFileHandlers.Yaml import YamlServices
from PyInfraCommon.GlobalFunctions.Utils.Function import GetFunctionName
from PyInfraCommon.Globals.Logger.GlobalTestLogger import GlobalLogger
import os
import inspect
from collections import OrderedDict
import sys


_supported_types = ["xls", "xlsx", "yaml"]


class DataFileManager(object):
    """
    this class provides an interface for working with various data files such as excel,xml, yaml
    it provides the following capabilities:
    1. Read from a file into python pre-generated class or runtime generated class or dict structures
    2. Auto generated python class code file that can be later filled with data from the data file
    3. Processing Table structures from the file into python structure

    # Note the Yaml method only supports the method read_file_to_object
    **currently only excel and yaml file formats are supported**
    """
    
    def __init__(self, filepath=None):
        self._file_path = filepath
        self._file_manager_obj = None
        self._type_to_manger = {"xls":ExcelServices(), "xlsx":ExcelServices(), "yaml":YamlServices()}
        if self._file_path:
                self._file_extension = os.path.splitext(filepath)[1].split(".")[1]
                if self._file_extension.lower() in _supported_types:
                    self._file_manager_obj = self._type_to_manger[self._file_extension.lower()]
                    self._file_manager_obj.file_path = self._file_path
                else:
                    err = "DataFileManager: current file extension is not supported\n\
                    supported file types are {}\n".format(" ".join(self._type_to_manger))
                    raise NotImplementedError(err)

    @staticmethod
    def my_path():
        filename = os.path.abspath(inspect.stack()[1][1])
        path = os.path.dirname(os.path.abspath(filename))

        # If we are running inside EXE file (bundle Python app)
        # We will need to get the 'froze' path instead of the real path
        if getattr(sys, 'frozen', False):
            # we are running in a bundle (e.g. 'exe' file)
            # so we must change the root dir to be the "Temp one"
            tmp_dir = getattr(sys, '_MEIPASS', "c:\\")
            project_name = "Python_Platform_Validation_Tests"
            pnl = len(project_name)
            pni = path.rfind(project_name)
            path = path[pni + pnl + 1:]
            path = os.path.join(tmp_dir, path)
        return path
    
    def _is_meth_supported(self, meth):
        """
        returns if this method is supported on given file format reader
        :param meth: method name
        :type meth: str
        :return:  True | False
        :rtype: bool
        """
        if hasattr(self._file_manager_obj, meth):
            if callable(getattr(self._file_manager_obj, meth)):
                return True
        return False
    
    def GetSectionAsDict(self, sheetName, SectionName,strip_key_value=True) ->OrderedDict:
        """
        :param SheetName: the name of the excel sheet the section is located
        :param SectionName: name of section
        :param strip_key_value: if True will strip the returned dictionary dict["yourkey]["key"]
        and dict["yourkey]"["value"] ==> to dict["yourkey"]
        :return:  dictionary of excel section
        :rtype: OrderedDict
        """
        funcname = GetFunctionName(self.GetSectionAsDict)
        if self._is_meth_supported("GetSectionAsDict"):
            return self._file_manager_obj.GetSectionAsDict(sheetName, SectionName,strip_key_value)
        else:
            err = funcname + " this function is not supported on {} file format".format(self._file_extension)
            raise NotImplementedError(err)
    
    def GetSheetAsDict(self, sheetName,strip_key_value=True) ->OrderedDict:
        """
        :param SheetName:
        :param strip_key_value: if True will strip the returned dictionary dict["yourkey]["key"]
        and dict["yourkey]"["value"] ==> to dict["yourkey"]
        :return:  dictionary of excel section
        :rtype: OrderedDict
        """
        funcname = GetFunctionName(self.GetSheetAsDict)
        if self._is_meth_supported("GetSheetAsDict"):
            return self._file_manager_obj.GetSheetAsDict(sheetName,strip_key_value)
        else:
            err = funcname + " this function is not supported on {} file format".format(self._file_extension)
            raise NotImplementedError(err)

    def GetExcelAsDict(self,strip_key_value:bool=True,move_child_up_by_key_list:list =None) ->OrderedDict:
        """
        
        :param strip_key_value: if True will strip the returned dictionary dict["yourkey]["key"]
        :type strip_key_value: bool
        :param move_child_up_by_key_list: if passed will move all child keys content to parent key
        :type move_child_up_by_key_list: list
        :return: dict of entire excel book
        :rtype: 
        """
        funcname = GetFunctionName(self.GetExcelAsDict)
        if self._is_meth_supported("GetExcelAsDict"):
            return self._file_manager_obj.GetExcelAsDict(strip_key_value,move_child_up_by_key_list)
        else:
            err = funcname + " this function is not supported on {} file format".format(self._file_extension)
            raise NotImplementedError(err)


    def GetSectionAsClass(self, sheetName, sectionName, cls=None, autoGenerateClassCode=True):
        """
        return the file section as filled class
        -if cls is none  and autoGenerateClassCode is False will return dynamic generated object
        -if cls is none and autoGenerateClassCode is True:
        it will automatically detect if the class code exist on the excel path
        if its already exists assuming the filename is "sectionname.py" it will import it and fill it else it will generate it then fill it and return it
        -if cls is existing section class and autoGenerateClassCode is False it will fill its values
        :param sheetName: name of excel sheet
        :param sectionName: name of section in sheet
        :param cls: optional, existing class to fill its values, if none will generate class code and will return it
        :param autoGenerateClassCode: if True will generate code if required else will not generate code
        :return: the class filled with the section values
        """
        funcname = GetFunctionName(self.GetSectionAsClass)
        if self._is_meth_supported("GetSectionAsClass"):
            return self._file_manager_obj.GetSectionAsClass(sheetName, sectionName, cls, autoGenerateClassCode)
        else:
            err = funcname + " this function is not supported on {} file format".format(self._file_extension)
            raise NotImplementedError(err)
    
    def GetSheetAsClass(self, sheetName, cls=None, autoGenerateClassCode=True):
        """
        return the excel shhet as filled class
        -if cls is none  and autoGenerateClassCode is False will return dynamic generated object
        -if cls is none and autoGenerateClassCode is True:
        it will automatically detect if the class code exist on the excel path
        if its already exists assuming the filename is "sheetname.py" it will import it and fill it else it will generate it then fill it and return it
        -if cls is existing section class and autoGenerateClassCode is False it will fill its values
        :param sheetName: name of excel sheet
        :param sectionName: name of section in sheet
        :param cls: optional, existing class to fill its values, if none will generate class code and will return it
        :param autoGenerateClassCode: if True will generate code if required else will not generate code
        :return: the class filled with the section values
        """
        funcname = GetFunctionName(self.GetSheetAsClass)
        if self._is_meth_supported("GetSheetAsClass"):
            return self._file_manager_obj.GetSheetAsClass(sheetName, cls, autoGenerateClassCode)
        else:
            err = funcname + " this function is not supported on {} file format".format(self._file_extension)
            raise NotImplementedError(err)
    
    def GenerateCode(self, output_file_path, key, excel_fle_path=None):
        """
        generate python code from an excel
        :param excel_fle_path:  path to excel file, if none will use self path member
        :param output_file_path:  path to where generated code file will be saved
        :param key: "sheetname"  to generate code classes for entire sheet
                    "sheetname.sectionName" to generate code class for only specific section in sheet
                    None  to generate code for all excel sheets
        :type output_file_path: str
        :type key: str
        :type excel_fle_path: str
        :return: after successfull import you can import the generated code and use it with Get methods of this class
        """
        path = ""
        funcname = GetFunctionName(self.GenerateCode)
        if self._is_meth_supported("GenerateCode"):
            return self._file_manager_obj.GenerateCode(output_file_path, key, excel_fle_path)
        else:
            err = funcname + " this function is not supported on {} file format".format(self._file_extension)
            raise NotImplementedError(err)
    
    @property
    def file_path(self):
        if self._file_manager_obj:
            return self._file_manager_obj.file_path
        return None
    
    @file_path.setter
    def file_path(self, path):
        funcname = GetFunctionName(self.file_path)
        if path:
            file_extension = os.path.splitext(path)[1].split(".")[1].lower()
            if file_extension in _supported_types:
                if not self._file_manager_obj:
                    # first time manager object creation
                    self._file_manager_obj = self._type_to_manger[file_extension]
                    self._file_manager_obj.file_path = path
                    self._file_extension = file_extension
                else:
                    # there is already a manger object and someone updated the file path
                    if type(self._type_to_manger[file_extension]) == type(self._file_manager_obj):
                        # just update file path
                        self._file_manager_obj.file_path = path
                        self._file_extension = file_extension
                    else:
                        # different type of manager
                        err = funcname + " changing file manager object from {} files manager to {} file manager" \
                                         "".format(self._file_extension, file_extension)
                        GlobalLogger.logger.warning(err)
                        self._file_manager_obj = self._type_to_manger[file_extension]
                        self._file_manager_obj.file_path = path
                        self._file_extension = file_extension
            
            else:
                err = "DataFileManager: current file extension is not supported\n\
                 supported file types are {}\n".format(" ".join(_type_to_manger))
                raise NotImplementedError(err)
