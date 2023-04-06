import json

from dent_os_testbed.lib.tc.linux.linux_tc_qdisc import LinuxTcQdisc


class LinuxTcQdiscImpl(LinuxTcQdisc):
    """
    tc  [  OPTIONS ] qdisc [ add | change | replace | link | delete ] dev DEV [ parent
    qdisc-id | root ] [ handle qdisc-id ] [ ingress_block BLOCK_INDEX ] [ egress_block
    BLOCK_INDEX ] qdisc [ qdisc specific parameters ]

    tc [ OPTIONS ] [ FORMAT ] qdisc show [ dev DEV ]

    """

    def format_modify(self, command, *argv, **kwarg):
        """
        tc  [  OPTIONS ] qdisc [ add | change | replace | link | delete ] dev DEV [ parent
        qdisc-id | root ] [ handle qdisc-id ] [ ingress_block BLOCK_INDEX ] [ egress_block
        BLOCK_INDEX ] qdisc [ qdisc specific parameters ]

        """
        params = kwarg['params']
        cmd = 'tc qdisc {} '.format(command)
        if 'dev' in params:
            cmd += 'dev {} '.format(params['dev'])
        if 'handle' in params:
            cmd += 'handle {} '.format(params['handle'])
        if 'parent' in params:
            cmd += 'parent {} '.format(params['parent'])
        if 'ingress_block' in params:
            cmd += 'ingress_block {} '.format(params['ingress_block'])
        if params.get('root'):
            cmd += 'root '
        cmd += '{} '.format(params.get('direction', ''))

        kind = params.get('kind', '')
        cmd += '{} '.format(kind)

        cmd += ' '.join(f'{key} {params[key]} '
                        for key in ('bands', 'strict', 'rate', 'burst', 'limit')
                        if key in params)

        cmd += ' '.join(f"{key} {' '.join(map(str, params[key]))} "
                        for key in ('quanta', 'priomap')
                        if key in params)

        return cmd

    def format_show(self, command, *argv, **kwarg):
        """
        tc [ OPTIONS ] [ FORMAT ] qdisc show [ dev DEV ]

        """
        params = kwarg['params']
        cmd = 'tc {} qdisc {} '.format(params.get('options', ''), command)
        if 'dev' in params:
            cmd += 'dev {} '.format(params['dev'])
        if 'handle' in params:
            cmd += 'handle {} '.format(params['handle'])
        if 'parent' in params:
            cmd += 'parent {} '.format(params['parent'])
        if params.get('root'):
            cmd += 'root '

        return cmd

    def parse_show(self, command, output, *argv, **kwarg):
        return json.loads(output)
