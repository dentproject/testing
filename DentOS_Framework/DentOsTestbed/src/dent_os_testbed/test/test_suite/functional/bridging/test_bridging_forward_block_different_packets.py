import pytest
import asyncio

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
        print('The testbed does not have enough dent with tgen connections')
        return
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
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
            'type' :'raw'
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
            'type' :'raw'
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
            'type' :'raw'
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
            'type' :'raw'
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
            'type' :'raw'
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
            'type' :'raw'
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
            'type' :'raw'
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
            'type' :'raw'
        },
        'IPv4_VRRP': {
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcIp': '1.1.1.2',
            'dstIp': '224.0.0.18',
            'srcMac': srcMac,
            'dstMac': '01:00:5E:00:00:12',
            # "packet.ipv4.protocol": 112,
            'frameSize': 96,
            'protocol': '0x0800',
            'type' :'raw'
        },
        'IPv4_IGMP' : {
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcIp': '1.1.1.2',
            'dstIp': '224.0.0.22',
            'srcMac': srcMac,
            'dstMac': '01:00:5E:00:00:16',
            'frameSize': 96,
            'protocol': '0x0800',
            'type' :'raw'
        },
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
