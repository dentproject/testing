from dent_os_testbed.lib.tc.linux.linux_tc_monitor import LinuxTcMonitor


class LinuxTcMonitorImpl(LinuxTcMonitor):
    """"""

    def format_show(self, command, *argv, **kwarg):
        """
        tc [ OPTIONS ] monitor [ file FILENAME ]

        """
        cmd = 'tc  {} '.format(command)
        # TODO: Implement me

        return cmd
