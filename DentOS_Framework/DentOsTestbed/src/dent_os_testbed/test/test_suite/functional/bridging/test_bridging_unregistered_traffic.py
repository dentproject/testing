import pytest
import asyncio

from dent_os_testbed.lib.bridge.bridge_link import BridgeLink
from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_get_loss,
)

pytestmark = [
    pytest.mark.suite_functional_bridging,
    pytest.mark.asyncio,
    pytest.mark.usefixtures('cleanup_bridges', 'cleanup_tgen')
]


async def test_bridging_unregistered_traffic(testbed):
    """
    Test Name: test_bridging_unregistered_traffic
    Test Suite: suite_functional_bridging
    Test Overview: Verify bridge flooding behaviour of unregistered packets.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1, swp2, swp3, swp4 master br0.
    3.  Set entities swp1, swp2, swp3, swp4 UP state.
    4.  Set bridge br0 admin state UP.
    5.  Send increment traffic from TG.
    6.  Verify that traffic flooded to all ports that are members in br0.
    7.  Disable multicast flooding on the ports.
    8.  Send increment traffic from TG.
    9.  Verify that traffic was not flooded/forwarded to any of the disabled ports.
    10. Enable back multicast flooding on the ports.
    11. Send increment traffic from TG.
    12. Verify that traffic flooded to all ports that are members in br0.
    """

    bridge = 'br0'
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 10
    mac_count = 1500
    pps_value = 1000

    out = await IpLink.add(
        input_data=[{device_host_name: [
            {'device': bridge, 'type': 'bridge'}]}])
    assert out[0][device_host_name]['rc'] == 0, f'Verify that bridge created.\n{out}'

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': bridge, 'operstate': 'up'}]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that bridge set to 'UP' state.\n{out}"

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': port, 'master': bridge, 'operstate': 'up'} for port in ports]}])
    err_msg = f"Verify that bridge entities set to 'UP' state and links enslaved to bridge.\n{out}"
    assert out[0][device_host_name]['rc'] == 0, err_msg

    address_map = (
        # swp port, tg port,    tg ip,     gw,        plen
        (ports[0], tg_ports[0], '1.1.1.2', '1.1.1.1', 24),
        (ports[1], tg_ports[1], '1.1.1.3', '1.1.1.1', 24),
        (ports[2], tg_ports[2], '1.1.1.4', '1.1.1.1', 24),
        (ports[3], tg_ports[3], '1.1.1.5', '1.1.1.1', 24),
    )

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': ip, 'gw': gw, 'plen': plen}
        for _, port, ip, gw, plen in address_map
    )

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    streams = {
        'streamA': {
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcMac': {'type': 'increment',
                       'start': '00:00:00:00:00:35',
                       'step': '00:00:00:00:10:00',
                       'count': mac_count},
            'dstMac': 'aa:bb:cc:dd:ee:11',
            'type': 'raw',
            'protocol': '802.1Q',
            'rate': pps_value,
        },
        'streamB': {
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[2]][0]['name'],
            'srcMac': {'type': 'increment',
                       'start': '00:00:00:00:00:35',
                       'step': '00:00:00:00:10:00',
                       'count': mac_count},
            'dstMac': 'aa:bb:cc:dd:ee:12',
            'type': 'raw',
            'protocol': '802.1Q',
            'rate': pps_value,
        },
        'streamC': {
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[3]][0]['name'],
            'srcMac': {'type': 'increment',
                       'start': '00:00:00:00:00:35',
                       'step': '00:00:00:00:10:00',
                       'count': mac_count},
            'dstMac': 'aa:bb:cc:dd:ee:13',
            'type': 'raw',
            'protocol': '802.1Q',
            'rate': pps_value,
        }
    }

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Traffic Item Statistics')
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) == 0.000, \
            f"Verify that traffic from {row['Tx Port']} to {row['Rx Port']} forwarded.\n{out}"

    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {'device': port, 'flood': False} for port in ports]}])
    err_msg = f"Verify that entities set to flooding 'OFF' state.\n{out}"
    assert out[0][device_host_name]['rc'] == 0, err_msg

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Traffic Item Statistics')
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) == 100.000, \
            f"Verify that traffic from {row['Tx Port']} to {row['Rx Port']} not forwarded.\n{out}"

    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {'device': port, 'flood': True} for port in ports]}])
    err_msg = f"Verify that entities set to flooding 'ON' state.\n{out}"
    assert out[0][device_host_name]['rc'] == 0, err_msg

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Traffic Item Statistics')
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) == 0.000, \
            f"Verify that traffic from {row['Tx Port']} to {row['Rx Port']} forwarded.\n{out}"
