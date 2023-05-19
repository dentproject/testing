import pytest
import asyncio

from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan
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
    pytest.mark.usefixtures('cleanup_bridges', 'cleanup_tgen')
]


async def test_port_isolation_interaction_vlan_membership(testbed):
    """
    Test Name: test_port_isolation_interaction_vlan_membership
    Test Suite: suite_functional_port_isolation
    Test Overview: Isolated ports added to multiple VLANs cannot send or receive traffic to
                   or from each other on all participant VLANs, but can still communicate normally
                   with other bridge interfaces configured according to the VLANs configuration.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init VLAN aware bridge entity br0 with no default PVID.
    2.  Set ports swp1, swp2, swp3, swp4 master br0.
    3.  Set entities swp1, swp2, swp3, swp4 UP state.
    4.  Set bridge br0 admin state UP.
    5.  Set the first two bridge entities as isolated.
    6.  Add participant interfaces to multiple VLANs.
    7.  Define RX and non-RX ports according to the VLAN configuration.
    8.  Set up tagged and untagged streams on the isolated tx port.
    9.  Set up the streams.
    10. Transmit traffic by TG.
    11. Verify traffic sent from isolated ports that was received on a non-isolated port only.
    12. Verify that isolated ports cannot send or receive traffic to or from each other on all participant VLANs.
    """

    bridge = 'br0'
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    device_host_name = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 10
    pps_value = 1000
    wait = 6

    out = await IpLink.add(
        input_data=[{device_host_name: [
            {'device': bridge, 'vlan_filtering': 1, 'type': 'bridge', 'vlan_default_pvid': 0}]}])
    err_msg = f"Verify that bridge created, vlan filtering set to 'ON' and vlan_default_pvid set to '0'.\n{out}"
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
            {'device': port, 'isolated': True} for port in ports[:2]]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that entities set to isolated state 'ON'.\n{out}"

    for x in range(2):
        out = await BridgeVlan.add(
            input_data=[{device_host_name: [
                {'device': port, 'vid': 22+x} for port in ports]}])
        assert out[0][device_host_name]['rc'] == 0, f"Verify that interfaces added to vlans '22' and '23'.\n{out}"

    out = await BridgeVlan.add(
        input_data=[{device_host_name: [
            {'device': port, 'vid': 24, 'pvid': True} for port in ports]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that interfaces added to vlans '24'.\n{out}"

    out = await BridgeVlan.show(input_data=[{device_host_name: [{'cmd_options': '-j'}]}],
                                parse_output=True)
    assert out[0][device_host_name]['rc'] == 0, 'Failed to show BridgeVlan detail.'

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
    — stream_0 —  |  — stream_1 —   |  — stream_2 —  |  — stream_3 —
    swp1 -> swp4  |  swp2 -> swp4   |  swp3 -> swp4  |  swp4 -> swp3

    — stream_0 —  |  — stream_1 —   |  — stream_2 —  |  — stream_3 —
    swp1 -> swp3  |  swp2 -> swp3   |  swp3 -> swp2  |  swp4 -> swp2

    — stream_0 —  |  — stream_1 —   |  — stream_2 —  |  — stream_3 —
    swp1 -> swp2  |  swp2 -> swp1   |  swp3 -> swp1  |  swp4 -> swp1
    """

    for x in range(3):
        streams = {
            'stream_0': {
                'ip_source': dev_groups[tg_ports[0]][0]['name'],
                'ip_destination': dev_groups[tg_ports[3-x]][0]['name'],
                'srcMac': '28:be:0d:47:eb:2b',
                'dstMac': f'1c:99:9f:fb:63:1{x+2}',
                'frameSize': 162,
                'rate': pps_value,
                'protocol': '0x0800',
                'type': 'raw'
            },
            'stream_1': {
                'ip_source': dev_groups[tg_ports[1]][0]['name'],
                'ip_destination': dev_groups[tg_ports[3-x if x < 2 else 0]][0]['name'],
                'srcMac': 'f2:de:a4:35:bd:4b',
                'dstMac': f'fa:f5:38:5e:1a:1{x+2}',
                'frameSize': 162,
                'rate': pps_value,
                'protocol': '0x0800',
                'type': 'raw',
                'vlanID': 22
            },
            'stream_2': {
                'ip_source': dev_groups[tg_ports[2]][0]['name'],
                'ip_destination': dev_groups[tg_ports[3-x if x <= 0 else 2-x]][0]['name'],
                'srcMac': '2a:3e:13:88:e5:6d',
                'dstMac': f'f2:c9:74:75:45:3{x+2}',
                'frameSize': 162,
                'rate': pps_value,
                'protocol': '0x0800',
                'type': 'raw',
                'vlanID': 23
            },
            'stream_3': {
                'ip_source': dev_groups[tg_ports[3]][0]['name'],
                'ip_destination': dev_groups[tg_ports[2-x]][0]['name'],
                'srcMac': 'ea:f9:ca:10:1d:b6',
                'dstMac': f'78:d5:fc:e5:42:8{x+2}',
                'frameSize': 162,
                'rate': pps_value,
                'protocol': '0x0800',
                'type': 'raw',
                'vlanID': 24
            }
        }

        await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)
        await tgen_utils_start_traffic(tgen_dev)
        await asyncio.sleep(traffic_duration)
        await tgen_utils_stop_traffic(tgen_dev)
        await asyncio.sleep(wait)

        if x == 2:
            expected_loss = {
                'stream_0': 100,
                'stream_1': 100,
                'stream_2': 0,
                'stream_3': 0
            }
        else:
            expected_loss = {
                'stream_0': 0,
                'stream_1': 0,
                'stream_2': 0,
                'stream_3': 0
            }
        # check the traffic stats
        stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
        for row in stats.Rows:
            assert tgen_utils_get_loss(row) == expected_loss[row['Traffic Item']], \
                'Verify that traffic is forwarded/not forwarded in accordance.'
        await tgen_utils_clear_traffic_items(tgen_dev)
