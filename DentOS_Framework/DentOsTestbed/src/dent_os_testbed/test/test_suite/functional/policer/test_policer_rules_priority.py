import asyncio
import pytest
import random
import copy
from math import isclose

from dent_os_testbed.lib.tc.tc_filter import TcFilter
from dent_os_testbed.lib.tc.tc_qdisc import TcQdisc
from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_get_traffic_stats
)

from dent_os_testbed.utils.test_utils.tc_flower_utils import tcutil_tc_rules_to_tgen_streams

pytestmark = [
    pytest.mark.suite_functional_policer,
    pytest.mark.usefixtures('cleanup_bridges', 'cleanup_qdiscs', 'cleanup_tgen'),
    pytest.mark.asyncio,
]


@pytest.mark.parametrize('qdisc_type', ['port', 'shared_block'])
async def test_policer_rules_priority(testbed, qdisc_type):
    """
    Test Name: Policer rules priority
    Test Suite: suite_functional_policer
    Test Overview: Verify policer rules priority with port/shared block
    Test Procedure:
    1. Create a bridge entity and set link up on it.
    2. Set link up on interfaces on all participant ports. Enslave all participant ports to the bridge.
    3. Create an ingress queue for all participant TX ports
    4. Create within the ingress qdisc two rules with the same selectors (generated random),
        and with: different police rate value second rule pref < first rule pref
    5. Prepare matching traffic and transmit
    6. Verify it is handled according to the first rule add action
    7. Delete the first rule and add it again with the same priority as before
    8. Send traffic matching the rules selectors
    9. Verify it is still handled according to the rule with the lowest priority
    10. Delete the rule again and add it with higher priority than the other rule
    11. Send traffic matching the rules selectors
    12. Verify it is still handled according to the rule with the lowest priority
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip(
            'The testbed does not have enough dent with tgen connections')
    device = dent_devices[0]
    dent = device.host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]
    ports_with_rule = ports[:1] if qdisc_type == 'port' else ports[1:]
    bridge = 'bridge0'
    block = random.randint(5, 3000)
    tc_rule_1_frame_rate = 250000  # bps
    tc_rule_2_frame_rate = tc_rule_1_frame_rate + tc_rule_1_frame_rate * 0.10  # bps
    dev_or_block = {'dev': ports_with_rule[0]} if qdisc_type == 'port' else {'block': block}
    tolerance = 0.12

    # 1. Create a bridge entity and set link up on it.
    out = await IpLink.add(input_data=[{dent: [{
        'dev': 'bridge0',
        'type': 'bridge'}]
    }])
    assert out[0][dent]['rc'] == 0, 'Failed creating bridge.'

    await IpLink.set(input_data=[{dent: [{'device': bridge, 'operstate': 'up'}]}])
    assert out[0][dent]['rc'] == 0, 'Failed setting bridge to state UP.'

    # 2. Set link up on interfaces on all participant ports. Enslave all participant ports to the bridge.
    out = await IpLink.set(input_data=[{dent: [{
        'device': port,
        'operstate': 'up',
        'master': bridge
    } for port in ports]}])
    assert out[0][dent]['rc'] == 0, 'Failed setting link to state UP.'

    config = [{'dev': port, 'ingress_block': block, 'direction': 'ingress'} for port in ports_with_rule]
    if qdisc_type == 'port':
        for item in config:
            del item['ingress_block']

    # 3. Create an ingress queue for all participant TX ports
    out = await TcQdisc.add(input_data=[{dent: config}])
    assert out[0][dent]['rc'] == 0, 'Failed to create a qdisc'

    # 4.Create within the ingress qdisc two rules with the same selectors (generated random),
    # and with: different police rate value first rule pref < second rule pref

    tc_rule_1 = {
            'action': {
                'police': {
                    'rate': tc_rule_1_frame_rate,
                    'burst': tc_rule_1_frame_rate + 1000,
                    'conform-exceed': 'drop'}
            },
            'direction': 'ingress',
            'protocol': '0x8100 ',
            'filtertype': {
                'skip_sw': '',
                'src_mac': '02:15:53:62:36:d1',
                'dst_mac': '02:06:a2:54:22:9f',
                'vlan_id': 1942},
            'pref': 100,
        }

    # First rule
    tc_rule_1.update(dev_or_block)
    out = await TcFilter.add(input_data=[{dent: [tc_rule_1]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create tc rule'

    # Second rule
    tc_rule_2 = copy.deepcopy(tc_rule_1)
    tc_rule_2['pref'] = 200
    tc_rule_2['action']['police']['rate'] = tc_rule_2_frame_rate
    tc_rule_2['action']['police']['burst'] = tc_rule_2_frame_rate + 1000

    out = await TcFilter.add(input_data=[{dent: [tc_rule_2]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create tc rule'

    # 5.Prepare matching traffic and transmit
    created_rules = {
        'direction': 'ingress',
        'options': '-j'}
    created_rules.update(dev_or_block)

    out = await TcFilter.show(input_data=[{dent: [created_rules]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get tc rule'

    out = await TcFilter.show(input_data=[{dent: [created_rules]}], parse_output=True)
    streams = tcutil_tc_rules_to_tgen_streams({port: out[0][dent]['parsed_output'] for port in ports_with_rule},
                                              frame_rate_type='line_rate',
                                              frame_rate_pps=100)

    dev_groups = tgen_utils_dev_groups_from_config((
        {'ixp': tg_ports[0], 'ip': '1.1.1.1', 'gw': '1.1.1.10', 'plen': 24},
        {'ixp': tg_ports[1], 'ip': '1.1.1.2', 'gw': '1.1.1.10', 'plen': 24},
        {'ixp': tg_ports[2], 'ip': '1.1.1.3', 'gw': '1.1.1.10', 'plen': 24},
        {'ixp': tg_ports[3], 'ip': '1.1.1.4', 'gw': '1.1.1.10', 'plen': 24}
    ))
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    await tgen_utils_setup_streams(tgen_dev, None, streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(30)

    # 6. Verify it is handled according to the first rule add action
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Port Statistics')
    for row in stats.Rows:
        err_msg = f'Expected {tc_rule_1_frame_rate} got : {float(row["Rx. Rate (bps)"])}'
        if qdisc_type == 'port':
            if row['Port Name'] == tg_ports[0]:
                continue
            assert isclose(float(row['Rx. Rate (bps)']), tc_rule_1_frame_rate, rel_tol=tolerance), err_msg
        else:
            if row['Port Name'] == tg_ports[0]:
                assert isclose(float(row['Rx. Rate (bps)']), tc_rule_1_frame_rate, rel_tol=tolerance), err_msg

    # 7. Delete the first rule and add it again with the same priority as before
    out = await TcFilter.delete(input_data=[{dent: [tc_rule_1]}])
    assert out[0][dent]['rc'] == 0, 'Failed to delete tc rule '

    out = await TcFilter.add(input_data=[{dent: [tc_rule_1]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create tc rule'

    # 8. Send traffic matching the rules selectors
    await asyncio.sleep(5)

    # 9. Verify it is still handled according to the rule with the lowest priority
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Port Statistics')
    for row in stats.Rows:
        err_msg = f'Expected {tc_rule_1_frame_rate} got : {float(row["Rx. Rate (bps)"])}'
        if qdisc_type == 'port':
            if row['Port Name'] == tg_ports[0]:
                continue
            assert isclose(float(row['Rx. Rate (bps)']), tc_rule_1_frame_rate, rel_tol=tolerance), err_msg
        else:
            if row['Port Name'] == tg_ports[0]:
                assert isclose(float(row['Rx. Rate (bps)']), tc_rule_1_frame_rate, rel_tol=tolerance), err_msg

    # 10. Delete the rule again and add it with higher priority than the other rule
    out = await TcFilter.delete(input_data=[{dent: [tc_rule_1]}])
    assert out[0][dent]['rc'] == 0, 'Failed to delete tc rule '

    tc_rule_1['pref'] = tc_rule_2['pref'] + 100
    out = await TcFilter.add(input_data=[{dent: [tc_rule_1]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create tc rule'

    # 11. Send traffic matching the rules selectors
    await asyncio.sleep(10)

    # 12. Verify it is still handled according to the rule with the lowest priority
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Port Statistics')
    for row in stats.Rows:
        err_msg = f'Expected {tc_rule_2_frame_rate} got : {float(row["Rx. Rate (bps)"])}'
        if qdisc_type == 'port':
            if row['Port Name'] == tg_ports[0]:
                continue
            assert isclose(float(row['Rx. Rate (bps)']), tc_rule_2_frame_rate, rel_tol=tolerance), err_msg
        else:
            if row['Port Name'] == tg_ports[0]:
                assert isclose(float(row['Rx. Rate (bps)']), tc_rule_2_frame_rate, rel_tol=tolerance), err_msg

    await tgen_utils_stop_traffic(tgen_dev)
