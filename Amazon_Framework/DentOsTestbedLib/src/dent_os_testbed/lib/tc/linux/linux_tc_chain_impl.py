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
        params = kwarg["params"]
        cmd = "tc chain {} ".format(command)
        ############# Implement me ################

        return cmd

    def format_show(self, command, *argv, **kwarg):
        """
        tc [ OPTIONS ] chain show dev DEV
        tc [ OPTIONS ] chain show block BLOCK_INDEX

        """
        params = kwarg["params"]
        cmd = "tc chain {} ".format(command)
        ############# Implement me ################

        return cmd
