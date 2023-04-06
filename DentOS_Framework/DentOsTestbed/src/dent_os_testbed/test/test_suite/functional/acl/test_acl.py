import asyncio
import pytest
import random

from dent_os_testbed.lib.tc.tc_filter import TcFilter
from dent_os_testbed.lib.tc.tc_qdisc import TcQdisc
from dent_os_testbed.lib.ip.ip_link import IpLink


from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_clear_traffic_stats,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
)
from dent_os_testbed.utils.test_utils.tc_flower_utils import (
    tcutil_generate_rule_with_random_selectors,
    tcutil_tc_rules_to_tgen_streams,
    tcutil_get_tc_stats_pref_map,
    tcutil_verify_tgen_stats,
    tcutil_verify_tc_stats,
)


pytestmark = [
    pytest.mark.suite_functional_acl,
    pytest.mark.usefixtures('cleanup_qdiscs', 'cleanup_tgen', 'cleanup_bridges'),
    pytest.mark.asyncio,
]


@pytest.mark.parametrize('action', ['pass', 'drop', 'trap'])
async def test_acl_skip_sw_hw_selector(testbed, action):
    """
    Test Name: test_acl_skip_sw_hw_selector
    Test Suite: suite_functional_acl
    Test Overview: Check that skip_hw/skip_sw selectors are working correctly
    Test Procedure:
    1. Initiate test params
    2. Create bridge and enslave ports to it
    3. Set link up on interfaces
    4. Create stream matching the rule
    5. Create ingress qdisc
    6. Configure the rule with skip_sw selector
    7. Send traffic matching the rule
    8. Verify it applies to HW only
    9. Configure the rule with skip_hw selector
    10. Send traffic matching the rule
    11. Verify it applies to SW only
    12. Configure the rule with no selector at all (default)
    13. Send traffic matching the rule
    14. Verify it applies to both SW and HW
    """
    # 1. Initiate test params
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0][:2]
    ports = tgen_dev.links_dict[dent][1][:2]
    port_with_rule = ports[0]
    tx_port, rx_port = tg_ports
    tc_stats_update_time = 5
    traffic_duration = 10
    rate_pps = 100
    bridge = 'br0'
    pref = 49000

    # 2. Create bridge and enslave ports to it
    out = await IpLink.add(input_data=[{dent: [{'name': bridge, 'type': 'bridge'}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create bridge'

    # 3. Set link up on interfaces
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up', 'master': bridge} for port in ports
    ] + [
        {'device': bridge, 'operstate': 'up'}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # 4. Create stream matching the rule
    dev_groups = tgen_utils_dev_groups_from_config((
        {'ixp': tx_port, 'ip': '1.1.1.1', 'gw': '1.1.1.10', 'plen': 24},
        {'ixp': rx_port, 'ip': '1.1.1.2', 'gw': '1.1.1.10', 'plen': 24},
    ))
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    streams = {'stream': {
        'ip_source': dev_groups[tx_port][0]['name'],
        'ip_destination': dev_groups[rx_port][0]['name'],
        'rate': rate_pps,  # pps
        'type': 'raw',
        # make sure that the packets will be trapped to cpu
        'dstMac': 'ff:ff:ff:ff:ff:ff',
        'srcMac': '02:00:00:00:00:01',
    }}

    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # 5. Create ingress qdisc
    out = await TcQdisc.add(input_data=[{dent: [
        {'dev': port_with_rule, 'direction': 'ingress'}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create qdisc'

    # 6. Configure the rule with skip_sw selector
    tc_rule = tcutil_generate_rule_with_random_selectors(
        port_with_rule, pref=pref, action=action, skip_sw=True, want_proto=False)
    out = await TcFilter.add(input_data=[{dent: [tc_rule]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create tc rule'

    # 7. Send traffic matching the rule
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # 8. Verify it applies to HW only
    await asyncio.sleep(tc_stats_update_time)  # wait for tc stats to update
    ixia_stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    tc_stats = await tcutil_get_tc_stats_pref_map(dent, port_with_rule)
    await tcutil_verify_tgen_stats(tgen_dev, ixia_stats.Rows, rule_action=action, actual_pps=rate_pps)
    tx_packets = int(ixia_stats.Rows['Tx Frames'])
    await tcutil_verify_tc_stats(dent_dev, tx_packets, tc_stats[pref], stats_type='hw')

    # 9. Configure the rule with skip_hw selector
    out = await TcFilter.delete(input_data=[{dent: [
        {'dev': port_with_rule, 'direction': 'ingress', 'pref': pref}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to remove tc rule'

    tc_rule = tcutil_generate_rule_with_random_selectors(
        port_with_rule, pref=pref, action=action, skip_hw=True, want_proto=False)

    out = await TcFilter.add(input_data=[{dent: [tc_rule]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create tc rule'

    # 10. Send traffic matching the rule
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # 11. Verify it applies to SW only
    await asyncio.sleep(tc_stats_update_time)  # wait for tc stats to update
    ixia_stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    tc_stats = await tcutil_get_tc_stats_pref_map(dent, port_with_rule)
    # broadcast traffic with sw rule will pass
    await tcutil_verify_tgen_stats(tgen_dev, ixia_stats.Rows,
                                   rule_action='pass', actual_pps=rate_pps)
    tx_packets = int(ixia_stats.Rows['Tx Frames'])
    await tcutil_verify_tc_stats(dent_dev, tx_packets, tc_stats[pref], stats_type='sw')

    # 12. Configure the rule with no selector at all (default)
    out = await TcFilter.delete(input_data=[{dent: [
        {'dev': port_with_rule, 'direction': 'ingress', 'pref': pref}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to remove tc rule'

    tc_rule = tcutil_generate_rule_with_random_selectors(
        port_with_rule, pref=pref, action=action, want_proto=False)

    out = await TcFilter.add(input_data=[{dent: [tc_rule]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create tc rule'

    # 13. Send traffic matching the rule
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # 14. Verify it applies to both SW and HW
    await asyncio.sleep(tc_stats_update_time)  # wait for tc stats to update
    ixia_stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    tc_stats = await tcutil_get_tc_stats_pref_map(dent, port_with_rule)
    # broadcast traffic with trap hw+sw rule will not be forwarded
    await tcutil_verify_tgen_stats(tgen_dev, ixia_stats.Rows, actual_pps=rate_pps,
                                   rule_action='drop' if action == 'trap' else action)
    tx_packets = int(ixia_stats.Rows['Tx Frames'])
    await tcutil_verify_tc_stats(dent_dev, tx_packets, tc_stats[pref], stats_type=['hw', 'sw'])


async def test_acl_rule_deletion(testbed):
    """
    Test Name: test_acl_rule_deletion
    Test Suite: suite_functional_acl
    Test Overview: Check that ACL rules are deleted correctly
    Test Procedure:
    1. Initiate test params
    2. Create an ingress queue on first TGDutLink DUT port
    3. Overflow qdisc with rules with random selectors
    4. Delete the last and the first rules within the qdisc
    5. Verify the entries were deleted
    """
    # 1. Initiate test params
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 1)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    port = tgen_dev.links_dict[dent][1][0]
    pref = 10000
    rule_count = 1536

    # 2. Create an ingress queue on first TGDutLink DUT port
    out = await TcQdisc.add(input_data=[{dent: [
        {'dev': port, 'direction': 'ingress'}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create qdisc'

    # 3. Overflow qdisc with rules with random selectors
    # Run the command in batches, so it does not exceed bash limit
    batch_size = 400
    for idx in range(0, rule_count, batch_size):
        count = batch_size if idx + batch_size < rule_count else rule_count - idx
        selector_list = ('want_vlan', 'want_ip', 'want_tcp', 'want_port', 'want_icmp')
        out = await TcFilter.add(input_data=[
            {dent: (tcutil_generate_rule_with_random_selectors(
                        port, pref=x, want_mac=True,
                        **{sel: random.randint(0, 1) for sel in selector_list})
                    for x in range(pref + idx, pref + idx + count))}
        ])
        assert out[0][dent]['rc'] == 0, 'Failed to add tc rules'

    rc, out = await dent_dev.run_cmd(f'tc filter show dev {port} ingress | grep action | wc -l')
    assert rc == 0, 'Failed to get tc rule count'
    total_rules = int(out)
    rc, out = await dent_dev.run_cmd(f'tc filter show dev {port} ingress | grep in_hw | wc -l')
    assert rc == 0, 'Failed to get tc rule count'
    offloaded_rules = int(out)
    dent_dev.applog.info(f'Total number of rules: {total_rules}, offloaded: {offloaded_rules}')
    assert offloaded_rules == rule_count, 'Some tc rules were not offloaded'

    # 4. Delete the last and the first rules within the qdisc
    out = await TcFilter.delete(input_data=[{dent: [
        {'dev': port, 'direction': 'ingress', 'pref': pref},
        {'dev': port, 'direction': 'ingress', 'pref': pref + rule_count - 1},
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to remove tc rules'

    # 5. Verify the entries were deleted
    out = await TcFilter.show(input_data=[{dent: [
        {'dev': port, 'direction': 'ingress', 'pref': pref},
        {'dev': port, 'direction': 'ingress', 'pref': pref + rule_count - 1},
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to get tc rules'
    assert not out[0][dent]['result'].strip(), f'Some of the rules were not deleted\n{out}'


async def test_acl_addition_deletion_under_traffic(testbed):
    """
    Test Name: test_acl_addition_deletion_under_traffic
    Test Suite: suite_functional_acl
    Test Overview: Test ACL rule addition and deletion under traffic
    Test Procedure:
    1. Initiate test params
    2. Create bridge and enslave ports to it
    3. Set link up on interfaces
    4. Set up host on TG ports
    5. Create an ingress qdisc
    6. Configure the following rules
       - action drop
       - rule with randomly generated selectors, action pass
    7. Set up stream matching the selectors
    8. Send continuous traffic from first TG port; verify it is forwarded
    9. Delete the pass rule; verify traffic is not forwarded
    10. Configure again the deleted rule; verify traffic is forwarded again
    """
    # 1. Initiate test params
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[dent][0][:2]
    ports = tgen_dev.links_dict[dent][1][:2]
    port_with_rule = ports[0]
    traffic_duration = 10
    rate_pps = 10_000
    bridge = 'br0'
    pref = 49000

    # 2. Create bridge and enslave ports to it
    out = await IpLink.add(input_data=[{dent: [{'name': bridge, 'type': 'bridge'}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create bridge'

    # 3. Set link up on interfaces
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up', 'master': bridge} for port in ports
    ] + [
        {'device': bridge, 'operstate': 'up'}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # 4. Set up host on TG ports
    dev_groups = tgen_utils_dev_groups_from_config((
        {'ixp': tg_ports[0], 'ip': '1.1.1.1', 'gw': '1.1.1.10', 'plen': 24},
        {'ixp': tg_ports[1], 'ip': '1.1.1.2', 'gw': '1.1.1.10', 'plen': 24},
    ))
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    # 5. Create an ingress qdisc
    out = await TcQdisc.add(input_data=[{dent: [
        {'dev': port_with_rule, 'direction': 'ingress'}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create qdisc'

    # 6. Configure rule with randomly generated selectors, action pass
    pass_rule = tcutil_generate_rule_with_random_selectors(
        port_with_rule, pref=pref, action='pass', want_ip=True, want_port=True, skip_sw=True)
    # Configure action drop (higher pref = lower priority)
    drop_rule = tcutil_generate_rule_with_random_selectors(
        port_with_rule, pref=pref + 1, action='drop', skip_sw=True, want_proto=False)

    out = await TcFilter.add(input_data=[{dent: [pass_rule, drop_rule]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create tc rules'

    # 7. Set up stream matching the selectors
    out = await TcFilter.show(input_data=[{dent: [
        {'dev': port_with_rule, 'direction': 'ingress', 'pref': pref, 'options': '-j'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get tc rule'

    streams = tcutil_tc_rules_to_tgen_streams({port_with_rule: out[0][dent]['parsed_output']},
                                              frame_rate_pps=rate_pps)
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # 8. Send continuous traffic from first TG port
    await tgen_utils_clear_traffic_stats(tgen_dev)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    # Do not stop traffic

    # Verify it is forwarded
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    # we should only have 1 traffic item and 1 row
    await tcutil_verify_tgen_stats(tgen_dev, stats.Rows, 'pass')

    # 9. Delete the pass rule
    out = await TcFilter.delete(input_data=[{dent: [
        {'dev': port_with_rule, 'direction': 'ingress', 'pref': pref}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to delete tc rule'

    await tgen_utils_clear_traffic_stats(tgen_dev)
    await asyncio.sleep(traffic_duration)

    # Verify traffic is not forwarded
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    await tcutil_verify_tgen_stats(tgen_dev, stats.Rows, 'drop')

    # 10. Configure again the deleted rule
    out = await TcFilter.add(input_data=[{dent: [pass_rule]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create tc rule'

    await tgen_utils_clear_traffic_stats(tgen_dev)
    await asyncio.sleep(traffic_duration)

    # Verify traffic is forwarded again
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    await tcutil_verify_tgen_stats(tgen_dev, stats.Rows, 'pass')
