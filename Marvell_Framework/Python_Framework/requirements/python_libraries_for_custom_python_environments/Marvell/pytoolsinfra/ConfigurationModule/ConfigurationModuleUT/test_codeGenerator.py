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
from unittest import TestCase
from os import path
from Marvell.pytoolsinfra.ConfigurationModule.Generator.Generator import \
    Generator

THIS_FOLDER = path.dirname(path.realpath(__file__)) + '\\'

class TestCodeGenerator(TestCase):
    file_path = THIS_FOLDER + r"..\assets\Setup_Example.xls"
    file_path_mi = THIS_FOLDER + r"..\assets\Setup_MI.xls"
    file_path_mi1 = THIS_FOLDER + r"..\assets\Setup_MI1.xls"
    file_path_cv = THIS_FOLDER + r'..\assets\Setup_CV.xls'
    tests_output_lib = THIS_FOLDER + '.\\tests_output\\'

    def test_generator_section_example(self):
        generator = Generator(True)
        output_file = "{}output_generator_example_section.py".format(
            self.tests_output_lib)
        generator.create(self.file_path, output_file, "setup.common settings")

    def test_generator_section(self):
        """

        :return:
        """
        generator = Generator(True)
        output_file = "{}output_generator_section.py".format(
            self.tests_output_lib)
        generator.create(self.file_path_cv, output_file,
                         "TGConnectionTableSheet.Table2")
        self.assertIsNotNone(generator.generator.codegenerator.workbook)

    def test_generator_sheet(self):
        generator = Generator(True)
        output_file = "{}output_generator_sheet.py".format(
            self.tests_output_lib)
        generator.create(self.file_path_cv, output_file,
                         "TGConnectionTableSheet")
        self.assertIsNotNone(generator.generator.codegenerator.workbook)

    def test_generator_workbook(self):
        generator = Generator(True)
        output_file = "{}output_generator_workbook.py".format(
            self.tests_output_lib)
        generator.create(self.file_path_cv, output_file, "")
        self.assertIsNotNone(generator.generator.codegenerator.workbook)

    def test_generator_section_type(self):
        generator = Generator(True)
        output_file = "{}output_generator_section1.py".format(
            self.tests_output_lib)
        generator.create(self.file_path_mi1, output_file,
                         "setupinfo.TGSettings")
        self.assertIsNotNone(generator.generator.codegenerator.workbook)

    def test_generator_sheet_type(self):
        generator = Generator(True)
        output_file = "{}output_generator_sheet1.py".format(
            self.tests_output_lib)
        generator.create(self.file_path_mi1, output_file, "setupinfo")
        self.assertIsNotNone(generator.generator.codegenerator.workbook)

    def test_generator_workbook_type(self):
        generator = Generator(True)
        output_file = "{}output_generator_book1.py".format(
            self.tests_output_lib)
        generator.create(self.file_path_mi1, output_file, "")
        self.assertIsNotNone(generator.generator.codegenerator.workbook)

# TGConnectionTable[0]
#
# class TGConnectionTable:
#     entries = []
#
# class TGConnectionTableEntry:
#     id = ""
#     tg_ip = ""
