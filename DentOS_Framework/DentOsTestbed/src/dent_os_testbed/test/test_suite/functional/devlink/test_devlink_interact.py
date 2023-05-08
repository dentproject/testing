from copy import deepcopy
import asyncio
import random
import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.tc.tc_qdisc import TcQdisc
from dent_os_testbed.lib.tc.tc_filter import TcFilter

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_get_loss,
)

from dent_os_testbed.utils.test_utils.tc_flower_utils import (
    tcutil_generate_rule_with_random_selectors,
    tcutil_tc_rules_to_tgen_streams,
)

from dent_os_testbed.test.test_suite.functional.devlink.devlink_utils import (
    verify_cpu_traps_rate_code_avg,
    verify_devlink_cpu_traps_rate_avg,
    CPU_STAT_CODE_ACL_CODE_3,
    CPU_MAX_PPS,
)


pytestmark = [
    pytest.mark.suite_functional_devlink,
    pytest.mark.usefixtures('define_bash_utils', 'cleanup_qdiscs',
                            'cleanup_bridges', 'cleanup_tgen'),
    pytest.mark.asyncio,
]


async def verify_cpu_rate(dent_dev, exp_rate_pps):
    await asyncio.gather(
        verify_cpu_traps_rate_code_avg(dent_dev, CPU_STAT_CODE_ACL_CODE_3, exp_rate_pps),
        verify_devlink_cpu_traps_rate_avg(dent_dev, 'acl_code_3', exp_rate_pps),
    )


async def test_devlink_interact_acl_with_dyn_traps(testbed):
    """
    Test Name: test_devlink_interact_acl_with_dyn_traps
    Test Suite: suite_functional_devlink
    Test Overview:
        Test devlink with acl rules
    Test Procedure:
    1. Create a bridge entity and set link up on it, enslave all participant ports to the bridge
    2. Create an ingress qdisc
    3. Generate rule with random selectors
    4. Add two rules with those selectors to the ingress qdisc:
       - first with police action
       - second with action drop
    5. Prepare traffic matching the random selectors
    6. Send traffic
    7. Verify traffic is trapped by the police rule, and verify the CPU trapped rate for that rule
    8. Delete the first rule and add it again with the same priority as before
    9. Send traffic
    10. Verify it is handled according to the rule with the lowest priority
    11. Delete the first rule again and add it with higher priority than the other rule
    12. Send traffic
    13. Verify traffic is no longer trapped (handled by the 'drop' rule)
    """
    num_of_ports = 2
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], num_of_ports)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0][:num_of_ports]
    ports = tgen_dev.links_dict[dent][1][:num_of_ports]
    ingress_port = ports[0]
    rate_bps = random.randint(400_000, 4_000_000)  # 0.4Mbps..4Mbps
    frame_size = random.randint(100, 1000)
    exp_rate_pps = min(rate_bps / frame_size, CPU_MAX_PPS)
    traffic_duration = 10  # sec
    bridge = 'br0'
    pref = random.randint(1, 10_000)

    dent_dev.applog.info(f'policer rate: {rate_bps // 1000}Kbps, traffic frame size: {frame_size}, '
                         f'expected trap rate: {exp_rate_pps // 1}pps')

    # 1. Create a bridge entity and set link up on it, enslave all participant ports to the bridge
    out = await IpLink.add(input_data=[{dent: [
        {'name': bridge, 'type': 'bridge'}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bridge'

    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up', 'master': bridge}
        for port in ports
    ] + [
        {'device': bridge, 'operstate': 'up'}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to enslave ports'

    # 2. Create an ingress qdisc
    out = await TcQdisc.add(input_data=[{dent: [
        {'dev': ingress_port, 'direction': 'ingress'}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add qdisc'

    # 3. Generate rule with random selectors
    selectors = {
        'want_mac': True, 'want_ip': True, 'want_port': True,
        'want_tcp': random.randint(0, 1), 'skip_sw': True, 'pref': pref,
        'action': {'trap': '', 'police': {'rate': f'{rate_bps}bps', 'burst': rate_bps + 1000}}}
    police_rule = tcutil_generate_rule_with_random_selectors(ingress_port, **selectors)

    drop_rule = deepcopy(police_rule)
    drop_rule['action'] = 'drop'
    drop_rule['pref'] *= 2

    # 4. Add two rules with those selectors to the ingress qdisc:
    out = await TcFilter.add(input_data=[{dent: [
        police_rule,  # first with police action
        drop_rule,  # second with action drop
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create tc rule'

    # 5. Prepare traffic matching the random selectors
    dev_groups = tgen_utils_dev_groups_from_config([
        {'ixp': tg_ports[0], 'ip': '1.1.1.1', 'gw': '2.2.2.2', 'plen': 24},
        {'ixp': tg_ports[1], 'ip': '2.2.2.2', 'gw': '1.1.1.1', 'plen': 24},
    ])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    out = await TcFilter.show(input_data=[{dent: [
        {'dev': ingress_port, 'direction': 'ingress', 'pref': pref, 'options': '-j'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get tc rule'

    streams = tcutil_tc_rules_to_tgen_streams(
        {ingress_port: out[0][dent]['parsed_output']},
        frame_rate_type='line_rate', frame_rate_pps=100,  # 100%
        frame_size=frame_size)

    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # 6. Send traffic, don't stop
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)

    # 7. Verify traffic is trapped by the police rule, and verify the CPU trapped rate for that rule
    await verify_cpu_rate(dent_dev, exp_rate_pps)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Traffic Item Statistics')
    assert 0 < tgen_utils_get_loss(stats.Rows) < 100, 'Unexpected traffic loss'
    await tgen_utils_stop_traffic(tgen_dev)

    # 8. Delete the first rule
    out = await TcFilter.delete(input_data=[{dent: [
        {'dev': ingress_port, 'direction': 'ingress', 'pref': pref}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create tc rule'

    # Add it again with the same priority as before
    out = await TcFilter.add(input_data=[{dent: [police_rule]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create tc rule'

    # 9. Send traffic
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)

    # 10. Verify it is handled according to the rule with the lowest priority
    await verify_cpu_rate(dent_dev, exp_rate_pps)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Traffic Item Statistics')
    assert 0 < tgen_utils_get_loss(stats.Rows) < 100, 'Unexpected traffic loss'
    await tgen_utils_stop_traffic(tgen_dev)

    # 11. Delete the first rule again
    out = await TcFilter.delete(input_data=[{dent: [
        {'dev': ingress_port, 'direction': 'ingress', 'pref': pref}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create tc rule'

    # Add it with higher priority than the other rule
    police_rule['pref'] *= 3
    out = await TcFilter.add(input_data=[{dent: [police_rule]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create tc rule'

    # 12. Send traffic
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)

    # 13. Verify traffic is no longer trapped (handled by the 'drop' rule)
    await verify_cpu_rate(dent_dev, 0)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Traffic Item Statistics')
    assert tgen_utils_get_loss(stats.Rows) == 100, 'Unexpected traffic'
    await tgen_utils_stop_traffic(tgen_dev)


@pytest.mark.usefixtures('cleanup_bonds')
async def test_devlink_interact_dyn_traps_lag(testbed):
    """
    Test Name: test_devlink_interact_dyn_traps_lag
    Test Suite: suite_functional_devlink
    Test Overview:
        Test devlink interaction with link aggregation
    Test Procedure:
    1. Create a bond, enslave ports
    2. Create an ingress qdisc
    3. Add the same police rule with random selectors to each port
    4. Prepare traffic matching the random selectors
    5. Send traffic
    6. Verify traffic is trapped by the police rule, and verify the CPU trapped rate for that rule
    """
    num_of_ports = 4
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], num_of_ports)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0][:num_of_ports]
    ports = tgen_dev.links_dict[dent][1][:num_of_ports]
    rate_bps = random.randint(400_000, 2_000_000)  # 0.1Mbps..2Mbps
    frame_size = random.randint(1000, 1500)
    exp_rate_pps = min(rate_bps / frame_size * num_of_ports, CPU_MAX_PPS)
    traffic_duration = 10  # sec
    bond = 'lag'

    dent_dev.applog.info(f'policer rate: {rate_bps // 1000}Kbps, traffic frame size: {frame_size}, '
                         f'expected trap rate: {exp_rate_pps // 1}pps')

    # 1. Create a bond
    out = await IpLink.add(input_data=[{dent: [
        {'name': bond, 'type': 'bond', 'mode': '802.3ad'}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bond'

    # Enslave ports
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'down'}
        for port in ports
    ] + [
        {'device': port, 'master': bond}
        for port in ports
    ] + [
        {'device': bond, 'operstate': 'up'}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to enslave ports'

    # 2. Create an ingress qdisc
    out = await TcQdisc.add(input_data=[{dent: [
        {'dev': port, 'direction': 'ingress'}
        for port in ports
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add qdisc'

    # 3. Add the same police rule with random selectors to each port
    selectors = {
        'want_mac': True, 'want_ip': True, 'want_port': True,
        'want_tcp': random.randint(0, 1), 'skip_sw': True,
        'action': {'trap': '', 'police': {'rate': f'{rate_bps}bps', 'burst': rate_bps + 1000}}}
    police_rule = tcutil_generate_rule_with_random_selectors(None, **selectors)

    out = await TcFilter.add(input_data=[{dent: [
        {**police_rule, 'dev': port}
        for port in ports
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create tc rule'

    # 4. Prepare traffic matching the random selectors
    dev_groups = tgen_utils_dev_groups_from_config([
        {'ixp': port, 'ip': '1.1.1.1', 'gw': '2.2.2.2', 'plen': 24}
        for port in tg_ports
    ])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    out = await TcFilter.show(input_data=[{dent: [
        {'dev': ports[0], 'direction': 'ingress', 'options': '-j'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get tc rule'

    streams = tcutil_tc_rules_to_tgen_streams(
        {port: out[0][dent]['parsed_output'] for port in ports},
        frame_rate_type='line_rate', frame_rate_pps=100,  # 100%
        frame_size=frame_size)

    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # 5. Send traffic, don't stop
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)

    # 6. Verify traffic is trapped by the police rule, and verify the CPU trapped rate for that rule
    await verify_cpu_rate(dent_dev, exp_rate_pps)
    await tgen_utils_stop_traffic(tgen_dev)


@pytest.mark.usefixtures('disable_sct')
async def test_devlink_interact_static_traps_disabled(testbed):
    """
    Test Name: test_devlink_interact_static_traps_disabled
    Test Suite: suite_functional_devlink
    Test Overview:
        Test devlink with SCT disabled
    Test Procedure:
    1. Disable SCT
    2. Set link up on interfaces on all participant ports
    3. Create an ingress qdisc
    4. Add a rule with randomly generated selectors
    5. Prepare a matching stream for the randomly selected selectors
    6. Transmit traffic
    7. Verify CPU trapped packet rate is as expected
    """
    num_of_ports = 2
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], num_of_ports)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0][:num_of_ports]
    ports = tgen_dev.links_dict[dent][1][:num_of_ports]
    ingress_port = ports[0]
    frame_size = random.randint(100, 1000)
    exp_rate_pps = random.randint(5_000, 10_000)
    rate_bps = exp_rate_pps * frame_size  # 1Mbps..10Mbps
    traffic_duration = 10  # sec

    dent_dev.applog.info(f'policer rate: {rate_bps // 1000}Kbps, traffic frame size: {frame_size}, '
                         f'expected trap rate: {exp_rate_pps // 1}pps')

    # 1. SCT disabled by fixture

    # 2. Set link up on interfaces on all participant ports
    out = await IpLink.set(input_data=[{dent: [
        {'device': ingress_port, 'operstate': 'up'}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to enslave ports'

    # 3. Create an ingress qdisc
    out = await TcQdisc.add(input_data=[{dent: [
        {'dev': ingress_port, 'direction': 'ingress'}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add qdisc'

    # 4. Add a rule with randomly generated selectors
    selectors = {
        'want_mac': True, 'want_ip': True, 'want_port': True,
        'want_tcp': random.randint(0, 1), 'skip_sw': True,
        'action': {'trap': '', 'police': {'rate': f'{rate_bps}bps', 'burst': rate_bps + 1000}}}
    police_rule = tcutil_generate_rule_with_random_selectors(ingress_port, **selectors)

    out = await TcFilter.add(input_data=[{dent: [police_rule]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create tc rule'

    # 5. Prepare a matching stream for the randomly selected selectors
    dev_groups = tgen_utils_dev_groups_from_config([
        {'ixp': tg_ports[0], 'ip': '1.1.1.1', 'gw': '2.2.2.2', 'plen': 24},
        {'ixp': tg_ports[1], 'ip': '2.2.2.2', 'gw': '1.1.1.1', 'plen': 24},
    ])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    out = await TcFilter.show(input_data=[{dent: [
        {'dev': ingress_port, 'direction': 'ingress', 'options': '-j'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get tc rule'

    streams = tcutil_tc_rules_to_tgen_streams(
        {ingress_port: out[0][dent]['parsed_output']},
        frame_rate_type='line_rate', frame_rate_pps=100,  # 100%
        frame_size=frame_size)

    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # 6. Transmit traffic
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)

    # 7. Verify CPU trapped packet rate is as expected
    await verify_cpu_rate(dent_dev, exp_rate_pps)
    await tgen_utils_stop_traffic(tgen_dev)
