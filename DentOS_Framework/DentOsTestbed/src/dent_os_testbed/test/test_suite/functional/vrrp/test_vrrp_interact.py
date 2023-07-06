import asyncio
import pytest

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.mstpctl.mstpctl import Mstpctl

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

    wait_for_keepalived = 10
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
