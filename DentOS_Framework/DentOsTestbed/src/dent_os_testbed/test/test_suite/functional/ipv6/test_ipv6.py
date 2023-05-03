from collections import namedtuple
import asyncio
import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink
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
    verify_dut_neighbors,
    verify_dut_routes,
    verify_dut_addrs,
)

pytestmark = [
    pytest.mark.suite_functional_ipv6,
    pytest.mark.usefixtures('cleanup_ip_addrs', 'enable_ipv6_forwarding'),
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
