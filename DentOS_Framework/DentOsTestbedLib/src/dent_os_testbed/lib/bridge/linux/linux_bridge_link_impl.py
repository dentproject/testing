import json

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
        params = kwarg['params']
        cmd = 'bridge {} link {} '.format(params.get('options', ''), command)

        cmd += 'dev {} '.format(params.get('device', ''))

        for key in ['cost', 'priority', 'state', 'mcast_router', 'hwmode', 'backup_port']:
            if key in params:
                cmd += f'{key} {params[key]} '

        for key in ['guard', 'hairpin', 'fastleave', 'root_block', 'learning', 'learning_sync',
                    'flood', 'mcast_flood', 'bcast_flood', 'mcast_to_unicast', 'neigh_suppress',
                    'vlan_tunnel', 'isolated', 'locked']:
            if type(params.get(key)) is bool:
                cmd += f'{key} {"on" if params[key] else "off"} '

        for key in ['nobackup_port', 'self', 'master']:
            if params.get(key):
                cmd += f'{key} '

        return cmd

    def format_show(self, command, *argv, **kwarg):
        """
        bridge link [ show ] [ dev DEV ]

        """
        params = kwarg['params']
        cmd = 'bridge {} link {} '.format(params.get('options', ''), command)

        if 'device' in params:
            cmd += f'dev {params["device"]} '

        return cmd

    def parse_show(self, command, output, *argv, **kwarg):
        return json.loads(output)
