from dent_os_testbed.lib.bridge.linux.linux_bridge_link import LinuxBridgeLink


class LinuxBridgeLinkImpl(LinuxBridgeLink):
    """
    bridge link set dev DEV [ cost COST ] [ priority PRIO ] [ state STATE ] [ guard { on | off } ]
      [ hairpin { on | off } ] [ fastleave { on | off } ] [ root_block { on | off } ]
      [ learning { on | off } ] [ learning_sync { on | off } ] [ flood { on | off } ]
      [ hwmode { vepa | veb } ] [ mcast_flood { on | off } ] [ mcast_to_unicast { on | off } ]
      [ neigh_suppress { on | off } ] [ vlan_tunnel { on | off } ] [ isolated { on | off } ]
      [ backup_port DEVICE ] [ nobackup_port ] [ self ] [ master ]
    bridge link [ show ] [ dev DEV ]

    """

    def format_set(self, command, *argv, **kwarg):
        """
        bridge link set dev DEV [ cost COST ] [ priority PRIO ] [ state STATE ] [ guard { on | off } ]
          [ hairpin { on | off } ] [ fastleave { on | off } ] [ root_block { on | off } ]
          [ learning { on | off } ] [ learning_sync { on | off } ] [ flood { on | off } ]
          [ hwmode { vepa | veb } ] [ mcast_flood { on | off } ] [ mcast_to_unicast { on | off } ]
          [ neigh_suppress { on | off } ] [ vlan_tunnel { on | off } ] [ isolated { on | off } ]
          [ backup_port DEVICE ] [ nobackup_port ] [ self ] [ master ]

        """
        params = kwarg["params"]
        cmd = "bridge link {} ".format(command)
        ############# Implement me ################
        cmd += "dev {} ".format(params.get("device", ""))
        if "isolated" in params:
            cmd += "isolated {} ".format("on" if params["isolated"] else "off")
        if "learning" in params:
            cmd += "learning {} ".format("on" if params["learning"] else "off")
        if "flood" in params:
            cmd += "flood {} ".format("on" if params["flood"] else "off")

        return cmd

    def format_show(self, command, *argv, **kwarg):
        """
        bridge link [ show ] [ dev DEV ]

        """
        params = kwarg["params"]
        cmd = "bridge link {} ".format(command)
        ############# Implement me ################

        return cmd
