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
from Marvell.pytoolsinfra.ConfigurationModule.Configurator.Providers.ExcelReaderHw import ExcelReaderHw
from unittest import TestCase
from os import path

THIS_FOLDER = path.dirname(path.realpath(__file__)) + '\\'


class TestConfigManagerHw(TestCase):
    file_path = THIS_FOLDER + r"..\assets\Setup_HW.xlsx"

    def test_something(self):
        import sys
        print(str(sys.modules[__name__]))

    def print_obj(self, obj):
        string = ""
        if hasattr(obj, '__dict__'):
            vs = vars(obj)
            for prop, value in list(vs.items()):
                if "__" not in prop:
                    string += prop + ": " + self.print_obj(value) + "\n\t"
        else:
            string = str(obj)
        return string

    def test_get_sheet_no_prototype(self):
        current_key = "setup"
        self.check_config(current_key, self.file_path)

    def test_get_section_no_prototype(self):
        current_key = "setup.Board General Info"
        self.check_config(current_key, self.file_path)

    def test_get_section_with_prototype(self):
        from .tests_output.output_generator_sheet_HW import CommonTestCharacterization
        current_key = "setup.Common Test Characterization"
        prototype = CommonTestCharacterization()
        self.check_config(current_key, self.file_path, prototype)

    def check_config(self, key, c_file, prototype=None):
        manager = ExcelReaderHw()
        obj = manager.get_obj(c_file, key, prototype)
        print(self.print_obj(obj))
        self.assertIsNotNone(obj)



