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
from builtins import zip
from builtins import range
from builtins import object
import re
from random import choice

from PyInfraCommon.GlobalFunctions.Utils.Enums import JetIntEnum

class MacFormat(JetIntEnum):
    MAC_EUI_48_COLUMN_UPPER = 0  # '00:1A:2B:0C:41:7D'
    MAC_MICROSOFT = 1  # '00-1A-2B-0C-41-7D'
    MAC_CISCO = 2  # Cisco triple hextet format '001A.2B0C.417D'
    MAC_UNIX = 3  # '0:1a:2b:c:41:7d' TODO: not supported
    MAC_UNIX_EXPANDED = 4  # '00:1a:2b:0c:41:7d'
    MAC_BARE = 5  # '001A2B0C417D'


class MacManager(object):

    def __init__(self):
        self.delimiter = None

    @classmethod
    def GenerateRandomMac(cls, mask="XX:XX:XX:XX:XX:XX"):
        """
        :param mask: MAC address mask 6 octets each octet [0-9A-FX], delimiter '-' or ':'
        :type mask: str
        :rtype: str
        """
        mac = "00:00:00:00:00:01"
        if cls.__ValidateMacMask(mask):
             mac = ""
             for c in mask.upper():
                 mac += cls.__GenerateHexNumber(1) if c == 'X' else c

        else:
            print ("Illegal mask format in {}. Correct format:  6 octets each octet [0-9a-fA-FX], delimiter - or\
                  :".format(mask))

        return mac

    @classmethod
    def GetMacIncremented(cls, start_mac, amount=1, inc_step=1, mac_format=MacFormat.MAC_EUI_48_COLUMN_UPPER):
        """
        :param start_mac: MAC address consists of 6 octets, each octet [0-9A-F] with delimiter '-' or ':'
        :type start_mac: str
        :param amount: Amount of desired MAC addresses
        :type amount: int
        :param step: Incrementation step
        :type step: int
        :rtype: list of str
        """
        mac_list = []
        if not cls.ValidateMac(start_mac):
            return mac_list
        else:
            try:
                trantab = str.maketrans('', '', '-.:')
                mac_no_del = start_mac.translate(trantab)
                # mac_no_del = start_mac.translate(None, '-.:')
                mac_int = int(mac_no_del, 16)
                # mac_int + i * inc_step - int number updated in each iteration with inc_step
                # {0:0{1}X}".format(temp_num, 12) - hex string padded with zeros to length of 12 chars, represents the
                # previously calculated integer value
                # BareStrToMac() - converts the bare string to MAC address string in specified MAC format
                mac_list = [cls.BareStrToMac("{0:0{1}X}".format(mac_int + i * inc_step, 12), mac_format) for i in 
                            range(0, amount)]
            except ValueError as ex:
                print("Failed to cast hex-string \'{}\' to int. ".format(start_mac))


            return mac_list

    @classmethod
    def Format(cls, mac, mac_format=MacFormat.MAC_EUI_48_COLUMN_UPPER):
        """
        :param mac: MAC address consists of 6 octets, each octet [0-9A-F] with delimiter '-' or ':'
        :type mac: str
        :param format: MAC Format
        :type mac_format: MacFormat
        :rtype: str
        """

        if not cls.ValidateMac(mac):
            return mac
        else:
            # Determine delimiter type
            delimiter = None
            if "." in mac:
                delimiter = "."
            elif ":" in mac:
                delimiter = ":"
            elif "-" in mac:
                delimiter = "-"

            # remove delimiter
            mac_no_del = mac.replace(delimiter, "")
            #upper = mac_no_del.upper()
            #lower = mac_no_del.lower()

            # formated_mac = None
            # if mac_format == MacFormat.MAC_EUI_48_COLUMN_UPPER:
            #     formated_mac = ":".join(a + b for a ,b in zip(upper[::2], upper[1::2]))
            # elif mac_format == MacFormat.MAC_MICROSOFT:
            #     formated_mac = "-".join(a + b for a, b in zip(upper[::2], upper[1::2]))
            # elif mac_format == MacFormat.MAC_UNIX_EXPANDED:
            #     formated_mac = ":".join(a + b for a, b in zip(lower[::2], lower[1::2]))
            # elif mac_format == MacFormat.MAC_CISCO:
            #     formated_mac = ".".join(a + b + c + d for a, b, c, d in zip(upper[::4], upper[1::4], upper[2::4],
            #                                                                 upper[3::4]))
            # elif mac_format == MacFormat.MAC_BARE:
            #     formated_mac = upper
            # else:
            #     formated_mac = mac
            #
            # return formated_mac
            return cls.BareStrToMac(mac_no_del, mac_format)

    @classmethod
    def BareStrToMac(cls, mac_str, mac_format):
        upper = mac_str.upper()
        lower = mac_str.lower()

        formated_mac = None
        if mac_format == MacFormat.MAC_EUI_48_COLUMN_UPPER:
            formated_mac = ":".join(a + b for a, b in zip(upper[::2], upper[1::2]))
        elif mac_format == MacFormat.MAC_MICROSOFT:
            formated_mac = "-".join(a + b for a, b in zip(upper[::2], upper[1::2]))
        elif mac_format == MacFormat.MAC_UNIX_EXPANDED:
            formated_mac = ":".join(a + b for a, b in zip(lower[::2], lower[1::2]))
        elif mac_format == MacFormat.MAC_CISCO:
            formated_mac = ".".join(a + b + c + d for a, b, c, d in zip(upper[::4], upper[1::4], upper[2::4],
                                                                        upper[3::4]))
        elif mac_format == MacFormat.MAC_BARE:
            formated_mac = upper
        else:
            formated_mac = mac_str

        return formated_mac

    @classmethod
    def __GenerateHexNumber(self, length):
        valid_chars = '0123456789ABCDE'
        return ''.join(choice(valid_chars) for i in range(length))

    @classmethod
    def __ValidateMacMask(self, mask):
        """
        :param mask: MAC address mask 6 octets each octet [0-9A-FX], delimiter '-' or ':'
        :type mask: str
        :rtype: bool
        """
        # [0-9A-FX]{2} - 2 chars, possible options: 0-9,A-F or X
        # ([-:]?) - delimiter (submatch), possible options: '-' or ':'
        # \\1 - first capturing group, matches the exact same text found in ([-:]?)
        # {4} - repeat previous parenthesized block 4 times
        return re.match("[0-9A-FX]{2}([-:]?)[0-9A-FX]{2}(\\1[0-9A-FX]{2}){4}$", mask.upper())

    @classmethod
    def ValidateMac(self, mac):
        """
        :param mask: MAC address mask 6 octets each octet [0-9A-FX], delimiter '-' or ':'
        :type mask: str
        :rtype: bool
        """
        # [0-9A-FX]{2} - 2 chars, possible options: 0-9,A-F
        # ([-:]?) - delimiter (submatch), possible options: '-' or ':'
        # \\1 - first capturing group, matches the exact same text found in ([-:]?)
        # {4} - repeat previous parenthesized block 4 times
        return re.match("[0-9A-F]{2}([-:]?)[0-9A-F]{2}(\\1[0-9A-F]{2}){4}$", mac.upper())