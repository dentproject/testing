from dent_os_testbed.lib.traffic.ixnetwork.trex_tgn_client import TrexTgnClient


class TrexTgnClientImpl(TrexTgnClient):
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

    """

    def format_connect(self, command, *argv, **kwarg):
        """
        - IxiaClient
          connect - client_addr, ports
          disconnect -

        """
        return command

    def run_connect(self, device, command, *argv, **kwarg):
        """
        - IxiaClient
          connect - client_addr, ports
          disconnect -

        """
        # TODO: Implement me
        if command == 'disconnect':
            if TrexTgnClientImpl.session is not None:
                device.applog.info(
                    'Removing Session ID %d' % (TrexTgnClientImpl.session.ctx.session_id)
                )
                TrexTgnClientImpl.session.disconnect()
                TrexTgnClientImpl.session = None

        params = kwarg['params']
        if not params or not params[0] or 'test' in device.host_name:
            return 0, ''
        param = params[0]
        try:
            from trex_stl_lib.api import STLClient

            caddr = param['client_addr']
            if not caddr:
                return 0, 'No Address to connect!'
            TrexTgnClientImpl.session = STLClient(server=caddr)
            TrexTgnClientImpl.session.connect()
            device.applog.info(
                'Connection to TREX API Server Established %d'
                % (TrexTgnClientImpl.session.ctx.session_id)
            )
        except Exception as e:
            return -1, str(e)
        return 0, ''

    def parse_connect(self, command, output, *argv, **kwarg):
        """
        - IxiaClient
          connect - client_addr, ports
          disconnect -

        """
        cmd = ' {} '.format(command)
        # TODO: Implement me

        return cmd

    def format_config(self, command, *argv, **kwarg):
        """
        - IxiaClient
           load_config - config_file_name
           save_config - config_file_name

        """
        cmd = ' {} '.format(command)
        # TODO: Implement me

        return cmd

    def run_config(self, command, *argv, **kwarg):
        """
        - IxiaClient
           load_config - config_file_name
           save_config - config_file_name

        """
        # TODO: Implement me

        return 0, ''

    def parse_config(self, command, output, *argv, **kwarg):
        """
        - IxiaClient
           load_config - config_file_name
           save_config - config_file_name

        """
        cmd = ' {} '.format(command)
        # TODO: Implement me

        return cmd

    def format_traffic_item(self, command, *argv, **kwarg):
        """
        - IxiaClient
           set_traffic - [traffic_names], ports
           start_traffic - [traffic_names]
           stop_traffic  - [traffic_names]
           get_stats - [traffic_names]
           clear_stats - [traffic_names]

        """
        cmd = ' {} '.format(command)
        # TODO: Implement me

        return cmd

    def run_traffic_item(self, command, *argv, **kwarg):
        """
        - IxiaClient
           set_traffic - [traffic_names], ports
           start_traffic - [traffic_names]
           stop_traffic  - [traffic_names]
           get_stats - [traffic_names]
           clear_stats - [traffic_names]

        """
        # TODO: Implement me

        return 0, ''

    def parse_traffic_item(self, command, output, *argv, **kwarg):
        """
        - IxiaClient
           set_traffic - [traffic_names], ports
           start_traffic - [traffic_names]
           stop_traffic  - [traffic_names]
           get_stats - [traffic_names]
           clear_stats - [traffic_names]

        """
        cmd = ' {} '.format(command)
        # TODO: Implement me

        return cmd

    def format_protocol(self, command, *argv, **kwarg):
        """
        - IxiaClient
           start_protocols - [protocols]
           stop_protocols - [protocols]
           set_protocol - [protocol]
           get_protocol_stats - [protocols]
           clear_protocol_stats - [protocols]

        """
        cmd = ' {} '.format(command)
        # TODO: Implement me

        return cmd

    def run_protocol(self, command, *argv, **kwarg):
        """
        - IxiaClient
           start_protocols - [protocols]
           stop_protocols - [protocols]
           set_protocol - [protocol]
           get_protocol_stats - [protocols]
           clear_protocol_stats - [protocols]

        """
        # TODO: Implement me

        return 0, ''

    def parse_protocol(self, command, output, *argv, **kwarg):
        """
        - IxiaClient
           start_protocols - [protocols]
           stop_protocols - [protocols]
           set_protocol - [protocol]
           get_protocol_stats - [protocols]
           clear_protocol_stats - [protocols]

        """
        cmd = ' {} '.format(command)
        # TODO: Implement me

        return cmd
