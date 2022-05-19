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

from enum import Enum
from xenavalkyrie.xena_stream import XenaModifierAction
from xenavalkyrie.xena_port import XenaCaptureBufferType

class XenaEnums:

    @staticmethod
    def unified_to_xena(what):
        try:
            where = getattr(XenaEnums, what.__class__.__name__)
            what = str(what).split(".")[-1]  # take the TGEnums enum, convert it's suffix to str
            result = getattr(where, what)  # from the generic str, get to IxEx enum of the requested enum
            return result.value  # return its numeric value
        except Exception as e:
            raise Exception("Failed to convert UTG enum to XenaEnums value")

    class MODIFIER_MAC_MODE(Enum):
        INCREMENT = XenaModifierAction.increment
        CONTINUOUS_INCREMENT = XenaModifierAction.increment
        DECREMENT = XenaModifierAction.decrement
        CONTINUOUS_DECREMENT = XenaModifierAction.decrement
        RANDOM = XenaModifierAction.random

    class MODIFIER_IPV4_ADDRESS_MODE(Enum):
        INCREMENT_HOST = XenaModifierAction.increment
        DECREMENT_HOST = XenaModifierAction.decrement
        CONTINUOUS_INCREMENT_HOST = XenaModifierAction.increment
        CONTINUOUS_DECREMENT_HOST = XenaModifierAction.decrement
        # INCREMENT_NET = 5
        # DECREMENT_NET = 6
        # CONTINUOUS_INCREMENT_NET = 7
        # CONTINUOUS_DECREMENT_NET = 8
        RANDOM = XenaModifierAction.random

    class PORT_PAYLOAD_MODE(Enum):
        NORMAL = 'NORMAL'  #: normalmode
        EXTPL = 'EXTPL'  #: extended payload
        CDF = 'CDF'  #: customdatafield
        UNDEFINED = 'UNDEF'