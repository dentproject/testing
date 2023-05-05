import asyncio
import pytest
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

from dent_os_testbed.utils.test_utils.tc_flower_utils import (
    tcutil_generate_rule_with_random_selectors,
    tcutil_tc_rules_to_tgen_streams,
)

pytestmark = [
    pytest.mark.suite_functional_policer,
    pytest.mark.usefixtures('cleanup_bridges', 'cleanup_qdiscs', 'cleanup_tgen'),
    pytest.mark.asyncio,
]


async def test_policer_rate_per_rule(testbed):
    """
    Test Name: Policer rate per rule
    Test Suite: suite_functional_policer
    Test Overview: Verify rate per rule when stream are sent from the same port in parallel
    Test Procedure:
    1. Set link up on interfaces on all participant ports
    2. Create a bridge entity and set link up on it. Enslave all participant ports to the bridge.
    3. Create an ingress qdisc on first port
    4. Add multiple rules with randomly generated selectors
    5. Prepare a matching streams for the randomly selected selectors
    6. Transmit traffic
    7. Verify RX rate per stream is as expected (limited by the rule)
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip(
            'The testbed does not have enough dent with tgen connections')
    device = dent_devices[0]
    dent = device.host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]
    port_with_rule = ports[0]
    bridge = 'bridge0'
    rates = [250000, 400000, 600000]  # bps
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

    config = [{'dev': port_with_rule, 'direction': 'ingress'}]

    # 3. Create an ingress qdisc on first port
    out = await TcQdisc.add(input_data=[{dent: config}])
    assert out[0][dent]['rc'] == 0, 'Failed to create a qdisc'

    # 4.Add multiple rules with randomly generated selectors
    # 'pref' in ascending order for correct stream generation in tcutil_tc_rules_to_tgen_streams()
    configs = [
        {'action': {'police': {'rate': rates[0],
                               'burst': rates[0] + 1000,
                               'conform-exceed': 'drop'}},
         'want_ip': True,
         'pref': 100,
         'want_port': True,
         'want_proto': True,
         'want_mac': True,
         },
        {'action': {'police': {'rate': rates[1],
                               'burst': rates[1] + 1000,
                               'conform-exceed': 'drop'}},
         'want_ip': True,
         'pref': 200,
         'want_port': True,
         'want_proto': True,
         'want_mac': True,
         },
        {'action': {'police': {'rate': rates[2],
                               'burst': rates[2] + 1000,
                               'conform-exceed': 'drop'}},
         'want_ip': True,
         'pref': 300,
         'want_port': True,
         'want_proto': True,
         'want_mac': True,
         }]

    for config in configs:
        rule = tcutil_generate_rule_with_random_selectors(port_with_rule, **config)
        out = await TcFilter.add(input_data=[{dent: [rule]}])
        assert out[0][dent]['rc'] == 0, 'Failed to create tc rule'

    out = await TcFilter.show(input_data=[{dent: [{
        'dev': port_with_rule,
        'direction': 'ingress',
        'options': '-j'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get tc rule'

    # 5. Prepare a matching streams for the randomly selected selectors
    streams = tcutil_tc_rules_to_tgen_streams({port_with_rule: out[0][dent]['parsed_output']},
                                              frame_rate_type='line_rate', frame_rate_pps=100)

    dev_groups = tgen_utils_dev_groups_from_config((
        {'ixp': tg_ports[0], 'ip': '1.1.1.1', 'gw': '1.1.1.10', 'plen': 24},
        {'ixp': tg_ports[1], 'ip': '1.1.1.2', 'gw': '1.1.1.10', 'plen': 24},
        {'ixp': tg_ports[2], 'ip': '1.1.1.3', 'gw': '1.1.1.10', 'plen': 24},
        {'ixp': tg_ports[3], 'ip': '1.1.1.4', 'gw': '1.1.1.10', 'plen': 24}
    ))
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # 6. Transmit traffic
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(15)

    # 7. Verify RX rate per stream is as expected (limited by the rule)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Traffic Item Statistics')
    rate_stream_matching = zip(rates, streams.keys())
    for row, stream in zip(stats.Rows, rate_stream_matching):
        device.applog.info(f'Veryfing rate for the stream {stream[1]}')
        err_msg = f'Expected rate for stream {stream[1]} to be {stream[0]} got {row["Rx Rate (bps)"]} '
        assert isclose(float(row['Rx Rate (bps)']), stream[0], rel_tol=tolerance), err_msg
    await tgen_utils_stop_traffic(tgen_dev)
