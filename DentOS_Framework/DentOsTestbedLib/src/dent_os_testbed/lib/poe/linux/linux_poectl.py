# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# generated using file ./gen/model/linux/platform/poe/poectl.yaml
#
# DONOT EDIT - generated by diligent bots

from dent_os_testbed.lib.test_lib_object import TestLibObject


class LinuxPoectl(TestLibObject):
    """
    POE details by running poectl
    """

    def format_show(self, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_show(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_modify(self, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_modify(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_persist(self, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_persist(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_command(self, command, *argv, **kwarg):
        if command in ["show"]:
            return self.format_show(command, *argv, **kwarg)

        if command in ["enable", "disable"]:
            return self.format_modify(command, *argv, **kwarg)

        if command in ["save", "restore"]:
            return self.format_persist(command, *argv, **kwarg)

        raise NameError("Cannot find command " + command)

    def parse_output(self, command, output, *argv, **kwarg):
        if command in ["show"]:
            return self.parse_show(command, output, *argv, **kwarg)

        if command in ["enable", "disable"]:
            return self.parse_modify(command, output, *argv, **kwarg)

        if command in ["save", "restore"]:
            return self.parse_persist(command, output, *argv, **kwarg)

        raise NameError("Cannot find command " + command)