from operator import itemgetter
import asyncio
import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.test.test_suite.functional.vrrp.vrrp_utils import (
    setup_topo_for_vrrp,
    verify_vrrp_ping,
)


pytestmark = [
    pytest.mark.suite_functional_vrrp,
    pytest.mark.usefixtures('cleanup_ip_addrs', 'enable_ipv4_forwarding', 'cleanup_bridges'),
    pytest.mark.asyncio,
]


@pytest.mark.parametrize('setup', ['port', 'bridge'])
async def test_vrrp_basic_on(testbed, setup, configure_vrrp):
    """
    Test Name: test_vrrp_basic_on[port|bridge]
    Test Suite: suite_functional_vrrp
    Test Overview:
        Verify basic VRRP configuration
    Test Procedure:
    1. Configure aggregation router
    2. Configure infra devices
    3. Configure VRRP on infra devices
    4. Verify infra[0] serves as master because it has a higher priority,
       Verify infra[1] serves as backup
    5. Make infra[0] unavailable
    6. Verify infra[1] takes over as master
    7. Make infra[0] active again
    8. Expect that it takes over as the master and infra[1] reverts to backup

    Setup:
            agg
         ___| |___
      L0 |       | L1
         |       |
    infra[0]    infra[1]

    Configure:
        agg:
            L0 and L1: master bridge
            bridge: ip address 192.168.1.5/24
        infra[0]:
            L0 (port/bridge):
                ip address 192.168.1.3/24
                vrrp 40 ip 192.168.1.2 prio 254
        infra[1]:
            L1 (port/bridge):
                ip address 192.168.1.4/24
                vrrp 40 ip 192.168.1.2 prio 100
    """
    count = 10
    vrrp_ip = '192.168.1.2'
    vr_id = 40
    use_bridge = setup == 'bridge'

    # 1. Configure aggregation router
    # 2. Configure infra devices
    config = await setup_topo_for_vrrp(testbed, use_bridge)
    infra, agg, bridge, links = itemgetter('infra', 'agg', 'bridge', 'links')(config)

    # 3. Configure VRRP on infra devices
    vrrp_ifaces = [bridge, bridge] if use_bridge else [links[0][infra[0]], links[1][infra[1]]]
    await asyncio.gather(*[
        configure_vrrp(dent, state=state, prio=prio, vr_ip=vrrp_ip, vr_id=vr_id, dev=port)
        for dent, port, state, prio
        in zip(infra, vrrp_ifaces, ['MASTER', 'BACKUP'], [254, 100])])
    await asyncio.sleep(10)  # wait for keepalived to start

    # 4. Verify infra[0] serves as master because it has a higher priority,
    #    Verify infra[1] serves as backup
    await verify_vrrp_ping(agg, infra, ports=(links[0][infra[0]], links[1][infra[1]]),
                           expected=(count, 0), dst=vrrp_ip, count=count)

    # 5. Make infra[0] unavailable
    out = await IpLink.set(input_data=[{
        infra[0].host_name: [{'device': f'vrrp.{vr_id}', 'operstate': 'down'}],
    }])
    assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
        'Failed to disable vrrp'
    await asyncio.sleep(10)  # wait for vrrp to change master

    # 6. Verify infra[1] takes over as master
    await verify_vrrp_ping(agg, infra, ports=(links[0][infra[0]], links[1][infra[1]]),
                           expected=(0, count), dst=vrrp_ip, count=count)

    # 7. Make infra[0] active again
    out = await IpLink.set(input_data=[{
        infra[0].host_name: [{'device': f'vrrp.{vr_id}', 'operstate': 'up'}],
    }])
    assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
        'Failed to enable vrrp'
    await asyncio.sleep(10)  # wait for vrrp to change master

    # 8. Expect that it takes over as the master and infra[1] reverts to backup
    await verify_vrrp_ping(agg, infra, ports=(links[0][infra[0]], links[1][infra[1]]),
                           expected=(count, 0), dst=vrrp_ip, count=count)


@pytest.mark.parametrize('setup', ['port', 'bridge'])
async def test_vrrp_basic_down_on(testbed, setup, configure_vrrp):
    """
    Test Name: test_vrrp_basic_down_on[port|bridge]
    Test Suite: suite_functional_vrrp
    Test Overview:
        Verify VRouter doesn't reply to pings when macvlan state is down on both routers
    Test Procedure:
    1. Configure aggregation router
    2. Configure infra devices
    3. Configure VRRP on infra devices
    4. Verify infra[0] serves as master because it has a higher priority,
       Verify infra[1] serves as backup
    5. Make infra[0] unavailable
    6. Verify infra[1] takes over as master
    7. Make infra[1] also unavailable
    8. Expect no ICMP reply

    Setup:
            agg
         ___| |___
      L0 |       | L1
         |       |
    infra[0]    infra[1]

    Configure:
        agg:
            L0 and L1: master bridge
            bridge: ip address 192.168.1.5/24
        infra[0]:
            L0 (port/bridge):
                ip address 192.168.1.3/24
                vrrp 40 ip 192.168.1.2 prio 200
        infra[1]:
            L1 (port/bridge):
                ip address 192.168.1.4/24
                vrrp 40 ip 192.168.1.2 prio 100
    """
    count = 10
    vrrp_ip = '192.168.1.2'
    vr_id = 40
    use_bridge = setup == 'bridge'

    # 1. Configure aggregation router
    # 2. Configure infra devices
    config = await setup_topo_for_vrrp(testbed, use_bridge)
    infra, agg, bridge, links = itemgetter('infra', 'agg', 'bridge', 'links')(config)

    # 3. Configure VRRP on infra devices
    vrrp_ifaces = [bridge, bridge] if use_bridge else [links[0][infra[0]], links[1][infra[1]]]
    await asyncio.gather(*[
        configure_vrrp(dent, state=state, prio=prio, vr_ip=vrrp_ip, vr_id=vr_id, dev=port)
        for dent, port, state, prio
        in zip(infra, vrrp_ifaces, ['MASTER', 'BACKUP'], [200, 100])])
    await asyncio.sleep(10)  # wait for keepalived to start

    # 4. Verify infra[0] serves as master because it has a higher priority,
    #    Verify infra[1] serves as backup
    await verify_vrrp_ping(agg, infra, ports=(links[0][infra[0]], links[1][infra[1]]),
                           expected=(count, 0), dst=vrrp_ip, count=count)

    # 5. Make infra[0] unavailable
    out = await IpLink.set(input_data=[{
        infra[0].host_name: [{'device': f'vrrp.{vr_id}', 'operstate': 'down'}],
    }])
    assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
        'Failed to disable vrrp'
    await asyncio.sleep(10)  # wait for vrrp to change master

    # 6. Verify infra[1] takes over as master
    await verify_vrrp_ping(agg, infra, ports=(links[0][infra[0]], links[1][infra[1]]),
                           expected=(0, count), dst=vrrp_ip, count=count)

    # 7. Make infra[1] also unavailable
    out = await IpLink.set(input_data=[{
        infra[1].host_name: [{'device': f'vrrp.{vr_id}', 'operstate': 'down'}],
    }])
    assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
        'Failed to disable vrrp'
    await asyncio.sleep(10)  # wait for vrrp to change master

    # 8. Expect no ICMP reply
    await verify_vrrp_ping(agg, infra, ports=(links[0][infra[0]], links[1][infra[1]]),
                           expected=(0, 0), dst=vrrp_ip, count=count)
