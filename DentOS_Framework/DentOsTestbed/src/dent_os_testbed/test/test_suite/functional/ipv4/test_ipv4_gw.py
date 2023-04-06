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
    tgen_utils_get_swp_info,
    tgen_utils_stop_traffic,
    tgen_utils_get_loss,
)

pytestmark = [
    pytest.mark.suite_functional_ipv4,
    pytest.mark.usefixtures('cleanup_ip_addrs', 'cleanup_tgen', 'enable_ipv4_forwarding'),
    pytest.mark.asyncio,
]


async def get_routes_list(dent):
    out = await IpRoute.show(input_data=[{dent: [
        {'cmd_options': '-j'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get list of route entries'
    return out[0][dent]['parsed_output']


@pytest.mark.usefixtures('remove_default_gateway')
async def test_ipv4_default_gw(testbed):
    """
    Test Name: test_ipv4_default_gw
    Test Suite: suite_functional_ipv4
    Test Overview: Test IPv4 default GW offloading
    Test Procedure:
    1. Add IP address
    2. Remove current default routes
    3. Add default routes
    4. Send traffic and verify it's passed through the route with best metric
    5. Verify the route to the network with best metric is the only offloaded route
    6. Add default route with best metrics via 3rd interface
    7. Send traffic and verify it's passed through the route with best metric
    8. Verify the route to the network with best metric is the only offloaded route
    """
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]
    traffic_duration = 10
    dip = '5.5.5.5'

    port_mac = {}
    for port in ports:
        swp_info = {}
        await tgen_utils_get_swp_info(dent_dev, port, swp_info)
        port_mac[port] = swp_info['mac']
    address_map = (
        # swp port, tg port,    swp ip,    tg ip,    plen, tg src mac
        (ports[0], tg_ports[0], '1.1.1.1', '1.1.1.2', 24, '02:00:00:00:00:01', port_mac[ports[0]]),
        (ports[1], tg_ports[1], '2.2.2.1', '2.2.2.2', 24, '02:00:00:00:00:02', port_mac[ports[1]]),
        (ports[2], tg_ports[2], '3.3.3.1', '3.3.3.2', 24, '02:00:00:00:00:03', port_mac[ports[2]]),
        (ports[3], tg_ports[3], '4.4.4.1', '4.4.4.2', 24, '02:00:00:00:00:04', port_mac[ports[3]]),
    )

    route_map = {
        port: {'gw': def_gw, 'metric': metric, 'should_offload': metric != 200}
        for (port, _, _, def_gw, *_), metric in zip(address_map, (100, 200, None))
    }

    # Configure ports up
    out = await IpLink.set(input_data=[{dent: [{'device': port, 'operstate': 'up'}
                                               for port in ports]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # 1. Add IP address
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
        f'{tg_ports[3]} -> {tg} {dip}': {
            'type': 'raw',
            'ip_source': dev_groups[tg_ports[3]][0]['name'],
            'ip_destination': dev_groups[tg][0]['name'],
            'protocol': 'ip',
            'rate': '1000',  # pps
            'srcMac': address_map[3][5],
            'dstMac': address_map[3][6],
            'srcIp': dev_groups[tg_ports[3]][0]['ip'],
            'dstIp': dip,
        } for tg in tg_ports[:3]
    }

    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # 2. Default gw removed in fixture

    # 3. Add default routes
    out = await IpRoute.add(input_data=[{dent: [
        {'dev': port, 'type': 'default', 'via': route['gw'], 'metric': route['metric']}
        for port, route in route_map.items() if route['metric']
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add default routes'

    # 4. Send traffic and verify it's passed through the route with best metric
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Traffic Item Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        expected = 0 if tg_ports[0] in row['Traffic Item'] else 100
        assert loss == expected, f'Expected loss: {expected}%, actual: {loss}%'

    # 5. Verify the route to the network with best metric is the only offloaded route
    routes = await get_routes_list(dent)
    for route in routes:
        if route['dst'] != 'default':
            continue
        dev = route['dev']
        assert 'metric' in route and route['metric'] == route_map[dev]['metric'], \
            f"Route {route['gateway']} should have metric {route_map[dev]['metric']}"
        if route_map[dev]['should_offload']:
            assert 'rt_offload' in route['flags'], f"Route {route['gateway']} should be offloaded"
        else:
            assert 'rt_offload' not in route['flags'], f"Route {route['gateway']} should not be offloaded"

    # 6. Add default route with best metrics via 3rd interface
    out = await IpRoute.add(input_data=[{dent: [
        {'dev': port, 'type': 'default', 'via': route['gw']}
        for port, route in route_map.items() if not route['metric']
    ]}])

    route_map[ports[0]]['should_offload'] = False

    # 7. Send traffic and verify it's passed through the route with best metric
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Traffic Item Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        expected = 0 if tg_ports[2] in row['Traffic Item'] else 100
        assert loss == expected, f'Expected loss: {expected}%, actual: {loss}%'

    # 8. Verify the route to the network with best metric is the only offloaded route
    routes = await get_routes_list(dent)
    for route in routes:
        if route['dst'] != 'default':
            continue
        dev = route['dev']
        if route_map[dev]['should_offload']:
            assert 'rt_offload' in route['flags'], 'Route without metric should be offloaded'
            assert 'metric' not in route, f"Route {route['gateway']} should no have any metric"
        else:
            assert 'rt_offload' not in route['flags'], f'Route with metric should not be offloaded'
            assert 'metric' in route and route['metric'] == route_map[dev]['metric'], \
                f"Route {route['gateway']} should have metric {route_map[dev]['metric']}"


async def test_ipv4_not_connected_gw(testbed):
    """
    Test Name: test_ipv4_not_connected_gw
    Test Suite: suite_functional_ipv4
    Test Overview: Test that default gw, that is not connected, cannot be configured
    Test Procedure:
    1. Configure IP addrs
    2. Configure default gw that is not connected
    3. Verify it is unconfigurable
    """
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent = dent_devices[0].host_name
    ports = tgen_dev.links_dict[dent][1]
    gw = '5.5.5.5'

    for idx, port in enumerate(ports):
        # 1. Configure IP addrs
        ip = '.'.join(map(str, [idx + 1] * 4))
        out = await IpAddress.add(input_data=[{dent: [
            {'dev': port, 'prefix': f'{ip}/24'}
        ]}])
        assert out[0][dent]['rc'] == 0, 'Failed to set ip addr'

        # 2. Configure default gw that is not connected
        out = await IpRoute.add(input_data=[{dent: [
            {'dev': port, 'type': 'default', 'via': gw}
        ]}])

        # 3. Verify it is unconfigurable
        assert out[0][dent]['rc'] != 0, f'Adding {gw} as default gw to {ip} should fail'
