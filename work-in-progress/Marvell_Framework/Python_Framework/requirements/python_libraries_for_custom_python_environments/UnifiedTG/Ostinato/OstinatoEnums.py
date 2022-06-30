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
from ostinato.protocols.mac_pb2 import Mac
from ostinato.protocols.ip4_pb2 import Ip4
from ostinato.protocols.ip6_pb2 import Ip6
from ostinato.protocols.payload_pb2 import Payload
from ostinato.protocols.protocol_pb2 import StreamCore,VariableField,Protocol

class OstinatoEnums:
    from enum import Enum

    @staticmethod
    def unified_to_ostinato(what):
        try:
            where = getattr(OstinatoEnums, what.__class__.__name__)
            what = str(what).split(".")[-1]  # take the TGEnums enum, convert it's suffix to str
            result = getattr(where, what)  # from the generic str, get to IxEx enum of the requested enum
            return result.value  # return its numeric value
        except Exception as e:
            raise Exception("Failed to convert UTG enum to Ostinato value")

    class MODIFIER_MAC_MODE(Enum):
        FIXED = Mac.e_mm_fixed
        INCREMENT = Mac.e_mm_inc
        CONTINUOUS_INCREMENT = Mac.e_mm_inc
        DECREMENT = Mac.e_mm_dec
        CONTINUOUS_DECREMENT = Mac.e_mm_dec
        RANDOM = Mac.e_mm_resolve

    class MODIFIER_IPV4_ADDRESS_MODE(Enum):
        FIXED = Ip4.e_im_fixed
        INCREMENT_HOST = Ip4.e_im_inc_host
        DECREMENT_HOST = Ip4.e_im_dec_host
        CONTINUOUS_INCREMENT_HOST = Ip4.e_im_inc_host
        CONTINUOUS_DECREMENT_HOST = Ip4.e_im_dec_host
        # INCREMENT_NET = 5
        # DECREMENT_NET = 6
        # CONTINUOUS_INCREMENT_NET = 7
        # CONTINUOUS_DECREMENT_NET = 8
        RANDOM = Ip4.e_im_random_host

    class MODIFIER_IPV6_ADDRESS_MODE(Enum):
        FIXED = Ip6.kFixed
        INCREMENT_INTERFACE_ID = Ip6.kIncHost
        DECREMENT_INTERFACE_ID = Ip6.kDecHost
        INCREMENT_HOST = Ip6.kIncHost
        DECREMENT_HOST = Ip6.kDecHost

    class DATA_PATTERN_TYPE(Enum):
        REPEATING = Payload.e_dp_fixed_word
        INCREMENT_BYTE = Payload.e_dp_inc_byte
        INCREMENT_WORD = Payload.e_dp_inc_byte
        DECREMENT_BYTE = Payload.e_dp_dec_byte
        DECREMENT_WORD = Payload.e_dp_dec_byte
        RANDOM = Payload.e_dp_random

    # class STREAM_TRANSMIT_MODE(Enum):
    #     CONTINUOUS_PACKET = e_sm_fixed
    #     CONTINUOUS_BURST = 1
    #     STOP_AFTER_THIS_STREAM = 2
    #     ADVANCE_TO_NEXT_STREAM = 3
    #     RETURN_TO_ID = 4
    #     RETURN_TO_ID_FOR_COUNT = 5

    class MODIFIER_FRAME_SIZE_MODE(Enum):
        FIXED = StreamCore.e_fl_fixed
        RANDOM = StreamCore.e_fl_random
        INCREMENT = StreamCore.e_fl_inc

    class MODIFIER_UDF_REPEAT_MODE(Enum):
        UP = VariableField.kIncrement
        DOWN = VariableField.kDecrement

    class _converter():
        @staticmethod
        def protoSize(ostProtoId):
            #TODO rest protocols
            switcher = {
                Protocol.kMacFieldNumber : 12,
                Protocol.kEth2FieldNumber: 2,
                Protocol.kVlanFieldNumber: 4,
                Protocol.kIp4FieldNumber: 20,
                Protocol.kTcpFieldNumber: 20,
                Protocol.kUdpFieldNumber: 8,
                Protocol.kDot3FieldNumber: 2,
                Protocol.kDot2SnapFieldNumber: 10,
                Protocol.kPayloadFieldNumber: 100,
                Protocol.kHexDumpFieldNumber: 100,
                #Protocol.kSampleFieldNumber : 0
                #Protocol.kUserScriptFieldNumber
                #Protocol.kSignFieldNumber
                #Protocol.kLlcFieldNumber
                # Protocol.kSnapFieldNumber
                # Protocol.kSvlanFieldNumber
                # Protocol.kDot2LlcFieldNumber
                # Protocol.kVlanStackFieldNumber
                # Protocol.kStpFieldNumber
                # Protocol.kArpFieldNumber
                Protocol.kIp6FieldNumber:16
                # Protocol.kIp6over4FieldNumber
                # Protocol.kIp4over6FieldNumber
                # Protocol.kIp4over4FieldNumber
                # Protocol.kIp6over6FieldNumber
                # Protocol.kIcmpFieldNumber
                # Protocol.kIgmpFieldNumber
                # Protocol.kMldFieldNumber
                # Protocol.kTextProtocolFieldNumber
            }
            return switcher.get(ostProtoId, "Invalid speed")


