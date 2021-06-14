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

from UnifiedTG.Unified.TGEnums import TGEnums


class IxExEnums:
    from enum import Enum

    @staticmethod
    def TGEnums_IxExEnums_map(val, IxExEnum_enum):
        val = str(val).split(".")[-1]  # take the TGEnums enum, convert it's suffix to str
        result = getattr(IxExEnum_enum, val)  # from the generic str, get to IxEx enum of the requested enum
        return result.value  # return its numeric value

    @staticmethod
    def IxExEnums_TGEnums_map(val, TGEnums_enum):
        val = str(val).split(".")[-1]  # take the IxExEnum_enum enum, convert it's suffix to str
        result = getattr(TGEnums_enum, val)  # from the generic str, get to TGEnums enum of the requested enum
        return result  # return its ENUM value

    class MODIFIER_MAC_MODE(Enum):
        FIXED = 4
        INCREMENT = 0
        CONTINUOUS_INCREMENT = 1
        DECREMENT = 2
        CONTINUOUS_DECREMENT = 3
        RANDOM = 5
        ARP = 6

    class FCS_ERRORS_MODE(Enum):
        NO_ERROR = 0
        BAD_CRC = 3
        NO_CRC = 4

    class MODIFIER_IPV4_ADDRESS_MODE(Enum):
        FIXED = 0
        INCREMENT_HOST = 1
        DECREMENT_HOST = 2
        CONTINUOUS_INCREMENT_HOST = 3
        CONTINUOUS_DECREMENT_HOST = 4
        INCREMENT_NET = 5
        DECREMENT_NET = 6
        CONTINUOUS_INCREMENT_NET = 7
        CONTINUOUS_DECREMENT_NET = 8
        RANDOM = 9

    class MODIFIER_IPV6_ADDRESS_MODE(Enum):
        FIXED = 0
        INCREMENT_HOST = 1
        DECREMENT_HOST = 2
        INCREMENT_NETWORK = 3
        DECREMENT_NETWORK = 4
        INCREMENT_INTERFACE_ID = 5
        DECREMENT_INTERFACE_ID = 6
        INCREMENT_GBL_UNI_TOP_LVL_AGG_ID = 7
        DECREMENT_GBL_UNI_TOP_LVL_AGG_ID = 8
        INCREMENT_GBL_UNI_NEXT_LVL_AGG_ID = 9
        DECREMENT_GBL_UNI_NEXT_LVL_AGG_ID = 10
        INCREMENT_GBL_UNI_SITE_LVL_AGG_ID = 11
        DECREMENT_GBL_UNI_SITE_LVL_AGG_ID = 12

    class FEC_MODES(Enum):
        Disabled = 0,
        RS_FEC = 1,
        FC_FEC = 2

    class _converter():
        speedSwitcher = {
            100000: TGEnums.PORT_PROPERTIES_SPEED.GIGA_100,
            50000: TGEnums.PORT_PROPERTIES_SPEED.GIGA_50,
            40000: TGEnums.PORT_PROPERTIES_SPEED.GIGA_40,
            25000: TGEnums.PORT_PROPERTIES_SPEED.GIGA_25,
            10000: TGEnums.PORT_PROPERTIES_SPEED.GIGA_10,
            5000: TGEnums.PORT_PROPERTIES_SPEED.GIGA_5,
            2500: TGEnums.PORT_PROPERTIES_SPEED.GIGA_2p5,
            1000: TGEnums.PORT_PROPERTIES_SPEED.GIGA,
            100: TGEnums.PORT_PROPERTIES_SPEED.FAST,
            10: TGEnums.PORT_PROPERTIES_SPEED.MEGA_10
        }
        @classmethod
        def speed_to_SPEED(cls,speedInt):
            return cls.speedSwitcher.get(speedInt, "Invalid speed")
        @classmethod
        def SPEED_to_speed(cls,speedEnum):
            res = filter(lambda spd : spd == speedEnum, cls.speedSwitcher)
            return res

    class UDF_COUNTER_MODE(Enum):
        COUNTER = 0
        RANDOM = 1
        VALUE_LIST = 2
        NESTED_COUNTER = 3
        RANGE_LIST = 4

    class UDF_REPEAT_MODE(Enum):
        UP = 15
        DOWN = 7

    class IxiaFeatures(Enum):
        portFeatureRxDataIntegrity = 6
        portFeatureTxDataIntegrity = 11
        portFeatureDataCenterMode = 322
        portFeatureDataCenter4Priority = 442
        portFeatureDataCenter8Priority = 443
        portFeaturePFC = 374
        portFeatureRsFec = 518

    class DataCenterMode(Enum):
        fourPriorityTrafficMapping = 1
        eightPriorityTrafficMapping = 2

