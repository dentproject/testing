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
async def test_vrrp_preempt_on(testbed, setup, configure_vrrp):
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
    5. Change VRRP configuration on infra[1] to have a higher priority and 'nopreempt' flag
    6. Verify infra[0] is still master

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
                vrrp 40 ip 192.168.1.2 prio 100 (prio 210 nopreempt)
    """
    wait_for_keepalived = 10
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
    await asyncio.sleep(wait_for_keepalived)

    # 4. Verify infra[0] serves as master because it has a higher priority,
    #    Verify infra[1] serves as backup
    await verify_vrrp_ping(agg, infra, ports=(links[0][infra[0]], links[1][infra[1]]),
                           expected=(count, 0), dst=vrrp_ip, count=count)

    # 5. Change VRRP configuration on infra[1] to have a higher priority and 'nopreempt' flag
    await configure_vrrp(infra[1], state='BACKUP', prio=210, vr_ip=vrrp_ip, vr_id=vr_id,
                         dev=links[1][infra[1]], additional_opts=['nopreempt'])
    await asyncio.sleep(wait_for_keepalived)

    # 6. Verify infra[0] is still MASTER
    await verify_vrrp_ping(agg, infra, ports=(links[0][infra[0]], links[1][infra[1]]),
                           expected=(count, 0), dst=vrrp_ip, count=count)
