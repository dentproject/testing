import json
from dent_os_testbed.lib.dcb.linux.linux_dcb_app import LinuxDcbApp


class LinuxDcbAppImpl(LinuxDcbApp):
    """
        dcb [ OPTIONS ] { app | buffer | ets | maxrate | pfc } { COMMAND | help }
        dcb [ -force ] -batch filename
        dcb [ OPTIONS ] help

    """

    def format_set(self, command, *argv, **kwarg):
        """
        dcb app {  add  |  del  |  replace  }  dev DEV [ default-prio
                PRIO-LIST ] [ ethtype-prio ET-MAP ] [ stream-port-prio
                PORT-MAP ] [ dgram-port-prio PORT-MAP ] [ port-prio PORT-
                MAP ] [ dscp-prio DSCP-MAP ]

        """
        params = kwarg['params']
        cmd = 'dcb {} app {} dev {} '.format(
            params.get('options', ''),
            command,
            params['dev'])

        if 'default_prio' in params:
            cmd += 'default-prio ' + ' '.join(map(str, params['default_prio']))

        for dcb_param in ('dscp_prio', 'ethtype_prio', 'port_prio',
                          'stream_port_prio', 'dgram_port_prio'):
            if dcb_param not in params:
                continue
            prio_map = (f'{key}:{prio}' for key, prio in params[dcb_param])
            cmd += dcb_param.replace('_', '-') + ' ' + ' '.join(prio_map)

        return cmd

    def format_show(self, command, *argv, **kwarg):
        """
        dcb app {  show  |  flush  }  dev DEV [ default-prio ] [
                ethtype-prio ] [ stream-port-prio ] [ dgram-port-prio ] [
                port-prio ] [ dscp-prio ]

        """
        params = kwarg['params']
        cmd = 'dcb {} app {} dev {} '.format(
            params.get('options', ''),
            command,
            params['dev'])

        opts = [dcb_param.replace('_', '-')
                for dcb_param in ('default_prio', 'dscp_prio', 'ethtype_prio',
                                  'port_prio', 'stream_port_prio', 'dgram_port_prio')
                if params.get(dcb_param)]
        cmd += ' '.join(opts)

        return cmd

    def parse_show(self, command, output, *argv, **kwarg):
        """
        dcb app {  show  |  flush  }  dev DEV [ default-prio ] [
                ethtype-prio ] [ stream-port-prio ] [ dgram-port-prio ] [
                port-prio ] [ dscp-prio ]

        """
        return json.loads(output)
