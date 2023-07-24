import asyncio
import pytest
import random

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.lib.os.service import Service
from dent_os_testbed.lib.ip.ip_route import IpRoute

from dent_os_testbed.test.test_suite.functional.vrrp.vrrp_utils import (
    verify_vrrp_ping,
)

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
)

from dent_os_testbed.test.test_suite.functional.ifupdown2.ifupdown2_utils import (
    VLAN_DEV_TEMPLATE, INTERFACES_FILE,
    write_reload_check_ifupdown_config,
    reboot_and_wait, config_bridge_temp,
    config_ipv4_temp,
)


pytestmark = [
    pytest.mark.suite_functional_vrrp,
    pytest.mark.usefixtures('cleanup_ip_addrs', 'enable_ipv4_forwarding', 'cleanup_bridges'),
    pytest.mark.asyncio,
]


async def test_vrrp_ifupdown2(testbed, configure_vrrp, modify_ifupdown_conf):
    """
    Test Name: test_vrrp_ifupdown2
    Test Suite: suite_functional_vrrp
    Test Overview:
        Verify basic VRRP configuration
    Test Procedure:
    1. Prepare ifupdown2 config
    2. Make ifupdown2 configuration:
       - Add VLAN-aware bridge
       - Create vlan interface on top of the bridge
       - Add IP address to the vlan interface
    3. Apply ifupdown configuration and restart Keepalived daemon
    4. Configure VRRP and restart Keepalived
    5. Verify Macvlan was created with a RIF
    6. Verify infra replies to the ICMP requests
    7. Change agg VRRP to a higher priority
    8. Verify infra doesn't reply to ICMP requests
    9. Reboot infra
    10. Verify Macvlan was created with a RIF
    11. Verify infra doesn't reply to ICMP requests
    12. Change agg VRRP back to a lower priority than infra
    13. Verify infra starts replying to the ICMP requests again

    Topology:
            agg
         ___| |___
      L0 |       | L1
         |       |
    infra[0]    infra[1]

    Config:
        agg:
            L0:     master bridge
            L1:     master bridge
            bridge: vlan aware
            vlan:   ip address 192.168.1.1/24
                    vrrp 40 ip 192.168.1.2 prio 150
        infra[0]:
            L0:     master bridge
            bridge: vlan aware
            vlan:   ip address 192.168.1.3/24
        infra[1]:
            L1:     master bridge
            bridge: vlan aware
            vlan:   ip address 192.168.1.4/24
                    vrrp 40 ip 192.168.1.2 prio [100|200]
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

    wait_for_keepalived = 20
    wait_for_ifupdown = 60
    vlan = random.randint(1, 4094)
    vrrp_ip = '192.168.1.2'
    bridge = 'br0'
    vlan_dev = f'{bridge}.{vlan}'
    count = 10
    vr_id = 40
    full_config = {
        agg: '',
        infra[0]: '',
        infra[1]: '',
    }
    links = [
        # L0
        {infra[0]: infra[0].links_dict[agg.host_name][0][0],
         agg: infra[0].links_dict[agg.host_name][1][0]},
        # L1
        {infra[1]: infra[1].links_dict[agg.host_name][0][0],
         agg: infra[1].links_dict[agg.host_name][1][0]},
    ]

    # 1. Prepare ifupdown2 config
    config = {
        'template_lookuppath': '/etc/network/ifupdown2/templates',
        'addon_syntax_check': 1,
        'default_interfaces_configfile': INTERFACES_FILE,
    }
    out = await asyncio.gather(*[modify_ifupdown_conf(dent, config) for dent in infra + [agg]])
    assert all(not rc for rc in out), 'Failed to prepare ifupdown2 enviroment config'

    # 2. Make ifupdown2 configuration:
    # Add VLAN-aware bridge
    full_config[agg] += config_bridge_temp(bridge, [links[0][agg], links[1][agg]], vlan_aware=True,
                                           pvid=0, vlans=[vlan])
    full_config[infra[0]] += config_bridge_temp(bridge, [links[0][infra[0]]], vlan_aware=True,
                                                pvid=0, vlans=[vlan])
    full_config[infra[1]] += config_bridge_temp(bridge, [links[1][infra[1]]], vlan_aware=True,
                                                pvid=0, vlans=[vlan])

    # Create vlan interface on top of the bridge
    full_config[agg] += VLAN_DEV_TEMPLATE.format(name=vlan_dev, vid=vlan, bridge=bridge)
    full_config[infra[0]] += VLAN_DEV_TEMPLATE.format(name=vlan_dev, vid=vlan, bridge=bridge)
    full_config[infra[1]] += VLAN_DEV_TEMPLATE.format(name=vlan_dev, vid=vlan, bridge=bridge)

    # Add IP address to the vlan interface
    full_config[agg] += config_ipv4_temp(vlan_dev, 'static', ipaddr='192.168.1.1/24')
    full_config[infra[0]] += config_ipv4_temp(vlan_dev, 'static', ipaddr='192.168.1.3/24')
    full_config[infra[1]] += config_ipv4_temp(vlan_dev, 'static', ipaddr='192.168.1.4/24')

    # 3. Apply ifupdown configuration
    await asyncio.gather(*[write_reload_check_ifupdown_config(dent, full_config[dent],
                                                              config['default_interfaces_configfile'])
                           for dent in infra + [agg]])

    # 4. Configure VRRP and restart Keepalived
    await asyncio.gather(*[
        configure_vrrp(dent, state=state, prio=prio, vr_ip=vrrp_ip, vr_id=vr_id, dev=vlan_dev)
        for dent, state, prio
        in zip([agg, infra[1]], ['MASTER', 'BACKUP'], [150, 100])])
    await asyncio.sleep(wait_for_keepalived)

    # 4. Verify Macvlan was created with a RIF
    out = await IpRoute.show(input_data=[{
        dent.host_name: [{'cmd_options': '-j', 'dev': vlan_dev}]
        for dent in infra + [agg]
    }], parse_output=True)
    assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
        'Macvlan does not have a RIF'

    # 6. Verify infra replies to the ICMP requests
    await verify_vrrp_ping(infra[0], [agg], ports=[bridge], expected=[count], dst=vrrp_ip, count=count, expect_reply=True)

    # 7. Change agg VRRP to a higher priority
    await configure_vrrp(infra[1], state='MASTER', prio=200, vr_ip=vrrp_ip, vr_id=vr_id, dev=vlan_dev)
    await asyncio.sleep(wait_for_keepalived)

    # 8. Verify infra doesn't reply to ICMP requests
    await verify_vrrp_ping(infra[0], [agg], ports=[bridge], expected=[0], dst=vrrp_ip, count=count, expect_reply=True)

    # 9. Reboot infra
    await reboot_and_wait(agg)
    await asyncio.sleep(wait_for_ifupdown)

    out = await Service.start(input_data=[{agg.host_name: [{'name': 'keepalived'}]}])
    assert out[0][agg.host_name]['rc'] == 0, 'Failed to restart keepalived'
    await asyncio.sleep(wait_for_keepalived)

    # 10. Verify Macvlan was created with a RIF
    out = await IpRoute.show(input_data=[{
        dent.host_name: [{'cmd_options': '-j', 'dev': vlan_dev}]
        for dent in infra + [agg]
    }], parse_output=True)
    assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
        'Macvlan does not have a RIF'

    # 11. Verify infra doesn't reply to ICMP requests
    await verify_vrrp_ping(infra[0], [agg], ports=[bridge], expected=[0], dst=vrrp_ip, count=count, expect_reply=True)

    # 12. Change agg VRRP back to a lower priority than infra
    await configure_vrrp(infra[1], state='BACKUP', prio=100, vr_ip=vrrp_ip, vr_id=vr_id, dev=vlan_dev)
    await asyncio.sleep(wait_for_keepalived)

    # 13. Verify infra starts replying to the ICMP requests again
    await verify_vrrp_ping(infra[0], [agg], ports=[bridge], expected=[count], dst=vrrp_ip, count=count, expect_reply=True)
