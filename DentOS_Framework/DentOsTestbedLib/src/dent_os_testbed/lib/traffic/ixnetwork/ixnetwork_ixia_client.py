# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# generated using file ./gen/model/traffic/ixia/ixia.yaml
#
# DONOT EDIT - generated by diligent bots

from dent_os_testbed.lib.test_lib_object import TestLibObject
class IxnetworkIxiaClient(TestLibObject):
    """
        - IxiaClient
            connect - client_addr, ports
            disconnect -
            load_config - [config_file_name]
            save_config - [config_file_name]
            set_traffic - [traffic_names]
            start_traffic - [traffic_names]
            stop_traffic  - [traffic_names]
            get_stats - [traffic_names]
            clear_stats - [traffic_names]
            start_protocols - [protocols]
            stop_protocols - [protocols]
            set_protocol - [protocol]
            get_protocol_stats - [protocols]
            clear_protocol_stats - [protocols]
            send_ping - [port, dst_ip, src_ip]
            send_arp - [port, src_ip]
            send_ns - [port, src_ip]
            update_l1_config - ['speed', 'autoneg', 'tgen_ports', 'duplex']
            clear_traffic - [traffic_names]
            switch_min_frame_size - [enable_min_size]

    """
    def format_connect(self, command, *argv, **kwarg):
        raise NotImplementedError

    def run_connect(self, device, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_connect(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_config(self, command, *argv, **kwarg):
        raise NotImplementedError

    def run_config(self, device, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_config(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_traffic_item(self, command, *argv, **kwarg):
        raise NotImplementedError

    def run_traffic_item(self, device, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_traffic_item(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_protocol(self, command, *argv, **kwarg):
        raise NotImplementedError

    def run_protocol(self, device, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_protocol(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_send_ping(self, command, *argv, **kwarg):
        raise NotImplementedError

    def run_send_ping(self, device, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_send_ping(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_resolve_neighbor(self, command, *argv, **kwarg):
        raise NotImplementedError

    def run_resolve_neighbor(self, device, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_resolve_neighbor(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_update_l1_config(self, command, *argv, **kwarg):
        raise NotImplementedError

    def run_update_l1_config(self, device, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_update_l1_config(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_switch_min_frame_size(self, command, *argv, **kwarg):
        raise NotImplementedError

    def run_switch_min_frame_size(self, device, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_switch_min_frame_size(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_command(self, command, *argv, **kwarg):
        if command in ['connect', 'disconnect']:
            return self.format_connect(command, *argv, **kwarg)

        if command in ['load_config', 'save_config']:
            return self.format_config(command, *argv, **kwarg)

        if command in ['set_traffic', 'start_traffic', 'stop_traffic', 'get_stats', 'clear_stats', 'clear_traffic', 'get_drilldown_stats']:
            return self.format_traffic_item(command, *argv, **kwarg)

        if command in ['start_protocols', 'stop_protocols', 'set_protocol', 'get_protocol_stats', 'clear_protocol_stats']:
            return self.format_protocol(command, *argv, **kwarg)

        if command in ['send_ping']:
            return self.format_send_ping(command, *argv, **kwarg)

        if command in ['send_arp', 'send_ns']:
            return self.format_resolve_neighbor(command, *argv, **kwarg)

        if command in ['update_l1_config']:
            return self.format_update_l1_config(command, *argv, **kwarg)

        if command in ['switch_min_frame_size']:
            return self.format_switch_min_frame_size(command, *argv, **kwarg)


        raise NameError('Cannot find command '+command)

    def run_command(self, device_obj, command, *argv, **kwarg):
        if command in ['connect', 'disconnect']:
            return self.run_connect(device_obj, command, *argv, **kwarg)

        if command in ['load_config', 'save_config']:
            return self.run_config(device_obj, command, *argv, **kwarg)

        if command in ['set_traffic', 'start_traffic', 'stop_traffic', 'get_stats', 'clear_stats', 'clear_traffic', 'get_drilldown_stats']:
            return self.run_traffic_item(device_obj, command, *argv, **kwarg)

        if command in ['start_protocols', 'stop_protocols', 'set_protocol', 'get_protocol_stats', 'clear_protocol_stats']:
            return self.run_protocol(device_obj, command, *argv, **kwarg)

        if command in ['send_ping']:
            return self.run_send_ping(device_obj, command, *argv, **kwarg)

        if command in ['send_arp', 'send_ns']:
            return self.run_resolve_neighbor(device_obj, command, *argv, **kwarg)

        if command in ['update_l1_config']:
            return self.run_update_l1_config(device_obj, command, *argv, **kwarg)

        if command in ['switch_min_frame_size']:
            return self.run_switch_min_frame_size(device_obj, command, *argv, **kwarg)


        print (len(command))
        raise NameError('Cannot find command '+command)

    def parse_output(self, command, output, *argv, **kwarg):
        if command in ['connect', 'disconnect']:
            return self.parse_connect(command, output, *argv, **kwarg)

        if command in ['load_config', 'save_config']:
            return self.parse_config(command, output, *argv, **kwarg)

        if command in ['set_traffic', 'start_traffic', 'stop_traffic', 'get_stats', 'clear_stats', 'clear_traffic', 'get_drilldown_stats']:
            return self.parse_traffic_item(command, output, *argv, **kwarg)

        if command in ['start_protocols', 'stop_protocols', 'set_protocol', 'get_protocol_stats', 'clear_protocol_stats']:
            return self.parse_protocol(command, output, *argv, **kwarg)

        if command in ['send_ping']:
            return self.parse_send_ping(command, output, *argv, **kwarg)

        if command in ['send_arp', 'send_ns']:
            return self.parse_resolve_neighbor(command, output, *argv, **kwarg)

        if command in ['update_l1_config']:
            return self.parse_update_l1_config(command, output, *argv, **kwarg)

        if command in ['switch_min_frame_size']:
            return self.parse_switch_min_frame_size(command, output, *argv, **kwarg)


        raise NameError('Cannot find command '+command)
