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
from Marvell.pytoolsinfra.ConfigurationModule.Configurator.ConfigurationManager.ConfigManager import ConfigManager

THIS_FOLDER = path.dirname(path.realpath(__file__)) + '\\'


class TestConfigManager(TestCase):
    file_path = THIS_FOLDER + r"..\assets\Setup_Example.xls"
    file_path_mi = THIS_FOLDER + r"..\assets\Setup_MI.xls"
    remote_mi = r"\\fileril103\dev\Objects\Jenkins_2.0\Python Test\Setup_MI1.xls"
    file_path_cv = THIS_FOLDER + r'..\assets\Setup_CV.xls'

    def test_read_config_file(self):
        current_config_file = THIS_FOLDER + r"..\Configurator\Core\config.yaml"

        manager = ConfigManager()
        obj = manager.read_config_file(current_config_file)
        print(self.print_obj(obj))
        self.assertIsNotNone(obj)

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
        current_key = "SetupInfo"
        self.check_config(current_key, self.file_path_cv)

    def test_get_section_no_prototype(self):
        current_key = "SetupInfo.Communication Settings"
        self.check_config(current_key, self.file_path_cv)

    def test_get_table_no_prototype(self):
        current_key = "TGConnectionTableSheet.TG Connection Table"
        self.check_config(current_key, self.file_path_cv)

    def test_get_section_with_prototype(self):
        from Marvell.pytoolsinfra.ConfigurationModule.ConfigurationModuleUT.tests_output.output_generator_workbook import \
            CommunicationSettings
        current_key = "SetupInfo.Communication Settings"
        prototype = CommunicationSettings()
        self.check_config(current_key, self.file_path_cv, prototype)

    def test_get_table_section_no_prototype(self):
        current_key = "TGConnectionTableSheet.Table2"
        self.check_config(current_key, self.file_path_cv)

    def test_get_table_section_with_prototype(self):
        from Marvell.pytoolsinfra.ConfigurationModule.ConfigurationModuleUT.tests_output.output_generator_workbook import \
            Table2
        current_key = "TGConnectionTableSheet.Table2"
        prototype = Table2()
        self.check_config(current_key, self.file_path_cv, prototype)

    def test_get_section_remote_success_rate(self):
        from Marvell.pytoolsinfra.ConfigurationModule.ConfigurationModuleUT.output_generator_section1 import Tgsettings
        prototype = Tgsettings()
        current_key = "SetupInfo.TGSettings"
        self.check_config(current_key, self.remote_mi, prototype)

    def test_remote_serial1(self):
        from Marvell.pytoolsinfra.ConfigurationModule.ConfigurationModuleUT.output_generator_sheet1 import Serial
        prototype = Serial()
        current_key = "SetupInfo.Serial1"
        self.check_config(current_key, self.remote_mi, prototype)

    def test_get_sheet_remote_success_rate(self):
        from Marvell.pytoolsinfra.ConfigurationModule.ConfigurationModuleUT.output_generator_sheet1 import SetupInfo
        prototype = SetupInfo()
        current_key = "SetupInfo"
        self.check_config(current_key, self.remote_mi, prototype)

    def test_get_workbook_remote_success_rate(self):
        from Marvell.pytoolsinfra.ConfigurationModule.ConfigurationModuleUT.output_generator_book1 import SetupMI1
        current_key = ""
        prototype = SetupMI1()
        self.check_config(current_key, self.remote_mi, prototype)

    def test_get_workbook_remote_no_prototype(self):
        current_key = ""
        self.check_config(current_key, self.remote_mi)

    def test_get_workbook_remote_no_pack(self):
        current_key = ""
        self.check_config(current_key, self.remote_mi)

    def check_config(self, key, c_file, prototype=None):
        manager = ConfigManager()
        obj = manager.get_obj(key, c_file, prototype)
        print(self.print_obj(obj))
        self.assertIsNotNone(obj)
