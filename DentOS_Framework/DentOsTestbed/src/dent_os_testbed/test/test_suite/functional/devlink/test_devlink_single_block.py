import asyncio
import pytest
from random import choice, randint
from math import floor
from copy import deepcopy


from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.tc.tc_qdisc import TcQdisc
from dent_os_testbed.lib.tc.tc_filter import TcFilter

from dent_os_testbed.test.test_suite.functional.devlink.devlink_utils import (
    randomize_rule_by_src_dst_field,
    overwrite_src_dst_stream_fields,
    verify_cpu_rate,
    CPU_MAX_PPS, RATE_UNITS)

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic
)

from dent_os_testbed.utils.test_utils.tc_flower_utils import (
    tcutil_generate_rule_with_random_selectors,
    tcutil_tc_rules_to_tgen_streams,
)

pytestmark = [
    pytest.mark.suite_functional_devlink,
    pytest.mark.usefixtures('define_bash_utils', 'cleanup_qdiscs'),
    pytest.mark.asyncio,
]


@pytest.mark.parametrize('traffic', ['l2', 'l3', 'l4'])
async def test_devlink_basic(testbed, traffic):
    """
    Test Name: test_devlink_basic
    Test Suite: suite_functional_devlink
    Test Overview: Test devlink single block basic functionality with (l2, l3, l4) traffic
    Test Procedure:
    1. Set link up on interfaces on all participant ports and connect devices
    2. Create an ingress qdisc on first port connected to Ixia and add a rule with (l2, l3, l4) selectors
    3. Prepare a matching stream for the randomly selected selectors and transmit traffic
    4. Verify CPU trapped packet rate is as expected
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dev_name = dent_devices[0].host_name
    dent_dev = dent_devices[0]
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]
    frame_size = randint(128, 1400)
    # Calculate max possible rate for cpu trap 4000pps is max
    max_rate = frame_size * CPU_MAX_PPS
    policer_rate = randint(300000, max_rate)

    # 1.Set link up on interfaces on all participant ports and connect devices
    out = await IpLink.set(
        input_data=[{dev_name: [
            {'device': port, 'operstate': 'up'} for port in dut_ports]}])
    err_msg = f"Verify that ports set to 'UP' state.\n{out}"
    assert out[0][dev_name]['rc'] == 0, err_msg

    dev_groups = tgen_utils_dev_groups_from_config(
        [{'ixp': tg_ports[0], 'ip': '1.1.1.3', 'gw': '1.1.1.1', 'plen': 24},
         {'ixp': tg_ports[1], 'ip': '2.2.2.4', 'gw': '2.2.2.1', 'plen': 24}]
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    # 2.Create an ingress qdisc on first port connected to Ixia and add a rule with (l2, l3, l4) selectors
    out = await TcQdisc.add(
        input_data=[{dev_name: [
            {'dev': dut_ports[0], 'direction': 'ingress'}]}])
    err_msg = f'Verify no error on setting Qdist for {dut_ports[0]}.\n{out}'
    assert out[0][dev_name]['rc'] == 0, err_msg

    rule = {'action': {'trap': '',
                       'police': {'rate': f'{policer_rate}bps', 'burst': policer_rate + 1000,
                                  'conform-exceed': '', 'drop': ''}},
            'want_ip': True if traffic in ['l3', 'l4'] else False,
            'want_port': True if traffic == 'l4' else False,
            'skip_sw': True,
            'want_mac': True if traffic == 'l2' else False,
            'want_vlan': True if traffic == 'l2' else False,
            'want_tcp': choice([True, False]) if traffic == 'l4' else False,
            'want_vlan_ethtype': False,
            }

    tc_rule = tcutil_generate_rule_with_random_selectors(dut_ports[0], **rule)

    if traffic == 'l2':
        tc_rule['protocol'] = choice(('0x8100', '802.1q'))
        tc_rule['filtertype']['src_mac'] = 'aa:aa:aa:aa:aa:00'
        tc_rule['filtertype']['dst_mac'] = 'aa:00:00:00:00:55'
    elif traffic == 'l3':
        tc_rule['filtertype']['src_mac'] = '00:00:00:00:00:01'
        tc_rule['filtertype']['dst_mac'] = '00:00:00:00:00:02'
    elif traffic == 'l4':
        tc_rule['filtertype']['src_mac'] = '00:00:00:00:00:01'
        tc_rule['filtertype']['dst_mac'] = '00:00:00:00:00:02'
        tc_rule['filtertype']['src_ip'] = '1.1.1.2'
        tc_rule['filtertype']['dst_ip'] = '2.2.2.3'

    out = await TcFilter.add(input_data=[{dev_name: [tc_rule]}])
    assert out[0][dev_name]['rc'] == 0, f'Failed to create tc rule \n{out}'

    # 3.Prepare a matching stream for the randomly selected selectors and transmit traffic
    out = await TcFilter.show(input_data=[{dev_name: [
        {'dev': dut_ports[0], 'direction': 'ingress', 'options': '-j'}]}], parse_output=True)
    assert out[0][dev_name]['rc'] == 0, f'Failed to get tc rule \n{out}'

    streams = tcutil_tc_rules_to_tgen_streams({dut_ports[0]: out[0][dev_name]['parsed_output']},
                                              frame_rate_pps=100, frame_rate_type='line_rate',
                                              frame_size=frame_size)
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)
    await tgen_utils_start_traffic(tgen_dev)

    # 4.Verify CPU trapped packet rate is as expected
    # Calculate expected pkt rate based on policer rate limitation
    exp_rate = policer_rate / frame_size
    await asyncio.sleep(10)
    await verify_cpu_rate(dent_dev, exp_rate)
    await tgen_utils_stop_traffic(tgen_dev)


async def test_devlink_random(testbed):
    """
    Test Name: test_devlink_random
    Test Suite: suite_functional_devlink
    Test Overview: Test devlink single block basic functionality with random traffic
    Test Procedure:
    1. Set link up on interfaces on all participant ports and connect devices
    2. Create an ingress qdisc on first port connected to Ixia and add a rule with random selectors
    3. Prepare a matching stream for the randomly selected selectors and transmit traffic
    4. Verify CPU trapped packet rate is as expected
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dev_name = dent_devices[0].host_name
    dent_dev = dent_devices[0]
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]
    frame_size = randint(128, 1400)
    # Calculate max possible rate for cpu trap 4000pps is max
    max_rate = frame_size * CPU_MAX_PPS
    policer_rate = randint(300000, max_rate)
    want_ip = choice([True, False])
    want_port = choice([True, False]) if want_ip else False
    want_vlan = choice([True, False])

    # 1.Set link up on interfaces on all participant ports and connect devices
    out = await IpLink.set(
        input_data=[{dev_name: [
            {'device': port, 'operstate': 'up'} for port in dut_ports]}])
    err_msg = f"Verify that ports set to 'UP' state.\n{out}"
    assert out[0][dev_name]['rc'] == 0, err_msg

    dev_groups = tgen_utils_dev_groups_from_config(
        [{'ixp': tg_ports[0], 'ip': '1.1.1.3', 'gw': '1.1.1.1', 'plen': 24},
         {'ixp': tg_ports[1], 'ip': '2.2.2.4', 'gw': '2.2.2.1', 'plen': 24}]
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    # 2.Create an ingress qdisc on first port connected to Ixia and add a rule with selectors
    out = await TcQdisc.add(
        input_data=[{dev_name: [
            {'dev': dut_ports[0], 'direction': 'ingress'}]}])
    err_msg = f'Verify no error on setting Qdist for {dut_ports[0]}.\n{out}'
    assert out[0][dev_name]['rc'] == 0, err_msg

    rule_selectors = {'action': {'trap': '',
                                 'police': {'rate': f'{policer_rate}bps', 'burst': policer_rate + 1000,
                                            'conform-exceed': '', 'drop': ''}},
                      'skip_sw': True,
                      'want_mac': True,
                      'want_vlan': want_vlan,
                      'want_ip': want_ip,
                      'want_port': want_port,
                      'want_tcp': choice([True, False]) if want_port else False,
                      'want_vlan_ethtype': True if want_ip and want_vlan else False}

    tc_rule = tcutil_generate_rule_with_random_selectors(dut_ports[0], **rule_selectors)
    tc_rule_copy = deepcopy(tc_rule)
    randomize_rule_by_src_dst_field(tc_rule, rule_selectors)

    out = await TcFilter.add(input_data=[{dev_name: [tc_rule]}])
    assert out[0][dev_name]['rc'] == 0, f'Failed to create tc rule \n{out}'

    # 3.Prepare a matching stream for the randomly selected selectors and transmit traffic
    out = await TcFilter.show(input_data=[{dev_name: [
        {'dev': dut_ports[0], 'direction': 'ingress', 'options': '-j'}]}], parse_output=True)
    assert out[0][dev_name]['rc'] == 0, f'Failed to get tc rule \n{out}'

    streams = tcutil_tc_rules_to_tgen_streams({dut_ports[0]: out[0][dev_name]['parsed_output']},
                                              frame_rate_pps=100, frame_rate_type='line_rate',
                                              frame_size=frame_size)

    # Overwrite stream dst/src fields after we randomized dst/src fields applying
    overwrite_src_dst_stream_fields(streams, tc_rule_copy, rule_selectors)
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)
    await tgen_utils_start_traffic(tgen_dev)

    # 4.Verify CPU trapped packet rate is as expected
    # Calculate expected pkt rate based on policer rate limitation
    exp_rate = policer_rate / frame_size
    await asyncio.sleep(10)
    await verify_cpu_rate(dent_dev, exp_rate)
    await tgen_utils_stop_traffic(tgen_dev)


async def test_devlink_policer_log(testbed):
    """
    Test Name: test_devlink_policer_log
    Test Suite: suite_functional_devlink
    Test Overview: Test devlink single block basic functionality with random traffic and policer loggin
    Test Procedure:
    1. Set link up on interfaces on all participant ports
    2. Create an ingress qdisc on first port connected to Ixia port and add
       two rules with randomly generated selectors: one with police action
       and one with log action
    3. Prepare a matching stream for the randomly selected selectors and transmit traffic
    4. Verify CPU matched packets are logged into /var/log/messages
    5. Verify CPU trapped packet rate is as expected
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dev_name = dent_devices[0].host_name
    dent_dev = dent_devices[0]
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]
    frame_size = randint(300, 800)
    policer_rate = 100
    want_ip = choice([True, False])
    want_port = choice([True, False]) if want_ip else False
    want_vlan = choice([True, False])

    # 1.Set link up on interfaces on all participant ports and connect devices
    out = await IpLink.set(
        input_data=[{dev_name: [
            {'device': port, 'operstate': 'up'} for port in dut_ports]}])
    err_msg = f"Verify that ports set to 'UP' state.\n{out}"
    assert out[0][dev_name]['rc'] == 0, err_msg

    dev_groups = tgen_utils_dev_groups_from_config(
        [{'ixp': tg_ports[0], 'ip': '1.1.1.3', 'gw': '1.1.1.1', 'plen': 24},
         {'ixp': tg_ports[1], 'ip': '2.2.2.4', 'gw': '2.2.2.1', 'plen': 24}]
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    # 2.Create an ingress qdisc on first port connected to Ixia port and add two rules with randomly generated selectors:
    # one with police action and one with log action
    out = await TcQdisc.add(
        input_data=[{dev_name: [
            {'dev': dut_ports[0], 'direction': 'ingress'}]}])
    err_msg = f'Verify no error on setting Qdist for {dut_ports[0]}.\n{out}'
    assert out[0][dev_name]['rc'] == 0, err_msg

    rule_selectors = {'action': {'trap': '',
                                 'police': {'rate': f'{policer_rate}kbit', 'burst': 6250,
                                            'conform-exceed': '', 'drop': ''}},
                      'skip_sw': True,
                      'want_mac': True,
                      'want_vlan': want_vlan,
                      'want_ip': want_ip,
                      'want_port': want_port,
                      'want_tcp': choice([True, False]) if want_port else False,
                      'want_vlan_ethtype': True if want_ip and want_vlan else False}

    tc_rule = tcutil_generate_rule_with_random_selectors(dut_ports[0], **rule_selectors)
    tc_rule_copy = deepcopy(tc_rule)
    randomize_rule_by_src_dst_field(tc_rule, rule_selectors)

    out = await TcFilter.add(input_data=[{dev_name: [tc_rule]}])
    assert out[0][dev_name]['rc'] == 0, f'Failed to create tc rule \n{out}'

    output_rule = await TcFilter.show(input_data=[{dev_name: [
        {'dev': dut_ports[0], 'direction': 'ingress', 'options': '-j'}]}], parse_output=True)
    assert output_rule[0][dev_name]['rc'] == 0, f'Failed to get tc rule \n{output_rule}'

    del tc_rule['filtertype']['skip_sw']
    tc_rule['action'] = {'xt': {'limit': '3/sec', '-j': 'LOG'}}

    out = await TcFilter.add(input_data=[{dev_name: [tc_rule]}])
    assert out[0][dev_name]['rc'] == 0, f'Failed to create tc rule \n{out}'

    # 3.Prepare a matching stream for the randomly selected selectors and transmit traffic
    streams = tcutil_tc_rules_to_tgen_streams({dut_ports[0]: output_rule[0][dev_name]['parsed_output']},
                                              frame_rate_pps=100, frame_rate_type='line_rate',
                                              frame_size=frame_size)
    # Overwrite stream dst/src fields after we randomized dst/src fields applying
    overwrite_src_dst_stream_fields(streams, tc_rule_copy, rule_selectors)
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(10)

    # 4.Verify CPU matched packets are logged into /var/log/messages
    exp_rate = floor((policer_rate * 125) / frame_size)

    rc, out = await dent_dev.run_cmd(f'tail -50 /var/log/messages | grep -Eo "IN={dut_ports[0]}" | wc -l')
    assert not rc, f'tail cmd failed with rc {rc} \n{out}'
    tail_res = int(out.strip())
    assert tail_res, f'CPU matched packets are not logged {tail_res}'

    # 5.Verify CPU trapped packet rate is as expected
    await verify_cpu_rate(dent_dev, exp_rate)
    await tgen_utils_stop_traffic(tgen_dev)


@pytest.mark.parametrize('rate_units', ['bit', 'kbit', 'gbit', 'bps', 'kbps', 'mbps', 'gbps', 'tbps'])
async def test_devlink_diff_rate_units(testbed, rate_units):
    """
    Test Name: test_devlink_diff_rate_units
    Test Suite: suite_functional_devlink
    Test Overview: Test devlink single block basic functionality with different rate units
    Test Procedure:
    1. Set link up on interfaces on all participant ports
    2. Create an ingress qdisc on first port connected to Ixia and add a rule with selectors
    3. Prepare a matching stream for the randomly selected selectors and transmit traffic
    4. Verify CPU trapped packet rate is as expected with different rate units
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dev_name = dent_devices[0].host_name
    dent_dev = dent_devices[0]
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]
    frame_size = randint(128, 500)
    # Calculate max possible rate for cpu trap 4000pps is max
    max_rate = (frame_size * CPU_MAX_PPS) * RATE_UNITS['bps']  # Max rate in bits per second
    policer_rate_bps = randint(2_000_000, max_rate)
    policer_rate = policer_rate_bps / RATE_UNITS[rate_units]
    want_ip = choice([True, False])
    want_port = choice([True, False]) if want_ip else False
    want_vlan = choice([True, False])

    # 1.Set link up on interfaces on all participant ports
    out = await IpLink.set(
        input_data=[{dev_name: [
            {'device': port, 'operstate': 'up'} for port in dut_ports]}])
    err_msg = f"Verify that ports set to 'UP' state.\n{out}"
    assert out[0][dev_name]['rc'] == 0, err_msg

    dev_groups = tgen_utils_dev_groups_from_config(
        [{'ixp': tg_ports[0], 'ip': '1.1.1.3', 'gw': '1.1.1.1', 'plen': 24},
         {'ixp': tg_ports[1], 'ip': '2.2.2.4', 'gw': '2.2.2.1', 'plen': 24}]
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    # 2.Create an ingress qdisc on first port connected to Ixia and add a rule with selectors
    out = await TcQdisc.add(
        input_data=[{dev_name: [
            {'dev': dut_ports[0], 'direction': 'ingress'}]}])
    err_msg = f'Verify no error on setting Qdist for {dut_ports[0]}.\n{out}'
    assert out[0][dev_name]['rc'] == 0, err_msg

    rule_selectors = {'action': {'trap': '',
                                 'police': {'rate': f'{policer_rate}{rate_units}',
                                            'burst': policer_rate + 1000,
                                            'conform-exceed': '', 'drop': ''}},
                      'skip_sw': True,
                      'want_mac': True,
                      'want_vlan': want_vlan,
                      'want_ip': want_ip,
                      'want_port': want_port,
                      'want_tcp': choice([True, False]) if want_port else False,
                      'want_vlan_ethtype': True if want_vlan and want_ip else False}

    tc_rule = tcutil_generate_rule_with_random_selectors(dut_ports[0], **rule_selectors)
    tc_rule_copy = deepcopy(tc_rule)
    randomize_rule_by_src_dst_field(tc_rule, rule_selectors)

    out = await TcFilter.add(input_data=[{dev_name: [tc_rule]}])
    assert out[0][dev_name]['rc'] == 0, f'Failed to create tc rule \n{out}'

    # 3.Prepare a matching stream for the randomly selected selectors and transmit traffic
    out = await TcFilter.show(input_data=[{dev_name: [
        {'dev': dut_ports[0], 'direction': 'ingress', 'options': '-j'}]}], parse_output=True)
    assert out[0][dev_name]['rc'] == 0, f'Failed to get tc rule \n{out}'

    streams = tcutil_tc_rules_to_tgen_streams({dut_ports[0]: out[0][dev_name]['parsed_output']},
                                              frame_rate_pps=100, frame_rate_type='line_rate',
                                              frame_size=frame_size)

    # Overwrite stream dst/src fields after we randomized dst/src fields applying
    overwrite_src_dst_stream_fields(streams, tc_rule_copy, rule_selectors)
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)
    await tgen_utils_start_traffic(tgen_dev)

    # 4.Verify CPU trapped packet rate is as expected with different rate units
    # Calculate expected pkt rate based on policer rate limitation
    exp_rate = policer_rate_bps / (frame_size * RATE_UNITS['bps'])
    await asyncio.sleep(10)
    await verify_cpu_rate(dent_dev, exp_rate)
    await tgen_utils_stop_traffic(tgen_dev)
