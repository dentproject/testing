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
from __future__ import absolute_import
#from demoAPI import demoAPI as api
#from example import *
from builtins import str
from builtins import object
from .PythonWrapper import *
import re

from robot.api import logger
import robot.libraries.BuiltIn

import time


class DemoKeywords(object):

    port1 = None
    port2 = None
    ports = {}
    sid1 = None
    sid2 = None
    pkt1 = None
    pkt2 = None

    @staticmethod
    def uninitialize_system():
        logger.console('uninitialize_system')

    @staticmethod
    def initialize_system():
        """
        Initialize the system
        """
        logger.console('System Initialize in progress...')
        System.Initialize()

    @staticmethod
    def connect_to_tg(config_file_path):

        """
        Connect to the Traffic generator and obtain available ports

        :param config_file_path: Configuration file path

        :return: A dictionary containing all available ports
        """

        logger.console('System AutoTgConnection in progress...')
        str_config_file_path = str(config_file_path)
        logger.console('type of str_config_file_path: ' + str(type(str_config_file_path)))
        System.AutoTgConnection(str_config_file_path)
        logger.console('System AutoTgConnection completed...')

        ports_dict = DemoKeywords.readConfigFile(config_file_path)
        ret_ports_dict = {}
        divId_index = 6
        portId_index = 8

        for key, value in ports_dict.items():
            DIV_ID = int(value[divId_index])
            PORT_ID = int(value[portId_index])

            port = TGPortManager.Create(DIV_ID, PORT_ID)
            DemoKeywords.ports[PORT_ID] = port

            ret_ports_dict[key] = PORT_ID

        return ret_ports_dict


    @staticmethod
    def create_stream(portId, pkt, streamMode, rateMode, value, packetsPerBurst):
        """
        Create an IPv4 flow and configure the stream properties

        :param portId: Port id

        :param pkt: Packet

        :param streamMode: Stream mode:

        .. next - Advance to next stream

        .. returnToId - Return to the stream with the given id

        :param rateMode: Rate mode - PPS / % rate

        :param ppsValue: Packets per second

        :param packetsPerBurst: Packets per burst

        :return: Id of the created stream
        """

        global sid1

        port = DemoKeywords.ports[portId]

        sid1 = port.Streams.NewStream()

        streamControl = port.Streams.Get(sid1)
        streamControl.FrameData.packetData = pkt

        if streamMode == "next":
            streamControl.Control.txMode = stmAdvanceToNextStream
        elif streamMode == "returnToId":
            streamControl.Control.txMode = stmReturnToId

        rm = None
        if rateMode == "PPS":
            rm = srmPPS
        elif rateMode == "%":
            rm = srmUtilization

        streamControl.Control.rateMode = rm
        streamControl.Control.ppsValue = value
        #streamControl.Control.utilizationValue = value
        streamControl.Control.txModeParams.packetsPerBurst = packetsPerBurst

        return sid1


    @staticmethod
    def create_IPv4_flow(portId, streamMode, rateMode, value, packetsPerBurst):
        """
        Create an IPv4 flow and configure the stream properties

        :param portId: Port id

        :param streamMode: Stream mode:

        .. next - Advance to next stream

        .. returnToId - Return to the stream with the given id

        :param rateMode: Rate mode - PPS / % rate

        :param ppsValue: Packets per second

        :param packetsPerBurst: Packets per burst

        :return: Id of the created stream
        """

        global pkt1
        pkt1 = V2Vlan_IPv4_UDP()
        return DemoKeywords.create_stream(portId, pkt1, streamMode, rateMode, value, packetsPerBurst)


    @staticmethod
    def create_IPv6_flow(portId, streamMode, rateMode, value, packetsPerBurst):
        """
        Create an IPv6 flow and configure the stream properties

        :param portId: Port id

        :param streamMode: Stream mode:

        .. next - Advance to next stream

        .. returnToId - Return to the stream with the given id

        :param rateMode: Rate mode - PPS / % rate

        :param ppsValue: Packets per second

        :param packetsPerBurst: Packets per burst

        :return: Id of the created stream
        """
        global pkt2, sid2

        pkt2 = V2_IPv6_TCP()
        return DemoKeywords.create_stream(portId, pkt1, streamMode, rateMode, value, packetsPerBurst)

    @staticmethod
    def set_SMAC_modifier_on_stream(portId, stream_id, count, step, mode="incr"):
        """
        Set a modifier of source MAC address on a given stream

        :param portId: Port id

        :param stream_id: Stream id

        :param count: Repeat counter - number of iterations

        :param step: Increment/Decrement step

        :param mode: Movement direction mode - incr/decr
        """

        if mode == "incr":
            mode = mfmIncr
        elif mode == "decr":
            mode = mfmDecr

        port = DemoKeywords.ports[portId]
        saMac = port.Streams.Get(stream_id).FrameData.fieldModMacSa

        saMac.mode = mode
        saMac.count = count
        saMac.step = step

    @staticmethod
    def set_SIP_modifier_on_stream(portId, stream_id, SA_MODE, SA_REPEAT, SA_CLASS="classC"):
        """
        Set a modifier of source IP address on a given stream

        :param portId: Port id

        :param stream_id: Stream id

        :param SA_MODE: Movement type and direction - incrHost/decrHost/incrNet/decrNet

        :param SA_REPEAT: Repeat counter - number of iterations

        :param SA_CLASS: Address class - default is classC
        """
        if SA_MODE == "incrNet":
            SA_MODE = v4IncrNet

        if SA_CLASS == "classC":
            SA_CLASS = clmClassC

        port = DemoKeywords.ports[portId]

        sourceIP = port.Streams.Get(stream_id).FrameData.fieldModIpv4Sa
        sourceIP.mode = SA_MODE
        sourceIP.repeat = SA_REPEAT
        sourceIP.ip4Class = SA_CLASS

    @staticmethod
    def set_CRC_mode(portId, stream_id, crc_type):
        """
        Set CRC mode

        :param portId: port id

        :param stream_id: Stream id

        :param crc_type: CRC type - NoError/BadCRC/NoCRC
        """

        if crc_type == "NoError":
            crc_type = feNoError
        elif crc_type == "BadCRC":
            crc_type = feBadCrc
        elif crc_type == "NoCRC":
            crc_type = feNoCrc

        port = DemoKeywords.ports[portId]

        port.Streams.Get(stream_id).FrameData.forceErrors = crc_type

    @staticmethod
    def override_checksum_value(portId, stream_id, header_type, cs_value):
        """
        Override the automatic checksum value of a given header with a specific value

        :param portId: Port id

        :param stream_id: Stream id

        :param header_type: The type of the given header, e.g. IPv4

        :param cs_value: The new checksum value
        """

        if header_type == "IPv4":
            pkt1.ipv4.Checksum = int(cs_value, 16)

        port = DemoKeywords.ports[portId]

        port.Streams.Get(stream_id).FrameData.packetData = pkt1

    @staticmethod
    def start_Tx(portId):
        """
        Start transmission

        :param portId: Port id
        """

        port = DemoKeywords.ports[portId]

        port.StartTx(True)


    @staticmethod
    def stop_Tx(portId):
        """
        Stop transmission

        :param portId: Port id
        """

        port = DemoKeywords.ports[portId]

        port.StopTx()

    @staticmethod
    def get_crc_errors_counter(portId):
        """
        Get the counter value of CRC errors

        :param portId: Port id

        :return: Number of CRC errors
        """

        port = DemoKeywords.ports[portId]

        port.GetCounters()
        crc_errors_counter = port.Statistic.count.CRCErrors

        return crc_errors_counter

    @staticmethod
    def get_checksum_counter(portId):
        """
        Get the counter value of the previously defined checksum error trigger

        :param portId: Port id

        :return: Number of checksum errors
        """

        port = DemoKeywords.ports[portId]

        port.GetCounters()
        checksum_counter = port.Statistic.count.UDS3

        return checksum_counter

    @staticmethod
    def set_checksum_trigger(portId, header_type, checksum_value):
        """
        Set a trigger for catching a specific checksum value in a given header

        :param portId: Port id

        :param header_type: The type of the given header, e.g. IPv4

        :param checksum_value: The checksum value to look for
        """

        port = DemoKeywords.ports[portId]
        checksum_offset = 0

        if header_type == "IPv4" :
            checksum_offset = 28  # TODO:calc offset

        pattern = port.Triggers.commonProperties
        pattern.patt1Pattern = str(checksum_value)
        pattern.patt1Offset = checksum_offset

        pattern_mode = pmPattern1
        trigger = port.Triggers.trigger3
        trigger.state = beTrue
        trigger.patternMode = pattern_mode

        port.Triggers.Apply()

    @staticmethod
    def confirm_all(portId):
        """
        Confirm and apply all changes done to a port

        :param portId: Port id
        """

        port = DemoKeywords.ports[portId]

        port.Streams.Apply()


    @classmethod
    def readConfigFile(self, file_path):
        ports_dict = {}
        port_prop = []
        port_index = 0

        f = open(file_path, 'r')
        valied_lines = f.readlines()[2:]

        for line in valied_lines:
            port_key = 'port' + str(port_index)

            line = line.replace(' ', '')
            line = line.replace('\n', '')

            if line:
                for w in line.split('|'):
                    port_prop.append(w)

                port_prop = port_prop[1:len(port_prop) - 1]

                ports_dict[port_key] = port_prop

                port_index += 1
                port_prop = []

        return ports_dict

    @staticmethod
    def set_IPv4_DSCP_modifier(portId, streamId, udfId, repeatCount, initValue="00", step=1):
        """
        Set a modifier of IPv4 DSCP value on a given stream

        :param portId: Port id

        :param streamId: Stream id

        :param udfId: Id of a free UDF to use

        :param repeatCount: Repeat counter - number of iterations

        :param initValue: Initial value

        :param step: Increment/Decrement step
        """

        frameData = DemoKeywords.ports[portId].Streams.Get(streamId).FrameData

        DemoKeywords.set_field_modifier_by_name(frameData, udfId, "IPv4Header", "Dscp", repeatCount, initValue, step)

    @staticmethod
    def set_IPv6_DSCP_modifier(portId, streamId, udfId, repeatCount, initValue="00", step=1):
        """
        Set a modifier of IPv6 DSCP value on a given stream

        :param portId: Port id

        :param streamId: Stream id

        :param udfId: Id of a free UDF to use

        :param repeatCount: Repeat counter - number of iterations

        :param initValue: Initial value

        :param step: Increment/Decrement step
        """

        frameData = DemoKeywords.ports[portId].Streams.Get(streamId).FrameData

        DemoKeywords.set_field_modifier_by_name(frameData, udfId, "IPv6Header", "Dscp", repeatCount, initValue, step)

    @staticmethod
    def set_UDP_destination_port_modifier(portId, streamId, udfId, repeatCount, initValue="00 00", step=1):
        """
        Set a modifier of UDP destination port on a given stream

        :param portId: Port id

        :param streamId: Stream id

        :param udfId: Id of a free UDF to use

        :param repeatCount: Repeat counter - number of iterations

        :param initValue: Initial value

        :param step: Increment/Decrement step
        """

        frameData = DemoKeywords.ports[portId].Streams.Get(streamId).FrameData

        DemoKeywords.set_field_modifier_by_name(frameData, udfId, "UDPHeader", "DestPort", repeatCount, initValue, step)

    @staticmethod
    def set_TCP_destination_port_modifier(portId, streamId, udfId, repeatCount, initValue="00 00", step=1):
        """
        Set a modifier of TCP destination port on a given stream

        :param portId: Port id

        :param streamId: Stream id

        :param udfId: Id of a free UDF to use

        :param repeatCount: Repeat counter - number of iterations

        :param initValue: Initial value

        :param step: Increment/Decrement step
        """

        frameData = DemoKeywords.ports[portId].Streams.Get(streamId).FrameData

        DemoKeywords.set_field_modifier_by_name(frameData, udfId, "TCPHeader", "DestPort", repeatCount, initValue, step)

    @staticmethod
    def set_IPv4_time_to_live_modifier(portId, streamId, udfId, repeatCount, initValue="00", step=1):
        """
        Set a modifier of IPv4 time-to-live on a given stream

        :param portId: Port id

        :param streamId: Stream id

        :param udfId: Id of a free UDF to use

        :param repeatCount: Repeat counter - number of iterations

        :param initValue: Initial value

        :param step: Increment/Decrement step
        """

        frameData = DemoKeywords.ports[portId].Streams.Get(streamId).FrameData

        DemoKeywords.set_field_modifier_by_name(frameData, udfId, "IPv4Header", "TimeToLive", repeatCount, initValue="00", step=1)

    @staticmethod
    def set_VLAN_id_modifier(portId, streamId, repeatCount, step=1):
        """
        Set a modifier of VLAN id on a given stream

        :param portId: Port id

        :param streamId: Stream id

        :param repeatCount: Repeat counter - number of iterations

        :param step: Increment/Decrement step
        """

        fieldMod = DemoKeywords.ports[portId].Streams.Get(streamId).FrameData.fieldModVlan

        fieldMod.mode = vfmIncr
        fieldMod.count = repeatCount
        fieldMod.step = step

    @staticmethod
    def config_port_transmit_mode(port_id, tm_mode):
        """
        Configure a port transmit mode

        :param port_id: Port id

        :param tm_mode: Transmit mode - packet/scheduler
        """
        port = DemoKeywords.ports[port_id]

        if tm_mode == "packet":
            tm_mode = tmPacketStream
        elif tm_mode == "scheduler":
            tm_mode = tmAdvancedScheduler

        port.Properties.transmitMode.mode = tm_mode
        port.Properties.transmitMode.Apply()

    @staticmethod
    def config_stream_to_rate_mode(port_id, stream_id, frame_size_mode, rate_value):
        """
        Configure a stream to a desired rate mode

        :param port_id: Port id

        :param stream_id: Stream id

        :param frame_size_mode: Frame size mode - random/imix

        :param rate_value: Rate value
        """
        port = DemoKeywords.ports[port_id]

        frameData = port.Streams.Get(stream_id).FrameData

        if frame_size_mode == "random":
             frameData.frameSizeMode = fsRandom

        elif frame_size_mode == "imix":

            frameData.frameSizeMode = fsRandom
            frameData.frameSizeRandom.mode = rmPreDefined
            frameData.frameSizeRandom.predefinedMode = pmImix

        streamControl = port.Streams.Get(stream_id).Control
        streamControl.txMode = stmStopAfterStream
        streamControl.rateMode = srmBitRate
        streamControl.bitRateValue = rate_value * 1000000

    @staticmethod
    def set_TCP_source_port(port_id, stream_id):
        port = DemoKeywords.ports[port_id]
        pkt = port.Streams.Get(stream_id).FrameData.packetData

        pkt.tcp.destPort = 77

        x = 3

    @classmethod
    def set_field_modifier_by_name(self, frameData, udfIndex, headerName, fieldName, repeatCount, initValue, step=1):
        udf_modifier = UdfProperties()

        udf_modifier.enable = beTrue
        udf_modifier.mode = udfCounterMode
        udf_modifier.repeatCount = repeatCount
        udf_modifier.initValue = initValue
        udf_modifier.step = step

        frameData.SetUdfProperties(udfIndex, udf_modifier)
        frameData.UpdateUdfOffsetAndSizeByPacketField(udfIndex, headerName, fieldName)

    @classmethod
    def readConfigFile(self, file_path):
        ports_dict = {}
        port_prop = []
        port_index = 0

        f = open(file_path, 'r')
        valid_lines = f.readlines()[2:]

        for line in valid_lines:
            port_key = 'port' + str(port_index)

            line = line.replace(' ', '')
            line = line.replace('\n', '')

            if line:
                for w in line.split('|'):
                    port_prop.append(w)

                port_prop = port_prop[1: len(port_prop) - 1]

                ports_dict[port_key] = port_prop

                port_index += 1
                port_prop = []

        return ports_dict


    """....................."""


    @staticmethod
    def print_entries(tableEntreis):
        for entry in tableEntreis:
            print(entry)


    def get_Rx_counter(portId):
        port = DemoKeywords.ports[portId]

        port.GetCounters()
        Rx_counter = port.Statistic.count.RxFrames

        return Rx_counter


    @staticmethod
    def create_packet(pktType, pktSize, vlanID, macDA, ethType):
        pkt = None
        macDA = str(macDA)
        ethType = int(ethType, 16)

        if str(pktType) == 'vlan':
            pkt = V2Vlan()

        pkt.SetSize(pktSize)
        pkt.vlan.VlanID = vlanID
        pkt.mac.da = macDA
        pkt.ethType.type = ethType
        return pkt


    """....................."""