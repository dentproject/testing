import json

from dent_os_testbed.lib.devlink.linux.devlink_port import DevlinkPort


class DevlinkPortImpl(DevlinkPort):
    """
        devlink [ OPTIONS ] {dev|port|monitor|sb|resource|region|health|trap } {COMMAND | help }
        devlink [ -force ] -batch filename

    """

    def format_set(self, command, *argv, **kwarg):
        """
        devlink port param set DEV/PORT_INDEX name PARAMETER value VALUE
                cmode { runtime | driverinit | permanent }

        """
        params = kwarg['params']
        cmd = 'devlink port param {} '.format(command)
        # TODO: Implement me
        if 'dev' in params:
            cmd += '{} '.format(params['dev'])
        if 'name' in params:
            cmd += 'name {} '.format(params['name'])
        if 'value' in params:
            cmd += 'value {} '.format(params['value'])
        if 'cmode' in params:
            cmd += 'cmode {} '.format(params['cmode'])

        return cmd

    def parse_set(self, command, output, *argv, **kwarg):
        """
        devlink port param set DEV/PORT_INDEX name PARAMETER value VALUE
                cmode { runtime | driverinit | permanent }

        """
        cmd = 'devlink port param {} '.format(command)
        # TODO: Implement me

        return cmd

    def format_show(self, command, *argv, **kwarg):
        """
        devlink port param show [ DEV/PORT_INDEX name PARAMETER ]
        """
        params = kwarg['params']
        cmd = 'devlink {} port param {} '.format(params.get('options', ''), command)
        # TODO: Implement me
        if 'dev' in params:
            cmd += '{} '.format(params['dev'])
        if 'name' in params:
            cmd += 'name {} '.format(params['name'])
        return cmd

    def parse_show(self, command, output, *argv, **kwarg):
        """
        devlink port param show [ DEV/PORT_INDEX name PARAMETER ]
        """
        return json.loads(output)
