from dent_os_testbed.lib.frr.linux.linux_frr_ip import LinuxFrrIp


class LinuxFrrIpImpl(LinuxFrrIp):
    """
    vtysh

    """

    def format_set(self, command, *argv, **kwarg):
        """"""
        params = kwarg["params"]
        cmd = "vtysh -c 'conf terminal' -c 'ip"
        if "as-path" in params:
            cmd += " as-path"
        if "access-list" in params:
            cmd += " access-list {}".format(params.get("access-list", ""))
        if "prefix-list" in params:
            cmd += " prefix-list {}".format(params.get("prefix-list", ""))
        if "sequence" in params:
            cmd += " seq {}".format(params.get("sequence", ""))
        if "options" in params and type(params["options"]) is dict:
            for option, value in params["options"].items():
                cmd += " {} {}".format(option, value)
        cmd += "'"

        return cmd

    def parse_set(self, command, output, *argv, **kwarg):
        """"""
        params = kwarg["params"]
        cmd = "vtysh {} ".format(command)
        ############# Implement me ################

        return cmd
