# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# generated using file ./gen/model/linux/network/ip/address.yaml
#
# DONOT EDIT - generated by diligent bots

from dent_os_testbed.lib.test_lib_object import TestLibObject
class LinuxIpAddress(TestLibObject):
    """
        ip [ OPTIONS ] address { COMMAND | help }
        - ip address { add | change | replace } IFADDR dev IFNAME [ LIFETIME ] [ CONFFLAG-LIST ]
        - ip address del IFADDR dev IFNAME [ mngtmpaddr ]
        - ip address { save | flush } [ dev IFNAME ] [ scope SCOPE-ID ] [ metric METRIC ] [ to PREFIX ]
          [ FLAG-LIST ] [ label PATTERN ] [ up ]
        - ip address [ show [ dev IFNAME ] [ scope SCOPE-ID ] [ to PREFIX ] [ FLAG-LIST ] [ label PATTERN
          ] [ master DEVICE ] [ type TYPE ] [ vrf NAME ] [ up ] ]
        - ip address { showdump | restore }
        IFADDR := PREFIX | ADDR peer PREFIX [ broadcast ADDR ] [ anycast ADDR ] [ label LABEL ] [ scope SCOPE-ID ]
        SCOPE-ID := [ host | link | global | NUMBER ]
        FLAG-LIST := [ FLAG-LIST ] FLAG
        FLAG := [ [-]permanent | [-]dynamic | [-]secondary | [-]primary | [-]tentative | [-]deprecated |
          [-]dadfailed | [-]temporary | CONFFLAG-LIST ]
        CONFFLAG-LIST := [ CONFFLAG-LIST ] CONFFLAG
        CONFFLAG := [ home | mngtmpaddr | nodad | noprefixroute | autojoin ]
        LIFETIME := [ valid_lft LFT ] [ preferred_lft LFT ]
        LFT := [ forever | SECONDS ]
        TYPE := [ bridge | bridge_slave | bond | bond_slave | can | dummy | hsr | ifb | ipoib | macvlan |
          macvtap | vcan | veth | vlan | vxlan | ip6tnl | ipip | sit | gre | gretap | erspan | ip6gre |
          ip6gretap | ip6erspan | vti | vrf | nlmon | ipvlan | lowpan | geneve | macsec ]

    """
    def format_modify(self, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_modify(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_delete(self, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_delete(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_save(self, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_save(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_show(self, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_show(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_restore(self, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_restore(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_command(self, command, *argv, **kwarg):
        if command in ['add', 'change', 'replace']:
            return self.format_modify(command, *argv, **kwarg)

        if command in ['delete']:
            return self.format_delete(command, *argv, **kwarg)

        if command in ['save', 'flush']:
            return self.format_save(command, *argv, **kwarg)

        if command in ['show']:
            return self.format_show(command, *argv, **kwarg)

        if command in ['showdump', 'restore']:
            return self.format_restore(command, *argv, **kwarg)


        raise NameError('Cannot find command '+command)

    def parse_output(self, command, output, *argv, **kwarg):
        if command in ['add', 'change', 'replace']:
            return self.parse_modify(command, output, *argv, **kwarg)

        if command in ['delete']:
            return self.parse_delete(command, output, *argv, **kwarg)

        if command in ['save', 'flush']:
            return self.parse_save(command, output, *argv, **kwarg)

        if command in ['show']:
            return self.parse_show(command, output, *argv, **kwarg)

        if command in ['showdump', 'restore']:
            return self.parse_restore(command, output, *argv, **kwarg)


        raise NameError('Cannot find command '+command)
