import pytest
import asyncio

from dent_os_testbed.lib.bridge.bridge_link import BridgeLink
from dent_os_testbed.lib.bridge.bridge_fdb import BridgeFdb
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
    pytest.mark.suite_functional_bridging,
    pytest.mark.asyncio,
    pytest.mark.usefixtures('cleanup_bridges', 'cleanup_tgen')
]


async def test_bridging_backward_forwarding(testbed):
    """
    Test Name: test_bridging_backward_forwarding
    Test Suite: suite_functional_bridging
    Test Overview: Verify that traffic with learned source mac is not being backward forwarding
                   to the transmitting port which the address has been learned for.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1, swp2, swp3, swp4 master br0.
    3.  Set bridge br0 admin state UP.
    4.  Set entities swp1, swp2, swp3, swp4 UP state.
    5.  Set ports swp1, swp2, swp3, swp4 learning ON.
    6.  Set ports swp1, swp2, swp3, swp4 flood OFF.
    7.  Traffic streamA sending to swp1 with source mac aa:bb:cc:dd:ee:11 and
        destination mac ff:ff:ff:ff:ff:ff for swp1 to learn source address.
    8.  Traffic streamB sending to swp1 with source mac aa:bb:cc:dd:ee:12 and
        destination mac aa:bb:cc:dd:ee:11.
    9.  Verify that there was no backward forwarding to swp1 from streamA.
    10. Verify that source mac aa:bb:cc:dd:ee:11 have been learned on swp1 from streamA.
    11. Verify that there was no backward forwarding back to swp1 from streamB.
    """

    bridge = 'br0'
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    device_host_name = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 5

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

    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {'device': port, 'learning': True, 'flood': False} for port in ports]}])
    err_msg = f"Verify that entities set to learning 'ON' and flooding 'OFF' state.\n{out}"
    assert out[0][device_host_name]['rc'] == 0, err_msg

    address_map = (
        # swp port, tg port,    tg ip,     gw,        plen
        (ports[0], tg_ports[0], '1.1.1.2', '1.1.1.1', 24),
        (ports[0], tg_ports[0], '1.1.1.3', '1.1.1.1', 24),
    )

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': ip, 'gw': gw, 'plen': plen}
        for _, port, ip, gw, plen in address_map
    )

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    streams = {
        'streamA': {
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[0]][1]['name'],
            'srcMac': 'aa:bb:cc:dd:ee:11',
            'dstMac': 'ff:ff:ff:ff:ff:ff',
            'type': 'raw',
            'protocol': '802.1Q',
        },
        'streamB': {
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[0]][1]['name'],
            'srcMac': 'aa:bb:cc:dd:ee:12',
            'dstMac': 'aa:bb:cc:dd:ee:11',
            'type': 'raw',
            'protocol': '802.1Q',
        }
    }

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Traffic Item Statistics')
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) == 100.000, \
            f"Verify that traffic from {row['Tx Port']} to {row['Rx Port']} not forwarded.\n{out}"

    out = await BridgeFdb.show(input_data=[{device_host_name: [{'options': '-j'}]}],
                               parse_output=True)
    assert out[0][device_host_name]['rc'] == 0, 'Failed to get fdb entry.'

    fdb_entries = out[0][device_host_name]['parsed_output']
    learned_macs = [en['mac'] for en in fdb_entries if 'mac' in en]
    list_macs = ['aa:bb:cc:dd:ee:11', 'aa:bb:cc:dd:ee:12']
    for mac in list_macs:
        err_msg = f'Expected MACs are not found in FDB, but found MACs:{out}\n'
        assert mac in learned_macs, err_msg


async def test_bridging_forward_block_different_packets(testbed):
    """
    Test Name: test_bridging_forward_block_different_packets
    Test Suite: suite_functional_bridging
    Test Overview: Verify that bridge forwarding/drop of different IPv4 packet types.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1. Init bridge entity br0.
    2. Set ports swp1, swp2, swp3, swp4 master br0.
    3. Set entities swp1, swp2, swp3, swp4 UP state.
    4. Set bridge br0 admin state UP.
    5. Send different types of packets from source TG.
    6. Analyze traffic behaviour taking into account the traffic type that was sent.
    """

    bridge = 'br0'
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    device_host_name = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 10
    srcMac = '00:00:AA:00:00:01'

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
        (ports[1], tg_ports[1], '1.1.1.3', '1.1.1.1', 24)
    )

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': ip, 'gw': gw, 'plen': plen}
        for _, port, ip, gw, plen in address_map
    )

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    streams = {
        'IPv4_Broadcast': {
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcIp': '1.1.1.2',
            'dstIp': '100.1.1.255',
            'srcMac': srcMac,
            'dstMac': 'FF:FF:FF:FF:FF:FF',
            'frameSize': 96,
            'protocol': '0x0800',
            'type': 'raw'
        },
        'IPv4_Reserved_MC': {
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcIp': '1.1.1.2',
            'dstIp': '224.0.0.69',
            'srcMac': {'type': 'increment',
                       'start': srcMac,
                       'step': '00:00:00:00:10:00',
                       'count': 32},
            'dstMac': '01:00:5E:00:00:45',
            'frameSize': 96,
            'protocol': '0x0800',
            'type': 'raw'
        },
        'IPv4_All_Systems_on_this_Subnet': {
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcIp': '1.1.1.2',
            'dstIp': '224.0.0.1',
            'srcMac': srcMac,
            'dstMac': '01:00:5E:00:00:01',
            'frameSize': 96,
            'protocol': '0x0800',
            'type': 'raw'
        },
        'IPv4_All_Routers_on_this_Subnet': {
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcIp': '1.1.1.2',
            'dstIp': '224.0.0.2',
            'srcMac': srcMac,
            'dstMac': '01:00:5E:00:00:02',
            'frameSize': 96,
            'protocol': '0x0800',
            'type': 'raw'
        },
        'IPv4_OSPFIGP': {
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcIp': '1.1.1.2',
            'dstIp': '224.0.0.5',
            'srcMac': {'type': 'increment',
                       'start': srcMac,
                       'step': '00:00:00:00:10:00',
                       'count': 2},
            'dstMac': '01:00:5E:00:00:05',
            'frameSize': 96,
            'protocol': '0x0800',
            'type': 'raw'
        },
        'IPv4_RIP2_Routers': {
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcIp': '1.1.1.2',
            'dstIp': '224.0.0.9',
            'srcMac': srcMac,
            'dstMac': '01:00:5E:00:00:09',
            'frameSize': 96,
            'protocol': '0x0800',
            'type': 'raw'
        },
        'IPv4_EIGRP_Routers': {
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcIp': '1.1.1.2',
            'dstIp': '224.0.0.10',
            'srcMac': srcMac,
            'dstMac': '01:00:5E:00:00:0A',
            'frameSize': 96,
            'protocol': '0x0800',
            'type': 'raw'
        },
        'IPv4_DHCP_Server/Relay_Agent': {
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcIp': '1.1.1.2',
            'dstIp': '224.0.0.12',
            'srcMac': srcMac,
            'dstMac': '01:00:5E:00:00:0C',
            'ipproto': 'udp',
            'srcPort': '68',
            'dstPort': '67',
            'frameSize': 96,
            'protocol': '0x0800',
            'type': 'raw'
        },
        'IPv4_VRRP': {
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcIp': '1.1.1.2',
            'dstIp': '224.0.0.18',
            'srcMac': srcMac,
            'dstMac': '01:00:5E:00:00:12',
            'frameSize': 96,
            'protocol': '0x0800',
            'type': 'raw'
        },
        'IPv4_IGMP': {
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcIp': '1.1.1.2',
            'dstIp': '224.0.0.22',
            'srcMac': srcMac,
            'dstMac': '01:00:5E:00:00:16',
            'frameSize': 96,
            'protocol': '0x0800',
            'type': 'raw'
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


async def test_bridging_fdb_flush_on_down(testbed):
    """
    Test Name: test_bridging_fdb_flush_on_down
    Test Suite: suite_functional_bridging
    Test Overview: Verify that fdb enries are removed when port goes to the down state.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1, swp2, swp3, swp4 master br0.
    3.  Set bridge br0 admin state UP.
    4.  Set entities swp1, swp2, swp3, swp4 UP state.
    5.  Set ports swp1, swp2, swp3, swp4 learning ON.
    6.  Set ports swp1, swp2, swp3, swp4 flood OFF.
    7.  Send traffic to swp1 with sourse mac aa:bb:cc:dd:ee:11.
    8.  Verify fdb entry on swp1 in mac table.
    9.  Set port swp2 admin state DOWN.
    10. Verify that entry does not exist in mac table.
    """

    bridge = 'br0'
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    device_host_name = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 5

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

    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {'device': port, 'learning': True, 'flood': False} for port in ports]}])
    err_msg = f"Verify that entities set to learning 'ON' and flooding 'OFF' state.\n{out}"
    assert out[0][device_host_name]['rc'] == 0, err_msg

    address_map = (
        # swp port, tg port,    tg ip,      gw          plen
        (ports[0], tg_ports[0], '11.0.0.1', '11.0.0.2', 24),
        (ports[1], tg_ports[1], '11.0.0.2', '11.0.0.1', 24)
    )

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': ip, 'gw': gw, 'plen': plen}
        for _, port, ip, gw, plen in address_map
    )

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    streams = {
        'bridge': {
            'ip_source': dev_groups[tg_ports[1]][0]['name'],
            'ip_destination': dev_groups[tg_ports[0]][0]['name'],
            'srcMac': 'aa:bb:cc:dd:ee:11',
            'dstMac': 'ff:ff:ff:ff:ff:ff',
            'type': 'raw',
            'protocol': '802.1Q',
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

    out = await BridgeFdb.show(input_data=[{device_host_name: [{'options': '-j'}]}],
                               parse_output=True)
    assert out[0][device_host_name]['rc'] == 0, 'Failed to get fdb entry.'

    fdb_entries = out[0][device_host_name]['parsed_output']
    learned_macs = [en['mac'] for en in fdb_entries if 'mac' in en]
    err_msg = 'Verify that entry exist in mac table.'
    assert streams['bridge']['srcMac'] in learned_macs, err_msg

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': ports[1], 'operstate': 'down'}]}])
    err_msg = f"Verify that swp2 entity set to 'DOWN' state.\n{out}"
    assert out[0][device_host_name]['rc'] == 0, err_msg

    out = await BridgeFdb.show(input_data=[{device_host_name: [{'options': '-j'}]}],
                               parse_output=True)
    assert out[0][device_host_name]['rc'] == 0, 'Failed to get fdb entry.'

    fdb_entries = out[0][device_host_name]['parsed_output']
    learned_macs = [en['mac'] for en in fdb_entries if 'mac' in en]
    err_msg = 'Verify that entry does not exist in mac table.'
    assert streams['bridge']['srcMac'] not in learned_macs, err_msg


async def test_bridging_traffic_from_nomaster(testbed):
    """
    Test Name: test_bridging_traffic_from_nomaster
    Test Suite: suite_functional_bridging
    Test Overview: Verify that traffic is not being forward from nomaster to slave port and vice versa.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1, swp2, swp3, swp4 master br0.
    3.  Set entities swp1, swp2, swp3, swp4 UP state.
    4.  Set bridge br0 admin state UP.
    5.  Set ports swp1, swp2, swp3, swp4 learning OFF.
    6.  Set ports swp1, swp2, swp3, swp4 flood OFF.
    7.  Adding FDB static entries for ports swp1, swp2, swp3, swp4.
    8.  Set port swp1 to nomaster.
    9.  Send traffic by TG.
    10. Verify that traffic is not being forward from nomaster to slave port.
    """

    bridge = 'br0'
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    device_host_name = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 5

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
    err_msg = f"Verify that bridge, bridge entities set to 'UP' state.\n{out}"
    assert out[0][device_host_name]['rc'] == 0, err_msg

    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {'device': port, 'learning': False, 'flood': False} for port in ports]}])
    err_msg = f"Verify that entities set to learning 'OFF' and flooding 'OFF' state.\n{out}"
    assert out[0][device_host_name]['rc'] == 0, err_msg

    out = await BridgeFdb.add(
        input_data=[{device_host_name: [
            {'device': ports[x], 'lladdr': f'aa:bb:cc:dd:ee:1{x+1}', 'master': True, 'static': True}
            for x in range(4)]}])
    assert out[0][device_host_name]['rc'] == 0, f'Verify that FDB static entries added.\n{out}'

    out = await IpLink.set(
        input_data=[{device_host_name: [{'device': ports[0], 'nomaster': True}]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that swp1 entity set to 'nomaster'.\n{out}"

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

    list_macs = ['aa:bb:cc:dd:ee:11', 'aa:bb:cc:dd:ee:12',
                 'aa:bb:cc:dd:ee:13', 'aa:bb:cc:dd:ee:14']

    streams = {
        f'bridge_{dst + 1}': {
            'ip_source': dev_groups[tg_ports[src]][0]['name'],
            'ip_destination': dev_groups[tg_ports[dst]][0]['name'],
            'srcMac': list_macs[src],
            'dstMac': list_macs[dst],
            'type': 'raw',
            'protocol': '802.1Q',
        } for src, dst in ((3, 0), (2, 1), (1, 2), (0, 3))
    }

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        if row['Traffic Item'] == 'bridge_1' and row['Rx Port'] == tg_ports[0]:
            assert tgen_utils_get_loss(row) == 100.000, \
                'Verify that traffic from swp4 to swp1 not forwarded.'
        if row['Traffic Item'] == 'bridge_2' and row['Rx Port'] == tg_ports[1]:
            assert tgen_utils_get_loss(row) == 0.000, \
                'Verify that traffic from swp3 to swp2 forwarded.'
        if row['Traffic Item'] == 'bridge_3' and row['Rx Port'] == tg_ports[2]:
            assert tgen_utils_get_loss(row) == 0.000, \
                'Verify that traffic from swp2 to swp3 forwarded.'
        if row['Traffic Item'] == 'bridge_4' and row['Rx Port'] == tg_ports[3]:
            assert tgen_utils_get_loss(row) == 100.000, \
                'Verify that traffic from swp1 to swp4 not forwarded.'


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
    device_host_name = dent_devices[0].host_name
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


async def test_bridging_wrong_fcs(testbed):
    """
    Test Name: test_bridging_wrong_fcs
    Test Suite: suite_functional_bridging
    Test Overview: Verify that packet drop due to wrong frame check sequence.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1, swp2, swp3, swp4 master br0.
    3.  Set bridge br0 admin state UP.
    4.  Set entities swp1, swp2, swp3, swp4 UP state.
    5.  Set ports swp1, swp2, swp3, swp4 learning ON.
    6.  Set ports swp1, swp2, swp3, swp4 flood ON.
    7.  Send traffic with bad_crc for bridge to learn address.
    8.  Verify that addresses haven't been learned and haven't been forwarded.
    """

    bridge = 'br0'
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    device_host_name = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 5

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
            {'device': port, 'master': 'br0', 'operstate': 'up'} for port in ports]}])
    err_msg = f"Verify that bridge entities set to 'UP' state and links enslaved to bridge.\n{out}"
    assert out[0][device_host_name]['rc'] == 0, err_msg

    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {'device': port, 'learning': True, 'flood': True} for port in ports]}])
    err_msg = f"Verify that entities set to learning 'ON' and flooding 'ON' state.\n{out}"
    assert out[0][device_host_name]['rc'] == 0, err_msg

    address_map = (
        # swp port, tg port,    tg ip,     gw,        plen
        (ports[0], tg_ports[0], '1.1.1.2', '1.1.1.1', 24),
        (ports[1], tg_ports[1], '2.2.2.2', '2.2.2.1', 24)
    )

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': ip, 'gw': gw, 'plen': plen}
        for _, port, ip, gw, plen in address_map
    )

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    streams = {
        'bridge': {
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcMac': 'aa:bb:cc:dd:ee:11',
            'dstMac': 'aa:bb:cc:dd:ee:12',
            'type': 'raw',
            'protocol': '802.1Q',
            'bad_crc': True,
        }
    }

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Traffic Item Statistics')
    for row in stats.Rows:
        assert float(row['Tx Frames']) > 0.000, f'Failed>Ixia should transmit traffic: {row["Tx Frames"]}'
        assert tgen_utils_get_loss(row) == 100.000, \
            f"Verify that traffic from {row['Tx Port']} to {row['Rx Port']} not forwarded.\n{out}"

    out = await BridgeFdb.show(input_data=[{device_host_name: [{'options': '-j'}]}],
                               parse_output=True)
    assert out[0][device_host_name]['rc'] == 0, 'Failed to get fdb entry.'

    fdb_entries = out[0][device_host_name]['parsed_output']
    learned_macs = [en['mac'] for en in fdb_entries if 'mac' in en]
    list_macs = ['aa:bb:cc:dd:ee:11', 'aa:bb:cc:dd:ee:12']
    for mac in list_macs:
        err_msg = 'Verify that source macs have not been learned due to wrong frame check sequence.'
        assert mac not in learned_macs, err_msg
