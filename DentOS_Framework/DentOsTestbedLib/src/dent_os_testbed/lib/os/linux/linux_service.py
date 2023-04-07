# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# generated using file ./gen/model/linux/system/os/service.yaml
#
# DONOT EDIT - generated by diligent bots

from dent_os_testbed.lib.test_lib_object import TestLibObject


class LinuxService(TestLibObject):
    """
        Service details by runnin systemctl list-units --type=service
    """
    def format_show(self, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_show(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_operation(self, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_operation(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_command(self, command, *argv, **kwarg):
        if command in ['show']:
            return self.format_show(command, *argv, **kwarg)

        if command in ['start', 'stop', 'restart', 'enable', 'disable']:
            return self.format_operation(command, *argv, **kwarg)

        raise NameError('Cannot find command '+command)

    def parse_output(self, command, output, *argv, **kwarg):
        if command in ['show']:
            return self.parse_show(command, output, *argv, **kwarg)

        if command in ['start', 'stop', 'restart', 'enable', 'disable']:
            return self.parse_operation(command, output, *argv, **kwarg)

        raise NameError('Cannot find command '+command)
