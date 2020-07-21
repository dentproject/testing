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
# utils for dict functions
from builtins import str
from builtins import range
from builtins import object
import random
import sys
from collections import OrderedDict
from PyInfraCommon.GlobalFunctions.Utils.Function import GetFunctionName
from PyInfraCommon.ExternalImports.Logger import BaseTestLogger
from prettytable import PrettyTable


class DictFunctions(object):
    """
    this class extends dicts with some useful methods
    """
    @staticmethod
    def strip_keys(dic,keys):
        """
        this functions scans the dictionary and removes the inputs keys from it
        :param dic:  the dictionary to work on
        :param keys: keys to strip from
        :type dic:OrderedDict()
        :type keys: list| set | tuple
        :return: None, works on the dic by reference
        """
        for key, val in list(dic.items()):
            if isinstance(val, (dict,OrderedDict)):
                # recursively remove keys from dic
                 DictFunctions.strip_keys(val, keys)
            else:
                if key in keys:
                    dic.pop(key)
                    
    @staticmethod
    def move_inner_child_value_to_parent(dic, child_key):
        """
        this functions scans dictionary for a values that are dict that contains child keys,
        if found it moves childs_value to parent value
        e.g. dict["param1"]["value"] : 1 == > dict["param1"] = 1
        :param dic: input dict
        :type dic: dict
        :param child_key:
        :return:
        """
        for key,val in list(dic.items()):
            if isinstance(val,dict):
                if child_key in list(val.keys()):
                    # move to parent dict
                    val2move = val[child_key]
                    dic[key] = val2move
                else:
                    DictFunctions.move_inner_child_value_to_parent(val,child_key)

    @staticmethod
    def move_redundant_keys_values_as_parent(dic):
        """
        this functions scans dictionary for a values that are dict that contains child key with name as dict key holding it
        if found it moves childs_value to parent value
        e.g. dict["param1"]["param1"] :1 == > dict["param1"] : 1
        :param dic: input dict
        :type dic: dict
        :param child_key:
        :return:
        """
        for key,val in list(dic.items()):
            if isinstance(val,dict):
                if len(val) == 1 and key.lower() == list(val.keys())[0].lower():
                    val2move = val[list(val.keys())[0]]
                    dic[key] = val2move
                    # keep scanning recursivley
                    DictFunctions.move_redundant_keys_values_as_parent(dic)
                else:
                    # keep scanning recursivley
                    DictFunctions.move_redundant_keys_values_as_parent(val)


    @staticmethod
    def get_dict_as_table_string(dic, table_titile):
        """
        :param dic:input dict
        :type dic: dict
        :param table_titile: table title
        :type table_titile: str
        :return: pretty table string with all keys as cols
        :rtype:
        """
        funcname = GetFunctionName(DictFunctions.get_dict_as_table_string)
        if not bool(dic):
            print(funcname+"Warning:input dict is empty")

        table = PrettyTable()
        table.title = table_titile
        cols = list(dic.keys())
        if not isinstance(cols[0],str):
            for i in range(len(cols)):
                cols[i] = str(cols[i])
        table.field_names = cols
        table.add_row(list(dic.values()))
        return table.get_string()

    @staticmethod
    def merge(src_dict,dest_dict):
        """
        merges source dict into destination dict, for any existing dict key, if value is a list then merges 2 lists
        this overrides dict.update method that causes values to get ovverun for existing keys
        :param src_dict: source dict to take new values from
        :type src_dict: dict
        :param dest_dict: destination dict where the  new key-values pairs will be updated
        :type dest_dict: dict
        :return:
        :rtype:
        """
        for key,value in list(src_dict.items()):
            if dest_dict.get(key) and isinstance(value,list):
                src = value
                dest_dict[key] = dest_dict[key] + src
            else:
                dest_dict[key] = value
        if not bool(src_dict):
            return dest_dict

    @staticmethod
    def is_subset(subset, superset):
        """

        :param subset: the subset dict to check
        :type subset: dict
        :param superset: the superset dict to check
        :type superset: dict
        :return: True if subset is a subset of superset
        :rtype: bool
        """
        if sys.version_info[0] < 3:
            return subset.viewitems() <= superset.viewitems()
        return subset.items() <= superset.items()






class RandomOrderedDict(OrderedDict):
    """
    this class extends OrderdDict to support randomize function
    """
    def __init__(self,logger=None,*args, **kwargs):
        OrderedDict.__init__(self,*args,**kwargs)
        self.random_seed_value = None
        self._orig_dict = None # type:RandomOrderedDict
        self.logger = logger  # type:BaseTestLogger
        
    def Shuffle(self, force_seed_value=None):
        """
        randomize the dict keys entries
        saving and printing the seed value for recovery
        :param force_seed_value: if given will use the seed value to randomize list
        :type force_seed_value:int
        :return: True on success
        :rtype:
        """
        res = True
        max_random_size = 10000000
        SEED = 0
        funcname = GetFunctionName(self.Shuffle)
        if not list(self.keys()):
            err = funcname + "dict is empty"
            print(err)
            res = False
        else:
            self._orig_dict = OrderedDict(self) # save original dictionary
            self.random_seed_value = force_seed_value
            if force_seed_value is None:
                # generate random seed value since it was not
                self.random_seed_value = random.randrange(max_random_size)
            random.seed(self.random_seed_value)
            if self.logger:
                self.logger.debug(funcname +" Seed Value: {}".format(self.random_seed_value))
            keys = list(self.keys())
            random.shuffle(keys)
            new_dict = RandomOrderedDict(self.logger)
            for index,value in enumerate(self.values()):
                self[keys[index]] = value
        return res
        
        


