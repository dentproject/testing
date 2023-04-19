import asyncio
import pytest
import time

from dent_os_testbed.lib.os.sysctl import Sysctl
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.ip.ip_neighbor import IpNeighbor

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_get_loss,
    tgen_utils_send_ping,
    tgen_utils_send_arp,
)

pytestmark = [
    pytest.mark.suite_functional_ipv4,
    pytest.mark.usefixtures('cleanup_ip_addrs', 'cleanup_tgen', 'enable_ipv4_forwarding'),
    pytest.mark.asyncio,
]


async def do_ping(dev, port, dst, count=1, interval=0.1, size=0, timeout=120):
    cmd = f'ping -I {port} -c {count} -i {interval} -s {size} -w {timeout} {dst}'
    cmd += ' | grep "ping statistics" -A 2'  # filter ouptut
    rc, out = await dev.run_cmd(cmd)
    assert rc == 0, f'Failed to send ping from {port} to {dst}'
    assert ' 0% ' in out, f'Some pings did not reach their destination\n{out}'


async def test_ipv4_icmp_disabled(testbed):
    """
    Test Name: test_ipv4_icmp_disabled
    Test Suite: suite_functional_ipv4
    Test Overview: Test IPv4 random routing
    Test Procedure:
    1. Init interfaces
    2. Configure ports up
    3. Configure IP addrs
    4. Enable ICMP echo ignoring
    5. Generate traffic and verify not getting ICMP response
    """
    # 1. Init interfaces
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]
    traffic_duration = 10
    icmp_ignore = 'net.ipv4.icmp_echo_ignore_all'
    address_map = (
        # swp port, tg port,    swp ip,    tg ip,     plen
        (ports[0], tg_ports[0], '1.1.1.1', '1.1.1.2', 24),
        (ports[1], tg_ports[1], '2.2.2.1', '2.2.2.2', 24),
        (ports[2], tg_ports[2], '3.3.3.1', '3.3.3.2', 24),
        (ports[3], tg_ports[3], '4.4.4.1', '4.4.4.2', 24),
    )

    # 2. Configure ports up
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up'}
        for port, *_ in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # 3. Configure IP addrs
    out = await IpAddress.add(input_data=[{dent: [
        {'dev': port, 'prefix': f'{ip}/{plen}'}
        for port, _, ip, _, plen in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': ip, 'gw': gw, 'plen': plen}
        for _, port, gw, ip, plen in address_map
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    # 4. Enable ICMP echo ignoring
    out = await Sysctl.get(input_data=[{dent: [
        {'variable': icmp_ignore, 'options': '-n'}
    ]}])
    assert out[0][dent]['rc'] == 0
    default_value = int(out[0][dent]['result'])

    out = await Sysctl.set(input_data=[{dent: [
        {'variable': icmp_ignore, 'value': '1'}
    ]}])
    assert out[0][dent]['rc'] == 0

    # 5. Generate traffic
    streams = {
        'ipv4': {'ip_source': dev_groups[tg_ports[0]][0]['name'],
                 'ip_destination': dev_groups[tg_ports[1]][0]['name']}
    }
    try:  # Make sure that the default value is restored

        await tgen_utils_setup_streams(tgen_dev, None, streams)

        await tgen_utils_start_traffic(tgen_dev)
        await asyncio.sleep(traffic_duration)
        await tgen_utils_stop_traffic(tgen_dev)

        stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
        for row in stats.Rows:
            loss = tgen_utils_get_loss(row)
            assert loss == 0, f'Expected loss: 0%, actual: {loss}%'

        # Verify not getting ICMP response
        out = await tgen_utils_send_ping(
            tgen_dev,
            ({'ixp': port, 'src_ip': src, 'dst_ip': dst}
             for _, port, dst, src, _ in address_map)
        )
        assert all(not status['success'] for status in out)
    finally:
        # Restore original value
        out = await Sysctl.set(input_data=[{dent: [
            {'variable': icmp_ignore, 'value': default_value}
        ]}])

    # Verify ICMP response working
    out = await tgen_utils_send_ping(
        tgen_dev,
        ({'ixp': port, 'src_ip': src, 'dst_ip': dst}
         for _, port, dst, src, _ in address_map)
    )
    assert all(status['success'] for status in out)


async def test_ipv4_ping_stability(testbed):
    """
    Test Name: test_ipv4_ping_stability
    Test Suite: suite_functional_ipv4
    Test Overview: Test IPv4 ping count
    Test Procedure:
    1. Init interfaces
    2. Configure ports up
    3. Configure IP addrs
    4. Add dynamic arp entries
    5. Send pings from 4 ports for 2 mins,
    6. Count how many packets did the device receive in total
    """
    # 1. Init interfaces
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]
    expected_rate_pps = 100
    deviation = .01  # +-1%
    address_map = (
        # swp port, tg port,    swp ip,    tg ip,     plen
        (ports[0], tg_ports[0], '1.1.1.1', '1.1.1.2', 24),
        (ports[1], tg_ports[1], '2.2.2.1', '2.2.2.2', 24),
        (ports[2], tg_ports[2], '3.3.3.1', '3.3.3.2', 24),
        (ports[3], tg_ports[3], '4.4.4.1', '4.4.4.2', 24),
    )

    # 2. Configure ports up
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up'}
        for port, *_ in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # 3. Configure IP addrs
    out = await IpAddress.add(input_data=[{dent: [
        {'dev': port, 'prefix': f'{ip}/{plen}'}
        for port, _, ip, _, plen in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': ip, 'gw': gw, 'plen': plen}
        for _, port, gw, ip, plen in address_map
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    # 4. Add dynamic arp entries
    streams = {
        'ipv4': {'ip_source': dev_groups[tg_ports[0]][0]['name'],
                 'ip_destination': dev_groups[tg_ports[1]][0]['name']}
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)  # will send arps to all ports

    # 5. Send pings from 4 ports for 2 mins
    cmd = 'ping -I {} -i 0.005 -w 120 {} | grep "bytes from" | wc -l'

    start_time_s = time.time()
    out = await asyncio.gather(*(dent_dev.run_cmd(cmd.format(port, dst))
                                 for port, *_, dst, _ in address_map))
    end_time_s = time.time()
    assert all(rc == 0 for rc, _ in out), f'Failed to send ping\n{out}'

    # 6. Count how many packets did the device receive in total
    pings_received = sum(int(recv) for _, recv in out)
    total_time = end_time_s - start_time_s
    actual_rate_pps = pings_received / total_time
    dent_dev.applog.info(f'Total run time: {total_time:.2f}s, pings received: {pings_received}')
    dent_dev.applog.info(f'Actual icmp rate: {actual_rate_pps:.2f}pps, expected: {expected_rate_pps}pps')
    assert expected_rate_pps * (1 - deviation) < actual_rate_pps < expected_rate_pps * (1 + deviation), \
        f'Expected rate: {expected_rate_pps}pps, actual: {actual_rate_pps:.2f}pps'


@pytest.mark.xfail(reason='Device does not support fragmentation')
async def test_ipv4_ping_size(testbed):
    """
    Test Name: test_ipv4_ping_size
    Test Suite: suite_functional_ipv4
    Test Overview: Test IPv4 ping size
    Test Procedure:
    1. Init interfaces
    2. Configure ports up
    3. Configure IP addrs
    4. Add dynamic arp entries
    5. Generate ping with size smaller than mru and larger than mru
       and verify fragmentation on the larger ping
    """
    # 1. Init interfaces
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]
    address_map = (
        # swp port, tg port,    swp ip,    tg ip,     plen
        (ports[0], tg_ports[0], '1.1.1.1', '1.1.1.2', 24),
        (ports[1], tg_ports[1], '2.2.2.1', '2.2.2.2', 24),
        (ports[2], tg_ports[2], '3.3.3.1', '3.3.3.2', 24),
        (ports[3], tg_ports[3], '4.4.4.1', '4.4.4.2', 24),
    )

    # 2. Configure ports up
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up'}
        for port, *_ in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # 3. Configure IP addrs
    out = await IpAddress.add(input_data=[{dent: [
        {'dev': port, 'prefix': f'{ip}/{plen}'}
        for port, _, ip, _, plen in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': ip, 'gw': gw, 'plen': plen}
        for _, port, gw, ip, plen in address_map
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    # 4. Add dynamic arp entries
    streams = {
        'ipv4': {'ip_source': dev_groups[tg_ports[0]][0]['name'],
                 'ip_destination': dev_groups[tg_ports[1]][0]['name']}
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)  # will send arps to all ports

    # 5. Generate ping with size smaller than mru
    await asyncio.gather(*(do_ping(dent_dev, port, dst, size=100, timeout=15)
                           for port, *_, dst, _ in address_map))

    # Generate ping with size larger than mru and verify fragmentation
    await asyncio.gather(*(do_ping(dent_dev, port, dst, size=1473, timeout=15)
                           for port, *_, dst, _ in address_map))


async def test_ipv4_ping_static_ip(testbed):
    """
    Test Name: test_ipv4_ping_static_ip
    Test Suite: suite_functional_ipv4
    Test Overview: Test IPv4 ping with static ip
    Test Procedure:
    1. Init interfaces
    2. Configure ports up
    3. Configure IP addrs
    4. Add dynamic arp entries
    5. Ping DUT port
    6. Ping the Ixia TG port
    """
    # 1. Init interfaces
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]
    address_map = (
        # swp port, tg port,    swp ip,    tg ip,     plen
        (ports[0], tg_ports[0], '1.1.1.1', '1.1.1.2', 24),
        (ports[1], tg_ports[1], '2.2.2.1', '2.2.2.2', 24),
        (ports[2], tg_ports[2], '3.3.3.1', '3.3.3.2', 24),
        (ports[3], tg_ports[3], '4.4.4.1', '4.4.4.2', 24),
    )

    # 2. Configure ports up
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up'}
        for port, *_ in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # 3. Configure IP addrs
    out = await IpAddress.add(input_data=[{dent: [
        {'dev': port, 'prefix': f'{ip}/{plen}'}
        for port, _, ip, _, plen in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': ip, 'gw': gw, 'plen': plen}
        for _, port, gw, ip, plen in address_map
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    # 4. Add dynamic arp entries
    streams = {
        'ipv4': {'ip_source': dev_groups[tg_ports[0]][0]['name'],
                 'ip_destination': dev_groups[tg_ports[1]][0]['name']}
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)  # will send arps to all ports

    # 5. Ping DUT port
    out = await tgen_utils_send_ping(tgen_dev, ({'ixp': port, 'dst_ip': dst}
                                                for _, port, dst, *_ in address_map))
    assert all(status['success'] for status in out)

    # 6. Ping the Ixia TG port
    await asyncio.gather(*(do_ping(dent_dev, port, dst)
                           for port, *_, dst, _ in address_map))


async def test_ipv4_fwd_disable(testbed):
    """
    Test Name: test_ipv4_fwd_disable
    Test Suite: suite_functional_ipv4
    Test Overview: Test IPv4 ping with static ip
    Test Procedure:
    1. Init interfaces
    2. Configure ports up
    3. Configure IP addrs
    4. Disable IPv4 forwarding
    6. Ping between Ixia ports
       Verify ping reply was received for ports 0, 3 because arp entry was resolved
       Verify no ping reply recieved for ports 1, 2 because ping requests haven't been fwd
    7. Enable IPv4 forwarding and flush all arp neighbors
    8. Ping between Ixia ports and verify replies
    """
    # 1. Init interfaces
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]
    ip_forward = 'net.ipv4.ip_forward'
    address_map = (
        # swp port, tg port,    swp ip,    tg ip,     plen
        (ports[0], tg_ports[0], '1.1.1.1', '1.1.1.2', 24),
        (ports[1], tg_ports[1], '2.2.2.1', '2.2.2.2', 24),
        (ports[2], tg_ports[2], '3.3.3.1', '3.3.3.2', 24),
        (ports[3], tg_ports[3], '4.4.4.1', '4.4.4.2', 24),
    )
    # map tg ports [0, 1, 2, 3] to tg ip [3, 2, 1, 0]
    peer_ip = {
        port: dst
        for ((_, port, *_,), (*_, dst, _)) in zip(address_map, reversed(address_map))
    }

    # 2. Configure ports up
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up'}
        for port, *_ in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # 3. Configure IP addrs
    out = await IpAddress.add(input_data=[{dent: [
        {'dev': port, 'prefix': f'{ip}/{plen}'}
        for port, _, ip, _, plen in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': ip, 'gw': gw, 'plen': plen}
        for _, port, gw, ip, plen in address_map
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    streams = {
        'ipv4': {'ip_source': dev_groups[tg_ports[0]][0]['name'],
                 'ip_destination': dev_groups[tg_ports[1]][0]['name']}
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # Flush neighbors because tgen_utils_setup_streams will by default
    # send arps to all ports
    out = await IpNeighbor.flush(input_data=[{dent: [
        {'device': port} for port in ports
    ]}])
    assert out[0][dent]['rc'] == 0

    # 4. Disable IPv4 forwarding
    out = await Sysctl.set(input_data=[{dent: [
        {'variable': ip_forward, 'value': 0}
    ]}])
    assert out[0][dent]['rc'] == 0

    # Send arp to first and last ports
    out = await tgen_utils_send_arp(tgen_dev, ({'ixp': tg_ports[0]},
                                               {'ixp': tg_ports[3]}))
    assert all(status['success'] for status in out)

    # 6. Ping between Ixia ports.
    #    Verify ping reply was received for ports 0, 3 because arp entry was resolved.
    #    Verify no ping reply recieved for ports 1, 2 because ping requests haven't been fwd.

    # Because of a device limitation when the arps are resolved (even when
    # forwarding is disabled) the ping between ports 0 and 3 will succeed,
    # but ping will fail between ports 1 and 2
    out = await tgen_utils_send_ping(
        tgen_dev,
        ({'ixp': port, 'dst_ip': peer_ip[port]}
         for port in tg_ports)
    )
    assert all(status['success'] for status in out if status['port'] in (tg_ports[0], tg_ports[3]))
    assert all(not status['success'] for status in out if status['port'] in (tg_ports[1], tg_ports[2]))

    # 7. Enable IPv4 forwarding
    out = await Sysctl.set(input_data=[{dent: [
        {'variable': ip_forward, 'value': 1}
    ]}])
    assert out[0][dent]['rc'] == 0

    # Flush all arp neighbors
    out = await IpNeighbor.flush(input_data=[{dent: [
        {'device': port} for port in ports
    ]}])
    assert out[0][dent]['rc'] == 0

    # 8. Ping between Ixia ports and verify replies
    out = await tgen_utils_send_ping(
        tgen_dev,
        ({'ixp': port, 'dst_ip': peer_ip[port]}
         for port in tg_ports)
    )
    assert all(status['success'] for status in out)
