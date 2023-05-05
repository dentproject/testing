from collections import namedtuple
import asyncio
import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_route import IpRoute
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.ip.ip_neighbor import IpNeighbor

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_clear_traffic_items,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_get_loss,
)

from dent_os_testbed.test.test_suite.functional.ipv6.ipv6_utils import (
    verify_dut_neighbors,
    verify_dut_routes,
)

pytestmark = [
    pytest.mark.suite_functional_ipv6,
    pytest.mark.usefixtures('cleanup_ip_addrs', 'enable_ipv6_forwarding', 'enable_ipv4_forwarding'),
    pytest.mark.asyncio,
]


async def test_ipv64_nh_reconfig(testbed):
    """
    Test Name: test_ipv64_nh_reconfig
    Test Suite: suite_functional_ipv6
    Test Overview:
        Verify IPv4/IPv6/IPv4 configuration on the port applied
        Verify clear traffic for IPv4 and IPv6
        Verify IPv4 and IPv6 routes are offloaded
    Test Procedure:
    1. Add IP interfaces for TG
    2. Set ports up
    3. Add IPv4 address for DUT
    4. Add static neighbors and nexthop routes
    5. Configure IPv4 bidirectional host to host streams
       Configure IPv4 unidirectional stream for nexthop
    6. Send traffic. Verify no losses
    7. Verify connected IPv4 routes added and offloaded, neighbors resolved
    8. Repeat steps 3-7 for IPv6
    9. Repeat steps 3-7 for IPv4 again
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
    nh_info = namedtuple('nh_info', ['swp', 'tg', 'dst', 'via', 'plen', 'mac'])
    traffic_duration = 10
    wait_for_stats = 5
    nh_src_idx = 3
    nh_dst_idx = 0
    IPV4 = 0
    IPV6 = 1

    address_map = {
        IPV4: [
            addr_info(port, tg, f'1.{idx}.1.1', f'1.{idx}.1.2', 24)
            for idx, (port, tg) in enumerate(zip(ports, tg_ports), start=1)
        ],
        IPV6: [
            addr_info(port, tg, f'2001:{idx}::1', f'2001:{idx}::2', 64)
            for idx, (port, tg) in enumerate(zip(ports, tg_ports), start=1)
        ],
    }
    nh_route = {
        IPV4: nh_info(
            address_map[IPV4][nh_dst_idx].swp,
            address_map[IPV4][nh_dst_idx].tg,
            '48.0.0.0',
            address_map[IPV4][nh_dst_idx].swp_ip[:-1] + '5',  # 1.1.1.5
            address_map[IPV4][nh_dst_idx].plen,
            '02:00:00:00:00:01',
        ),
        IPV6: nh_info(
            address_map[IPV6][nh_dst_idx].swp,
            address_map[IPV6][nh_dst_idx].tg,
            '2001:1234::',
            address_map[IPV6][nh_dst_idx].swp_ip[:-1] + '5',  # 2001:1::5
            address_map[IPV6][nh_dst_idx].plen,
            '02:00:00:00:00:02',
        ),
    }

    out = await IpLink.show(input_data=[{dent: [
        {'cmd_options': '-j'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get port info'

    dut_mac = {link['ifname']: link['address']
               for link in out[0][dent]['parsed_output']
               if link['ifname'] in ports}

    # 1. Add IP interfaces for TG
    dev_groups = tgen_utils_dev_groups_from_config([
        {'ixp': info.tg, 'ip': info.tg_ip, 'gw': info.swp_ip,
         'plen': info.plen}
        for info in address_map[IPV4]
    ] + [
        {'ixp': info.tg, 'ip': info.tg_ip, 'gw': info.swp_ip,
         'plen': info.plen, 'version': 'ipv6'}
        for info in address_map[IPV6]
    ])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    # 2. Set ports up
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up'} for port in ports
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    for version in (IPV4, IPV6, IPV4):
        # 3. Add IPv4 address for DUT
        out = await IpAddress.add(input_data=[{dent: [
            {'dev': info.swp, 'prefix': f'{info.swp_ip}/{info.plen}'}
            for info in address_map[version]
        ]}])
        assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

        # 4. Add static neighbors and nexthop routes
        out = await IpNeighbor.add(input_data=[{dent: [
            {'dev': nh_route[version].swp,
             'address': nh_route[version].via,
             'lladdr': nh_route[version].mac},
        ]}])
        assert out[0][dent]['rc'] == 0, 'Failed to add static arp entries'

        out = await IpRoute.add(input_data=[{dent: [
            {'dst': f'{nh_route[version].dst}/{nh_route[version].plen}',
             'nexthop': [{'via': nh_route[version].via}]},
        ]}])
        assert out[0][dent]['rc'] == 0, 'Failed to add nexthop'

        # 5. Configure IPv4 bidirectional host to host streams
        proto = 'ipv4' if version == IPV4 else 'ipv6'
        streams = {f'{src} <-> {[dst for dst in tg_ports if src < dst]}': {
            'type': proto,
            'rate': 10000,  # pps
            'ip_source': dev_groups[src][version]['name'],
            'ip_destination': [dev_groups[dst][version]['name'] for dst in tg_ports if src < dst],
            'bi_directional': True}
            for src in tg_ports[:-1]
        }
        # Configure IPv4 unidirectional stream for nexthop
        streams.update({f'{tg_ports[nh_src_idx]} -> nexthop': {
            'type': 'raw',
            'protocol': proto,
            'ip_source': dev_groups[tg_ports[nh_src_idx]][version]['name'],
            'ip_destination': dev_groups[nh_route[version].tg][version]['name'],
            'rate': 10000,  # pps
            'srcMac': '02:00:00:00:00:05',
            'dstMac': dut_mac[ports[nh_src_idx]],
            'srcIp': '5.0.0.5' if version == IPV4 else '2001:5::5',
            'dstIp': nh_route[version].dst,
        }})
        await tgen_utils_setup_streams(tgen_dev, None, streams)

        # 6. Send traffic
        await tgen_utils_start_traffic(tgen_dev)
        await asyncio.sleep(traffic_duration)
        await tgen_utils_stop_traffic(tgen_dev)

        # Verify no losses
        await asyncio.sleep(wait_for_stats)
        stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
        for row in stats.Rows:
            loss = tgen_utils_get_loss(row)
            assert loss == 0, f'Expected loss: 0%, actual: {loss}%'

        # 7. Verify neighbors resolved
        out = await IpNeighbor.show(input_data=[{dent: [
            {'cmd_options': '-j -' + proto[-1]},  # -4/-6
        ]}], parse_output=True)
        assert out[0][dent]['rc'] == 0, 'Failed to get neighbors'

        expected_neis = [{'dev': info.swp,
                          'dst': info.tg_ip,
                          'states': ['REACHABLE', 'PROBE', 'STALE', 'DELAY']}
                         for info in address_map[version]]
        expected_neis += [{'dev': nh_route[version].swp,
                           'dst': nh_route[version].via,
                           'states': ['PERMANENT']}]
        await verify_dut_neighbors(dent, expected_neis)

        # Verify connected IPv4 routes added and offloaded
        out = await IpRoute.show(input_data=[{dent: [
            {'cmd_options': '-j -' + proto[-1]},  # -4/-6
        ]}], parse_output=True)
        assert out[0][dent]['rc'] == 0, 'Failed to get routes'

        expected_routes = [{'dev': info.swp,
                            'dst': info.swp_ip[:-1] + ('0/' if version == IPV4 else '/') + str(info.plen),
                            'should_exist': True,
                            'flags': ['rt_trap']}
                           for info in address_map[version]]
        expected_routes += [{'dev': nh_route[version].swp,
                             'dst': f'{nh_route[version].dst}/{nh_route[version].plen}',
                             'should_exist': True,
                             'flags': ['offload', 'rt_offload']}]
        await verify_dut_routes(dent, expected_routes)

        # clear traffic items and ip addrs to prepare for the next iteration
        await tgen_utils_clear_traffic_items(tgen_dev)
        out = await IpAddress.delete(input_data=[{dent: [
            {'dev': info.swp, 'prefix': f'{info.swp_ip}/{info.plen}'}
            for info in address_map[version]
        ]}])
        assert out[0][dent]['rc'] == 0, 'Failed to remove IP addr from port'


async def test_ipv64_nh_routes(testbed):
    """
    Test Name: test_ipv64_nh_routes
    Test Suite: suite_functional_ipv6
    Test Overview:
        Verify IPv4 and IPv6 configuration on the port applied
        Verify clear traffic for IPv4 and IPv6
        Verify IPv4 and IPv6 routes are offloaded
    Test Procedure:
    1. Set ports up. Add IPv4 and IPv6 address for interfaces
    2. Add static neighbors. Add nexthop routes
    3. Configure IPv4 and IPv6 bidirectional streams
    4. Configure IPv4 and IPv6 unidirectional stream for nexthop
    5. Send traffic. Verify no losses
    6. Verify connected routes added and offloaded, neighbors resolved
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
    nh_info = namedtuple('nh_info', ['swp', 'tg', 'dst', 'via', 'plen', 'mac'])
    traffic_duration = 10
    wait_for_stats = 5

    address_map = (
        addr_info(ports[0], tg_ports[0], '1.1.1.1', '1.1.1.2', 24),
        addr_info(ports[1], tg_ports[1], '2001:2::1', '2001:2::2', 64),
        addr_info(ports[2], tg_ports[2], '1.3.1.1', '1.3.1.2', 24),
        addr_info(ports[3], tg_ports[3], '2001:4::1', '2001:4::2', 64),
    )
    nh_route = (
        nh_info(
            address_map[0].swp,
            address_map[0].tg,
            '48.0.0.0',
            address_map[0].swp_ip[:-1] + '5',  # 1.1.1.5
            address_map[0].plen,
            '02:00:00:00:00:01',
        ),
        nh_info(
            address_map[1].swp,
            address_map[1].tg,
            '2001:1234::',
            address_map[1].swp_ip[:-1] + '5',  # 2001:2::5
            address_map[1].plen,
            '02:00:00:00:00:02',
        ),
    )

    out = await IpLink.show(input_data=[{dent: [
        {'cmd_options': '-j'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get port info'

    dut_mac = {link['ifname']: link['address']
               for link in out[0][dent]['parsed_output']
               if link['ifname'] in ports}

    # 1. Set ports up
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up'} for port in ports
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # Add IPv4 and IPv6 address for interfaces
    dev_groups = tgen_utils_dev_groups_from_config([
        {'ixp': info.tg, 'ip': info.tg_ip, 'gw': info.swp_ip,
         'plen': info.plen, 'version': 'ipv6' if ':' in info.tg_ip else 'ipv4'}
        for info in address_map
    ])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    out = await IpAddress.add(input_data=[{dent: [
        {'dev': info.swp, 'prefix': f'{info.swp_ip}/{info.plen}'}
        for info in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    # 2. Add static neighbors
    out = await IpNeighbor.add(input_data=[{dent: [
        {'dev': route.swp,
         'address': route.via,
         'lladdr': route.mac}
        for route in nh_route
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add static arp entries'

    # Add nexthop routes
    out = await IpRoute.add(input_data=[{dent: [
        {'dst': f'{route.dst}/{route.plen}',
         'nexthop': [{'via': route.via}]}
        for route in nh_route
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add nexthop'

    # 3. Configure IPv4 and IPv6 bidirectional streams
    streams = {
        f'{proto}: {src} <-> {dst}': {
            'type': proto,
            'rate': 10000,  # pps
            'ip_source': dev_groups[src][0]['name'],
            'ip_destination': dev_groups[dst][0]['name'],
            'bi_directional': True,
        }
        for src, dst, proto in ((tg_ports[0], tg_ports[2], 'ipv4'),
                                (tg_ports[1], tg_ports[3], 'ipv6'))
    }
    # 4. Configure IPv4 and IPv6 unidirectional stream for nexthop
    streams.update({
        f'{proto}: {src} -> nexthop': {
            'type': 'raw',
            'protocol': proto,
            'ip_source': dev_groups[src.tg][0]['name'],
            'ip_destination': dev_groups[dst.tg][0]['name'],
            'rate': 10000,  # pps
            'srcMac': '02:00:00:00:00:05',
            'dstMac': dut_mac[src.swp],
            'srcIp': '5.0.0.5' if proto == 'ipv4' else '2001:5::5',
            'dstIp': dst.dst,
        }
        for src, dst, proto in ((address_map[2], nh_route[0], 'ipv4'),
                                (address_map[3], nh_route[1], 'ipv6'))
    })
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # 5. Send traffic
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # Verify no losses
    await asyncio.sleep(wait_for_stats)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        assert loss == 0, f'Expected loss: 0%, actual: {loss}%'

    # 6. Verify neighbors resolved
    expected_neis = [{'dev': info.swp,
                      'dst': info.tg_ip,
                      'states': ['REACHABLE', 'PROBE', 'STALE', 'DELAY']}
                     for info in address_map]
    expected_neis += [{'dev': route.swp,
                       'dst': route.via,
                       'states': ['PERMANENT']}
                      for route in nh_route]
    await verify_dut_neighbors(dent, expected_neis)

    # Verify connected routes added and offloaded
    expected_routes = [{'dev': info.swp,
                        'dst': info.swp_ip[:-1] + ('/' if ':' in info.swp_ip else '0/') + str(info.plen),
                        'should_exist': True,
                        'flags': ['rt_trap']}
                       for info in address_map]
    expected_routes += [{'dev': route.swp,
                         'dst': f'{route.dst}/{route.plen}',
                         'should_exist': True,
                         'flags': ['offload', 'rt_offload']}
                        for route in nh_route]
    await verify_dut_routes(dent, expected_routes)
