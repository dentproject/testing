from collections import namedtuple
import asyncio
import pytest
import random
import time

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.ip.ip_neighbor import IpNeighbor
from dent_os_testbed.lib.os.recoverable_sysctl import RecoverableSysctl

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_start_traffic,
    tgen_utils_setup_streams,
    tgen_utils_stop_traffic,
    tgen_utils_get_loss,
    tgen_utils_send_ns,
)

from dent_os_testbed.utils.test_utils.tb_utils import (
    tb_ping_device,
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


async def wait_for_nei_state(dent_dev, expected_neis, timeout=60, poll_interval=10):
    dent_dev.applog.info('Begin neighbor polling')
    start = time.time()
    while time.time() < start + timeout:
        try:
            await verify_dut_neighbors(dent_dev.host_name, expected_neis)
        except (AssertionError, LookupError) as e:
            dent_dev.applog.debug(f'Neighbors did not match expectation. Trying again in {poll_interval}s\n{e}')
            await asyncio.sleep(poll_interval)
        else:
            dent_dev.applog.info(f'Neighbors matched expectation after {(time.time() - start) // 1}s')
            return

    raise TimeoutError(f'Neighbors did not have expected state\n{expected_neis}')


async def test_ipv6_nei_ageing(testbed):
    """
    Test Name: test_ipv6_nei_ageing
    Test Suite: suite_functional_ipv6
    Test Overview:
        Verify neighbor ageing and flush
    Test Procedure:
    0. Set IP addresses on DUT ports, add ip interfaces to TG
    1.1 Set gc_interval, but leave default threshold values
    1.2 Resolve neighbors
    1.3 Check that neighbor entries are STALE
    1.4 Check that neighbor entries are still STALE and not aged
    2.1 Set a large gc_stale_time_s value, set small threshold values
    2.2 Resolve neighbors
    2.3 Check that neighbor entries are REACHABLE
    2.4 Check that neighbor entries are STALE
    2.5 Check that neighbor entries are aged
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
    nei_update_time_s = 5
    base_reach_time_s = 15
    gc_interval_s = 5
    gc_stale_time_s = 30

    address_map = (
        addr_info(ports[0], tg_ports[0], '2001:1111::1', '2001:1111::2', 64),
        addr_info(ports[0], tg_ports[0], '2001:2222::1', '2001:2222::2', 64),
        addr_info(ports[1], tg_ports[1], '2001:3333::1', '2001:3333::2', 64),
        addr_info(ports[1], tg_ports[1], '2001:4444::1', '2001:4444::2', 64),
    )
    config = {
        'net.ipv6.neigh.default.gc_interval': gc_interval_s,
        'net.ipv6.neigh.default.gc_stale_time': gc_stale_time_s,
        f'net.ipv6.neigh.{ports[0]}.gc_stale_time': gc_stale_time_s,
        f'net.ipv6.neigh.{ports[1]}.gc_stale_time': gc_stale_time_s,
        'net.ipv6.neigh.default.gc_thresh1': 1,
        'net.ipv6.neigh.default.gc_thresh2': 20,
        'net.ipv6.neigh.default.gc_thresh3': 30,
        'net.ipv6.neigh.default.base_reachable_time_ms': base_reach_time_s * 1000,
        'net.ipv6.neigh.default.delay_first_probe_time': nei_update_time_s,
    }

    # 0. Set IP addresses on DUT ports, add ip interfaces to TG
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

    await tgen_utils_setup_streams(tgen_dev, None, {
        'dummy': {
            'type': 'raw',
            'ep_source': ports[0],
            'ep_destination': ports[1]
        },
    })

    expected_routes = [
        {'dev': info.swp,
         'dst': info.swp_ip[:-1] + f'/{info.plen}',
         'should_exist': True,
         'flags': ['rt_trap']}
        for info in address_map
    ]
    await verify_dut_routes(dent, expected_routes)

    # Scenario #1
    # 1.1 Set gc_interval, but leave default threshold values
    out = await RecoverableSysctl.set(input_data=[{dent: [
        {'variable': variable, 'value': value}
        for variable, value in config.items() if 'gc_thresh' not in variable
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to update sysctl values'

    # 1.2 Resolve neighbors
    out = await tgen_utils_send_ns(tgen_dev, ({'ixp': tg} for tg in tg_ports))
    assert all(rc['success'] for rc in out), 'Failed to send NS from TG'

    out = await asyncio.gather(*[
        tb_ping_device(dent_dev, info.tg_ip, pkt_loss_treshold=0, dump=True, count=1)
        for info in address_map
    ])
    assert all(rc == 0 for rc in out), 'Some pings did not have a reply'

    # 1.3 Check that neighbor entries are STALE
    expected_neis = [
        {'dev': info.swp, 'dst': info.tg_ip, 'should_exist': True, 'offload': True, 'states': ['STALE']}
        for info in address_map
    ]
    # Neighbor ageing depends on linux behavior.
    # Changing state from REACHABLE to STALE should take
    # between base_reach_time_s * 1/2 and base_reach_time_s * 3/2,
    # but we are waiting a little longer here.
    # If neighbors did not age in 60s then something is definitely wrong.
    await wait_for_nei_state(dent_dev, expected_neis, timeout=60)

    # 1.4 Check that neighbor entries are still STALE and not aged
    dent_dev.applog.info(f'Wait for a total of {gc_stale_time_s * 3 = }s to make sure that neighbors did not age')
    await asyncio.sleep(gc_stale_time_s * 3)
    await verify_dut_neighbors(dent, expected_neis)  # no need for polling here

    # Scenario #2
    # 2.1 Set a large gc_stale_time_s value, set small threshold values
    new_gc_stale_time_s = gc_stale_time_s * 3

    out = await RecoverableSysctl.set(input_data=[{dent: [
        {'variable': variable, 'value': value}
        for variable, value in config.items() if 'stale_time' not in variable
    ] + [
        {'variable': variable, 'value': new_gc_stale_time_s}
        for variable in config if 'stale_time' in variable
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to update sysctl values'

    # 2.2 Resolve neighbors
    out = await tgen_utils_send_ns(tgen_dev, ({'ixp': tg} for tg in tg_ports))
    assert all(rc['success'] for rc in out), 'Failed to send NS from TG'

    out = await asyncio.gather(*[
        tb_ping_device(dent_dev, info.tg_ip, pkt_loss_treshold=0, dump=True, count=1)
        for info in address_map
    ])
    assert all(rc == 0 for rc in out), 'Some pings did not have a reply'

    start = time.time()

    # 2.3 Check that neighbor entries are REACHABLE
    expected_neis = [
        {'dev': info.swp, 'dst': info.tg_ip, 'should_exist': True, 'offload': True, 'states': ['REACHABLE']}
        for info in address_map
    ]
    await wait_for_nei_state(dent_dev, expected_neis, poll_interval=nei_update_time_s)
    elapsed = time.time() - start
    assert elapsed < base_reach_time_s, \
        f'Expected neighbors to be REACHABLE after no more than {base_reach_time_s = }s, ' + \
        f'but waited for {elapsed // 1}s'

    # 2.4 Check that neighbor entries are STALE
    [nei.update({'states': ['STALE']}) for nei in expected_neis]
    await wait_for_nei_state(dent_dev, expected_neis)
    elapsed = time.time() - start
    assert elapsed < new_gc_stale_time_s + gc_interval_s, \
        f'Expected neighbors to be STALE after no more than {new_gc_stale_time_s + gc_interval_s = }s, ' + \
        f'but waited for {elapsed // 1}s'

    # 2.5 Check that neighbor entries are aged
    [nei.update({'should_exist': False}) for nei in expected_neis]
    await wait_for_nei_state(dent_dev, expected_neis, timeout=new_gc_stale_time_s*2)
    elapsed = time.time() - start
    assert gc_stale_time_s*2 < elapsed < new_gc_stale_time_s*2, \
        f'Expected neighbors to be STALE after no more than {new_gc_stale_time_s*2 = }s, ' + \
        f'but waited for {elapsed // 1}s'


async def test_ipv6_nei_change(testbed):
    """
    Test Name: test_ipv6_nei_change
    Test Suite: suite_functional_ipv6
    Test Overview:
        Verify neighbor entries modification, delete and flush
    Test Procedure:
    1. Add IP addrs, configure hosts on TG
       - Verify IP addresses added
       - Verify routes created
    2. Configure protocol interfaces on TG
    3. Send bidirectional traffic between TG hosts
       - Verify neighbor on DUT
    4. Change neighbor nud state to permanent
       - Verify nud change
       - Verify its not stale after timeout
       - Verify neighbor entries have been offloaded
    5. Change neighbor nud state to reachable
       - Verify neighbor nud change
       - Verify entries will change nud state to stale after timeout
    6. Add two permanent neighbor entries and two stale neighbor entries
       - Verify neighbor entries were added successfully
    7. Flush specific entries by prefix and state
       - Verify all entries by prefix and nud state are flushed,
         except entries that do not fit by prefix and nud state
    8. Initiate neighbor from TG to restore entries
    9. Delete one permanent and one dynamic entry
       - Verify neighbor entries are deleted
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
    gc_interval_s = 15
    gc_thresh = 20
    nei_update_time_s = 5
    base_reach_time_s = 35

    address_map = (
        addr_info(ports[0], tg_ports[0], '2001:1111::1', '2001:1111::2', 64),
        addr_info(ports[1], tg_ports[1], '2001:2222::1', '2001:2222::2', 64),
    )
    config = {
        'net.ipv6.neigh.default.gc_interval': gc_interval_s,
        'net.ipv6.neigh.default.gc_thresh1': gc_thresh,
        'net.ipv6.neigh.default.base_reachable_time_ms': base_reach_time_s * 1000,
        'net.ipv6.neigh.default.delay_first_probe_time': nei_update_time_s,
    }

    out = await RecoverableSysctl.set(input_data=[{dent: [
        {'variable': variable, 'value': value}
        for variable, value in config.items() if 'gc_thresh' not in variable
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to update sysctl values'

    # 1. Add IP addrs, configure hosts on TG
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up'} for port in ports
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    out = await IpAddress.add(input_data=[{dent: [
        {'dev': info.swp, 'prefix': f'{info.swp_ip}/{info.plen}'}
        for info in address_map
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    # Verify IP addresses added
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

    # Verify routes created
    expected_routes = [
        {'dev': info.swp,
         'dst': info.swp_ip[:-1] + f'/{info.plen}',
         'should_exist': True,
         'flags': ['rt_trap']}
        for info in address_map
    ]
    await verify_dut_routes(dent, expected_routes)

    # 2. Configure protocol interfaces on TG
    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': info.tg, 'ip': info.tg_ip, 'gw': info.swp_ip,
         'plen': info.plen, 'version': 'ipv6'}
        for info in address_map
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    # 3. Send bidirectional traffic between TG hosts
    await tgen_utils_setup_streams(tgen_dev, None, {'dummy': {'type': 'ipv6'}})

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    await asyncio.sleep(wait_for_stats)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    assert all(tgen_utils_get_loss(row) == 0 for row in stats.Rows), 'Unexpected traffic loss'

    # Verify neighbor on DUT
    expected_neis = [
        {'dev': info.swp,
         'dst': info.tg_ip,
         'should_exist': True,
         'offload': True,
         'states': ['REACHABLE', 'STALE']}
        for info in address_map
    ]
    await wait_for_nei_state(dent_dev, expected_neis, poll_interval=nei_update_time_s)

    # 4. Change neighbor nud state to permanent
    out = await IpNeighbor.show(input_data=[{dent: [
        {'cmd_options': '-j -6'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get DUT neighbors'

    dut_nei = {
        nei['dev']: {'ip': nei['dst'], 'lladdr': nei['lladdr']}
        for nei in out[0][dent]['parsed_output']
        if nei['dev'] in ports and not nei['dst'].startswith('f')
    }

    out = await IpNeighbor.change(input_data=[{dent: [
        {'dev': dev, 'lladdr': nei['lladdr'], 'address': nei['ip'], 'nud': 'permanent'}
        for dev, nei in dut_nei.items()
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to update DUT neighbors'

    # Verify nud change
    [nei.update({'states': ['PERMANENT']}) for nei in expected_neis]
    await verify_dut_neighbors(dent, expected_neis)

    # Verify its not stale after timeout
    dent_dev.applog.info('Waiting for neighbor state to change')
    await asyncio.sleep(base_reach_time_s*1.5 + nei_update_time_s*2)

    # Verify neighbor entries have been offloaded
    await verify_dut_neighbors(dent, expected_neis)

    # 5. Change neighbor nud state to reachable
    out = await IpNeighbor.change(input_data=[{dent: [
        {'dev': dev, 'lladdr': nei['lladdr'], 'address': nei['ip'], 'nud': 'reachable'}
        for dev, nei in dut_nei.items()
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to update DUT neighbors'

    # Verify neighbor nud change
    [nei.update({'states': ['REACHABLE']}) for nei in expected_neis]
    await verify_dut_neighbors(dent, expected_neis)

    # Verify entries will change nud state to stale after timeout
    [nei.update({'states': ['STALE']}) for nei in expected_neis]
    await wait_for_nei_state(dent_dev, expected_neis)

    # 6. Add two permanent neighbor entries and two stale neighbor entries
    rand_ip = [info.tg_ip[:-1] + f'{idx + 1:x}:{random.randint(0xf, 0xfff0):x}'
               for idx, info in enumerate(address_map + address_map)]
    rand_mac = [f'02:00:00:00:{idx:02x}:{random.randint(1, 255):02x}' for idx in range(4)]
    nei_state = ['permanent', 'permanent', 'stale', 'stale']

    out = await IpNeighbor.add(input_data=[{dent: [
        {'dev': dev, 'lladdr': lladdr, 'address': ip, 'nud': state}
        for dev, ip, lladdr, state in zip(ports + ports, rand_ip, rand_mac, nei_state)
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to update DUT neighbors'

    # Verify neighbor entries were added successfully
    expected_neis += [
        {'dev': dev,
         'dst': ip,
         'lladdr': lladdr,
         'should_exist': True,
         'offload': True,
         'states': [state.upper()]}
        for dev, ip, lladdr, state in zip(ports + ports, rand_ip, rand_mac, nei_state)
    ]
    await verify_dut_neighbors(dent, expected_neis)

    # 7. Flush specific entries by prefix and state
    out = await IpNeighbor.flush(input_data=[{dent: [
        {'dev': address_map[0].swp,
         'address': address_map[0].swp_ip[:-1] + f'/{address_map[0].plen}',  # 2001:1111::/64
         'nud': 'permanent'},
        {'dev': address_map[1].swp,
         'address': address_map[1].swp_ip[:-1] + f'/{address_map[1].plen}'},  # 2001:2222::/64
    ] * 2  # flush twice
    }])
    assert out[0][dent]['rc'] == 0, 'Failed to update DUT neighbors'

    # Verify all entries by prefix and nud state are flushed,
    # except entries that do not fit by prefix and nud state
    expected_neis = [
        {'dev': info.swp,
         'dst': info.tg_ip,
         'should_exist': info.swp == address_map[0].swp,
         'offload': True,
         'states': ['STALE']}
        for info in address_map
    ]
    expected_neis += [
        {'dev': dev,
         'dst': ip,
         'lladdr': lladdr,
         'should_exist': ip == rand_ip[1] or ip == rand_ip[2],
         'offload': True,
         'states': [state.upper()]}
        for dev, ip, lladdr, state in zip(ports + ports, rand_ip, rand_mac, nei_state)
    ]
    await verify_dut_neighbors(dent, expected_neis)

    # 8. Initiate neighbor from TG to restore entries
    out = await tgen_utils_send_ns(tgen_dev, ({'ixp': tg} for tg in tg_ports))
    assert all(rc['success'] for rc in out), 'Failed to send NS from TG'

    # 9. Delete one permanent and one dynamic entry
    out = await IpNeighbor.delete(input_data=[{dent: [
        {'dev': dev, 'address': ip, 'lladdr': lladdr, 'nud': state}
        for dev, ip, lladdr, state in zip(ports[::-1], rand_ip[1:3], rand_mac[1:3], nei_state[1:3])
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to update DUT neighbors'

    # Verify neighbor entries are deleted
    expected_neis = [
        {'dev': info.swp,
         'dst': info.tg_ip,
         'should_exist': True,
         'offload': True,
         'states': ['REACHABLE', 'STALE']}
        for info in address_map
    ]
    expected_neis += [
        {'dev': dev,
         'dst': ip,
         'lladdr': lladdr,
         'should_exist': False}
        for dev, ip, lladdr in zip(ports + ports, rand_ip, rand_mac)
    ]
    await wait_for_nei_state(dent_dev, expected_neis, timeout=base_reach_time_s)
