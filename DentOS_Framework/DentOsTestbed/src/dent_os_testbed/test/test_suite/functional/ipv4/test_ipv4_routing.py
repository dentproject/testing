import asyncio
import pytest
import random

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_route import IpRoute
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.ip.ip_neighbor import IpNeighbor
from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan

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


def get_random_ip():
    ip = [random.randint(11, 126), random.randint(1, 254), random.randint(1, 254), random.randint(1, 253)]
    peer = ip[:-1] + [ip[-1] ^ 1]
    plen = random.randint(1, 31)
    return '.'.join(map(str, ip)), '.'.join(map(str, peer)), plen


async def test_ipv4_random_routing(testbed):
    """
    Test Name: test_ipv4_random_routing
    Test Suite: suite_functional_ipv4
    Test Overview: Test IPv4 random routing
    Test Procedure:
    1. Init interfaces
    2. Configure ports up
    3. Configure random IP addrs on all interfaces
    4. Generate traffic and verify reception
    """
    # 1. Init interfaces
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]
    traffic_duration = 10

    # 2. Configure ports up
    out = await IpLink.set(input_data=[{dent: [{'device': port, 'operstate': 'up'}
                                               for port in ports]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # 3. Configure random IP addrs on all interfaces
    address_map = (
        # swp port, tg port,    swp ip, tg ip, plen
        (ports[0], tg_ports[0], *get_random_ip()),
        (ports[1], tg_ports[1], *get_random_ip()),
        (ports[2], tg_ports[2], *get_random_ip()),
        (ports[3], tg_ports[3], *get_random_ip()),
    )

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

    # 4. Generate traffic and verify reception
    streams = {'ipv4': {
        'type': 'ipv4',
        'protocol': 'ip',
        'rate': '1000',  # pps
    }}

    await tgen_utils_setup_streams(tgen_dev, None, streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        assert loss == 0, f'Expected loss: 0%, actual: {loss}%'


async def test_ipv4_nexthop_route(testbed):
    """
    Test Name: test_ipv4_nexthop_route
    Test Suite: suite_functional_ipv4
    Test Overview: Test IPv4 nexthop routing
    Test Procedure:
    1. Init interfaces
    2. Configure ports up
    3. Configure IP addrs
    4. Add static arp entries
    5. Add routes nexthops
    6. Transmit traffic for routes and verify reception
    """
    # 1. Init interfaces
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]
    traffic_duration = 10

    # 2. Configure ports up
    out = await IpLink.set(input_data=[{dent: [{'device': port, 'operstate': 'up'}
                                               for port in ports]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # 3. Configure IP addrs
    address_map = (
        # swp port, tg port,    swp ip,    tg ip,     plen
        (ports[0], tg_ports[0], '1.1.1.1', '1.1.1.2', 24),
        (ports[1], tg_ports[1], '2.2.2.1', '2.2.2.2', 24),
    )

    out = await IpAddress.add(input_data=[{dent: [
        {'dev': port, 'prefix': f'{ip}/{plen}'}
        for port, _, ip, _, plen in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': ip, 'gw': gw, 'plen': plen}
        for _, port, gw, ip, plen in address_map
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports[:2], ports[:2], dev_groups)

    nei_address_map = (
        {'mac': 'aa:bb:cc:dd:ee:01', 'ip': '1.1.1.5', 'dst': '48.0.0.0'},
        {'mac': 'aa:bb:cc:dd:ee:02', 'ip': '2.2.2.5', 'dst': '16.0.0.0'},
    )

    # 4. Add static arp entries
    out = await IpNeighbor.add(input_data=[{dent: [
        {'dev': ports[0], 'address': nei_address_map[0]['ip'], 'lladdr': nei_address_map[0]['mac']},
        {'dev': ports[1], 'address': nei_address_map[1]['ip'], 'lladdr': nei_address_map[1]['mac']},
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add static arp entries'

    # 5. Add routes nexthops
    out = await IpRoute.add(input_data=[{dent: [
        {'dst': f"{nei_address_map[0]['dst']}/24", 'nexthop': [{'via': nei_address_map[0]['ip']}]},
        {'dst': f"{nei_address_map[1]['dst']}/24", 'nexthop': [{'via': nei_address_map[1]['ip']}]},
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add nexthop'

    # 6. Transmit traffic for routes and verify reception
    swp_info = {}
    await tgen_utils_get_swp_info(dent_dev, ports[0], swp_info)
    mac_port0 = swp_info['mac']

    await tgen_utils_get_swp_info(dent_dev, ports[1], swp_info)
    mac_port1 = swp_info['mac']

    streams = {
        f'{tg_ports[0]} -> {tg_ports[1]}': {
            'type': 'raw',
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'protocol': 'ip',
            'rate': '1000',  # pps
            'srcMac': nei_address_map[0]['mac'],
            'dstMac': mac_port0,
            'srcIp': address_map[0][3],
            'dstIp': nei_address_map[1]['dst'],
        },
        f'{tg_ports[1]} -> {tg_ports[0]}': {
            'type': 'raw',
            'ip_source': dev_groups[tg_ports[1]][0]['name'],
            'ip_destination': dev_groups[tg_ports[0]][0]['name'],
            'protocol': 'ip',
            'rate': '1000',  # pps
            'srcMac': nei_address_map[1]['mac'],
            'dstMac': mac_port1,
            'srcIp': address_map[1][3],
            'dstIp': nei_address_map[0]['dst'],
        },
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Traffic Item Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        assert loss == 0, f'Expected loss: 0%, actual: {loss}%'


@pytest.mark.usefixtures('cleanup_bridges')
async def test_ipv4_route_between_vlan_devs(testbed):
    """
    Test Name: test_ipv4_route_between_vlan_devs
    Test Suite: suite_functional_ipv4
    Test Overview: Test IPv4 route between vlan devices
    Test Procedure:
    1. Create a bridge entity
    2. Assign ports to bridge, add ports to VLAN, add bridge to VLANs, create VLAN-devices
    3. Set link up on all participant ports and VLAN-devices
    4. Configure ip address on VLAN-devices
    5. Verify offload flag appear in VLAN-devices default routes
    6. Prepare streams from one VLAN-device`s neighbor to the other
    7. Transmit Traffic
    8. Verify traffic is forwarded to both VLAN-devices` neighbors
    9. Remove IP address from VLAN-devices and re-configure; Send ARPs and transmit again
    10. Verify offload flag appear in VLAN-devices default routes
    11. Verify traffic is forwarded to both VLAN-devices` neighbors
    """
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0][:2]
    ports = tgen_dev.links_dict[dent][1][:2]
    traffic_duration = 10
    bridge = 'br0'
    vlan10 = f'{bridge}.10'
    vlan20 = f'{bridge}.20'

    address_map = (
        # swp port, vlan iface, tg port, swp ip,   tg ip,    plen, vid
        (ports[0], vlan10, tg_ports[0], '1.1.1.1', '1.1.1.2', 24,  10),
        (ports[1], vlan20, tg_ports[1], '2.2.2.1', '2.2.2.2', 24,  20),
    )

    # 1. Create a bridge entity
    out = await IpLink.add(input_data=[{dent: [
        {'device': bridge, 'type': 'bridge', 'vlan_filtering': 1, 'vlan_default_pvid': 0},
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create bridge'

    # 2. Assign ports to bridge
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'master': bridge} for port in ports
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to assign ports to bridge'

    # Add ports to VLAN, add bridge to VLANs
    out = await BridgeVlan.add(input_data=[{dent: [
        {'device': port, 'vid': vid}
        for port, *_, vid in address_map
    ] + [
        {'device': bridge, 'vid': vid, 'self': True}
        for *_, vid in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add vlan id to ports'

    # Create VLAN-devices
    out = await IpLink.add(input_data=[{dent: [
        {'link': bridge, 'name': vlan, 'type': f'vlan id {id}'}
        for _, vlan, *_, id in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create vlan interfaces'

    # 3. Set link up on all participant ports and VLAN-devices
    out = await IpLink.set(input_data=[{dent: [
        {'device': dev, 'operstate': 'up'}
        for dev in ports + [bridge, vlan10, vlan20]
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # 4. Configure ip address on VLAN-devices
    out = await IpAddress.add(input_data=[{dent: [
        {'dev': vlan, 'prefix': f'{ip}/{plen}'}
        for _, vlan, _, ip, _, plen, _ in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to vlans'

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': tg_port, 'ip': ip, 'gw': gw, 'plen': plen, 'vlan': vid}
        for _, _, tg_port, gw, ip, plen, vid in address_map
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    # 5. Verify offload flag appear in VLAN-devices default routes
    out = await IpRoute.show(input_data=[{dent: [
        {'cmd_options': '-j'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get list of route entries'

    for route in out[0][dent]['parsed_output']:
        if route.get('dev', None) in (vlan10, vlan20):
            assert 'rt_trap' in route['flags'], \
                f"Route {route['dst']} for dev {route['dev']} should be offloaded"

    # 6. Prepare streams from one VLAN-device`s neighbor to the other
    streams = {'traffic': {
        'type': 'ipv4',
        'protocol': 'ip',
        'rate': '1000',  # pps
    }}
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # 7. Transmit Traffic
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # 8. Verify traffic is forwarded to both VLAN-devices` neighbors
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        assert loss == 0, f'Expected loss: 0%, actual: {loss}%'

    # 9. Remove IP address from VLAN-devices
    out = await IpAddress.flush(input_data=[{dent: [
        {'dev': vlan} for _, vlan, *_ in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to flush IP addr from vlans'

    # Re-configure
    out = await IpAddress.add(input_data=[{dent: [
        {'dev': vlan, 'prefix': f'{ip}/{plen}'}
        for _, vlan, _, ip, _, plen, _ in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to vlans'

    # Transmit again
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # 10. Verify offload flag appear in VLAN-devices default routes
    out = await IpRoute.show(input_data=[{dent: [
        {'cmd_options': '-j'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get list of route entries'

    for route in out[0][dent]['parsed_output']:
        if route.get('dev', None) in (vlan10, vlan20):
            assert 'rt_trap' in route['flags'], \
                f"Route {route['dst']} for dev {route['dev']} should be offloaded"

    # 11. Verify traffic is forwarded to both VLAN-devices` neighbors
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        assert loss == 0, f'Expected loss: 0%, actual: {loss}%'


async def test_ipv4_nexthop_static_route(testbed):
    """
    Test Name: test_ipv4_nexthop_static_route
    Test Suite: suite_functional_ipv4
    Test Overview: Test IPv4 nexthop static routing
    Test Procedure:
    1. Init interfaces
    2. Configure ports up
    3. Configure IP addrs
    4. Add static routes
    5. Check added static routes
    7. Send Arp requests and generate traffic
    8. Check added arp entries
    9. Remove added static routes
    10. Check static routes have been removed
    11. Remove added dynamic arp entries
    12. Check dynamic arp entries have been removed
    """
    # 1. Init interfaces
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]
    traffic_duration = 10

    port_mac = {}
    for port in ports:
        swp_info = {}
        await tgen_utils_get_swp_info(dent_dev, port, swp_info)
        port_mac[port] = swp_info['mac']

    address_map = (
        # swp port, tg port,    swp ip,    tg ip,    plen, dst
        (ports[0], tg_ports[0], '1.1.1.1', '1.1.1.2', 24, '100.0.0.1', port_mac[ports[0]]),
        (ports[1], tg_ports[1], '2.2.2.1', '2.2.2.2', 24, '101.0.0.1', port_mac[ports[1]]),
        (ports[2], tg_ports[2], '3.3.3.1', '3.3.3.2', 24, '102.0.0.1', port_mac[ports[2]]),
        (ports[3], tg_ports[3], '4.4.4.1', '4.4.4.2', 24, '103.0.0.1', port_mac[ports[3]]),
    )
    nei_map = {
        # TODO add TG lladdr
        port: {'dst': nei_ip}
        for port, _, _, nei_ip, *_ in address_map
    }
    route_map = {
        port: {'gw': nei_ip, 'dst': dst}
        for port, _, _, nei_ip, _, dst, _ in address_map[:2]
    }

    # 2. Configure ports up
    out = await IpLink.set(input_data=[{dent: [{'device': port, 'operstate': 'up'}
                                               for port, *_ in address_map]}])
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

    streams = {
        f'{tg_ports[src]} -> {tg_ports[dst]}': {
            'type': 'raw',
            'ip_source': dev_groups[tg_ports[src]][0]['name'],
            'ip_destination': dev_groups[tg_ports[dst]][0]['name'],
            'protocol': 'ip',
            'rate': '1000',  # pps
            'srcMac': '02:00:00:00:00:01',
            'dstMac': address_map[dst][6],
            'srcIp': address_map[src][3],
            'dstIp': address_map[dst][5],
        } for src, dst in ((3, 0), (2, 1))
    }

    # 4. Add static routes
    out = await IpRoute.add(input_data=[{dent: [
        {'dev': port, 'dst': dst, 'nexthop': [{'via': nei_ip}]}
        for port, _, _, nei_ip, _, dst, _ in address_map[:2]
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add static routes'

    # 5. Check added static routes
    out = await IpRoute.show(input_data=[{dent: [
        {'cmd_options': '-j'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get list of routes'

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

    # 7. Send Arp requests and generate traffic
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # 8. Check added arp entries
    out = await IpNeighbor.show(input_data=[{dent: [
        {'cmd_options': '-j'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get list of arp entries'

    for nei in out[0][dent]['parsed_output']:
        if nei['dev'] not in ports:
            continue
        assert nei['dst'] == nei_map[nei['dev']]['dst'], \
            f"Expected {nei_map[nei['dev']]['dst']} for dev {nei['dev']}, not {nei['dst']}"
        assert 'offload' in nei, 'ARP entry should be offloaded'
        # TODO check correct mac addr
        # assert nei["lladdr"] == nei_map[nei["dev"]]["lladdr"], \
        #     f"Expected {nei_map[nei['dev']]['lladdr']} for dev {nei['dev']}, not {nei['lladdr']}"

    # 9. Remove added static routes
    out = await IpRoute.delete(input_data=[{dent: [
        {'dev': port, 'dst': route['dst']}
        for port, route in route_map.items()
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to delete arp entries'

    # 10. Check static routes have been removed
    out = await IpRoute.show(input_data=[{dent: [
        {'cmd_options': '-j'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get list of routes'

    for ro in out[0][dent]['parsed_output']:
        if 'gateway' not in ro:
            continue
        assert ro.get('dev', None) not in ports

    # 11. Remove added dynamic arp entries
    out = await IpNeighbor.delete(input_data=[{dent: [
        {'dev': port, 'address': nei['dst']}
        for port, nei in nei_map.items()
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to delete arp entries'

    # 12. Check dynamic arp entries have been removed
    out = await IpNeighbor.show(input_data=[{dent: [
        {'cmd_options': '-j'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get list of arp entries'
    for nei in out[0][dent]['parsed_output']:
        if nei['dev'] not in ports:
            continue
        assert 'FAILED' in nei['state'], 'ARP entry should be removed'


async def test_ipv4_two_routes_to_same_net(testbed):
    """
    Test Name: test_ipv4_two_routes_to_same_net
    Test Suite: suite_functional_ipv4
    Test Overview: Test IPv4 two routes to same network
    Test Procedure:
    1. Set link up on all participant ports
    2. Configure ip addresses, and configure route to the same network as the network configured
       in second port connected to Ixia via neighbor of the first port connected to Ixia
    3. Verify offload flag appear in the directly connected route of the second port connected to Ixia
    4. Resolve neighborship and prepare continuous stream with SIP of first Ixia port neighbor and DIP of second Ixia port neighbor
    5. Transmit traffic
    6. Verify traffic is not forwarded to second Ixia port neighbor
    7. Remove IP address from the second port connected to Ixia
    8. Verify offload flag appear in the next-hop static route via neighbor of the first port connected to Ixia
    9. Verify traffic is forwarded to first Ixia port neighbor
    """
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[dent][0][:2]
    ports = tgen_dev.links_dict[dent][1][:2]
    tx_port, rx_port = tg_ports
    traffic_duration = 10
    address_map = (
        # swp port, tg port,    swp ip,    tg ip,    plen
        (ports[0], tx_port, '1.1.1.1', '1.1.1.2', 24),
        (ports[1], rx_port, '2.2.2.1', '2.2.2.2', 24),
    )
    common_net_ip = f'{address_map[1][3][:-2]}.0/{address_map[1][-1]}'  # 2.2.2.0/24

    # 1. Set link up on all participant ports
    out = await IpLink.set(input_data=[{dent: [{'device': port, 'operstate': 'up'}
                                               for port, *_ in address_map]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # 2. Configure ip addresses
    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': ip, 'gw': gw, 'plen': plen}
        for _, port, gw, ip, plen in address_map
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    out = await IpAddress.add(input_data=[{dent: [
        {'dev': port, 'prefix': f'{ip}/{plen}'}
        for port, _, ip, _, plen in address_map[:1]  # first port
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    # Configure route to the same network as the network configured in second
    # port connected to Ixia via neighbor of the first port connected to Ixia
    out = await IpRoute.add(input_data=[{dent: [
        {'dev': port, 'dst': common_net_ip, 'nexthop': [{'via': ip}]}
        for port, _, _, ip, _ in address_map[:1]  # src ip of first tg port
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add route'

    out = await IpAddress.add(input_data=[{dent: [
        {'dev': port, 'prefix': f'{ip}/{plen}'}
        for port, _, ip, _, plen in address_map[1:]  # second port
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    # 3. Verify offload flag appear in the directly connected route of the second port connected to Ixia
    out = await IpRoute.show(input_data=[{dent: [{'cmd_options': '-j'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get list of routes'

    for ro in out[0][dent]['parsed_output']:
        if 'dst' not in ro or ro['dst'] != common_net_ip:
            continue
        if ro['dev'] == ports[0]:
            assert ro['gateway'] == address_map[0][3], f'Expected gateway to be {address_map[0][3]}'
            assert 'rt_offload' in ro['flags'], 'Route should be offloaded'
        else:
            assert 'rt_offload' not in ro['flags'], 'Route should not be offloaded'

    # 4. Resolve neighborship and prepare continuous stream with SIP of first Ixia port neighbor and DIP of second Ixia port neighbor
    streams = {f'{tx_port} -> {rx_port}': {
        'type': 'ipv4',
        'ip_source': dev_groups[tx_port][0]['name'],
        'ip_destination': dev_groups[rx_port][0]['name'],
        'rate': 1000,  # pps
    }}
    await tgen_utils_setup_streams(
        tgen_dev,
        f'/tmp/{tgen_dev.host_name}/tgen_ipv4_two_routes_to_same_net_config.ixncfg',
        streams,
        force_update=False,
    )

    # 5. Transmit traffic
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    # Don't stop

    # 6. Verify traffic is not forwarded to second Ixia port neighbor
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Traffic Item Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        assert loss == 100, f'Expected loss: 100%, actual: {loss}%'

    # 7. Remove IP address from the second port connected to Ixia
    out = await IpAddress.delete(input_data=[{dent: [
        {'dev': port, 'prefix': f'{ip}/{plen}'}
        for port, _, ip, _, plen in address_map[1:]  # second port
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    out = await IpRoute.show(input_data=[{dent: [{'cmd_options': '-j'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get list of routes'

    for ro in out[0][dent]['parsed_output']:
        if 'dst' not in ro or ro['dst'] != common_net_ip:
            continue
        assert ro['gateway'] == address_map[0][3], f'Expected gateway to be {address_map[0][3]}'
        assert 'rt_offload' in ro['flags'], 'Route should be offloaded'
        assert 'offload' in ro['flags'], 'Route should be offloaded'
        break
    else:
        raise LookupError(f'Expected to find route {common_net_ip} via {address_map[0][3]}' +
                          f"\n{out[0][dent]['parsed_output']}")

    # 9. Verify traffic is forwarded to first Ixia port neighbor
    await asyncio.sleep(traffic_duration)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Port Statistics')
    for row in stats.Rows:
        if row['Port Name'] == tx_port:
            tx = int(row['Frames Tx.'])
            rx = int(row['Valid Frames Rx.'])
            tol = 5
            # Allow a tolerance of +- 5 packets
            assert tx - tol < rx < tx + tol, \
                'Traffic should be forwarded to origin port'
