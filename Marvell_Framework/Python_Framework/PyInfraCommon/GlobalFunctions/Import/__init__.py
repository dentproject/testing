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

import imp
from PyInfraCommon.Globals.Logger.GlobalTestLogger import GlobalLogger
from PyInfraCommon.GlobalFunctions.Utils.Function import GetFunctionName


def loadDynamicModule(moduleName,modulePath):
	"""
	trys to load a moudle from a given path
	:param moduleName:
	:param modulePath:
	:return: loaded module or None if not found
	"""
	funcname = GetFunctionName(loadDynamicModule)
	f = None
	try:
		f, filename , description = imp.find_module(moduleName,[modulePath])
		mod = imp.load_module(moduleName,f, filename , description)
		if mod is not None:
			return mod
		GlobalLogger.logger.error(funcname + " Failed to load module")
		return None
	except Exception as e:
		GlobalLogger.logger.error(funcname+" Failed to load module got error:\n"+str(e))
		return None
	finally:
		if f:
			f.close()

