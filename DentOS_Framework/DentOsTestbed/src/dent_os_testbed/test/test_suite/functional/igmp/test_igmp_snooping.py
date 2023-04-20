import math
import asyncio
import pytest

from dent_os_testbed.lib.bridge.bridge_mdb import BridgeMdb
from dent_os_testbed.lib.bridge.bridge_link import BridgeLink
from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_dev_groups_from_config,
    tgen_utils_traffic_generator_connect,
    tgen_utils_setup_streams,
    tgen_utils_get_traffic_stats,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_clear_traffic_items,
)

pytestmark = [pytest.mark.suite_functional_igmp,
              pytest.mark.asyncio,
              pytest.mark.usefixtures('cleanup_bridges')]

GENERAL_QUERY_IP = '224.0.0.1'
IGMP_LEAVE_V2_IP = '224.0.0.2'
DEVIATION_BPS = 1000


async def get_bridge_mdb(device_name, options='-d -s -j'):
    """
    Get parsed bridge Mdb entries
    Args:
        device_name (str): Dent device host_name
        options (str): Options to pass to bridge cmd
    Returns:
        Dictionary with parsed mdb and router entries
    """

    out = await BridgeMdb.show(
        input_data=[{device_name: [
            {'options': options}]}], parse_output=True)
    err_msg = f'Verify bridge mdb show cmd was successful \n{out}'
    assert out[0][device_name]['rc'] == 0, err_msg

    router_entires = out[0][device_name]['parsed_output'][0]['router']
    mdb_entires = out[0][device_name]['parsed_output'][0]['mdb']
    return mdb_entires, router_entires


async def common_bridge_and_igmp_setup(device_name, bridge, igmp_ver, dut_ports, querier_interval=0):
    """
    Common setup part for bridge and igmp
    Args:
        device_name (str): Dent device host name
        bridge (str): Bridge device name
        igm_ver (int): IGMP Version to set on bridge dev
        dut_ports (list): List containing Dent device ports
        querier_interval (int): Multicast querier_interval to be set
    """

    out = await IpLink.add(
        input_data=[{device_name: [
            {'device': bridge, 'type': 'bridge', 'vlan_filtering': 1}]}])
    err_msg = f'Verify that bridge created and vlan filtering set successful\n{out}'
    assert out[0][device_name]['rc'] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_name: [
            {'device': bridge, 'operstate': 'up'}]}])
    err_msg = f"Verify that bridge set to 'UP' state.\n{out}"
    assert out[0][device_name]['rc'] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_name: [
            {'device': bridge, 'type': 'bridge', 'mcast_snooping': 1, 'mcast_igmp_version': igmp_ver}]}])
    err_msg = f'Verify that bridge set mcast_snooping 1 and mcast_igmp_version {igmp_ver}.\n{out}'
    assert out[0][device_name]['rc'] == 0, err_msg

    if querier_interval:
        out = await IpLink.set(
            input_data=[{device_name: [
                {'device': bridge, 'type': 'bridge', 'mcast_querier': 1,
                 'mcast_querier_interval': querier_interval * 100}]}])
        err_msg = f'Verify bridge set mcast_querier 1 and mcast_querier_interval to {querier_interval * 100}.\n{out}'
        assert out[0][device_name]['rc'] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_name: [
            {'device': port, 'master': bridge, 'operstate': 'up'} for port in dut_ports]}])
    err_msg = f"Verify that bridge entities set to 'UP' state and links enslaved to bridge.\n{out}"
    assert out[0][device_name]['rc'] == 0, err_msg


def verify_expected_rx_rate(stats, tx_port, rx_ports, rate_coef=0, deviation=0.10):
    """
    Verify expected rx_rate in bytes on ports
    Args:
        stats (stats_object): Output of tgen_utils_get_traffic_stats
        tx_port (str): Name of Tx Port
        rx_ports (list): list of Rx ports which rate should be verified
        rate_coef (float): Rate coefficient for expected rx_rate
        deviation (int): Permissible deviation percentage
    """
    collected = {row['Port Name']:
                 {'tx_rate': row['Bytes Tx. Rate'], 'rx_rate': row['Bytes Rx. Rate']} for row in stats.Rows}
    tx_name = tx_port.split('_')[0]
    exp_rate = float(collected[tx_name]['tx_rate']) * rate_coef if rate_coef else float(collected[tx_name]['tx_rate'])
    for port in rx_ports:
        rx_name = port.split('_')[0]
        res = math.isclose(exp_rate, float(collected[rx_name]['rx_rate']), rel_tol=deviation)
        assert res, f"Rx_rate {collected[rx_name]['rx_rate']} on {rx_name} exceeds expected rx_rate {exp_rate}"


def verify_mdb_entries(mdb_entries, port_names, grp_addrs):
    """
    Verify that expected Mdb entires are present in Mdb table
    Args:
        mdb_entries (dict): Dict with Mdb entries
        port_names (list): DUT port names expected to be in Mdb entries
        grp_addrs (list): Igmp group address to check
    """
    for port, group in zip(port_names, grp_addrs):
        for mdb in mdb_entries:
            if mdb['port'] == port:
                assert mdb['grp'] == group, f'Mdb entry by port {port} is {mdb[port]} expected {group}'


def mcast_ip_to_mac(ip):
    """
    Calculate multicast Mac address based on mcast ip
    Args:
        ip (str): Multicast ip address
    Returns:
        Multicast Mac address as string
    """
    mac_addr = [0x01, 0x00, 0x5e]
    for index, octet in enumerate(ip.split('.')[1:]):
        octet = int(octet) & 0x7f if not index else int(octet)
        mac_addr.append(octet)
    return ':'.join(['{:02x}'.format(octet) for octet in mac_addr])


@pytest.mark.parametrize('igmp_ver, igmp_msg_ver', [(2, 2), (3, 3), (2, 1), (3, 1), (3, 2)])
async def test_igmp_snooping_mixed_ver(testbed, igmp_ver, igmp_msg_ver):
    """
    Test Name: test_igmp_snooping
    Test Suite: suite_functional_igmp
    Test Overview: Test IGMP snooping mixed and identical versions
    Test Procedure:
    1. Create bridge and enable IGMP Snooping, enslave all TG ports to bridge interface
       Config Fastleave on 1st rx_port
    2. Init interfaces and create 2 mcast Streams
    3. Create 3 membership report streams, 1 with invalid checksum
    4. Send Traffic from router port and from clients
    5. Verify Mdb entries were created from clients
    6. Verify the multicast traffic is flooded to all bridge ports
    7. Stop traffic, create a general query stream from tx_port and send traffic
    8. Verify MDB entries were created for router
    9. Verify the traffic is forwarded to the members only
    10. Create and send Leave stream from 1st rx_port
    11. Verify MDB entry for leave port is deleted and no traffic is received
    """

    bridge = 'br0'
    sleep_value = 8
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dev_name = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]
    mcast_group1 = '227.1.1.1'
    mcast_group2 = '239.2.2.2'
    mcast_group_addr = [mcast_group1, mcast_group2, mcast_group2]
    macs = ['a6:00:00:00:00:01', 'a6:00:00:00:00:02', 'a6:00:00:00:00:03', 'a6:00:00:00:00:04']
    igmpv_and_type = {1: {'igmp_msg_v': 'igmpv2', 'igmp_type': '18', 'totalLength': '28'},
                      2: {'igmp_msg_v': 'igmpv2', 'igmp_type': '22', 'totalLength': '28'},
                      3: {'igmp_msg_v': 'igmpv3MembershipReport', 'igmp_type': '22', 'totalLength': '40'}}

    # 1.Create bridge and enable IGMP Snooping, enslave all TG ports to bridge interface
    # Config Fastleave on 1st rx_port
    await common_bridge_and_igmp_setup(dev_name, bridge, igmp_ver, dut_ports)
    out = await BridgeLink.set(
        input_data=[{dev_name: [
            {'device': dut_ports[1], 'fastleave': 'on'}]}])
    err_msg = f'Verify that port entities set to fastleave ON.\n{out}'
    assert out[0][dev_name]['rc'] == 0, err_msg

    # 2.Init interfaces and create 2 mcast Streams
    # 3.Create 3 membership report streams, 1 stream with invalid checksum
    dev_groups = tgen_utils_dev_groups_from_config(
        [{'ixp': tg_ports[0], 'ip': '102.0.0.3', 'gw': '102.0.0.1', 'plen': 24},
         {'ixp': tg_ports[1], 'ip': '100.0.0.3', 'gw': '100.0.0.1', 'plen': 24},
         {'ixp': tg_ports[2], 'ip': '101.0.0.3', 'gw': '101.0.0.1', 'plen': 24},
         {'ixp': tg_ports[3], 'ip': '99.0.0.3', 'gw': '99.0.0.1', 'plen': 24}])

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)
    tx_port = dev_groups[tg_ports[0]][0]['name']
    rx_ports = [dev_groups[tg_ports[1]][0]['name'],
                dev_groups[tg_ports[2]][0]['name'],
                dev_groups[tg_ports[3]][0]['name']]

    streams = {f'mcast_{idx + 1}': {
            'type': 'raw',
            'protocol': 'ip',
            'ip_source': tx_port,
            'ip_destination': rx_ports[1],
            'srcMac': macs[0],
            'dstMac': mcast_ip_to_mac(dst_ip),
            'srcIp': '0.0.0.0',
            'dstIp': dst_ip,
            'frame_rate_type': 'line_rate',
            'rate': 40,
        } for idx, dst_ip in enumerate([mcast_group1, mcast_group2])}

    streams.update({f'member_report{idx + 1}': {
            'type': 'raw',
            'protocol': 'ip',
            'ip_source': dev_groups[tg_ports[idx + 1]][0]['name'],
            'ip_destination': dev_groups[tg_ports[0]][0]['name'],
            'srcMac': mac,
            'dstMac': mcast_ip_to_mac(grp_addr),
            'srcIp': dev_groups[tg_ports[idx + 1]][0]['ip'],
            'dstIp': grp_addr,
            'ipproto': igmpv_and_type[igmp_msg_ver]['igmp_msg_v'],
            'totalLength': igmpv_and_type[igmp_msg_ver]['totalLength'],
            'igmpType': igmpv_and_type[igmp_msg_ver]['igmp_type'],
            'igmpGroupAddr': grp_addr,
            'rate': 1,
            'transmissionControlType': 'fixedPktCount',
            'frameCount': 1
        } for idx, (grp_addr, mac) in enumerate(zip(mcast_group_addr, macs[1:]))
    })

    streams['member_report3']['igmpChecksum'] = '0'
    if igmp_msg_ver == 3:
        for name, stream in streams.items():
            if 'member_report' in name:
                stream['numberOfSources'] = '1'
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    # 4.Send Traffic from tx_port and rx_ports
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(sleep_value)

    # 5.Verify MDB entries were created from clients
    mdb_entires, _ = await get_bridge_mdb(dev_name)
    verify_mdb_entries(mdb_entires, dut_ports[1:2], mcast_group_addr[:-1])

    # 6.Verify the multicast traffic is flooded to all bridge ports
    await asyncio.sleep(sleep_value)
    stats = await tgen_utils_get_traffic_stats(tgen_dev)
    verify_expected_rx_rate(stats, tx_port, rx_ports)

    # 7.Stop traffic, create a general query stream from tx_port and send traffic
    await tgen_utils_stop_traffic(tgen_dev)
    stream_query = {'igmp_query': {
            'type': 'raw',
            'protocol': 'ip',
            'frameSize': '74',
            'ip_source': tx_port,
            'ip_destination': rx_ports[1],
            'srcMac': macs[0],
            'dstMac': mcast_ip_to_mac(GENERAL_QUERY_IP),
            'srcIp': dev_groups[tg_ports[0]][0]['ip'],
            'dstIp': GENERAL_QUERY_IP,
            'ipproto': 'igmpv2',
            'totalLength': '28',
            'igmpType': '17',
            'igmpGroupAddr': '0.0.0.0',
            'rate': 1,
            'transmissionControlType': 'fixedPktCount',
            'frameCount': 1
    }}
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=stream_query)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(sleep_value)

    # 8.Verify MDB entries were created for router
    _, router_entires = await get_bridge_mdb(dev_name)
    assert len(router_entires), f'No MDB router entries were added to bridge MDB table {router_entires}'

    # 9.Verify the traffic is forwarded to the members only
    await asyncio.sleep(15)
    stats = await tgen_utils_get_traffic_stats(tgen_dev)
    verify_expected_rx_rate(stats, tx_port, rx_ports[:-1], rate_coef=0.5)
    # Verify rx_port have 0 rx_rate possbile deviation 1000 Bps, due to some pkt's can pass through the port
    for row in stats.Rows:
        if row['Port Name'] == rx_ports[-1].split('_')[0]:
            assert int(row['Bytes Rx. Rate']) <= DEVIATION_BPS, f"Actual rate {row['Bytes Rx. Rate']} expected rate 0"

    # 10.Create and send Leave stream from first rx_port
    stream_leave = {'igmp_leave': {
            'type': 'raw',
            'protocol': 'ip',
            'frameSize': '74',
            'ip_source': rx_ports[0],
            'ip_destination': tx_port,
            'srcMac': macs[1],
            'dstMac': mcast_ip_to_mac(IGMP_LEAVE_V2_IP),
            'srcIp': dev_groups[tg_ports[1]][0]['ip'],
            'dstIp': IGMP_LEAVE_V2_IP,
            'ipproto': 'igmpv2',
            'totalLength': '28',
            'igmpType': '23',
            'igmpGroupAddr': mcast_group1,
            'rate': 1,
            'transmissionControlType': 'fixedPktCount',
            'frameCount': 1,
    }}
    await tgen_utils_stop_traffic(tgen_dev)
    await tgen_utils_clear_traffic_items(tgen_dev, traffic_names=['member_report1'])
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=stream_leave)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(sleep_value)

    # 11.Verify its MDB entry is deleted and no traffic is received
    mdb_entires, _ = await get_bridge_mdb(dev_name)
    verify_mdb_entries(mdb_entires, [dut_ports[2]], [mcast_group2])
    for entry in mdb_entires:
        assert dut_ports[1] != entry['port'], f'Mdb entry of port {dut_ports[1]} still exists: \n{mdb_entires}'

    # Verify no traffic is received on the port that left the group
    await asyncio.sleep(15)
    stats = await tgen_utils_get_traffic_stats(tgen_dev)
    verify_expected_rx_rate(stats, tx_port, [rx_ports[1]], rate_coef=0.5)
    # Verify rx_ports have 0 rx_rate possbile deviation 1000 Bps, due to some pkt's can pass through the port
    for row in stats.Rows:
        if row['Port Name'] in [rx_ports[0].split('_')[0], rx_ports[2].split('_')[0]]:
            assert int(row['Bytes Rx. Rate']) <= DEVIATION_BPS, f"Actual rate {row['Bytes Rx. Rate']} expected rate 0"
    await tgen_utils_stop_traffic(tgen_dev)


async def test_igmp_snooping_diff_source_addrs(testbed):
    """
    Test Name: test_igmp_snooping_diff_sources
    Test Suite: suite_functional_igmp
    Test Overview: Test IGMP snooping with different source addrs
    Test Procedure:
    1. Create a bridge and enable IGMP Snooping v3,
       Enslave all TG ports to bridge interface and set all interfaces to up state
    2. Init interfaces, create 4 multicast streams and 1 general query
    3. Generate 3 Membership reports from the clients, 1 with invalid Checksum
    4. Send Traffic from router port and from clients
    5. Verify Mdb entries were created from clients and router
    6. Verify the multicast traffic is flooded to the client #1 and #2 only
    7. Statically un-subscribe client #1 from multicast group 227.1.1.1
    8. Verify the Mdb entry for client #1 is deleted
    9. Verify the traffic is not forwarded to client #1 and still is to client #2
    """

    bridge = 'br0'
    mcast_group1 = '226.1.1.1'
    mcast_group2 = '238.2.2.2'
    sleep_value = 5
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dev_name = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]
    macs = ['a6:00:00:00:00:01', 'a6:00:00:00:00:02', 'a6:00:00:00:00:03', 'a6:00:00:00:00:04']
    mcast_group_addr = [mcast_group1, mcast_group2, mcast_group2]
    mrouter_1 = '80.1.1.5'
    mrouter_2 = '70.1.1.5'

    # 1.Create a bridge and enable IGMP Snooping v3,
    #   Enslave all TG ports to bridge interface and set all interfaces to up state
    await common_bridge_and_igmp_setup(dev_name, bridge, 3, dut_ports)

    # 2.Init interfaces, create 4 multicast streams and 1 general query
    dev_groups = tgen_utils_dev_groups_from_config(
        [{'ixp': tg_ports[0], 'ip': '102.0.0.3', 'gw': '102.0.0.1', 'plen': 24},
         {'ixp': tg_ports[1], 'ip': '100.0.0.3', 'gw': '100.0.0.1', 'plen': 24},
         {'ixp': tg_ports[2], 'ip': '101.0.0.3', 'gw': '101.0.0.1', 'plen': 24},
         {'ixp': tg_ports[3], 'ip': '99.0.0.3', 'gw': '99.0.0.1', 'plen': 24}])

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)
    tx_port = dev_groups[tg_ports[0]][0]['name']
    rx_ports = [dev_groups[tg_ports[1]][0]['name'],
                dev_groups[tg_ports[2]][0]['name'],
                dev_groups[tg_ports[3]][0]['name']]

    streams = {f'mcast_{idx + 1}': {
            'type': 'raw',
            'protocol': 'ip',
            'ip_source': tx_port,
            'ip_destination': rx_ports[1],
            'srcMac': macs[0],
            'dstMac': mcast_ip_to_mac(dst_ip),
            'srcIp': '0.0.0.0',
            'dstIp': dst_ip,
            'frame_rate_type': 'line_rate',
            'rate': 20,
        } for idx, dst_ip in enumerate([mcast_group1, mcast_group2, mcast_group1, mcast_group2])}

    streams.update({'igmp_query': {
            'type': 'raw',
            'protocol': 'ip',
            'ip_source': tx_port,
            'ip_destination': rx_ports[2],
            'frameSize': '82',
            'srcMac': macs[0],
            'dstMac': mcast_ip_to_mac(GENERAL_QUERY_IP),
            'srcIp': dev_groups[tg_ports[0]][0]['ip'],
            'dstIp': GENERAL_QUERY_IP,
            'ipproto': 'igmpv3MembershipQuery',
            'totalLength': '32',
            'igmpType': '11',
            'igmpGroupAddr': '0.0.0.0',
            'maxResponseCode': '99',
            'numberOfSources': '0',
            'rate': 1,
            'transmissionControlType': 'fixedPktCount',
            'frameCount': 1
        }})

    # 3.Generate 3 Membership reports from the clients, 1 with invalid checksum
    streams.update({f'member_report{idx + 1}': {
            'type': 'raw',
            'protocol': 'ip',
            'ip_source': dev_groups[tg_ports[idx + 1]][0]['name'],
            'ip_destination': dev_groups[tg_ports[0]][0]['name'],
            'srcMac': mac,
            'dstMac': mcast_ip_to_mac(grp_addr),
            'srcIp': dev_groups[tg_ports[idx + 1]][0]['ip'],
            'dstIp': grp_addr,
            'ipproto': 'igmpv3MembershipReport',
            'totalLength': '40',
            'igmpType': '22',
            'igmpGroupAddr': grp_addr,
            'igmpRecordType': '5',
            'igmpSourceAddr': router,
            'numberOfSources': '1',
            'rate': 1,
            'transmissionControlType': 'fixedPktCount',
            'frameCount': 1
        } for idx, (grp_addr, mac, router) in enumerate(zip(mcast_group_addr, macs[1:], [mrouter_1, mrouter_2, mrouter_2]))
    })
    streams['member_report3']['igmpChecksum'] = '0'
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    # 4.Send Traffic from router port and from clients
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(8)

    # 5.Verify Mdb entries were created from clients and router
    mdb_entires, router_entires = await get_bridge_mdb(dev_name)
    verify_mdb_entries(mdb_entires, dut_ports[1:2], mcast_group_addr[:-1])
    assert len(router_entires), f'No MDB router entries were added to bridge MDB table {len(router_entires)}'

    # 6.Verify the multicast traffic is flooded to the client #1 and #2 only
    await asyncio.sleep(15)
    stats = await tgen_utils_get_traffic_stats(tgen_dev)
    verify_expected_rx_rate(stats, tx_port, rx_ports[:-1], rate_coef=0.5)
    # Verify rx_ports have 0 rx_rate possbile deviation 1000 Bps, due to some pkt's can pass through the port
    for row in stats.Rows:
        if row['Port Name'] == rx_ports[-1].split('_')[0]:
            assert int(row['Bytes Rx. Rate']) <= DEVIATION_BPS, f"Actual rate {row['Bytes Rx. Rate']} expected rate 0"

    # 7.Statically un-subscribe client #1 from multicast group 227.1.1.1
    out = await BridgeMdb.delete(
        input_data=[{dev_name: [
            {'dev': bridge, 'port': dut_ports[1], 'group': mcast_group1, 'vid': 1}]}])
    err_msg = f'Verify that Mdb entry was successfully deleted\n{out}'
    assert out[0][dev_name]['rc'] == 0, err_msg
    await asyncio.sleep(sleep_value)

    # 8.Verify the Mdb entry for client #1 is deleted
    mdb_entires, _ = await get_bridge_mdb(dev_name)
    verify_mdb_entries(mdb_entires, [dut_ports[2]], [mcast_group2])
    for entry in mdb_entires:
        assert dut_ports[1] != entry['port'], f'Mdb entry of port {dut_ports[1]} still exists: \n{mdb_entires}'

    # 9.Verify the traffic is not forwarded to client #1 and still is to client #2
    stats = await tgen_utils_get_traffic_stats(tgen_dev)
    verify_expected_rx_rate(stats, tx_port, [rx_ports[1]], rate_coef=0.5)
    # Verify rx_ports have 0 rx_rate possbile deviation 1000 Bps, due to some pkt's can pass through the port
    for row in stats.Rows:
        if row['Port Name'] in [rx_ports[0].split('_')[0], rx_ports[2].split('_')[0]]:
            assert int(row['Bytes Rx. Rate']) <= DEVIATION_BPS, f"Actual rate {row['Bytes Rx. Rate']} expected rate 0"
    await tgen_utils_stop_traffic(tgen_dev)
