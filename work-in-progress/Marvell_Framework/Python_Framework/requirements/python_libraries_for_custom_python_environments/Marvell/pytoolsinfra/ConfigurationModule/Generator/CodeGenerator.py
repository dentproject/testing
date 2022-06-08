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

from __future__ import print_function
from builtins import str
from builtins import range
from builtins import object
import xlrd
import os
from Marvell.pytoolsinfra.ConfigurationModule.Configurator.Core.ABCConfigurationReader import ABCConfigurationReader

indent = "  "
indentX2 = "    "
indentX4 = "        "
indentX8 = "            "


class CodeGenerator(object):
    def __init__(self):
        self.output_file = None
        self.file_path = None
        self.result_string = None
        self.workbook = None
        self.ignore_sheet_names = ["DropDown"]
        self.sections = {}
        self.sheets = []
        self.total_sheets = []
        self._section_title_mark = "%%"
        self._section_title_index = 0
        self._default_members_value = ''

    def is_valid(self, file_path=None):
        """
        checks if this class has the minimum properties to generate an object
        returns true if self.workbook is ok for use
        :param file_path: the xsl file path
        :return: True if generation is valid
        """
        if file_path is None:
            if self.file_path is None:
                if self.workbook is None:
                    print("----ERROR----> No file_path configured")
                    return False
            elif self.workbook is None:
                self.workbook = xlrd.open_workbook(self.file_path)
        else:
            if self.file_path is None:
                self.file_path = file_path
            if self.workbook is None:
                self.workbook = xlrd.open_workbook(self.file_path)
        return True

    def get_sheet_name_from_name(self, sheet_name):
        for sheet_name_org in self.workbook.sheet_names():
            if sheet_name_org.lower() == sheet_name.lower():
                return sheet_name_org

    def get_base_obj(self, i_sheet_name, file_path=None):
        """
        Gets the basic object defined by the sheet
        typically the object will be constructed by members named by the first row of the sheet
        :param i_sheet_name: the requested sheet name
        :param file_path: the path to the xsl file
        :return: returns a GeneratorObject presentation of the sheet object
        """
        if self.is_valid(file_path):
            object_members = []
            sheet = None
            is_class = True
            incoming_sheet = self.low_strip(i_sheet_name, is_class_name=is_class)
            for sheet_name in self.workbook.sheet_names():
                real_sheet = self.low_strip(sheet_name, is_class_name=is_class)
                if sheet_name not in self.ignore_sheet_names and real_sheet == incoming_sheet:
                    sheet = self.workbook.sheet_by_name(sheet_name)
                    break
            if sheet is not None:
                for j in range(sheet.ncols):
                    if self._section_title_mark in sheet.cell_value(0, j):
                        break
                    object_members.append(self.low_strip(sheet.cell_value(0, j)))
                sheet_template_name = "SheetData"
                if object_members:
                    return self.GeneratorObject(
                        self.low_strip(sheet.name + sheet_template_name, make_low=False, is_class_name=True),
                        object_members, {})
                else:
                    return self.GeneratorObject("", [], {})
            else:
                raise Exception(
                    "Cannot instantiate base obj for sheet named: {} possible solutions: {}".format(
                        i_sheet_name,
                        self.workbook.sheet_names()))

    def add_to_result(self, string_to_add):
        """
        Adds the given string_to_add to the result string
        in case the given string is already in the result string, it will not be added
        :param string_to_add: the string to add to the result
        :return: None
        """
        if self.result_string is None:
            self.result_string = string_to_add
        elif string_to_add not in self.result_string:
            self.result_string += string_to_add

    def create_section_code(self, start_row, sheet_name, section_name, file_path, output_file_path="model_objects.py",
                            base_obj=None, write=False):
        if self.is_valid(file_path):
            if base_obj is None:
                base_obj = self.get_base_obj(sheet_name, file_path)

            sheet = self.workbook.sheet_by_name(self.get_sheet_name_from_name(sheet_name))
            stripped_sec_name = self.low_strip(section_name, [self._section_title_mark], True, False)
            org_section_name = ""
            section_type = None
            members = []
            done_with_section = False
            section_in_progress = False
            table_obj_index = -1
            for i in range(start_row, sheet.nrows):
                if self._section_title_mark in str(sheet.cell_value(i, 0)):
                    if section_in_progress:
                        done_with_section = True
                        break
                    else:
                        temp_name = self.low_strip(sheet.cell_value(i, self._section_title_index), [self._section_title_mark], True, False)
                        if stripped_sec_name in temp_name:
                            if '(' in temp_name:
                                org_section_name = temp_name[0:temp_name.index('(')]
                                section_type = temp_name[temp_name.index(':') + 1:temp_name.index(')')].lower()
                                if section_type == 'table':
                                    base_obj = self.GeneratorObject("", [], {})
                                    table_obj_index = i + 1
                                    base_obj.class_name = "{}Entry".format(org_section_name)
                                    members.append("entries")
                            else:
                                org_section_name = temp_name
                            section_in_progress = True
                            continue

                for j in range(sheet.ncols):
                    if not section_in_progress:
                        break
                    if section_type == 'table':
                        if i == table_obj_index:
                            entry_key = self.low_strip(sheet.cell_value(i, j))
                            if entry_key:
                                base_obj.class_members.append(entry_key)
                        else:
                            break
                    elif j == 0:
                        cell_val = sheet.cell_value(i, j)
                        if isinstance(cell_val, str):
                            cell_val = cell_val.lower()
                        entry_name = self.low_strip(cell_val)
                        numeric_value = ABCConfigurationReader.get_numeric_value(entry_name)
                        if numeric_value is not None:

                            entry_name = '_{}'.format(numeric_value).replace('.', '_')

                        members.append(entry_name)
                    else:
                        break
                if done_with_section:
                    break
            if section_in_progress is False and done_with_section is False:
                print("----ERROR----> Cannot find section named: {}".format(section_name))
            if section_type is None:
                section_class = self.GeneratorObject(org_section_name, members, {})
                section_class.members_value = base_obj if base_obj is not None else self._default_members_value
            elif section_type == 'table':
                section_class = self.GeneratorObject(org_section_name, members, {})
                section_class.members_value = "[{}]".format(base_obj.class_name)
            else:
                section_class = self.GeneratorObject(section_type.title(), members, {})
                section_class.members_value = base_obj if base_obj is not None else self._default_members_value

            if base_obj is not None:
                self.add_to_result(base_obj.get_string())
            self.add_to_result(section_class.get_string())
            self.sections[org_section_name] = section_class
        self.write_content(output_file_path, write)

    def create_sheet_code(self, sheet_name, file_path=None, output_file_path="model_objects.py", write=False):
        if self.is_valid(file_path):
            base_obj = self.get_base_obj(sheet_name)
            sheet_empty = True
            if base_obj:
                self.add_to_result(base_obj.get_string())
            sheet = self.workbook.sheet_by_name(self.get_sheet_name_from_name(sheet_name))
            j = 0
            for i in range(sheet.nrows):
                if self._section_title_mark in str(sheet.cell_value(i, j)):
                    self.create_section_code(i, sheet_name, self.low_strip(sheet.cell_value(i,self._section_title_index),
                                                                           [self._section_title_mark], True, False),
                                             file_path, output_file_path, base_obj=base_obj, write=write)
                    sheet_empty = False
            if not sheet_empty:
                self.sheets.append(sheet_name)
                self.write_content(output_file_path, write)

    def create_workbook_code(self, excel_file, output_directory="model_objects.py", write=False):
        self.output_file = open(output_directory, "w")
        self.file_path = excel_file
        self.workbook = xlrd.open_workbook(self.file_path)
        for sheet_name in self.workbook.sheet_names():
            if sheet_name not in self.ignore_sheet_names:
                self.create_sheet_code(sheet_name)  # self.workbook.sheet_by_name(sheet_name)

        self.write_content(output_directory, write)

    def write_content(self, output_directory="model_objects.py", write=False):
        if write:
            self.output_file = open(output_directory, "w")
            self.output_file.write(self.result_string)
            print("Writing CodeGenerator result to file " + os.path.realpath(self.output_file.name))

    @staticmethod
    def low_strip(*args, **kwargs):
        # use Same format as TG
        return ABCConfigurationReader.low_strip(*args, **kwargs)

    class GeneratorObject(object):
        """
           An object that represents a printable code object
           """

        def __init__(self, name, i_members, i_members_dict):
            self.class_name = name
            self.class_members = i_members
            self.class_members_dict = i_members_dict
            self.members_value = "\"\""

        # def set(self, name, members, members_dict):
        #     self.class_members = members
        #     self.class_name = name.replace(" ", "")
        #     self.members_value = "\"\""
        #     self.class_members_dict = members_dict
        def get_string(self):
            if len(self.class_members) > 0 or self.class_members_dict:
                class_str = "class " + self.class_name + "(object):\n"
                class_str += indentX2 + "def __init__(self):\n"

                if len(self.class_members) > 0:
                    for member in self.class_members:
                        class_str += indentX4 + "self." + member + " = "

                        if type(self.members_value) is bytes or type(self.members_value) is str:
                            class_str += str(self.members_value)
                        else:
                            class_str += self.members_value.class_name + "()"

                        class_str += "\n"

                        if (type(self.members_value) is bytes or type(self.members_value) is str) and \
                                        '[' in self.members_value and \
                                        self.members_value != "[]":
                            class_str += indentX4 + "self." + member + ".pop()\n\n" + self.get_table_functions()
                elif self.class_members_dict:
                    for k, v in list(self.class_members_dict.items()):
                        class_str += indentX4 + "self." + str(k) + " = " + str(v) + "\n"
                else:  # never happen
                    class_str += indentX4 + "pass\n"

                return class_str + "\n\n"
            return ""

        @staticmethod
        def get_table_functions():
            return "{}{}\n{}{}\n\n{}{}\n{}{}\n{}{}\n".format(indentX2, "def __getitem__(self, item):", indentX4,
                                                           "return self.entries[item]", indentX2, "def __iter__(self):",
                                                           indentX4, "for entry in self.entries:", indentX8,
                                                           "yield entry")
