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

import xlrd
import os
from Marvell.pytoolsinfra.ConfigurationModule.Configurator.Core.ABCConfigurationReader import ABCConfigurationReader
from Marvell.pytoolsinfra.ConfigurationModule.Generator.CodeGenerator import CodeGenerator

indent = "  "
indentX2 = "    "
indentX4 = "        "
indentX8 = "            "


class CodeGeneratorHw(CodeGenerator):
    def __init__(self):
        super(CodeGeneratorHw, self).__init__()

        self._section_title_mark = "***"
        self._section_title_index = 1
        self._default_members_value = '[]'


    def get_base_obj(self, i_sheet_name, file_path=None):
        """
        Gets the basic object defined by the sheet
        typically the object will be constructed by members named by the first row of the sheet
        :param i_sheet_name: the requested sheet name
        :param file_path: the path to the xsl file
        :return: returns a GeneratorObject presentation of the sheet object
        """
        return None

