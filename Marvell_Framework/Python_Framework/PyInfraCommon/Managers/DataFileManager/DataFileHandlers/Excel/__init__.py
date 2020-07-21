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
import inspect
import os
from collections import OrderedDict

import PyInfraCommon.Globals.Logger.GlobalTestLogger
from PyInfraCommon.BaseTest.BaseTestExceptions import TestCrashedException
from PyInfraCommon.GlobalFunctions.Import import loadDynamicModule
from PyInfraCommon.GlobalFunctions.Utils.Function import GetFunctionName
from PyInfraCommon.ExternalImports.ResourceManager import ConfigManager, Generator
from PyInfraCommon.Globals.Logger import GlobalTestLogger
from PyInfraCommon.GlobalFunctions.Utils.dict import DictFunctions

class ExcelServices(object):

    """
    this class provides all Excel services in one place
    you should provide path to excel on the class init
    """

    def __init__(self,excelPath=None):
        self._excelPath = None
        self.file_path = excelPath
        self._manager = ConfigManager()
        self._generator = Generator()

    @staticmethod
    def my_path(self):
        filename = os.path.abspath(inspect.stack()[1][1])
        path = os.path.dirname(os.path.abspath(filename))
        return path

    @property
    def file_path(self):
        return self._excelPath

    @file_path.setter
    def file_path(self , path):
        self._excelPath = path

    def GetSectionAsDict(self,sheetName,SectionName,strip_key_value=True):
        """
        :param SheetName: the name of the excel sheet the section is located
        :param SectionName: name of section
        :param strip_key_value: if True will strip the returned dictionary dict["yourkey]["key"]
        and dict["yourkey]"["value"] ==> to dict["yourkey"]
        :return:  dictionary of excel section of None if failed
        """
        res = OrderedDict()
        key = sheetName+"."+SectionName
        res = self._manager.get_obj(key , self.file_path, pack_result=False,apply_format=False)
        if res:
            if not strip_key_value:
                return list(res.values())[0]
            else:
                ret_dict = list(res.values())[0]  # type: OrderedDict
                # strip key,description
                strip_list = ["key","description"]
                DictFunctions.strip_keys(ret_dict,strip_list)
                value_str = "value"
                DictFunctions.move_inner_child_value_to_parent(ret_dict,value_str)
                return ret_dict
        return res

    def GetSheetAsDict(self,sheetName,strip_key_value=False):
        """
        :param SheetName:
        :return:dictionary of all excel Section as
        """
        res = OrderedDict()
        key = sheetName
        res = self._manager.get_obj(key , self.file_path, pack_result=False, apply_format=False)
        if res:
            if not strip_key_value:
                return list(res.values())[0]
            else:
                ret_dict = list(res.values())[0]  # type: dict
                # strip key,description
                strip_list = ["key", "description"]
                DictFunctions.strip_keys(ret_dict, strip_list)
                value_str = "value"
                DictFunctions.move_inner_child_value_to_parent(ret_dict, value_str)
                return ret_dict
        return res

    def GetExcelAsDict(self,strip_key_value=False,move_child_up_by_key_list:list =None):
        """
        :param strip_key_value:
        :type strip_key_value:
        :param move_child_up_by_key_list: if passed will move all child keys content to parent key
        :type move_child_up_by_key_list:
        :return: dictionary of all excel workbook
        :rtype:
        """
        res = OrderedDict()
        res = self._manager.get_obj(None , self.file_path, pack_result=False, apply_format=False)
        default_strip_list = ("key","description")
        move_inner_list = ["value","entries"]
        move_inner_list.extend(move_child_up_by_key_list)
        if res:
            if not strip_key_value:
                return list(res.values())[0] # type: dict
            else:
                ret_dict :dict = list(res.values())[0]
                # strip key,description
                DictFunctions.strip_keys(ret_dict, default_strip_list)
                value_str = "value"
                for key in move_inner_list:
                    DictFunctions.move_inner_child_value_to_parent(ret_dict, key)
                DictFunctions.move_redundant_keys_values_as_parent(ret_dict)
                return ret_dict
        return res

    def GetSectionAsClass(self,sheetName,sectionName,cls=None,autoGenerateClassCode=True):
        """
        return the excel section as filled class
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
        key = sheetName + "." + sectionName
        newsectionName = sectionName.replace(" " , "_")
        if cls is None and autoGenerateClassCode is False:
            res = None
            res = self._manager.get_obj(key , self.file_path , ret_obj=res)
            return res
        elif cls is None and autoGenerateClassCode is True:
            # check if the class code already exists at the path
            from os import path
            exceldir = path.dirname(self.file_path)
            # check if the class code file actually exists
            classfile = exceldir+ "\\"+ newsectionName + ".py"
            if path.isfile(classfile):
                # file exists try to import it
                ret = loadDynamicModule(newsectionName,exceldir)
                if ret is not None:
                    return ret
                else:
                    GlobalTestLogger.GlobalLogger.logger.error(funcname+" failed to  load module")
                    return ret
            else:
                # file doesnt exist generate it
                self._generator.create(self.file_path , classfile , key)
                if path.isfile(classfile):
                    # file exists try to import it
                    ret = loadDynamicModule(newsectionName,exceldir)
                    if ret is not None:
                        return ret
                    else:
                        GlobalTestLogger.GlobalLogger.logger.error(funcname + " failed to load {} module after generating it".format(sectionName))

        elif cls is not None:
            cls = self._manager.get_obj(key , self.file_path , ret_obj=cls)
            return cls

    def GetSheetAsClass(self,sheetName,cls=None,autoGenerateClassCode=True):
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
        key = sheetName
        if cls is None and autoGenerateClassCode is False:
            res = None
            res = self._manager.get_obj(key , self.file_path , ret_obj=res)
            return res
        elif cls is None and autoGenerateClassCode is True:
            # check if the class code already exists at the path
            from os import path
            exceldir = path.dirname(self.file_path)
            excelfile = path.basename(self.file_path)
            fname = excelfile.split(".")[0]+"_"+sheetName
            # check if the class code file actually exists
            classfilepath = exceldir + "\\" + fname + ".py"
            if path.isfile(classfilepath):
                # file exists try to import it
                mod = loadDynamicModule(fname , exceldir)
                if mod is not None:
                    #loaded the module , now try to load class
                    if hasattr(mod,sheetName):
                        klass = getattr(mod,sheetName)
                        Instance = klass()
                        #now fill the instance and return it
                        return self.GetSheetAsClass(sheetName,Instance)
                else:
                    GlobalTestLogger.GlobalLogger.logger.error(funcname + " failed to load the module {} from the dir {}".format(fname,exceldir))
                    return None
            else:
                # file doesnt exist generate it
                self._generator.create(self.file_path , classfilepath , key)
                if path.isfile(classfilepath):
                    # file generated try to import it
                    mod = loadDynamicModule(fname,exceldir)
                    if mod is not None:
                        # loaded the module , now try to load class
                        if hasattr(mod,sheetName):
                            klass = getattr(mod,sheetName)
                            Instance = klass()
                            # now fill the instance and return it
                            return self.GetSheetAsClass(sheetName , Instance)
                        else:
                            # didnt find the class name
                            GlobalTestLogger.GlobalLogger.logger.error(funcname + \
                                                      "failed to load {} class after generating it from the excel file:\n{}".format(
                                                          sheetName , self.file_path))
                            return None
                    else:
                        GlobalTestLogger.GlobalLogger.logger.error(funcname +\
                        "failed to load {} class after generating it from the excel file:\n{}".format(sheetName , self.file_path))
                        return None
                else:
                    GlobalTestLogger.GlobalLogger.logger.error(funcname + \
                    " failed to Generate the excel module from the sheet {}".format(sheetName))
                    return None

        elif cls is not None:
            cls = self._manager.get_obj(key , self.file_path , ret_obj=cls)
            return cls

    def GenerateCode(self,output_file_path, key, excel_fle_path=None):
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
        if excel_fle_path is None:
            path = self.file_path
        else:
            path = excel_fle_path

        if output_file_path is None:
            raise TestCrashedException("output_file_path must be specified,None given")
        return self._generator.create(path,output_file_path,key)
