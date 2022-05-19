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

from collections import OrderedDict
import re

class myItems(object):
    def __init__(self):
        self._items = OrderedDict()

    def __getitem__(self, idx):
        # type: (str) -> pcaview
        return self._items[idx]

    def __setitem__(self, idx, value):
        self._items[idx] = value

    def __iter__(self):
        return self._items.__iter__()

    @property
    def count(self):
        return len(self._items)


class packetFieldsResultEntry(myItems):
    hex_from_raw_packet_view = re.compile(r'\d{4}\s+((?:(?:[\da-fA-F]{2})\s)+)', re.MULTILINE)

    def __init__(self):
        super(self.__class__, self).__init__()
        self._parent = None
        self._raw_packet_data = None
    @property
    def timeStamp(self):
        return self._items['frame.time_relative']

    @property
    def frameSize(self):
        return self._items['frame.len']

    @property
    def fid(self):
        return self._items['frame.number']

    @property
    def raw_packet_data(self):
        if not self._raw_packet_data:
            self._raw_packet_data = self._parent.extract_raw_packet_data(self.fid[0])
        return self._raw_packet_data


    @property
    def fcs(self):
        s = ''.join(self.__class__.hex_from_raw_packet_view.findall(self.raw_packet_data))
        res = s[(len(s)-12):]
        return res



