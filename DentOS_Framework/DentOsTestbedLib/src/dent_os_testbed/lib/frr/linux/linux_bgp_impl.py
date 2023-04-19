from dent_os_testbed.lib.frr.linux.linux_bgp import LinuxBgp


class LinuxBgpImpl(LinuxBgp):
    """
    vtysh

    """

    def format_show(self, command, *argv, **kwarg):
        """"""
        params = kwarg['params']
        cmd = "vtysh -c '{} {} bgp ".format(command, 'ip' if 'ip' in params else '')
        if 'ip' in params:
            if 'ip-address' in params['ip']:
                cmd += '{} '.format(params['ip']['ip-address'])
            if 'mask' in params['ip']:
                cmd += '{} '.format(params['ip']['mask'])
        if 'neighbors' in params:
            cmd += 'neighbors '
            for neighbor_name in params['neighbors']:
                cmd += '{} '.format(neighbor_name)
        elif 'type' in params:
            cmd += '{} '.format(params['type'])
            if 'ip-address' in params:
                cmd += '{} '.format(params['ip-address'])
            if 'mask' in params:
                cmd += '{} '.format(params['mask'])
        else:
            cmd += 'summary '
        cmd += params.get('options', '')
        cmd += "'"
        return cmd

    def parse_show(self, command, output, *argv, **kwarg):
        """"""
        cmd = 'vtysh {} '.format(command)
        # TODO: Implement me

        return cmd

    def format_configure(self, command, *argv, **kwarg):
        """"""
        params = kwarg['params']
        cmd = "vtysh -c 'conf terminal' "

        if 'asn' in params:
            cmd += "-c 'router bgp {}' ".format(params.get('asn', ''))
        if 'address-family' in params:
            cmd += "-c 'address-family {}' ".format(params['address-family'])
        if 'neighbor' in params:
            cmd += "-c 'neighbor "
            if 'ip' in params:
                cmd += '{} '.format(params['ip'])
                cmd += 'peer-group {}'.format(params.get('group', ''))
            else:
                cmd += '{}'.format(params.get('group', ''))
                if 'route-map' in params['neighbor']:
                    cmd += ' route-map {}'.format(
                        params['neighbor']['route-map'].get('mapname', '')
                    )
                    for option, value in params['neighbor']['route-map'].get('options', {}).items():
                        cmd += ' {} {}'.format(option, value)
                if type(params.get('neighbor')) is dict:
                    neighbor_option_set = params.get('neighbor', {}).get('options', {})
                    for neighbor_option in neighbor_option_set:
                        cmd += ' {} {}'.format(
                            neighbor_option, neighbor_option_set.get(neighbor_option, '')
                        )

            cmd += "'"

        return cmd

    def parse_configure(self, command, output, *argv, **kwarg):
        """"""
        cmd = 'vtysh {} '.format(command)
        # TODO: Implement me

        return cmd
