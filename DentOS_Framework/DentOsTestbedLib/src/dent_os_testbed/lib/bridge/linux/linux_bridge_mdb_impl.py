import json

from dent_os_testbed.lib.bridge.linux.linux_bridge_mdb import LinuxBridgeMdb


class LinuxBridgeMdbImpl(LinuxBridgeMdb):
    """
    The corresponding commands display mdb entries, add new entries, and delete old ones.

    """

    def format_update(self, command, *argv, **kwarg):
        """
        bridge mdb { add | del } dev DEV port PORT grp GROUP [ permanent | temp ] [ vid VID ]

        """
        params = kwarg['params']
        cmd = 'bridge mdb {} '.format(command)
        ############# Implement me ################
        mdb_entry_type = params.get('permanent', 'temp')
        if 'dev' in params:
            cmd += 'dev {} '.format(params['dev'])
        if 'port' in params:
            cmd += 'port {} '.format(params['port'])
        if 'group' in params:
            cmd += 'grp {} {} '.format(params['group'], mdb_entry_type)
        if 'vid' in params:
            cmd += 'vid {} '.format(params['vid'])

        return cmd

    def format_show(self, command, *argv, **kwarg):
        """
        bridge mdb show [ dev DEV ]

        """
        params = kwarg['params']
        cmd = 'bridge {} mdb {} '.format(params.get('options', ''), command)
        ############# Implement me ################

        return cmd

    def parse_show(self, command, output, *argv, **kwarg):
        return json.loads(output)
