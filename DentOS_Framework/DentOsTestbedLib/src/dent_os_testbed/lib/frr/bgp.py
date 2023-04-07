# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# generated using file ./gen/model/dent/protocol/frr/bgp.yaml
#
# DONOT EDIT - generated by diligent bots

import pytest
from dent_os_testbed.lib.test_lib_object import TestLibObject
from dent_os_testbed.lib.frr.linux.linux_bgp_impl import LinuxBgpImpl


class Bgp(TestLibObject):
    """
        - router bgp 65534
          bgp router-id 10.2.0.101
          neighbor INFRA peer-group
          neighbor INFRA remote-as 65534
          neighbor INFRA timers 3 10
          neighbor 10.2.112.2 peer-group INFRA
          address-family ipv4 unicast
          network 10.1.0.0/16
          neighbor INFRA route-map DENY-ALL out
          neighbor POD soft-reconfiguration inbound
          exit-address-family

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
                        device_result[device_name] = 'No matching device ' + device_name
                        result.append(device_result)
                        return result
                    device_obj = pytest.testbed.devices_dict[device_name]
                commands = ''
                if device_obj.os in ['dentos', 'cumulus']:
                    impl_obj = LinuxBgpImpl()
                    for command in device[device_name]:
                        commands += impl_obj.format_command(command=api, params=command)
                        commands += '&& '
                    commands = commands[:-3]

                else:
                    device_result[device_name]['rc'] = -1
                    device_result[device_name]['result'] = 'No matching device OS ' + device_obj.os
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
        Bgp.show(
            input_data = [{
                # device 1
                'dev1' : [{
                    # command 1
                        'asn':'string',
                        'router-id':'string',
                        'neighbor':'string',
                        'address-family':'string',
                        'options':'string',
                }],
            }],
        )
        Description:

        """
        return await Bgp._run_command('show', *argv, **kwarg)

    async def configure(*argv, **kwarg):
        """
        Platforms: ['dentos', 'cumulus']
        Usage:
        Bgp.configure(
            input_data = [{
                # device 1
                'dev1' : [{
                    # command 1
                        'asn':'string',
                        'router-id':'string',
                        'neighbor':'string',
                        'address-family':'string',
                        'options':'string',
                }],
            }],
        )
        Description:

        """
        return await Bgp._run_command('configure', *argv, **kwarg)
