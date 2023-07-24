import asyncio
import pytest
from random import randint, choice
from copy import deepcopy

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.tc.tc_qdisc import TcQdisc
from dent_os_testbed.lib.tc.tc_filter import TcFilter
from dent_os_testbed.test.test_suite.functional.devlink.devlink_utils import (
    randomize_rule_by_src_dst_field,
    verify_cpu_rate, CPU_MAX_PPS)

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic
)

from dent_os_testbed.utils.test_utils.tc_flower_utils import tcutil_generate_rule_with_random_selectors

pytestmark = [
    pytest.mark.suite_functional_devlink,
    pytest.mark.usefixtures('define_bash_utils', 'cleanup_tgen', 'cleanup_qdiscs'),
    pytest.mark.asyncio,
]


@pytest.mark.parametrize('block_type', ['single_block', 'shared_block'])
async def test_devlink_same_rule_pref(testbed, block_type):
    """
    Test Name: test_devlink_same_rule_pref
    Test Suite: suite_functional_devlink
    Test Overview: Test devlink single/shared block priority of same rules
    Test Procedure:
    1. Set link up on interfaces and connect devices
    2. Create an ingress queue for all participant TX ports
    3. Create within the ingress qdisc two rules with the same selectors (generated random),
       but with identical pref value
    4. Prepare matching traffic and transmit
    5. Verify it is handled according to the first rule add action
    6. Delete the first rule and add it again with the same priority as before
    7. Send traffic matching the rules selectors and verify traffic is handled by the first rule added to the qdisc
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dev_name = dent_devices[0].host_name
    dent_dev = dent_devices[0]
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]
    frame_size = randint(128, 1400)
    # Calculate max possible rate for cpu trap 4000pps is max
    max_rate = frame_size * CPU_MAX_PPS
    policer_rate = randint(30000, max_rate)
    policer_rate_2 = policer_rate // randint(2, 4)
    pref = randint(1000, 25000)
    block = randint(100, 300)
    shared_block = block_type == 'shared_type'

    # 1.Set link up on interfaces and connect devices
    out = await IpLink.set(
        input_data=[{dev_name: [
            {'device': port, 'operstate': 'up'} for port in dut_ports]}])
    err_msg = f"Verify that ports set to 'UP' state.\n{out}"
    assert out[0][dev_name]['rc'] == 0, err_msg

    dev_groups = tgen_utils_dev_groups_from_config(
        [{'ixp': tg_ports[0], 'ip': '1.1.1.3', 'gw': '1.1.1.1', 'plen': 24},
         {'ixp': tg_ports[1], 'ip': '2.2.2.4', 'gw': '2.2.2.1', 'plen': 24},
         {'ixp': tg_ports[2], 'ip': '3.3.3.4', 'gw': '3.3.3.1', 'plen': 24},
         {'ixp': tg_ports[3], 'ip': '4.4.4.4', 'gw': '4.4.4.1', 'plen': 24}]
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    # 2.Create an ingress queue for all participant TX ports
    if shared_block:
        for port in dut_ports[:3]:
            out = await TcQdisc.add(
                input_data=[{dev_name: [
                    {'dev': port, 'ingress_block': block, 'direction': 'ingress'}]}])
            err_msg = f'Verify no error on setting Qdist for {port}.\n{out}'
            assert out[0][dev_name]['rc'] == 0, err_msg
    else:
        out = await TcQdisc.add(input_data=[{dev_name: [{'dev': dut_ports[0], 'direction': 'ingress'}]}])
        err_msg = f'Verify no error on setting Qdist for {dut_ports[0]}.\n{out}'
        assert out[0][dev_name]['rc'] == 0, err_msg

    # 3.Create within the ingress qdisc two rules with the same selectors (generated random), but with identical pref value
    rule_selectors = {'action': {'trap': '',
                                 'police': {'rate': f'{policer_rate}bps', 'burst': policer_rate + 1000,
                                            'conform-exceed': '', 'drop': ''}},
                      'skip_sw': True,
                      'want_mac': True,
                      'want_vlan': True,
                      'want_vlan_ethtype': False,
                      'pref': pref}
    tc_rule = tcutil_generate_rule_with_random_selectors(dut_ports[0], **rule_selectors)

    tc_rule['protocol'] = '0x8100'
    if shared_block:
        tc_rule['block'] = block
        del tc_rule['dev']
    tc_rule_copy = deepcopy(tc_rule)
    del tc_rule['filtertype']['src_mac']

    out = await TcFilter.add(input_data=[{dev_name: [tc_rule]}])
    assert out[0][dev_name]['rc'] == 0, f'Failed to create tc rule \n{out}'

    tc_rule['filtertype']['src_mac'] = tc_rule_copy['filtertype']['src_mac']
    tc_rule['action']['police']['rate'] = f'{policer_rate_2}bps'
    tc_rule['action']['police']['burst'] = policer_rate_2 + 1000
    out = await TcFilter.add(input_data=[{dev_name: [tc_rule]}])
    assert out[0][dev_name]['rc'] == 0, f'Failed to create tc rule \n{out}'

    # 4.Prepare matching traffic and transmit
    streams = {f'stream_{idx + 1}': {
            'type': 'raw',
            'protocol': '802.1Q',
            'ip_source': dev_groups[tg_ports[idx]][0]['name'],
            'ip_destination': dev_groups[tg_ports[3]][0]['name'],
            'srcMac': tc_rule_copy['filtertype']['src_mac'],
            'dstMac': tc_rule_copy['filtertype']['dst_mac'],
            'vlanID': tc_rule_copy['filtertype']['vlan_id'],
            'frame_rate_type': 'line_rate',
            'frameSize': frame_size,
            'rate': 100
    } for idx in range(3 if shared_block else 1)}
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)
    await tgen_utils_start_traffic(tgen_dev)

    # 5.Verify it is handled according to the first rule add action
    exp_rate = policer_rate / frame_size
    await asyncio.sleep(10)
    await verify_cpu_rate(dent_dev, exp_rate)
    await tgen_utils_stop_traffic(tgen_dev)

    # 6.Delete the first rule and add it again with the same priority as before
    if shared_block:
        out = await TcFilter.delete(input_data=[{dev_name: [{'block': block, 'direction': 'ingress',
                                                             'pref': pref, 'handle': '0x1',
                                                             'filtertype': {}}]}])
        assert out[0][dev_name]['rc'] == 0, f'Failed to create tc rule \n{out}'
    else:
        out = await TcFilter.delete(input_data=[{dev_name: [{'dev': dut_ports[0], 'direction': 'ingress',
                                                             'pref': pref, 'handle': '0x1',
                                                             'filtertype': {}}]}])
        assert out[0][dev_name]['rc'] == 0, f'Failed to create tc rule \n{out}'

    del tc_rule_copy['filtertype']['src_mac']
    out = await TcFilter.add(input_data=[{dev_name: [tc_rule_copy]}])
    assert out[0][dev_name]['rc'] == 0, f'Failed to create tc rule \n{out}'

    # 7.Send traffic matching the rules selectors and verify traffic is handled by the first rule added to the qdisc
    await tgen_utils_start_traffic(tgen_dev)
    exp_rate = policer_rate_2 / frame_size
    await asyncio.sleep(10)
    await verify_cpu_rate(dent_dev, exp_rate)
    await tgen_utils_stop_traffic(tgen_dev)


@pytest.mark.parametrize('block_type', ['single_block', 'shared_block'])
async def test_devlink_rule_priority(testbed, block_type):
    """
    Test Name: test_devlink_rule_priority
    Test Suite: suite_functional_devlink
    Test Overview: Test devlink single/shared block priority of rules
    Test Procedure:
    1. Set link up on interfaces and connect devices
    2. Create an ingress queue for all participant TX ports
    3. Create within the ingress qdisc two rules with the same selectors (generated random),
       different police rate and second rule pref < first rule pref
    4. Prepare matching traffic and transmit
    5. Verify it is handled according to rule with highest priority
    6. Delete the first rule and add it again with the same priority as before
    7. Send traffic matching the rules selectors and verify it is still handled
       according to rule with lowest pref (highest priority)
    8. Delete the rule again and add it with higher priority than the other rule
    9. Send traffic matching the rules selectors and verify it is handled according to the rule with the highest priority
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dev_name = dent_devices[0].host_name
    dent_dev = dent_devices[0]
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]
    frame_size = randint(128, 1400)
    # Calculate max possible rate for cpu trap 4000pps is max
    max_rate = frame_size * CPU_MAX_PPS
    policer_rate = randint(30000, max_rate)
    policer_rate_2 = policer_rate // randint(2, 4)
    pref = randint(10000, 25000)
    block = randint(100, 300)
    want_ip = choice([True, False])
    want_port = choice([True, False]) if want_ip else False
    want_vlan = choice([True, False])
    shared_block = block_type == 'shared_type'

    # 1.Set link up on interfaces and connect devices
    out = await IpLink.set(
        input_data=[{dev_name: [
            {'device': port, 'operstate': 'up'} for port in dut_ports]}])
    err_msg = f"Verify that ports set to 'UP' state.\n{out}"
    assert out[0][dev_name]['rc'] == 0, err_msg

    dev_groups = tgen_utils_dev_groups_from_config(
        [{'ixp': tg_ports[0], 'ip': '1.1.1.3', 'gw': '1.1.1.1', 'plen': 24},
         {'ixp': tg_ports[1], 'ip': '2.2.2.4', 'gw': '2.2.2.1', 'plen': 24},
         {'ixp': tg_ports[2], 'ip': '3.3.3.4', 'gw': '3.3.3.1', 'plen': 24},
         {'ixp': tg_ports[3], 'ip': '4.4.4.4', 'gw': '4.4.4.1', 'plen': 24}]
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    # 2.Create an ingress queue for all participant TX ports
    if shared_block:
        for port in dut_ports[:3]:
            out = await TcQdisc.add(
                input_data=[{dev_name: [
                    {'dev': port, 'ingress_block': block, 'direction': 'ingress'}]}])
            err_msg = f'Verify no error on setting Qdist for {port}.\n{out}'
            assert out[0][dev_name]['rc'] == 0, err_msg
    else:
        out = await TcQdisc.add(input_data=[{dev_name: [{'dev': dut_ports[0], 'direction': 'ingress'}]}])
        err_msg = f'Verify no error on setting Qdist for {dut_ports[0]}.\n{out}'
        assert out[0][dev_name]['rc'] == 0, err_msg

    # 3.Create within the ingress qdisc two rules with the same selectors (generated random),
    # different police rate and second rule pref < first rule pref
    rule_selectors = {'action': {'trap': '',
                                 'police': {'rate': f'{policer_rate}bps', 'burst': policer_rate + 1000,
                                            'conform-exceed': '', 'drop': ''}},
                      'skip_sw': True,
                      'want_mac': True,
                      'want_vlan': want_vlan,
                      'want_ip': want_ip,
                      'want_port': want_port,
                      'want_tcp': choice([True, False]) if want_port else False,
                      'want_vlan_ethtype': want_ip and want_vlan,
                      'pref': pref}

    tc_rule = tcutil_generate_rule_with_random_selectors(dut_ports[0], **rule_selectors)
    if shared_block:
        tc_rule['block'] = block
        del tc_rule['dev']

    original_rule = deepcopy(tc_rule)
    randomize_rule_by_src_dst_field(tc_rule, rule_selectors)
    first_tc_rule = deepcopy(tc_rule)

    out = await TcFilter.add(input_data=[{dev_name: [tc_rule]}])
    assert out[0][dev_name]['rc'] == 0, f'Failed to create tc rule \n{out}'

    tc_rule['action']['police']['rate'] = f'{policer_rate_2}bps'
    tc_rule['action']['police']['burst'] = policer_rate_2 + 1000
    tc_rule['pref'] = pref + 1000

    out = await TcFilter.add(input_data=[{dev_name: [tc_rule]}])
    assert out[0][dev_name]['rc'] == 0, f'Failed to create tc rule \n{out}'

    # 4.Prepare matching traffic and transmit
    streams = {f'stream_{idx + 1}': {
            'type': 'raw',
            'protocol': '802.1Q' if want_vlan else tc_rule['protocol'],
            'ip_source': dev_groups[tg_ports[idx]][0]['name'],
            'ip_destination': dev_groups[tg_ports[3]][0]['name'],
            'srcMac': original_rule['filtertype']['src_mac'],
            'dstMac': original_rule['filtertype']['dst_mac'],
            'frame_rate_type': 'line_rate',
            'frameSize': frame_size,
            'rate': 100
    } for idx in range(3 if shared_block else 1)}

    for name in list(streams.keys()):
        if want_vlan:
            streams[name]['vlanID'] = original_rule['filtertype']['vlan_id']
        if want_ip:
            streams[name]['srcIp'] = original_rule['filtertype']['src_ip']
            streams[name]['dstIp'] = original_rule['filtertype']['dst_ip']
        if want_port:
            streams[name]['ipproto'] = original_rule['filtertype']['ip_proto']
            streams[name]['srcPort'] = original_rule['filtertype']['src_port']
            streams[name]['dstPort'] = original_rule['filtertype']['dst_port']

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)
    await tgen_utils_start_traffic(tgen_dev)

    # 5.Verify it is handled according to rule with lowest pref (highest priority)
    exp_rate = policer_rate / frame_size
    await asyncio.sleep(10)
    await verify_cpu_rate(dent_dev, exp_rate)
    await tgen_utils_stop_traffic(tgen_dev)

    # 6.Delete the first rule and add it again with the same priority as before
    if shared_block:
        out = await TcFilter.delete(input_data=[{dev_name: [{'block': block, 'direction': 'ingress', 'pref': pref}]}])
        assert out[0][dev_name]['rc'] == 0, f'Failed to create tc rule \n{out}'
    else:
        out = await TcFilter.delete(input_data=[{dev_name: [{'dev': dut_ports[0], 'direction': 'ingress', 'pref': pref}]}])
        assert out[0][dev_name]['rc'] == 0, f'Failed to create tc rule \n{out}'

    out = await TcFilter.add(input_data=[{dev_name: [first_tc_rule]}])
    assert out[0][dev_name]['rc'] == 0, f'Failed to create tc rule \n{out}'

    # 7.Send traffic matching the rules selectors and verify it is still handled
    # according to rule with lowest pref (highest priority)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(10)
    await verify_cpu_rate(dent_dev, exp_rate)
    await tgen_utils_stop_traffic(tgen_dev)

    # 8.Delete the rule again and add it with higher priority than the other rule
    if shared_block:
        out = await TcFilter.delete(input_data=[{dev_name: [{'block': block, 'direction': 'ingress', 'pref': pref}]}])
        assert out[0][dev_name]['rc'] == 0, f'Failed to create tc rule \n{out}'
    else:
        out = await TcFilter.delete(input_data=[{dev_name: [{'dev': dut_ports[0], 'direction': 'ingress', 'pref': pref}]}])
        assert out[0][dev_name]['rc'] == 0, f'Failed to create tc rule \n{out}'

    first_tc_rule['pref'] = pref + 2000
    out = await TcFilter.add(input_data=[{dev_name: [first_tc_rule]}])
    assert out[0][dev_name]['rc'] == 0, f'Failed to create tc rule \n{out}'

    # 9.Send traffic matching the rules selectors and verify it is handled according to the rule with the highest priority
    await tgen_utils_start_traffic(tgen_dev)
    exp_rate = policer_rate_2 / frame_size
    await asyncio.sleep(10)
    await verify_cpu_rate(dent_dev, exp_rate)
    await tgen_utils_stop_traffic(tgen_dev)
