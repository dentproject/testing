# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# generated using file ./gen/model/linux/network/bridge/bridge.yaml
#
# DONOT EDIT - generated by diligent bots

from dent_os_testbed.lib.test_lib_object import TestLibObject
class LinuxBridgeMonitor(TestLibObject):
    """

    """
    def format_monitor(self, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_monitor(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_command(self, command, *argv, **kwarg):
        if command in ['monitor']:
            return self.format_monitor(command, *argv, **kwarg)


        raise NameError("Cannot find command "+command)

    def parse_output(self, command, output, *argv, **kwarg):
        if command in ['monitor']:
            return self.parse_monitor(command, output, *argv, **kwarg)


        raise NameError("Cannot find command "+command)
