import pytest
import asyncio

from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan
from dent_os_testbed.lib.bridge.bridge_link import BridgeLink
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.ip.ip_route import IpRoute
from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_get_loss
)

pytestmark = [
    pytest.mark.suite_functional_port_isolation,
    pytest.mark.asyncio,
    pytest.mark.usefixtures('cleanup_bridges', 'cleanup_tgen', 'cleanup_ip_addrs')
]


async def test_port_isolation_interaction_route_between_vlan_devices(testbed):
    """
    Test Name: test_port_isolation_interaction_route_between_vlan_devices
    Test Suite: suite_functional_port_isolation
    Test Overview: Verify Routing between VLAN devices when VLANs' enslaved ports defined as isolated.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set bridge br0 admin state UP.
    3.  Set ports swp1, swp2 master br0.
    4.  Create VLAN-devices br0.10 and br0.11.
    5.  Set all entities admin state UP.
    6.  Add bridges to VLAN of the VLAN-devices.
    7.  Set the first two bridge entities as isolated.
    8.  Add ports to VLANs, and then configure IP addresses on VLAN devices.
    9.  Verify the offload flag appears in VLAN-device default routes.
    10. Prepare streams from one VLAN device's neighbor to the other.
    11. Transmit traffic by TG.
    12. Verify traffic is forwarded to both VLAN-device neighbors.
    """

    bridge = 'br0'
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    device_host_name = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 15
    pps_value = 1000

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
            {'device': port, 'master': bridge, 'operstate': 'up'} for port in ports[:2]]}])
    err_msg = f"Verify that bridge entities set to 'UP' state and links enslaved to bridge.\n{out}"
    assert out[0][device_host_name]['rc'] == 0, err_msg

    out = await IpLink.add(
        input_data=[{device_host_name: [
            {'link': bridge, 'name': f'br0.1{x}', 'type': f'vlan id 1{x}'} for x in range(2)]}])
    err_msg = f"Verify that links created and type set to 'vlan id 10' and 'vlan id 11'.\n{out}"
    assert out[0][device_host_name]['rc'] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': f'br0.1{x}', 'operstate': 'up'} for x in range(2)]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that links set to 'UP' state.\n{out}"

    out = await BridgeVlan.add(
        input_data=[{device_host_name: [
            {'device': bridge, 'vid': f'1{x}', 'self': True} for x in range(2)]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that bridge added to vid '10' and '11'.\n{out}"

    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {'device': port, 'isolated': True} for port in ports[:2]]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that entities set to isolated state 'ON'.\n{out}"

    out = await BridgeVlan.add(
        input_data=[{device_host_name: [
            {'device': ports[x], 'vid': f'1{x}'} for x in range(2)]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that entitie added to vid '10' and '11'.\n{out}"

    out = await IpAddress.add(
        input_data=[{device_host_name: [
            {'dev': 'br0.10', 'prefix': '1.1.1.1/24'},
            {'dev': 'br0.11', 'prefix': '2.2.2.2/24'}]}])
    assert out[0][device_host_name]['rc'] == 0, f"Failed to add IP address to 'br0.10'.\n{out}"

    for x in range(2):
        out = await IpRoute.show(input_data=[{device_host_name: [{'dev': f'br0.1{x}', 'cmd_options': '-j'}]}],
                                 parse_output=True)
        assert out[0][device_host_name]['rc'] == 0, f'Failed to execute the command IpRoute.show.\n{out}'

        ip_route_entries = out[0][device_host_name]['parsed_output']
        offload_flag = str([en['flags'] for en in ip_route_entries if 'flags' in en]).strip("]'[")
        err_msg = 'Verify the offload flag appears in VLAN-device default routes.'
        assert offload_flag == 'rt_trap', err_msg

    address_map = (
        # swp port, tg port,    tg ip,     gw,        plen
        (ports[0], tg_ports[0], '1.1.1.2', '1.1.1.1', 24),
        (ports[1], tg_ports[1], '1.1.1.3', '1.1.1.1', 24)
    )

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': ip, 'gw': gw, 'plen': plen}
        for _, port, ip, gw, plen in address_map
    )

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    """
    Set up the following streams:
    — stream_0 —  |  — stream_1 —
    swp1 -> swp4  |  swp2 -> swp4
    """

    streams = {
        'vlan_10': {
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcIp': '0.0.0.0',
            'dstIp': '2.2.2.3',
            'srcMac': '00:00:00:00:00:01',
            'dstMac': '00:00:00:00:00:02',
            'frameSize': 150,
            'rate': pps_value,
            'protocol': '0x0800',
            'type': 'raw'
        },
        'vlan_11': {
            'ip_source': dev_groups[tg_ports[1]][0]['name'],
            'ip_destination': dev_groups[tg_ports[0]][0]['name'],
            'srcIp': '0.0.0.0',
            'dstIp': '1.1.1.2',
            'srcMac': '00:00:00:00:00:01',
            'dstMac': '00:00:00:00:00:02',
            'frameSize': 150,
            'rate': pps_value,
            'protocol': '0x0800',
            'type': 'raw'
        }
    }

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) == 0.000, \
            f"Verify that traffic from {row['Tx Port']} to {row['Rx Port']} forwarded.\n{out}"
