# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# generated using file ./gen/model/linux/platform/onlp/onie.yaml
#
# DONOT EDIT - generated by diligent bots

from dent_os_testbed.lib.test_lib_object import TestLibObject


class LinuxOnie(TestLibObject):
    """
        To run onie-select
    """

    def format_select(self, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_select(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_command(self, command, *argv, **kwarg):
        if command in ['select']:
            return self.format_select(command, *argv, **kwarg)

        raise NameError('Cannot find command '+command)

    def parse_output(self, command, output, *argv, **kwarg):
        if command in ['select']:
            return self.parse_select(command, output, *argv, **kwarg)

        raise NameError('Cannot find command '+command)
