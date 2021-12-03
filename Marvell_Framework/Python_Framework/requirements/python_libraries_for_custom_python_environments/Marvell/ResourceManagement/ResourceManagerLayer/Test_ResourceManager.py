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
from __future__ import absolute_import
from Marvell.pytoolsinfra.ConfigurationModule.Configurator.ConfigurationManager.ConfigManager import ConfigManager

from Marvell.ResourceManagement.ResourceManagerLayer.Setup_CV import SetupInfo
from Marvell.ResourceManagement.ResourceManagerLayer.TG_Settings import TG_ConnectionTable
from Marvell.ResourceManagement.ResourceManagerLayer.ResourceManager import ResourceManager

# m = ResourceManager.GetSetupPath(setup_name="Aldrin2-1", settings_section_name="SetupsList1.Common Settings",
#                                  attribute_name="Setup Path")
# print (m)

# manager = ConfigManager()
# TGConTable = TG_ConnectionTable()
# SetupXlsPath = r'\\fileril103\testing\New structure\Projects\Automation\Python\Shared\Setups\JetSetup\SetupStas.xlsx'
# TGConTable = manager.get_obj('TG_ConnectionTable', SetupXlsPath, ret_obj=TGConTable)
# print(dir(TGConTable))
#
# SetupXlsPath = r'\\fileril103\TESTING\New structure\Projects\Automation\Python\Shared\Setups\CI\PIPE_DB.xlsx'
# CVSetup = SetupInfo()
# CVSetup = manager.get_obj('SetupInfo',SetupXlsPath , ret_obj=CVSetup)
# print(dir(CVSetup))
#
#
# m = ResourceManager.GetSetupPath(setup_name="PIPE_DB_A385_450MHz_AI_CI_Setup1",
#                                  settings_section_name="SetupNames.Path Settings",
#                                  attribute_name="Path")
# print (m)
#
# # m = ResourceManager.GetSetupPath()
#
# print (m)
#
# m1 = ResourceManager.GetConnectionData("dutmainchannel", "_proto_type", current_config_file=m)
# print (dir(m1))
#
# m = ResourceManager.GetChannel("dutmainchannel", current_config_file=m)
# print (dir(m))