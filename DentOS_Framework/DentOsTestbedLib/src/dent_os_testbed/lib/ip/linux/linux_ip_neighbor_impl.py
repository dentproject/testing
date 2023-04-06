import json

from dent_os_testbed.lib.ip.linux.linux_ip_neighbor import LinuxIpNeighbor


class LinuxIpNeighborImpl(LinuxIpNeighbor):
    def format_modify(self, command, *argv, **kwarg):

        """
        ip neigh { add | del | change | replace } { ADDR [ lladdr LLADDR ]
                 [ nud { permanent | noarp | stale | reachable } ] | proxy ADDR } [ dev DEV ]

        """
        params = kwarg['params']
        cmd = 'ip neigh {} '.format(command)
        # custom code here
        if 'address' in params:
            cmd += '{} '.format(params['address'])
        if 'lladdr' in params:
            cmd += 'lladdr {} '.format(params['lladdr'])
        if 'nud' in params:
            cmd += 'nud {} '.format(params['nud'])
        if 'proxy' in params:
            cmd += 'proxy {} '.format(params['proxy'])
        if 'dev' in params:
            cmd += 'dev {} '.format(params['dev'])

        return cmd

    def format_show(self, command, *argv, **kwarg):

        """
        ip neigh { show | flush } [ proxy ] [ to PREFIX ] [ dev DEV ] [ nud STATE ]

        """
        params = kwarg['params']
        cmd = 'ip {} neigh {} '.format(params.get('cmd_options', ''), command)
        # custom code here
        if 'proxy' in params:
            cmd += '{} '.format(params['proxy'])
        if 'address' in params:
            cmd += 'to {} '.format(params['address'])
        if 'device' in params:
            cmd += 'dev {} '.format(params['device'])
        if 'nud' in params:
            cmd += 'nud {} '.format(params['nud'])

        return cmd

    def parse_show(self, command, output, *argv, **kwarg):
        return json.loads(output)
