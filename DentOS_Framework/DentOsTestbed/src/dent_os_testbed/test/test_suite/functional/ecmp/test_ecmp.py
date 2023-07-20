import math
import asyncio
import pytest
from random import randint

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.ip.ip_neighbor import IpNeighbor
from dent_os_testbed.lib.ip.ip_route import IpRoute

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_dev_groups_from_config,
    tgen_utils_traffic_generator_connect,
    tgen_utils_setup_streams,
    tgen_utils_get_traffic_stats,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_get_swp_info,
    tgen_utils_clear_traffic_stats,
)

pytestmark = [pytest.mark.suite_functional_ecmp,
              pytest.mark.asyncio,
              pytest.mark.usefixtures('cleanup_ip_addrs', 'cleanup_tgen', 'enable_ipv4_forwarding')]

RX_STATS = 'Valid Frames Rx.'
ERR_MSG = 'Expected Rx amount of pkts on port {} to be 0 actual results {}'
DEVIATION_PKTS = 50


def random_mac():
    return ':'.join(['02'] + [f'{randint(0, 255):02x}' for _ in range(5)])


async def verify_ecmp_distribution(stats, tx_port, rx_ports):
    """
    Verify Ecmp packet distribution between ports
    Args:
        stats: Ixia statistics
        tx_port (object): Tg Port object
        rx_ports (list): List with Tg Ports objects
    """
    p_err_msg = 'Port {} received pkts {} expected => {}'
    rx_sum_msg = 'Tx pkts sent {} isnt equal to sum of all rx ports received {}'
    tx_pkts_sent = [int(row['Frames Tx.']) for row in stats.Rows if row['Port Name'] == tx_port][0]
    rx_pkts_sum = []
    # We cant expected that amount of pkts traversed through each nexthop will be equal
    # Check that at least 1/10 of traffic went through port and verify sum of all rx packets is equal to tx packets
    expected = tx_pkts_sent // 10
    for row in stats.Rows:
        if row['Port Name'] in rx_ports:
            assert int(row[RX_STATS]) >= expected, p_err_msg.format(row['Port Name'], row[RX_STATS], expected)
            rx_pkts_sum.append(int(row[RX_STATS]))
    assert math.isclose(tx_pkts_sent, sum(rx_pkts_sum), rel_tol=0.01), rx_sum_msg.format(tx_pkts_sent, sum(rx_pkts_sum))


@pytest.mark.usefixtures('enable_ignore_linkdown_routes')
@pytest.mark.parametrize('nexthops_down', [1, 3])
async def test_ecmp_nexthops_down(testbed, nexthops_down):
    """
    Test Name: test_ecmp_nexthops_down
    Test Suite: suite_functional_ecmp
    Test Overview: Test Ecmp with ignore_routes_with_linkdown sysctl on and simulate 1/3 nexthops down
    Test Procedure:
    1. Enable ignore_routes_with_linkdown with fixture
    2. Configure 4 ports up
    3. Configure IP addrs on 4 dut ports and connect all devices
    4. Add static arp entries to last 3 ports (all rx ports)
    5. Configure Ecmp route to 100.0.0.0/8 with rx ports as nexthops
    6. Setup ipv4 stream with incremented ip_dst addresses that would distribute through all nexthops
    7. Configure 1st/all rx_ports down to simulate nexthops down
    8. Transmit added stream
    9. Verify traffic distributed through all expected nexthops
    10. Disable ignore_routes_with_linkdown on teardown with fixture
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dev_name = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]
    dent_dev = dent_devices[0]

    # 1.Enable net.ipv4.conf.default.ignore_routes_with_linkdown with fixture
    # 2.Configure 4 ports up
    out = await IpLink.set(
        input_data=[{dev_name: [
            {'device': port, 'operstate': 'up'} for port in dut_ports]}])
    err_msg = f"Verify that ports set to 'UP' state.\n{out}"
    assert not out[0][dev_name]['rc'], err_msg

    # 3.Configure IP addrs on 4 dut ports and connect all devices
    address_map = (
        # swp port,    tg port,     swp ip,    tg ip,     plen               lladdr
        (dut_ports[0], tg_ports[0], '1.1.1.1',  '1.1.1.2',  24, 'aa:bb:cc:dd:ee:11'),
        (dut_ports[1], tg_ports[1], '11.0.0.1', '11.0.0.2', 8,  '00:AD:20:B2:A7:75'),
        (dut_ports[2], tg_ports[2], '12.0.0.1', '12.0.0.2', 16, '00:59:CD:1E:83:1B'),
        (dut_ports[3], tg_ports[3], '13.0.0.1', '13.0.0.2', 20, '00:76:69:89:E0:7B'),
    )
    out = await IpAddress.add(input_data=[{dev_name: [
            {'dev': port, 'prefix': f'{ip}/{plen}'} for port, _, ip, _, plen, _ in address_map]}])
    assert not out[0][dev_name]['rc'], 'Failed to add IP addr to ports'

    dev_groups = tgen_utils_dev_groups_from_config(
        [{'ixp': tg_port, 'ip': tg_ip, 'gw': swp_ip, 'plen': plen}
         for _, tg_port, swp_ip, tg_ip, plen, _ in address_map])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    # 4.Add static arp entries to last 3 ports (all rx ports)
    out = await IpNeighbor.add(input_data=[{dev_name: [
        {'dev': port, 'address': nei_ip, 'lladdr': lladdr}
        for port, _, _, nei_ip, _, lladdr in address_map[1:]
    ]}])
    assert not out[0][dev_name]['rc'], 'Failed to add static arp entries'

    # 5.Configure Ecmp route to 100.0.0.0/8 with rx ports as nexthops
    out = await IpRoute.add(input_data=[{dev_name: [
        {'dst': '100.0.0.0/8', 'nexthop': [
            {'via': tg_ip, 'weight': 1} for _, _, _, tg_ip, _, _ in address_map[1:]]}
    ]}])
    assert not out[0][dev_name]['rc'], 'Failed to add nexthop'

    # 6.Setup ipv4 stream with incremented ip_dst address that would distribute through all nexthops
    swp_info = {}
    await tgen_utils_get_swp_info(dent_dev, dut_ports[0], swp_info)
    stream = {'increment_ip_dst_': {
        'type': 'raw',
        'protocol': 'ip',
        'ip_source': dev_groups[tg_ports[0]][0]['name'],
        'ip_destination': dev_groups[tg_ports[1]][0]['name'],  # We dont care about ip_dst as we will use port stats
        'srcMac': random_mac(),
        'dstMac': swp_info['mac'],
        'srcIp': f'1.1.1.{randint(3, 100)}',
        'dstIp': {'type': 'increment',
                  'start': '100.0.0.1',
                  'step':  '0.0.0.1',
                  'count': 30},
        'frameSize': 200,
        'rate': 100,
        'frame_rate_type': 'line_rate'}
    }
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=stream)

    # 7.Configure 1st/all rx_ports down to simulate nexthops down
    out = await IpLink.set(
        input_data=[{dev_name: [
            {'device': dut_ports[hop], 'operstate': 'down'} for hop in range(1, nexthops_down + 1)]}])
    err_msg = f"Verify that ports set to 'DOWN' state.\n{out}"
    assert not out[0][dev_name]['rc'], err_msg

    # 8.Transmit added stream
    await tgen_utils_clear_traffic_stats(tgen_dev)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(15)
    await tgen_utils_stop_traffic(tgen_dev)
    # Wait 15 sec for stats to be updated
    await asyncio.sleep(15)

    # 9.Verify traffic distributed through all expected nexthops
    # 10.Disable ignore_routes_with_linkdown on teardown with fixture
    stats = await tgen_utils_get_traffic_stats(tgen_dev)
    if nexthops_down == 1:
        await verify_ecmp_distribution(stats, tg_ports[0], tg_ports[2:])
        for row in stats.Rows:
            if row['Port Name'] == tg_ports[1]:
                assert int(row[RX_STATS]) <= DEVIATION_PKTS, ERR_MSG.format(row['Port Name'], row[RX_STATS])
    else:
        for row in stats.Rows:
            if row['Port Name'] != tg_ports[0]:
                assert int(row[RX_STATS]) <= DEVIATION_PKTS, ERR_MSG.format(row['Port Name'], row[RX_STATS])
    out = await IpLink.set(
        input_data=[{dev_name: [
            {'device': dut_ports[hop], 'operstate': 'up'} for hop in range(1, nexthops_down + 1)]}])
    err_msg = f"Verify that ports set to 'UP' state.\n{out}"
    assert not out[0][dev_name]['rc'], err_msg


@pytest.mark.usefixtures('enable_multipath_hash_policy')
async def test_ecmp_hash_policy(testbed):
    """
    Test Name: test_ecmp_hash_policy
    Test Suite: suite_functional_ecmp
    Test Overview: Test Ecmp with fib_multipath_hash_policy on, and hash calculated on L4 (5-tuple)
    Test Procedure:
    1. Enable net.ipv4.fib_multipath_hash_policy=1 with fixture
    2. Configure 4 ports up
    3. Configure IP addrs on 4 dut ports and connect all devices
    4. Add static arp entries to last 3 ports (all rx ports)
    5. Configure Ecmp route to 100.0.0.0/8 with rx ports as nexthops
    6. Setup 20 streams with identical l2/l3 info but random tcp dst/src ports value to 100.0.0.0/8 network
    7. Transmit all streams and wait streams to finish
    8. Verify traffic distributed through all expected nexthops
    9. Disable net.ipv4.fib_multipath_hash_policy on teardown with fixture
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dev_name = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]
    dent_dev = dent_devices[0]

    # 1.Enable net.ipv4.fib_multipath_hash_policy=1 with fixture
    # 2.Configure 4 ports up
    out = await IpLink.set(
        input_data=[{dev_name: [
            {'device': port, 'operstate': 'up'} for port in dut_ports]}])
    err_msg = f"Verify that ports set to 'UP' state.\n{out}"
    assert not out[0][dev_name]['rc'], err_msg

    # 3.Configure IP addrs on 4 dut ports and connect all devices
    address_map = (
        # swp port,    tg port,     swp ip,    tg ip,     plen               lladdr
        (dut_ports[0], tg_ports[0], '1.1.1.1',  '1.1.1.2',  24, 'aa:bb:cc:dd:ee:11'),
        (dut_ports[1], tg_ports[1], '11.0.0.1', '11.0.0.2', 8,  '00:AD:20:B2:A7:75'),
        (dut_ports[2], tg_ports[2], '12.0.0.1', '12.0.0.2', 16, '00:59:CD:1E:83:1B'),
        (dut_ports[3], tg_ports[3], '13.0.0.1', '13.0.0.2', 20, '00:76:69:89:E0:7B'),
    )
    out = await IpAddress.add(input_data=[{dev_name: [
            {'dev': port, 'prefix': f'{ip}/{plen}'} for port, _, ip, _, plen, _ in address_map]}])
    assert not out[0][dev_name]['rc'], 'Failed to add IP addr to ports'

    dev_groups = tgen_utils_dev_groups_from_config(
        [{'ixp': tg_port, 'ip': tg_ip, 'gw': swp_ip, 'plen': plen}
         for _, tg_port, swp_ip, tg_ip, plen, _ in address_map])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    # 4.Add static arp entries to last 3 ports (all rx ports)
    out = await IpNeighbor.add(input_data=[{dev_name: [
        {'dev': port, 'address': nei_ip, 'lladdr': lladdr}
        for port, _, _, nei_ip, _, lladdr in address_map[1:]
    ]}])
    assert not out[0][dev_name]['rc'], 'Failed to add static arp entries'

    # 5.Configure Ecmp route to 100.0.0.0/8 with rx ports as nexthops
    out = await IpRoute.add(input_data=[{dev_name: [
        {'dst': '100.0.0.0/8', 'nexthop': [
            {'via': tg_ip, 'weight': 1} for _, _, _, tg_ip, _, _ in address_map[1:]]}
    ]}])
    assert not out[0][dev_name]['rc'], 'Failed to add nexthop'

    # 6.Setup 20 streams with identical l2/l3 info but random tcp dst/src ports value to 100.0.0.0/8 network
    swp_info = {}
    await tgen_utils_get_swp_info(dent_dev, dut_ports[0], swp_info)
    stream = {f'stream_random_ports_{i}': {
        'type': 'raw',
        'protocol': 'ip',
        'ip_source': dev_groups[tg_ports[0]][0]['name'],
        'ip_destination': dev_groups[tg_ports[1]][0]['name'],  # We dont care about ip_dst as we will use port stats
        'srcMac': random_mac(),
        'dstMac': swp_info['mac'],
        'srcIp': '1.1.1.20',
        'dstIp': '100.0.0.1',
        'ipproto': 'tcp',
        'dstPort': randint(4000, 4500),
        'srcPort': randint(5000, 5500),
        'frameSize': 200,
        'transmissionControlType': 'fixedPktCount',
        'frameCount': 1000,
        'rate': 1000} for i in range(20)
    }
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=stream)

    # 7.Transmit all streams and wait streams to finish
    await tgen_utils_clear_traffic_stats(tgen_dev)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(60)

    # 8.Verify traffic distributed through all expected nexthops
    # 9.Disable net.ipv4.fib_multipath_hash_policy on teardown with fixture
    stats = await tgen_utils_get_traffic_stats(tgen_dev)
    await verify_ecmp_distribution(stats, tg_ports[0], tg_ports[1:])


@pytest.mark.parametrize('tc_scenario', ['basic', 'nexthop_down', 'dynamic'])
async def test_ecmp_traffic_distribution(testbed, tc_scenario):
    """
    Test Name: test_ecmp_traffic_distribution
    Test Suite: suite_functional_ecmp
    Test Overview: Test Ecmp traffic distribution between nexthops with next scenarios basic/nexthop_down/dynamic_arps
    Test Procedure:
    1. Configure 4 ports up
    2. Configure IP addrs on 4 dut ports and connect all devices
    3. Add static arp entries to last 3 ports (all rx ports) in case basic/nexthop_down scenario
       In dynamic scenario arps will be generated dynamically by Ixia
    4. Configure Ecmp route to 100.0.0.0/8 with rx ports as nexthops
    5. Setup ipv4 stream with incremented ip_dst addresses that would distribute through all nexthops
    6. In case of nexthop_down scenario, simulate nexthop down by setting first rx_port to down state
    7. Transmit added stream for 15 sec
    8. Verify traffic distributed through all expected nexthops
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dev_name = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]
    dent_dev = dent_devices[0]

    # 1.Configure 4 ports up
    out = await IpLink.set(
        input_data=[{dev_name: [
            {'device': port, 'operstate': 'up'} for port in dut_ports]}])
    err_msg = f"Verify that ports set to 'UP' state.\n{out}"
    assert not out[0][dev_name]['rc'], err_msg

    # 2.Configure IP addrs on 4 dut ports and connect all devices
    address_map = (
        # swp port,    tg port,     swp ip,    tg ip,     plen               lladdr
        (dut_ports[0], tg_ports[0], '1.1.1.1',  '1.1.1.2',  24, 'aa:bb:cc:dd:ee:11'),
        (dut_ports[1], tg_ports[1], '11.0.0.1', '11.0.0.2', 8,  '00:AD:20:B2:A7:75'),
        (dut_ports[2], tg_ports[2], '12.0.0.1', '12.0.0.2', 16, '00:59:CD:1E:83:1B'),
        (dut_ports[3], tg_ports[3], '13.0.0.1', '13.0.0.2', 20, '00:76:69:89:E0:7B'),
    )

    out = await IpAddress.add(input_data=[{dev_name: [
            {'dev': port, 'prefix': f'{ip}/{plen}'} for port, _, ip, _, plen, _ in address_map]}])
    assert not out[0][dev_name]['rc'], 'Failed to add IP addr to ports'

    dev_groups = tgen_utils_dev_groups_from_config(
        [{'ixp': tg_port, 'ip': tg_ip, 'gw': swp_ip, 'plen': plen}
         for _, tg_port, swp_ip, tg_ip, plen, _ in address_map])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    # 3.Add static arp entries to last 3 ports (all rx ports) in case basic/nexthop_down scenario
    # In dynamic scenario arps will be generated dynamically by Ixia
    if tc_scenario != 'dynamic':
        out = await IpNeighbor.add(input_data=[{dev_name: [
            {'dev': port, 'address': nei_ip, 'lladdr': lladdr}
            for port, _, _, nei_ip, _, lladdr in address_map[1:]
        ]}])
        assert not out[0][dev_name]['rc'], 'Failed to add static arp entries'

    # 4.Configure Ecmp route to 100.0.0.0/8 with rx ports as nexthops
    out = await IpRoute.add(input_data=[{dev_name: [
        {'dst': '100.0.0.0/8', 'nexthop': [
            {'via': tg_ip, 'weight': 1} for _, _, _, tg_ip, _, _ in address_map[1:]]}
    ]}])
    assert not out[0][dev_name]['rc'], 'Failed to add nexthop'

    # 5.Setup ipv4 stream with incremented ip_dst addresses that would distribute through all nexthops
    swp_info = {}
    await tgen_utils_get_swp_info(dent_dev, dut_ports[0], swp_info)
    stream = {'increment_ip_dst_': {
        'type': 'raw',
        'protocol': 'ip',
        'ip_source': dev_groups[tg_ports[0]][0]['name'],
        'ip_destination': dev_groups[tg_ports[1]][0]['name'],  # We dont care about ip_dst as we will use port stats
        'srcMac': random_mac(),
        'dstMac': swp_info['mac'],
        'srcIp': f'1.1.1.{randint(3, 100)}',
        'dstIp': {'type': 'increment',
                  'start': '100.0.0.1',
                  'step':  '0.0.0.1',
                  'count': 30},
        'frameSize': 200,
        'rate': 100,
        'frame_rate_type': 'line_rate',
        }
    }
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=stream)

    # 6.In case of nexthop_down scenario, simulate nexthop down by setting first rx_port to down state
    if tc_scenario == 'nexthop_down':
        out = await IpLink.set(
            input_data=[{dev_name: [
                {'device': dut_ports[1], 'operstate': 'down'}]}])
        err_msg = f"Verify that ports set to 'DOWN' state.\n{out}"
        assert not out[0][dev_name]['rc'], err_msg

    # 7.Transmit added stream for 15 sec
    await tgen_utils_clear_traffic_stats(tgen_dev)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(15)
    await tgen_utils_stop_traffic(tgen_dev)
    # Wait 15 sec for stats to be updated
    await asyncio.sleep(15)

    # 8.Verify traffic distributed through all expected nexthops
    stats = await tgen_utils_get_traffic_stats(tgen_dev)
    if tc_scenario == 'basic' or tc_scenario == 'dynamic':
        await verify_ecmp_distribution(stats, tg_ports[0], tg_ports[1:])
    elif tc_scenario == 'nexthop_down':
        await verify_ecmp_distribution(stats, tg_ports[0], tg_ports[2:])
        for row in stats.Rows:
            if row['Port Name'] == tg_ports[1]:
                assert int(row[RX_STATS]) <= DEVIATION_PKTS, ERR_MSG.format(row['Port Name'], row[RX_STATS])

        out = await IpLink.set(
            input_data=[{dev_name: [
                {'device': dut_ports[1], 'operstate': 'up'}]}])
        err_msg = f"Verify that ports set to 'UP' state.\n{out}"
        assert not out[0][dev_name]['rc'], err_msg


@pytest.mark.usefixtures('cleanup_bonds')
async def test_ecmp_distribution_lags(testbed):
    """
    Test Name: test_ecmp_distribution_lags
    Test Suite: suite_functional_ecmp
    Test Overview: Test Ecmp distribution between nexthops with ports in Lag
    Test Procedure:
    1. Add lag interfaces bond1 and bond2
    2. Configure last 3 ports down in order to enslave them to bond1 and bond2
    3. Add first rx_port to lag interface bond1 and last 2 rx_ports lag interface bond2
    4. Configure 1st dut_port and lag interfaces bond1 and bond2 up
    5. Configure IP addrs to 1st dut_port, bond1, bond2 interfaces
    6. Add static arp entries to bond1 and bond2
    7. Configure Ecmp route to 100.0.0.0/8 network with bond1 and bond2 as nexthops
    8. Setup ipv4 stream with incremented ip_dst addresses that would distribute through all nexthops
    9. Transmit added stream for 15 sec
    10. Verify traffic distributed through bond1 and bond2 as expected
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dev_name = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]
    dent_dev = dent_devices[0]
    bond1 = 'bond1'
    bond2 = 'bond2'

    # 1.Add lag interfaces bond1 and bond2
    out = await IpLink.add(
        input_data=[{dev_name: [
            {'name': bond1, 'type': 'bond', 'mode': '802.3ad'},
            {'name': bond2, 'type': 'bond', 'mode': '802.3ad'}]}])
    err_msg = f'Verify that {bond1} and {bond2} was successfully added. \n{out}'
    assert not out[0][dev_name]['rc'], err_msg

    # 2.Configure last 3 ports down in order to enslave them to bond1 and bond2
    out = await IpLink.set(
        input_data=[{dev_name: [
            {'device': port, 'operstate': 'down'} for port in dut_ports[1:]]}])
    err_msg = f"Verify that ports {dut_ports[1:]} set to 'DOWN' state.\n{out}"
    assert not out[0][dev_name]['rc'], err_msg

    # 3.Add first rx_port to lag interface bond1 and last 2 rx_ports lag interface bond2
    out = await IpLink.set(
        input_data=[{dev_name: [
            {'device': dut_ports[1], 'master': bond1},
            {'device': dut_ports[2], 'master': bond2},
            {'device': dut_ports[3], 'master': bond2}]}])
    err_msg = f'Verify that {dut_ports[0]} set to master .\n{out}'
    assert not out[0][dev_name]['rc'], err_msg

    # 4.Configure 1st dut_port and lag interfaces bond1 and bond2 up
    out = await IpLink.set(
        input_data=[{dev_name: [
            {'device': dev, 'operstate': 'up'} for dev in [dut_ports[0], bond1, bond2]]}])
    err_msg = f"Verify that ports {[dut_ports[0], bond1, bond2]} set to 'UP' state.\n{out}"
    assert not out[0][dev_name]['rc'], err_msg

    # 5.Configure IP addrs to 1st dut_port, bond1, bond2 interfaces
    dev_grp = (
        {'ixp': tg_ports[0], 'ip': '1.1.1.2', 'gw': '1.1.1.1', 'plen': 24},
        {'ixp': bond1, 'ip': '11.0.0.2', 'gw': '11.0.0.1', 'plen': 8, 'lag_members': [tg_ports[1]]},
        {'ixp': bond2, 'ip': '12.0.0.2', 'gw': '12.0.0.1', 'plen': 16, 'lag_members': tg_ports[2:]}
    )
    address_map = (
        # swp port,    tg port,     swp ip,    tg ip,     plen               lladdr
        (dut_ports[0], tg_ports[0], '1.1.1.1',  '1.1.1.2',  24, '00:00:00:00:00:10'),
        (bond1,        tg_ports[1], '11.0.0.1', '11.0.0.2', 8,  '00:AD:20:B2:A7:75'),
        (bond2,        tg_ports[2:], '12.0.0.1', '12.0.0.2', 16, '00:59:CD:1E:83:1B')
    )

    out = await IpAddress.add(input_data=[{dev_name: [
            {'dev': device, 'prefix': '{}/{}'.format(ip, plen)}
            for device, _, ip, _, plen, _ in address_map]}])
    assert not out[0][dev_name]['rc'], 'Failed to add IP addr to ports'

    dev_groups = tgen_utils_dev_groups_from_config(dev_grp)
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    # 6.Add static arp entries to bond1 and bond2
    out = await IpNeighbor.add(input_data=[{dev_name: [
        {'dev': device, 'address': tg_ip, 'lladdr': lladdr}
        for device, _, _, tg_ip, _, lladdr in address_map[1:]
    ]}])
    assert not out[0][dev_name]['rc'], 'Failed to add static arp entries'

    # 7.Configure Ecmp route to 100.0.0.0/8 network with bond1 and bond2 as nexthops
    out = await IpRoute.add(input_data=[{dev_name: [
        {'dst': '100.0.0.0/8', 'nexthop': [
            {'via': tg_ip, 'weight': 1} for _, _, _, tg_ip, _, _ in address_map[1:]]}
    ]}])
    assert not out[0][dev_name]['rc'], 'Failed to add nexthop'

    # 8.Setup ipv4 stream with incremented ip_dst addresses that would distribute through all nexthops
    swp_info = {}
    await tgen_utils_get_swp_info(dent_dev, dut_ports[0], swp_info)
    stream = {'increment_ip_dst_': {
        'type': 'raw',
        'protocol': 'ip',
        'ip_source': dev_groups[tg_ports[0]][0]['name'],
        'ip_destination': dev_groups[bond1][0]['name'],  # We dont care about ip_dst as we will use port stats
        'srcMac': random_mac(),
        'dstMac': swp_info['mac'],
        'srcIp': f'1.1.1.{randint(3, 100)}',
        'dstIp': {'type': 'increment',
                  'start': '100.0.0.1',
                  'step':  '0.0.0.1',
                  'count': 30},
        'frameSize': 200,
        'rate': 100,
        'frame_rate_type': 'line_rate',
        }
    }

    try:
        await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=stream)
    except AssertionError as e:
        if 'LAG' in str(e):
            pytest.skip(str(e))
        else:
            raise  # will re-raise the AssertionError

    # 9.Transmit added stream for 15 sec
    await tgen_utils_clear_traffic_stats(tgen_dev)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(15)
    await tgen_utils_stop_traffic(tgen_dev)
    # Wait 15 sec for stats to be updated
    await asyncio.sleep(15)

    # 10.Verify traffic distributed through bond1 and bond2 as expected
    stats = await tgen_utils_get_traffic_stats(tgen_dev)
    await verify_ecmp_distribution(stats, tg_ports[0], tg_ports[1:])
