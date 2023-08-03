import math
import copy
import asyncio

from dent_os_testbed.lib.devlink.devlink_port import DevlinkPort
from dent_os_testbed.lib.tc.tc_filter import TcFilter
from dent_os_testbed.test.test_suite.functional.devlink.devlink_utils import (
    verify_devlink_cpu_traps_rate_avg, SCT_MAP
)


def get_streams(list_streams, prefixes):
    filtered_streams = {}
    for stream_name, stream in list_streams.items():
        for prefix in prefixes:
            if stream_name.startswith(prefix):
                filtered_streams[stream_name] = stream
                break
    return filtered_streams


async def verify_cpu_rate(dent_dev, deviation):
    new_map = copy.deepcopy(SCT_MAP)
    keys_to_delete = ['arp_response', 'ssh', 'telnet', 'bgp', 'local_route', 'mac_to_me', 'icmp', 'acl_code_3']
    for key in keys_to_delete:
        if key in new_map:
            del new_map[key]
    for trap_name, sct in new_map.items():
        await verify_devlink_cpu_traps_rate_avg(dent_dev, trap_name, sct['exp'], deviation=deviation, logs=True)
        await asyncio.sleep(5)


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


async def verify_expected_rx_rate(kbyte_value, stats, rx_ports, deviation=0.10):
    """
    Verify expected rx_rate in bytes on ports
    Args:
        kbyte_value (int): Kbyte per sec rate
        stats (stats_object): Output of tgen_utils_get_traffic_stats
        rx_ports (list): list of Rx ports which rate should be verified
        deviation (int): Permissible deviation percentage
    """
    collected = {row['Port Name']:
                 {'tx_rate': row['Bytes Tx. Rate'], 'rx_rate': row['Bytes Rx. Rate']} for row in stats.Rows}
    exp_rate = kbyte_value*1000
    for port in rx_ports:
        rx_name = port.split('_')[0]
        res = math.isclose(exp_rate, float(collected[rx_name]['rx_rate']), rel_tol=deviation)
        assert res, f"The rate is not limited by storm control, \
                        actual rate {float(collected[rx_name]['rx_rate'])} instead of {exp_rate}."


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
