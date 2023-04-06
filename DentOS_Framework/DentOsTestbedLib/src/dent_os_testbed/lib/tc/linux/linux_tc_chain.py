# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# generated using file ./gen/model/linux/network/tc/tc.yaml
#
# DONOT EDIT - generated by diligent bots

from dent_os_testbed.lib.test_lib_object import TestLibObject
class LinuxTcChain(TestLibObject):
    """

    """
    def format_modify(self, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_modify(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_show(self, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_show(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_command(self, command, *argv, **kwarg):
        if command in ['add', 'delete', 'get']:
            return self.format_modify(command, *argv, **kwarg)

        if command in ['show']:
            return self.format_show(command, *argv, **kwarg)


        raise NameError("Cannot find command "+command)

    def parse_output(self, command, output, *argv, **kwarg):
        if command in ['add', 'delete', 'get']:
            return self.parse_modify(command, output, *argv, **kwarg)

        if command in ['show']:
            return self.parse_show(command, output, *argv, **kwarg)


        raise NameError("Cannot find command "+command)
