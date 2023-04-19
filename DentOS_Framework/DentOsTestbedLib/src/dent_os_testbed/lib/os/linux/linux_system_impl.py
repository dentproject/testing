from dent_os_testbed.lib.os.linux.linux_system import LinuxSystem


class LinuxSystemImpl(LinuxSystem):
    def format_reboot(self, command, *argv, **kwarg):
        """
        Reboot the system

        """
        cmd = '#reboot'
        # custom code here

        return cmd

    def format_shutdown(self, command, *argv, **kwarg):
        """
        Shutdown the system

        """
        params = kwarg['params']
        cmd = 'shutdown '
        # TODO: Implement me
        if 'options' in params:
            cmd += params['options']

        return cmd
