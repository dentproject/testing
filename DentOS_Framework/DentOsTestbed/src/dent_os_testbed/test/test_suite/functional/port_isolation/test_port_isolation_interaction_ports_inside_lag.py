import pytest
import asyncio

from dent_os_testbed.lib.bridge.bridge_link import BridgeLink
from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_clear_traffic_items,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_get_loss
)

pytestmark = [
    pytest.mark.suite_functional_port_isolation,
    pytest.mark.asyncio,
    pytest.mark.usefixtures('cleanup_bridges', 'cleanup_tgen', 'cleanup_bonds')
]


async def test_port_isolation_interaction_ports_inside_lag(testbed):
    """
    Test Name: test_port_isolation_interaction_ports_inside_lag
    Test Suite: suite_functional_port_isolation
    Test Overview: Verify port isolation functionally when ports enslaved to an isolated and non-isolated LAGs.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Create a bond (bond1), set link UP state on it and enslave the first port connected to Ixia to it.
    2.  Create a bond (bond2), set link UP state on it and enslave the second port connected to Ixia to it.
    3.  Set entities swp1, swp2, swp3, swp4 UP state.
    4.  Init bridge entity br0.
    5.  Set bridge br0 admin state UP.
    6.  Set ports swp3, swp4 master br0.
    7.  Set bonds bond1, bond2 master br0.
    8.  Set bond1 and swp3 as isolated.
    9.  Set up the streams.
    10. Verify traffic sent from isolated bond/port that was received on a non-isolated ports only.
    11. Verify traffic sent from a non-isolated bond/port is received on all ports.
    """

    bridge = 'br0'
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    device_host_name = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 15
    pps_value = 1000
    wait = 6

    for x in range(2):
        out = await IpLink.add(
            input_data=[{device_host_name: [
                {'device': f'bond{x+1}', 'type': 'bond mode 802.3ad'}]}])
        err_msg = f"Verify that bond{x+1} created and type set to 'bond mode 802.3ad'.\n{out}"
        assert out[0][device_host_name]['rc'] == 0, err_msg

        out = await IpLink.set(
            input_data=[{device_host_name: [
                {'device': f'bond{x+1}', 'operstate': 'up'},
                {'device': ports[x], 'operstate': 'down'},
                {'device': ports[x], 'master': f'bond{x+1}'}]}])
        err_msg = f"Verify that bond{x+1} set to 'UP' state, {ports[x]} set to 'DOWN' state \
            and enslave {ports[x]} port connected to Ixia.\n{out}"
        assert out[0][device_host_name]['rc'] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': port, 'operstate': 'up'} for port in ports]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that entities set to 'UP' state.\n{out}"

    out = await IpLink.add(
        input_data=[{device_host_name: [
            {'device': bridge, 'vlan_filtering': 1, 'type': 'bridge'}]}])
    err_msg = f"Verify that bridge created and vlan filtering set to 'ON'.\n{out}"
    assert out[0][device_host_name]['rc'] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': bridge, 'operstate': 'up'}]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that bridge set to 'UP' state.\n{out}"

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': port, 'master': bridge} for port in ports[2:]]}])
    err_msg = f'Verify that bridge entities {ports[2]} and {ports[3]} enslaved to bridge.\n{out}'
    assert out[0][device_host_name]['rc'] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': f'bond{x+1}', 'master': bridge} for x in range(2)]}])
    err_msg = f'Verify that bond1 and bond2 enslaved to bridge.\n{out}'
    assert out[0][device_host_name]['rc'] == 0, err_msg

    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {'device': 'bond1', 'isolated': True},
            {'device': ports[2], 'isolated': True}]}])
    err_msg = f"Verify that bond1 and {ports[2]} set to isolated state 'ON'.\n{out}"
    assert out[0][device_host_name]['rc'] == 0, err_msg

    address_map = (
        # swp port, tg port,    tg ip,     gw,        plen
        (ports[0], tg_ports[0], '1.1.1.2', '1.1.1.1', 24),
        (ports[1], tg_ports[1], '1.1.1.3', '1.1.1.1', 24),
        (ports[2], tg_ports[2], '1.1.1.4', '1.1.1.1', 24),
        (ports[3], tg_ports[3], '1.1.1.5', '1.1.1.1', 24)
    )

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': ip, 'gw': gw, 'plen': plen}
        for _, port, ip, gw, plen in address_map
    )

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    """
    Set up the following streams:
    — stream_0 —  |  — stream_1 —
    swp1 -> swp2  |  swp2 -> swp1

    — stream_0 —  |  — stream_1 —
    swp1 -> swp3  |  swp2 -> swp3

    — stream_0 —  |  — stream_1 —
    swp1 -> swp4  |  swp2 -> swp4
    """

    for x in range(3):
        streams = {
            'stream_0': {
                'ip_source': dev_groups[tg_ports[0]][0]['name'],
                'ip_destination': dev_groups[tg_ports[x+1]][0]['name'],
                'srcMac': '50:8f:f6:ba:49:9d',
                'dstMac': f'00:00:00:00:00:0{x+2}',
                'frameSize': 1164,
                'rate': pps_value,
                'protocol': '0x0800',
                'type': 'raw'
            },
            'stream_1': {
                'ip_source': dev_groups[tg_ports[1]][0]['name'],
                'ip_destination': dev_groups[tg_ports[x if x == 0 else x+1]][0]['name'],
                'srcMac': '78:f4:02:a4:db:cc',
                'dstMac': f'04:ff:a0:79:13:1{x+1}',
                'frameSize': 1164,
                'rate': pps_value,
                'protocol': '0x0800',
                'type': 'raw'
            }
        }

        await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)
        await tgen_utils_start_traffic(tgen_dev)
        await asyncio.sleep(traffic_duration)
        await tgen_utils_stop_traffic(tgen_dev)
        await asyncio.sleep(wait)

        if x == 1:
            expected_loss = {
                'stream_0': 100,
                'stream_1': 0
            }
        else:
            expected_loss = {
                'stream_0': 0,
                'stream_1': 0
            }
        # check the traffic stats
        stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
        for row in stats.Rows:
            assert tgen_utils_get_loss(row) == expected_loss[row['Traffic Item']], \
                'Verify that traffic is forwarded/not forwarded in accordance.'

        await tgen_utils_clear_traffic_items(tgen_dev)
