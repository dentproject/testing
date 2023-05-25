import asyncio
import pytest

from dent_os_testbed.lib.os.sysctl import Sysctl
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_route import IpRoute
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.ip.ip_neighbor import IpNeighbor

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_get_swp_info,
    tgen_utils_stop_traffic,
    tgen_utils_get_loss,
)

pytestmark = [
    pytest.mark.suite_functional_ipv4,
    pytest.mark.usefixtures('cleanup_ip_addrs', 'cleanup_tgen', 'enable_ipv4_forwarding'),
    pytest.mark.asyncio,
]


async def get_neigh_list(dent):
    out = await IpNeighbor.show(input_data=[{dent: [
        {'cmd_options': '-j'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get list of arp entries'
    return out[0][dent]['parsed_output']


async def configure_traffic(tgen_dev, dev_groups, tg_ports):
    streams = {
        f'{tg1} <-> {tg2}': {
            'type': 'ipv4',
            'ip_source': dev_groups[tg1][0]['name'],
            'ip_destination': dev_groups[tg2][0]['name'],
            'protocol': 'ip',
            'rate': '1000',  # pps
            'bi_directional': True,
        } for tg1, tg2 in ((tg_ports[0], tg_ports[1]), (tg_ports[2], tg_ports[3]))
    }

    await tgen_utils_setup_streams(tgen_dev, None, streams)


async def send_traffic_and_verify(tgen_dev, traffic_duration=10):
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Traffic Item Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        assert loss == 0, f'Expected loss: 0%, actual: {loss}%'


async def verify_dyn_arps_added(dent, ports, port_nei_map):
    neighs = await get_neigh_list(dent)
    for nei in neighs:
        if nei['dev'] not in ports:
            continue
        assert nei['dst'] == port_nei_map[nei['dev']]['dst'], \
            f"Expected {port_nei_map[nei['dev']]['dst']} for dev {nei['dev']}, not {nei['dst']}"
        assert 'offload' in nei, 'ARP entry should be offloaded'
        # TODO check correct mac addr
        # assert nei["lladdr"] == port_nei_map[nei["dev"]]["lladdr"], \
        #     f"Expected {port_nei_map[nei['dev']]['lladdr']} for dev {nei['dev']}, not {nei['lladdr']}"


async def verify_stat_arps_added(dent, ports, port_nei_map):
    neighs = await get_neigh_list(dent)
    for nei in neighs:
        if nei['dev'] not in ports:
            continue
        assert nei['dst'] == port_nei_map[nei['dev']]['dst'], \
            f"Expected {port_nei_map[nei['dev']]['dst']} for dev {nei['dev']}, not {nei['dst']}"
        assert nei['lladdr'] == port_nei_map[nei['dev']]['static_lladdr'], \
            f"Expected {port_nei_map[nei['dev']]['static_lladdr']} for dev {nei['dev']}, not {nei['lladdr']}"
        assert 'PERMANENT' in nei['state'], 'ARP entry should be PERMANENT'
        assert 'offload' in nei, 'ARP entry should be offloaded'


async def remove_arp_entries_and_verify(dent, ports):
    neighs = await get_neigh_list(dent)
    out = await IpNeighbor.delete(input_data=[{dent: [
        {'dev': nei['dev'], 'address': nei['dst']}
        for nei in neighs if nei['dev'] in ports
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to delete arp entries'

    # Due to a limitation need to delete arp entries twice
    out = await IpNeighbor.delete(input_data=[{dent: [
        {'dev': nei['dev'], 'address': nei['dst']}
        for nei in neighs if nei['dev'] in ports
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to delete arp entries'

    neighs = await get_neigh_list(dent)
    for nei in neighs:
        assert nei['dev'] not in ports, 'Port should not have any ARP entries'


async def test_ipv4_dynamic_arp(testbed):
    """
    Test Name: test_ipv4_dynamic_arp
    Test Suite: suite_functional_ipv4
    Test Overview: Test adding dynamic entry to arp table
    Test Procedure:
    1. Init interfaces
    2. Configure ports up
    3. Configure IP addrs
    4. Add dynamic arp entries and generate traffic and verify reception
    5. Check added arp entries
    6. Remove added arp entries
    7. Check arp entries have been removed
    """
    # 1. Init interfaces
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]
    address_map = (
        # swp port, tg port,    swp ip,    tg ip,     plen
        (ports[0], tg_ports[0], '1.1.1.1', '1.1.1.2', 24),
        (ports[1], tg_ports[1], '2.2.2.1', '2.2.2.2', 24),
        (ports[2], tg_ports[2], '3.3.3.1', '3.3.3.2', 24),
        (ports[3], tg_ports[3], '4.4.4.1', '4.4.4.2', 24),
    )
    port_nei_map = {
        # TODO add tg lladdr
        port: {'dst': nei_ip}
        for port, _, _, nei_ip, _ in address_map
    }

    # 2. Configure ports up
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up'}
        for port, *_, in address_map
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

    # 4. Add dynamic arp entries and generate traffic
    await configure_traffic(tgen_dev, dev_groups, tg_ports)

    # Verify reception
    await send_traffic_and_verify(tgen_dev)

    # 5. Check added arp entries
    await verify_dyn_arps_added(dent, ports, port_nei_map)

    # 6. Remove added arp entries
    # 7. Check arp entries have been removed
    await remove_arp_entries_and_verify(dent, ports)


async def test_ipv4_static_arp(testbed):
    """
    Test Name: test_ipv4_static_arp
    Test Suite: suite_functional_ipv4
    Test Overview: Test adding static entry to arp table
    Test Procedure:
    1. Init interfaces
    2. Configure ports up
    3. Configure IP addrs
    4. Add static arp entries
    5. Check added arp entries
    6. Remove added arp entries
    7. Check arp entries have been removed
    """
    # 1. Init interfaces
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent = dent_devices[0].host_name
    ports = tgen_dev.links_dict[dent][1]
    address_map = (
        # swp port, swp ip,   nei ip,   plen, nei mac
        (ports[0], '1.1.1.1', '1.1.1.2', 24, '02:00:00:00:00:01'),
        (ports[1], '2.2.2.1', '2.2.2.2', 24, '02:00:00:00:00:02'),
        (ports[2], '3.3.3.1', '3.3.3.2', 24, '02:00:00:00:00:03'),
        (ports[3], '4.4.4.1', '4.4.4.2', 24, '02:00:00:00:00:04'),
    )
    port_nei_map = {
        port: {'dst': nei_ip, 'static_lladdr': lladdr}
        for port, _, nei_ip, _, lladdr in address_map
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
        for port, ip, _, plen, _ in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    # 4. Add static arp entries
    out = await IpNeighbor.add(input_data=[{dent: [
        {'dev': port, 'address': nei_ip, 'lladdr': lladdr}
        for port, _, nei_ip, _, lladdr in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add static arp entries'

    # 5. Check added arp entries
    await verify_stat_arps_added(dent, ports, port_nei_map)

    # 6. Remove added arp entries
    # 7. Check arp entries have been removed
    await remove_arp_entries_and_verify(dent, ports)


async def test_ipv4_replace_dyn_stat_arp(testbed):
    """
    Test Name: test_ipv4_replace_dyn_stat_arp
    Test Suite: suite_functional_ipv4
    Test Overview: Test replacing dynamic entry with static entry in arp table
    Test Procedure:
    1. Init interfaces
    2. Configure ports up
    3. Configure IP addrs
    4. Add static arp entries, check added arp entries
    5. Remove added arp entries, check arp entries have been removed
    6. Add dynamic arp entries, Check added arp entries
    7. Remove added arp entries, check arp entries have been removed
    8. Add static arp entries, check added arp entries
    9. Remove added arp entries, check arp entries have been removed
    """
    # 1. Init interfaces
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]
    address_map = (
        # swp port, tg port,    swp ip,    tg ip,    plen, static lladdr
        (ports[0], tg_ports[0], '1.1.1.1', '1.1.1.2', 24, '02:00:00:00:00:01'),
        (ports[1], tg_ports[1], '2.2.2.1', '2.2.2.2', 24, '02:00:00:00:00:02'),
        (ports[2], tg_ports[2], '3.3.3.1', '3.3.3.2', 24, '02:00:00:00:00:03'),
        (ports[3], tg_ports[3], '4.4.4.1', '4.4.4.2', 24, '02:00:00:00:00:04'),
    )
    port_nei_map = {
        # TODO add tg lladdr
        port: {'dst': nei_ip, 'static_lladdr': lladdr}
        for port, _, _, nei_ip, _, lladdr in address_map
    }

    # 2. Configure ports up
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up'} for port, *_ in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # 3. Configure IP addrs
    out = await IpAddress.add(input_data=[{dent: [
        {'dev': port, 'prefix': f'{ip}/{plen}'}
        for port, _, ip, _, plen, _ in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': ip, 'gw': gw, 'plen': plen}
        for _, port, gw, ip, plen, _ in address_map
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    # 4. Add static arp entries
    out = await IpNeighbor.add(input_data=[{dent: [
        {'dev': port, 'address': nei_ip, 'lladdr': lladdr}
        for port, _, _, nei_ip, _, lladdr in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add static arp entries'

    # Check added arp entries
    await verify_stat_arps_added(dent, ports, port_nei_map)

    # 5. Remove added arp entries, check arp entries have been removed
    await remove_arp_entries_and_verify(dent, ports)

    # 6. Add dynamic arp entries
    await configure_traffic(tgen_dev, dev_groups, tg_ports)
    await send_traffic_and_verify(tgen_dev)

    # Check added arp entries
    await verify_dyn_arps_added(dent, ports, port_nei_map)

    # 7. Remove added arp entries, check arp entries have been removed
    await remove_arp_entries_and_verify(dent, ports)

    # 8. Add static arp entries
    out = await IpNeighbor.add(input_data=[{dent: [
        {'dev': port, 'address': nei_ip, 'lladdr': lladdr}
        for port, _, _, nei_ip, _, lladdr in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add static arp entries'

    # Check added arp entries
    await verify_stat_arps_added(dent, ports, port_nei_map)

    # 9. Remove added arp entries, check arp entries have been removed
    await remove_arp_entries_and_verify(dent, ports)


async def test_ipv4_static_arp_with_traffic(testbed):
    """
    Test Name: test_ipv4_static_arp_with_traffic
    Test Suite: suite_functional_ipv4
    Test Overview: Test traffic with static arps
    Test Procedure:
    1. Init interfaces
    2. Configure ports up
    3. Configure IP addrs
    4. Add static arp entries
    5. Check added arp entries
    6. Generate traffic and verify reception
    7. Remove added arp entries
    8. Check arp entries have been removed
    """
    # 1. Init interfaces
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]
    address_map = (
        # swp port, tg ports,   swp ip,    nei ip,   plen, nei mac
        (ports[0], tg_ports[0], '1.1.1.1', '1.1.1.2', 24, '02:00:00:00:00:01'),
        (ports[1], tg_ports[1], '2.2.2.1', '2.2.2.2', 24, '02:00:00:00:00:02'),
        (ports[2], tg_ports[2], '3.3.3.1', '3.3.3.2', 24, '02:00:00:00:00:03'),
        (ports[3], tg_ports[3], '4.4.4.1', '4.4.4.2', 24, '02:00:00:00:00:04'),
    )
    port_nei_map = {
        port: {'dst': nei_ip, 'static_lladdr': lladdr}
        for port, _, _, nei_ip, _, lladdr in address_map
    }

    # 2. Configure ports up
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up'} for port, *_ in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # 3. Configure IP addrs
    out = await IpAddress.add(input_data=[{dent: [
        {'dev': port, 'prefix': f'{ip}/{plen}'}
        for port, _, ip, _, plen, _ in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': ip, 'gw': gw, 'plen': plen}
        for _, port, gw, ip, plen, _ in address_map
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    # 4. Add static arp entries
    out = await IpNeighbor.add(input_data=[{dent: [
        {'dev': port, 'address': nei_ip, 'lladdr': lladdr}
        for port, _, _, nei_ip, _, lladdr in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add static arp entries'

    # 5. Check added arp entries
    await verify_stat_arps_added(dent, ports, port_nei_map)

    # 6. Generate traffic
    await configure_traffic(tgen_dev, dev_groups, tg_ports)

    # Verify reception
    await send_traffic_and_verify(tgen_dev)

    # 7. Remove added arp entries
    # 8. Check arp entries have been removed
    await remove_arp_entries_and_verify(dent, ports)


async def test_ipv4_static_route_over_static_arp(testbed):
    """
    Test Name: test_ipv4_static_route_over_static_arp
    Test Suite: suite_functional_ipv4
    Test Overview: Test traffic with static routes over static arp
    Test Procedure:
    1. Init interfaces
    2. Configure ports up
    3. Configure IP addrs
    4. Add static arp entries, check added arp entries
    5. Add static routes, check added static routes
    6. Generate traffic and verify traffic reception
    7. Check added dynamic arp entries
    8. Remove added static routes, check static routes have been removed
    9. Remove added static arp entries, check static arp entries have been removed
    10. Remove added dynamic arp entries, check dynamic arp entries have been removed
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
        # swp port, tg ports,   swp ip,    nei ip,   plen, nei mac,            route
        (ports[0], tg_ports[0], '1.1.1.1', '1.1.1.2', 24, '02:00:00:00:00:01', '20.0.0.1'),
        (ports[1], tg_ports[1], '2.2.2.1', '2.2.2.2', 24, '02:00:00:00:00:02', '21.0.0.1'),
        (ports[2], tg_ports[2], '3.3.3.1', '3.3.3.2', 24, '02:00:00:00:00:03', '22.0.0.1'),
        (ports[3], tg_ports[3], '4.4.4.1', '4.4.4.2', 24, '02:00:00:00:00:04', '23.0.0.1'),
    )
    port_nei_map = {
        port: {'dst': nei_ip, 'static_lladdr': lladdr}
        for port, _, _, nei_ip, _, lladdr, _ in address_map
    }

    # 2. Configure ports up
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up'} for port, *_ in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # 3. Configure IP addrs
    out = await IpAddress.add(input_data=[{dent: [
        {'dev': port, 'prefix': f'{ip}/{plen}'}
        for port, _, ip, _, plen, *_ in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': ip, 'gw': gw, 'plen': plen}
        for _, port, gw, ip, plen, *_ in address_map
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    swp_info = {}
    await tgen_utils_get_swp_info(dent_dev, ports[0], swp_info)
    mac_port0 = swp_info['mac']
    await tgen_utils_get_swp_info(dent_dev, ports[1], swp_info)
    mac_port1 = swp_info['mac']

    streams = {
        f'{tg_ports[0]} -> {address_map[1][6]}': {
            'type': 'raw',
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcIp': dev_groups[tg_ports[0]][0]['ip'],
            'dstIp': address_map[1][6],
            'srcMac': address_map[0][5],
            'dstMac': mac_port0,
            'protocol': 'ip',
            'rate': '1000',  # pps
        },
        f'{tg_ports[1]} -> {address_map[0][6]}': {
            'type': 'raw',
            'ip_source': dev_groups[tg_ports[1]][0]['name'],
            'ip_destination': dev_groups[tg_ports[0]][0]['name'],
            'srcIp': dev_groups[tg_ports[1]][0]['ip'],
            'dstIp': address_map[0][6],
            'srcMac': address_map[1][5],
            'dstMac': mac_port1,
            'protocol': 'ip',
            'rate': '1000',  # pps
        },
        f'{tg_ports[2]} <-> {tg_ports[3]}': {
            'type': 'ipv4',
            'ip_source': dev_groups[tg_ports[2]][0]['name'],
            'ip_destination': dev_groups[tg_ports[3]][0]['name'],
            'protocol': 'ip',
            'rate': '1000',  # pps
            'bi_directional': True,
        },
    }

    # 4. Add static arp entries
    out = await IpNeighbor.add(input_data=[{dent: [
        {'dev': port, 'address': nei_ip, 'lladdr': lladdr}
        for port, _, _, nei_ip, _, lladdr, _ in address_map[:2]
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add static arp entries'

    # Check added arp entries
    await verify_stat_arps_added(dent, ports[:2], port_nei_map)

    # 5. Add static routes
    out = await IpRoute.add(input_data=[{dent: [
        {'dev': port, 'dst': dst, 'nexthop': [{'via': nei_ip}]}
        for port, _, _, nei_ip, _, _, dst in address_map[:2]
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add static routes'

    # Check added static routes
    out = await IpRoute.show(input_data=[{dent: [
        {'cmd_options': '-j'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get list of routes'

    route_map = {
        port: {'gw': nei_ip, 'dst': dst}
        for port, _, _, nei_ip, _, _, dst in address_map[:2]
    }
    for ro in out[0][dent]['parsed_output']:
        if ro.get('dev', None) not in ports[:2]:
            continue
        if 'gateway' not in ro:
            continue
        assert ro['dst'] == route_map[ro['dev']]['dst'], \
            f"Expected {route_map[ro['dev']]['dst']} for dev {ro['dev']}, not {ro['dst']}"
        assert ro['gateway'] == route_map[ro['dev']]['gw'], \
            f"Expected {route_map[ro['dev']]['gw']} for dev {ro['dev']}, not {ro['gateway']}"
        assert 'rt_offload' in ro['flags'], 'Route entry should be offloaded'

    # 6. Generate traffic
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # Verify reception
    await send_traffic_and_verify(tgen_dev)

    # 7. Check added dynamic arp entries
    await verify_dyn_arps_added(dent, ports[2:], port_nei_map)

    # 8. Remove added static routes
    out = await IpRoute.delete(input_data=[{dent: [
        {'dev': port, 'dst': dst, 'nexthop': [{'via': nei_ip}]}
        for port, _, _, nei_ip, _, _, dst in address_map[:2]
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to remove static routes'

    # Check static routes have been removed
    out = await IpRoute.show(input_data=[{dent: [
        {'cmd_options': '-j'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get list of routes'

    for ro in out[0][dent]['parsed_output']:
        if ro.get('dev', None) not in ports[:2]:
            continue
        assert ro['dst'] != route_map[ro['dev']]['dst'], \
            f"dev {ro['dev']} should have only default routes"

    # 9. Remove added static arp entries, check static arp entries have been removed
    # 10. Remove added dynamic arp entries, check dynamic arp entries have been removed
    await remove_arp_entries_and_verify(dent, ports)


async def test_ipv4_arp_reachable_timeout(testbed):
    """
    Test Name: test_ipv4_arp_reachable_timeout
    Test Suite: suite_functional_ipv4
    Test Overview: Test IPv4 arp timeout
    Test Procedure:
    1. Init interfaces
    2. Configure ports up
    3. Configure IP addrs
    4. Configure arp base reachable timeout to 1 sec
    5. Transmit traffic and verify ports are not in REACHABLE mode
    6. Configure arp base reachable timeout back to default 30 sec
    7. Send traffic again and verify ports are in REACHABLE mode
    """
    # 1. Init interfaces
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]
    reachable = 'REACHABLE'
    nei_update_time_s = 5
    address_map = (
        # swp port, tg ports,   swp ip,    tg ip,     plen
        (ports[0], tg_ports[0], '1.1.1.1', '1.1.1.2', 24),
        (ports[1], tg_ports[1], '2.2.2.1', '2.2.2.2', 24),
        (ports[2], tg_ports[2], '3.3.3.1', '3.3.3.2', 24),
        (ports[3], tg_ports[3], '4.4.4.1', '4.4.4.2', 24),
    )
    config = {
        f'net.ipv4.neigh.{port}.base_reachable_time_ms': 1000
        for port, *_ in address_map
    }

    # 2. Configure ports up
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up'} for port, *_ in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # 3. Configure IP addrs
    out = await IpAddress.add(input_data=[{dent: [
        {'dev': port, 'prefix': f'{ip}/{plen}'}
        for port, _, ip, _, plen, *_ in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': ip, 'gw': gw, 'plen': plen}
        for _, port, gw, ip, plen, *_ in address_map
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    # 4. Configure arp base reachable timeout to 1 sec
    out = await Sysctl.get(input_data=[{dent: [
        {'variable': key} for key in config.keys()
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get port base reachable time'
    def_values = out[0][dent]['parsed_output']

    out = await Sysctl.set(input_data=[{dent: [
        {'variable': key, 'value': value} for key, value in config.items()
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port base reachable time'

    try:  # Make sure that reachable time is restored even if the test fails

        # 5. Transmit traffic
        await configure_traffic(tgen_dev, dev_groups, tg_ports)
        await send_traffic_and_verify(tgen_dev)

        # Verify ports are not in REACHABLE mode
        await asyncio.sleep(nei_update_time_s)
        neighs = await get_neigh_list(dent)
        for nei in neighs:
            if nei['dev'] not in ports:
                continue
            assert reachable not in nei['state'], f'Arp entry should be aged {nei}'

    finally:
        # 6. Configure arp base reachable timeout back to default 30 sec
        out = await Sysctl.set(input_data=[{dent: [
            {'variable': key, 'value': value}
            for key, value in def_values.items()
        ]}])
        assert out[0][dent]['rc'] == 0, 'Failed to set port base reachable time'

    # 7. Send traffic again
    await send_traffic_and_verify(tgen_dev)

    # Wait a few seconds to be sure that arp state is updated
    await asyncio.sleep(nei_update_time_s)

    # Verify ports are in REACHABLE mode
    neighs = await get_neigh_list(dent)
    for nei in neighs:
        if nei['dev'] not in ports:
            continue
        assert reachable in nei['state'], f'Arp entry should be reachable {nei}'


async def test_ipv4_arp_ageing(testbed):
    """
    Test Name: test_ipv4_arp_ageing
    Test Suite: suite_functional_ipv4
    Test Overview: Test IPv4 arp aging
    Test Procedure:
    1. Init interfaces
    2. Configure ports up
    3. Configure IP addrs
    4. Configure ARP table min entries to 0 in order to make gc run
    5. Configure arp aging gc_stale timeout to 1 sec
    6. Generate traffic and verify arp entries don't exist
    """
    # 1. Init interfaces
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]
    config = {
        'net.ipv4.neigh.default.gc_thresh1': 0,
        'net.ipv4.neigh.default.gc_stale_time': 1,
    }
    address_map = (
        # swp port, tg ports,   swp ip,    tg ip,     plen
        (ports[0], tg_ports[0], '1.1.1.1', '1.1.1.2', 24),
        (ports[1], tg_ports[1], '2.2.2.1', '2.2.2.2', 24),
        (ports[2], tg_ports[2], '3.3.3.1', '3.3.3.2', 24),
        (ports[3], tg_ports[3], '4.4.4.1', '4.4.4.2', 24),
    )

    # 2. Configure ports up
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up'} for port, *_ in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # 3. Configure IP addrs
    out = await IpAddress.add(input_data=[{dent: [
        {'dev': port, 'prefix': f'{ip}/{plen}'}
        for port, _, ip, _, plen, *_ in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': ip, 'gw': gw, 'plen': plen}
        for _, port, gw, ip, plen, *_ in address_map
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    # Get default values to restore them later
    out = await Sysctl.get(input_data=[{dent: [
        {'variable': key} for key in config.keys()
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get port base reachable time'
    def_values = out[0][dent]['parsed_output']

    # 4. Configure ARP table min entries to 0 in order to make gc run
    # 5. Configure arp aging gc_stale timeout to 1 sec
    out = await Sysctl.set(input_data=[{dent: [
        {'variable': key, 'value': value} for key, value in config.items()
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to get port base reachable time'

    try:  # Make sure that default values are restored even if the test fails

        # 6. Generate traffic
        await configure_traffic(tgen_dev, dev_groups, tg_ports)
        await send_traffic_and_verify(tgen_dev)

        # Wait for the entries to age
        await asyncio.sleep(90)

        # Verify arp entries don't exist
        neighs = await get_neigh_list(dent)
        for nei in neighs:
            assert nei['dev'] not in ports, f'Did not expect arp entry {nei}'

    finally:
        # Restore default values
        out = await Sysctl.set(input_data=[{dent: [
            {'variable': key, 'value': value}
            for key, value in def_values.items()
        ]}])
        assert out[0][dent]['rc'] == 0, 'Failed to get port base reachable time'
