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

from Marvell.pytoolsinfra.ConfigurationModule.Configurator.Providers.ExcelWrapper import ExcelWrapper
from os import path, getcwd, remove

THIS_FOLDER = path.dirname(path.realpath(__file__)) + '\\'


file_path = THIS_FOLDER + r"..\assets\Test.xlsx"
sheet_name = "Test_Sheet"

cwd = getcwd()
wb = ExcelWrapper()
wb.setVisibility()
file_path = path.join(cwd, file_path)
# Create Excel File for every test
wb.openFile(file_path)

wb.CreateSheet(sheet_name)
wb.setCellVal(sheet_name, 1, 2, 34543545454567.1)
wb.setCellVal(sheet_name, 1, 3, 4.568)
wb.setCellVal(sheet_name, 1, 4, "Test")


