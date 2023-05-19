import asyncio
import pytest
from random import choice, randint
from copy import deepcopy
from ipaddress import IPv4Network


from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.tc.tc_qdisc import TcQdisc
from dent_os_testbed.lib.tc.tc_filter import TcFilter
from dent_os_testbed.lib.ip.ip_address import IpAddress

from dent_os_testbed.test.test_suite.functional.devlink.devlink_utils import (
    verify_cpu_traps_rate_code_avg,
    verify_devlink_cpu_traps_rate_avg,
    randomize_rule_by_src_dst_field,
    overwrite_src_dst_stream_fields,
    get_sct_streams, SCT_MAP, DEVIATION,
    verify_cpu_rate)

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_clear_traffic_items,
)

from dent_os_testbed.utils.test_utils.tc_flower_utils import tcutil_generate_rule_with_random_selectors

pytestmark = [
    pytest.mark.suite_functional_devlink,
    pytest.mark.usefixtures('define_bash_utils', 'cleanup_qdiscs', 'cleanup_ip_addrs'),
    pytest.mark.asyncio,
]


@pytest.mark.parametrize('ports_num', [1, 2, 4])
async def test_devlink_sct_basic_ports(testbed, ports_num):
    """
    Test Name: test_devlink_sct_basic
    Test Suite: suite_functional_devlink
    Test Overview: Test devlink SCT supported traps with 1/2/4 ports
    Test Procedure:
    1. Set link up on interfaces on all participant ports
    2. Configure ip address on portd and connect devices
    3. Generate random trap rule
    4. Prepare traffic matching all SCT supported traps and transmit
    5. For each stream, verify CPU rate is as expected
    6. Add rule created earlier to trap user defined traffic
    7. Verify CPU rate for user defined trap
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dev_name = dent_devices[0].host_name
    dent_dev = dent_devices[0]
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]
    frame_size = randint(128, 1400)
    want_ip = choice([True, False])
    want_port = choice([True, False]) if want_ip else False
    want_vlan = choice([True, False])
    ip_network = IPv4Network('192.168.1.0/24')

    # 1.Set link up on interfaces on all participant ports
    out = await IpLink.set(
        input_data=[{dev_name: [
            {'device': port, 'operstate': 'up'} for port in dut_ports]}])
    err_msg = f"Verify that ports set to 'UP' state.\n{out}"
    assert not out[0][dev_name]['rc'], err_msg

    # 2.Configure ip address on ports and connect devices
    addr_map = []
    for port_indx in range(ports_num):
        ip_addr = ip_network[4]

        out = await IpAddress.add(input_data=[{dev_name: [
            {'dev': dut_ports[port_indx], 'prefix': f'{ip_addr}/{ip_network.prefixlen}', 'broadcast': str(ip_network.broadcast_address)}]}])
        assert not out[0][dev_name]['rc'], f'Failed to add IP addr to port {dut_ports[port_indx]}'
        if ports_num == 1:
            addr_map.append({'ixp': tg_ports[port_indx], 'ip': str(ip_addr + 1), 'gw': str(ip_addr), 'plen': ip_network.prefixlen})
            addr_map.append({'ixp': tg_ports[port_indx + 1], 'ip': '2.2.2.5', 'gw': '2.2.2.1', 'plen': 24})
        else:
            addr_map.append({'ixp': tg_ports[port_indx], 'ip': str(ip_addr + 1), 'gw': str(ip_addr), 'plen': ip_network.prefixlen})
        ip_network = IPv4Network(f'{ip_network[0] + 256}/{ip_network.prefixlen}')

    dev_groups = tgen_utils_dev_groups_from_config(addr_map)
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    # 3.Generate random trap rule
    rule_selectors = {'action': 'trap',
                      'skip_sw': True,
                      'want_mac': True,
                      'want_vlan': want_vlan,
                      'want_ip': want_ip,
                      'want_port': want_port,
                      'want_tcp': choice([True, False]) if want_port else False,
                      'want_vlan_ethtype': want_ip and want_vlan}

    tc_rules = {}
    for port_indx in range(ports_num):
        tc_rule = tcutil_generate_rule_with_random_selectors(dut_ports[port_indx], **rule_selectors)
        original_rule = deepcopy(tc_rule)
        randomize_rule_by_src_dst_field(tc_rule, rule_selectors)
        tc_rules[dut_ports[port_indx]] = {'tc_rule': tc_rule, 'original_rule': original_rule}

    # 4.Prepare traffic matching all SCT supported traps and transmit
    streams = {}
    for port_indx in range(ports_num):
        src_dst_ports = [tg_ports[port_indx], tg_ports[port_indx ^ 1]]
        stream = await get_sct_streams(dent_dev, dev_groups, src_dst_ports, dut_ports[port_indx])
        streams.update(stream)
        custome_stream = {f'custome_stream_{dut_ports[port_indx]}': {
            'type': 'raw',
            'protocol': '802.1Q' if want_vlan else tc_rule['protocol'],
            'ip_source': dev_groups[src_dst_ports[0]][0]['name'],
            'ip_destination': dev_groups[src_dst_ports[1]][0]['name'],
            'srcMac': tc_rules[dut_ports[port_indx]]['original_rule']['filtertype']['src_mac'],
            'dstMac': tc_rules[dut_ports[port_indx]]['original_rule']['filtertype']['dst_mac'],
            'frameSize': frame_size,
            'rate': SCT_MAP['acl_code_3']['exp'] + 2000}
        }
        overwrite_src_dst_stream_fields(custome_stream, tc_rules[dut_ports[port_indx]]['original_rule'], rule_selectors)
        streams.update(custome_stream)
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(20 if ports_num == 4 else 10)

    # 5.For each stream, verify CPU rate is as expected
    coroutines_cpu_stat = []
    coroutines_devlink = []
    for trap_name, sct in SCT_MAP.items():
        if trap_name == 'acl_code_3':
            continue
        # Due to absence of ability to suspend streams, increase devitation for sct traffic with expected rate around <=200
        # in case when we send traffic from 4 ports at once
        deviation = 0.25 if sct['exp'] <= 200 and ports_num == 4 else DEVIATION
        coroutines_cpu_stat.append(verify_cpu_traps_rate_code_avg(dent_dev, sct['cpu_code'], sct['exp'], deviation=deviation, logs=True))
        coroutines_devlink.append(verify_devlink_cpu_traps_rate_avg(dent_dev, trap_name, sct['exp'], deviation=deviation, logs=True))
    # Asyncio may fail even with 15 tasks executed in parallel, separate coroutines into chunks of 7-8 tasks
    tasks_slice = len(coroutines_cpu_stat) // 2
    await asyncio.gather(*coroutines_cpu_stat[:tasks_slice])
    await asyncio.gather(*coroutines_cpu_stat[tasks_slice:])
    await asyncio.gather(*coroutines_devlink[:tasks_slice])
    await asyncio.gather(*coroutines_devlink[tasks_slice:])

    # 6.Add rule created earlier to trap user defined traffic
    for port_indx in range(ports_num):
        out = await TcQdisc.add(
            input_data=[{dev_name: [
                {'dev': dut_ports[port_indx], 'direction': 'ingress'}]}])
        err_msg = f'Verify no error on setting Qdist for {dut_ports[port_indx]}.\n{out}'
        assert not out[0][dev_name]['rc'], err_msg

        out = await TcFilter.add(input_data=[{dev_name: [tc_rules[dut_ports[port_indx]]['tc_rule']]}])
        assert not out[0][dev_name]['rc'], f'Failed to create tc rule \n{out}'

    # 7. Verify CPU rate for user defined trap
    await verify_cpu_rate(dent_dev, SCT_MAP['acl_code_3']['exp'])
    await tgen_utils_stop_traffic(tgen_dev)


@pytest.mark.usefixtures('disable_sct')
async def test_devlink_static_trap_disable(testbed):
    """
    Test Name: test_devlink_static_trap_disable
    Test Suite: suite_functional_devlink
    Test Overview: Test devlink with disabled Sct
    Test Procedure:
    1. Disable default Sct configuration and set link up on interfaces on all participant ports
    2. Configure ip address on port and connect devices
    3. Generate random trap rule
    4. Prepare traffic matching all SCT supported traps
    5. Transmit each traffic type and verify CPU rate is 65 000
    6. Add rule created earlier to trap user defined traffic
    7. Verify CPU rate for user defined trap is 65 000
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dev_name = dent_devices[0].host_name
    dent_dev = dent_devices[0]
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]
    frame_size = randint(128, 1400)
    want_ip = choice([True, False])
    want_port = choice([True, False]) if want_ip else False
    want_vlan = choice([True, False])
    ip_network = IPv4Network('192.168.1.0/24')
    ip_addr = ip_network[4]
    exp_rate = 65_000

    # 1.Disable default Sct configuration and set link up on interfaces on all participant ports
    out = await IpLink.set(
        input_data=[{dev_name: [
            {'device': port, 'operstate': 'up'} for port in dut_ports]}])
    err_msg = f"Verify that ports set to 'UP' state.\n{out}"
    assert not out[0][dev_name]['rc'], err_msg

    # 2.Configure ip address on port and connect devices
    out = await IpAddress.add(input_data=[{dev_name: [
        {'dev': dut_ports[0], 'prefix': f'{ip_addr}/{ip_network.prefixlen}', 'broadcast': str(ip_network.broadcast_address)}]}])
    assert not out[0][dev_name]['rc'], f'Failed to add IP addr to port {dut_ports[0]}'

    dev_groups = tgen_utils_dev_groups_from_config(
        [{'ixp': tg_ports[0], 'ip': str(ip_addr + 1), 'gw': str(ip_addr), 'plen': ip_network.prefixlen},
         {'ixp': tg_ports[1], 'ip': '2.2.2.5', 'gw': '2.2.2.1', 'plen': 24}])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    # 3.Generate random trap rule
    rule_selectors = {'action': 'trap',
                      'skip_sw': True,
                      'want_mac': True,
                      'want_vlan': want_vlan,
                      'want_ip': want_ip,
                      'want_port': want_port,
                      'want_tcp': choice([True, False]) if want_port else False,
                      'want_vlan_ethtype': want_ip and want_vlan}

    tc_rule = tcutil_generate_rule_with_random_selectors(dut_ports[0], **rule_selectors)
    original_rule = deepcopy(tc_rule)
    randomize_rule_by_src_dst_field(tc_rule, rule_selectors)

    # 4.Prepare traffic matching all SCT supported traps
    streams = {}
    stream = await get_sct_streams(dent_dev, dev_groups, tg_ports[:2], dut_ports[0], rate=exp_rate + 10_000)
    streams.update(stream)
    custome_stream = {f'custome_stream_{dut_ports[0]}': {
                    'type': 'raw',
                    'protocol': '802.1Q' if want_vlan else tc_rule['protocol'],
                    'ip_source': dev_groups[tg_ports[0]][0]['name'],
                    'ip_destination': dev_groups[tg_ports[1]][0]['name'],
                    'srcMac': original_rule['filtertype']['src_mac'],
                    'dstMac': original_rule['filtertype']['dst_mac'],
                    'frameSize': frame_size,
                    'rate': exp_rate + 10_000}
                     }
    overwrite_src_dst_stream_fields(custome_stream, original_rule, rule_selectors)
    streams.update(custome_stream)

    # 5.Transmit each traffic type and verify CPU rate is 65 000
    for trap_name, sct in SCT_MAP.items():
        if trap_name == 'acl_code_3':
            continue
        stream_name = f'{trap_name}_{dut_ports[0]}'
        single_stream = {stream_name: streams[stream_name]}
        await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=single_stream)
        await tgen_utils_start_traffic(tgen_dev)
        await asyncio.sleep(10)
        await asyncio.gather(verify_cpu_traps_rate_code_avg(dent_dev, sct['cpu_code'], exp_rate, logs=True),
                             verify_devlink_cpu_traps_rate_avg(dent_dev, trap_name, exp_rate, logs=True))
        await tgen_utils_stop_traffic(tgen_dev)
        await asyncio.sleep(6)
        await tgen_utils_clear_traffic_items(tgen_dev, traffic_names=[stream_name])

    # 6.Add rule created earlier to trap user defined traffic
    out = await TcQdisc.add(
        input_data=[{dev_name: [
            {'dev': dut_ports[0], 'direction': 'ingress'}]}])
    err_msg = f'Verify no error on setting Qdist for {dut_ports[0]}.\n{out}'
    assert not out[0][dev_name]['rc'], err_msg

    out = await TcFilter.add(input_data=[{dev_name: [tc_rule]}])
    assert not out[0][dev_name]['rc'], f'Failed to create tc rule \n{out}'

    # 7.Verify CPU rate for user defined trap is 65 000
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=custome_stream)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(10)
    await verify_cpu_rate(dent_dev, exp_rate)
    await tgen_utils_stop_traffic(tgen_dev)
