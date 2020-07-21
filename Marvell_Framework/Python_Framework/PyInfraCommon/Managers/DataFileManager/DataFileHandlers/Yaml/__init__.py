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
from PyInfraCommon.ExternalImports.ResourceManager import ConfigManager


class YamlServices(object):

	"""
	this class provides all Yaml file services in one place
	you should provide path to yaml file on the class init
	"""
	def __init__(self,yaml_file_path=None):
		self._manager = ConfigManager()
		self._yaml_file_path = yaml_file_path
		self.file_path = yaml_file_path

	@property
	def file_path(self):
		return self._yaml_file_path

	@file_path.setter
	def file_path(self,path):
		self._yaml_file_path = path

	def read_config_file(self):
		"""
		Reads the given file_path and parse it to object
		:param file_path:
        :return: an object described by the file
		"""
		res = self._manager.read_config_file(self.file_path)
		return res

