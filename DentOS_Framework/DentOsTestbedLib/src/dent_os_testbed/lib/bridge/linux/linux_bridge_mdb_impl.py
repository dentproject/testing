from dent_os_testbed.lib.bridge.linux.linux_bridge_mdb import LinuxBridgeMdb


class LinuxBridgeMdbImpl(LinuxBridgeMdb):
    """
    The corresponding commands display mdb entries, add new entries, and delete old ones.

    """

    def format_update(self, command, *argv, **kwarg):
        """
        bridge mdb { add | del } dev DEV port PORT grp GROUP [ permanent | temp ] [ vid VID ]

        """
        params = kwarg["params"]
        cmd = "bridge mdb {} ".format(command)
        ############# Implement me ################

        return cmd

    def format_show(self, command, *argv, **kwarg):
        """
        bridge mdb show [ dev DEV ]

        """
        params = kwarg["params"]
        cmd = "bridge mdb {} ".format(command)
        ############# Implement me ################

        return cmd
