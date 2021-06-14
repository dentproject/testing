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
from abc import ABCMeta, abstractmethod
import re

from future.types import newbytes

from Marvell.pytoolsinfra.ConfigurationModule.Configurator.Utilities import ConfiguratorUtils
from future.utils import with_metaclass


class ABCConfigurationReader(with_metaclass(ABCMeta, object)):
    def __init__(self):
        raise NotImplementedError("Cannot instantiate abstract class!")

    _support_types = ""
    _base_config_path = None

    @property
    def support_types(self):
        return self._support_types

    @support_types.setter
    def support_types(self, value):
        self._support_types = value

    @support_types.deleter
    def support_types(self):
        del self._support_types

    @abstractmethod
    def read_config_file(self, file_path):
        """
                Reads the give file_path and parse it to object
                :return: an object described by file_path
                """
        pass

    @abstractmethod
    def get_obj(self, file_path, key, obj=None, similar_threshold=0.7, pack_result=True, apply_format=True):
        """
                Reads the give file_path and parse it to object
                :return: an object described by file_path
                """
        pass

    @staticmethod
    def low_strip(io_string, remove=None, is_class_name=False, make_low=True):
        if remove is None:
            remove = []
        # to remove any Befor/After spaces
        if type(io_string) is str :
            new_string = str(io_string).strip()
        elif type(io_string) is bytes or type(io_string) is newbytes:
            new_string = io_string.decode("utf-8").strip()
        else:
            new_string = str(io_string).strip()

        for item in remove:
            new_string = new_string.replace(item, "")

        # To make sure we remove any Befor/After spaces after we removed the "remove" items
        new_string = str(new_string).strip()

        if is_class_name:
            new_string = new_string.replace(" ", "").replace("-", "")
        else:
            new_string = new_string.replace("_", " ")
            new_string = re.sub(r"(\w)([A-Z][a-z])", r"\1 \2", new_string)
            new_string = new_string.replace(" ", "_").replace("-", "_")
        if make_low:
            new_string = new_string.lower()
        return new_string

    @staticmethod
    def get_numeric_value(raw_value):
        float_val = ConfiguratorUtils.parse_float(raw_value)
        int_val = ConfiguratorUtils.parse_integer(raw_value)
        cell = None
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
