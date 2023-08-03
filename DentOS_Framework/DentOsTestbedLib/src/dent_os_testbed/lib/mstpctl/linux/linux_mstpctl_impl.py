from dent_os_testbed.lib.mstpctl.linux.linux_mstpctl import LinuxMstpctl
import json


class LinuxMstpctlImpl(LinuxMstpctl):
    """
        MSTPCTL is used for configuring STP parameters on bridges which have user-space
        STP enabled. Currently, STP is disabled by default on the bridge. To
        enable user-space STP, configure "brctl stp <bridge> on" or
        "ip link set <bridge> type bridge stp_state 1" while ensuring that
        /sbin/bridge-stp kernel helper script will return success (0) for
        this operation.

    """

    def format_set(self, command, *argv, **kwarg):
        params = kwarg['params']
        cmd = 'mstpctl {} {}{} '.format(params.get('options', ''), command, params['parameter'])
        for key in ['bridge', 'port', 'revision', 'name', 'ageing_time', 'max_age', 'fwd_delay',
                    'max_hops', 'hello_time', 'version', 'mstid', 'priority', 'tx_hold_count', 'cost']:
            if key in params.keys():
                cmd += f'{params[key]} '
        if 'enable' in params:
            if type(params['enable']) is bool:
                cmd += 'yes ' if params['enable'] else 'no '
            else:
                cmd += '{} '.format(params['enable'])
        return cmd

    def format_show(self, command, *argv, **kwarg):
        params = kwarg['params']
        cmd = 'mstpctl {} {}{} '.format(params.get('options', ''), command, params['parameter'])
        if 'bridge' in params:
            cmd += '{} '.format(params['bridge'])
        if 'port' in params:
            cmd += '{} '.format(params['port'])
        if 'mstid' in params:
            cmd += '{} '.format(params['mstid'])
        return cmd

    def parse_show(self, command, output, *argv, **kwarg):
        return json.loads(output)

    def format_remove(self, command, *argv, **kwarg):
        """
        Remove bridges from the mstpd's list
        """
        params = kwarg['params']
        cmd = 'mstpctl {} {}{} '.format(params.get('options', ''), command, params['parameter'])
        if 'bridge' in params:
            cmd += '{} '.format(params['bridge'])
        if 'mstid' in params:
            cmd += '{} '.format(params['mstid'])
        return cmd

    def format_add(self, command, *argv, **kwarg):
        """
        Add bridges to the mstpd's list
        """
        params = kwarg['params']
        cmd = 'mstpctl addbridge '
        if 'bridge' in params:
            cmd += '{} '.format(params['bridge'])
        return cmd
