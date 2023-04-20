import pytest
import asyncio

from dent_os_testbed.lib.bridge.bridge_link import BridgeLink
from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_clear_traffic_stats,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_get_loss
)

pytestmark = [
    pytest.mark.suite_functional_port_isolation,
    pytest.mark.asyncio,
    pytest.mark.usefixtures('cleanup_bridges', 'cleanup_tgen')
]


# verifying the traffic stats
async def check_traffic_stats(stats, expected_loss):
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) == expected_loss[row['Traffic Item']], \
            'Verify that traffic is forwarded/not forwarded in accordance.'


async def test_port_isolation_enable_disable_feature_under_ws_traffic(testbed):
    """
    Test Name: test_port_isolation_enable_disable_feature_under_ws_traffic
    Test Suite: suite_functional_port_isolation
    Test Overview: Port Isolation feature can be enabled and disabled under WS traffic.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1, swp2, swp3, swp4 master br0.
    3.  Set entities swp1, swp2, swp3, swp4 UP state.
    4.  Set bridge br0 admin state UP.
    5.  Set the first three bridge entities as isolated.
    6.  Set up the following streams:
            - stream on the second (isolated) TG port
            - stream on the third (isolated) TG port
            - stream on the fourth (non-isolated) TG port
    7.  Transmit continues traffic by TG.
    8.  Verify traffic sent from isolated ports that was received on a non-isolated port only.
    9.  Disable Port Isolation on all ports.
    10. Verify traffic sent from a non-isolated port is received on all ports.
    11. Set the first three bridge entities as isolated again.
    12. Verify traffic sent from isolated ports that was received on a non-isolated port only.
    13. Disable Port Isolation on all ports again.
    14. Verify traffic sent from a non-isolated port is received on all ports.
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
            {'device': port, 'master': bridge, 'operstate': 'up'} for port in ports]}])
    err_msg = f"Verify that bridge entities set to 'UP' state and links enslaved to bridge.\n{out}"
    assert out[0][device_host_name]['rc'] == 0, err_msg

    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {'device': port, 'isolated': True} for port in ports[:3]]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that entities set to isolated state 'ON'.\n{out}"

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
    — stream_1 —  |  — stream_2 —  |  — stream_3 —
    swp1 -> swp2  |  swp1 -> swp3  |  swp1 -> swp4
    """

    streams = {
        f'stream_{dst}': {
            'ip_source': dev_groups[tg_ports[src]][0]['name'],
            'ip_destination': dev_groups[tg_ports[dst]][0]['name'],
            'srcMac': f'c4:6e:c7:3c:f6:5{dst}',
            'dstMac': f'00:00:00:00:00:0{dst}',
            'frameSize': 64,
            'rate': pps_value,
            'protocol': '0x88a8',
            'type': 'raw'
        } for src, dst in ((0, 1), (0, 2), (0, 3))
    }

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)

    for x in range(2):
        # check the traffic stats
        stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
        expected_loss = {
            'stream_1': 100,
            'stream_2': 100,
            'stream_3': 0
        }
        await check_traffic_stats(stats, expected_loss)

        out = await BridgeLink.set(
            input_data=[{device_host_name: [
                {'device': port, 'isolated': False} for port in ports[:3]]}])
        assert out[0][device_host_name]['rc'] == 0, f"Verify that entities set to isolated state 'OFF'.\n{out}"

        await tgen_utils_clear_traffic_stats(tgen_dev)
        await asyncio.sleep(traffic_duration/2)

        # check the traffic stats
        stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
        expected_loss = {
            'stream_1': 0,
            'stream_2': 0,
            'stream_3': 0
        }
        await check_traffic_stats(stats, expected_loss)

        if x == 0:
            out = await BridgeLink.set(
                input_data=[{device_host_name: [
                    {'device': port, 'isolated': True} for port in ports[:3]]}])
            assert out[0][device_host_name]['rc'] == 0, f"Verify that entities set to isolated state 'ON'.\n{out}"

            await tgen_utils_clear_traffic_stats(tgen_dev)
            await asyncio.sleep(traffic_duration/2)
