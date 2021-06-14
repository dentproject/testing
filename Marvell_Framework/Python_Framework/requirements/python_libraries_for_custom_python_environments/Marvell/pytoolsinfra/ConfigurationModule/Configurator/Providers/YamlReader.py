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

from builtins import str
# import yaml
from Marvell.pytoolsinfra.ConfigurationModule import *
from Marvell.pytoolsinfra.ConfigurationModule.Configurator.Core.ConfigReader import ConfigReader


class YamlReader(ConfigReader):
    def __init__(self):
        super(self.__class__, self).__init__()
        self._support_types += ".yaml "

    def read_config_file(self, file_path):
        import yaml
        config_logger.debug("Reading config file " + file_path)
        if os.path.isfile(file_path):
            self._base_config_path = file_path
            with open(self._base_config_path, "r") as file_descriptor:
                data = yaml.load(file_descriptor, Loader=yaml.FullLoader)
                obj = self.dict_to_obj(data)
                config_logger.debug("Finished reading config file " + file_path)
                return obj
        else:
            config_logger.error("----ERROR----> YamlReader - Can't find file: " + str(file_path))

    def get_obj(self, file_path, key, obj=None, similar_threshold=0.7, pack_result=True, apply_format=True):
        pass


# This line decorates all the functions in this class with the "LogWith" decorator
# YamlReader = Log_all_class_methods(YamlReader, config_logger, show_params)
