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

import re
import functools
import inspect
import ipaddress
import sys
PY3K = sys.version_info >= (3, 0)

class attrWithDefault(object):
    def __init__(self, def_val, val=None):
        self._default_val = def_val
        self._previous_val = None  # self._default_val
        if val is None:
            self._current_val = def_val
        else:
            self._current_val = val
        self._is_default = True
        self._was_default_set = False
        self._was_written_to_driver = False
        self._driver_field=None

    @property
    def _default_val(self):
        """_default_val : """
        return self.__default_val

    @_default_val.setter
    def _default_val(self, v):
        """_default_val docstring"""
        self.__default_val = v

    @property
    def current_val(self):
        """current_val : """
        return self._current_val

    @current_val.setter
    def current_val(self, v):
        """Holds the current value of the attribute.\n
        Updating the previous value into _previous_val.\n
        Updating the is_default boolean status
        """
        self._previous_val = self._current_val
        self._current_val = v
        if self._current_val != self._default_val:
            self._is_default = False
        else:
            self._is_default = True
        self._was_default_set = True

    @property
    def previous_val(self):
        """previous_val : """
        return self._previous_val

    @previous_val.setter
    def previous_val(self, v):
        self._previous_val = v

    @property
    def was_default_set(self):
        """was_default_set : """
        return self._was_default_set

    @was_default_set.setter
    def was_default_set(self, v):
        self._was_default_set = v


    def _reset_to_default(self):
        # self._previous_val = None  # self._default_val
        # self._current_val = self._default_val
        self._is_default = False
        self._was_default_set = True
        self._was_written_to_driver = False



import functools

def rsetattr(obj, attr, val):
    pre, _, post = attr.rpartition('.')
    return setattr(rgetattr(obj, pre) if pre else obj, post, val)

sentinel = object()
def rgetattr(obj, attr, default=sentinel):
    if default is sentinel:
        _getattr = getattr
    else:
        def _getattr(obj, name):
            return getattr(obj, name, default)
    return functools.reduce(_getattr, [obj]+attr.split('.'))


class _stat_member(object):

    def __init__(self, enable=True, return_type=int, default_val=-1):
        previous_frame = inspect.currentframe().f_back
        (filename, line_number,function_name, lines, index) = inspect.getframeinfo(previous_frame)
        self._name = lines[0].split()[0].replace("self._", "")
        self._value = -1
        self._default_val = default_val
        self._previous = -1
        self._enable = enable
        self._stats_return_type = return_type

    def _set_return_type(self,type):
        if type == int:
            self._stats_return_type = int
        elif type == str:
            self._stats_return_type = str

    def _clear(self):
        self._value = self._default_val

    @property
    def value(self):
        if self._stats_return_type == int:
            return int(float(self._value))
        elif self._stats_return_type == str:
            return str(self._value)

    @value.setter
    def value(self, v):
        if v != 'None':
            self._previous = self._value
            self._value = v

    def get_previous_value(self):
        return self._previous

    def set_state(self, enable=True):
        self._enable = enable

    def get_state(self):
        return self._enable



def _generate_getter_setter(list_of_attr):
    for attr in list_of_attr:
        print("@property\ndef {}(self):\n\treturn self._{}.value\n".format(attr,attr))
        print("@{}.setter\ndef {}(self, v):\n\tself._{}.value = v\n".format(attr, attr, attr))


if __name__ == "__main__":
    my_list = [
        "average_latency",
"big_sequence_error",
"bit_rate",
"byte_rate",
"duplicate_frames",
"first_time_stamp",
"frame_rate",
"last_time_stamp",
"max_delay_variation",
"max_latency",
"max_min_delay_variation",
"maxmin_interval",
"min_delay_variation",
"min_latency",
"num_groups",
"prbs_ber_ratio",
"prbs_bits_received",
"prbs_errored_bits",
"read_time_stamp",
"reverse_sequence_error",
"sequence_gaps",
"small_sequence_error",
"standard_deviation",
"total_byte_count",
"total_frames",
"total_sequence_error",
    ]
    _generate_getter_setter(my_list)

class Converter():
    reIxiaPortFormat = re.compile(r"(?:{((?:\d+\s*){3})})")
    uc23 = str if PY3K else unicode

    @classmethod
    def convertstring2int(cls,string):
        if string.count(':'):
            return cls.stringMac2int(string)
        elif string.count('.'):
            return cls.stringIp2int(string)
        elif string.count(' '):
            return cls.stringMac2int(string, ' ')
        else:
            tmp = cls.remove_non_hexa_sumbols(string)
            return int('0x' + tmp, 16)

    @classmethod
    def intIp2string(cls,intIp):
        try:
            res = str(ipaddress.IPv4Address(intIp))
        except Exception as e:
            res = ''
        return res

    @classmethod
    def stringIp2int(cls,stringIP,delimiter = '.'):
        octets_list = stringIP.split(delimiter)
        return functools.reduce(lambda out, x: (out << 8) + int(x), octets_list, 0) if len(octets_list) == 4 else None
    @classmethod
    def stringMac2int(cls,stringMac,delimiter = ':'):
        hex_mac = '0x'+stringMac.replace(delimiter,'')
        return int(hex_mac, 16)
    @classmethod
    def remove_non_hexa_sumbols(cls,input):
        return re.sub("[^0-9a-fA-F]", "", input)
    @classmethod
    def ixia_ports_string_2list(cls,ixia_ports_string):
        return cls.reIxiaPortFormat.findall(ixia_ports_string)
    @classmethod
    def hexaString2int(cls,hexa_string):
        return int(hexa_string, 16)

    @classmethod
    def expand_ipv6(cls,input):
        uc = str if PY3K else unicode
        addr = ipaddress.ip_address(uc(input))
        return addr.exploded

