# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# generated using file ./gen/model/linux/network/interfaces/interface.yaml
#
# DONOT EDIT - generated by diligent bots

from dent_os_testbed.lib.test_lib_object import TestLibObject


class LinuxInterface(TestLibObject):
    """
        ifupdown - network interface management commands
         ifup - bring a network interface up
         ifdown - take a network interface down
        ifquery - query network interface configuration
        ifreload - reload network interface configuration

    """

    def format_up_down(self, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_up_down(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_query(self, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_query(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_reload(self, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_reload(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_command(self, command, *argv, **kwarg):
        if command in ['up', 'down']:
            return self.format_up_down(command, *argv, **kwarg)

        if command in ['query']:
            return self.format_query(command, *argv, **kwarg)

        if command in ['reload']:
            return self.format_reload(command, *argv, **kwarg)

        raise NameError('Cannot find command '+command)

    def parse_output(self, command, output, *argv, **kwarg):
        if command in ['up', 'down']:
            return self.parse_up_down(command, output, *argv, **kwarg)

        if command in ['query']:
            return self.parse_query(command, output, *argv, **kwarg)

        if command in ['reload']:
            return self.parse_reload(command, output, *argv, **kwarg)

        raise NameError('Cannot find command '+command)
