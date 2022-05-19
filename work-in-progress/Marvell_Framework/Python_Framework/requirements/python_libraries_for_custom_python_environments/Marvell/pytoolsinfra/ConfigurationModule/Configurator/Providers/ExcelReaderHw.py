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

from Marvell.pytoolsinfra.ConfigurationModule.Configurator.Providers.BaseExcelReader import BaseExcelReader

class ExcelReaderHw(BaseExcelReader):
    def __init__(self):
        super(self.__class__, self).__init__()
        self._section_title_mark = "***"
        self._section_title_char = '*'
        self._section_title_index = 1
        self._row_data_end = '$$$'

    def update_entry_data(self, obj, entry_name, clo_index, cell_data, entry_key=""):
        if clo_index == 0:
            obj[entry_name] = []
        else:
            obj[entry_name].append(cell_data)

# This line decorates all the functions in this class with the "LogWith" decorator
# ExcelReader = Log_all_class_methods(ExcelReader, config_logger, show_params)
