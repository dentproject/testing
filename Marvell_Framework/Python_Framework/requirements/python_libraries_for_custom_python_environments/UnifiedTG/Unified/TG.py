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

import sys
import logging
from collections import OrderedDict
import inspect
from UnifiedTG.Unified.UtgObject import UtgObject
from UnifiedTG.Unified.Port import Port
from UnifiedTG.Unified.TgInfo import *
from UnifiedTG.Unified.ObjectCreator import objectCreator
from UnifiedTG.Unified.Chassis import Chassis,Card,resourceGroup


class UtgOrderedDict(OrderedDict):
    def __getitem__(self, items):
        item = super(self.__class__, self).__getitem__(items)
        return item


class Traffic(UtgObject):

    def __init__(self):
        stack = inspect.stack()
        self._parent = stack[1][0].f_locals['self']
        self.item_stats = None

    def l23_start(self,blocking=False):
        pass

    def l23_stop(self):
        pass

    def apply(self):
        pass

    def read_item_stats(self):
        pass


class Protocols(UtgObject):

    def __init__(self):
        stack = inspect.stack()
        self._parent = stack[1][0].f_locals['self']
        self.global_stats = None
        self.flow_stats = None

    def start(self,protocol=None):
        pass

    def stop(self,protocol=None):
        pass

    def action(self,protocol,action):
        pass

    def read_global_stats(self):
        pass

    def read_flow_stats(self):
        pass


class QuickTests(object):

    def __init__(self):
        stack = inspect.stack()
        self._parent = stack[1][0].f_locals['self']
        self.flow_view = None

    def apply(self, name='QuickTest1'):
        pass

    def start(self, name='QuickTest1', blocking=False, timeout=3600):
        pass

    def stop(self, name='QuickTest1'):
        pass

    def wait_for_status(self, name='QuickTest1', status=False, timeout=3600):
        pass

    def read_flow_view(self):
        pass


class TG(UtgObject):
    def __init__(self, server_host, login_name, server_tcp_port):
        # self._vendor_compatability_matrix = {
        #     "ixia": True,
        #     "stc": True,
        #     "xena": True,
        #     "ostinato": True
        # }

        self._server_host = server_host
        self._server_tcp_port = server_tcp_port
        self._login_name = login_name
        self.ports = OrderedDict()  # type: list[Port]
        self.chassis = UtgOrderedDict()  # type: list[Chassis]
        self._objCreator = None  # type: objectCreator
        self._connector = None
        self.waitLinkUpOnTx = None
        self.traffic = Traffic()
        self.protocols = Protocols()
        self.quick_tests = QuickTests()

    def __str__(self):
        tempstr = "Server_host: {}\nServer_tcp_port: {}\nLogin_name: {}\nPorts [".format(self._server_host, self._server_tcp_port, self._login_name)
        for port in self.ports:
            tempstr += "{}, ".format(str(port))
        tempstr += "]\n"
        return tempstr

    def discover(self,chassisList):
        pass

    def _connect(self,chassisList = None):
        if not self._connector.connected:
            try:
                self._connector.connect(self._login_name)
            except Exception as e:
                raise Exception('Failed to connect to server host: {}:{} \nDriver response: {}'.format(self._server_host,self._server_tcp_port,str(e)))
        if chassisList is not None:
            for chasIp in chassisList:
                if chasIp not in self.chassis:
                    try:
                        self._connector.add(chasIp)
                        self.chassis[chasIp] = self._objCreator.create_chassis(chasIp)
                        self.chassis[chasIp]._parent = self
                    except Exception as e:

                        raise Exception('Failed on add chassis \nDriver response: {}\n'
                                        'You are trying to connect to the Chassis: {} ,type: {},using Server {},\n'
                                        .format(str(e),chasIp, self._objCreator._type,self._server_host))
    def disconnect(self):
        try:
            self._connector.disconnect()
        except Exception as e:
            print(str(e))

    def _port_name_by_uri(self,uri):
        pName = list(filter(lambda p: self.ports[p]._port_uri == uri, self.ports))
        return pName[0] if pName else None

    def _remove_ports(self,uri_list):
        pNames = []
        for uri in uri_list:
            pName = self._port_name_by_uri(uri)
            if pName:
                self.ports[pName]._port_driver_obj.release()
                del self.ports[pName]
                pNames.append(pName)
                #todo delete from UTG
                #del utg.ports[pName]
        return pNames

    def reserve_ports(self, ports_list, force=False, clear=False):
        """
        Create port objects and take reservation

        :param ports_list: list of port names and port uri, example: ["port_name_1:0.0.0.0/1/1", "port_name_2:0.0.0.0/1/2"]
        :type ports_list: list
        :param force: Take port ownership regardless of current owner
        :type force: bool
        :param clear: Clear configuration when taking port ownership or not
        :type clear: bool
        """
        from UnifiedTG.Unified.UTG import utg
        pList = tgPortsInfo(ports_list)
        try:
            self._connect(pList.chassis_list)
        except Exception as e:
            raise Exception('Failed to connect to chassis:{}\nReason : {}'.format(pList.chassis_list,str(e))) #from None
            #raise Exception("Failed to connect to Chassis\n" + str(ports_list) + "\nReason: " + str(e))
        try:
            for pInfo in pList.pinfoList:
                self.ports[pInfo.name] = self._objCreator.create_port(pInfo.uri, pInfo.name)
                self.ports[pInfo.name]._parent = self
                utg.ports[pInfo.name] = self.ports[pInfo.name]
        except Exception as e:
            raise Exception('Failed to create port objects:{}\nReason:{}'.format(ports_list, str(e))) #from None
            #raise Exception("Failed to reserve ports\n" + str(ports_list) + "\nReason: " + str(e))

    def print_ports(self):
        """
        Prints all ports str representation in TG
        """
        for port in self.ports:
            print (str(self.ports[port]))

    def load_config_file(self, config_file_dict):
        """
        Load configuration files to list of ports, supports port or stream files.
        :param config_file_dict: dictionary of port names as keys and full file paths as keys, example: config_dict = {\n
        "my_port1":r"C:/path_to_file/port1.prt",\n
        "my_port2": r"C:/path_to_file/port2.prt",\n
        }
        :type config_file_dict: dict
        """
        pass

    def save_config_file(self, config_file_dict):
        """
        Save configuration files of list of ports, supports port or stream files.
        :param config_file_dict: dictionary of port names as keys and full file paths as keys, example: config_dict = {\n
        "my_port1":r"C:/path_to_file/port1.prt",\n
        "my_port2": r"C:/path_to_file/port2.prt",\n
        }
        :type config_file_dict: dict
        """
        pass

    def get_all_ports_stats(self):
        """
        Get all port stats of all ports from HW and update the statistics's member attributes
        """
        return self._create_list_of_port_objects()

    def get_all_streams_stats(self):
        """
        Get all stream stats of all streams from HW and update the statistics's member attributes
        """
        pass

    def get_streams_stats_by_list(self, stats_list=None):
        """
        Gets all streams stats by list of names of stats, or all if empty.\n
        Available stats:
        averageLatency, bigSequenceError, bitRate, byteRate, duplicateFrames, firstTimeStamp, frameRate,\n
        lastTimeStamp, maxDelayVariation, maxLatency, maxMinDelayVariation, maxminInterval, minDelayVariation,\n
        minLatency, numGroups, prbsBerRatio, prbsBitsReceived, prbsErroredBits, readTimeStamp, reverseSequenceError,\n
        sequenceGaps, smallSequenceError, standardDeviation, totalByteCount, totalFrames, totalSequenceError
        :param stats_list: list of str of stats names
        :type stats_list : list[str]
        """
        pass

    def start_traffic(self,port_or_port_list=None, blocking=False, start_packet_groups=True, wait_up = None):
        """
        Starts traffic on all ports or ports names list.
        :param port_or_port_list:
        :type port_or_port_list : list[Port]
        :param blocking: If set to True, function will not return until tx is done on all ports - use carefully only
        on bursty traffic.
        :type blocking: bool
        :param start_packet_groups: If set to True, will start collect stream stats as well.
        :type start_packet_groups: bool
        """
        common_wait_up = False
        global_wait_up = self.waitLinkUpOnTx
        if wait_up is None:
            if global_wait_up is True:
                common_wait_up = True
        elif wait_up is True:
            common_wait_up = True

        port_or_port_list = self._create_list_of_port_objects(port_or_port_list)
        if common_wait_up:
            for p in port_or_port_list:
                if not p.properties.ignore_link_status:
                    p.wait_link_up()
        return port_or_port_list

    def stop_traffic(self,port_or_port_list=None):
        """
        Stops traffic on all ports or ports names list.
        :param port_or_port_list:
        :type port_or_port_list: list of port names or none for all ports in session.
        """
        return self._create_list_of_port_objects(port_or_port_list)

    def start_capture(self,port_or_port_list=None):
        """
        Starts capture on all ports or ports names list.
        :param port_or_port_list:
        :type port_or_port_list: list of port names or none for all ports in session.
        """
        return self._create_list_of_port_objects(port_or_port_list)

    def stop_capture(self,port_or_port_list=None, cap_file_name="", cap_mode="buffer"):
        """
        :param port_or_port_list:
        :type port_or_port_list: list of port names or none for all ports in session.
        :param cap_file_name: currently not implemented.
        :param cap_mode: buffer mode - loops over the frames captured frames on port and append them\n
        to capture_buffer list.\n file_buffer mode - currently not supported.
        The capture_buffer is a list of str of bytes with space separation ("00 11 22 33...").
        """
        return self._create_list_of_port_objects(port_or_port_list)

    def hw_refresh(self):
        """
        Sync data from HW - currently does not update UTG objects
        """
        pass

    def configure_advanced_stats(self, rx_port_list=None, tx_streams_list=None, sequence_checking=True,
                                 data_integrity=True, time_stamp=True, starting_offset=40, prbs=False):
        """
        Loop over all ports or rx ports list and set the receive mode to collect PGID stats.
        :param rx_port_list: List of ports to set the receive mode on, or none for all.
        :type rx_port_list: bool
        :param tx_streams_list: Dict of port names as keys, each with list of stream names as values.
        :type tx_streams_list: dict
        :param sequence_checking: Add sequence checking signature (4 Bytes).
        :type sequence_checking: bool
        :param data_integrity: Add data integrity signature (4 Bytes).
        :type data_integrity: bool
        :param time_stamp: Add time stamp signature (2 Bytes).
        :type time_stamp: bool
        :param starting_offset: The offset of which to start adding signatures (8 Bytes for PGID + all optional).
        :type starting_offset: bool
        :param prbs: If set to true, disables data integrity, configures all other signatures to automatic.
        :type prbs: bool
        """
        pass

    def get_advanced_stats(self):
        """
        Gets all streams stats on all ports.\n
        :return:
        """
        pass

    def start_packet_groups(self, clear_time_stamps=True, port_list=list()):
        """
        Start collecting PGIDs on port list or all ports if empty (IXIA only)
        :param clear_time_stamps: Clear time stamps before TX
        :type clear_time_stamps: bool
        :param port_list: list of port names to start packet groups on
        :type port_list: list
        """
        pass

    def wait_for_link_up(self, timeout=60, port_list=list()):
        """
        Wait for the link to be in up state until timeout, or raise exception after timeout.
        :param timeout: The time to wait for up.
        :type timeout: int
        :param port_list: List of ports names to wait for up on, or all if empty.
        :type port_list: list
        """
        pass

    def clear_all_stats(self, port_list=list()):
        """
        Clear all statistic counters (port, streams and packet groups) on list of ports.
        :param port_list: list of ports to clear.
        :type port_list: list
        """
        port_or_port_list = self._create_list_of_port_objects(port_list)
        for p in port_or_port_list:
            p.clear_port_statistics()

    def release_ports(self):
        """
        Currently not implemented.
        """
        pass

    def _get_tg_log_title(self):
        title = "UTG.{}.{}()".format(self._login_name, inspect.stack()[1][3])
        return title

    def _get_tg_log_message(self):
        message = self.__str__()
        args, _, _, values_dict = inspect.getargvalues(inspect.stack()[1][0])
        values_dict_iter = iter((v, k) for k, v in values_dict.items() if not k.startswith('self') and not k.startswith('__'))
        message += "args:\n"
        for val, key in values_dict_iter:
            message += "{}: {}\n".format(key, val)
        return message

    def _create_list_of_port_objects(self,list_of_ports=None):
        port_list = []
        if not list_of_ports:
            for port in self.ports:
                port_list.append(self.ports[port])
        elif type(list_of_ports) == list:
            if isinstance(list_of_ports[0], Port):
                return list_of_ports
            for port in list_of_ports:
                port_list.append(self.ports[port])
        elif type(list_of_ports) == str:
            port_list.append(self.ports[list_of_ports])
        elif isinstance(list_of_ports, Port):
            port_list.append(list_of_ports)
        else:
            raise Exception("port_or_port_list is not a str or list of str of port names")
        return port_list