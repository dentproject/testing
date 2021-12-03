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
import xlrd
import os
from Marvell.pytoolsinfra.ConfigurationModule.Generator.CodeGenerator import CodeGenerator


class SheetBasedGenerator(object):
    """
    Creates python code based on the Sections inside the xls file
    """

    def __init__(self, generator):
        self.codegenerator = generator

    def create_sheet_code(self, sheet_name, file_path=None, output_file_path="model_objects.py", write=False):
        self.codegenerator.create_sheet_code(sheet_name, file_path, output_file_path, write)
        sheet_members = {}
        for k, v in list(self.codegenerator.sections.items()):
            sheet_members[self.codegenerator.low_strip(k, ["(", ")"], False, True)] = v.class_name + "()"
            del self.codegenerator.sections[k]

        if len(self.codegenerator.sheets) > 0:
            done_with = self.codegenerator.sheets.pop()
            org_sheet_name = self.codegenerator.low_strip(self.codegenerator.get_sheet_name_from_name(done_with), [" "], True, False)
            sheet_class = self.codegenerator.GeneratorObject(org_sheet_name, [], sheet_members)
            self.codegenerator.total_sheets.append(done_with)

            self.codegenerator.add_to_result(sheet_class.get_string())
            self.codegenerator.write_content(output_file_path, write)
            # do something with dict

    def create_workbook_code(self, excel_file, output_directory="model_objects.py", write=False):
        self.codegenerator.output_file = open(output_directory, "w")
        self.codegenerator.file_path = excel_file
        self.codegenerator.workbook = xlrd.open_workbook(self.codegenerator.file_path)
        workbook_name = os.path.splitext(os.path.basename(excel_file))[0]
        workbook_name = self.codegenerator.low_strip(workbook_name, [" ", "_"], True, False)
        workbook_members = {}
        for sheet_name in self.codegenerator.workbook.sheet_names():
            if sheet_name not in self.codegenerator.ignore_sheet_names:
                self.create_sheet_code(sheet_name)  # self.workbook.sheet_by_name(sheet_name)
                sheet_class_name = self.codegenerator.low_strip(self.codegenerator.get_sheet_name_from_name(sheet_name), ["(", ")", " "], True,
                                                  False) + "()"
                if sheet_name in self.codegenerator.total_sheets:
                    workbook_members[self.codegenerator.low_strip(sheet_name, ["(", ")", " "], False, True)] = sheet_class_name

        workbook_class = self.codegenerator.GeneratorObject(workbook_name, [], workbook_members)

        self.codegenerator.result_string += workbook_class.get_string()
        self.codegenerator.write_content(output_directory, write)

    def create_section_code(self, start_row, sheet_name, section_name, file_path, output_file_path="model_objects.py",
                            base_obj=None, write=False):
        self.codegenerator.create_section_code(start_row, sheet_name, section_name, file_path, output_file_path,
                            base_obj, write)
