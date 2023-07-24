from operator import itemgetter
from math import isclose as is_close
import asyncio
import pytest

from dent_os_testbed.lib.tc.tc_filter import TcFilter
from dent_os_testbed.lib.tc.tc_qdisc import TcQdisc

from dent_os_testbed.test.test_suite.functional.vrrp.vrrp_utils import (
    setup_topo_for_vrrp,
    vr_id_to_mac,
)

from dent_os_testbed.utils.test_utils.tc_flower_utils import (
    tcutil_get_tc_stats_pref_map,
)

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
)

from dent_os_testbed.test.test_suite.functional.devlink.devlink_utils import (
    verify_cpu_traps_rate_code_avg,
    CPU_STAT_CODE_VRRP,
    CPU_MAX_VRRP_PPS,
)


pytestmark = [
    pytest.mark.suite_functional_vrrp,
    pytest.mark.usefixtures('cleanup_ip_addrs', 'cleanup_tgen', 'enable_ipv4_forwarding', 'cleanup_bridges'),
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
    wait_for_keepalived = 15
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


@pytest.mark.usefixtures('cleanup_tgen', 'define_bash_utils')
async def test_vrrp_advert_overflow(testbed, configure_vrrp):
    """
    Test Name: test_vrrp_advert_overflow
    Test Suite: suite_functional_vrrp
    Test Overview:
        Verify DUT stability and availability under VRRP advertisements overflow
    Test Procedure:
    1. Configure aggregation router
    2. Configure infra devices
    3. Configure VRRP on infra devices
    4. Send VRRPv3 advertisements for 60 seconds
    5. Verify both infra devices trap those advertisements and they remain stable

    Setup:
                   TG L0     ______
            agg ------------ |    |
         ___| |___           |    |
      L0 |       | L1        | TG |
         |       |           |    |
    infra[0]    infra[1]     |____|

    Configure:
        agg:
            L0, L1, TG L0: master bridge
        infra[0]:
            L0: master bridge
                ip address 192.168.1.3/24
                vrrp 40 ip 192.168.1.2 prio 250
        infra[1]:
            L1: master bridge
                ip address 192.168.1.4/24
                vrrp 40 ip 192.168.1.2 prio 100
        TG:
            L0: ip address 192.168.1.5/24
                vrrp 40 ip 192.168.1.2 prio 200
    """
    """
    [no ethernet header]
    Protocol: VRRP
    Source Address: 192.168.1.5
    Destination Address: 224.0.0.18
    Virtual Router ID: 40
    Priority: 250
    VRRP IP Address: 192.168.1.2
    """
    vrrp_packet = '45C0002000010000FF7018EDC0A80105E00000123128FA010064708AC0A80102'
    vrrp_ip = '192.168.1.2'
    vr_id = 40
    sleep_time_s = 60
    wait_for_keepalived = 15

    # 1. Configure aggregation router
    # 2. Configure infra devices
    config = await setup_topo_for_vrrp(testbed, use_bridge=True, use_tgen=True, vrrp_ip=vrrp_ip)
    infra, tgen_dev, bridge, links, tg_links, dev_groups, ep_ip = \
        itemgetter('infra', 'tgen_dev', 'bridge', 'links', 'tg_links', 'dev_groups', 'ep_ip')(config)

    # 3. Configure VRRP on infra devices
    await asyncio.gather(*[
        configure_vrrp(dent, state=state, prio=prio, vr_ip=vrrp_ip, vr_id=vr_id, dev=bridge)
        for dent, state, prio
        in zip(infra, ['MASTER', 'BACKUP'], [200, 100])])
    await asyncio.sleep(wait_for_keepalived)

    # 4. Send VRRPv3 advertisements for 60 seconds
    streams = {
        'vrrp adv traffic': {
            'type': 'custom',
            'protocol': '0800',
            'ip_source': dev_groups[tg_links[0][tgen_dev]][0]['name'],
            'ip_destination': dev_groups[tg_links[0][tgen_dev]][0]['name'],
            'allowSelfDestined': True,
            'srcMac': vr_id_to_mac(vr_id),
            'dstMac': '01:00:5e:00:00:12',
            'frame_rate_type': 'line_rate',
            'rate': 100,  # %
            'frameSize': 100,
            'customLength': len(vrrp_packet) // 2,
            'customData': vrrp_packet,
        }
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    await tgen_utils_start_traffic(tgen_dev)
    # don't stop
    await asyncio.sleep(sleep_time_s)

    # 5. Verify both infra devices trap those advertisements and they remain stable
    await asyncio.gather(*[verify_cpu_traps_rate_code_avg(dent, CPU_STAT_CODE_VRRP, CPU_MAX_VRRP_PPS)
                           for dent in infra])
