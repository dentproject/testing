from dent_os_testbed.lib.frr.linux.linux_route_map import LinuxRouteMap


class LinuxRouteMapImpl(LinuxRouteMap):
    """
    vtysh

    """

    def format_configure(self, command, *argv, **kwarg):
        """"""
        params = kwarg['params']
        cmd = "vtysh -c 'conf terminal' "
        cmd += "-c 'route-map {}".format(params.get('mapname', ''))
        if 'options' in params and type(params['options']) is dict:
            for option, value in params.get('options', {}).items():
                cmd += ' {} {}'.format(option, value)
        cmd += "' "

        if 'match' in params and type(params['match']) is dict:
            cmd += "-c 'match "
            if 'as-path' in params['match']:
                cmd += 'as-path '
            if 'ip-prefix' in params['match']:
                cmd += 'ip address prefix-list {}'.format(params['match'].get('ip-prefix', ''))
            elif 'community' in params['match']:
                cmd += 'community {}'.format(params['match'].get('community', ''))
            elif 'access-list' in params['match']:
                cmd += '{}'.format(params['match'].get('access-list', ''))
            cmd += "' "
        if 'set' in params and type(params['set']) is dict:
            cmd += "-c 'set "
            if 'as-path' in params['set']:
                cmd += 'as-path '
                if 'prepend' in params['set']['as-path']:
                    cmd += 'prepend'
                    for asn in params['set']['as-path'].get('prepend', []):
                        cmd += ' {}'.format(asn)
            if 'metric' in params['set']:
                cmd += 'metric {}'.format(params['set'].get('metric', ''))
            if 'community' in params['set']:
                cmd += 'community {}'.format(params['set'].get('community', ''))
            if 'local-preference' in params['set']:
                cmd += 'local-preference {}'.format(params['set'].get('local-preference', ''))
            cmd += "' "

        return cmd

    def parse_configure(self, command, output, *argv, **kwarg):
        """"""
        params = kwarg['params']
        cmd = 'vtysh {} '.format(command)
        # TODO: Implement me

        return cmd
