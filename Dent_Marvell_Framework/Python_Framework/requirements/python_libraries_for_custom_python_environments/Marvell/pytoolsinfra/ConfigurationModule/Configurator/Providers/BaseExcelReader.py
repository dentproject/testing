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

from builtins import str
from builtins import range
# import xlrd
from Marvell.pytoolsinfra.ConfigurationModule import *
from Marvell.pytoolsinfra.ConfigurationModule.Configurator.Core.ConfigReader import ConfigReader
from Marvell.pytoolsinfra.ConfigurationModule.Configurator.Utilities import ConfiguratorUtils
from Marvell.pytoolsinfra.CommonDef.InfrastructureExceptions.Exceptions import FileNotFoundErrorInfra
from collections import OrderedDict


class BaseExcelReader(ConfigReader):
    def __init__(self):
        super(BaseExcelReader, self).__init__()
        self._support_types += ".xls .xlsx "
        self.ignore_sheets = ["dropdown"]
        self.work_book = None
        self.work_book_file_path = None
        self._section_title_mark = "%%"
        self._section_title_char = '%'
        self._section_title_index = 0
        self._row_data_end = None

    def init_workbook(self, file_path):
        import xlrd
        """
        Check if work_book property is not None, if it is initialize it with the given file
        :param file_path: the xsl/xslx file
        :return: Nothing, may raise FileNotFoundErrorInfra exception
        """
        if not self.work_book or file_path != self.work_book_file_path:
            if os.path.exists(file_path):
                self.work_book = xlrd.open_workbook(file_path)
                self.work_book_file_path = file_path
            else:
                raise FileNotFoundErrorInfra("----ERROR----> ExcelReader - Can't find file: ", file_path)

    def get_obj(self, file_path, key=None, obj=None, similar_threshold=0.7,
                pack_result=True, apply_format=True, section_type_key=None):
        """
        A method that creates an object from xsl/xslx file

        key may have 3 options:
        1. None or Empty ('') - this case will return an object representing the whole workbook(file)
        2. "sheet_name" - this case will return an object representing the sheet requested
        3. "sheet_name.section_name" - this case will return an object representing the requested section within the
            requested sheet
        :param apply_format: A flag to indicate if to use tolower, title, delete spaces and such
        :param pack_result: a flag to determine if to return an object(True) or a dict(False)
        :param file_path: the xsl/xslx file
        :param key: the key by which the object should be extracted
        :param obj: the prototype object (commonly will be generated object to fill)
        :param similar_threshold: how similar the user wants it to be (created one against generated one)
        :param section_type_key: the attribute name to inject to dynamic obj that can be used to parse the section type
        :return: the extracted object from xsl/xslx
        """
        if key is None or not key:
            ret_obj = self.get_workbook_obj(file_path, pack_result, apply_format)  # return workbook presentation
        elif '.' not in key:
            ret_obj = self.get_sheet_obj(file_path, key, pack_result, apply_format)  # return sheet presentation
        else:
            # return section presentation
            ret_obj = self.get_section_obj(file_path, key, pack_result, apply_format, section_type_key)
        """
        At this point we have the requested object
        """
        if ret_obj is None:
            return
        if obj is None:  # if user don't want to use prototype
            return ret_obj
        else:
            rate = ConfiguratorUtils.get_similarity_rate(obj, ret_obj)

            if rate < similar_threshold:
                # throw exception
                config_logger.error("----ERROR----> similarity rate({}) below threshold({}".format(str(rate), str(
                    similar_threshold)))
            else:
                # from Marvell.pytoolsinfra.CommonDef.CommonUtils.CommonFuncs import fill_object
                # fill_object(ret_obj,obj)
                ConfiguratorUtils.fill_object(ret_obj, obj)
                return obj

    def get_workbook_obj(self, xls_file, pack_result=True, apply_format=True):
        sheets = {}
        excel_dic = OrderedDict()
        self.init_workbook(xls_file)
        workbook_name = os.path.splitext(os.path.basename(xls_file))[0]
        workbook_name = self.low_strip(workbook_name, [" ", "_"], True, False)
        for sheet_name in self.work_book.sheet_names():
            sheet = self.get_sheet_obj(xls_file, sheet_name, pack_result=pack_result, apply_format=apply_format)
            if sheet is not None:
                sheets[self.low_strip(sheet_name)] = sheet

        excel_dic[workbook_name] = sheets

        if pack_result:
            ob = self.dict_to_obj(list(excel_dic.values())[0])
        else:
            ob = excel_dic
        return ob

    def get_sheet_obj(self, xls_file, key, pack_result=True, apply_format=True):
        self.init_workbook(xls_file)
        sections = OrderedDict()
        sections_names = []
        excel_dic = OrderedDict()
        sheet_name_org = None
        ob = None
        key_sheet_name = key.replace(" ", "").lower().split(".")[0]
        sheet_found = False
        sheet_empty = True
        for sheet_name in self.work_book.sheet_names():
            if sheet_name.lower() not in self.ignore_sheets and sheet_name.lower() == key_sheet_name:
                sheet = self.work_book.sheet_by_name(sheet_name)
                sheet_name_org = sheet_name
                sheet_found = True
                excel_dic[sheet_name] = []
                for i in range(sheet.nrows):
                    # for j in range(sheet.ncols):
                    if self._section_title_mark in str(sheet.cell_value(i, 0)):

                        section_name = sheet.row_values(i)[self._section_title_index].replace(self._section_title_char,
                                                                                              "")
                        if apply_format:
                            section_name = self.low_strip(section_name, is_class_name=False)

                        sections_names.append(section_name)
                        sheet_empty = False
            elif sheet_found:
                break
        for i in range(len(sections_names)):
            sec = self.get_section_obj(xls_file, "{}.{}".format(key_sheet_name, sections_names[i]), pack_result=False,
                                       apply_format=apply_format, section_type_key=None, is_class_name=False)
            for k, v in list(sec.items()):
                sections[k] = sec[k]

        excel_dic[sheet_name_org] = sections
        if pack_result:
            ob = self.dict_to_obj(list(excel_dic.values())[0])
        else:
            ob = excel_dic
        if sheet_empty:
            return None
        else:
            return ob

    def get_section_obj(self, xls_file, key, pack_result=True, apply_format=True, section_type_key=None,
                        is_class_name=True):
        self.init_workbook(xls_file)
        section_type = ""
        if apply_format:
            if '(' in key:
                key_sheet_name, key_section_name = self.low_strip(key[0:key.index('(')],
                                                                  is_class_name=is_class_name).split(".")
                key_section_name = key_section_name.rstrip('_')
            else:
                key_sheet_name, key_section_name = self.low_strip(key, is_class_name=is_class_name).split(".")
        else:
            if '(' in key:
                key_sheet_name, key_section_name = key[0:key.index('(')].split(".")
            else:
                key_sheet_name, key_section_name = key.split(".")
        excel_dic = OrderedDict()
        table_obj_index = -1
        close_section = False
        _found_section = False
        ob = None
        section_name = ""
        section_type = ""
        for sheet_name in self.work_book.sheet_names():
            if sheet_name.lower() not in self.ignore_sheets:
                if sheet_name.lower() == key_sheet_name.lower():
                    sheet = self.work_book.sheet_by_name(sheet_name)
                    columns = []
                    for i in range(sheet.nrows):
                        for j in range(sheet.ncols):
                            cell_val = str(sheet.cell_value(i, j)).strip()
                            # str(sheet.cell_value(i, j)).encode('utf8').strip(bytes(b"' '"))
                            if i == 0 and self._section_title_mark not in str(cell_val):
                                columns.append(self.low_strip(cell_val))
                            elif self._section_title_mark in str(cell_val):
                                cell_val = sheet.row_values(i)[self._section_title_index]
                                if '(' in sheet.row_values(i)[self._section_title_index]:
                                    if apply_format:
                                        section_name = self.low_strip(
                                            cell_val[:cell_val.index("(")], [self._section_title_char],
                                            is_class_name=is_class_name).rstrip('_')
                                    else:
                                        section_name = str(cell_val[:cell_val.index("(")]
                                                           .replace(self._section_title_char, ""))
                                    section_type = cell_val[cell_val.index(':'):cell_val.index(")")].strip(
                                        "_,: ").lower()
                                else:
                                    if apply_format:
                                        section_name = self.low_strip(cell_val, [self._section_title_char],
                                                                      is_class_name=is_class_name)
                                    else:
                                        section_name = str(
                                            cell_val.replace(self._section_title_char, ''))
                                if bool(excel_dic):
                                    close_section = True
                                    break

                                if section_name == key_section_name:
                                    excel_dic[section_name] = OrderedDict()
                                    if section_type:
                                        if section_type.lower() == 'table':
                                            table_obj_index = i + 1
                                        if section_type_key:
                                            excel_dic[section_name][section_type_key] = section_type
                                    _found_section = True
                                    break
                                else:
                                    break

                            # if there is a key but no value we set its value to none ,else we don't take it
                            if _found_section:
                                if section_type and section_type == 'table':
                                    if cell_val != "":
                                        if table_obj_index > -1:
                                            if table_obj_index == i:
                                                if apply_format:
                                                    columns.append(self.low_strip(cell_val.lower()))
                                                else:
                                                    columns.append(cell_val.lower())
                                            else:
                                                if 'entries' not in excel_dic[section_name]:
                                                    excel_dic[section_name]['entries'] = []
                                                entry_index = i - table_obj_index - 1
                                                if len(excel_dic[section_name]['entries']) > entry_index:
                                                    if apply_format:
                                                        cell_val = self.low_strip(cell_val.lower())

                                                    numeric_value = self.get_numeric_value(cell_val)
                                                    if numeric_value is None:
                                                        excel_dic[section_name]['entries'][entry_index].update(
                                                            {columns[j]: cell_val.lower()})
                                                    else:
                                                        excel_dic[section_name]['entries'][entry_index].update(
                                                            {columns[j]: numeric_value})

                                                else:
                                                    numeric_value = self.get_numeric_value(cell_val)
                                                    if numeric_value is None:
                                                        excel_dic[section_name]['entries'].append(
                                                            {columns[j]: cell_val.lower()})
                                                    else:
                                                        excel_dic[section_name]['entries'].append(
                                                            {columns[j]: numeric_value})

                                        else:
                                            config_logger.error("----ERROR----> cant find table base object")

                                else:
                                    cell_raw_value = sheet.cell_value(i, j)
                                    if cell_raw_value == self._row_data_end:
                                        break

                                    if j == 0:
                                        if apply_format:
                                            if isinstance(cell_raw_value, str):
                                                cell_val = self.low_strip(cell_raw_value.lower())
                                            else:
                                                cell_val = cell_raw_value
                                        else:
                                            cell_val = str(cell_raw_value)
                                    numeric_value = self.get_numeric_value(cell_raw_value)
                                    if numeric_value is not None:
                                        cell = numeric_value
                                    else:
                                        cell = cell_val

                                    if apply_format:
                                        if isinstance(sheet.cell_value(i, 0), str):
                                            entry_name = self.low_strip(sheet.cell_value(i, 0).lower())
                                        else:
                                            entry_name = sheet.cell_value(i, 0)
                                    else:
                                        entry_name = str(sheet.cell_value(i, 0))

                                    numeric_value = self.get_numeric_value(entry_name)
                                    if numeric_value is not None:
                                        entry_name = '_{}'.format(numeric_value)

                                    entry_key = columns[j] if len(columns) > j else ""
                                    self.update_entry_data(excel_dic[section_name], entry_name, j, cell, entry_key)
                                    # if j is 0:
                                    #     excel_dic[section_name][entry_name] = {}
                                    # # else:
                                    # excel_dic[section_name][entry_name].update({columns[j]: cell})
                        if close_section:
                            break

        if len(excel_dic) == 0:
            config_logger.error(
                "----ERROR----> Cannot find sheet named: {} possible solutions: {}".format(
                    key_sheet_name,
                    self.work_book.sheet_names()))

        else:
            excel_dic = OrderedDict((k, v) for k, v in list(excel_dic.items()) if v)
            if pack_result:
                ob = self.dict_to_obj(list(excel_dic.values())[0])
            else:
                ob = excel_dic
        return ob

    def update_entry_data(self, obj, entry_name, clo_index, cell_data, entry_key=""):
        if clo_index == 0:
            obj[entry_name] = {}

        obj[entry_name].update({entry_key: cell_data})

# This line decorates all the functions in this class with the "LogWith" decorator
# ExcelReader = Log_all_class_methods(ExcelReader, config_logger, show_params)
