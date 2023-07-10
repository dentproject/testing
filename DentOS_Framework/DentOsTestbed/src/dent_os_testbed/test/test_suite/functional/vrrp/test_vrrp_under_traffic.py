from operator import itemgetter
import asyncio
import pytest
import random
import math

from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_poll,
)

from dent_os_testbed.test.test_suite.functional.vrrp.vrrp_utils import (
    setup_topo_for_vrrp,
    get_rx_bps,
)


pytestmark = [
    pytest.mark.suite_functional_vrrp,
    pytest.mark.usefixtures('cleanup_ip_addrs', 'enable_ipv4_forwarding',
                            'cleanup_bridges', 'cleanup_tgen'),
    pytest.mark.asyncio,
]


@pytest.mark.parametrize('setup', ['bridge', 'vlan', 'port'])
async def test_vrrp_under_traffic(testbed, setup, configure_vrrp):
    """
    Test Name: test_vrrp_under_traffic
    Test Suite: suite_functional_vrrp
    Test Overview:
        Verify basic VRRP configuration when a macvlan is created over a bridge and under heavy traffic
    Test Procedure:
    1. Configure aggregation router
    2. Configure infra devices
    3. Configure VRRP on infra devices

    Setup:
                   TG L0     ______
            agg ------------ |    |
         ___| |___           |    |
      L0 |       | L1        | TG |
         |       |           |    |
    infra[0] -- infra[1] --- |____|
             L2         TG L1

    Configure:
        agg:
            L0, L1, TG L0: master bridge
        infra[0]:
            L0 (port/bridge):
                ip address 192.168.1.3/24
                vrrp 40 ip 192.168.1.2 prio 200
            L2:
                ip address 192.168.3.10/24
                route 192.168.2.2 via 192.168.3.11
        infra[1]:
            L1 (port/bridge):
                ip address 192.168.1.4/24
                vrrp 40 ip 192.168.1.2 prio 100
            TG L1:
                ip address 192.168.2.1/24
            L2:
                ip address 192.168.3.11/24
        TG:
            L0: ip address 192.168.1.5/24
            L1: ip address 192.168.2.2/24
    """
    wait_for_keepalived = 15
    vrrp_ip = '192.168.1.2'
    vr_id = 40
    packet_size = random.randint(100, 1500)
    max_rate_bit = 1_000_000_000  # 1Gbit, 100%
    rate_bit = max_rate_bit * 0.85  # ~850Mbit, 85%
    rate_bps = rate_bit // 8  # ~100Mbps, 85%

    if setup == 'bridge':
        use_bridge = True
        vlan = None
    elif setup == 'vlan':
        use_bridge = True
        vlan = random.randint(2, 4094) if setup == 'vlan' else None
    else:
        use_bridge = False
        vlan = None

    # 1. Configure aggregation router
    config = await setup_topo_for_vrrp(testbed, use_bridge, use_vid=vlan, use_tgen=True, vrrp_ip=vrrp_ip)
    infra, tgen_dev, bridge, links, tg_links, dev_groups, vlan_dev = \
        itemgetter('infra', 'tgen_dev', 'bridge', 'links', 'tg_links', 'dev_groups', 'vlan_dev')(config)

    if setup == 'bridge':
        vrrp_ifaces = [bridge, bridge]
    elif setup == 'vlan':
        vrrp_ifaces = [vlan_dev, vlan_dev]
    else:
        vrrp_ifaces = [links[0][infra[0]], links[1][infra[1]]]

    # 3. Configure VRRP on infra devices
    await asyncio.gather(*[
        configure_vrrp(dent, state=state, prio=prio, vr_ip=vrrp_ip, vr_id=vr_id, dev=port)
        for dent, port, state, prio
        in zip(infra, vrrp_ifaces, ['MASTER', 'BACKUP'], [200, 100])])
    await asyncio.sleep(wait_for_keepalived)

    streams = {
        'data traffic': {
            'type': 'ipv4',
            'ip_source': dev_groups[tg_links[0][tgen_dev]][0]['name'],  # TG L0
            'ip_destination': dev_groups[tg_links[1][tgen_dev]][0]['name'],  # TG L1
            'frameSize': packet_size,
            'frame_rate_type': 'bps_rate',
            'rate': rate_bit,
        },
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    await tgen_utils_start_traffic(tgen_dev)
    # don't stop

    for state, expected in [('up', [rate_bps, 0]),
                            ('down', [0, rate_bps]),
                            ('up', [rate_bps, 0])]:
        out = await IpLink.set(input_data=[{
            infra[0].host_name: [{'device': f'vrrp.{vr_id}', 'operstate': state}],
        }])
        assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
            'Failed to enable/disable vrrp'
        await asyncio.sleep(wait_for_keepalived)

        async def verify_correct_traffic(dent, port, expected_rate):
            current_rate = await get_rx_bps(dent, port)
            assert math.isclose(current_rate, expected_rate, rel_tol=0.10, abs_tol=1000), \
                f'Expected rate for {dent}: {expected_rate}, actual: {current_rate}'

        await asyncio.gather(*[tgen_utils_poll(infra[idx], verify_correct_traffic,
                                               dent=infra[idx].host_name, port=links[idx][infra[idx]],
                                               expected_rate=expected[idx], timeout=90)
                               for idx in [0, 1]])
