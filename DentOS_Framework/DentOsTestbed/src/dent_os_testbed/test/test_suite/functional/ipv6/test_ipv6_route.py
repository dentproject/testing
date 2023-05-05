from collections import namedtuple
import asyncio
import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_route import IpRoute
from dent_os_testbed.lib.ip.ip_address import IpAddress

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

from dent_os_testbed.test.test_suite.functional.ipv6.ipv6_utils import (
    verify_dut_routes,
)

pytestmark = [
    pytest.mark.suite_functional_ipv6,
    pytest.mark.usefixtures('cleanup_ip_addrs', 'enable_ipv6_forwarding'),
    pytest.mark.asyncio,
]


@pytest.mark.usefixtures('remove_default_gateway')
async def test_ipv6_route_default_offload(testbed):
    """
    Test Name: test_ipv6_route_default_offload
    Test Suite: suite_functional_ipv6
    Test Overview:
        Verify default GW offloading
    Test Procedure:
    1. Add IP address
    2. Add default routes via 2nd and 3rd interfaces
    3. Verify the route to the network with best metric is the only offloaded route
    4. Send traffic and verify it's passed through the route with best metric
    5. Add default route with best metrics via 3rd interface
    6. Verify the route to the network with best metric is the only offloaded route
    7. Send traffic and verify it's passed through the route with best metric
    """
    num_of_ports = 3
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], num_of_ports)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0][:num_of_ports]
    ports = tgen_dev.links_dict[dent][1][:num_of_ports]
    addr_info = namedtuple('addr_info', ['swp', 'tg', 'swp_ip', 'tg_ip', 'plen'])
    traffic_duration = 10
    wait_for_stats = 5
    dip = '2001:5555::5'

    address_map = (
        addr_info(ports[0], tg_ports[0], '2001:1111::1', '2001:1111::2', 64),
        addr_info(ports[1], tg_ports[1], '2001:2222::1', '2001:2222::2', 64),
        addr_info(ports[2], tg_ports[2], '2001:3333::1', '2001:3333::2', 64),
    )

    route_map = [
        {'port': port, 'gw': def_gw, 'metric': metric, 'should_offload': metric == 200}
        for (port, _, _, def_gw, _), metric in zip(address_map[1:], (200, 300))
    ]

    out = await IpLink.show(input_data=[{dent: [
        {'cmd_options': '-j'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get port info'

    dut_mac = {link['ifname']: link['address']
               for link in out[0][dent]['parsed_output']
               if link['ifname'] in ports}
    tg_to_swp = {tg: swp for tg, swp in zip(tg_ports, ports)}

    # Configure ports up
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up'} for port in ports
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # 1. Add IP address
    out = await IpAddress.add(input_data=[{dent: [
        {'dev': info.swp, 'prefix': f'{info.swp_ip}/{info.plen}'}
        for info in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': info.tg, 'ip': info.tg_ip, 'gw': info.swp_ip,
         'plen': info.plen, 'version': 'ipv6'}
        for info in address_map
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    streams = {
        f'{src} -> {dip}': {
            'type': 'raw',
            'protocol': 'ipv6',
            'ip_source': dev_groups[src][0]['name'],
            'ip_destination': [dev_groups[tg][0]['name'] for tg in dst],
            'rate': 10000,  # pps
            'srcMac': '02:00:00:00:00:01',
            'dstMac': dut_mac[tg_to_swp[src]],
            'srcIp': dev_groups[src][0]['ip'],
            'dstIp': dip,
        } for src, *dst in (tg_ports,)
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # 2. Add default routes via 2nd and 3rd interfaces
    out = await IpRoute.add(input_data=[{dent: [
        {'dev': route['port'], 'type': 'default', 'via': route['gw'], 'metric': route['metric']}
        for route in route_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add default routes'

    # 3. Verify the route to the network with best metric is the only offloaded route
    expected_routes = [{'dev': route['port'],
                        'dst': 'default',
                        'gateway': route['gw'],
                        'metric': route['metric'],
                        'should_exist': True,
                        'flags': ['rt_offload'] if route['should_offload'] else []}
                       for route in route_map]
    await verify_dut_routes(dent, expected_routes)

    # 4. Send traffic and verify it's passed through the route with best metric
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    await asyncio.sleep(wait_for_stats)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        expected = 0 if tg_ports[1] == row['Rx Port'] else 100
        assert loss == expected, f'Expected loss: {expected}%, actual: {loss}%'

    # 5. Add default route with best metrics via 3rd interface
    route_map[0]['should_offload'] = False
    route_map[1]['should_offload'] = True
    route_map[1]['metric'] = 100
    out = await IpRoute.add(input_data=[{dent: [
        {'dev': route['port'], 'type': 'default', 'via': route['gw'], 'metric': route['metric']}
        for route in (route_map[1],)
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add default routes'

    # 6. Verify the route to the network with best metric is the only offloaded route
    expected_routes = [{'dev': route['port'],
                        'dst': 'default',
                        'gateway': route['gw'],
                        'metric': route['metric'],
                        'should_exist': True,
                        'flags': ['rt_offload'] if route['should_offload'] else []}
                       for route in route_map]
    await verify_dut_routes(dent, expected_routes)

    # 7. Send traffic and verify it's passed through the route with best metric
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    await asyncio.sleep(wait_for_stats)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        expected = 0 if tg_ports[2] == row['Rx Port'] else 100
        assert loss == expected, f'Expected loss: {expected}%, actual: {loss}%'


async def test_ipv6_route_hosts_offload(testbed):
    """
    Test Name: test_ipv6_route_hosts_offload
    Test Suite: suite_functional_ipv6
    Test Overview:
        Verify LPM proper processing
    Test Procedure:
    1. Add IP address
    2. Add next hop routes. Send one way traffic. Verify packets received on port#2
    3. Verify routes offloaded
    4. Remove next hop route. Send one way traffic. Verify packets received on port#1
    5. Verify routes offloaded
    6. Add next hop routes. Send one way traffic. Verify packets received on port#3
    7. Verify routes offloaded
    """
    num_of_ports = 4
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], num_of_ports)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0][:num_of_ports]
    ports = tgen_dev.links_dict[dent][1][:num_of_ports]
    addr_info = namedtuple('addr_info', ['swp', 'tg', 'swp_ip', 'tg_ip', 'plen'])
    traffic_duration = 10
    wait_for_stats = 5

    address_map = (
        addr_info(ports[0], tg_ports[0], '2001:1111::1', '2001:1111::2', 64),
        addr_info(ports[1], tg_ports[1], '2001:2222::1', '2001:2222::2', 64),
        addr_info(ports[2], tg_ports[2], '2001:3333::1', '2001:3333::2', 64),
        addr_info(ports[3], tg_ports[3], '2001:4444::1', '2001:4444::2', 64),
    )

    out = await IpLink.show(input_data=[{dent: [
        {'cmd_options': '-j'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get port info'

    dut_mac = {link['ifname']: link['address']
               for link in out[0][dent]['parsed_output']
               if link['ifname'] in ports}
    tg_to_swp = {tg: swp for tg, swp in zip(tg_ports, ports)}

    # Configure ports up
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up'} for port in ports
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # 1. Add IP address
    out = await IpAddress.add(input_data=[{dent: [
        {'dev': info.swp, 'prefix': f'{info.swp_ip}/{info.plen}'}
        for info in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': info.tg, 'ip': info.tg_ip, 'gw': info.swp_ip,
         'plen': info.plen, 'version': 'ipv6'}
        for info in address_map
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    routes = [('2002:1::', 64, address_map[1]), ('2002:1::2', 128, address_map[2])]
    streams = {
        'traffic': {
            'type': 'raw',
            'protocol': 'ipv6',
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'rate': 10000,  # pps
            'srcMac': '02:00:00:00:00:01',
            'dstMac': dut_mac[tg_to_swp[tg_ports[0]]],
            'srcIp': dev_groups[tg_ports[0]][0]['ip'],
            'dstIp': routes[-1][0],
        },
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # 2. Add next hop routes
    out = await IpRoute.add(input_data=[{dent: [
        {'dst': f'{dst}/{plen}', 'via': link.tg_ip}
        for dst, plen, link in routes
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add static routes'

    # Send one way traffic from port#0
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # Verify packets received on port#2
    await asyncio.sleep(wait_for_stats)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        expected_loss = 0 if row['Rx Port'] == address_map[2].tg else 100
        assert loss == expected_loss, f'Expected loss: {expected_loss}%, actual: {loss}%'

    # 3. Verify routes offloaded
    expected_routes = [{'dev': info.swp,
                        'dst': info.swp_ip[:-1] + f'/{info.plen}',
                        'should_exist': True,
                        'flags': ['rt_trap']}
                       for info in address_map]
    expected_routes += [{'dev': link.swp,
                         'dst': dst + (f'/{plen}' if plen != 128 else ''),
                         'should_exist': True,
                         'flags': ['offload', 'rt_offload']}
                        for dst, plen, link in routes]
    await verify_dut_routes(dent, expected_routes)

    # 4. Remove next hop route
    out = await IpRoute.delete(input_data=[{dent: [
        {'dst': f'{dst}/{plen}', 'via': link.tg_ip}
        for dst, plen, link in (routes[-1],)
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to remove static route'

    # Send one way traffic
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # Verify packets received on port#1
    await asyncio.sleep(wait_for_stats)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        expected_loss = 0 if row['Rx Port'] == address_map[1].tg else 100
        assert loss == expected_loss, f'Expected loss: {expected_loss}%, actual: {loss}%'

    # 5. Verify routes offloaded
    expected_routes.pop()
    await verify_dut_routes(dent, expected_routes)

    # 6. Add next hop routes
    routes.pop()
    routes += [(routes[0][0], plen, link)
               for plen, link in ((80, address_map[1]),
                                  (100, address_map[2]),
                                  (120, address_map[3]))]
    out = await IpRoute.add(input_data=[{dent: [
        {'dst': f'{dst}/{plen}', 'via': link.tg_ip}
        for dst, plen, link in routes[1:]  # nexthop #0 is already configured
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add static routes'

    # Send one way traffic
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # Verify packets received on port#3
    await asyncio.sleep(wait_for_stats)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        expected_loss = 0 if row['Rx Port'] == address_map[3].tg else 100
        assert loss == expected_loss, f'Expected loss: {expected_loss}%, actual: {loss}%'

    # 7. Verify routes offloaded
    routes.pop()
    expected_routes += [{'dev': link.swp,
                         'dst': f'{dst}/{plen}',
                         'should_exist': True,
                         'flags': ['offload', 'rt_offload']}
                        for dst, plen, link in routes]
    await verify_dut_routes(dent, expected_routes)


async def test_ipv6_nh_state(testbed):
    """
    Test Name: test_ipv6_nh_state
    Test Suite: suite_functional_ipv6
    Test Overview:
        Verify traffic over next hop routes with port in link up state
    Test Procedure:
    1. Add IP address for 3 interfaces
    2. Add 2 net routes and 2 host routes for one of subnets
    3. Add less specific routes to same networks (shorter mask)
    4. Set the 2d interface to down state
    5. Verify routes through down port are deleted and other routes to same network are not
    6. Send traffic for deleted networks
    7. Verify traffic reaches the 3d interface despite better paths were defined to the 2d interface
    """
    num_of_ports = 3
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], num_of_ports)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0][:num_of_ports]
    ports = tgen_dev.links_dict[dent][1][:num_of_ports]
    addr_info = namedtuple('addr_info', ['swp', 'tg', 'swp_ip', 'tg_ip', 'plen'])
    traffic_duration = 10
    wait_for_stats = 5

    address_map = (
        addr_info(ports[0], tg_ports[0], '2001:1111::1', '2001:1111::2', 64),
        addr_info(ports[1], tg_ports[1], '2001:2222::1', '2001:2222::2', 64),
        addr_info(ports[2], tg_ports[2], '2001:3333::1', '2001:3333::2', 64),
    )

    egress_port1 = address_map[1]
    egress_port2 = address_map[2]
    route_info = namedtuple('route_info', ['swp', 'net', 'host', 'plen', 'gw', 'metric'])
    routes = [
        # 2 net routes and 2 host routes for one of subnets
        route_info(egress_port1.swp, '2001:1::', '5', 128, egress_port1.tg_ip, None),
        route_info(egress_port1.swp, '2001:1::', '8', 126, egress_port1.tg_ip, None),
        route_info(egress_port1.swp, '2001:2::', '5', 128, egress_port1.tg_ip, None),
        route_info(egress_port1.swp, '2001:2::', '8', 126, egress_port1.tg_ip, None),
        # less specific routes to same networks (shorter mask)
        route_info(egress_port1.swp, '2001:3::', '', 64, egress_port1.tg_ip, 10),
        route_info(egress_port2.swp, '2001:3::', '', 64, egress_port2.tg_ip, 100),
        route_info(egress_port2.swp, '2001:2::', '', 64, egress_port2.tg_ip, None),
    ]

    out = await IpLink.show(input_data=[{dent: [
        {'cmd_options': '-j'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get port info'

    dut_mac = {link['ifname']: link['address']
               for link in out[0][dent]['parsed_output']
               if link['ifname'] in ports}
    tg_to_swp = {tg: swp for tg, swp in zip(tg_ports, ports)}

    # Configure ports up
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up'} for port in ports
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # 1. Add IP address for 3 interfaces
    out = await IpAddress.add(input_data=[{dent: [
        {'dev': info.swp, 'prefix': f'{info.swp_ip}/{info.plen}'}
        for info in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    # Configure TG interfaces
    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': info.tg, 'ip': info.tg_ip, 'gw': info.swp_ip,
         'plen': info.plen, 'version': 'ipv6'}
        for info in address_map
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    # Configure traffic items
    nets = list(set(r.net for r in routes))
    hosts = list(set(r.host for r in routes if r.host))
    streams = {
        f'traffic to {net}{host}': {
            'type': 'raw',
            'protocol': 'ipv6',
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'rate': 10,  # %
            'frame_rate_type': 'line_rate',
            'srcMac': '02:00:00:00:00:01',
            'dstMac': dut_mac[tg_to_swp[tg_ports[0]]],
            'srcIp': dev_groups[tg_ports[0]][0]['ip'],
            'dstIp': f'{net}{host}',
        } for net in nets for host in hosts
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # 2. Add 2 net routes and 2 host routes for one of subnets
    # 3. Add less specific routes to same networks (shorter mask)
    config = [
        {'dst': f'{net}/{plen}', 'via': via}
        for _, net, _, plen, via, metric in routes if metric is None
    ]
    config += [
        {'dst': f'{net}/{plen}', 'metric': metric, 'via': via}
        for _, net, _, plen, via, metric in routes if metric is not None
    ]
    out = await IpRoute.add(input_data=[{dent: config}])
    assert out[0][dent]['rc'] == 0, 'Failed to add routes'

    # 4. Set the 2d interface to down state
    out = await IpLink.set(input_data=[{dent: [
        {'device': egress_port1.swp, 'operstate': 'down'}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # 5. Verify routes through down port are deleted and other routes to same network are not
    expected_routes = [{'dev': info.swp,
                        'dst': f'{info.swp_ip[:-1]}/{info.plen}',
                        'should_exist': info.swp != egress_port1.swp,
                        'flags': ['rt_trap']}
                       for info in address_map]
    expected_routes += [{'dev': route.swp,
                         'dst': f'{route.net}{route.host}/{route.plen}',
                         'gateway': route.gw,
                         'should_exist': route.swp != egress_port1.swp,
                         'flags': ['offload', 'rt_offload']}
                        for route in routes]
    await verify_dut_routes(dent, expected_routes)

    # 6. Send traffic for deleted networks
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # 7. Verify traffic reaches the 3d interface despite better paths were defined to the 2d interface
    await asyncio.sleep(wait_for_stats)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        if row['Rx Port'] != egress_port1.tg and routes[0].net not in row['Traffic Item']:
            expected_loss = 0
        else:
            expected_loss = 100
        assert loss == expected_loss, f'Expected loss: {expected_loss}%, actual: {loss}%'


async def test_ipv6_route_metrics(testbed):
    """
    Test Name: test_ipv6_route_metrics
    Test Suite: suite_functional_ipv6
    Test Overview:
        Verify that the route with the best metric is used and offloaded
    Test Procedure:
    1. Add IP address for 3 interfaces
    2. Add multiple routes to a subnet with different metrics via 2nd and 3rd interfaces
    3. Send traffic and verify it's passed through the route with best metric
    4. Verify the route to the network with best metric is the only offloaded route
    5. Delete route with the best metrics (via 2nd interface)
    6. Send traffic and verify it's passed through the route with best metric
    7. Verify the route to the network with best metric is the only offloaded route
    8. Add route with best metrics (via 3rd interface)
    9. Send traffic and verify it's passed through the route with best metric
    10. Verify the route to the network with best metric is the only offloaded route
    """
    num_of_ports = 3
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], num_of_ports)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0][:num_of_ports]
    ports = tgen_dev.links_dict[dent][1][:num_of_ports]
    addr_info = namedtuple('addr_info', ['swp', 'tg', 'swp_ip', 'tg_ip', 'plen'])
    traffic_duration = 10
    wait_for_stats = 5

    address_map = (
        addr_info(ports[0], tg_ports[0], '2001:1111::1', '2001:1111::2', 64),
        addr_info(ports[1], tg_ports[1], '2001:2222::1', '2001:2222::2', 64),
        addr_info(ports[2], tg_ports[2], '2001:3333::1', '2001:3333::2', 64),
        addr_info(ports[2], tg_ports[2], '2001:4444::1', '2001:4444::2', 64),
    )

    route_info = namedtuple('route_info', ['swp', 'dst', 'plen', 'gw', 'metric'])
    dst_ip = address_map[-1].tg_ip[:-1] + '5'
    routes = [
        route_info(address_map[1].swp, dst_ip[:-1], 64, address_map[1].tg_ip, 100),
        route_info(address_map[1].swp, dst_ip[:-1], 64, address_map[1].tg_ip, 101),
        route_info(address_map[2].swp, dst_ip[:-1], 64, address_map[2].tg_ip, 102),
        route_info(address_map[2].swp, dst_ip[:-1], 64, address_map[2].tg_ip, 99),
    ]

    out = await IpLink.show(input_data=[{dent: [
        {'cmd_options': '-j'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get port info'

    dut_mac = {link['ifname']: link['address']
               for link in out[0][dent]['parsed_output']
               if link['ifname'] in ports}
    tg_to_swp = {tg: swp for tg, swp in zip(tg_ports, ports)}

    # Configure ports up
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up'} for port in ports
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # 1. Add IP address for 3 interfaces
    out = await IpAddress.add(input_data=[{dent: [
        {'dev': info.swp, 'prefix': f'{info.swp_ip}/{info.plen}'}
        for info in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    # Configure TG interfaces
    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': info.tg, 'ip': info.tg_ip, 'gw': info.swp_ip,
         'plen': info.plen, 'version': 'ipv6'}
        for info in address_map
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    # Configure traffic items
    streams = {
        'traffic': {
            'type': 'raw',
            'protocol': 'ipv6',
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'rate': 10,  # %
            'frame_rate_type': 'line_rate',
            'srcMac': '02:00:00:00:00:01',
            'dstMac': dut_mac[tg_to_swp[tg_ports[0]]],
            'srcIp': dev_groups[tg_ports[0]][0]['ip'],
            'dstIp': dst_ip,
        }
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # 2. Add multiple routes to a subnet with different metrics via 2nd and 3rd interfaces
    out = await IpRoute.add(input_data=[{dent: [
        {'dst': f'{route.dst}/{route.plen}', 'metric': route.metric, 'via': route.gw}
        for route in routes[:-1]  # don't add the last route yet
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add routes'

    # 3. Send traffic and verify it's passed through the route with best metric
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    await asyncio.sleep(wait_for_stats)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        expected_loss = 0 if tg_to_swp[row['Rx Port']] == routes[0].swp else 100
        assert loss == expected_loss, f'Expected loss: {expected_loss}%, actual: {loss}%'

    # 4. Verify the route to the network with best metric is the only offloaded route
    connected_routes = [{'dev': info.swp,
                         'dst': f'{info.swp_ip[:-1]}/{info.plen}',
                         'should_exist': True,
                         'flags': ['rt_trap'] if info != address_map[-1] else []}
                        for info in address_map]
    expected_routes = [{'dev': route.swp,
                        'dst': f'{route.dst}/{route.plen}',
                        'gateway': route.gw,
                        'metric': route.metric,
                        'should_exist': route.metric != 99,
                        'flags': ['offload', 'rt_offload'] if route.metric == 100 else []}
                       for route in routes[:-1]]
    await verify_dut_routes(dent, connected_routes + expected_routes)

    # 5. Delete route with the best metrics (via 2nd interface)
    out = await IpRoute.delete(input_data=[{dent: [
        {'dst': f'{routes[0].dst}/{routes[0].plen}',
         'metric': routes[0].metric,
         'gateway': routes[0].gw,
         'dev': routes[0].swp}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to delete routes'

    # 6. Send traffic and verify it's passed through the route with best metric
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    await asyncio.sleep(wait_for_stats)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        expected_loss = 0 if tg_to_swp[row['Rx Port']] == routes[0].swp else 100
        assert loss == expected_loss, f'Expected loss: {expected_loss}%, actual: {loss}%'

    # 7. Verify the route to the network with best metric is the only offloaded route
    expected_routes[0]['should_exist'] = False               # metric 100
    expected_routes[1]['flags'] = ['offload', 'rt_offload']  # metric 101
    await verify_dut_routes(dent, connected_routes + expected_routes)

    # 8. Add route with best metrics (via 3rd interface)
    out = await IpRoute.add(input_data=[{dent: [
        {'dst': f'{routes[-1].dst}/{routes[-1].plen}',
         'metric': routes[-1].metric,
         'via': routes[-1].gw}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add routes'

    # 9. Send traffic and verify it's passed through the route with best metric
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    await asyncio.sleep(wait_for_stats)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        expected_loss = 0 if tg_to_swp[row['Rx Port']] == routes[-1].swp else 100
        assert loss == expected_loss, f'Expected loss: {expected_loss}%, actual: {loss}%'

    # 10. Verify the route to the network with best metric is the only offloaded route
    expected_routes[1]['flags'] = ['offload']  # metric 101
    expected_routes[2]['should_exist'] = True  # metric 102
    expected_routes[2]['flags'] = []
    expected_routes.append({
        'dev': routes[-1].swp,
        'dst': f'{routes[-1].dst}/{routes[-1].plen}',
        'gateway': routes[-1].gw,
        'metric': routes[-1].metric,  # metric 99
        'should_exist': True,
        'flags': ['offload', 'rt_offload']})

    await verify_dut_routes(dent, connected_routes + expected_routes)
