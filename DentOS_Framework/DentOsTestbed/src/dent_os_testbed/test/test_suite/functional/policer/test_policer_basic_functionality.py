import asyncio
import pytest
import random
from math import isclose

from dent_os_testbed.lib.tc.tc_filter import TcFilter
from dent_os_testbed.lib.tc.tc_qdisc import TcQdisc
from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
)

from dent_os_testbed.utils.test_utils.tc_flower_utils import (
    tcutil_generate_rule_with_random_selectors,
    tcutil_tc_rules_to_tgen_streams,
)

pytestmark = [
    pytest.mark.suite_functional_policer,
    pytest.mark.usefixtures('cleanup_qdiscs', 'cleanup_bridges', 'cleanup_tgen'),
    pytest.mark.asyncio,
]


@pytest.mark.parametrize('traffic_type', ['ipv4', 'l2', 'udp', 'tcp'])
@pytest.mark.parametrize('qdisc_type', ['port', 'shared_block'])
async def test_policer_basic_functionality(testbed, traffic_type, qdisc_type):
    """
    Test Name: Basic policer functionality
    Test Suite: suite_functional_policer
    Test Overview: Verify basic policer functionality
    Test Procedure:
    1. Create a bridge entity and set link up on it.
    2. Set link up on interfaces on all participant ports. Enslave all participant ports to the bridge.
    3. Create an ingress qdisc on first port connected to Tgen port/shared block and add a rule with random selectors
    4. Prepare a matching stream for the randomly selected selectors.
    5. Send traffic
    6. Verify RX rate on RX ports is as expected (rate is limited by the police pass rule).
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip(
            'The testbed does not have enough dent with tgen connections')
    device = dent_devices[0]
    dent = device.host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1][:2]
    ports_with_rule = ports[:1] if qdisc_type == 'port' else ports[1:]
    bridge = 'bridge0'
    block = random.randint(5, 3000)
    frame_rate = 300000  # bps
    tolerance = 0.12

    # 1. Create a bridge entity and set link up on it.
    out = await IpLink.add(input_data=[{dent: [{
        'dev': bridge,
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
    assert out[0][dent]['rc'] == 0, 'Failed setting link to state UP'

    # 3. Create an ingress qdisc on first port connected to Tgen port/shared block and add a rule with random selectors
    config = [{'dev': port, 'ingress_block': block, 'direction': 'ingress'} for port in ports_with_rule]
    if qdisc_type == 'port':
        for item in config:
            del item['ingress_block']

    out = await TcQdisc.add(input_data=[{dent: config}])
    assert out[0][dent]['rc'] == 0, 'Failed to add a qdisc'

    rule_config = {
        'action': {'police': {'rate': frame_rate, 'burst': frame_rate + 1000, 'conform-exceed': 'drop'}},
        'want_ip': traffic_type != 'l2',
        'want_port': traffic_type in ['tcp', 'udp'],
        'skip_sw': True,
        'want_vlan': traffic_type == 'l2',
        'want_tcp': traffic_type != 'udp',
        'want_mac': traffic_type == 'l2',
        'want_vlan_ethtype': False,
    }

    tc_rule = tcutil_generate_rule_with_random_selectors(ports_with_rule[0], **rule_config)

    # Update tc rule protocol based on traffic type
    if traffic_type == 'ipv4':  # forcibly select ipv4
        tc_rule['protocol'] = 'ipv4'

    if qdisc_type == 'port':
        out = await TcFilter.add(input_data=[{dent: [tc_rule]}])
        assert out[0][dent]['rc'] == 0, 'Failed to create tc rule'
    else:
        del tc_rule['dev']
        tc_rule['block'] = block
        out = await TcFilter.add(input_data=[{dent: [tc_rule]}])
        assert out[0][dent]['rc'] == 0, 'Failed to create tc rule'

    created_rules = {
        'dev': ports_with_rule[0],
        'direction': 'ingress',
        'options': '-j'}
    if qdisc_type == 'shared_block':
        del created_rules['dev']
        created_rules['block'] = block

    out = await TcFilter.show(input_data=[{dent: [created_rules]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get tc rule'

    # 4 Prepare a matching stream for the randomly selected selectors and with random generated size of packet.
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

    # 5. Send Traffic
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(15)

    # 6 Verify RX rate on RX ports is as expected (rate is limited by the police pass rule).
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Port Statistics')
    for row in stats.Rows:

        is_correct_rate = isclose(float(row['Rx. Rate (bps)']), frame_rate, rel_tol=tolerance)
        err_msg = f'Expected rate between {(frame_rate - (frame_rate * tolerance))} and ' \
                  f"{float(frame_rate + (frame_rate * tolerance))} got: { float(row['Rx. Rate (bps)'])}"
        if qdisc_type == 'port':
            if row['Port Name'] == tg_ports[0]:
                continue
            assert is_correct_rate, err_msg
        else:
            if row['Port Name'] == tg_ports[0]:
                assert is_correct_rate, err_msg

    await tgen_utils_stop_traffic(tgen_dev)
