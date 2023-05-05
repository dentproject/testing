from dent_os_testbed.lib.devlink.devlink_port import DevlinkPort
from dent_os_testbed.lib.tc.tc_filter import TcFilter


async def devlink_rate_value(dev, name, value, cmode=False, device_host_name=True, set=False, verify=False):
    if set:
        out = await DevlinkPort.set(input_data=[{device_host_name: [
            {'dev': dev, 'name': name, 'value': value, 'cmode': cmode}]}])
        assert out[0][device_host_name]['rc'] == 0, f"Failed to set rate value '{value}'.\n{out}"
    if verify:
        out = await DevlinkPort.show(input_data=[{device_host_name: [
            {'options': '-j', 'dev': dev, 'name': name}]}], parse_output=True)
        assert out[0][device_host_name]['rc'] == 0, f"Failed to execute the command 'DevlinkPort.show'.\n{out}"
        devlink_info = out[0][device_host_name]['parsed_output']
        kbyte_value = devlink_info['param'][dev][0]['values'][0]['value']
        assert kbyte_value == value, f"Verify that storm control rate configured is '{value}' kbps.\n"


async def tc_filter_add(dev, vlan_id, src_mac, dst_mac, rate, burst, device_host_name=True):
    out = await TcFilter.add(
            input_data=[
                {
                    device_host_name: [
                        {
                            'dev': dev,
                            'direction': 'ingress',
                            'protocol': '0x8100',
                            'filtertype': {
                                'skip_sw': '',
                                'vlan_id': vlan_id,
                                'src_mac': src_mac,
                                'dst_mac': dst_mac,
                            },
                            'action': {
                                'trap': '',
                                'police': {
                                    'rate': rate,
                                    'burst': burst,
                                    'conform-exceed': '',
                                    'drop': '',
                                }
                            },
                        }
                    ]
                }
            ]
        )
    assert out[0][device_host_name]['rc'] == 0, f'Failed to create tc rules.\n{out}'
