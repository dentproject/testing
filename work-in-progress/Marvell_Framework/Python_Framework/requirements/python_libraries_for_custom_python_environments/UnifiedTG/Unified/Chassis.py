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

from UnifiedTG.Unified.Utils import attrWithDefault
from UnifiedTG.Unified.TGEnums import TGEnums
from collections import OrderedDict

class resourceGroup(object):
    def __init__(self):
        self._enableCapture = False
        self._splitMode = attrWithDefault(TGEnums.splitSpeed.HW_DEFAULT)
        self._supported_modes = []
        self._driver_obj = None
        self._parent = None #type: Card

    @property
    def supported_modes(self):
        return self._supported_modes

    @property
    def split_mode(self):
        return self._splitMode.current_val

    @split_mode.setter
    def split_mode(self,mode):
        self._splitMode.current_val = mode

    @property
    def enable_capture(self):
        #todo capture
        return self._enableCapture

    @enable_capture.setter
    def enable_capture(self,mode):
        self._enable_capture_state(mode)

    def _enable_capture_state(self, mode, wr=False):
        pass

    def apply(self):
        """
        :return:
        :rtype: list[Port]
        """
        pass

class Card(object):
    def __init__(self,id):
        self.id = id
        self.resourceGroups = OrderedDict()  # type: list[resourceGroup]
        self._parent = None
        self._driver_obj = None
        self._supported_speeds = []

    @property
    def splitable(self):
        """
        Detect is card able to split
        :rtype: bool
        """
        return True if len(self.resourceGroups)>0 else False

    @property
    def supported_speeds(self):
        return self._supported_speeds

    def _get_port_rgId(self,pid):
        for rgId in self.resourceGroups:
            portsList = self.resourceGroups[rgId]._driver_obj.resource_ports
            if int(pid) in portsList:
                return rgId
        return None

    def apply(self):
        for rgId in self.resourceGroups:
            self.resourceGroups[rgId].apply()

class Chassis(object):
    def __init__(self,ip):
        self.ip = ip
        self._parent = None
        self._driver_obj = None
        self.cards = OrderedDict() #type: list[Card]
