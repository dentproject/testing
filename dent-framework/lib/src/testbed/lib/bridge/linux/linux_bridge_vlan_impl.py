from testbed.lib.bridge.linux.linux_bridge_vlan import LinuxBridgeVlan


class LinuxBridgeVlanImpl(LinuxBridgeVlan):
    """
    The corresponding commands display vlan filter entries, add new entries, and delete old ones.

    """

    def format_update(self, command, *argv, **kwarg):
        """
        bridge vlan { add | del } dev DEV vid VID [ tunnel_info TUNNEL_ID ] [ pvid ] [ untagged ] [ self ] [ master ]

        """
        ############# Implement me ################
        params = kwarg["params"]
        cmd = "bridge {} vlan {} ".format(params.get("cmd_options", ""), command)
        # custom code here
        if "device" in params:
            cmd += "dev {} ".format((params["device"]))
        if "vid" in params:
            cmd += "vid {} ".format((params["vid"]))
        if "pvid" in params:
            cmd += "pvid {} ".format((params["pvid"]))
        if "untagged" in params and params["untagged"]:
            cmd += "untagged "
        if "self" in params and params["self"]:
            cmd += "self "
        if "master" in params and params["master"]:
            cmd += "master "
        return cmd

    def format_show(self, command, *argv, **kwarg):
        """"""
        ############# Implement me ################
        params = kwarg["params"]
        if params.get("dut_discovery", False):
            params["cmd_options"] = "-j"
        cmd = "bridge {} vlan {} ".format(params.get("cmd_options", ""), command)
        # custom code here
        if "device" in params:
            cmd += "dev {} ".format((params["device"]))

        return cmd

    def parse_show(self, command, output, *argv, **kwarg):
        return json.loads(output)
