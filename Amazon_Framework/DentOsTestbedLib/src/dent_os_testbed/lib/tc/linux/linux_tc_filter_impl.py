from dent_os_testbed.lib.tc.linux.linux_tc_filter import LinuxTcFilter


class LinuxTcFilterImpl(LinuxTcFilter):
    """"""

    def format_modify(self, command, *argv, **kwarg):
        """
        tc [ OPTIONS ] filter [ add | change | replace | delete | get ] dev DEV  [  parent
        qdisc-id  | root ] [ handle filter-id ] protocol protocol prio priority filtertype
        [ filtertype specific parameters ] flowid flow-id
        tc [ OPTIONS ] filter [ add | change | replace | delete | get ] block  BLOCK_INDEX
        [  handle filter-id ] protocol protocol prio priority filtertype [ filtertype spe
        cific parameters ] flowid flow-id

        """
        params = kwarg["params"]
        cmd = "tc filter {} ".format(command)
        ############# Implement me ################

        return cmd

    def format_show(self, command, *argv, **kwarg):
        """
        tc [ OPTIONS ] filter show dev DEV
        tc [ OPTIONS ] filter show block BLOCK_INDEX

        """
        params = kwarg["params"]
        cmd = "tc filter {} ".format(command)
        ############# Implement me ################

        return cmd
