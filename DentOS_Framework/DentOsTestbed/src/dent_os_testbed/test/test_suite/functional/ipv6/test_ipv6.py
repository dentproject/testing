from collections import namedtuple
import asyncio
import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.ip.ip_neighbor import IpNeighbor
from dent_os_testbed.lib.os.recoverable_sysctl import RecoverableSysctl

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
    verify_dut_neighbors,
    verify_dut_routes,
    verify_dut_addrs,
)

pytestmark = [
    pytest.mark.suite_functional_ipv6,
    pytest.mark.usefixtures('cleanup_ip_addrs', 'cleanup_tgen', 'enable_ipv6_forwarding', 'cleanup_sysctl'),
    pytest.mark.asyncio,
]


async def test_ipv6_basic_config(testbed):
    """
    Test Name: test_ipv6_basic_config
    Test Suite: suite_functional_ipv6
    Test Overview:
        Verify adding removing IPv6 address.
        Verify connected route adding removing.
        Verify routing based on connected routes.
        Verify basic scenario for neighbors.
    Test Procedure:
    1. Add IP address for 2 interfaces: IP1 and IP2 in different subnets
    2. Verify IP configuration: no errors on IP address adding, connected routes added and offloaded
    3. Send bidirectional traffic between TG ports. Verify clear traffic
    4. Verify neighbors on DUT
    5. Delete IP addresses on DUT and send traffic
    6. Verify connected routes are deleted, neighbors are flushed, packets loss
    """
    num_of_ports = 2
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
    plen = 64

    address_map = (
        addr_info(ports[0], tg_ports[0], '2001:1111:10:1::1', '2001:1111:10:1::2', plen),
        addr_info(ports[0], tg_ports[0], '2001:2222:20:2::1', '2001:2222:20:2::2', plen),
        addr_info(ports[1], tg_ports[1], '2001:3333:30:3::1', '2001:3333:30:3::2', plen),
    )

    # 1. Add IP address for 2 interfaces: IP1 and IP2 in different subnets
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up'} for port in ports
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

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

    # 2. Verify IP configuration: no errors on IP address adding, connected routes added and offloaded
    expected_addrs = [
        {'ifname': info.swp,
         'should_exist': True,
         'addr_info': {
            'family': 'inet6',
            'local': info.swp_ip,
            'prefixlen': info.plen}}
        for info in address_map
    ]
    await verify_dut_addrs(dent, expected_addrs)

    expected_routes = [{'dev': info.swp,
                        'dst': info.swp_ip[:-1] + f'/{info.plen}',
                        'should_exist': True,
                        'flags': ['rt_trap']}
                       for info in address_map]
    await verify_dut_routes(dent, expected_routes)

    # 3. Send bidirectional traffic between TG ports. Verify clear traffic
    streams = {
        f'{tg_ports[0]} <-> {tg_ports[1]}': {
            'type': 'ipv6',
            'ip_source': dev_groups[tg_ports[1]][0]['name'],
            'ip_destination': [ep['name'] for ep in dev_groups[tg_ports[0]]],
            'rate': 10000,  # pps
            'bi_directional': True,
        },
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    await asyncio.sleep(wait_for_stats)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        assert loss == 0, f'Expected loss: 0%, actual: {loss}%'

    # 4. Verify neighbors on DUT
    expected_neis = [{'dev': info.swp,
                      'dst': info.tg_ip,
                      'should_exist': True,
                      'offload': True,
                      'states': ['REACHABLE', 'PROBE', 'STALE', 'DELAY']}
                     for info in address_map]
    await verify_dut_neighbors(dent, expected_neis)

    # 5. Delete IP addresses on DUT and send traffic
    out = await IpAddress.delete(input_data=[{dent: [
        {'dev': info.swp, 'prefix': f'{info.swp_ip}/{info.plen}'}
        for info in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to del IP addr from port'

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # 6. Verify connected routes are deleted, neighbors are flushed, packets loss
    await asyncio.sleep(wait_for_stats)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        assert loss == 100, f'Expected loss: 100%, actual: {loss}%'


async def test_ipv6_flags(testbed):
    """
    Test Name: test_ipv6_flags
    Test Suite: suite_functional_ipv6
    Test Overview:
        Verify IPv6 address change, replace, set lifetime
    Test Procedure:
    1. Add IP addrs in different subnets using change/replace
    2. Configure Hosts on TG
    3. Send bidirectional traffic
       - Verify no packet losses
       - Verify ip addresses have 'dynamic' True
    4. Set preferred timer to zero, valid timer must be non zero
    5. Send bidirectional traffic
       - Verify no packet losses
       - Verify entries with preferred timer equal to zero are deprecated
    6. Set valid timer to one
       - Verify ip addresses that were marked as 'deprecated' are deleted
    7. Flush neighbor entries
    8. Send bidirectional traffic
       - Verify packet loss occurs as IP addresses got deleted
    """
    num_of_ports = 2
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
        addr_info(ports[0], tg_ports[0], '2001:3333::1', '2001:3333::2', 64),
        addr_info(ports[1], tg_ports[1], '2001:4444::1', '2001:4444::2', 64),
    )

    # 1. Add IP addrs in different subnets using change/replace
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up'} for port in ports
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    valid_lft = 960
    preferred_lft = 900
    out = await IpAddress.change(input_data=[{dent: [
        {'dev': address_map[0].swp,
         'prefix': f'{address_map[0].swp_ip}/{address_map[0].plen}',
         'valid_lft': valid_lft,
         'preferred_lft': preferred_lft},
        {'dev': address_map[1].swp,
         'prefix': f'{address_map[1].swp_ip}/{address_map[1].plen}'},
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    out = await IpAddress.replace(input_data=[{dent: [
        {'dev': address_map[2].swp,
         'prefix': f'{address_map[2].swp_ip}/{address_map[2].plen}'},
        {'dev': address_map[3].swp,
         'prefix': f'{address_map[3].swp_ip}/{address_map[3].plen}',
         'valid_lft': valid_lft,
         'preferred_lft': preferred_lft},
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    expected_addrs = [
        {'ifname': info.swp,
         'should_exist': True,
         'addr_info': {
            'family': 'inet6',
            'local': info.swp_ip,
            'dynamic': True if info == address_map[0] or info == address_map[3] else None,
            'prefixlen': info.plen}}
        for info in address_map
    ]
    await verify_dut_addrs(dent, expected_addrs)

    # 2. Configure Hosts on TG
    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': info.tg, 'ip': info.tg_ip, 'gw': info.swp_ip,
         'plen': info.plen, 'version': 'ipv6'}
        for info in address_map
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    # 3. Send bidirectional traffic
    streams = {
        f'{tg_ports[0]} <-> {tg_ports[1]}': {
            'type': 'ipv6',
            'ip_source': [ep['name'] for ep in dev_groups[tg_ports[0]]],
            'ip_destination': [ep['name'] for ep in dev_groups[tg_ports[1]]],
            'rate': 10000,  # pps
            'bi_directional': True,
        },
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # Verify no packet losses
    await asyncio.sleep(wait_for_stats)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        assert loss == 0, f'Expected loss: 0%, actual: {loss}%'

    # Verify ip addresses have 'dynamic' True
    await verify_dut_addrs(dent, expected_addrs)

    # 4. Set preferred timer to zero, valid timer must be non zero
    valid_lft = 120
    preferred_lft = 0
    out = await IpAddress.change(input_data=[{dent: [
        {'dev': address_map[0].swp,
         'prefix': f'{address_map[0].swp_ip}/{address_map[0].plen}',
         'valid_lft': valid_lft,
         'preferred_lft': preferred_lft},
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    out = await IpAddress.replace(input_data=[{dent: [
        {'dev': address_map[3].swp,
         'prefix': f'{address_map[3].swp_ip}/{address_map[3].plen}',
         'valid_lft': valid_lft,
         'preferred_lft': preferred_lft},
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    # 5. Send bidirectional traffic
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # Verify no packet losses
    await asyncio.sleep(wait_for_stats)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        assert loss == 0, f'Expected loss: 0%, actual: {loss}%'

    # Verify entries with preferred timer equal to zero are deprecated
    expected_addrs = [
        {'ifname': info.swp,
         'should_exist': True,
         'addr_info': {
            'family': 'inet6',
            'local': info.swp_ip,
            'dynamic': True if info == address_map[0] or info == address_map[3] else None,
            'deprecated': True if info == address_map[0] or info == address_map[3] else None,
            'prefixlen': info.plen}}
        for info in address_map
    ]
    await verify_dut_addrs(dent, expected_addrs)

    # 6. Set valid timer to one
    valid_lft = 1
    preferred_lft = 0
    out = await IpAddress.change(input_data=[{dent: [
        {'dev': address_map[0].swp,
         'prefix': f'{address_map[0].swp_ip}/{address_map[0].plen}',
         'valid_lft': valid_lft,
         'preferred_lft': preferred_lft},
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    out = await IpAddress.replace(input_data=[{dent: [
        {'dev': address_map[3].swp,
         'prefix': f'{address_map[3].swp_ip}/{address_map[3].plen}',
         'valid_lft': valid_lft,
         'preferred_lft': preferred_lft},
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    # Verify ip addresses that were marked as 'deprecated' are deleted
    await asyncio.sleep(5)
    expected_addrs = [
        {'ifname': info.swp,
         'should_exist': info == address_map[1] or info == address_map[2],
         'addr_info': {
            'family': 'inet6',
            'local': info.swp_ip,
            'prefixlen': info.plen}}
        for info in address_map
    ]
    await verify_dut_addrs(dent, expected_addrs)

    # 7. Flush neighbor entries
    out = await IpNeighbor.flush(input_data=[{dent: [
        {'device': port} for port in ports * 2  # flush twice
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to flush neighbors'

    # 8. Send bidirectional traffic
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # Verify packet loss occurs as IP addresses got deleted
    await asyncio.sleep(wait_for_stats)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        # some packet loss is expected
        assert loss >= 99, f'Expected loss: 100%, actual: {loss}%'


async def test_ipv6_secondary_addr(testbed):
    """
    Test Name: test_ipv6_secondary_addr
    Test Suite: suite_functional_ipv6
    Test Overview:
        Verify DUT link local address sends requests and responds to ICMPv6 echo requests
        Verify packets with link local IPv6 addresses not routed
        Verify link local address available, pingable after port down/up
    Test Procedure:
    1. Set ports up. Increase base_reachable_time_ms
    2. Add IP addrs
       - Verify no errors on IP address adding
       - Verify connected routes added and offloaded
    3. Send traffic
       - Verify neighbor resolved
       - Verify clear traffic
    4. Delete first secondary IP addresses on DUT
    5. Send traffic
       - Verify IP addresses are deleted
       - Verify traffic after secondary IP addresses are deleted
    6. Delete other secondary and primary (in this order) IP addresses on DUT
    7. Send traffic
       - Verify IP addresses are deleted
       - Verify no traffic as IP addresses are deleted
    8. Add primary and secondary IPv4 addresses back for two DUT ports
       - Verify IP addresses are added
       - Verify traffic for primary and secondary IP addresses
    """
    num_of_ports = 2
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
    base_reach_time_s = 150

    address_map = (
        # primary
        addr_info(ports[0], tg_ports[0], '2001:1111::1', '2001:1111::2', 64),
        addr_info(ports[1], tg_ports[1], '2001:2222::1', '2001:2222::2', 64),
        # secondary 1
        addr_info(ports[0], tg_ports[0], '2001:1111::3', '2001:1111::4', 64),
        addr_info(ports[1], tg_ports[1], '2001:2222::3', '2001:2222::4', 64),
        # secondary 2
        addr_info(ports[0], tg_ports[0], '2001:1111::5', '2001:1111::6', 64),
        addr_info(ports[1], tg_ports[1], '2001:2222::5', '2001:2222::6', 64),
    )
    config = {
        f'net.ipv6.neigh.{ports[0]}.base_reachable_time_ms': base_reach_time_s * 1000,
        f'net.ipv6.neigh.{ports[1]}.base_reachable_time_ms': base_reach_time_s * 1000,
    }

    # 1. Increase base_reachable_time_ms
    out = await RecoverableSysctl.set(input_data=[{dent: [
        {'variable': variable, 'value': value}
        for variable, value in config.items()
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to update sysctl values'

    # Set ports up
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up'} for port in ports
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # 2. Add IP addrs
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

    # Verify no errors on IP address adding
    expected_addrs = [
        {'ifname': info.swp,
         'should_exist': True,
         'addr_info': {
            'family': 'inet6',
            'local': info.swp_ip,
            'prefixlen': info.plen}}
        for info in address_map
    ]
    await verify_dut_addrs(dent, expected_addrs)

    # Verify connected routes added and offloaded
    expected_routes = [
        {'dev': info.swp,
         'dst': info.swp_ip[:-1] + f'/{info.plen}',
         'should_exist': True,
         'flags': ['rt_trap']}
        for info in address_map
    ]
    await verify_dut_routes(dent, expected_routes)

    # 3. Send traffic
    streams = {
        f"{src['name']} <-> {dst['name']}": {
            'type': 'ipv6',
            'ip_source': src['name'],
            'ip_destination': dst['name'],
            'rate': 10000,  # pps
            'bi_directional': True,
        } for src, dst in zip(dev_groups[tg_ports[0]], dev_groups[tg_ports[1]])
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # Verify clear traffic
    await asyncio.sleep(wait_for_stats)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    assert all(tgen_utils_get_loss(row) == 0 for row in stats.Rows), 'Unexpected traffic loss'

    # Verify neighbor resolved
    expected_neis = [{'dev': info.swp,
                      'dst': info.tg_ip,
                      'should_exist': True,
                      'offload': True,
                      'states': ['REACHABLE']}
                     for info in address_map]
    await verify_dut_neighbors(dent, expected_neis)

    # 4. Delete first secondary IP addresses on DUT
    out = await IpAddress.delete(input_data=[{dent: [
        {'dev': info.swp, 'prefix': f'{info.swp_ip}/{info.plen}'}
        for info in address_map[2:4]
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    # 5. Send traffic
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # Verify IP addresses are deleted
    [addr.update({'should_exist': False}) for addr in expected_addrs[2:4]]
    await verify_dut_addrs(dent, expected_addrs)

    # Verify traffic after secondary IP addresses are deleted
    await asyncio.sleep(wait_for_stats)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    assert all(tgen_utils_get_loss(row) == 0 for row in stats.Rows), 'Unexpected traffic loss'

    # 6. Delete other secondary and primary (in this order) IP addresses on DUT
    out = await IpAddress.delete(input_data=[{dent: [
        {'dev': info.swp, 'prefix': f'{info.swp_ip}/{info.plen}'}
        for info in address_map[4:] + address_map[:2]
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    # 7. Send traffic
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # Verify IP addresses are deleted
    [addr.update({'should_exist': False}) for addr in expected_addrs]
    await verify_dut_addrs(dent, expected_addrs)

    # Verify no traffic as IP addresses are deleted
    await asyncio.sleep(wait_for_stats)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    assert all(tgen_utils_get_loss(row) == 100 for row in stats.Rows), 'Unexpected traffic'

    # 8. Add primary and secondary IPv4 addresses back for two DUT ports
    out = await IpAddress.add(input_data=[{dent: [
        {'dev': info.swp, 'prefix': f'{info.swp_ip}/{info.plen}'}
        for info in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    # Verify IP addresses are added
    [addr.update({'should_exist': True}) for addr in expected_addrs]
    await verify_dut_addrs(dent, expected_addrs)

    # Verify traffic for primary and secondary IP addresses
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    await asyncio.sleep(wait_for_stats)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    assert all(tgen_utils_get_loss(row) == 0 for row in stats.Rows), 'Unexpected traffic loss'
