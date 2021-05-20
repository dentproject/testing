# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# generated using file ./gen/model/dent/system/os/memory.yaml
#
# DONOT EDIT - generated by diligent bots

import pytest
from dent_os_testbed.lib.os.linux.linux_memory_usage_impl import LinuxMemoryUsageImpl
from dent_os_testbed.lib.test_lib_object import TestLibObject


class MemoryUsage(TestLibObject):
    """
    cat /proc/meminfo
    MemTotal:       15844588 kB
    MemFree:         1907880 kB
    MemAvailable:   14177180 kB
    Buffers:         2597832 kB
    Cached:          8131124 kB
    SwapCached:            0 kB
    Active:          8455648 kB
    Inactive:        3306968 kB

    """

    async def _run_command(api, *argv, **kwarg):
        devices = kwarg["input_data"]
        result = list()
        for device in devices:
            for device_name in device:
                device_result = {device_name: dict()}
                # device lookup
                if "device_obj" in kwarg:
                    device_obj = kwarg.get("device_obj", None)[device_name]
                else:
                    if device_name not in pytest.testbed.devices_dict:
                        device_result[device_name] = "No matching device " + device_name
                        result.append(device_result)
                        return result
                    device_obj = pytest.testbed.devices_dict[device_name]
                commands = ""
                if device_obj.os in ["dentos", "cumulus"]:
                    impl_obj = LinuxMemoryUsageImpl()
                    for command in device[device_name]:
                        commands += impl_obj.format_command(command=api, params=command)
                        commands += "&& "
                    commands = commands[:-3]

                else:
                    device_result[device_name]["rc"] = -1
                    device_result[device_name]["result"] = "No matching device OS " + device_obj.os
                    result.append(device_result)
                    return result
                device_result[device_name]["command"] = commands
                try:
                    rc, output = await device_obj.run_cmd(
                        ("sudo " if device_obj.ssh_conn_params.pssh else "") + commands
                    )
                    device_result[device_name]["rc"] = rc
                    device_result[device_name]["result"] = output
                    if "parse_output" in kwarg:
                        parse_output = impl_obj.parse_output(
                            command=api, output=output, commands=commands
                        )
                        device_result[device_name]["parsed_output"] = parse_output
                except Exception as e:
                    device_result[device_name]["rc"] = -1
                    device_result[device_name]["result"] = str(e)
                result.append(device_result)
        return result

    async def show(*argv, **kwarg):
        """
        Platforms: ['dentos', 'cumulus']
        Usage:
        MemoryUsage.show(
            input_data = [{
                # device 1
                'dev1' : [{
                    # command 1

                }],
            }],
        )
        Description:
        MemTotal:       15844588 kB
        MemFree:         1314612 kB
        MemAvailable:   14144464 kB
        Buffers:         2058212 kB
        Cached:          9129160 kB
        SwapCached:            0 kB
        Active:          9729612 kB
        Inactive:        2537912 kB
        Active(anon):    1080196 kB
        Inactive(anon):    99792 kB

        """
        return await MemoryUsage._run_command("show", *argv, **kwarg)
