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
import time
from PyInfraCommon.Globals.Logger.GlobalTestLogger import GlobalLogger


class Randomize(object):
    """
    this class provides ability to randomize various data types and sequences
    related
    """

    def __init__(self, _seed=0):
        self.randValueMin = 1
        self.randValueMax = 100
        if (_seed == 0):
            self.seed = int(time.time()%1000)
            GlobalLogger.logger.info("Random seed value is {}".format(str(self.seed)))
        else:
            self.seed = _seed
            GlobalLogger.logger.info("Debug mode - Random is according fixed seed {}".format(str(self.seed)))

        random.seed(self.seed)


    def Int(self, minVal=0, maxVal=1000000000):
        """
        Return a random integer in range:
                minVal <= N <= maxVal
        """

        _localSeed = random.randint(self.randValueMin, self.randValueMax)
        self.randValueMax = self.randValueMax + 49
        self.randValueMin = self.randValueMin + 17
        if(self.randValueMax > 2000000000):
            self.randValueMax = int(self.randValueMax % 2000000000)
            self.randValueMin = int(self.randValueMin % self.randValueMax)

        random.seed(_localSeed)
        ret = random.randint(minVal, maxVal)

        return ret


    def Vlan(self, start=1, stop=4095):
        """
        Return vlan value (type integer)
        """
        return self.Int(start, stop)


    def Mac(self, UCorMC="UC"):
        """
        Return UC/MC mac value (type string)
        """
        _mac = ''
        _digits = "0123456789ABCDEF"
        _cnt = 0

        for i in range(0, 12):
            if((UCorMC == "UC") and (_cnt==1)):
                _mac = _mac + _digits[self.Int(0, 15) & 0xE]
            elif ((UCorMC == "MC") and (_cnt == 1)):
                _mac = _mac + _digits[(self.Int(0, 15) & 0xE)+1]
            else:
                _mac = _mac + _digits[self.Int(0, 15)]
            _cnt = _cnt + 1
            if(_cnt == 2) and (len(_mac)<17):
                _mac = _mac + ':'
                _cnt = 0

        return _mac


    def Mac_List(self, macAmount=10, UCorMC = "UC"):
        """
        return list of random mac's
        """
        _macList = []

        for i in range(0, macAmount):
            while True:
                _mac = self.Mac(UCorMC)
                if _mac not in _macList:
                    break
            _macList.append(_mac)

        return _macList


    def IPv4(self, ipv4_type="unicast"):
        """
        ipv4_type: 'unicast' or 'multicast'
        Returns random IPv4 address
        """
        _ipv4 = ''
        octet0 = ''
        octet = ['','','']

        if ipv4_type == "unicast":
            octet0 = str(self.Int(0, 223)) # should not be 224 and above
        elif ipv4_type == "multicast":
            octet0 = str(self.Int(224, 239))
        else:
            print("Error:{} mode is not supported".format(ipv4_type))

        _ipv4 += octet0

        for i in range(0, 3):
            octet[i] = str(self.Int(0, 255))
            _ipv4 += '.'
            _ipv4 += octet[i]

        return _ipv4
        pass

    def IPv6(self, ipv6_type="unicast"):
        """
        ipv6_type: 'unicast' or 'multicast'
        Returns random IPv6 address
        """
        _ipv6 = ''
        _digits = "0123456789ABCDEF"
        _cnt = 0

        if ipv6_type != "unicast" or ipv6_type != "multicast":
            print("{} mode is not supported".format(ipv6_type))

        for i in range(0, 32):
            if ((ipv6_type == "unicast") and (i < 4)):
                _ipv6 += _digits[self.Int(0, 15) & 0xE] # should not be 0xFFFF
            elif ((ipv6_type == "multicast") and (i < 4)):
                _ipv6 += 'F'
            else:
                _ipv6 += _digits[self.Int(0, 15)]
            _cnt = _cnt + 1

            if (_cnt == 4) and (len(_ipv6) < 39):
                _ipv6 += ':'
                _cnt = 0

        return _ipv6


    def Get_mixPortList(self, start=0, stop=4, size=4):
        """
        return list with random numbers (without return on same number) according given range
        """
        return random.sample(list(range(start, stop)), size)
