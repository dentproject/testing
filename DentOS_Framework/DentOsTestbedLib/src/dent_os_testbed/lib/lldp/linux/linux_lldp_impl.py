import json

from dent_os_testbed.lib.lldp.linux.linux_lldp import LinuxLldp


class LinuxLldpImpl(LinuxLldp):
    """
    LLDP module

    """

    def format_show(self, command, *argv, **kwarg):
        """
        Usage:   lldpctl [OPTIONS ...] [COMMAND ...]
        Version: lldpd 2020-09-23
        -d          Enable more debugging information.
        -u socket   Specify the Unix-domain socket used for communication with lldpd(8).
        -f format   Choose output format (plain, keyvalue, json, json0, xml).
        see manual page lldpcli(8) for more information

        """
        params = kwarg['params']
        if params.get('dut_discovery', False):
            params['cmd_options'] = '-f json'
        cmd = 'lldpctl {} '.format(params.get('cmd_options', ''))
        if 'interface' in kwarg['params']:
            cmd += ' {} '.format(kwarg['params']['interface'])
        return cmd

    def parse_show(self, command, output, *argv, **kwarg):
        interfaces = []
        try:
            parsed_out = json.loads(output)
            for interface in parsed_out['lldp']['interface']:
                for port, data in interface.items():
                    item = {'interface': port, 'remote_interface': data['port']['id']['value']}
                    for chassis in data['chassis']:
                        item['remote_host'] = chassis
                    interfaces.append(item)
        except Exception as e:
            return []
        return interfaces

    def format_set(self, command, *argv, **kwarg):
        """
        Usage:   lldpcli [OPTIONS ...] [COMMAND ...]
        Version: lldpd 2020-09-23
        -d          Enable more debugging information.
        -u socket   Specify the Unix-domain socket used for communication with lldpd(8).
        -f format   Choose output format (plain, keyvalue, json, json0, xml).
        see manual page lldpcli(8) for more information

        """
        params = kwarg['params']
        cmd = 'lldpcli {} '.format(command)
        # TODO: Implement me

        return cmd

    def parse_set(self, command, output, *argv, **kwarg):
        """
        Usage:   lldpcli [OPTIONS ...] [COMMAND ...]
        Version: lldpd 2020-09-23
        -d          Enable more debugging information.
        -u socket   Specify the Unix-domain socket used for communication with lldpd(8).
        -f format   Choose output format (plain, keyvalue, json, json0, xml).
        see manual page lldpcli(8) for more information

        """
        params = kwarg['params']
        cmd = 'lldpcli {} '.format(command)
        # TODO: Implement me

        return cmd
