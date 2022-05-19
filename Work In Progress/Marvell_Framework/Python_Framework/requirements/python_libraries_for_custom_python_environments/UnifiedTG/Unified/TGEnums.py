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



class TGEnums(object):
    from enum import Enum,IntEnum

    @staticmethod
    def get_l2_proto_enum(val):
        """
        :param val: Available types: NONE, SNAP, RAW, IPX, PROTOCOL_OFFSET
        :type val: string
        """
        result = getattr(TGEnums.L2_PROTO, val)
        return result

    class L2_PROTO(Enum):
        NONE = 0
        ETHERNETII = 1
        SNAP = 2
        RAW = 3
        IPX = 4
        PROTOCOL_OFFSET = 5

    @staticmethod
    def get_l3_proto_enum(val):
        """
        :param val: Available types: NONE, ARP, IPV4, IPV6
        :type val: string
        """
        result = getattr(TGEnums.L3_PROTO, val)
        return result

    class L3_PROTO(Enum):
        NONE = 0
        ARP = 1
        IPV4 = 2
        IPV6 = 3
        IPV4_O_IPV6 = 4
        IPV6_O_IPV4 = 5
        IPX = 6
        PAUSE_CONTROL = 7
        CUSTOM = 8


    @staticmethod
    def get_arp_operation_enum(val):
        """
        :param val: Available types: UNKNOWN, ARP_REQUEST, ARP_REPLY, RARP_REQUEST, RARP_REPLY
        :type val: string
        """
        result = getattr(TGEnums.ARP_OPERATION, val)
        return result

    class ARP_OPERATION(Enum):
        UNKNOWN = 0
        ARP_REQUEST = 1
        ARP_REPLY = 2
        RARP_REQUEST = 3
        RARP_REPLY = 4

    @staticmethod
    def get_data_pattern_type_enum(val):
        """
        :param val: Available types: REPEATING, FIXED, INCREMENT_BYTE, INCREMENT_WORD, DECREMENT_BYTE, DECREMENT_WORD
        RANDOM, LOAD_FROM_FILE
        :type val: string
        """
        result = getattr(TGEnums.DATA_PATTERN_TYPE, val)
        return result

    class DATA_PATTERN_TYPE(Enum):
        REPEATING = 0
        FIXED = 1
        INCREMENT_BYTE = 2
        INCREMENT_WORD = 3
        DECREMENT_BYTE = 4
        DECREMENT_WORD = 5
        RANDOM = 6
        LOAD_FROM_FILE = 7

    @staticmethod
    def get_fcs_errors_mode_enum(val):
        """
        :param val: Available types: NO_ERROR, BAD_CRC, NO_CRC
        :type val: string
        """
        result = getattr(TGEnums.FCS_ERRORS_MODE, val)
        return result

    class FCS_ERRORS_MODE(Enum):
        NO_ERROR = 0
        BAD_CRC = 1
        NO_CRC = 2

    @staticmethod
    def get_qoss_mode_enum(val):
        """
        :param val: Available types: NO_ERROR, BAD_CRC, NO_CRC
        RANDOM, LOAD_FROM_FILE
        :type val: string
        """
        result = getattr(TGEnums.QOS_MODE, val)
        return result


    class QOS_MODE(Enum):
        TOS = 0
        DSCP = 1



    @staticmethod
    def get_l4_proto_enum(val):
        """
        :param val: Available types: NONE, TCP, UDP
        RANDOM, LOAD_FROM_FILE
        :type val: string
        """
        result = getattr(TGEnums.L4_PROTO, val)
        return result

    class L4_PROTO(Enum):
        NONE = 0
        TCP = 1
        UDP = 2
        ICMP = 3
        IGMP = 4
        OSPF = 5
        GRE = 6
        RIP = 7
        DHCP = 8


    # @staticmethod
    # def get_stream_mode_enum(val):
    #     """
    #     :param val: Available types: CONTINUOUS_PACKET, STOP_AFTER_THIS_STREAM, CONTINUOUS_BURST, ADVANCE_TO_NEXT_STREAM
    #     , RETURN_TO_ID, RETURN_TO_ID_FOR_COUNT
    #     RANDOM, LOAD_FROM_FILE
    #     :type val: string
    #     """
    #     result = getattr(TGEnums.STREAM_MODE, val)
    #     return result
    #
    # class STREAM_MODE(Enum):
    #     CONTINUOUS_PACKET = 0
    #     STOP_AFTER_THIS_STREAM = 1
    #     CONTINUOUS_BURST = 2
    #     ADVANCE_TO_NEXT_STREAM = 3
    #     RETURN_TO_ID = 4
    #     RETURN_TO_ID_FOR_COUNT = 5

    @staticmethod
    def get_stream_rate_mode_enum(val):
        """
        :param val: Available types: UTILIZATION, PACKETS_PER_SECOND, BITRATE_PER_SECOND, INTER_PACKET_GAP
        RANDOM, LOAD_FROM_FILE
        :type val: string
        """
        result = getattr(TGEnums.STREAM_RATE_MODE, val)
        return result

    class STREAM_RATE_MODE(Enum):
        INTER_PACKET_GAP = 0
        UTILIZATION = 1
        PACKETS_PER_SECOND = 2
        BITRATE_PER_SECOND = 3
        L1_BITRATE_PER_SECOND = 4

    @staticmethod
    def get_stream_rate_inter_packet_gap_mode_enum(val):
        """
        :param val: Available types: NANOSECONDS, MICROSECONDS, MILLISECONDS, SECONDS, BYTES
        RANDOM, LOAD_FROM_FILE
        :type val: string
        """
        result = getattr(TGEnums.STREAM_RATE_INTER_PACKET_GAP_MODE, val)
        return result

    class STREAM_RATE_INTER_PACKET_GAP_MODE(Enum):
        NANOSECONDS = 0
        MICROSECONDS = 1
        MILLISECONDS = 2
        SECONDS = 3
        BYTES = 4

    @staticmethod
    def get_stream_inter_burst_gap_unit_enum(val):
        """
        :param val: Available types: NANOSECONDS, MICROSECONDS, MILLISECONDS, SECONDS, BYTES
        :type val: string
        """
        result = getattr(TGEnums.STREAM_INTER_BURST_GAP_UNIT, val)
        return result

    class STREAM_INTER_BURST_GAP_UNIT(Enum):
        NANOSECONDS = 0
        MICROSECONDS = 1
        MILLISECONDS = 2
        SECONDS = 3
        BYTES = 4

    @staticmethod
    def get_stream_inter_stream_gap_unit_enum(val):
        """
        :param val: Available types: NANOSECONDS, MICROSECONDS, MILLISECONDS, SECONDS, BYTES
        :type val: string
        """
        result = getattr(TGEnums.STREAM_INTER_STREAM_GAP_UNIT, val)
        return result

    class STREAM_INTER_STREAM_GAP_UNIT(Enum):
        NANOSECONDS = 0
        MICROSECONDS = 1
        MILLISECONDS = 2
        SECONDS = 3
        BYTES = 4

    @staticmethod
    def get_stream_start_tx_delay_unit_enum(val):
        """
        :param val: Available types: NANOSECONDS, MICROSECONDS, MILLISECONDS, SECONDS, BYTES
        :type val: string
        """
        result = getattr(TGEnums.STREAM_START_TX_DELAY_UNIT, val)
        return result

    class STREAM_START_TX_DELAY_UNIT(Enum):
        NANOSECONDS = 0
        MICROSECONDS = 1
        MILLISECONDS = 2
        SECONDS = 3
        BYTES = 4

    @staticmethod
    def get_stream_transmit_mode_enum(val):
        """
        :param val: Available types: CONTINUOUS_PACKET, CONTINUOUS_BURST, STOP_AFTER_THIS_STREAM,
        ADVANCE_TO_NEXT_STREAM, RETURN_TO_ID, RETURN_TO_ID_FOR_COUNT
        :type val: string
        """
        result = getattr(TGEnums.STREAM_TRANSMIT_MODE, val)
        return result

    class STREAM_TRANSMIT_MODE(Enum):
        CONTINUOUS_PACKET = 0
        CONTINUOUS_BURST = 1
        STOP_AFTER_THIS_STREAM = 2
        ADVANCE_TO_NEXT_STREAM = 3
        RETURN_TO_ID = 4
        RETURN_TO_ID_FOR_COUNT = 5

    @staticmethod
    def get_port_properties_auto_negotiation_master_slave_mode_enum(val):
        """
        :param val: Available types: SLAVE, MASTER
        RANDOM, LOAD_FROM_FILE
        :type val: string
        """
        result = getattr(TGEnums.PORT_PROPERTIES_AUTO_NEGOTIATION_MASTER_SLAVE_MODE, val)
        return result

    class PORT_PROPERTIES_AUTO_NEGOTIATION_MASTER_SLAVE_MODE(Enum):
        SLAVE = 0
        MASTER = 1

    @staticmethod
    def get_port_properties_loopback_mode_enum(val):
        """
        :param val: Available types: NORMAL, INTERNAL_LOOPBACK_10G_ONLY, LINE_LOOPBACK_10G_ONLY
        RANDOM, LOAD_FROM_FILE
        :type val: string
        """
        result = getattr(TGEnums.PORT_PROPERTIES_LOOPBACK_MODE, val)
        return result

    class PORT_PROPERTIES_LOOPBACK_MODE(Enum):
        NORMAL = 0
        INTERNAL_LOOPBACK = 1
        LINE_LOOPBACK = 2

    @staticmethod
    def get_port_properties_flow_control_advertise_flow_control_abilities_mode_enum(val):
        """
        :param val: Available types: NONE, SEND_ONLY, SEND_AND_RECEIVE, SEND_AND_OR_RECEIVE
        RANDOM, LOAD_FROM_FILE
        :type val: string
        """
        result = getattr(TGEnums.PORT_PROPERTIES_FLOW_CONTROL_ADVERTISE_FLOW_CONTROL_ABILITIES_MODE, val)
        return result

    class PORT_PROPERTIES_FLOW_CONTROL_ADVERTISE_FLOW_CONTROL_ABILITIES_MODE(Enum):
        NONE = 0
        SEND_ONLY = 1
        SEND_AND_RECEIVE = 2
        SEND_AND_OR_RECEIVE = 3

    @staticmethod
    def get_port_properties_transmit_modes_enum(val):
        """
        :param val: Available types: PACKET_STREAMS, ADVANCED_STREAMS, ECHO,
         ADVANCED_STREAMS_TRANSPARENT_DYNAMIC_RATE_CHANGE_10G_ONLY
        RANDOM, LOAD_FROM_FILE
        :type val: string
        """
        result = getattr(TGEnums.PORT_PROPERTIES_TRANSMIT_MODES, val)
        return result

    class PORT_PROPERTIES_TRANSMIT_MODES(Enum):
        MANUAL_BASED = 0  # IXIA: Packet Streams STC: Manual Based
        STREAM_BASED = 1  # IXIA: ??? STC: Load per Stream Block
        PORT_BASED = 2  # IXIA: Advanced Stream Scheduler, STC: Port Based
        ECHO = 3  # IXIA: ECHO, STC: ???
        PORT_BASED_DYNAMIC_RATE_CHANGE = 4  # IXIA: ADVANCED_STREAMS_TRANSPARENT_DYNAMIC_RATE_CHANGE_10G_ONLY
        # PACKET_STREAMS = 0
        # ADVANCED_STREAMS = 1
        # ECHO = 2
        # ADVANCED_STREAMS_TRANSPARENT_DYNAMIC_RATE_CHANGE_10G_ONLY = 3

    class AutoEnum(Enum):
        def __new__(cls):
            value = len(cls.__members__) + 1
            obj = object.__new__(cls)
            obj._value_ = value
            return obj
        def __ge__(self, other):
            if self.__class__ is other.__class__:
                return self.value >= other.value
            return NotImplemented
        def __gt__(self, other):
            if self.__class__ is other.__class__:
                return self.value > other.value
            return NotImplemented
        def __le__(self, other):
            if self.__class__ is other.__class__:
                return self.value <= other.value
            return NotImplemented
        def __lt__(self, other):
            if self.__class__ is other.__class__:
                return self.value < other.value
            return NotImplemented

    class PORT_PROPERTIES_FEC_MODES(AutoEnum):
        AN_RESULT = ()  # IXIA: According to FEC AN
        FC_FEC = ()  # IXIA:
        RS_FEC = ()  # IXIA:
        DISABLED = ()  # IXIA:
        UNDEFINED = ()

    class PORT_PROPERTIES_FEC_AN(AutoEnum):
        ADVERTISE_FC = ()
        REQUEST_FC =()
        ADVERTISE_RS = ()
        REQUEST_RS = ()

    class PORT_PROPERTIES_SPEED(IntEnum):
        MEGA_10=10
        FAST = 100
        GIGA = 1000
        GIGA_2p5 = 2500
        GIGA_5=5000
        GIGA_10 = 10000
        GIGA_25 = 25000
        GIGA_40 = 40000
        GIGA_50 = 50000
        GIGA_100 = 100000
        GIGA_200 = 200000
        GIGA_400 = 400000
        UNDEFINED = -1

    speedSwitcher = {
        400000: PORT_PROPERTIES_SPEED.GIGA_400,
        200000: PORT_PROPERTIES_SPEED.GIGA_200,
        100000: PORT_PROPERTIES_SPEED.GIGA_100,
        50000: PORT_PROPERTIES_SPEED.GIGA_50,
        40000: PORT_PROPERTIES_SPEED.GIGA_40,
        25000: PORT_PROPERTIES_SPEED.GIGA_25,
        10000: PORT_PROPERTIES_SPEED.GIGA_10,
        5000: PORT_PROPERTIES_SPEED.GIGA_5,
        2500: PORT_PROPERTIES_SPEED.GIGA_2p5,
        1000: PORT_PROPERTIES_SPEED.GIGA,
        100: PORT_PROPERTIES_SPEED.FAST,
        10: PORT_PROPERTIES_SPEED.MEGA_10
    }

    class _converter(object):
        from enum import Enum, IntEnum
        class PORT_PROPERTIES_SPEED(IntEnum):
            MEGA_10 = 10
            FAST = 100
            GIGA = 1000
            GIGA_2p5 = 2500
            GIGA_5 = 5000
            GIGA_10 = 10000
            GIGA_25 = 25000
            GIGA_40 = 40000
            GIGA_50 = 50000
            GIGA_100 = 100000
            GIGA_200 = 200000
            GIGA_400 = 400000
            UNDEFINED = -1

        @classmethod
        def speed_to_SPEED(cls, speedInt):
            return TGEnums.speedSwitcher.get(speedInt, "Invalid speed")

        @classmethod
        def SPEED_to_speed(cls, speedEnum):
            res = filter(lambda spd: spd == speedEnum, TGEnums.speedSwitcher)
            return res




    class LOGICAL_OPERATOR(AutoEnum):
        NOT = ()
        AND = ()
        OR = ()
    class MATCH_TERM_TYPE(AutoEnum):
        MAC_DA = ()
        MAC_SA =()
        CUSTOM = ()
        SIZE = ()
    @staticmethod
    def get_port_properties_meida_type_enum(val):
        """
        :param val: Available types: COPPER, FIBER
        RANDOM, LOAD_FROM_FILE
        :type val: string
        """
        result = getattr(TGEnums.PORT_PROPERTIES_MEDIA_TYPE, val)
        return result

    class PORT_PROPERTIES_MEDIA_TYPE(Enum):
        COPPER = 0
        FIBER = 1
        SGMII = 2
        HW_DEFAULT = 3

    @staticmethod
    def get_duplex_and_speed_enum(val):
        """
        :param val: Available types: HALF10, FULL10, HALF100, FULL100, FULL1000
        RANDOM, LOAD_FROM_FILE
        :type val: string
        """
        result = getattr(TGEnums.DUPLEX_AND_SPEED, val)
        return result

    class DUPLEX_AND_SPEED(Enum):
        HALF10 = 0
        FULL10 = 1
        HALF100 = 2
        FULL100 = 3
        FULL1000 = 4
        FULL2500=5
        FULL5000 = 6
        FULL10000 = 7

    @staticmethod
    def get_duplex_enum(val):
        """
        :param val: Available types: HALF, FULL
        :type val: string
        """
        result = getattr(TGEnums.DUPLEX, val)
        return result

    class DUPLEX(Enum):
        HALF = 0
        FULL = 1

    @staticmethod
    def get_speed_enum(val):
        """
        :param val: Available types: 10, 100
        :type val: string
        """
        result = getattr(TGEnums.SPEED, val)
        return result

    class SPEED(Enum):
        SPEED10 = 0
        SPEED100 = 1

    class CHECKSUM_MODE(Enum):
        INVALID = 0
        VALID = 1
        OVERRIDE = 2

    @staticmethod
    def get_modifier_frame_size_mode_enum(val):
        """
        :param val: Available modes: FIXED, RANDOM, INCREMENT, AUTO, WEIGHT_PAIRS, IMIX
        :type val: string
        """
        result = getattr(TGEnums.MODIFIER_FRAME_SIZE_MODE, val)
        return result

    class MODIFIER_FRAME_SIZE_MODE(Enum):
        FIXED = 0
        RANDOM = 1
        INCREMENT = 2
        AUTO = 3
        WEIGHT_PAIRS = 4
        IMIX = 5
        CISCO = 6
        TOLLY = 7
        RPRTRI = 8
        RPRQUAD = 9
        QUAD_GAUSSIAN = 10


    @staticmethod
    def get_modifier_mac_mode_enum(val):
        """
        :param val: Available modes: FIXED, INCREMENT, CONTINUOUS_INCREMENT, DECREMENT, CONTINUOUS_DECREMENT, RANDOM
        :type val: string
        """
        result = getattr(TGEnums.MODIFIER_MAC_MODE, val)
        return result

    class MODIFIER_MAC_MODE(Enum):
        FIXED = 0
        INCREMENT = 1
        CONTINUOUS_INCREMENT = 2
        DECREMENT = 3
        CONTINUOUS_DECREMENT = 4
        RANDOM = 5
        ARP = 6


    @staticmethod
    def get_modifier_arp_mode_enum(val):
        """
        :param val: Available modes: FIXED, INCREMENT, CONTINUOUS_INCREMENT, DECREMENT, CONTINUOUS_DECREMENT, RANDOM
        :type val: string
        """
        result = getattr(TGEnums.MODIFIER_ARP_MODE, val)
        return result

    class MODIFIER_ARP_MODE(Enum):
        FIXED = 0
        INCREMENT = 1
        DECREMENT = 2
        CONTINUOUS_INCREMENT = 3
        CONTINUOUS_DECREMENT = 4

    @staticmethod
    def get_modifier_vlan_mode_enum(val):
        """
        :param val: Available modes: FIXED, INCREMENT, CONTINUOUS_INCREMENT, DECREMENT, CONTINUOUS_DECREMENT, RANDOM
        :type val: string
        """
        result = getattr(TGEnums.MODIFIER_VLAN_MODE, val)
        return result

    class MODIFIER_VLAN_MODE(Enum):
        FIXED = 0
        INCREMENT = 1
        CONTINUOUS_INCREMENT = 2
        DECREMENT = 3
        CONTINUOUS_DECREMENT = 4
        RANDOM = 5


    @staticmethod
    def get_modifier_ipv4_address_mode_enum(val):
        """
        :param val: Available modes: FIXED, RANDOM, INCREMENT_HOST, INCREMENT_NET, CONTINUOUS_INCREMENT_HOST,
         CONTINUOUS_INCREMENT_NET, DECREMENT_HOST, DECREMENT_NET, CONTINUOUS_DECREMENT_HOST, CONTINUOUS_DECREMENT_NET
        :type val: string
        """
        result = getattr(TGEnums.MODIFIER_IPV4_ADDRESS_MODE, val)
        return result

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

    @staticmethod
    def get_modifier_l4_port_mode_enum(val):
        """
        :param val: Available modes: FIXED, RANDOM, INCREMENT, DECREMENT
        :type val: string
        """
        result = getattr(TGEnums.MODIFIER_L4_PORT_MODE, val)
        return result

    class MODIFIER_L4_PORT_MODE(Enum):
        FIXED = 0
        INCREMENT = 1
        DECREMENT = 2
        RANDOM = 3

    @staticmethod
    def get_modifier_ipv6_Address_mode_enum(val):
        """
        :param val: Available modes: FIXED, INCREMENT_INTERFACE_ID, DECREMENT_INTERFACE_ID,
         INCREMENT_GBL_UNI_TOP_LVL_AGG_ID, DECREMENT_GBL_UNI_TOP_LVL_AGG_ID, INCREMENT_GBL_UNI_NEXT_LVL_AGG_ID,
         DECREMENT_GBL_UNI_NEXT_LVL_AGG_ID, INCREMENT_GBL_UNI_SITE_LVL_AGG_ID, DECREMENT_GBL_UNI_SITE_LVL_AGG_ID
        :type val: string
        """
        result = getattr(TGEnums.MODIFIER_IPV6_ADDRESS_MODE, val)
        return result

    class MODIFIER_IPV6_ADDRESS_MODE(Enum):
        FIXED = 0
        INCREMENT_INTERFACE_ID = 1
        DECREMENT_INTERFACE_ID = 2
        INCREMENT_NETWORK = 3
        DECREMENT_NETWORK = 4
        INCREMENT_GBL_UNI_TOP_LVL_AGG_ID = 5
        DECREMENT_GBL_UNI_TOP_LVL_AGG_ID = 6
        INCREMENT_GBL_UNI_NEXT_LVL_AGG_ID = 7
        DECREMENT_GBL_UNI_NEXT_LVL_AGG_ID = 8
        INCREMENT_GBL_UNI_SITE_LVL_AGG_ID = 9
        DECREMENT_GBL_UNI_SITE_LVL_AGG_ID = 10
        INCREMENT_HOST = 11
        DECREMENT_HOST = 12






    @staticmethod
    def get_modifier_ipv6_flow_label_mode_enum(val):
        """
        :param val: Available modes: FIXED, INCREMENT, DECREMENT
        :type val: string
        """
        result = getattr(TGEnums.MODIFIER_IPV6_FLOW_LABEL_MODE, val)
        return result

    class MODIFIER_IPV6_FLOW_LABEL_MODE(Enum):
        FIXED = 0
        INCREMENT = 1
        DECREMENT = 2


    @staticmethod
    def get_modifier_udf_mode_enum(val):
        """
        :param val: Available modes: COUNTER, RANDOM
        :type val: string
        """
        result = getattr(TGEnums.MODIFIER_UDF_MODE, val)
        return result

    class MODIFIER_UDF_MODE(Enum):
        COUNTER = 0
        RANDOM = 1
        VALUE_LIST = 2
        NESTED_COUNTER = 3
        RANGE_LIST = 4


    @staticmethod
    def get_modifier_udf_from_chain_mode_enum(val):
        """
        :param val: Available modes: NONE, UDF1, UDF2, UDF3, UDF4, UDF5
        :type val: string
        """
        result = getattr(TGEnums.MODIFIER_UDF_FROM_CHAIN_MODE, val)
        return result

    class MODIFIER_UDF_FROM_CHAIN_MODE(Enum):
        NONE = 0
        UDF1 = 1
        UDF2 = 2
        UDF3 = 3
        UDF4 = 4
        UDF5 = 5


    @staticmethod
    def get_modifier_udf_repeat_mode_enum(val):
        """
        :param val: Available modes: UP, DOWN
        :type val: string
        """
        result = getattr(TGEnums.MODIFIER_UDF_REPEAT_MODE, val)
        return result

    class MODIFIER_UDF_REPEAT_MODE(Enum):
        UP = 0
        DOWN = 1


    @staticmethod
    def get_modifier_udf_bits_mode_enum(val):
        """
        :param val: Available modes: BITS_1 - BITS_32
        :type val: string
        """
        result = getattr(TGEnums.MODIFIER_UDF_BITS_MODE, val)
        return result

    class MODIFIER_UDF_BITS_MODE(Enum):
        BITS_1 = 1
        BITS_2 = 2
        BITS_3 = 3
        BITS_4 = 4
        BITS_5 = 5
        BITS_6 = 6
        BITS_7 = 7
        BITS_8 = 8
        BITS_9 = 9
        BITS_10 = 10
        BITS_11 = 11
        BITS_12 = 12
        BITS_13 = 13
        BITS_14 = 14
        BITS_15 = 15
        BITS_16 = 16
        BITS_17 = 17
        BITS_18 = 18
        BITS_19 = 19
        BITS_20 = 20
        BITS_21 = 21
        BITS_22 = 22
        BITS_23 = 23
        BITS_24 = 24
        BITS_25 = 25
        BITS_26 = 26
        BITS_27 = 27
        BITS_28 = 28
        BITS_29 = 29
        BITS_30 = 30
        BITS_31 = 31
        BITS_32 = 32


    class Header_Offset(Enum):
        MacDA = 0,
        MacSA = 6,
        EtherType = 12

    class Flow_Control_Type(Enum):
        IEEE802_3x = 0
        IEEE802_1Qbb = 1
        Undefined = -1

    class TG_TYPE(Enum):
        Ixia = 'ixia'
        Ostinato = 'ostinato'
        IxiaVirtualSSH = 'ixiavirtualssh'
        IxiaSSH = 'ixiassh'
        Xena = 'xena'
        Trex = 'trex'
        Spirent = 'spirent'
        IxNetwork = 'ixnetwork'
        IxNetworkRestPy = 'ixnetworkrestpy'

    class splitSpeed(Enum):
        One_400G = '400000.1'
        Two_200G = '200000.2'
        One_200G = '200000.1'
        Four_100G = '100000.4'
        Two_100G = '100000.2'
        One_100G = '100000.1'
        Eight_50G = '50000.8'
        Four_50G = '50000.4'
        One_40G = '40000.1'
        Four_25G = '25000.4'
        Four_10G = '10000.4'
        Two_50G = '50000.2'
        HW_DEFAULT = '-1'

    class Link_State(Enum):
        linkDown=0
        linkUp = 1
        linkLoopback = 2
        restartAuto = 4
        autoNegotiating =5
        noTransceiver =7
        unKnown = -1

    class SpecialTagType(AutoEnum):

        Undefined = ()
        eTag = ()
        DSA_Forward = ()
        DSA_To_CPU = ()
        DSA_From_CPU_use_vidx_1 = ()
        DSA_From_CPU_use_vidx_0 = ()
        DSA_To_ANALYZER = ()

        extDSA_Forward_use_vidx_0 = ()
        extDSA_Forward_use_vidx_1 = ()
        extDSA_To_CPU = ()
        extDSA_From_CPU_use_vidx_0 = ()
        extDSA_From_CPU_use_vidx_1_exclude_is_trunk_1 = ()
        extDSA_From_CPU_use_vidx_1_exclude_is_trunk_0 = ()
        extDSA_To_ANALYZER = ()

        EDSA_Forward_use_vidx_0 = ()
        EDSA_Forward_use_vidx_1 = ()
        EDSA_To_CPU = ()
        EDSA_From_CPU_use_vidx_0 = ()
        EDSA_From_CPU_use_vidx_1_exclude_is_trunk_0 = ()
        EDSA_From_CPU_use_vidx_1_exclude_is_trunk_1 = ()
        EDSA_To_ANALYZER_use_eVIDX_0 = ()
        EDSA_To_ANALYZER_use_eVIDX_1 = ()

    class ARP_For(Enum):
        RESOLVE = 0
        LEARN = 1
        BOTH = 2

    class Ipv6ExtensionType(Enum):
        HopByHop = 'HopByHop'
        Routing = 'Routing'
        Fragment = 'Fragment'
        Destination = 'Destination'
        Authentication = 'Authentication'

    class Ipv6OptionType(Enum):
        PAD1 = 0
        PADN = 1
        HomeAddress = 2
        Jumbo = 194
        RouterAlert = 5
        BindingUpdate = 198
        BindingAcknowledgment = 7
        BindingRequest = 8
        MIpV6UniqueIdSub = 1002
        MlpV6AlternativeCoaSub = 4

    class RouterAlertType(Enum):
        MLD = 0
        RSVP = 1
        ActiveNetworks = 2


    class ICMP_HEADER_TYPE(Enum):
        ECHO_REPLY = 0
        DEST_UNREACHABLE = 3
        SOURCE_QUENCH = 4
        REDIRECT = 5
        ECHO_REQUEST = 8
        TIME_EXCEEDED = 11
        PARAMETER_PROBLEM = 12
        TIME_STAMP_REQUEST = 13
        TIME_STAMP_REPLY = 14
        INFO_REQUEST = 15
        INFO_REPLY = 16
        MASK_REQUEST = 17
        MASK_REPLY = 18

    class PROTOCOL_PAD_TYPE(Enum):
        CUSTOM = 0
        PTP = 1

    class FP_PACKET_TYPE(Enum):
        SMD_V = 0x01
        SMD_R = 0x02
        Express = 0x03
        SMD_S0 = 0x04
        SMD_S1 = 0x05
        SMD_S2 = 0x06
        SMD_S3 = 0x07
        SMD_C0 = 0x08
        SMD_C1 = 0x09
        SMD_C2 = 0x0A
        SMD_C3 = 0x0B
        Auto_SMDS = 0x0C
        Auto_SMDC = 0x0D
        Auto_SMD = 0x0E
        Invalid_SMD = 0x0F

    class FP_FRAG_COUNT(Enum):
        FragCount0 = 0x0
        FragCount1 = 0x1
        FragCount2 = 0x2
        FragCount3 = 0x3
        FragCountAuto = 0x4

    class FP_CRC_TYPE(Enum):
        CRCmCRC = 0x01
        CRCFCS = 0x02
        CRCInvalid = 0x03


