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
from builtins import object
from Marvell.pytoolsinfra.ConfigurationModule.Configurator.Providers.BaseExcelReader import BaseExcelReader
from Marvell.pytoolsinfra.ConfigurationModule.Configurator.Providers.YamlReader import YamlReader
from Marvell.pytoolsinfra.ConfigurationModule.Configurator.Providers.YamlReader import ConfigReader
from Marvell.pytoolsinfra.ConfigurationModule import *
from shutil import copyfile
import os
import errno


class ConfigManager(object):
    readers = [ConfigReader()]
    readers.pop(0)

    def __init__(self):
        self.readers = [BaseExcelReader(), YamlReader()]
        self.temp_dir = os.path.join(os.getenv('APPDATA', '/tmp'), 'pytoolsinfra', 'ConfigurationModule') #tmpdir for Windows=APPDATA Linux=/tmp

    def get_reader(self, config_file):
        file_extension = os.path.splitext(config_file)[1]
        for reader in self.readers:
            if file_extension in reader.support_types.lower():
                return reader

        config_logger.error("----ERROR----> ConfigManager: No reader found for file type " + str(file_extension))
        return None

    def read_config_file(self, file_path):
        """
        Reads the given file_path and parse it to object

        :param file_path: the path of the config file
        :return: an object described by the file
        """
        filename, file_extension = os.path.splitext(file_path)
        for reader in self.readers:
            if file_extension in reader.support_types.lower():
                return reader.read_config_file(file_path)
        config_logger.error("----ERROR----> ConfigManager: No reader found for file type " + str(file_extension))

    def get_obj(self, key, config_file, ret_obj=None, work_local=True, similar_threshold=0.7, pack_result=True,
                apply_format=True, section_type_key=None):
        """
        key - "sheet_name.section_name"
        Fills the ret_obj with the data from config_file
        If ret_obj is None - returns a new dynamic object
        Possible errors: FileNotFound, FileNotSupported, unresolved_key
        pack_result - a flag to determine if to return an object(True) or a dict(False)
        section_type_key - the attribute name to inject to dynamic obj that can be used to parse the section obj type
        If file is not local copy it to temp folder and use it
        """
        if isinstance(config_file, bytes):
            config_file = config_file.decode('utf-8')

        config_logger.debug("Reading config file get_obj " + config_file)
        config_path = config_file
        if work_local:
            here = os.path.dirname(os.path.realpath(__file__))
            abs_config = os.path.abspath(config_file)
            work_drive = os.path.splitdrive(here)[0]
            config_drive = os.path.splitdrive(abs_config)[0]

            if work_drive != config_drive:
                file_name_with_extension = os.path.basename(config_file)
                config_path = os.path.join(self.temp_dir, file_name_with_extension)
                try:
                    os.makedirs(os.path.dirname(config_path))
                except OSError as exc:  # Guard against race condition
                    if exc.errno != errno.EEXIST:
                        raise
                copyfile(abs_config, config_path)

        reader = self.get_reader(config_path)
        if reader is not None:
            # for excel reader input the section_type_key
            if isinstance(reader, BaseExcelReader):
                ret = reader.get_obj(config_path, key, ret_obj, similar_threshold, pack_result, apply_format,
                                     section_type_key)
            else:
                ret = reader.get_obj(config_path, key, ret_obj, similar_threshold, pack_result, apply_format)
            config_logger.debug("Finished reading config file get_obj " + config_file)
            return ret

        return None

# This line decorates all the functions in this class with the "LogWith" decorator
# ConfigManager = Log_all_class_methods(ConfigManager, config_logger, show_params)
