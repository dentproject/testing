import json

from dent_os_testbed.lib.ip.linux.linux_ip_link import LinuxIpLink


class LinuxIpLinkImpl(LinuxIpLink):
    def format_add(self, command, *argv, **kwarg):

        """
        ip link add [ link DEVICE ] [ name ] NAME [ ageing_time AGEING_TIME ] [ txqueuelen PACKETS ] [ address LLADDR ]
                    [ broadcast LLADDR ] [ mtu MTU ] [ index IDX ] [ numtxqueues QUEUE_COUNT ]
                    [ numrxqueues QUEUE_COUNT ] type TYPE [ ARGS ]
        TYPE := [ bridge | bond ] can | dummy | hsr | ifb | ipoib | macvlan | macvtap | vcan |
                  veth | vlan | vxlan | ip6tnl | ipip | sit | gre | gretap | ip6gre | ip6gretap ]

        """
        params = kwarg["params"]
        cmd = "ip link {} ".format(command)
        # custom code here
        if "device" in params:
            cmd += "{} ".format((params["device"]))
        if "name" in params:
            cmd += "name {} ".format((params["name"]))
        if "txqueuelen" in params:
            cmd += "txqueuelen {} ".format((params["txqueuelen"]))
        if "address" in params:
            cmd += "address {} ".format((params["address"]))
        if "broadcast" in params:
            cmd += "broadcast {} ".format((params["broadcast"]))
        if "mtu" in params:
            cmd += "mtu {} ".format((params["mtu"]))
        if "index" in params:
            cmd += "index {} ".format((params["index"]))
        if "numtxqueues" in params:
            cmd += "numtxqueues {} ".format((params["numtxqueues"]))
        if "numrxqueues" in params:
            cmd += "numrxqueues {} ".format((params["numrxqueues"]))
        if "type" in params:
            cmd += "type {} ".format((params["type"]))
        if "ageing_time" in params:
            cmd += "ageing_time {} ".format((params["ageing_time"]))
        if "vlan_filtering" in params:
            cmd += "vlan_filtering {} ".format((params["vlan_filtering"]))
        return cmd

    def format_delete(self, command, *argv, **kwarg):

        """
        ip link delete DEVICE type TYPE [ ARGS ]
        TYPE := [ bridge | bond ] can | dummy | hsr | ifb | ipoib | macvlan | macvtap | vcan |
                  veth | vlan | vxlan | ip6tnl | ipip | sit | gre | gretap | ip6gre | ip6gretap ]

        """
        params = kwarg["params"]
        cmd = "ip link {} ".format(command)
        # custom code here
        if "device" in params:
            cmd += "{} ".format((params["device"]))
        if "type" in params:
            cmd += "type {} ".format((params["type"]))
        return cmd

    def format_set(self, command, *argv, **kwarg):

        """
        ip link set { DEVICE | group GROUP } { up | down | arp { on | off } | promisc { on | off } |
                      allmulticast { on | off } | dynamic { on | off } | multicast { on | off } |
                      txqueuelen PACKETS | name NEWNAME | address LLADDR | broadcast LLADDR |
                      mtu MTU | netns PID | netns NETNSNAME | alias NAME | vf NUM [ mac LLADDR ]
                      [ vlan VLANID [ qos VLAN-QOS ] ] [ rate TXRATE ] [ max_tx_rate TXRATE ]
                      [ min_tx_rate TXRATE ] [ spoofchk { on | off } ] [ state { auto | enable | disable} ] |
                      [{master DEVICE | nomaster }]

        """
        params = kwarg["params"]
        cmd = "ip link {} ".format(command)
        # custom code here
        if "device" in params:
            cmd += "{} ".format((params["device"]))
        if "group" in params:
            cmd += "group {} ".format((params["group"]))
        if "ageing_time" in params:
            cmd += "ageing_time {} ".format((params["ageing_time"]))
        if "operstate" in params:
            cmd += "{} ".format((params["operstate"]))
        if "arp" in params:
            cmd += "arp {} ".format((params["arp"]))
        if "promiscuity" in params:
            cmd += "promisc {} ".format((params["promiscuity"]))
        if "allmulticast" in params:
            cmd += "allmulticast {} ".format((params["allmulticast"]))
        if "dynamic" in params:
            cmd += "dynamic {} ".format((params["dynamic"]))
        if "multicast" in params:
            cmd += "multicast {} ".format((params["multicast"]))
        if "txqueuelen" in params:
            cmd += "txqueuelen {} ".format((params["txqueuelen"]))
        if "name" in params:
            cmd += "name {} ".format((params["name"]))
        if "address" in params:
            cmd += "address {} ".format((params["address"]))
        if "broadcast" in params:
            cmd += "broadcast {} ".format((params["broadcast"]))
        if "mtu" in params:
            cmd += "mtu {} ".format((params["mtu"]))
        if "netns" in params:
            cmd += "netns {} ".format((params["netns"]))
        if "alias" in params:
            cmd += "alias {} ".format((params["alias"]))
        if "vf" in params:
            cmd += "vf {} ".format((params["vf"]))
        if "mac" in params:
            cmd += "mac {} ".format((params["mac"]))
        if "vlan" in params:
            cmd += "vlan {} ".format((params["vlan"]))
            if "qos" in params:
                cmd += "qos {} ".format((params["qos"]))
        if "rate" in params:
            cmd += "rate {} ".format((params["rate"]))
        if "max_tx_rate" in params:
            cmd += "max_tx_rate {} ".format((params["max_tx_rate"]))
        if "min_tx_rate" in params:
            cmd += "min_tx_rate {} ".format((params["min_tx_rate"]))
        if "spoofchk" in params:
            cmd += "spoofchk {} ".format((params["spoofchk"]))
        if "state" in params:
            cmd += "state {} ".format((params["state"]))
        if "master" in params:
            cmd += "master {} ".format((params["master"]))
        if "nomaster" in params:
            cmd += "nomaster"
        return cmd

    def format_show(self, command, *argv, **kwarg):

        """
        ip link show [ DEVICE | group GROUP ]
        """
        params = kwarg["params"]
        if params.get("dut_discovery", False):
            params["cmd_options"] = "-j -d"
        cmd = "ip {} link {} ".format(params.get("cmd_options", ""), command)
        # custom code here
        if "device" in params:
            cmd += "{} ".format((params["device"]))
        if "group" in params:
            cmd += "group {} ".format((params["group"]))

        return cmd

    def parse_show(self, command, output, *argv, **kwarg):
        return json.loads(output)
