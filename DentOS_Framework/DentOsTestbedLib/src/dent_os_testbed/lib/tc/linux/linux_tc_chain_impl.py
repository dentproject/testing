from dent_os_testbed.lib.tc.linux.linux_tc_chain import LinuxTcChain


class LinuxTcChainImpl(LinuxTcChain):
    """"""

    def format_modify(self, command, *argv, **kwarg):
        """
        tc [ OPTIONS ] chain [ add | delete | get ] dev DEV [ parent  qdisc-id  |  root  ]
        filtertype [ filtertype specific parameters ]
        tc [ OPTIONS ] chain [ add | delete | get ] block BLOCK_INDEX filtertype [ filter‐
        type specific parameters ]

        """
        params = kwarg['params']
        cmd = 'tc chain {} '.format(command)
        if 'dev' in params:
            cmd += 'dev {} '.format(params['dev'])
        if 'block' in params:
            cmd += 'block {} '.format(params['block'])
        if 'direction' in params:
            cmd += '{} '.format(params['direction'])
        if 'proto' in params:
            cmd += 'proto {} '.format(params['proto'])
        if 'chain' in params:
            cmd += 'chain {} '.format(params['chain'])
        if 'filtertype' in params:
            if type(params['filtertype']) is dict:
                cmd += 'flower '
                for field, value in params['filtertype'].items():
                    cmd += '{} {} '.format(field, value)

        return cmd

    def format_show(self, command, *argv, **kwarg):
        """
        tc [ OPTIONS ] chain show dev DEV
        tc [ OPTIONS ] chain show block BLOCK_INDEX

        """
        params = kwarg['params']
        cmd = 'tc chain {} '.format(command)
        # TODO: Implement me

        return cmd
