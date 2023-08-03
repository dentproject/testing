from operator import itemgetter
import asyncio
import pytest

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
async def test_vrrp_priority_on(testbed, setup, configure_vrrp):
    """
    Test Name: test_vrrp_priority_on[port|bridge]
    Test Suite: suite_functional_vrrp
    Test Overview:
        Verify that the VR configured over a port with the highest priority becomes the master.
    Test Procedure:
    1. Configure aggregation router
    2. Configure infra devices
    3. Configure VRRP on infra devices
    4. Verify infra[0] serves as master because it has a higher priority,
       Verify infra[1] serves as backup
    5. Set infra[1] VRRP priority greater than the infra[0] VRRP priority
    6. Verify infra[1] takes over as a master and infra[0] becomes a backup router

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
                vrrp 40 ip 192.168.1.2 prio 100(210)
    """
    wait_for_keepalived = 15
    count = 10
    vrrp_ip = '192.168.1.2'
    use_bridge = setup == 'bridge'

    # 1. Configure aggregation router
    # 2. Configure infra devices
    config = await setup_topo_for_vrrp(testbed, use_bridge)
    infra, agg, bridge, links = itemgetter('infra', 'agg', 'bridge', 'links')(config)

    # 3. Configure VRRP on infra devices
    vrrp_ifaces = [bridge, bridge] if use_bridge else [links[0][infra[0]], links[1][infra[1]]]
    await asyncio.gather(*[
        configure_vrrp(dent, state=state, prio=prio, vr_ip=vrrp_ip, dev=port)
        for dent, port, state, prio
        in zip(infra, vrrp_ifaces, ['MASTER', 'BACKUP'], [200, 100])])
    await asyncio.sleep(wait_for_keepalived)

    # 4. Verify infra[0] serves as master because it has a higher priority,
    #    Verify infra[1] serves as backup
    await verify_vrrp_ping(agg, infra, ports=(links[0][infra[0]], links[1][infra[1]]),
                           expected=(count, 0), dst=vrrp_ip, count=count)

    # 5. Set infra[1] VRRP priority greater than the infra[0] VRRP priority
    await configure_vrrp(infra[1], state='MASTER', prio=210, vr_ip=vrrp_ip,
                         dev=links[1][infra[1]] if setup == 'port' else bridge)
    await asyncio.sleep(wait_for_keepalived)  # wait for keepalived to restart

    # 6. Verify infra[1] takes over as a master and infra[0] becomes a backup router
    await verify_vrrp_ping(agg, infra, ports=(links[0][infra[0]], links[1][infra[1]]),
                           expected=(0, count), dst=vrrp_ip, count=count)
