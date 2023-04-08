import subprocess

from dent_os_testbed.lib.poe_tester.dni.dni_poe_tester import DniPoeTester
from dent_os_testbed.lib.poe_tester.dni.poe_tester_client import PoeTesterClient


class DniPoeTesterImpl(DniPoeTester):
    """
    - PoeTester
        attach - [hostname, serial_dev, baudrate]
        detach -
        configure_port - [input_data]
        get_port_stats -

    """

    client = None

    def format_attach(self, command, *argv, **kwarg):
        """
        - PoeTester
          attach - hostname, serial_dev, baudrate
          detach -

        """
        params = kwarg['params']
        cmd = ' {} '.format(command)
        # TODO: Implement me

        return cmd

    def run_attach(self, device, command, *argv, **kwarg):
        """
        - PoeTester
          attach - hostname, serial_dev, baudrate
          detach -

        """
        if (
            not hasattr(device, 'serial_dev')
            or not hasattr(device, 'host_name')
            or not hasattr(device, 'baudrate')
        ):
            return 0, 'Bad Device'
        if DniPoeTesterImpl.client:
            device.applog.info('Removing existing attached POE Tester Session')
            DniPoeTesterImpl.client.handler.close()
        subprocess.run(
            f"for session in $(screen -ls | grep -o '[0-9]*\\.{device.host_name}'); do screen -XS ${{session}} quit;  done",
            shell=True,
        )
        DniPoeTesterImpl.client = None
        if command == 'detach':
            return 0, 'Detached!'
        DniPoeTesterImpl.client = PoeTesterClient(
            device.host_name, device.serial_dev, device.baudrate
        )
        return 0, 'Attached!'

    def parse_attach(self, command, output, *argv, **kwarg):
        """
        - PoeTester
          attach - hostname, serial_dev, baudrate
          detach -

        """
        params = kwarg['params']
        cmd = ' {} '.format(command)
        # TODO: Implement me

        return cmd

    def format_configure_port(self, command, *argv, **kwarg):
        """
        - PoeTester
          configure_port -

        """
        params = kwarg['params']
        cmd = ' {} '.format(command)
        # TODO: Implement me

        return cmd

    def run_configure_port(self, device, command, *argv, **kwarg):
        """
        - PoeTester
          configure_port -

        """
        if (
            not hasattr(device, 'serial_dev')
            or not hasattr(device, 'host_name')
            or not hasattr(device, 'baudrate')
        ):
            return 0, 'Bad Device'
        if DniPoeTesterImpl.client is None:
            device.applog.info('POE Tester session is not attached!')
            return 0, ''
        params_list = kwarg['params']

        for params in params_list:
            if 'power pair type' in params:
                DniPoeTesterImpl.client.set_power_pair_config(params)
            if 'load level' in params:
                DniPoeTesterImpl.client.set_loading_config(params)
            if 'classification' in params:
                DniPoeTesterImpl.client.set_classification_config(params)
            if 'connection option' in params:
                DniPoeTesterImpl.client.set_test_connection(params)
            if 'lldp_option' in params:
                DniPoeTesterImpl.client.set_lldp_options(params)

        return 0, 'Port(s) configured!'

    def parse_configure_port(self, command, output, *argv, **kwarg):
        """
        - PoeTester
          configure_port -

        """
        params = kwarg['params']
        cmd = ' {} '.format(command)
        # TODO: Implement me

        return cmd

    def format_get_port_stats(self, command, *argv, **kwarg):
        """
        - PoeTester
          get_port_stats
        """
        params = kwarg['params']
        cmd = ' {} '.format(command)
        # TODO: Implement me

        return cmd

    def run_get_port_stats(self, device, command, *argv, **kwarg):
        """
        - PoeTester
          get_port_stats
        """
        if (
            not hasattr(device, 'serial_dev')
            or not hasattr(device, 'host_name')
            or not hasattr(device, 'baudrate')
        ):
            return 0, 'Bad Device'
        if DniPoeTesterImpl.client is None:
            device.applog.info('POE Tester session is not attached!')
            return 0, ''
        stats_dict = {}
        stats = list(filter(None, DniPoeTesterImpl.client.get_status()))
        title_index = stats.index(
            next((s for s in stats if s[0:2] == '<<' and s[-2:] == '>>'), None)
        )
        end_index = stats.index(next((s for s in stats if '<COMMAND>' in s), None))
        for line in stats[title_index + 1: end_index]:
            if '=' in line:
                continue
            tokens = line.split()
            if tokens[0] == 'Port':
                stats_dict = dict.fromkeys(list(map(int, tokens[1:])), None)
                stats_dict = {key: {} for key in tokens[1:]}
            else:
                category, values = line.split(':')
                category = category[: category.index('(') if '(' in category else None].strip()
                for index, value in enumerate(values.split()):
                    stats_dict[f'{index+1}'][category] = value
        return 0, stats_dict

    def parse_get_port_stats(self, command, output, *argv, **kwarg):
        """
        - PoeTester
          get_port_stats
        """
        params = kwarg['params']
        cmd = ' {} '.format(command)
        # TODO: Implement me

        return cmd
