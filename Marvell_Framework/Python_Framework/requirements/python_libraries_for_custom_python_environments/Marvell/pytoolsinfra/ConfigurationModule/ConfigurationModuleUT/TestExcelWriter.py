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


# wb.setCellVal(sheet_name, 1, 2, 11)
# wb.setCellTextColor(sheet_name, 1, 2, (255, 0, 0))
# wb.setCellBgColor(sheet_name, 1, 2, (0, 255, 0))

# print wb._current_wb[sheet_name]['A1'].value
# wb.saveFile()
# wb.CloseFile()

# FIX FOR JENKINS MACHINE IN ORDER TEST TO RUN CORRECTLY:
# The automatic process that launches Python from Jenkins calls Excel when using xlswrite.
# It uses a Windows system user account to launch the process and Excel is looking for the 'Desktop' directory within this system account.
# For x64 processes create the following folder:
# C:\Windows\SysWOW64\config\systemprofile\Desktop
# For x86 processes create the following folder:
# C:\Windows\System32\config\systemprofile\Desktop

from unittest import TestCase
from Marvell.pytoolsinfra.ConfigurationModule.Configurator.Providers.ExcelWrapper import ExcelWrapper
from os import path, getcwd, remove

THIS_FOLDER = path.dirname(path.realpath(__file__)) + '\\'

class TestExcelWrapper(TestCase):
    file_path = THIS_FOLDER + r"..\assets\Test.xlsx"
    sheet_name = "Test_Sheet"
    wb = None

    @classmethod
    def setUpClass(cls):
        cwd = getcwd()
        cls.wb = ExcelWrapper()
        cls.wb.setVisibility()
        cls.file_path = path.join(cwd , cls.file_path)
        # Create Excel File for every test
        cls.wb.openFile(cls.file_path)

    @classmethod
    def tearDownClass(cls):
        cls.wb.CloseFile()
        remove(cls.file_path)
        cls.wb._application.Quit()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_create_sheet(self):
        ret = self.wb.CreateSheet(self.sheet_name)
        self.assertTrue(ret)

    def test_set_cell_val(self):
        ret = self.wb.CreateSheet(self.sheet_name)
        self.assertTrue(ret)
        set_val = "Test Excel Wrapper"
        self.wb.setCellVal(self.sheet_name, 1, 2, set_val)
        ret_val = self.wb.getCellVal(self.sheet_name, 1, 2)
        self.assertEqual(set_val, ret_val)

    def test_set_cells_vals(self):
        ret = self.wb.CreateSheet(self.sheet_name)
        self.assertTrue(ret)
        cells_data = []
        col = 2
        set_val = "Test Excel Wrapper"
        num_cells = 10
        for i in range(1, num_cells):
            row_data = {}
            row_data["row"] = i
            row_data["col"] = col
            row_data["val"] = "{} - {},{}".format(set_val, i, col)

            cells_data.append(row_data)

        self.wb.setCellsValues(self.sheet_name, cells_data)

        for i in range(1, num_cells):
            ret_val = self.wb.getCellVal(self.sheet_name, i, 2)
            self.assertEqual("{} - {},{}".format(set_val, i, 2), ret_val)

    # def test_set_cells_vals_old(self):
    #     ret = self.wb.CreateSheet(self.sheet_name)
    #     self.assertTrue(ret)
    #     col = 2
    #     set_val = "Test Excel Wrapper"
    #     num_cells = 10
    #     for i in range(1, num_cells):
    #         self.wb.setCellVal(self.sheet_name, i, col, "{} - {},{}".format(set_val, i, col))
    #
    #     for i in range(1, num_cells):
    #         ret_val = self.wb.getCellVal(self.sheet_name, i, 2)
    #         self.assertEqual("{} - {},{}".format(set_val, i, 2), ret_val)

    def test_cell_text_color(self):
        ret = self.wb.CreateSheet(self.sheet_name)
        self.assertTrue(ret)
        set_val = "Test Excel Wrapper"
        self.wb.setCellVal(self.sheet_name, 1, 2, set_val)

        set_color = (0, 0, 255)
        self.wb.setCellTextColor(self.sheet_name, 1, 2, set_color)
        ret_color = self.wb.getCellTextColor(self.sheet_name, 1, 2)
        self.assertEqual(self.wb.rgb_to_hex(set_color), ret_color)

    def test_cell_bg_color(self):
        ret = self.wb.CreateSheet(self.sheet_name)
        self.assertTrue(ret)
        set_color = (255, 0, 0)
        self.wb.setCellBgColor(self.sheet_name, 1, 2, set_color)
        ret_color = self.wb.getCellBgColor(self.sheet_name, 1, 2)
        self.assertEqual(self.wb.rgb_to_hex(set_color), ret_color)

    def test_cell_bold(self):
        ret = self.wb.CreateSheet(self.sheet_name)
        self.assertTrue(ret)

        self.wb.setCellBold(self.sheet_name, 1, 2)
        ret_bold = self.wb.getCellBold(self.sheet_name, 1, 2)
        self.assertTrue(ret_bold)


# def suite():
#     suite = TestSuite()
#     # suite.addTest(TestExcelWrapper('test_create_sheet'))
#     suite.addTest(TestExcelWrapper('test_set_cell_val'))
#     return suite
#
# if __name__ == '__main__':
#     runner = TextTestRunner()
#     runner.run(suite())
