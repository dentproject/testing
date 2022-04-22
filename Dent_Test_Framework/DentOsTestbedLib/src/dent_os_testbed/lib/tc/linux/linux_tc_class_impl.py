from dent_os_testbed.lib.tc.linux.linux_tc_class import LinuxTcClass


class LinuxTcClassImpl(LinuxTcClass):
    """"""

    def format_modify(self, command, *argv, **kwarg):
        """
        tc [ OPTIONS ] class [ add | change | replace | delete ] dev DEV parent qdisc-id [
        classid class-id ] qdisc [ qdisc specific parameters ]

        """
        params = kwarg["params"]
        cmd = "tc class {} ".format(command)
        ############# Implement me ################

        return cmd

    def format_show(self, command, *argv, **kwarg):
        """
        tc [ OPTIONS ] [ FORMAT ] class show dev DEV

        """
        params = kwarg["params"]
        cmd = "tc class {} ".format(command)
        ############# Implement me ################

        return cmd
