import json

from dent_os_testbed.lib.ip.linux.linux_ip_address import LinuxIpAddress


class LinuxIpAddressImpl(LinuxIpAddress):
    def format_modify(self, command, *argv, **kwarg):

        """
        Usage: ip address {add|change|replace} IFADDR dev IFNAME [ LIFETIME ]
                                                              [ CONFFLAG-LIST ]
        IFADDR := PREFIX | ADDR peer PREFIX
                  [ broadcast ADDR ] [ anycast ADDR ]
                  [ label IFNAME ] [ scope SCOPE-ID ]
        SCOPE-ID := [ host | link | global | NUMBER ]
        CONFFLAG-LIST := [ CONFFLAG-LIST ] CONFFLAG
        CONFFLAG  := [ home | nodad | mngtmpaddr | noprefixroute | autojoin ]
        LIFETIME := [ valid_lft LFT ] [ preferred_lft LFT ]
        LFT := forever | SECONDS

        """
        params = kwarg["params"]
        cmd = "ip address {} ".format(command)
        # custom code here
        if "prefix" in params:
            cmd += "{} ".format(params["prefix"])
        if "peer" in params:
            cmd += "peer {} ".format(params["peer"])
        if "broadcast" in params:
            cmd += "broadcast {} ".format(params["broadcast"])
        if "anycast" in params:
            cmd += "anycast {} ".format(params["anycast"])
        if "label" in params:
            cmd += "label {} ".format(params["label"])
        if "scope" in params:
            cmd += "scope {} ".format(params["scope"])
        if "dev" in params:
            cmd += "dev {} ".format(params["dev"])
        if "valid_lft" in params:
            cmd += "valid_lft {} ".format(params["valid_lft"])
        if "preferred_lft" in params:
            cmd += "preferred_lft {} ".format(params["preferred_lft"])
        if "confflag_list" in params:
            for confflag in params["confflag_list"]:
                cmd += "{} ".format(confflag)
        return cmd

    def format_delete(self, command, *argv, **kwarg):

        """
        ip address del IFADDR dev IFNAME [mngtmpaddr]
        IFADDR := PREFIX | ADDR peer PREFIX
               [ broadcast ADDR ] [ anycast ADDR ]
               [ label IFNAME ] [ scope SCOPE-ID ]
        SCOPE-ID := [ host | link | global | NUMBER ]

        """
        params = kwarg["params"]
        cmd = "ip address {} ".format(command)
        # custom code here
        if "prefix" in params:
            cmd += "{} ".format(params["prefix"])
        if "dev" in params:
            cmd += "dev {} ".format(params["dev"])
        if "peer" in params:
            cmd += "peer {} ".format(params["peer"])
        if "broadcast" in params:
            cmd += "broadcast {} ".format(params["broadcast"])
        if "anycast" in params:
            cmd += "anycast {} ".format(params["anycast"])
        if "label" in params:
            cmd += "label {} ".format(params["label"])
        if "scope" in params:
            cmd += "scope {} ".format(params["scope"])

        return cmd

    def format_save(self, command, *argv, **kwarg):

        """
        ip address {save|flush} [ dev IFNAME ] [ scope SCOPE-ID ]
                                 [ to PREFIX ] [ FLAG-LIST ] [ label LABEL ] [up]
        SCOPE-ID := [ host | link | global | NUMBER ]
        FLAG-LIST := [ FLAG-LIST ] FLAG
        FLAG  := [ permanent | dynamic | secondary | primary |
                    [-]tentative | [-]deprecated | [-]dadfailed | temporary |
                    CONFFLAG-LIST ]
        CONFFLAG-LIST := [ CONFFLAG-LIST ] CONFFLAG
        CONFFLAG  := [ home | nodad | mngtmpaddr | noprefixroute | autojoin ]

        """
        params = kwarg["params"]
        cmd = "ip address {} ".format(command)
        # custom code here
        if "dev" in params:
            cmd += "{} ".format(params["dev"])
        if "scope" in params:
            cmd += "scope {} ".format(params["scope"])
        if "prefix" in params:
            cmd += "to {} ".format(params["prefix"])
        if "flag_list" in params:
            for flag in params["flag_list"]:
                cmd += "{} ".format(flag)
        if "confflag_list" in params:
            for confflag in params["confflag_list"]:
                cmd += "{} ".format(confflag)
        return cmd

    def format_show(self, command, *argv, **kwarg):

        """
        ip address [ show [ dev IFNAME ] [ scope SCOPE-ID ] [ master DEVICE ]
                              [ type TYPE ] [ to PREFIX ] [ FLAG-LIST ]
                              [ label LABEL ] [up] [ vrf NAME ] ]
        FLAG-LIST := [ FLAG-LIST ] FLAG
        FLAG  := [ permanent | dynamic | secondary | primary |
                   [-]tentative | [-]deprecated | [-]dadfailed | temporary |
                   CONFFLAG-LIST ]
        CONFFLAG-LIST := [ CONFFLAG-LIST ] CONFFLAG
        CONFFLAG  := [ home | nodad | mngtmpaddr | noprefixroute | autojoin ]
        TYPE := { vlan | veth | vcan | dummy | ifb | macvlan | macvtap |
                  bridge | bond | ipoib | ip6tnl | ipip | sit | vxlan | lowpan |
                  gre | gretap | ip6gre | ip6gretap | vti | nlmon | can |
                  bond_slave | ipvlan | geneve | bridge_slave | vrf | hsr | macsec }
                 ip [ OPTIONS ] address { COMMAND | help }

        """
        params = kwarg["params"]
        if params.get("dut_discovery", False):
            params["cmd_options"] = "-j -d"
        cmd = "ip {} address {} ".format(params.get("cmd_options", ""), command)
        if "dev" in params:
            cmd += "{} ".format(params["dev"])
        if "scope" in params:
            cmd += "scope {} ".format(params["scope"])
        if "master" in params:
            cmd += "master {} ".format(params["master"])
        if "type" in params:
            cmd += "type {} ".format(params["type"])
        if "prefix" in params:
            cmd += "to {} ".format(params["prefix"])
        if "flag_list" in params:
            for flag in params["flag_list"]:
                cmd += "{} ".format(flag)
        if "confflag_list" in params:
            for confflag in params["confflag_list"]:
                cmd += "{} ".format(confflag)
        if "label" in params:
            cmd += "label {} ".format(params["label"])
        if "vrf" in params:
            cmd += "vrf {} ".format(params["vrf"])
        return cmd

    def format_restore(self, command, *argv, **kwarg):

        """
        Restore the config
        """
        params = kwarg["params"]
        cmd = "ip address {} ".format(command)
        # custom code here

        return cmd

    def parse_show(self, command, output, *argv, **kwarg):
        return json.loads(output)
