from operator import itemgetter
import asyncio
import pytest

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.tc.tc_qdisc import TcQdisc
from dent_os_testbed.lib.tc.tc_filter import TcFilter
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.mstpctl.mstpctl import Mstpctl

from dent_os_testbed.test.test_suite.functional.vrrp.vrrp_utils import (
    setup_topo_for_vrrp,
    verify_vrrp_advert,
    vr_id_to_mac,
)

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
)

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
)

from dent_os_testbed.test.test_suite.functional.vrrp.vrrp_utils import (
    verify_vrrp_ping,
)


pytestmark = [
    pytest.mark.suite_functional_vrrp,
    pytest.mark.usefixtures('cleanup_ip_addrs', 'enable_ipv4_forwarding', 'cleanup_bridges'),
    pytest.mark.asyncio,
]


@pytest.mark.usefixtures('enable_mstpd')
async def test_vrrp_and_stp(testbed, configure_vrrp):
    """
    Test Name: test_vrrp_and_stp
    Test Suite: suite_functional_vrrp
    Test Overview:
        Verify VRRP functionality and STP work together without interfere each other
    Test Procedure:
    1. Configure bridges
    2. Enslave ports
    3. Enable stp on infra[0]
    4. Configure VRRP on infra devices
    5. Verify bridge on infra[0] has a blocking port
    6. If infra[0] is available:
       Verify infra[0] serves as master because it has a higher priority,
       Verify infra[1] serves as backup
    7. If infra[0] is unavailable:
       Verify infra[1] takes over as master

    Setup:
            agg
         ___| |___
      L0 |       | L1
         |       |
    infra[0]----infra[1]
             L2

    Configure:
        agg:
            L0 and L1: master bridge
            bridge: ip address 192.168.1.5/24
        infra[0]:
            L0 and L2: master bridge stp_state 1
                ip address 192.168.1.3/24
                vrrp 40 ip 192.168.1.2 prio 200
        infra[1]:
            L1 and L2: master bridge
                ip address 192.168.1.4/24
                vrrp 40 ip 192.168.1.2 prio 100
    """
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [
        DeviceType.AGGREGATION_ROUTER,
        DeviceType.INFRA_SWITCH,
    ], 0)
    if not tgen_dev or not dent_devices or len(dent_devices) < 3:
        pytest.skip('The testbed does not have enough devices (1 agg + 2 infra)')

    infra = [dent for dent in dent_devices if dent.type == DeviceType.INFRA_SWITCH]
    if len(infra) < 2:
        pytest.skip('The testbed does not have enough infra devices')
    infra = infra[:2]

    agg = [dent for dent in dent_devices if dent.type == DeviceType.AGGREGATION_ROUTER]
    if len(agg) < 1:
        pytest.skip('The testbed does not have enough agg devices')
    agg = agg[0]

    wait_for_keepalived = 15
    convergence_time_s = 40
    vrrp_ip = '192.168.1.2'
    bridge = 'br0'
    count = 10
    vr_id = 40
    dut_bridge_ip = {
        infra[0]: '192.168.1.3/24',
        infra[1]: '192.168.1.4/24',
        agg: '192.168.1.5/24',
    }
    links = [
        # L0
        {infra[0]: infra[0].links_dict[agg.host_name][0][0],
         agg: infra[0].links_dict[agg.host_name][1][0]},
        # L1
        {infra[1]: infra[1].links_dict[agg.host_name][0][0],
         agg: infra[1].links_dict[agg.host_name][1][0]},
        # L2
        {infra[0]: infra[0].links_dict[infra[1].host_name][0][0],
         infra[1]: infra[0].links_dict[infra[1].host_name][1][0]},
    ]

    # 1. Configure bridges
    out = await IpLink.add(input_data=[{
        infra[0].host_name: [{'name': bridge, 'type': 'bridge', 'stp_state': 1}],
        infra[1].host_name: [{'name': bridge, 'type': 'bridge'}],
        agg.host_name: [{'name': bridge, 'type': 'bridge'}],
    }])
    assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
        'Failed to add bridges'

    # 2. Enslave ports
    out = await IpLink.set(input_data=[
        {
            dent.host_name: [{'device': port, 'master': bridge, 'operstate': 'up'}]
            for dent, port in link.items()
        }
        for link in links
    ] + [
        {
            dent.host_name: [{'device': bridge, 'operstate': 'up'}]
        }
        for dent in infra + [agg]
    ])
    assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
        'Failed to enslave ports'

    # 3. Enable stp on infra[0]
    out = await Mstpctl.add(input_data=[{infra[0].host_name: [{'bridge': bridge}]}])
    assert out[0][infra[0].host_name]['rc'] == 0, 'Failed to add bridge'

    out = await Mstpctl.set(input_data=[{infra[0].host_name: [
        {'parameter': 'forcevers', 'bridge': bridge, 'version': 'stp'},
    ]}])
    assert out[0][infra[0].host_name]['rc'] == 0, 'Failed to enable stp'

    # 4. Configure VRRP on infra devices
    out = await IpAddress.add(input_data=[{
        dent.host_name: [{'dev': bridge, 'prefix': prefix}]
        for dent, prefix in dut_bridge_ip.items()
    }])
    assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
        'Failed to add IP addr'

    await asyncio.gather(*[
        configure_vrrp(dent, state=state, prio=prio, vr_ip=vrrp_ip, vr_id=vr_id, dev=bridge)
        for dent, state, prio
        in zip(infra, ['MASTER', 'BACKUP'], [200, 100])])
    await asyncio.sleep(wait_for_keepalived)

    # 5. Verify bridge on infra[0] has a blocking port
    await asyncio.sleep(convergence_time_s)
    out = await Mstpctl.show(input_data=[{infra[0].host_name: [
        {'parameter': 'portdetail', 'bridge': bridge, 'options': '-f json'}
    ]}], parse_output=True)
    assert out[0][infra[0].host_name]['rc'] == 0, 'Failed to get port detail'

    assert any(port['state'] == 'discarding' for port in out[0][infra[0].host_name]['parsed_output']), \
        'Expected one of the ports to be \'discarding\''

    # 6. If infra[0] is available:
    #    Verify infra[0] serves as master because it has a higher priority,
    #    Verify infra[1] serves as backup
    # 7. If infra[0] is unavailable:
    #    Verify infra[1] takes over as master
    for state, expected in [('up', [count, 0]),
                            ('down', [0, count]),
                            ('up', [count, 0])]:
        out = await IpLink.set(input_data=[{
            infra[0].host_name: [{'device': f'vrrp.{vr_id}', 'operstate': state}],
        }])
        assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
            'Failed to enable/disable vrrp'
        await asyncio.sleep(wait_for_keepalived)

        await verify_vrrp_ping(agg, infra, ports=(links[0][infra[0]], links[1][infra[1]]),
                               expected=expected, dst=vrrp_ip, count=count)


@pytest.mark.usefixtures('cleanup_tgen', 'cleanup_qdiscs')
async def test_vrrp_and_acl(testbed, configure_vrrp):
    """
    Test Name: test_vrrp_and_acl
    Test Suite: suite_functional_vrrp
    Test Overview:
        Verify DUT stability and availability under VRRP advertisements overflow
    Test Procedure:
    1. Configure aggregation router
    2. Configure infra devices
    3. Configure VRRP on infra devices
    4. Send VRRPv3 advertisements
    5. Verify the advertisements are trapped
    6. Configure ACL to drop VRRP advertisements
    7. Verify the advertisements are dropped

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
    wait_for_keepalived = 15
    vrrp_ip = '192.168.1.2'
    vr_id = 40
    pps_rate = 1
    timeout = 20
    expected = 10

    # 1. Configure aggregation router
    # 2. Configure infra devices
    config = await setup_topo_for_vrrp(testbed, use_bridge=True, use_tgen=True, vrrp_ip=vrrp_ip)
    infra, tgen_dev, bridge, links, tg_links, dev_groups, ep_ip = \
        itemgetter('infra', 'tgen_dev', 'bridge', 'links', 'tg_links', 'dev_groups', 'ep_ip')(config)
    tg_ip = ep_ip.split('/')[0]

    # 3. Configure VRRP on infra devices
    await asyncio.gather(*[
        configure_vrrp(dent, state=state, prio=prio, vr_ip=vrrp_ip, vr_id=vr_id, dev=bridge)
        for dent, state, prio
        in zip(infra, ['MASTER', 'BACKUP'], [200, 100])])
    await asyncio.sleep(wait_for_keepalived)

    # 4. Send VRRPv3 advertisements
    streams = {
        'vrrp adv traffic': {
            'type': 'custom',
            'protocol': '0800',
            'ip_source': dev_groups[tg_links[0][tgen_dev]][0]['name'],
            'ip_destination': dev_groups[tg_links[0][tgen_dev]][0]['name'],
            'allowSelfDestined': True,
            'srcMac': vr_id_to_mac(vr_id),
            'dstMac': '01:00:5e:00:00:12',
            'rate': pps_rate,
            'frameSize': 100,
            'customLength': len(vrrp_packet) // 2,
            'customData': vrrp_packet,
        }
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    await tgen_utils_start_traffic(tgen_dev)
    # don't stop

    # 5. Verify the advertisements are trapped
    await asyncio.gather(*[verify_vrrp_advert(dent, port, expected_pkts=expected,
                                              timeout=timeout, options=f'-c {expected}',
                                              filter=[f'src host {tg_ip}'])
                           for dent, port in zip(infra, [links[0][infra[0]], links[1][infra[1]]])])

    # 6. Configure ACL to drop VRRP advertisements
    out = await TcQdisc.add(input_data=[{
        dent.host_name: [{'dev': port, 'direction': 'ingress'}]
        for dent, port in zip(infra, [links[0][infra[0]], links[1][infra[1]]])
    }])
    assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
        'Failed to add qdisc'

    out = await TcFilter.add(input_data=[{
        dent.host_name: [{
            'dev': port,
            'action': 'drop',
            'direction': 'ingress',
            'protocol': 'ip',
            'filtertype': {
                'src_ip': tg_ip,
            },
        }]
        for dent, port in zip(infra, [links[0][infra[0]], links[1][infra[1]]])
    }])
    assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
        'Failed to add drop rule'

    # 7. Verify the advertisements are dropped
    expected = 0
    await asyncio.gather(*[verify_vrrp_advert(dent, port, expected_pkts=expected,
                                              timeout=timeout, filter=[f'src host {tg_ip}'])
                           for dent, port in zip(infra, [links[0][infra[0]], links[1][infra[1]]])])
