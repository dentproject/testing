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

import time
from collections import OrderedDict
import inspect

from UnifiedTG.Unified.ProtocolManagement import protocolManagment
from UnifiedTG.Unified.Stream import Stream
from UnifiedTG.Unified.Utils import attrWithDefault
from UnifiedTG.Unified.TGEnums import TGEnums
from UnifiedTG.Unified.ObjectCreator import objectCreator
from UnifiedTG.Unified.UtgObject import UtgObject
from UnifiedTG.Unified.Chassis import Card , resourceGroup
from UnifiedTG.Unified.Utils import _stat_member
from UnifiedTG.Unified.UtgAnalyzer import utgAnalyzer


class Port(UtgObject):
    def __init__(self,uri,port_name=None, debug_prints=False):
        self._debug_prints = debug_prints
        self._port_driver_obj = None
        self._parent = None #type: TG
        self.card = None #type: Card
        self._port_uri = uri
        self._port_name = port_name
        if self._port_name is None:
            self._port_name = ""
        self.streams = OrderedDict()  #type: list[Stream]
        self._current_stream_idx = 0
        self._streams_count = 0
        self.properties = _PortProperties()
        self.statistics = _port_stats()
        self.data_integrity = _DATA_INTEGRITY()
        self.receive_mode = _RECEIVE_MODE()
        self._capture_buffer = []
        self._capture_scapy = []
        self.filter_properties = _FILTER_PROPERTIES()
        # self.statistics = PortStatistics
        self._objCreator = None  # type: objectCreator
        self._rgId = None
        self._analyzer = utgAnalyzer()
        self.protocol_managment = None  # type: protocolManagment
        self.port_preemption = None


    @property
    def vport(self):
        return self._port_driver_obj

    @property
    def enable_protocol_managment(self):
        pass

    @enable_protocol_managment.setter
    def enable_protocol_managment(self, state):
        if state is True and self.protocol_managment is None:
            self.protocol_managment = self._objCreator.create_router()
            self.protocol_managment._parent = self
            self.protocol_managment._driver_obj = self._port_driver_obj
            self.protocol_managment.protocol_interfaces._driver_obj = self._port_driver_obj
        elif state is False:
            self.protocol_managment = None


    @property
    def capture_buffer(self):
        return self._capture_buffer

    @capture_buffer.setter
    def capture_buffer(self,data):
        self._capture_buffer = data

    @property
    def capture_scapy(self):
        return self._capture_scapy

    @capture_scapy.setter
    def capture_scapy(self, data):
        self._capture_scapy = data

    @property
    def analyzer(self):
        return self._analyzer

    def __str__(self):
        tempstr = "Port name: {}\nPort uri: {}\nPort stream names: [".format(self._port_name, self._port_uri)
        for stream in self.streams:
            tempstr += "{}, ".format(str(stream))
        tempstr += "]\n"
        return tempstr

    def reset_sequence_index(self):
        pass

    def add_stream(self,stream_name=None):
        """
        :param stream_name: The name of the stream to create; if not filled will generate stream_ + idx of stream
        :type stream_name: str
        :return: The stream name created
        :rtype: str
        """
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())
        name = stream_name if stream_name else str("stream_"+str(self.streams.__len__()+1))
        new_stream = self._objCreator.create_stream(name)
        self.streams[name] = new_stream
        self.streams[name]._port_transmit_mode = self.properties.transmit_mode
        self.streams[name]._parent = self
        self._current_stream_idx += 1
        self._streams_count += 1
        return name

    def print_streams(self):
        """
        Loops over the streams of the port and print them
        """
        for stream in self.streams:
            print (str(self.streams[stream]))


    def start_traffic(self, blocking=False, start_packet_groups=True, wait_up = None):
        """ Start transmit on port.
        :param blocking: True - wait for traffic end, False - return after traffic start.
        :param start_packet_groups: True - start collecting packet groups on IXIA
        :param wait_up: None - Check global_wait_up, True - wait for the port to be up, False - don't wait\n
        In case ignore_link_status - don't wait
        """
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())
        common_wait_up = False
        global_wait_up = self._parent.waitLinkUpOnTx
        if wait_up is None:
            if global_wait_up is True:
                common_wait_up = True
        elif wait_up is True:
            common_wait_up = True

        if common_wait_up and not self.properties.ignore_link_status:
            self.wait_link_up()

    def wait_tx_done(self, timeout=600):
        time.sleep(3)
        self.get_stats()
        while int(self.statistics.bits_sent_rate) and timeout:
            time.sleep(1)
            timeout -= 1
            self.get_stats()


    def wait_link_up(self, timeout=60):
        """
        Wait for the link to be in up state until timeout, or raise exception after timeout.
        """
        self._port_driver_obj.wait_for_up(timeout)


    def _is_continuous_traffic(self):
        for stream in self.streams:
            stream = self.streams[stream]
            if stream.enabled:
                if stream.control.mode == TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM:
                    return False
                if stream.control.mode == TGEnums.STREAM_TRANSMIT_MODE.CONTINUOUS_PACKET \
                        or stream.control.mode == TGEnums.STREAM_TRANSMIT_MODE.CONTINUOUS_BURST \
                        or stream.control.mode == TGEnums.STREAM_TRANSMIT_MODE.RETURN_TO_ID:
                    return True
        return False

    def stop_traffic(self):
        """
        Stop tx on the port
        """
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())

    def start_capture(self, rx=True, tx=False, limit=None, mode=None, bpf_filter=None):
        """
        Start capture on the port
        :param rx: if rx, capture RX packets, else, do not capture
        :type rx: bool
        :param tx: if tx, capture TX packets, else, do not capture
        :type tx: bool
        """
        pass

    def stop_capture(self, cap_file_name="", cap_mode="buffer"):
        """
        Captured packets automatically stored in analyzer : self.analyzer,once initialized default_view - also run it
        :param cap_file_name:
        :param cap_mode: buffer mode - loops over the frames captured frames on port and append them\n
        to capture_buffer list.\n file_buffer mode - gets the file of captured frames on port and append them\n
        to capture_buffer list (only works when TCL server is on the same machine with the test runner).
        In both cases the capture_buffer is a list of str of bytes with space separation ("00 11 22 33...").
        """

        if self.analyzer.default_view:
            try:
                self.analyzer.input_data = self.capture_buffer
                self.analyzer.default_view.run()
            except Exception as e:
                self._logger.info(self._get_port_log_title(), str(e))

    def start_packet_groups(self, clear_time_stamps=True):
        """
        Start collecting PGIDs on IXIA
        :param clear_time_stamps: Clear time stamps before TX
        """
        pass

    def clear_port_statistics(self):
        """
        Clear all port statistics
        """
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())
        self.statistics._reset_stats()

    def clear_all_statistics(self):
        """
        Clear all port statistics (due to bug, streams stats are not cleared)
        """
        self.statistics._reset_stats()

    def get_supported_speeds(self):
        """
        Fills the card.supported_speeds attribute with supported TGEnums.PORT_PROPERTIES_SPEED as read from HW
        """
        pass

    def clear_ownership(self):
        """
        Clear current ownership from the port
        """
        self._port_driver_obj.release()

    def apply(self):
        """
        Applies all configurations to the HW (calls apply_port_config, apply_receive_mode, apply_data_integrity,
        apply_filters, apply_flow_control, apply_auto_neg)\n
        In IXIA also apply all streams configurations of the port.
        """
        self.apply_port_config()
        self.apply_receive_mode()
        self.apply_data_integrity()
        self.apply_filters()
        self.apply_flow_control()
        self.apply_auto_neg()
        # for stream in self.streams:
        #     self.streams[stream].apply(apply_to_hw=False)
        # self.apply_streams()
        #todo check if needed to apply streams here
        # for stream in self.streams:
        #    self.streams[stream].apply(apply_to_hw=False)

    def apply_port_config(self):
        """
        Apply only port configurations (not steams configurations of the port)
        """
        self._logger.info(self._get_port_log_title(), "{}{}".format(self._get_port_log_message(), self.properties))
        pass

    def apply_data_integrity(self):
        """
        Apply only port data integrity configuration
        """
        pass

    def apply_receive_mode(self):
        """
        Apply only port receive mode configuration
        """
        pass

    def apply_streams(self):
        """
        Apply only port streams configuration
        """
        for stream in self.streams:
            self.streams[stream].apply(apply_to_hw=True)

    def apply_flow_control(self):
        """
        Apply only port flow control configuration
        """
        pass

    def apply_auto_neg(self):
        """
        Apply only port auto negotiation configuration
        """
        pass

    def get_stats(self):
        '''
        Updates ports stats from HW to port.stats members
            :rtype: OrderedDict
            :return: dict of the port stats as received from HW (some manipulated stats may not appear)
        '''
        pass

    def get_fp_stats(self):
        '''
        Updates preemption stats from HW
            :rtype: OrderedDict
            :return: dict of the port stats as received from HW
        '''
        pass

    def del_all_streams(self, apply_to_hw=True):
        """
        Delete all streams on the port
        :param apply_to_hw: True - also write the deletion to HW, False - only delete them from port object
        """
        self.streams = OrderedDict()
        pass

    def reset_factory_defaults(self, apply=True):
        """
        Reset all port configurations and streams to default
        :param apply: True - Also reset on HW, False - only reset the port object
        """
        self._logger.info(self._get_port_log_title(), self._get_port_log_message())
        self._current_stream_idx = 0
        self._streams_count = 0
        self.properties = _PortProperties()
        self.statistics = _port_stats()
        self.data_integrity = _DATA_INTEGRITY()
        self.receive_mode = _RECEIVE_MODE()
        self.filter_properties = _FILTER_PROPERTIES()

    def get_stream_count(self):
        """
        :return: Returns the steams on the port as read from HW
        :rtype: int
        """
        pass

    # todo functions to ask from Yoram
    # todo port get link status
    def restart_auto_neg(self):
        """
        Calls port restart auto negotiation on HW
        """
        pass

    def apply_filters(self):
        """
        Applies port filters configuration to HW
        """
        pass

    def count_error_stats(self, counters_name_list=list()):
        """
        :param counters_name_list: A list of string counter names to check if they are > 0
        :type counters_name_list: [str]
        :return: A dictionary with counters names as keys and counter values as values in case they are > 0, and appears
        in the default error counter list or in the provided list counters_name_list.\n
        The default list is:\n
        alignment_errors, alignment_errors_rate, asynchronous_frames_sent, asynchronous_frames_sent_rate,
        collision_frames, collision_frames_rate, collisions, collisions_rate, data_integrity_errors,
        data_integrity_errors_rate, dribble_errors, dribble_errors_rate, dropped_frames, dropped_frames_rate,
        excessive_collision_frames, excessive_collision_frames_rate, crc_errors, crc_errors_rate, ip_checksum_errors,
        ip_checksum_errors_rate, late_collisions, late_collisions_rate, oversize_and_crc_errors,
        oversize_and_crc_errors_rate, prbs_errored_bits, sequence_errors, sequence_errors_rate,
        symbol_error_frames, symbol_error_frames_rate, symbol_errors, symbol_errors_rate, synch_error_frames,
        synch_error_frames_rate, tcp_checksum_errors, tcp_checksum_errors_rate, udp_checksum_errors,
        udp_checksum_errors_rate
        """
        stats_dict = self.statistics._count_error_stats(counters_name_list=counters_name_list)
        return stats_dict

    def _get_port_log_title(self):
        title = "UTG.{}.{}()".format(self._port_name, inspect.stack()[1][3])
        return title

    def _get_port_log_message(self):
        message = self.__str__()
        args, _, _, values_dict = inspect.getargvalues(inspect.stack()[1][0])
        values_dict_iter = iter((v, k) for k, v in values_dict.items() if not k.startswith('self') and not k.startswith('__'))
        message += "args:\n"
        for val, key in values_dict_iter:
            message += "{}: {}\n".format(key, str(val))
        return message

    def _udpate_autoneg_supported(self):
        pass

    def chassis_refresh(self):
        """
        Sync data from HW
        """
        self.card._parent.refresh()

    @property
    def supported_split_modes(self):
        """
        return split modes supported by card
        :rtype: list[TGEnums.splitSpeed]
        """
        if self.rgId:
            return self.card.resourceGroups[self._rgId].supported_modes



    @property
    def split_mode(self):
        """
        Return current card split mode
        :return:
        :rtype: TGEnums.splitSpeed
        """
        if self.rgId:
            return self.card.resourceGroups[self.rgId].split_mode

    def apply_split_mode(self, mode):
        """
        Split port according to mode and return new ports list
        :param mode:
        :type mode: TGEnums.splitSpeed
        :return:
        :rtype: list[Port]
        """
        if self.rgId:
            self.card.resourceGroups[self.rgId].split_mode = mode
            newTgPorts = self.card.resourceGroups[self.rgId].apply()
            return newTgPorts


    def dict_to_port(self, input_dict, configure_streams=True, configure_packet=True):
        Port._tg_dict_to_port(input_dict=input_dict, port_obj=self, configure_streams=configure_streams, configure_packet=configure_packet)

    @staticmethod
    def _tg_dict_to_port(input_dict, port_obj, configure_streams=True, configure_packet=True):
        streams = input_dict["streams"]
        for stream in streams:
            if stream["name"] not in port_obj.streams:
                port_obj.add_stream(stream["name"])

        if configure_streams:
            Stream._tg_dict_to_stream(input_dict, port_obj, configure_packet=configure_packet)
        elif configure_packet:
            Stream._tg_dict_to_packet(input_dict, port_obj)

class _PortProperties(object):
    def __init__(self):
        stack = inspect.stack()
        # all of the below are common between IxEx & STC
        self._parent = stack[1][0].f_locals['self'] #type: Port
        self._port_type = attrWithDefault("1g")  #todo consider overriding default when reserving the port
        self._media_type = attrWithDefault(TGEnums.PORT_PROPERTIES_MEDIA_TYPE.HW_DEFAULT)#type: TGEnums.PORT_PROPERTIES_MEDIA_TYPE
        self._dual_phy = False
        self._link_state = attrWithDefault(TGEnums.Link_State.unKnown)
        self._loopback_mode = attrWithDefault(TGEnums.PORT_PROPERTIES_LOOPBACK_MODE.NORMAL)
        self._transmit_mode = attrWithDefault(TGEnums.PORT_PROPERTIES_TRANSMIT_MODES.STREAM_BASED)
        self._ignore_link_status = attrWithDefault(False)
        self._auto_neg_enable = attrWithDefault(True)
        self._auto_neg_master = attrWithDefault(False)
        self._auto_neg_negotiate_master_slave = attrWithDefault(True)
        self._fc_auto_neg_enable = attrWithDefault(True)
        self._auto_neg_speed = attrWithDefault(TGEnums.SPEED.SPEED100)
        self._auto_neg_duplex = attrWithDefault(TGEnums.DUPLEX.FULL)
        self._auto_neg_adver_list = attrWithDefault([TGEnums.DUPLEX_AND_SPEED.HALF10,
                                                     TGEnums.DUPLEX_AND_SPEED.FULL10,
                                                     TGEnums.DUPLEX_AND_SPEED.HALF100,
                                                     TGEnums.DUPLEX_AND_SPEED.FULL100,
                                                     TGEnums.DUPLEX_AND_SPEED.FULL1000,
                                                     ]) #type: TGEnums.DUPLEX_AND_SPEED
        # End of common
        self._fec_mode = attrWithDefault(TGEnums.PORT_PROPERTIES_FEC_MODES.UNDEFINED) #type TGEnums.PORT_PROPERTIES_FEC_MODES
        self._speed = attrWithDefault(TGEnums.PORT_PROPERTIES_SPEED.UNDEFINED) #type TGEnums.PORT_PROPERTIES_SPEED
        self.flow_control = _Flow_Control(self)
        self._enable_simulate_cable_disconnect = attrWithDefault(False)
        self._auto_neg_adver_supported_list = []  # attrWithDefault()
        self._use_ieee = attrWithDefault(False) #type TGEnums.BOOL_EXT
        self._fec_an_list = attrWithDefault([TGEnums.PORT_PROPERTIES_FEC_AN.ADVERTISE_FC,
                                             TGEnums.PORT_PROPERTIES_FEC_AN.REQUEST_FC,
                                             TGEnums.PORT_PROPERTIES_FEC_AN.ADVERTISE_RS,
                                             TGEnums.PORT_PROPERTIES_FEC_AN.REQUEST_RS
                                             ])

        self._enable_basic_frame_preemption = attrWithDefault(None)
        #self._enable_SmdVRExchange = attrWithDefault(None)


    def __iter__(self):
        return iter([attr for attr in dir(self) if attr[:2] != "__"])

    def __str__(self):
        str_delimit = ", "
        temp_str = "port_type: {}\n" \
                   "media_type: {}\n" \
                   "loopback_mode: {}\n" \
                   "transmit_mode: {}\n" \
                   "ignore_link_status: {}\n" \
                   "auto_neg_enable: {}\n" \
                   "auto_neg_master: {}\n" \
                   "fc_auto_neg_enable: {}\n" \
                   "auto_neg_adver_list: {}\n" \
                   "fec_mode: {}\n" \
                   "speed: {}\n" \
                   "flow_control: {}\n".format( self.port_type,
                                                self.media_type,
                                                self.loopback_mode,
                                                self.transmit_mode,
                                                self.ignore_link_status,
                                                self.auto_neg_enable,
                                                self.auto_neg_master,
                                                self.fc_auto_neg_enable,
                                                self.auto_neg_adver_list,
                                                self.fec_mode,
                                                self.speed,
                                                self.flow_control,
                                                )
        return temp_str

    @property
    def enable_basic_frame_preemption(self):
         return self._enable_basic_frame_preemption.current_val

    @enable_basic_frame_preemption.setter
    def enable_basic_frame_preemption(self, v):
        self._enable_basic_frame_preemption.current_val = v

    # @property
    # def enable_SmdVRExchange(self):
    #      return self._enable_SmdVRExchange.current_val
    #
    # @enable_SmdVRExchange.setter
    # def enable_SmdVRExchange(self, v):
    #     self._enable_SmdVRExchange.current_val = v


    @property
    def link_state(self):
        """
        Read actual port link state
        :rtype: TGEnums.Link_State
        """
        self._parent._read_link()
        return self._link_state

    @property
    def dual_phy(self):
        """_dual phy : """
        return self._dual_phy

    @property
    def port_type(self):
        """_port_type : """
        return self._port_type.current_val

    @port_type.setter
    def port_type(self, v):
        """

        :param v:
        :type v:
        :return:
        :rtype:
        """
        self._port_type.current_val = v

    @property
    def media_type(self):
        """
        Copper/Fiber
        :return:
        :rtype:TGEnums.PORT_PROPERTIES_MEDIA_TYPE
        """
        return self._media_type.current_val

    @media_type.setter
    def media_type(self, v):
        """
        Copper/Fiber
        :param v:
        :type v:TGEnums.PORT_PROPERTIES_MEDIA_TYPE
        """
        self._media_type.current_val = v

    @property
    def loopback_mode(self):
        """_loopback_mode : """
        return self._loopback_mode.current_val

    @loopback_mode.setter
    def loopback_mode(self, v):
        """_loopback_mode : """
        self._loopback_mode.current_val = v

    @property
    def transmit_mode(self):
        """_transmit_mode : """
        return self._transmit_mode.current_val

    @transmit_mode.setter
    def transmit_mode(self, v):
        """_transmit_mode : """
        self._transmit_mode.current_val = v

    @property
    def ignore_link_status(self):
        """_ignore_link_status : """
        return self._ignore_link_status.current_val

    @ignore_link_status.setter
    def ignore_link_status(self, v):
        """_ignore_link_status : """
        self._ignore_link_status.current_val = v

    @property
    def auto_neg_enable(self):
        """_auto_neg_enable : """
        return self._auto_neg_enable.current_val

    @auto_neg_enable.setter
    def auto_neg_enable(self, v):
        """
        :param v:
        :type v: bool
        :return:
        :rtype:
        """
        self._auto_neg_enable.current_val = v

    @property
    def auto_neg_speed(self):
        """auto_neg_speed : """
        return self._auto_neg_speed.current_val

    @auto_neg_speed.setter
    def auto_neg_speed(self, v):
        """_auto_neg_speed : """
        self._auto_neg_speed.current_val = v

    @property
    def auto_neg_duplex(self):
        """auto_neg_duplex : """
        return self._auto_neg_duplex.current_val

    @auto_neg_duplex.setter
    def auto_neg_duplex(self, v):
        """_auto_neg_duplex : """
        self._auto_neg_duplex.current_val = v

    @property
    def auto_neg_master(self):
        """_auto_neg_master : """
        return self._auto_neg_master.current_val

    @auto_neg_master.setter
    def auto_neg_master(self, v):
        """_auto_neg_master : """
        self._auto_neg_master.current_val = v

    @property
    def auto_neg_negotiate_master_slave(self):
        """auto_neg_negotiate_master_slave : """
        return self._auto_neg_negotiate_master_slave.current_val

    @auto_neg_negotiate_master_slave.setter
    def auto_neg_negotiate_master_slave(self, v):
        """_auto_neg_negotiate_master_slave : """
        self._auto_neg_negotiate_master_slave.current_val = v

    @property
    def fc_auto_neg_enable(self):
        """_fc_auto_neg_enable : """
        return self._fc_auto_neg_enable.current_val

    @fc_auto_neg_enable.setter
    def fc_auto_neg_enable(self, v):
        """_fc_auto_neg_enable : """
        self._fc_auto_neg_enable.current_val = v

    @property
    def auto_neg_adver_list(self):
        """

        :return:
        :rtype: list[TGEnums.DUPLEX_AND_SPEED]
        """
        return self._auto_neg_adver_list.current_val

    @auto_neg_adver_list.setter
    def auto_neg_adver_list(self, v):
        """

        :param v:
        :type v: list[TGEnums.DUPLEX_AND_SPEED]
        :return:
        :rtype:
        """

        self._auto_neg_adver_list.current_val = v

    @property
    def supported_autoneg_speeds(self):
        """
        Return list of autoneg speeds supported on port
        :return:
        :rtype: list[TGEnums.DUPLEX_AND_SPEED]
        """
        self._parent._udpate_autoneg_supported()
        return self._auto_neg_adver_supported_list

    @property
    def supported_forced_speeds(self):
        """
        Return list of forced speeds supported on port
        :return:
        :rtype: list[TGEnums.PORT_PROPERTIES_SPEED]
        """
        return self._parent.get_supported_speeds()

    @property
    def available_forced_speeds(self):
        """
        Return list of forced speeds depends on actual port state and config
        :return:
        :rtype: list[TGEnums.PORT_PROPERTIES_SPEED]
        """
        speeds = self._parent.properties.supported_forced_speeds
        available_speeds = []
        countHD = filter(lambda spd:spd > TGEnums.PORT_PROPERTIES_SPEED.GIGA_10,speeds)
        if countHD or len(speeds)<2:
            return [self._parent.properties.speed]
        mGig = filter(lambda spd: spd > TGEnums.PORT_PROPERTIES_SPEED.GIGA, speeds)
        if mGig:
            if self._parent.properties.media_type == TGEnums.PORT_PROPERTIES_MEDIA_TYPE.COPPER:
                available_speeds = [TGEnums.PORT_PROPERTIES_SPEED.FAST]
            else:
                available_speeds = [TGEnums.PORT_PROPERTIES_SPEED.FAST,TGEnums.PORT_PROPERTIES_SPEED.GIGA,TGEnums.PORT_PROPERTIES_SPEED.GIGA_10]
        else:
            if self._parent.properties.media_type == TGEnums.PORT_PROPERTIES_MEDIA_TYPE.FIBER:
                if self._parent.properties.port_type == "82":
                    available_speeds = [TGEnums.PORT_PROPERTIES_SPEED.GIGA]
                else:
                    available_speeds = [TGEnums.PORT_PROPERTIES_SPEED.FAST,TGEnums.PORT_PROPERTIES_SPEED.GIGA]
            else:
                available_speeds = [TGEnums.PORT_PROPERTIES_SPEED.MEGA_10, TGEnums.PORT_PROPERTIES_SPEED.FAST]
        return available_speeds

    @property
    def fec_mode(self):
        # type: () -> TGEnums.PORT_PROPERTIES_FEC_MODES
        """
        :return: FEC Mode
        """
        return self._fec_mode.current_val
    @fec_mode.setter
    def fec_mode(self,mode):
        """
        configuring FEC : Disable/RS-FEC/FC-FEC
        :param mode: Disable/RS-FEC/FC-FEC
        :type mode: TGEnums.PORT_PROPERTIES_FEC_MODES
        :return:
        """
        self._fec_mode.current_val = mode

    @property
    def use_ieee_defaults(self):
        """

        :return:
        """
        return self._use_ieee.current_val

    @use_ieee_defaults.setter
    def use_ieee_defaults(self, mode):
        """
        Enable/Disable flow control IEEE defaults option
        :type mode: bool
        :return:
        """
        if self._parent.card.splitable:
            self._use_ieee.current_val = mode
            if mode:
                self.auto_neg_enable = True

    @property
    def fec_an_list(self):
        return self._fec_an_list.current_val

    @fec_an_list.setter
    def fec_an_list(self,fec_an_list):
        """
        list like: [TGEnums.PORT_PROPERTIES_FEC_AN.ADVERTISE_FC,TGEnums.PORT_PROPERTIES_FEC_AN.REQUEST_FC,TGEnums.PORT_PROPERTIES_FEC_AN.ADVERTISE_RS,TGEnums.PORT_PROPERTIES_FEC_AN.REQUEST_RS]
        :param fec_an_list:
        :type  fec_an_list: list[TGEnums.PORT_PROPERTIES_FEC_AN]
        """
        self._fec_an_list.current_val = fec_an_list

    @property
    def speed(self):
        """
        Read Only - view actual port speed(p.properties.auto_neg_speed to config)
        :return:
        :rtype: TGEnums.PORT_PROPERTIES_SPEED
        """
        self._parent._read_speed()
        return self._speed

    # @speed.setter
    # def speed(self,speed):
    #     """
    #     configuring Speed : for low speed interfaces 10/100/1000/2500/5000/10000
    #     :param mode:
    #     :return:
    #     """
    #     self.auto_neg_speed = anSpeed

    @property
    def enable_simulate_cable_disconnect(self):
        """
        :return: enable simulate cable disconnect value
        """
        return self._enable_simulate_cable_disconnect.current_val

    @enable_simulate_cable_disconnect.setter
    def enable_simulate_cable_disconnect(self, status=False):
        """
        :param status: set the enable simulate cable disconnect value
        :return:
        """
        self._enable_simulate_cable_disconnect.current_val = status

    # @property
    # def data_center_mode(self):
    #     pass
    #
    # @data_center_mode.setter
    # def data_center_mode(self, Enable):
    #     pass

class pfc_priority(object):
    def __init__(self):
        self._enabled = attrWithDefault(False)
        self._value = attrWithDefault(0)

    def __str__(self):
        tempstr = "enabled: {}; value: {}\n".format(self.enable, self.value,)
        return tempstr
    @property
    def enable(self):
        return self._enabled.current_val

    @enable.setter
    def enable(self,v):
        self._enabled.current_val = v

    @property
    def value(self):
        return self._value.current_val

    @value.setter
    def value(self,v):
        self._value.current_val = v

class _Flow_Control(object):

    def __init__(self,parent):
        self._enabled = attrWithDefault(False)
        self._type = attrWithDefault(TGEnums.Flow_Control_Type.IEEE802_1Qbb)
        self._directed_address = attrWithDefault('{01 80 C2 00 00 01}')
        self._multicast_pause_address =attrWithDefault('{01 80 C2 00 00 01}')
        self.pfc_matrix = [pfc_priority(),pfc_priority(),pfc_priority(),pfc_priority(),pfc_priority(),pfc_priority(),pfc_priority(),pfc_priority()]
        self._enable_response_delay = attrWithDefault(None)
        self._delay_quanta = attrWithDefault(1)

        self._data_center_enabled = attrWithDefault(True)
        self._data_center_mode = attrWithDefault(2)
        self._parent_port = parent

    def __str__(self):
        tempstr = "enabled: {}\n" \
                  "type: {}\n" \
                  "directed_address: {}\n" \
                  "multicast_pause_address: {}\n" \
                  "pfc_matrix: {}\n" \
                  "data_center_enabled: {}\n" \
                  "data_center_mode: {}\n".format(self.enable,
                                           self.type,
                                           self.directed_address,
                                           self.multicast_pause_address,
                                           # str(self.pfc_matrix),
                                           '[%s]' % ', '.join(map(str, self.pfc_matrix)),
                                           self._data_center_enabled.current_val,
                                           self._data_center_mode.current_val,)
        return tempstr


    @property
    def enable_response_delay(self):
        return self._enable_response_delay.current_val

    @enable_response_delay.setter
    def enable_response_delay(self,v):
        self._enable_response_delay.current_val = v

    @property
    def delay_quanta(self):
        return self._delay_quanta.current_val

    @delay_quanta.setter
    def delay_quanta(self,v):
        self._delay_quanta.current_val = v

    @property
    def enable(self):
        return self._enabled.current_val

    @enable.setter
    def enable(self,v):
        self._enabled.current_val = v

    @property
    def type(self):
        return self._type.current_val

    @type.setter
    def type(self, v):
        self._type.current_val = v

    @property
    def directed_address(self):
        return self._directed_address.current_val

    @directed_address.setter
    def directed_address(self,v):
        self._directed_address.current_val = '{'+v+'}'

    @property
    def multicast_pause_address(self):
        return self._multicast_pause_address.current_val

    @multicast_pause_address.setter
    def multicast_pause_address(self,v):
        self._multicast_pause_address.current_val = '{'+v+'}'

class _fec_stats(object):
    def __init__(self):
        self._max_symbol_errors=_stat_member()
        self._uncorrectable_codewords = _stat_member()
        self._transcoding_uncorrectable_events=_stat_member()
        self._name = 'FEC'
        self.value = 0
        self._value = 0


    def __str__(self):
        return str(self._max_symbol_errors)+str(self._uncorrectable_codewords)+str(self._transcoding_uncorrectable_events)

    def _clear(self):
        self._max_symbol_errors._clear()
        self._uncorrectable_codewords._clear()
        self._transcoding_uncorrectable_events._clear()

    @property
    def max_symbol_errors(self):
        return self._max_symbol_errors.value

    @property
    def uncorrectable_codewords(self):
        return self._uncorrectable_codewords.value

    @property
    def transcoding_uncorrectable_events(self):
        return self._transcoding_uncorrectable_events.value


class _port_stats(object):
    def __init__(self):
        self._stats_type = str
        self._alignment_errors = _stat_member()
        self._alignment_errors_rate = _stat_member()
        self._asynchronous_frames_sent = _stat_member()
        self._asynchronous_frames_sent_rate = _stat_member()
        self._bits_received = _stat_member()
        self._bits_received_rate = _stat_member()
        self._bits_sent = _stat_member()
        self._bits_sent_rate = _stat_member()
        self._bytes_received = _stat_member()
        self._bytes_received_rate = _stat_member()
        self._bytes_sent = _stat_member()
        self._bytes_sent_rate = _stat_member()
        self._capture_filter = _stat_member()
        self._capture_filter_rate = _stat_member()
        self._capture_trigger = _stat_member()
        self._capture_trigger_rate = _stat_member()
        self._collision_frames = _stat_member()
        self._collision_frames_rate = _stat_member()
        self._collisions = _stat_member()
        self._collisions_rate = _stat_member()
        self._data_integrity_errors = _stat_member()
        self._data_integrity_errors_rate = _stat_member()
        self._data_integrity_frames = _stat_member()
        self._data_integrity_frames_rate = _stat_member()
        self._dribble_errors = _stat_member()
        self._dribble_errors_rate = _stat_member()
        self._dropped_frames = _stat_member()
        self._dropped_frames_rate = _stat_member()
        self._duplex_mode = _stat_member()
        self._duplex_mode_rate = _stat_member()
        self._excessive_collision_frames = _stat_member()
        self._excessive_collision_frames_rate = _stat_member()
        self._crc_errors = _stat_member()
        self._crc_errors_rate = _stat_member()
        self._flow_control_frames = _stat_member()
        self._flow_control_frames_rate = _stat_member()
        self._fragments = _stat_member()
        self._fragments_rate = _stat_member()
        self._frames_received = _stat_member()
        self._frames_received_rate = _stat_member()
        self._frames_sent = _stat_member()
        self._frames_sent_rate = _stat_member()
        self._ip_checksum_errors = _stat_member()
        self._ip_checksum_errors_rate = _stat_member()
        self._ip_packets = _stat_member()
        self._ip_packets_rate = _stat_member()
        self._late_collisions = _stat_member()
        self._late_collisions_rate = _stat_member()
        self._line_speed = _stat_member()
        self._line_speed_rate = _stat_member()
        self._link = _stat_member()
        self._link_rate = _stat_member()
        self._link_fault_state = _stat_member()
        self._link_fault_state_rate = _stat_member()
        self._oversize = _stat_member()
        self._oversize_and_crc_errors = _stat_member()
        self._oversize_and_crc_errors_rate = _stat_member()
        self._oversize_rate = _stat_member()
        self._pause_acknowledge = _stat_member()
        self._pause_acknowledge_rate = _stat_member()
        self._pause_end_frames = _stat_member()
        self._pause_end_frames_rate = _stat_member()
        self._pause_overwrite = _stat_member()
        self._pause_overwrite_rate = _stat_member()
        self._prbsFramesReceived = _stat_member()
        self._prbsHeaderError = _stat_member()
        self._prbsBitsReceived = _stat_member()
        self._prbsErroredBits = _stat_member()
        self._prbsBerRatio = _stat_member()
        self._rx_ping_reply = _stat_member()
        self._rx_ping_reply_rate = _stat_member()
        self._rx_ping_request = _stat_member()
        self._rx_ping_request_rate = _stat_member()
        self._scheduled_frames_sent = _stat_member()
        self._scheduled_frames_sent_rate = _stat_member()
        self._sequence_errors = _stat_member()
        self._sequence_errors_rate = _stat_member()
        self._sequence_frames = _stat_member()
        self._sequence_frames_rate = _stat_member()
        self._symbol_error_frames = _stat_member()
        self._symbol_error_frames_rate = _stat_member()
        self._symbol_errors = _stat_member()
        self._symbol_errors_rate = _stat_member()
        self._synch_error_frames = _stat_member()
        self._synch_error_frames_rate = _stat_member()
        self._tcp_checksum_errors = _stat_member()
        self._tcp_checksum_errors_rate = _stat_member()
        self._tcp_packets = _stat_member()
        self._tcp_packets_rate = _stat_member()
        self._transmit_duration = _stat_member()
        self._transmit_duration_rate = _stat_member()
        self._transmit_duration_seconds = _stat_member()
        self._tx_ping_reply = _stat_member()
        self._tx_ping_reply_rate = _stat_member()
        self._tx_ping_request = _stat_member()
        self._tx_ping_request_rate = _stat_member()
        self._udp_checksum_errors = _stat_member()
        self._udp_checksum_errors_rate = _stat_member()
        self._udp_packets = _stat_member()
        self._udp_packets_rate = _stat_member()
        self._undersize = _stat_member()
        self._undersize_rate = _stat_member()
        self._user_defined_stat_1 = _stat_member()
        self._user_defined_stat_1_rate = _stat_member()
        self._user_defined_stat_2 = _stat_member()
        self._user_defined_stat_2_rate = _stat_member()
        self._vlan_tagged_frames_rx = _stat_member()
        self._vlan_tagged_frames_rx_rate = _stat_member()
        self._fec = _fec_stats()
        self._rx_Fp_VerifyProtocolErrors = _stat_member()
        self._rx_Fp_SmdRNotTransmittedCount = _stat_member()
        self._rx_Fp_SmdVNotTransmittedCount = _stat_member()
        self._rx_Fp_UnexpectedSmdRCount = _stat_member()
        self._rx_Fp_SmdSStartProtocolErrors = _stat_member()
        self._rx_Fp_SmdSFrameCountErrors = _stat_member()
        self._rx_Fp_SmdCFrameCountErrors = _stat_member()
        self._rx_Fp_FragCountErrors = _stat_member()
        self._rx_Fp_InvalidCrcTypeErrors = _stat_member()
        self._rx_Fp_ExpressCrcTypeErrors = _stat_member()
        self._rx_Fp_SmdSTerminationErrors = _stat_member()
        self._rx_Fp_SmdCTerminationErrors = _stat_member()
        self._rx_Fp_SmdCCrcCalcErrors = _stat_member()
        self._rx_Fp_ReassemblyGoodCount = _stat_member()
        self._rx_Fp_VerifymPacketCount = _stat_member()
        self._rx_Fp_RespondmPacketCount = _stat_member()
        self._rx_Fp_SmdS0mPacketCount = _stat_member()
        self._rx_Fp_SmdS1mPacketCount = _stat_member()
        self._rx_Fp_SmdS2mPacketCount = _stat_member()
        self._rx_Fp_SmdS3mPacketCount = _stat_member()
        self._rx_Fp_SmdC0mPacketCount = _stat_member()
        self._rx_Fp_SmdC1mPacketCount = _stat_member()
        self._rx_Fp_SmdC2mPacketCount = _stat_member()
        self._rx_Fp_SmdC3mPacketCount = _stat_member()
        self._rx_Fp_VerifymPacketCrcErrors = _stat_member()
        self._rx_Fp_RespondmPacketCrcErrors = _stat_member()
        self._rx_Fp_SmdS0mPacketCrcErrors = _stat_member()
        self._rx_Fp_SmdS1mPacketCrcErrors = _stat_member()
        self._rx_Fp_SmdS2mPacketCrcErrors = _stat_member()
        self._rx_Fp_SmdS3mPacketCrcErrors = _stat_member()
        self._rx_Fp_SmdC0mPacketCrcErrors = _stat_member()
        self._rx_Fp_SmdC1mPacketCrcErrors = _stat_member()
        self._rx_Fp_SmdC2mPacketCrcErrors = _stat_member()
        self._rx_Fp_SmdC3mPacketCrcErrors = _stat_member()

    @property
    def rx_Fp_VerifyProtocolErrors(self):
        return self._rx_Fp_VerifyProtocolErrors.value

    @rx_Fp_VerifyProtocolErrors.setter
    def rx_Fp_VerifyProtocolErrors(self, v):
        self._rx_Fp_VerifyProtocolErrors.value = v

    @property
    def rx_Fp_SmdRNotTransmittedCount(self):
        return self._rx_Fp_SmdRNotTransmittedCount.value

    @rx_Fp_SmdRNotTransmittedCount.setter
    def rx_Fp_SmdRNotTransmittedCount(self, v):
        self._rx_Fp_SmdRNotTransmittedCount.value = v

    @property
    def rx_Fp_SmdVNotTransmittedCount(self):
        return self._rx_Fp_SmdVNotTransmittedCount.value

    @rx_Fp_SmdVNotTransmittedCount.setter
    def rx_Fp_SmdVNotTransmittedCount(self, v):
        self._rx_Fp_SmdVNotTransmittedCount.value = v

    @property
    def rx_Fp_UnexpectedSmdRCount(self):
        return self._rx_Fp_UnexpectedSmdRCount.value

    @rx_Fp_UnexpectedSmdRCount.setter
    def rx_Fp_UnexpectedSmdRCount(self, v):
        self._rx_Fp_UnexpectedSmdRCount.value = v

    @property
    def rx_Fp_SmdSStartProtocolErrors(self):
        return self._rx_Fp_SmdSStartProtocolErrors.value

    @rx_Fp_SmdSStartProtocolErrors.setter
    def rx_Fp_SmdSStartProtocolErrors(self, v):
        self._rx_Fp_SmdSStartProtocolErrors.value = v

    @property
    def rx_Fp_SmdSFrameCountErrors(self):
        return self._rx_Fp_SmdSFrameCountErrors.value

    @rx_Fp_SmdSFrameCountErrors.setter
    def rx_Fp_SmdSFrameCountErrors(self, v):
        self._rx_Fp_SmdSFrameCountErrors.value = v

    @property
    def rx_Fp_SmdCFrameCountErrors(self):
        return self._rx_Fp_SmdCFrameCountErrors.value

    @rx_Fp_SmdCFrameCountErrors.setter
    def rx_Fp_SmdCFrameCountErrors(self, v):
        self._rx_Fp_SmdCFrameCountErrors.value = v

    @property
    def rx_Fp_FragCountErrors(self):
        return self._rx_Fp_FragCountErrors.value

    @rx_Fp_FragCountErrors.setter
    def rx_Fp_FragCountErrors(self, v):
        self._rx_Fp_FragCountErrors.value = v

    @property
    def rx_Fp_InvalidCrcTypeErrors(self):
        return self._rx_Fp_InvalidCrcTypeErrors.value

    @rx_Fp_InvalidCrcTypeErrors.setter
    def rx_Fp_InvalidCrcTypeErrors(self, v):
        self._rx_Fp_InvalidCrcTypeErrors.value = v

    @property
    def rx_Fp_ExpressCrcTypeErrors(self):
        return self._rx_Fp_ExpressCrcTypeErrors.value

    @rx_Fp_ExpressCrcTypeErrors.setter
    def rx_Fp_ExpressCrcTypeErrors(self, v):
        self._rx_Fp_ExpressCrcTypeErrors.value = v

    @property
    def rx_Fp_SmdSTerminationErrors(self):
        return self._rx_Fp_SmdSTerminationErrors.value

    @rx_Fp_SmdSTerminationErrors.setter
    def rx_Fp_SmdSTerminationErrors(self, v):
        self._rx_Fp_SmdSTerminationErrors.value = v

    @property
    def rx_Fp_SmdCTerminationErrors(self):
        return self._rx_Fp_SmdCTerminationErrors.value

    @rx_Fp_SmdCTerminationErrors.setter
    def rx_Fp_SmdCTerminationErrors(self, v):
        self._rx_Fp_SmdCTerminationErrors.value = v

    @property
    def rx_Fp_SmdCCrcCalcErrors(self):
        return self._rx_Fp_SmdCCrcCalcErrors.value

    @rx_Fp_SmdCCrcCalcErrors.setter
    def rx_Fp_SmdCCrcCalcErrors(self, v):
        self._rx_Fp_SmdCCrcCalcErrors.value = v

    @property
    def rx_Fp_ReassemblyGoodCount(self):
        return self._rx_Fp_ReassemblyGoodCount.value

    @rx_Fp_ReassemblyGoodCount.setter
    def rx_Fp_ReassemblyGoodCount(self, v):
        self._rx_Fp_ReassemblyGoodCount.value = v

    @property
    def rx_Fp_VerifymPacketCount(self):
        return self._rx_Fp_VerifymPacketCount.value

    @rx_Fp_VerifymPacketCount.setter
    def rx_Fp_VerifymPacketCount(self, v):
        self._rx_Fp_VerifymPacketCount.value = v

    @property
    def rx_Fp_RespondmPacketCount(self):
        return self._rx_Fp_RespondmPacketCount.value

    @rx_Fp_RespondmPacketCount.setter
    def rx_Fp_RespondmPacketCount(self, v):
        self._rx_Fp_RespondmPacketCount.value = v

    @property
    def rx_Fp_SmdS0mPacketCount(self):
        return self._rx_Fp_SmdS0mPacketCount.value

    @rx_Fp_SmdS0mPacketCount.setter
    def rx_Fp_SmdS0mPacketCount(self, v):
        self._rx_Fp_SmdS0mPacketCount.value = v

    @property
    def rx_Fp_SmdS1mPacketCount(self):
        return self._rx_Fp_SmdS1mPacketCount.value

    @rx_Fp_SmdS1mPacketCount.setter
    def rx_Fp_SmdS1mPacketCount(self, v):
        self._rx_Fp_SmdS1mPacketCount.value = v

    @property
    def rx_Fp_SmdS2mPacketCount(self):
        return self._rx_Fp_SmdS2mPacketCount.value

    @rx_Fp_SmdS2mPacketCount.setter
    def rx_Fp_SmdS2mPacketCount(self, v):
        self._rx_Fp_SmdS2mPacketCount.value = v

    @property
    def rx_Fp_SmdS3mPacketCount(self):
        return self._rx_Fp_SmdS3mPacketCount.value

    @rx_Fp_SmdS3mPacketCount.setter
    def rx_Fp_SmdS3mPacketCount(self, v):
        self._rx_Fp_SmdS3mPacketCount.value = v

    @property
    def rx_Fp_SmdC0mPacketCount(self):
        return self._rx_Fp_SmdC0mPacketCount.value

    @rx_Fp_SmdC0mPacketCount.setter
    def rx_Fp_SmdC0mPacketCount(self, v):
        self._rx_Fp_SmdC0mPacketCount.value = v

    @property
    def rx_Fp_SmdC1mPacketCount(self):
        return self._rx_Fp_SmdC1mPacketCount.value

    @rx_Fp_SmdC1mPacketCount.setter
    def rx_Fp_SmdC1mPacketCount(self, v):
        self._rx_Fp_SmdC1mPacketCount.value = v

    @property
    def rx_Fp_SmdC2mPacketCount(self):
        return self._rx_Fp_SmdC2mPacketCount.value

    @rx_Fp_SmdC2mPacketCount.setter
    def rx_Fp_SmdC2mPacketCount(self, v):
        self._rx_Fp_SmdC2mPacketCount.value = v

    @property
    def rx_Fp_SmdC3mPacketCount(self):
        return self._rx_Fp_SmdC3mPacketCount.value

    @rx_Fp_SmdC3mPacketCount.setter
    def rx_Fp_SmdC3mPacketCount(self, v):
        self._rx_Fp_SmdC3mPacketCount.value = v

    @property
    def rx_Fp_VerifymPacketCrcErrors(self):
        return self._rx_Fp_VerifymPacketCrcErrors.value

    @rx_Fp_VerifymPacketCrcErrors.setter
    def rx_Fp_VerifymPacketCrcErrors(self, v):
        self._rx_Fp_VerifymPacketCrcErrors.value = v

    @property
    def rx_Fp_RespondmPacketCrcErrors(self):
        return self._rx_Fp_RespondmPacketCrcErrors.value

    @rx_Fp_RespondmPacketCrcErrors.setter
    def rx_Fp_RespondmPacketCrcErrors(self, v):
        self._rx_Fp_RespondmPacketCrcErrors.value = v

    @property
    def rx_Fp_SmdS0mPacketCrcErrors(self):
        return self._rx_Fp_SmdS0mPacketCrcErrors.value

    @rx_Fp_SmdS0mPacketCrcErrors.setter
    def rx_Fp_SmdS0mPacketCrcErrors(self, v):
        self._rx_Fp_SmdS0mPacketCrcErrors.value = v

    @property
    def rx_Fp_SmdS1mPacketCrcErrors(self):
        return self._rx_Fp_SmdS1mPacketCrcErrors.value

    @rx_Fp_SmdS1mPacketCrcErrors.setter
    def rx_Fp_SmdS1mPacketCrcErrors(self, v):
        self._rx_Fp_SmdS1mPacketCrcErrors.value = v

    @property
    def rx_Fp_SmdS2mPacketCrcErrors(self):
        return self._rx_Fp_SmdS2mPacketCrcErrors.value

    @rx_Fp_SmdS2mPacketCrcErrors.setter
    def rx_Fp_SmdS2mPacketCrcErrors(self, v):
        self._rx_Fp_SmdS2mPacketCrcErrors.value = v

    @property
    def rx_Fp_SmdS3mPacketCrcErrors(self):
        return self._rx_Fp_SmdS3mPacketCrcErrors.value

    @rx_Fp_SmdS3mPacketCrcErrors.setter
    def rx_Fp_SmdS3mPacketCrcErrors(self, v):
        self._rx_Fp_SmdS3mPacketCrcErrors.value = v

    @property
    def rx_Fp_SmdC0mPacketCrcErrors(self):
        return self._rx_Fp_SmdC0mPacketCrcErrors.value

    @rx_Fp_SmdC0mPacketCrcErrors.setter
    def rx_Fp_SmdC0mPacketCrcErrors(self, v):
        self._rx_Fp_SmdC0mPacketCrcErrors.value = v

    @property
    def rx_Fp_SmdC1mPacketCrcErrors(self):
        return self._rx_Fp_SmdC1mPacketCrcErrors.value

    @rx_Fp_SmdC1mPacketCrcErrors.setter
    def rx_Fp_SmdC1mPacketCrcErrors(self, v):
        self._rx_Fp_SmdC1mPacketCrcErrors.value = v

    @property
    def rx_Fp_SmdC2mPacketCrcErrors(self):
        return self._rx_Fp_SmdC2mPacketCrcErrors.value

    @rx_Fp_SmdC2mPacketCrcErrors.setter
    def rx_Fp_SmdC2mPacketCrcErrors(self, v):
        self._rx_Fp_SmdC2mPacketCrcErrors.value = v

    @property
    def rx_Fp_SmdC3mPacketCrcErrors(self):
        return self._rx_Fp_SmdC3mPacketCrcErrors.value

    @rx_Fp_SmdC3mPacketCrcErrors.setter
    def rx_Fp_SmdC3mPacketCrcErrors(self, v):
        self._rx_Fp_SmdC3mPacketCrcErrors.value = v

    @property
    def prbs_frames_received(self):
        return self._prbsFramesReceived.value

    @prbs_frames_received.setter
    def prbs_frames_received(self, v):
        self._prbsFramesReceived.value = v

    @property
    def prbs_header_error(self):
        return self._prbsHeaderError.value

    @prbs_header_error.setter
    def prbs_header_error(self, v):
        self._prbsHeaderError.value = v

    @property
    def prbs_bits_received(self):
        return self._prbsBitsReceived.value

    @prbs_bits_received.setter
    def prbs_bits_received(self, v):
        self._prbsBitsReceived.value = v

    @property
    def prbs_errored_bits(self):
        return self._prbsErroredBits.value

    @prbs_errored_bits.setter
    def prbs_errored_bits(self, v):
        self._prbsErroredBits.value = v

    @property
    def prbs_ber_ratio(self):
        return self._prbsBerRatio.value

    @prbs_ber_ratio.setter
    def prbs_ber_ratio(self, v):
        self._prbsBerRatio.value = v

    @property
    def FEC(self):
        return self._fec

    @property
    def alignment_errors(self):
        return self._alignment_errors.value

    @alignment_errors.setter
    def alignment_errors(self, v):
        self._alignment_errors.value = v

    @property
    def alignment_errors_rate(self):
        return self._alignment_errors_rate.value

    @alignment_errors_rate.setter
    def alignment_errors_rate(self, v):
        self._alignment_errors_rate.value = v

    @property
    def asynchronous_frames_sent(self):
        return self._asynchronous_frames_sent.value

    @asynchronous_frames_sent.setter
    def asynchronous_frames_sent(self, v):
        self._asynchronous_frames_sent.value = v

    @property
    def asynchronous_frames_sent_rate(self):
        return self._asynchronous_frames_sent_rate.value

    @asynchronous_frames_sent_rate.setter
    def asynchronous_frames_sent_rate(self, v):
        self._asynchronous_frames_sent_rate.value = v

    @property
    def bits_received(self):
        return self._bits_received.value

    @bits_received.setter
    def bits_received(self, v):
        self._bits_received.value = v

    @property
    def bits_received_rate(self):
        return self._bits_received_rate.value

    @bits_received_rate.setter
    def bits_received_rate(self, v):
        self._bits_received_rate.value = v

    @property
    def bits_sent(self):
        return self._bits_sent.value

    @bits_sent.setter
    def bits_sent(self, v):
        self._bits_sent.value = v

    @property
    def bits_sent_rate(self):
        return self._bits_sent_rate.value

    @bits_sent_rate.setter
    def bits_sent_rate(self, v):
        self._bits_sent_rate.value = v

    @property
    def bytes_received(self):
        return self._bytes_received.value

    @bytes_received.setter
    def bytes_received(self, v):
        self._bytes_received.value = v

    @property
    def bytes_received_rate(self):
        return self._bytes_received_rate.value

    @bytes_received_rate.setter
    def bytes_received_rate(self, v):
        self._bytes_received_rate.value = v

    @property
    def bytes_sent(self):
        return self._bytes_sent.value

    @bytes_sent.setter
    def bytes_sent(self, v):
        self._bytes_sent.value = v

    @property
    def bytes_sent_rate(self):
        return self._bytes_sent_rate.value

    @bytes_sent_rate.setter
    def bytes_sent_rate(self, v):
        self._bytes_sent_rate.value = v

    @property
    def capture_filter(self):
        return self._capture_filter.value

    @capture_filter.setter
    def capture_filter(self, v):
        self._capture_filter.value = v

    @property
    def capture_filter_rate(self):
        return self._capture_filter_rate.value

    @capture_filter_rate.setter
    def capture_filter_rate(self, v):
        self._capture_filter_rate.value = v

    @property
    def capture_trigger(self):
        return self._capture_trigger.value

    @capture_trigger.setter
    def capture_trigger(self, v):
        self._capture_trigger.value = v

    @property
    def capture_trigger_rate(self):
        return self._capture_trigger_rate.value

    @capture_trigger_rate.setter
    def capture_trigger_rate(self, v):
        self._capture_trigger_rate.value = v

    @property
    def collision_frames(self):
        return self._collision_frames.value

    @collision_frames.setter
    def collision_frames(self, v):
        self._collision_frames.value = v

    @property
    def collision_frames_rate(self):
        return self._collision_frames_rate.value

    @collision_frames_rate.setter
    def collision_frames_rate(self, v):
        self._collision_frames_rate.value = v

    @property
    def collisions(self):
        return self._collisions.value

    @collisions.setter
    def collisions(self, v):
        self._collisions.value = v

    @property
    def collisions_rate(self):
        return self._collisions_rate.value

    @collisions_rate.setter
    def collisions_rate(self, v):
        self._collisions_rate.value = v

    @property
    def data_integrity_errors(self):
        return self._data_integrity_errors.value

    @data_integrity_errors.setter
    def data_integrity_errors(self, v):
        self._data_integrity_errors.value = v

    @property
    def data_integrity_errors_rate(self):
        return self._data_integrity_errors_rate.value

    @data_integrity_errors_rate.setter
    def data_integrity_errors_rate(self, v):
        self._data_integrity_errors_rate.value = v

    @property
    def data_integrity_frames(self):
        return self._data_integrity_frames.value

    @data_integrity_frames.setter
    def data_integrity_frames(self, v):
        self._data_integrity_frames.value = v

    @property
    def data_integrity_frames_rate(self):
        return self._data_integrity_frames_rate.value

    @data_integrity_frames_rate.setter
    def data_integrity_frames_rate(self, v):
        self._data_integrity_frames_rate.value = v

    @property
    def dribble_errors(self):
        return self._dribble_errors.value

    @dribble_errors.setter
    def dribble_errors(self, v):
        self._dribble_errors.value = v

    @property
    def dribble_errors_rate(self):
        return self._dribble_errors_rate.value

    @dribble_errors_rate.setter
    def dribble_errors_rate(self, v):
        self._dribble_errors_rate.value = v

    @property
    def dropped_frames(self):
        return self._dropped_frames.value

    @dropped_frames.setter
    def dropped_frames(self, v):
        self._dropped_frames.value = v

    @property
    def dropped_frames_rate(self):
        return self._dropped_frames_rate.value

    @dropped_frames_rate.setter
    def dropped_frames_rate(self, v):
        self._dropped_frames_rate.value = v

    @property
    def duplex_mode(self):
        return self._duplex_mode.value

    @duplex_mode.setter
    def duplex_mode(self, v):
        self._duplex_mode.value = v

    @property
    def duplex_mode_rate(self):
        return self._duplex_mode_rate.value

    @duplex_mode_rate.setter
    def duplex_mode_rate(self, v):
        self._duplex_mode_rate.value = v

    @property
    def excessive_collision_frames(self):
        return self._excessive_collision_frames.value

    @excessive_collision_frames.setter
    def excessive_collision_frames(self, v):
        self._excessive_collision_frames.value = v

    @property
    def excessive_collision_frames_rate(self):
        return self._excessive_collision_frames_rate.value

    @excessive_collision_frames_rate.setter
    def excessive_collision_frames_rate(self, v):
        self._excessive_collision_frames_rate.value = v

    @property
    def crc_errors(self):
        return self._crc_errors.value

    @crc_errors.setter
    def crc_errors(self, v):
        self._crc_errors.value = v

    @property
    def crc_errors_rate(self):
        return self._crc_errors_rate.value

    @crc_errors_rate.setter
    def crc_errors_rate(self, v):
        self._crc_errors_rate.value = v

    @property
    def flow_control_frames(self):
        return self._flow_control_frames.value

    @flow_control_frames.setter
    def flow_control_frames(self, v):
        self._flow_control_frames.value = v

    @property
    def flow_control_frames_rate(self):
        return self._flow_control_frames_rate.value

    @flow_control_frames_rate.setter
    def flow_control_frames_rate(self, v):
        self._flow_control_frames_rate.value = v

    @property
    def fragments(self):
        return self._fragments.value

    @fragments.setter
    def fragments(self, v):
        self._fragments.value = v

    @property
    def fragments_rate(self):
        return self._fragments_rate.value

    @fragments_rate.setter
    def fragments_rate(self, v):
        self._fragments_rate.value = v

    @property
    def frames_received(self):
        return self._frames_received.value

    @frames_received.setter
    def frames_received(self, v):
        self._frames_received.value = v

    @property
    def frames_received_rate(self):
        return self._frames_received_rate.value

    @frames_received_rate.setter
    def frames_received_rate(self, v):
        self._frames_received_rate.value = v

    @property
    def frames_sent(self):
        return self._frames_sent.value

    @frames_sent.setter
    def frames_sent(self, v):
        self._frames_sent.value = v

    @property
    def frames_sent_rate(self):
        return self._frames_sent_rate.value

    @frames_sent_rate.setter
    def frames_sent_rate(self, v):
        self._frames_sent_rate.value = v

    @property
    def ip_checksum_errors(self):
        return self._ip_checksum_errors.value

    @ip_checksum_errors.setter
    def ip_checksum_errors(self, v):
        self._ip_checksum_errors.value = v

    @property
    def ip_checksum_errors_rate(self):
        return self._ip_checksum_errors_rate.value

    @ip_checksum_errors_rate.setter
    def ip_checksum_errors_rate(self, v):
        self._ip_checksum_errors_rate.value = v

    @property
    def ip_packets(self):
        return self._ip_packets.value

    @ip_packets.setter
    def ip_packets(self, v):
        self._ip_packets.value = v

    @property
    def ip_packets_rate(self):
        return self._ip_packets_rate.value

    @ip_packets_rate.setter
    def ip_packets_rate(self, v):
        self._ip_packets_rate.value = v

    @property
    def late_collisions(self):
        return self._late_collisions.value

    @late_collisions.setter
    def late_collisions(self, v):
        self._late_collisions.value = v

    @property
    def late_collisions_rate(self):
        return self._late_collisions_rate.value

    @late_collisions_rate.setter
    def late_collisions_rate(self, v):
        self._late_collisions_rate.value = v

    @property
    def line_speed(self):
        return self._line_speed.value

    @line_speed.setter
    def line_speed(self, v):
        self._line_speed.value = v

    @property
    def line_speed_rate(self):
        return self._line_speed_rate.value

    @line_speed_rate.setter
    def line_speed_rate(self, v):
        self._line_speed_rate.value = v

    @property
    def link(self):
        return self._link.value

    @link.setter
    def link(self, v):
        self._link.value = v

    @property
    def link_rate(self):
        return self._link_rate.value

    @link_rate.setter
    def link_rate(self, v):
        self._link_rate.value = v

    @property
    def link_fault_state(self):
        return self._link_fault_state.value

    @link_fault_state.setter
    def link_fault_state(self, v):
        self._link_fault_state.value = v

    @property
    def link_fault_state_rate(self):
        return self._link_fault_state_rate.value

    @link_fault_state_rate.setter
    def link_fault_state_rate(self, v):
        self._link_fault_state_rate.value = v

    @property
    def oversize(self):
        return self._oversize.value

    @oversize.setter
    def oversize(self, v):
        self._oversize.value = v

    @property
    def oversize_and_crc_errors(self):
        return self._oversize_and_crc_errors.value

    @oversize_and_crc_errors.setter
    def oversize_and_crc_errors(self, v):
        self._oversize_and_crc_errors.value = v

    @property
    def oversize_and_crc_errors_rate(self):
        return self._oversize_and_crc_errors_rate.value

    @oversize_and_crc_errors_rate.setter
    def oversize_and_crc_errors_rate(self, v):
        self._oversize_and_crc_errors_rate.value = v

    @property
    def oversize_rate(self):
        return self._oversize_rate.value

    @oversize_rate.setter
    def oversize_rate(self, v):
        self._oversize_rate.value = v

    @property
    def pause_acknowledge(self):
        return self._pause_acknowledge.value

    @pause_acknowledge.setter
    def pause_acknowledge(self, v):
        self._pause_acknowledge.value = v

    @property
    def pause_acknowledge_rate(self):
        return self._pause_acknowledge_rate.value

    @pause_acknowledge_rate.setter
    def pause_acknowledge_rate(self, v):
        self._pause_acknowledge_rate.value = v

    @property
    def pause_end_frames(self):
        return self._pause_end_frames.value

    @pause_end_frames.setter
    def pause_end_frames(self, v):
        self._pause_end_frames.value = v

    @property
    def pause_end_frames_rate(self):
        return self._pause_end_frames_rate.value

    @pause_end_frames_rate.setter
    def pause_end_frames_rate(self, v):
        self._pause_end_frames_rate.value = v

    @property
    def pause_overwrite(self):
        return self._pause_overwrite.value

    @pause_overwrite.setter
    def pause_overwrite(self, v):
        self._pause_overwrite.value = v

    @property
    def pause_overwrite_rate(self):
        return self._pause_overwrite_rate.value

    @pause_overwrite_rate.setter
    def pause_overwrite_rate(self, v):
        self._pause_overwrite_rate.value = v

    @property
    def rx_ping_reply(self):
        return self._rx_ping_reply.value

    @rx_ping_reply.setter
    def rx_ping_reply(self, v):
        self._rx_ping_reply.value = v

    @property
    def rx_ping_reply_rate(self):
        return self._rx_ping_reply_rate.value

    @rx_ping_reply_rate.setter
    def rx_ping_reply_rate(self, v):
        self._rx_ping_reply_rate.value = v

    @property
    def rx_ping_request(self):
        return self._rx_ping_request.value

    @rx_ping_request.setter
    def rx_ping_request(self, v):
        self._rx_ping_request.value = v

    @property
    def rx_ping_request_rate(self):
        return self._rx_ping_request_rate.value

    @rx_ping_request_rate.setter
    def rx_ping_request_rate(self, v):
        self._rx_ping_request_rate.value = v

    @property
    def scheduled_frames_sent(self):
        return self._scheduled_frames_sent.value

    @scheduled_frames_sent.setter
    def scheduled_frames_sent(self, v):
        self._scheduled_frames_sent.value = v

    @property
    def scheduled_frames_sent_rate(self):
        return self._scheduled_frames_sent_rate.value

    @scheduled_frames_sent_rate.setter
    def scheduled_frames_sent_rate(self, v):
        self._scheduled_frames_sent_rate.value = v

    @property
    def sequence_errors(self):
        return self._sequence_errors.value

    @sequence_errors.setter
    def sequence_errors(self, v):
        self._sequence_errors.value = v

    @property
    def sequence_errors_rate(self):
        return self._sequence_errors_rate.value

    @sequence_errors_rate.setter
    def sequence_errors_rate(self, v):
        self._sequence_errors_rate.value = v

    @property
    def sequence_frames(self):
        return self._sequence_frames.value

    @sequence_frames.setter
    def sequence_frames(self, v):
        self._sequence_frames.value = v

    @property
    def sequence_frames_rate(self):
        return self._sequence_frames_rate.value

    @sequence_frames_rate.setter
    def sequence_frames_rate(self, v):
        self._sequence_frames_rate.value = v

    @property
    def symbol_error_frames(self):
        return self._symbol_error_frames.value

    @symbol_error_frames.setter
    def symbol_error_frames(self, v):
        self._symbol_error_frames.value = v

    @property
    def symbol_error_frames_rate(self):
        return self._symbol_error_frames_rate.value

    @symbol_error_frames_rate.setter
    def symbol_error_frames_rate(self, v):
        self._symbol_error_frames_rate.value = v

    @property
    def symbol_errors(self):
        return self._symbol_errors.value

    @symbol_errors.setter
    def symbol_errors(self, v):
        self._symbol_errors.value = v

    @property
    def symbol_errors_rate(self):
        return self._symbol_errors_rate.value

    @symbol_errors_rate.setter
    def symbol_errors_rate(self, v):
        self._symbol_errors_rate.value = v

    @property
    def synch_error_frames(self):
        return self._synch_error_frames.value

    @synch_error_frames.setter
    def synch_error_frames(self, v):
        self._synch_error_frames.value = v

    @property
    def synch_error_frames_rate(self):
        return self._synch_error_frames_rate.value

    @synch_error_frames_rate.setter
    def synch_error_frames_rate(self, v):
        self._synch_error_frames_rate.value = v

    @property
    def tcp_checksum_errors(self):
        return self._tcp_checksum_errors.value

    @tcp_checksum_errors.setter
    def tcp_checksum_errors(self, v):
        self._tcp_checksum_errors.value = v

    @property
    def tcp_checksum_errors_rate(self):
        return self._tcp_checksum_errors_rate.value

    @tcp_checksum_errors_rate.setter
    def tcp_checksum_errors_rate(self, v):
        self._tcp_checksum_errors_rate.value = v

    @property
    def tcp_packets(self):
        return self._tcp_packets.value

    @tcp_packets.setter
    def tcp_packets(self, v):
        self._tcp_packets.value = v

    @property
    def tcp_packets_rate(self):
        return self._tcp_packets_rate.value

    @tcp_packets_rate.setter
    def tcp_packets_rate(self, v):
        self._tcp_packets_rate.value = v

    @property
    def transmit_duration(self):
        return self._transmit_duration.value

    @transmit_duration.setter
    def transmit_duration(self, v):
        self._transmit_duration.value = v

    @property
    def transmit_duration_rate(self):
        return self._transmit_duration_rate.value

    @transmit_duration_rate.setter
    def transmit_duration_rate(self, v):
        self._transmit_duration_rate.value = v

    @property
    def transmit_duration_seconds(self):
        return self._transmit_duration_seconds.value

    @transmit_duration_seconds.setter
    def transmit_duration_seconds(self, v):
        self._transmit_duration_seconds.value = v

    @property
    def tx_ping_reply(self):
        return self._tx_ping_reply.value

    @tx_ping_reply.setter
    def tx_ping_reply(self, v):
        self._tx_ping_reply.value = v

    @property
    def tx_ping_reply_rate(self):
        return self._tx_ping_reply_rate.value

    @tx_ping_reply_rate.setter
    def tx_ping_reply_rate(self, v):
        self._tx_ping_reply_rate.value = v

    @property
    def tx_ping_request(self):
        return self._tx_ping_request.value

    @tx_ping_request.setter
    def tx_ping_request(self, v):
        self._tx_ping_request.value = v

    @property
    def tx_ping_request_rate(self):
        return self._tx_ping_request_rate.value

    @tx_ping_request_rate.setter
    def tx_ping_request_rate(self, v):
        self._tx_ping_request_rate.value = v

    @property
    def udp_checksum_errors(self):
        return self._udp_checksum_errors.value

    @udp_checksum_errors.setter
    def udp_checksum_errors(self, v):
        self._udp_checksum_errors.value = v

    @property
    def udp_checksum_errors_rate(self):
        return self._udp_checksum_errors_rate.value

    @udp_checksum_errors_rate.setter
    def udp_checksum_errors_rate(self, v):
        self._udp_checksum_errors_rate.value = v

    @property
    def udp_packets(self):
        return self._udp_packets.value

    @udp_packets.setter
    def udp_packets(self, v):
        self._udp_packets.value = v

    @property
    def udp_packets_rate(self):
        return self._udp_packets_rate.value

    @udp_packets_rate.setter
    def udp_packets_rate(self, v):
        self._udp_packets_rate.value = v

    @property
    def undersize(self):
        return self._undersize.value

    @undersize.setter
    def undersize(self, v):
        self._undersize.value = v

    @property
    def undersize_rate(self):
        return self._undersize_rate.value

    @undersize_rate.setter
    def undersize_rate(self, v):
        self._undersize_rate.value = v

    @property
    def user_defined_stat_1(self):
        return self._user_defined_stat_1.value

    @user_defined_stat_1.setter
    def user_defined_stat_1(self, v):
        self._user_defined_stat_1.value = v

    @property
    def user_defined_stat_1_rate(self):
        return self._user_defined_stat_1_rate.value

    @user_defined_stat_1_rate.setter
    def user_defined_stat_1_rate(self, v):
        self._user_defined_stat_1_rate.value = v

    @property
    def user_defined_stat_2(self):
        return self._user_defined_stat_2.value

    @user_defined_stat_2.setter
    def user_defined_stat_2(self, v):
        self._user_defined_stat_2.value = v

    @property
    def user_defined_stat_2_rate(self):
        return self._user_defined_stat_2_rate.value

    @user_defined_stat_2_rate.setter
    def user_defined_stat_2_rate(self, v):
        self._user_defined_stat_2_rate.value = v

    @property
    def vlan_tagged_frames_rx(self):
        return self._vlan_tagged_frames_rx.value

    @vlan_tagged_frames_rx.setter
    def vlan_tagged_frames_rx(self, v):
        self._vlan_tagged_frames_rx.value = v

    @property
    def vlan_tagged_frames_rx_rate(self):
        return self._vlan_tagged_frames_rx_rate.value

    @vlan_tagged_frames_rx_rate.setter
    def vlan_tagged_frames_rx_rate(self, v):
        self._vlan_tagged_frames_rx_rate.value = v


    def __str__(self):
        temp_str = ""
        allClassMembers = inspect.getmembers(self)
        for memberType, memberName in allClassMembers:
            if (str(memberType)[0] == "_" and str(memberType)[1] != "_" and str(memberType) != "_stats_type" and not inspect.ismethod(memberName)):
                temp_str += "\n{}:{}".format(memberName._name, memberName.value)
        return temp_str

    def _reset_stats(self, stat_type=str):
        allClassMembers = inspect.getmembers(self)
        for memberType, memberName in allClassMembers:
            if (str(memberType)[0] == "_" and str(memberType)[1] != "_" and str(memberType) != "_stats_type" and not inspect.ismethod(memberName)):
                memberName._clear()

    def set_stats_type(self, stat_type=str):
        if stat_type == str:
            self._stats_type = str
        elif stat_type == int:
            self._stats_type = int

        allClassMembers = inspect.getmembers(self)
        for memberType, memberName in allClassMembers:
            if (str(memberType)[0] == "_" and str(memberType)[1] != "_" and str(memberType) != "_stats_type" and not inspect.ismethod(memberName)):
                memberName._set_return_type(stat_type)

    def _count_error_stats(self, counters_name_list=list()):

        allClassMembers = inspect.getmembers(self)
        error_stats_dict = {}
        error_counters_list = [
            "alignment_errors",
            "alignment_errors_rate",
            "asynchronous_frames_sent",
            "asynchronous_frames_sent_rate",
            "collision_frames",
            "collision_frames_rate",
            "collisions",
            "collisions_rate",
            "data_integrity_errors",
            "data_integrity_errors_rate",
            "dribble_errors",
            "dribble_errors_rate",
            "dropped_frames",
            "dropped_frames_rate",
            "excessive_collision_frames",
            "excessive_collision_frames_rate",
            "crc_errors",
            "crc_errors_rate",
            "ip_checksum_errors",
            "ip_checksum_errors_rate",
            "late_collisions",
            "late_collisions_rate",
            "oversize_and_crc_errors",
            "oversize_and_crc_errors_rate",
            "prbs_errored_bits",
            "sequence_errors",
            "sequence_errors_rate",
            "symbol_error_frames",
            "symbol_error_frames_rate",
            "symbol_errors",
            "symbol_errors_rate",
            "synch_error_frames",
            "synch_error_frames_rate",
            "tcp_checksum_errors",
            "tcp_checksum_errors_rate",
            "udp_checksum_errors",
            "udp_checksum_errors_rate",
        ]
        if counters_name_list:
            error_counters_list = counters_name_list
        for memberType, memberName in allClassMembers:
            if (str(memberType)[0] == "_" and str(memberType)[1] != "_" and str(memberType) != "_stats_type" and not inspect.ismethod(memberName)):
                stat_name = memberName._name
                stat_val = memberName._value
                if stat_name in error_counters_list:
                    if float(stat_val) > 0.0:
                        error_stats_dict[stat_name] = stat_val
        return error_stats_dict

class _DATA_INTEGRITY(object):
    def __init__(self):
        self._enable = attrWithDefault(False)
        self._signature = attrWithDefault("08711800")
        self._signature_offset = attrWithDefault("40")
        self._enable_time_stamp = attrWithDefault(False)

    def __iter__(self):
        return iter([attr for attr in dir(self) if attr[:2] != "__"])

    @property
    def enable(self):
        """_enable : """
        return self._enable.current_val

    @enable.setter
    def enable(self, v):
        """_enable : """
        self._enable.current_val = v

    @property
    def signature(self):
        """_signature : """
        val = self._signature.current_val.rstrip("}")
        val = val.lstrip("{")
        return val

    @signature.setter
    def signature(self, v):
        """_signature : """
        v = "{" + v + "}"
        self._signature.current_val = v

    @property
    def signature_offset(self):
        """_signature_offset : """
        return self._signature_offset.current_val

    @signature_offset.setter
    def signature_offset(self, v):
        """_signature_offset : """
        self._signature_offset.current_val = v

    @property
    def enable_time_stamp(self):
        """_enable_time_stamp : """
        return self._enable_time_stamp.current_val

    @enable_time_stamp.setter
    def enable_time_stamp(self, v):
        """_enable_time_stamp : """
        self._enable_time_stamp.current_val = v

    def _reset_to_default(self):
        self._enable._reset_to_default()
        self._signature._reset_to_default()
        self._signature_offset._reset_to_default()
        self._enable_time_stamp._reset_to_default()

class automatic_instrumentation_signature(object):
    def __init__(self):
        self._enabled = attrWithDefault(None)
        self._start_scan_at = attrWithDefault(0)
        self._signature_value = attrWithDefault('87 73 67 49 42 87 11 80 08 71 18 05')

    @property
    def enabled(self):
        return self._enabled.current_val

    @enabled.setter
    def enabled(self, v):
        self._enabled.current_val = v

    # @property
    # def start_scan_at(self):
    #     return self._start_scan_at.current_val
    #
    # @start_scan_at.setter
    # def start_scan_at(self, v):
    #     self._start_scan_at.current_val = v
    #
    # @property
    # def signature_value(self):
    #     return self._signature_value.current_val
    #
    # @signature_value.setter
    # def signature_value(self, v):
    #     self._signature_value.current_val = v


class _RECEIVE_MODE(object):
    def __init__(self):
        self._capture = attrWithDefault(True)
        self._echo = attrWithDefault(False)
        self._packet_group = attrWithDefault(False)
        self._wide_packet_group = attrWithDefault(False)
        self._sequence_checking = attrWithDefault(False)
        self._data_inetgrity = attrWithDefault(False)
        self._prbs = attrWithDefault(False)
        self.automatic_signature = automatic_instrumentation_signature()


    def __iter__(self):
        return iter([attr for attr in dir(self) if attr[:2] != "__"])

    @property
    def capture(self):
        """_capture : """
        return self._capture.current_val

    @capture.setter
    def capture(self, v):
        """_capture : """
        self._capture.current_val = v

    @property
    def echo(self):
        """_echo : """
        return self._echo.current_val

    @echo.setter
    def echo(self, v):
        """_echo : """
        self._echo.current_val = v

    @property
    def packet_group(self):
        """_packet_group : """
        return self._packet_group.current_val

    @packet_group.setter
    def packet_group(self, v):
        """_packet_group : """
        self._packet_group.current_val = v

    @property
    def wide_packet_group(self):
        """_wide_packet_group : """
        return self._wide_packet_group.current_val

    @wide_packet_group.setter
    def wide_packet_group(self, v):
        """_wide_packet_group : """
        self._wide_packet_group.current_val = v

    @property
    def sequence_checking(self):
        """_sequence_checking : """
        return self._sequence_checking.current_val

    @sequence_checking.setter
    def sequence_checking(self, v):
        """_sequence_checking : """
        self._sequence_checking.current_val = v

    @property
    def data_inetgrity(self):
        """_data_inetgrity : """
        return self._data_inetgrity.current_val

    @data_inetgrity.setter
    def data_inetgrity(self, v):
        """_data_inetgrity : """
        self._data_inetgrity.current_val = v

    @property
    def prbs(self):
        """_prbs : """
        return self._prbs.current_val

    @prbs.setter
    def prbs(self, v):
        """_prbs : """
        self._prbs.current_val = v

class match_term(object):
    def __init__(self,pattern,offset,mask = None):
        self._id = None
        #self.name = name
        self._offset = offset
        self._pattern = '{'+pattern+'}'
        self._mask = '{' + mask + '}' if mask is not None else None
        if offset == 0:
            self._type = TGEnums.MATCH_TERM_TYPE.MAC_DA
        elif offset == 6:
            self._type = TGEnums.MATCH_TERM_TYPE.MAC_SA
        else :
            self._type = TGEnums.MATCH_TERM_TYPE.CUSTOM

    @property
    def offset(self):
        """enabled : """
        return self._offset

    @offset.setter
    def offset(self, v):
        """enabled docstring"""
        self._offset = v

    @property
    def pattern(self):
        """enabled : """
        return self._pattern

    @pattern.setter
    def pattern(self, v):
        """enabled docstring"""
        self._pattern = v

    @property
    def mask(self):
        """enabled : """
        return self._mask

    @mask.setter
    def mask(self, v):
        """enabled docstring"""
        self._mask = v

class length_match_term(object):
    def __init__(self, from_size, to_size):
        #self.name = name
        self._type = TGEnums.MATCH_TERM_TYPE.SIZE
        self._from_size = attrWithDefault(from_size)
        self._to_size = attrWithDefault(to_size)

    @property
    def from_size(self):
        """enabled : """
        return self._from_size.current_val

    @from_size.setter
    def from_size(self, v):
        """enabled docstring"""
        self._from_size.current_val = v

    @property
    def to_size(self):
        """enabled : """
        return self._to_size.current_val

    @to_size.setter
    def to_size(self, v):
        """enabled docstring"""
        self._to_size.current_val = v

class condition(object):
    def __init__(self,term,operator):
        self._match_term = attrWithDefault(_FILTER_PROPERTIES.match_terms[term])#type:match_term
        self._logical_operator = attrWithDefault(operator) # type: TGEnums.LOGICAL_OPERATOR

    @property
    def logical_operator(self):
        """logical_operator : """
        return self._logical_operator.current_val

    @logical_operator.setter
    def logical_operator(self, v):
        """enabled docstring"""
        self._logical_operator.current_val = v

    @property
    def match_term(self):
        """enabled : """
        return self._match_term.current_val

    @match_term.setter
    def match_term(self, v):
        """enabled docstring"""
        self._match_term.current_val = v

class trafficFilter(object):
    def __init__(self, default=False):
        self._enabled = attrWithDefault(default)
        self.conditions = [] #type: list[condition]
        self._errors = attrWithDefault(None)

    @property
    def enabled(self):
        """enabled : """
        return self._enabled.current_val

    @enabled.setter
    def enabled(self, v):
        """
        Enable/Disable filter
        :param v:
        :type v: bool
        :return:
        :rtype:
        """
        self._enabled.current_val = v

    @property
    def errors(self):
        """enabled : """
        return self._errors.current_val

    @errors.setter
    def errors(self, v):
        """enabled docstring"""
        self._errors.current_val = v

    def add_condition(self,matchterm,logical_operator= TGEnums.LOGICAL_OPERATOR.AND):
        """
        Create & add contition to filter,condition = term + logical operator
        :param matchterm:  name/key of matchterm found in global terms dictionary
        :type matchterm: basestring
        :param logical_operator: and/or/not
        :type logical_operator: TGEnums.LOGICAL_OPERATOR
        """
        x = condition(matchterm,logical_operator)
        self.conditions.append(x)

    def _get_match_term_list(self):
        terms = []
        for cond in self.conditions:
            terms.append(cond.match_term)
        return terms

class _FILTER_PROPERTIES(object):
    match_terms = OrderedDict()  # type: list[match_term]

    def __init__(self):
        self.filters = [None]  #type: list[trafficFilter]
        self.filters.insert(1, trafficFilter())
        self.filters.insert(2, trafficFilter())
        self.filters.insert(3, trafficFilter(default=True))
        self.capture_filter = trafficFilter(default=True)

    @classmethod
    def create_match_term(cls,pattern,offset, mask=None,name=None):
        """
        Create & add term to global terms dictinary and return key  ;term = pattern+offset+mask
        :param pattern:
        :type pattern: string
        :param offset:
        :type offset: int
        :param mask:
        :type mask: string
        :param name:
        :type name:
        :return: name/key of pattern
        :rtype: basestring
        """
        if name is None:
            name =''.join(e for e in pattern if e.isalnum())+'_'+str(offset)
        cls.match_terms[name] = match_term(pattern,offset,mask)
        return name

    @classmethod
    def create_size_match_term(cls,from_size,to_size , name = None):
        if name is None:
            name ='from_'+str(from_size)+'_to_'+str(to_size)
        cls.match_terms[name] = length_match_term(from_size,to_size)
        return name










