from operator import itemgetter
from math import isclose as is_close
import asyncio
import pytest

from dent_os_testbed.lib.tc.tc_filter import TcFilter
from dent_os_testbed.lib.tc.tc_qdisc import TcQdisc

from dent_os_testbed.test.test_suite.functional.vrrp.vrrp_utils import (
    setup_topo_for_vrrp,
)

from dent_os_testbed.utils.test_utils.tc_flower_utils import (
    tcutil_get_tc_stats_pref_map,
)


pytestmark = [
    pytest.mark.suite_functional_vrrp,
    pytest.mark.usefixtures('cleanup_ip_addrs', 'enable_ipv4_forwarding', 'cleanup_bridges'),
    pytest.mark.asyncio,
]


@pytest.mark.usefixtures('cleanup_qdiscs')
async def test_vrrp_advert_interval(testbed, configure_vrrp):
    """
    Test Name: test_vrrp_advert_interval
    Test Suite: suite_functional_vrrp
    Test Overview:
        Verify VRRP advertisement interval setting
    Test Procedure:
    1. Configure aggregation router
    2. Configure infra devices
    3. Configure VRRP on infra devices
    4. Capture VRRP advertisement packets from each DUT for X seconds
    5. Verify X packets are received
    6. Change advertisement interval to 0.1 second
    7. Verify 10*X packets are received

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
    wait_for_keepalived = 10
    sleep_time_s = 30
    vrrp_ip = '192.168.1.2'
    vr_id = 40
    pref = 100
    tolerance = 0.1  # 10%

    # 1. Configure aggregation router
    # 2. Configure infra devices
    config = await setup_topo_for_vrrp(testbed, use_bridge=True)
    infra, agg, bridge, links = itemgetter('infra', 'agg', 'bridge', 'links')(config)
    links = [link for link in links if agg in link]

    # 3. Configure VRRP on infra devices
    advert_int = 1
    await asyncio.gather(*[
        configure_vrrp(dent, state=state, prio=prio, vr_ip=vrrp_ip, vr_id=vr_id,
                       dev=bridge, additional_opts=[f'advert_int {advert_int}'])
        for dent, state, prio
        in zip(infra, ['MASTER', 'BACKUP'], [200, 100])])
    await asyncio.sleep(wait_for_keepalived)

    # 4. Capture VRRP advertisement packets from each DUT for X seconds
    out = await TcQdisc.add(input_data=[{agg.host_name: [
        {'dev': link[agg], 'direction': 'ingress'}
        for link in links
    ]}])
    assert out[0][agg.host_name]['rc'] == 0, 'Failed to create qdisc'

    out = await TcFilter.add(input_data=[{agg.host_name: [
        {'dev': link[agg],
         'action': 'pass',
         'direction': 'ingress',
         'protocol': 'ip',
         'pref': pref,
         'filtertype': {'skip_sw': '', 'dst_ip': '224.0.0.18'}}
        for link in links
    ]}])
    assert out[0][agg.host_name]['rc'] == 0, 'Failed to add tc filter rules'

    agg.applog.info(f'Capture packets for {sleep_time_s}s')
    await asyncio.sleep(sleep_time_s)

    # 5. Verify X packets are received
    stats = await asyncio.gather(*[tcutil_get_tc_stats_pref_map(agg.host_name, link[agg])
                                   for link in links])

    assert is_close(stats[0][pref]['packets'], sleep_time_s / advert_int, rel_tol=tolerance), \
        f'Expected {sleep_time_s / advert_int} advertisement packets from {infra[0]}'
    assert stats[1][pref]['packets'] == 0, \
        f'Expected 0 advertisement packets from {infra[1]} (backup)'

    # 6. Change advertisement interval to 0.1 second
    #    Also change roles of infra[0] (now backup) and infra[1] (now master)
    advert_int = 0.1
    await asyncio.gather(*[
        configure_vrrp(dent, state=state, prio=prio, vr_ip=vrrp_ip, vr_id=vr_id,
                       dev=bridge, additional_opts=[f'advert_int {advert_int}'])
        for dent, state, prio
        in zip(infra, ['BACKUP', 'MASTER'], [100, 200])])
    await asyncio.sleep(wait_for_keepalived)

    # 7. Verify 10*X packets are received
    old_stats = await asyncio.gather(*[tcutil_get_tc_stats_pref_map(agg.host_name, link[agg])
                                       for link in links])

    agg.applog.info(f'Capture packets for {sleep_time_s}s')
    await asyncio.sleep(sleep_time_s)

    new_stats = await asyncio.gather(*[tcutil_get_tc_stats_pref_map(agg.host_name, link[agg])
                                       for link in links])

    pkts = [_new[pref]['packets'] - _old[pref]['packets'] for _new, _old in zip(new_stats, old_stats)]

    assert pkts[0] == 0, \
        f'Expected 0 advertisement packets from {infra[0]} (backup)'
    assert is_close(pkts[1], sleep_time_s / advert_int, rel_tol=tolerance), \
        f'Expected {sleep_time_s / advert_int} advertisement packets from {infra[1]}'
