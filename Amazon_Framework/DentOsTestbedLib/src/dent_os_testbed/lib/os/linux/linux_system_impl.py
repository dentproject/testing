from dent_os_testbed.lib.os.linux.linux_system import LinuxSystem


class LinuxSystemImpl(LinuxSystem):
    def format_reboot(self, command, *argv, **kwarg):

        """
        Reboot the system

        """
        cmd = "#reboot"
        # custom code here

        return cmd
