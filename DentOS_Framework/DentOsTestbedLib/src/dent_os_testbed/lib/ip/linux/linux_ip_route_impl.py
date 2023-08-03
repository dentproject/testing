import json

from dent_os_testbed.lib.ip.linux.linux_ip_route import LinuxIpRoute


class LinuxIpRouteImpl(LinuxIpRoute):
    def format_update(self, command, *argv, **kwarg):
        """
        Add/Delete/Change/Append/Replace route using the below command
        ip route { add | del | change | append | replace } ROUTE
        ROUTE := NODE_SPEC [ INFO_SPEC ]
        NODE_SPEC := [ TYPE ] PREFIX [ tos TOS ]
                     [ table TABLE_ID ] [ proto RTPROTO ]
                     [ scope SCOPE ] [ metric METRIC ]
        INFO_SPEC := NH OPTIONS FLAGS [ nexthop NH ]...
        NH := [ encap ENCAPTYPE ENCAPHDR ] [ via [ FAMILY ] ADDRESS ]
                   [ dev STRING ] [ weight NUMBER ] NHFLAGS
        FAMILY := [ inet | inet6 | ipx | dnet | mpls | bridge | link ]
        OPTIONS := FLAGS [ mtu NUMBER ] [ advmss NUMBER ] [ as [ to ] ADDRESS ]
                   [ rtt TIME ] [ rttvar TIME ] [ reordering NUMBER ]
                   [ window NUMBER ] [ cwnd NUMBER ] [ initcwnd NUMBER ]
                   [ ssthresh NUMBER ] [ realms REALM ] [ src ADDRESS ]
                   [ rto_min TIME ] [ hoplimit NUMBER ] [ initrwnd NUMBER ]
                   [ features FEATURES ] [ quickack BOOL ] [ congctl NAME ]
                   [ pref PREF ] [ expires TIME ]
        TYPE := { unicast | local | broadcast | multicast | throw |
                  unreachable | prohibit | blackhole | nat }
        TABLE_ID := [ local | main | default | all | NUMBER ]
        SCOPE := [ host | link | global | NUMBER ]
        NHFLAGS := [ onlink | pervasive ]
        RTPROTO := [ kernel | boot | static | NUMBER ]
        PREF := [ low | medium | high ]
        TIME := NUMBER[s|ms]
        BOOL := [1|0]
        FEATURES := ecn
        ENCAPTYPE := [ mpls | ip | ip6 ]
        ENCAPHDR := [ MPLSLABEL ]
        """
        #        if "prefix" not in kwarg:
        #            raise NameError("Cannot find prefix " + command)
        params = kwarg['params']
        cmd = 'ip {} route {} '.format(params.get('cmd_options', ''), command)
        if 'table' in params:
            cmd += 'table {} '.format(params.get('table'))
        if 'vrf' in params:
            cmd += 'vrf {} '.format(params.get('vrf'))
        if 'type' in params:
            cmd += '{} '.format(params.get('type'))
        cmd += params.get('dst', '') + ' '
        if 'tos' in params:
            cmd += 'tos {} '.format(params.get('tos'))
        if 'protocol' in params:
            cmd += 'proto {} '.format(params.get('protocol'))
        if 'scope' in params:
            cmd += 'scope {} '.format(params.get('scope'))
        if 'metric' in params:
            cmd += 'metric {} '.format(params.get('metric'))
        if 'nexthop' in params:
            for nh in params.get('nexthop'):
                cmd += 'nexthop '
                if 'via' in nh:
                    cmd += 'via {} '.format(nh['via'])
                if 'dev' in nh:
                    cmd += 'dev {} '.format(nh['dev'])
                if 'weight' in nh:
                    cmd += 'weight {} '.format(nh['weight'])
        if 'via' in params:
            cmd += 'via {} '.format(params['via'])
        if 'dev' in params:
            cmd += 'dev {} '.format(params['dev'])
        if 'weight' in params:
            cmd += 'weight {} '.format(params['weight'])
        if 'nhflags' in params:
            cmd += '{} '.format(params.get('nhflags'))
        if 'mtu' in params:
            cmd += 'mtu {} '.format(params.get('mtu'))
        if 'advmss' in params:
            cmd += 'advmss {} '.format(params.get('advmss'))
        if 'rtt' in params:
            cmd += 'rtt {} '.format(params.get('rtt'))
        if 'rttvar' in params:
            cmd += 'rttvar {} '.format(params.get('rttvar'))
        if 'reordering' in params:
            cmd += 'reordering {} '.format(params.get('reordering'))
        if 'window' in params:
            cmd += 'window {} '.format(params.get('window'))
        if 'cwnd' in params:
            cmd += 'cwnd {} '.format(params.get('cwnd'))
        if 'ssthresh' in params:
            cmd += 'ssthresh {} '.format(params.get('ssthresh'))
        if 'realms' in params:
            cmd += 'realms {} '.format(params.get('realms'))
        if 'rto_min' in params:
            cmd += 'rto_min {} '.format(params.get('rto_min'))
        if 'initcwnd' in params:
            cmd += 'initcwnd {} '.format(params.get('initcwnd'))
        if 'initrwnd' in params:
            cmd += 'initrwnd {} '.format(params.get('initrwnd'))
        if 'quickack' in params:
            cmd += 'quickack {} '.format(params.get('quickack'))
        if 'congctl' in params:
            cmd += 'congctl {} '.format(params.get('congctl'))
        if 'features' in params:
            cmd += 'features {} '.format(params.get('features'))
        if 'src' in params:
            cmd += 'src {} '.format(params.get('src'))
        if 'hoplimit' in params:
            cmd += 'hoplimit {} '.format(params.get('hoplimit'))
        if 'pref' in params:
            cmd += 'pref {} '.format(params.get('pref'))
        if 'expires' in params:
            cmd += 'expires {} '.format(params.get('expires'))
        if 'table_id' in params:
            cmd += ' {} '.format(params.get('table_id'))
        return cmd

    def format_get(self, command, *argv, **kwarg):
        """
        Get the details of the route
        ip route get ADDRESS [ from ADDRESS iif STRING ]
                             [ oif STRING ] [ tos TOS ]
                             [ mark NUMBER ] [ vrf NAME ]

        """
        params = kwarg['params']
        cmd = 'ip route {} '.format(command)
        cmd += params.get('dst', '') + ' '
        if 'from' in params:
            cmd += 'from {} iif {} '.format(params.get('from'), params.get('iif'))
        if 'oif' in params:
            cmd += 'oif {} '.format(params.get('oif'))
        if 'tos' in params:
            cmd += 'tos {} '.format(params.get('tos'))
        return cmd

    def format_show(self, command, *argv, **kwarg):
        """
        Show/Flush the route
        ip route { list | flush } SELECTOR
        SELECTOR := [ root PREFIX ] [ match PREFIX ] [ exact PREFIX ]
                [ table TABLE_ID ] [ vrf NAME ] [ proto RTPROTO ]
                [ type TYPE ] [ scope SCOPE ]
        TYPE := [ unicast | local | broadcast | multicast | throw | unreachable | prohibit | blackhole | nat ]
        TABLE_ID := [ local| main | default | all | NUMBER ]
        SCOPE := [ host | link | global | NUMBER ]
        RTPROTO := [ kernel | boot | static | NUMBER ]

        """
        params = kwarg['params']
        if params.get('dut_discovery', False):
            params['cmd_options'] = '-j -d'
        cmd = 'ip {} route {} '.format(params.get('cmd_options', ''), command)
        cmd += params.get('dst', '') + ' '
        if 'dev' in params:
            cmd += 'dev {} '.format(params['dev'])
        if 'root' in params:
            cmd += 'root {} '.format(params.get('root'))
        if 'match' in params:
            cmd += 'match {} '.format(params.get('match'))
        if 'exact' in params:
            cmd += 'exact {} '.format(params.get('exact'))
        if 'table' in params:
            cmd += 'table {} '.format(params.get('table'))
        if 'proto' in params:
            cmd += 'proto {} '.format(params.get('proto'))
        if 'type' in params:
            cmd += 'type {} '.format(params.get('type'))
        if 'scope' in params:
            cmd += 'scope {} '.format(params.get('scope'))
        return cmd

    def format_save(self, command, *argv, **kwarg):
        """
        Save the route config
        ip route save SELECTOR
        SELECTOR := [ root PREFIX ] [ match PREFIX ] [ exact PREFIX ]
                [ table TABLE_ID ] [ vrf NAME ] [ proto RTPROTO ]
                [ type TYPE ] [ scope SCOPE ]
        TYPE := [ unicast | local | broadcast | multicast | throw | unreachable | prohibit | blackhole | nat ]
        TABLE_ID := [ local| main | default | all | NUMBER ]
        SCOPE := [ host | link | global | NUMBER ]
        RTPROTO := [ kernel | boot | static | NUMBER ]

        """
        params = kwarg['params']
        cmd = 'ip {} route {} '.format(params.get('cmd_options', ''), command)
        if 'root' in params:
            cmd += 'root {} '.format(params.get('root'))
        if 'match' in params:
            cmd += 'match {} '.format(params.get('match'))
        if 'exact' in params:
            cmd += 'exact {} '.format(params.get('exact'))
        if 'table' in params:
            cmd += 'table {} '.format(params.get('table'))
        if 'proto' in params:
            cmd += 'proto {} '.format(params.get('proto'))
        if 'type' in params:
            cmd += 'type {} '.format(params.get('type'))
        if 'scope' in params:
            cmd += 'scope {} '.format(params.get('scope'))
        return cmd

    def format_restore(self, command, *argv, **kwarg):
        """
        Restore the route
        ip route restore
        """
        params = kwarg['params']
        cmd = 'ip {} route {} '.format(params.get('cmd_options', ''), command)
        return cmd

    def parse_show(self, command, output, *argv, **kwarg):
        return json.loads(output)
