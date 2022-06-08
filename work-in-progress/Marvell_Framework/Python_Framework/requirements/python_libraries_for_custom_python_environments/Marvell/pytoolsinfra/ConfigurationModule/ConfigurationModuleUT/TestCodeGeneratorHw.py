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

from Marvell.pytoolsinfra.ConfigurationModule.Generator.Generator import Generator
from unittest import TestCase
from os import path

THIS_FOLDER = path.dirname(path.realpath(__file__)) + '\\'


class TestCodeGeneratorHw(TestCase):
    file_path = THIS_FOLDER + r"..\assets\Setup_HW.xlsx"
    tests_output_lib = path.dirname(
        path.realpath(__file__)) + '\\' +'tests_output\\'

    def test_generator_section(self):
        generator = Generator(gen_type=Generator.GeneratorType.HW_GENERATOR_TYPE)
        output_file = "{}output_generator_example_section_HW.py".format(self.tests_output_lib)
        generator.create(self.file_path, output_file, "setup.DUT General Info")
        self.assertIsNotNone(generator.generator.codegenerator.workbook)

    def test_generator_sheet(self):
        generator = Generator(gen_type=Generator.GeneratorType.HW_GENERATOR_TYPE)
        output_file = "{}output_generator_sheet_HW.py".format(self.tests_output_lib)
        generator.create(self.file_path, output_file, "setup")
        self.assertIsNotNone(generator.generator.codegenerator.workbook)

    def test_generator_section_type(self):
        generator = Generator(gen_type=Generator.GeneratorType.HW_GENERATOR_TYPE)
        output_file = "{}output_generator_section_with_type_HW.py".format(self.tests_output_lib)
        generator.create(self.file_path, output_file, "setup.Port Data1")
        self.assertIsNotNone(generator.generator.codegenerator.workbook)

