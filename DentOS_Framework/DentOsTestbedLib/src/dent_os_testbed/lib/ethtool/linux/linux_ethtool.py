# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# generated using file ./gen/model/linux/network/ethtool/ethtool.yaml
#
# DONOT EDIT - generated by diligent bots

from dent_os_testbed.lib.test_lib_object import TestLibObject
class LinuxEthtool(TestLibObject):
    """
        ethtool - query or control network driver and hardware settings

    """
    def format_show(self, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_show(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_set(self, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_set(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_change(self, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_change(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_init(self, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_init(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_test(self, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_test(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_flash(self, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_flash(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_config(self, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_config(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_reset(self, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_reset(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_command(self, command, *argv, **kwarg):
        if command in ['show']:
            return self.format_show(command, *argv, **kwarg)

        if command in ['set']:
            return self.format_set(command, *argv, **kwarg)

        if command in ['change']:
            return self.format_change(command, *argv, **kwarg)

        if command in ['init']:
            return self.format_init(command, *argv, **kwarg)

        if command in ['test']:
            return self.format_test(command, *argv, **kwarg)

        if command in ['flash']:
            return self.format_flash(command, *argv, **kwarg)

        if command in ['config']:
            return self.format_config(command, *argv, **kwarg)

        if command in ['reset']:
            return self.format_reset(command, *argv, **kwarg)


        raise NameError("Cannot find command "+command)

    def parse_output(self, command, output, *argv, **kwarg):
        if command in ['show']:
            return self.parse_show(command, output, *argv, **kwarg)

        if command in ['set']:
            return self.parse_set(command, output, *argv, **kwarg)

        if command in ['change']:
            return self.parse_change(command, output, *argv, **kwarg)

        if command in ['init']:
            return self.parse_init(command, output, *argv, **kwarg)

        if command in ['test']:
            return self.parse_test(command, output, *argv, **kwarg)

        if command in ['flash']:
            return self.parse_flash(command, output, *argv, **kwarg)

        if command in ['config']:
            return self.parse_config(command, output, *argv, **kwarg)

        if command in ['reset']:
            return self.parse_reset(command, output, *argv, **kwarg)


        raise NameError("Cannot find command "+command)
