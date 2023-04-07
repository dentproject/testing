# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# generated using file ./gen/model/dent/system/os/cpu.yaml
#
# DONOT EDIT - generated by diligent bots

import pytest
from dent_os_testbed.lib.test_lib_object import TestLibObject
from dent_os_testbed.lib.os.linux.linux_cpu_usage_impl import LinuxCpuUsageImpl


class CpuUsage(TestLibObject):
    """
        /usr/bin/mpstat
        dev-dsk-muchetan-2b-1f031d76 % mpstat
          04:47:43 AM  CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest   %idle
          04:47:43 AM  all    0.49    0.04    0.07    0.02    0.00    0.00    0.00    0.00   99.37

    """
    async def _run_command(api, *argv, **kwarg):
        devices = kwarg['input_data']
        result = list()
        for device in devices:
            for device_name in device:
                device_result = {
                    device_name : dict()
                }
                # device lookup
                if 'device_obj' in kwarg:
                    device_obj = kwarg.get('device_obj', None)[device_name]
                else:
                    if device_name not in pytest.testbed.devices_dict:
                        device_result[device_name] = 'No matching device '+ device_name
                        result.append(device_result)
                        return result
                    device_obj = pytest.testbed.devices_dict[device_name]
                commands = ''
                if device_obj.os in ['dentos', 'cumulus']:
                    impl_obj = LinuxCpuUsageImpl()
                    for command in device[device_name]:
                        commands += impl_obj.format_command(command=api, params=command)
                        commands += '&& '
                    commands = commands[:-3]

                else:
                    device_result[device_name]['rc'] = -1
                    device_result[device_name]['result'] = 'No matching device OS '+ device_obj.os
                    result.append(device_result)
                    return result
                device_result[device_name]['command'] = commands
                try:
                    rc, output = await device_obj.run_cmd(('sudo ' if device_obj.ssh_conn_params.pssh else '') + commands)
                    device_result[device_name]['rc'] = rc
                    device_result[device_name]['result'] = output
                    if 'parse_output' in kwarg:
                        parse_output = impl_obj.parse_output(command=api, output=output, commands=commands)
                        device_result[device_name]['parsed_output'] = parse_output
                except Exception as e:
                    device_result[device_name]['rc'] = -1
                    device_result[device_name]['result'] = str(e)
                result.append(device_result)
        return result

    async def show(*argv, **kwarg):
        """
        Platforms: ['dentos', 'cumulus']
        Usage:
        CpuUsage.show(
            input_data = [{
                # device 1
                'dev1' : [{
                    # command 1
                        'options':'undefined',
                        'cpu':'int',
                        'interval':'undefined',
                }],
            }],
        )
        Description:
        mpstat [ -A ] [ -I { SUM | CPU | ALL } ] [ -u ] [ -P { cpu [,...] | ALL } ] [ -V ] [ interval [ count ] ]

        """
        return await CpuUsage._run_command('show', *argv, **kwarg)
