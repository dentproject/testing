# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# generated using file ./gen/model/linux/system/os/cpu.yaml
#
# DONOT EDIT - generated by diligent bots

from dent_os_testbed.lib.test_lib_object import TestLibObject


class LinuxCpuUsage(TestLibObject):
    """
        /usr/bin/mpstat
        dev-dsk-muchetan-2b-1f031d76 % mpstat
          04:47:43 AM  CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest   %idle
          04:47:43 AM  all    0.49    0.04    0.07    0.02    0.00    0.00    0.00    0.00   99.37

    """
    def format_show(self, command, *argv, **kwarg):
        raise NotImplementedError

    def parse_show(self, command, output, *argv, **kwarg):
        raise NotImplementedError

    def format_command(self, command, *argv, **kwarg):
        if command in ['show']:
            return self.format_show(command, *argv, **kwarg)

        raise NameError('Cannot find command '+command)

    def parse_output(self, command, output, *argv, **kwarg):
        if command in ['show']:
            return self.parse_show(command, output, *argv, **kwarg)

        raise NameError('Cannot find command '+command)
