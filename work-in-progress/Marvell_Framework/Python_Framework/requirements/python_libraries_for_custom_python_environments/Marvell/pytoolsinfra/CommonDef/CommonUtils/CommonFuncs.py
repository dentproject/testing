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

from future import standard_library
from future.types.newbytes import unicode

standard_library.install_aliases()
from builtins import str
import sys
import keyword
import builtins as __builtins__
import inspect

from enum import Enum

seqs = tuple, list, set, frozenset


def dict_to_obj(dic):
    top = type('new', (object,), dic)
    for i, j in list(dic.items()):
        if isinstance(j, dict):
            setattr(top, i, dict_to_obj(j))
        elif isinstance(j, seqs):
            setattr(top, i,
                    type(j)(dict_to_obj(sj) if isinstance(sj, dict) else sj for sj in j))
        elif i.isdigit():  # this is a list
            list_len = len(dic)
            top = [0] * list_len
            for key, val in list(dic.items()):
                i_key = int(key)
                if i_key >= list_len:
                    top = top + ([0] * (i_key - list_len + 1))
                    list_len = len(dic)
                top[i_key] = val
            break
        else:
            setattr(top, i, j)
    return top


def str_to_class(the_str, imported_module=None):
    try:
        frm = inspect.stack()[1]
        mod = inspect.getmodule(frm[0])
        instance = getattr(sys.modules[mod.__name__], the_str)
    except AttributeError:
        instance = getattr(imported_module, the_str)
    return instance


def fill_object(prototype, subject):
    if hasattr(prototype, '__dict__'):
        vs = vars(prototype)

        for prop, value in list(vs.items()):
            if '__' not in prop and hasattr(subject, prop):
                if hasattr(value, '__dict__'):
                    fill_object(value, getattr(subject, prop))
                elif isinstance(getattr(subject, prop), list):
                    fill_object_list(value, getattr(subject, prop))
                elif isinstance(getattr(subject, prop), Enum):
                    setattr(subject, prop, type(getattr(subject, prop))['{}'.format(getattr(prototype, prop))])
                else:
                    setattr(subject, prop, getattr(prototype, prop))  # subject.prop = prototype.prop


def fill_object_list(prototype, subject):
    index = 0
    for item in prototype:
        if isinstance(subject[index], Enum):
            subject[index] = type(subject[index])['{}'.format(str(item))]
        elif isinstance(subject[index], list):
            fill_object_list(item, subject[index])
        elif hasattr(subject[index], "__dict__"):
            fill_object_list(item, subject[index])
        else:
            subject[index] = item
        index += 1



built_ins = dir(__builtins__)


def get_valid_name(name):
    if keyword.iskeyword(name) or name in built_ins:
        return "_" + name
    else:
        return name


def unicode2string(input):
    if isinstance(input, dict):
        return {unicode2string(key): unicode2string(value) for key, value in list(input.items())}
    elif isinstance(input, list):
        return [unicode2string(element) for element in input]
    elif isinstance(input, str):
        return input.encode('utf-8')
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input
