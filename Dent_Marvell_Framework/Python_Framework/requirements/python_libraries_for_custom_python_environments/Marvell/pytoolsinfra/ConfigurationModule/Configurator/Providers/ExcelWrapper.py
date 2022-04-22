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
import os
import win32com.client

from Marvell.pytoolsinfra.ConfigurationModule.Configurator.Utilities import ConfiguratorUtils

# Good reference code
# https://docs.microsoft.com/en-us/previous-versions/office/developer/office-2003/aa220733(v%3doffice.11)

class ExcelWrapper(object):
    """
        This class is wrapping the use of Excel application using COM technology
    """

    def __init__(self):
        self._file_name = ""
        self._is_open = False
        self._current_wb = None
        # Open Excel
        self._application = win32com.client.Dispatch("Excel.Application")

    def setVisibility(self, show=True):
        """
        Set the visibility of the excel application
        :param show:
        :return:
        """
        self._application.Visible = show

    def validate_open(self):
        if not self.IsOpen:
            raise Exception("No file is open.\nPlease first open Excel file.")

    @property
    def IsOpen(self):
        return self._is_open and self._current_wb is not None

    def openFile(self, file_path):
        """
         Open the given filename and return the workbook

         :param file_path: the path to open
         :type file_path: string
        """
        if self._is_open:
            self.CloseFile()

        try:
            if os.path.exists(file_path):
                self._current_wb = self._application.Workbooks.Open(file_path)

            else:
                self._current_wb = self._application.Workbooks.Add()
                self._current_wb.SaveAs(file_path)
        except Exception as e:
            raise Exception("The file couldn't be open please check: " + e.message)

        self._file_name = self._current_wb.FullName
        self._is_open = True
        return True

    def CloseFile(self):
        """
         Close workbook file if open.
        """
        if self._is_open:
            self.saveFile()
            self._current_wb.Close()

        self._is_open = False

    def CreateSheet(self, sheet_name, sheet_index=None):
        """
        Create a worksheet (at an optional index).

        :param sheet_name: optional title of the sheet
        :type sheet_name: basestring
        :param sheet_index: optional position at which the sheet will be inserted
        :type sheet_index: int

        :return: boolean
        """
        self.validate_open()
        try:
            ws = self._current_wb.Worksheets(sheet_name)
        except: # If we got exception this sheet is not exists yet
            ws = self._current_wb.Worksheets.Add()
            ws.Name = sheet_name
        return ws is not None

    def setCellVal(self, sheet_name, row, col, val):
        """
        Sets cell value
        :param sheet_name: The name of the Sheet you need to set the cell value in
        :param row: Row number inside the sheet
        :param col: Column number inside the sheet
        :param val: the value to set
        :return: boolean if succeeded
        """
        self.validate_open()

        ws = self._current_wb.Worksheets(sheet_name)
        cell = ws.Cells(row, col)
        cell.NumberFormat = self.get_cell_format(val)
        cell.Value = val
        return True

    def setCellsValues(self, sheet_name, cells_data_list):
        """
        Sets cell value
        :param sheet_name: The name of the Sheet you need to set the cell value in
        :param cells_data_list: a list of the cells you want to set the format should be
                                [{"row": 1,"col": 2, "val": 3},...]
        :return: boolean if succeeded
        """
        self.validate_open()

        ws = self._current_wb.Worksheets(sheet_name)

        for cell_data in cells_data_list:
            cell = ws.Cells(cell_data.get('row'), cell_data.get('col'))
            cell.NumberFormat = self.get_cell_format(cell_data.get('val'))
            cell.Value = cell_data.get('val')
        return True

    def getCellVal(self, sheet_name, row, col):
        """
        Sets cell value
        :param sheet_name: The name of the Sheet you need to set the cell value in
        :param row: Row number inside the sheet
        :param col: Column number inside the sheet
        :param val: the value to set
        :return: boolean if succeeded
        """
        self.validate_open()

        ws = self._current_wb.Worksheets(sheet_name)
        cell = ws.Cells(row, col)
        return self.get_numeric_value(cell.Value)

    def setCellBold(self, sheet_name, row, col):
        """
        Sets cell text to bold
        :param sheet_name: The name of the Sheet you need to set the cell value in
        :param row: Row number inside the sheet
        :param col: Column number inside the sheet
        :return: boolean if succeeded
        """
        self.validate_open()

        ws = self._current_wb.Worksheets(sheet_name)
        cell = ws.Cells(row, col)
        cell.Font.Bold = True
        return True

    def getCellBold(self, sheet_name, row, col):
        """
        Sets cell value
        :param sheet_name: The name of the Sheet you need to set the cell value in
        :param row: Row number inside the sheet
        :param col: Column number inside the sheet
        :param val: the value to set
        :return: boolean if succeeded
        """
        self.validate_open()

        ws = self._current_wb.Worksheets(sheet_name)
        cell = ws.Cells(row, col)
        return cell.Font.Bold

    @staticmethod
    def get_numeric_value(raw_value):
        float_val = ConfiguratorUtils.parse_float(raw_value)
        int_val = ConfiguratorUtils.parse_integer(raw_value)
        cell = raw_value
        if float_val is not None and int_val is not None:
            if float_val == int_val:
                cell = int_val
            else:
                cell = float_val
        elif int_val:
            cell = int_val
        elif float_val:
            cell = float_val
        return cell

    @staticmethod
    def get_cell_format(raw_value):
        float_val = ConfiguratorUtils.parse_float(raw_value)
        int_val = ConfiguratorUtils.parse_integer(raw_value)
        format = "General"
        if float_val is not None and int_val is not None:
            if float_val == int_val:
                format = "0"
            else:
                format = "0.00"
        elif int_val:
            format = "0"
        elif float_val:
            format = "0.00"
        return format

    def setCellTextColor(self, sheet_name, row, column, color):
        """
        Sets the text color of a given cell

        :param sheet_name: The name of the Sheet you need to set the cell Text Color in
        :param row: Row number inside the sheet
        :param column: Column number inside the sheet
        :param color: a RGB tuple that represents the text color
        :return: boolean if succeeded
        """
        self.validate_open()

        ws = self._current_wb.Worksheets(sheet_name)
        cell = ws.Cells(row, column)

        cell.Font.Color = self.rgb_to_hex(color)

    def getCellTextColor(self, sheet_name, row, column):
        """
        Sets the text color of a given cell

        :param sheet_name: The name of the Sheet you need to set the cell Text Color in
        :param row: Row number inside the sheet
        :param column: Column number inside the sheet
        :param color: a RGB tuple that represents the text color
        :return: boolean if succeeded
        """
        self.validate_open()

        ws = self._current_wb.Worksheets(sheet_name)
        cell = ws.Cells(row, column)

        return cell.Font.Color

    def setCellBgColor(self, sheet_name, row, column, color):
        """
        Sets the BG color of a given cell

        :param sheet_name: The name of the Sheet you need to set the cell BG Color in
        :param row: Row number inside the sheet
        :param column: Column number inside the sheet
        :param color: string representing the Color number
        :return: boolean if succeeded
        """

        self.validate_open()

        ws = self._current_wb.Worksheets(sheet_name)
        cell = ws.Cells(row, column)

        cell.Interior.Color = self.rgb_to_hex(color)

        return True

    def getCellBgColor(self, sheet_name, row, column):
        """
        Sets the BG color of a given cell

        :param sheet_name: The name of the Sheet you need to set the cell BG Color in
        :param row: Row number inside the sheet
        :param column: Column number inside the sheet
        :param color: string representing the Color number
        :return: boolean if succeeded
        """

        self.validate_open()

        ws = self._current_wb.Worksheets(sheet_name)
        cell = ws.Cells(row, column)

        return cell.Interior.Color

    def saveFile(self):
        self.validate_open()

        self._current_wb.Save()

    def rgb_to_hex(self, rgb):
        strValue = '%02x%02x%02x' % (rgb[2], rgb[1] , rgb[0])
        iValue = int(strValue, 16)
        return iValue

    # def _rgbToInt(rgb):
    #     colorInt = rgb[0] + (rgb[1] * 256) + (rgb[2] * 256 * 256)
    #     return colorInt
