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
from builtins import str
from builtins import range
from builtins import object
import random
from PyInfraCommon.GlobalFunctions.Utils.Function import GetFunctionName
from PyInfraCommon.GlobalFunctions.Utils.MAC import MacManager
from future.utils import with_metaclass

# first octet ranges
_MUTLICAST_RANGE = [224,239]


# Work around for python to allow class method properties
class _ClassProperty(object):
    def __init__(self, getter, setter):
        self.getter = getter
        self.setter = setter
    def __get__(self, cls, owner):
        return getattr(cls, self.getter)()
    def __set__(self, cls, value):
        getattr(cls, self.setter)(value)

class _MetaProp(type):
    SEED = _ClassProperty('_getseed', '_setseed')


class Randomize(with_metaclass(_MetaProp, object)):
    """
    this class provides ability to randomize various data types and sequences
    related
    """
    # privates which should never change
    __UserFixedSEED = None  # user defined fixed seed value
    __LastUsedSeed = None  # the seed value used on last random action
    __default_start = 0
    __default_stop = 1000000000
    __default_step = 1
    
    
    @classmethod
    def _getseed(cls):
        """
        :return: last used seed
        :rtype:
        """
        return cls.__LastUsedSeed
    
    @classmethod
    def _setseed(cls, seed_value):
        """
        manually set the class seed value
        ##################IMPORTANT###################################
        this value will always be used for randomizing in all functions
        - To change seed value call this function again with another value
        - To choose different seed value every time change seed back to None
        :param seed_value: manual numeric value to use as SEED value,
        If None(default) then every call will randomize with different seed value
        :type seed_value:int
        """
        funcname = GetFunctionName(cls.SEED)
        cls.__UserFixedSEED = seed_value
        if seed_value is not None:
            if isinstance(seed_value, int):
                cls.__UserFixedSEED = seed_value
            elif isinstance(seed_value, str) and seed_value.isdigit():
                    cls.__UserFixedSEED = int(seed_value)
            else:
                err = funcname + "manual seed value must be a number"
                raise ValueError(err)
    
    @classmethod
    def _InitSeed(cls):
        """
        sets the seed value of the random library, or uses the manual set value every time
        :return: the seed value that was set
        :rtype:int
        """
        ret = 0
        cls.__LastUsedSeed = cls.__UserFixedSEED
        if cls.__UserFixedSEED is None:
            cls.__LastUsedSeed = random.randrange(cls.__default_stop)
        random.seed(cls.__LastUsedSeed)
        return cls.__LastUsedSeed

    @classmethod
    def Int(cls, start=__default_start, stop=__default_stop, exclude_range=None):
        """
        Return a random integer N such that start <= N <= stop
        :param start: start range border
        :type start:int
        :param stop:stop range border
        :type stop:int
        :param exclude_range: optional list of numbers to exlude
        :type exclude_range : list
        :return: Return a random integer N such that start <= N <= stop
        :rtype: int
        """
        cls._InitSeed()
        ret = random.randint(start,stop)
        while exclude_range and ret in exclude_range:
            ret = random.randint(start, stop)

        return ret

    @classmethod
    def Vlan(cls,start=1,stop=4095):
        """
        generates a random vlan id
        :param start: start range border
        :type start:int
        :param stop:stop range border
        :type stop:int
        :return: random vlan id based
        :rtype: int
        """
        return cls.Int(start,stop)
    
    @classmethod
    def Mac(cls, mask="00:XX:XX:XX:XX:XX"):
        """
        returns a random MAC address
        :param mask: MAC address mask 6 octets each octet [0-9A-FX], delimiter '-' or ':'
        :type mask: str
        :rtype: str
        """
        cls._InitSeed()
        return MacManager.GenerateRandomMac(mask)
    
    @classmethod
    def IPv4(cls, ipv4_type="unicast"):
        """
        :param ipv4_type: 'unicast' or 'multicast'
        :return:a random valid ipv4 unicast or mulitcast address
        :rtype:str
        """
        funcname = GetFunctionName(cls.IPv4)
        ret = ""
        cls._InitSeed()
        def validate_params():
            err = ""
            if not isinstance(ipv4_type, str) :
                err = funcname + "wrong ipv_type {} should be string type\n".format(type(ipv4_type))
            if not ("multicast" in ipv4_type.lower() or "unicast" in ipv4_type.lower()):
                err += funcname + "wrong ipv4_type value {}: possible options (multicast,unicast)\n".format(ipv4_type)
            if err:
                raise ValueError(err)
        validate_params()
        octet1 = 0
        if "unicast" in ipv4_type.lower():
            # generate first octet to be in Unicast only range
            tmp = [random.randint(1,_MUTLICAST_RANGE[0]-1)] + [random.randint(_MUTLICAST_RANGE[1]+1,254)]
            octet1 = random.choice(tmp)
        elif "multicast" in ipv4_type.lower():
            octet1 = random.randint(_MUTLICAST_RANGE[0],_MUTLICAST_RANGE[1])
        # now generate the remaining 3 octets ( 24 bytes)
        remaining_octets = ".".join(str(random.randint(0,255)) for _ in range(3))
        ret = "{}.{}".format(octet1,remaining_octets)
        return ret
    
    #TODO: add IPv6 support
    
########################Usage Examples#####################
if __name__ == "__main__":
    
    # Random Int
    num = Randomize.Int()
    # read the last seed that was used to get num
    last_seed = Randomize.SEED
    num_in_range = Randomize.Int(start=10,stop=150) # random number in the range [10,150]
    # read the last seed that was used to get num_in_range
    last_seed2 = Randomize.SEED
    # optionaly set the SEED your self to get same numbers, Important from This point till you reset the seed to None
    # you will get the SAME results for the same ranges !
    Randomize.SEED = last_seed
    num2 =  Randomize.Int()
    print((num2 == num))  # True
    
    # Random Vlan
    Randomize.SEED = None  # unset the fixed SEED
    vlan = Randomize.Vlan()
    last_seed = Randomize.SEED
    evlan = Randomize.Vlan(start=4095,stop=8092)
    last_seed2 = Randomize.SEED
    
    # Random MAC Address
    mac = Randomize.Mac()
    
    # Random IPv4 Unicast
    ipv4_unicast = Randomize.IPv4()
    last_seed = Randomize.SEED
    # Random IPv4 Multicast
    ipv4_multicast = Randomize.IPv4(ipv4_type="multicast")
    pass