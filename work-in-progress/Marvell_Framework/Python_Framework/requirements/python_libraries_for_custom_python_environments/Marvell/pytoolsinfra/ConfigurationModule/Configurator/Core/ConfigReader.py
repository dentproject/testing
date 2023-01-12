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
import os
import socket
from collections import OrderedDict

from Marvell.pytoolsinfra.ConfigurationModule.Configurator.Core.ABCConfigurationReader import ABCConfigurationReader


class ConfigReader(ABCConfigurationReader):
    def __init__(self):
        self._pc_name = os.environ.get('COMPUTERNAME',os.environ.get('HOST')) # gets PT-LTxxxx, For Linux=Host windows=Computername
        self._pc_ip = socket.gethostbyname(socket.gethostname())

    @property
    def pc_name(self):
        return self._pc_name

    @pc_name.setter
    def pc_name(self, value):
        self._pc_name = value

    @pc_name.deleter
    def pc_name(self):
        del self._pc_name

    def read_config_file(self, key):
        pass

    def get_obj(self, file_path, key, obj=None, similar_threshold=0.7, pack_result=True, apply_format=True):
        pass

    def __str__(self):
        string = " ConfigReader: {\n\t"
        for prop, value in list(vars(self).items()):
            string += prop + ": " + str(value) + "\n\t"
        string += "}"
        return string

    def dict_to_obj(self, d):
        top = type('new', (object,), d)
        seqs = tuple, list, set, frozenset
        for i, j in list(d.items()):
            if isinstance(j, (dict,OrderedDict)):
                setattr(top, i, self.dict_to_obj(j))
            elif isinstance(j, seqs):
                setattr(top, i,
                        type(j)(self.dict_to_obj(sj) if isinstance(sj, (dict,OrderedDict)) else sj for sj in j))
            else:
                setattr(top, i, j)
        return top
