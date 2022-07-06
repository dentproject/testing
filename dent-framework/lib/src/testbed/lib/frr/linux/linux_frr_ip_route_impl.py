from testbed.lib.frr.linux.linux_frr_ip_route import LinuxFrrIpRoute


class LinuxFrrIpRouteImpl(LinuxFrrIpRoute):
    """
    vtysh

    """

    def format_show(self, command, *argv, **kwarg):
        """"""
        params = kwarg["params"]
        cmd = "vtysh -c '{} ip route ".format(command)

        if "network" in params:
            cmd += "{} ".format(params.get("network", ""))
        if "mask" in params:
            cmd += "{} ".format(params.get("mask", ""))
        cmd += params.get("options", "")
        cmd += "'"
        return cmd

    def parse_show(self, command, output, *argv, **kwarg):
        """"""
        params = kwarg["params"]
        cmd = "vtysh {} ".format(command)
        ############# Implement me ################

        return cmd

    def format_add(self, command, *argv, **kwarg):
        """"""
        params = kwarg["params"]
        cmd = "vtysh -c 'config t' -c 'ip route "

        if "network" in params:
            cmd += "{} ".format(params.get("network", ""))
        if "mask" in params:
            cmd += "{} ".format(params.get("mask", ""))
        if "gateway" in params:
            cmd += "{} ".format(params.get("gateway", ""))
        if "distance" in params:
            cmd += "{}".format(params.get("distance", ""))
        cmd += "'"
        cmd += " -c 'end'"

        return cmd

    def parse_add(self, command, output, *argv, **kwarg):
        """"""
        params = kwarg["params"]
        cmd = "vtysh {} ".format(command)
        ############# Implement me ################

        return cmd
