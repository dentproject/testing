from testbed.lib.onlp.linux.linux_onie import LinuxOnie


class LinuxOnieImpl(LinuxOnie):
    """
    To run onie-select
    """

    def format_select(self, command, *argv, **kwarg):
        """
        Onie select

        """
        params = kwarg["params"]
        cmd = "onie-select "
        ############# Implement me ################
        if "options" in params:
            cmd += params["options"]

        return cmd
