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

from __future__ import absolute_import
from builtins import str
from builtins import object
from .ScriptTypeClassesDictionary import SCRIPT_TYPE_CLASSES
from .ScriptExecuterExceptions import *
import os

class ScriptTypeFactory(object):

    @staticmethod
    def create_script_class(path,script_params=None):
        if path is None:
            raise PathException("No Provided Path!!\nCannot Execute Script")
        assert path is not None
        """parsing the script suffix"""
        script_suffix = "." + str(str(path).split('.')[-1])
        """check if script suffix is a valid suffix specified in SCRIPT_TYPE_CLASSES"""
        if (script_suffix in SCRIPT_TYPE_CLASSES) is False:
            raise WrongTypesException("Given path is to unsupported script type\n The suffix of "
                                      +"the script is: " + script_suffix)

        if os.path.isfile(path) is False:
            raise PathException("Provided Path is NOT exists path!!\nCannot Execute Script")

        """check if params_dict was passed"""
        if script_params is not None:
            """is params_dict that was passed is of dict type"""
            if type(script_params) != type({}):
                raise WrongTypesException("Parameters for script must be passed in dictionary "
                                          "type!!\npassed: " +str(type(script_params)) + "\n")
        try:
            script_class = SCRIPT_TYPE_CLASSES[script_suffix](path,script_params)
        except TypeError as e:
            raise WrongTypesException("Cannot Create Script Class Using Given Parameters.\n"
                                      + e.message)
        return script_class
