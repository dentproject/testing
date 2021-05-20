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
        params = kwarg["params"]
        cmd = "tc qdisc {} ".format(command)
        ############# Implement me ################

        return cmd

    def format_show(self, command, *argv, **kwarg):
        """
        tc [ OPTIONS ] [ FORMAT ] qdisc show [ dev DEV ]

        """
        params = kwarg["params"]
        cmd = "tc qdisc {} ".format(command)
        ############# Implement me ################

        return cmd
