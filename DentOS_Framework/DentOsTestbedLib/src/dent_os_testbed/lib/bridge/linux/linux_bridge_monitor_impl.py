from dent_os_testbed.lib.bridge.linux.linux_bridge_monitor import LinuxBridgeMonitor


class LinuxBridgeMonitorImpl(LinuxBridgeMonitor):
    """"""

    def format_monitor(self, command, *argv, **kwarg):
        """
        bridge monitor [ all | neigh | link | mdb ]

        """
        cmd = 'bridge monitor {} '.format(command)
        # TODO: Implement me

        return cmd
