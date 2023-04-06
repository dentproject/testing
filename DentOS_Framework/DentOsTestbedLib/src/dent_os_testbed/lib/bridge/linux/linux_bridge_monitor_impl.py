from dent_os_testbed.lib.bridge.linux.linux_bridge_monitor import LinuxBridgeMonitor


class LinuxBridgeMonitorImpl(LinuxBridgeMonitor):
    """"""

    def format_monitor(self, command, *argv, **kwarg):
        """
        bridge monitor [ all | neigh | link | mdb ]

        """
        params = kwarg['params']
        cmd = 'bridge monitor {} '.format(command)
        ############# Implement me ################

        return cmd
