from operator import itemgetter
import asyncio
import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_address import IpAddress

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
)

from dent_os_testbed.test.test_suite.functional.vrrp.vrrp_utils import (
    setup_topo_for_vrrp,
    verify_vrrp_ping,
    vr_id_to_mac,
)


pytestmark = [
    pytest.mark.suite_functional_vrrp,
    pytest.mark.usefixtures('cleanup_ip_addrs', 'enable_ipv4_forwarding', 'cleanup_bridges'),
    pytest.mark.asyncio,
]


async def test_vrrp_master_and_backup(testbed, configure_vrrp):
    """
    Test Name: test_vrrp_master_and_backup
    Test Suite: suite_functional_vrrp
    Test Overview:
        Verify DUT can be both MASTER for one VRID and at the same time BACKUP for another
    Test Procedure:
    1. Configure aggregation router
    2. Configure infra devices
    3. Configure VRRP on infra devices
    4. Verify infra[0] serves as master, infra[1] serves as backup (vr id 40)
    5. Verify infra[1] serves as master, infra[0] serves as backup (vr id 50)

    Setup:
            agg
         ___| |___
      L0 |       | L1
         |       |
    infra[0]    infra[1]

    Configure:
        agg:
            L0 and L1: master bridge
            bridge: ip address 192.168.10.5/24
                               192.168.20.5/24
        infra[0]:
            L0 (port/bridge):
                ip address 192.168.10.3/24
                           192.168.20.3/24
                vrrp 40 ip 192.168.10.2 prio 200 (MASTER)
                vrrp 50 ip 192.168.20.2 prio 100 (BACKUP)
        infra[1]:
            L1 (port/bridge):
                ip address 192.168.10.4/24
                           192.168.20.4/24
                vrrp 40 ip 192.168.10.2 prio 100 (BACKUP)
                vrrp 50 ip 192.168.20.2 prio 200 (MASTER)
    """
    wait_for_keepalived = 15
    vr_addr = ['192.168.10.2', '192.168.20.2']
    count = 10

    # 1. Configure aggregation router
    # 2. Configure infra devices
    config = await setup_topo_for_vrrp(testbed, use_bridge=True)
    infra, agg, bridge, links = itemgetter('infra', 'agg', 'bridge', 'links')(config)

    out = await IpAddress.add(input_data=[{
        agg.host_name: [{'dev': bridge, 'prefix': '192.168.10.5/24'},
                        {'dev': bridge, 'prefix': '192.168.20.5/24'}],
        infra[0].host_name: [{'dev': bridge, 'prefix': '192.168.10.3/24'},
                             {'dev': bridge, 'prefix': '192.168.20.3/24'}],
        infra[1].host_name: [{'dev': bridge, 'prefix': '192.168.10.4/24'},
                             {'dev': bridge, 'prefix': '192.168.20.4/24'}],
    }])
    assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
        'Failed to add IP addr'

    # 3. Configure VRRP on infra devices
    await asyncio.gather(*[
        configure_vrrp(infra[0], state='MASTER', prio=200, vr_ip=vr_addr[0], vr_id=40, dev=bridge, apply=False),
        configure_vrrp(infra[1], state='BACKUP', prio=100, vr_ip=vr_addr[0], vr_id=40, dev=bridge, apply=False),
    ])
    await asyncio.gather(*[
        configure_vrrp(infra[0], state='BACKUP', prio=100, vr_ip=vr_addr[1],
                       vr_id=50, dev=bridge, apply=True, clear=False),
        configure_vrrp(infra[1], state='MASTER', prio=200, vr_ip=vr_addr[1],
                       vr_id=50, dev=bridge, apply=True, clear=False),
    ])
    await asyncio.sleep(wait_for_keepalived)

    # 4. Verify infra[0] serves as master, infra[1] serves as backup (vr id 40)
    await verify_vrrp_ping(agg, infra, ports=(links[0][infra[0]], links[1][infra[1]]),
                           expected=(count, 0), dst=vr_addr[0], count=count)

    # 5. Verify infra[1] serves as master, infra[0] serves as backup (vr id 50)
    await verify_vrrp_ping(agg, infra, ports=(links[0][infra[0]], links[1][infra[1]]),
                           expected=(0, count), dst=vr_addr[1], count=count)


@pytest.mark.usefixtures('cleanup_tgen')
async def test_vrrp_multiple_addr(testbed, configure_vrrp):
    """
    Test Name: test_vrrp_multiple_addr
    Test Suite: suite_functional_vrrp
    Test Overview:
        Verify it possible to set multiple IP addresses on a single virtual router and their availability
    Test Procedure:
    1. Configure aggregation router
    2. Configure infra devices
    3. Configure VRRP on infra devices
    4. Setup ICMP echo request stream
    5. If infra[0] is available:
       Verify infra[0] serves as master because it has a higher priority,
       Verify infra[1] serves as backup
    6. If infra[0] is unavailable:
       Verify infra[1] takes over as master

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
                ip address 192.168.1.2/24
                vrrp 40 ip 192.168.20.1 prio 200
                ...
                vrrp 40 ip 192.168.20.255 prio 200
        infra[1]:
            L1: master bridge
                ip address 192.168.1.3/24
                vrrp 40 ip 192.168.20.1 prio 100
                ...
                vrrp 40 ip 192.168.20.255 prio 100
    """
    wait_for_keepalived = 15
    vrrp_ips = [f'192.168.20.{ip+1}' for ip in range(255)]
    count = len(vrrp_ips)
    vr_id = 40
    rate_pps = 50

    # 1. Configure aggregation router
    # 2. Configure infra devices
    config = await setup_topo_for_vrrp(testbed, use_bridge=True, use_tgen=True, vrrp_ip=vrrp_ips[0])
    infra, agg, tgen_dev, bridge, links, tg_links, dev_groups = \
        itemgetter('infra', 'agg', 'tgen_dev', 'bridge', 'links', 'tg_links', 'dev_groups')(config)

    # 3. Configure VRRP on infra devices
    await asyncio.gather(*[
        configure_vrrp(dent, state=state, prio=prio, vr_ip=vrrp_ips, vr_id=vr_id, dev=bridge)
        for dent, state, prio
        in zip(infra, ['MASTER', 'BACKUP'], [200, 100])])
    await asyncio.sleep(wait_for_keepalived)

    # 4. Setup ICMP echo request stream
    streams = {
        'icmp': {
            'type': 'raw',
            'protocol': 'ip',
            'frameSize': 100,
            'ip_source': dev_groups[tg_links[0][tgen_dev]][0]['name'],
            'ip_destination': dev_groups[tg_links[1][tgen_dev]][0]['name'],
            'srcMac': '02:00:00:00:00:01',
            'dstMac': vr_id_to_mac(vr_id),
            'srcIp': dev_groups[tg_links[0][tgen_dev]][0]['ip'],
            'dstIp': {'type': 'list', 'list': vrrp_ips},
            'ipproto': 'icmpv2',
            'icmpType': '8',
            'icmpCode': '0',
            'rate': rate_pps,
        },
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    await tgen_utils_start_traffic(tgen_dev)
    # don't stop

    # 5. If infra[0] is available:
    #    Verify infra[0] serves as master because it has a higher priority,
    #    Verify infra[1] serves as backup
    # 6. If infra[0] is unavailable:
    #    Verify infra[1] takes over as master
    for state, expected in [('up', (count, 0)),
                            ('down', (0, count)),
                            ('up', (count, 0))]:
        out = await IpLink.set(input_data=[{
            infra[0].host_name: [{'device': f'vrrp.{vr_id}', 'operstate': state}],
        }])
        assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
            'Failed to disable vrrp'
        await asyncio.sleep(wait_for_keepalived)

        await verify_vrrp_ping(agg, infra, ports=(links[0][infra[0]], links[1][infra[1]]),
                               expected=expected, count=count, do_ping=False, interval=1/rate_pps)


@pytest.mark.usefixtures('cleanup_tgen')
async def test_vrrp_max_instances(testbed, configure_vrrp):
    """
    Test Name: test_vrrp_max_instances
    Test Suite: suite_functional_vrrp
    Test Overview:
        Verify it is possible to configure maximum number of VRRP interfaces and verify their connectivity
    Test Procedure:
    1. Configure aggregation router
    2. Configure infra devices
    3. Configure VRRP on infra devices
    4. Setup ICMP echo request stream
    5. If infra[0] is available:
       Verify infra[0] serves as master because it has a higher priority,
       Verify infra[1] serves as backup
    6. If infra[0] is unavailable:
       Verify infra[1] takes over as master

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
                ip address 192.168.1.2/24
                vrrp 1 ip 192.168.20.1 prio 200
                ...
                vrrp 254 ip 192.168.20.254 prio 200
        infra[1]:
            L1: master bridge
                ip address 192.168.1.3/24
                vrrp 1 ip 192.168.20.1 prio 100
                ...
                vrrp 254 ip 192.168.20.254 prio 100
    """
    wait_for_keepalived = 15
    vr_ids = [id+1 for id in range(254)]
    vrrp_ips = [f'192.168.20.{id}' for id in vr_ids]
    count = len(vrrp_ips)
    rate_pps = 50

    # 1. Configure aggregation router
    # 2. Configure infra devices
    config = await setup_topo_for_vrrp(testbed, use_bridge=True, use_tgen=True, vrrp_ip=vrrp_ips[0])
    infra, agg, tgen_dev, bridge, links, tg_links, dev_groups = \
        itemgetter('infra', 'agg', 'tgen_dev', 'bridge', 'links', 'tg_links', 'dev_groups')(config)

    # 3. Configure VRRP on infra devices
    for id, ip in zip(vr_ids, vrrp_ips):
        await asyncio.gather(*[
            configure_vrrp(dent, state=state, prio=prio, vr_ip=ip, vr_id=id, dev=bridge,
                           clear=ip == vrrp_ips[0], apply=ip == vrrp_ips[-1],
                           additional_opts=['advert_int 3'])
            for dent, state, prio
            in zip(infra, ['MASTER', 'BACKUP'], [200, 100])])
    await asyncio.sleep(wait_for_keepalived)

    # 4. Setup ICMP echo request stream
    streams = {
        'icmp': {
            'type': 'raw',
            'protocol': 'ip',
            'frameSize': 100,
            'ip_source': dev_groups[tg_links[0][tgen_dev]][0]['name'],
            'ip_destination': dev_groups[tg_links[1][tgen_dev]][0]['name'],
            'srcMac': '02:00:00:00:00:01',
            'dstMac': {'type': 'list', 'list': [vr_id_to_mac(id) for id in vr_ids]},
            'srcIp': dev_groups[tg_links[0][tgen_dev]][0]['ip'],
            'dstIp': {'type': 'list', 'list': vrrp_ips},
            'ipproto': 'icmpv2',
            'icmpType': '8',
            'icmpCode': '0',
            'rate': rate_pps,
        },
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    await tgen_utils_start_traffic(tgen_dev)
    # don't stop

    # 5. If infra[0] is available:
    #    Verify infra[0] serves as master because it has a higher priority,
    #    Verify infra[1] serves as backup
    # 6. If infra[0] is unavailable:
    #    Verify infra[1] takes over as master
    for state, expected in [('up', (count, 0)),
                            ('down', (0, count)),
                            ('up', (count, 0))]:
        out = await IpLink.set(input_data=[{
            infra[0].host_name: [{'device': f'vrrp.{id}', 'operstate': state}
                                 for id in vr_ids],
        }])
        assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
            'Failed to disable vrrp'
        await asyncio.sleep(20)  # wait for vrrp to change master

        await verify_vrrp_ping(agg, infra, ports=(links[0][infra[0]], links[1][infra[1]]),
                               expected=expected, count=count, do_ping=False, interval=1/rate_pps)
