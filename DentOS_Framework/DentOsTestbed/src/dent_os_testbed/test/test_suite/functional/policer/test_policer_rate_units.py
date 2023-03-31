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
    pytest.mark.usefixtures('cleanup_bridges', 'cleanup_qdiscs', 'cleanup_tgen'),
    pytest.mark.asyncio,
]


@pytest.mark.parametrize('unit_type', ['IEC', 'SI'])
async def test_policer_rate_config(testbed, unit_type):
    """
    Test Name: Policer rate config functionality
    Test Suite: suite_functional_policer
    Test Overview: Verify different units for the same rate and burst function the same (same RX rate)
    Test Procedure:
    1. Create a bridge entity and set link up on it.
    2. Set link up on interfaces on all participant ports. Enslave all participant ports to the bridge.
    3. Create an ingress qdisc on first port connected to Ixia port and add a rule with random selectors
    4. Prepare a matching stream for the randomly selected selectors and with random generated size of packet.
    5. Send traffic
    6. Verify RX rate on RX ports is as expected (rate is limited by the police pass rule).
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip(
            'The testbed does not have enough dent with tgen connections')
    device = dent_devices[0]
    dent = device.host_name
    tg_ports = tgen_dev.links_dict[dent][0][:2]
    ports = tgen_dev.links_dict[dent][1][:2]
    port_with_rule = ports[0]
    bridge = 'bridge0'
    frame_rate = 250000
    tolerance = 0.1

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

    # 3. Create an ingress qdisc on first port connected to Ixia port and add a rule with random selectors
    out = await TcQdisc.add(input_data=[{dent: [{
        'dev': ports[0],
        'direction': 'ingress'}]}])
    assert out[0][dent]['rc'] == 0, f'Failed creating qdisc on port: {ports[0]}.'

    rule_config = {
        'action': {'police': {'rate': frame_rate, 'burst': frame_rate + 1000, 'conform-exceed': 'drop'}},
        'want_ip': True,
        'want_port': True,
        'skip_sw': True,
        'want_proto': True,
        'want_mac': True,
        'want_tcp': True,
    }

    tc_rule = tcutil_generate_rule_with_random_selectors(
        port_with_rule, **rule_config)

    out = await TcFilter.add(input_data=[{dent: [tc_rule]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create tc rule'

    out = await TcFilter.show(input_data=[{dent: [{
        'dev': port_with_rule,
        'direction': 'ingress',
        'options': '-j'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get tc rule'

    # 4 Prepare a matching stream for the randomly selected selectors and with random generated size of packet.
    streams = tcutil_tc_rules_to_tgen_streams({port_with_rule: out[0][dent]['parsed_output']},
                                              frame_rate_pps=frame_rate,
                                              frame_rate_type='line_rate')

    dev_groups = tgen_utils_dev_groups_from_config((
        {'ixp': tg_ports[0], 'ip': '1.1.1.1', 'gw': '1.1.1.10', 'plen': 24},
        {'ixp': tg_ports[1], 'ip': '1.1.1.2', 'gw': '1.1.1.10', 'plen': 24}
    ))
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # 5. Send Traffic
    await tgen_utils_start_traffic(tgen_dev)

    unit_multiplier_map = {
        'SI': {
            'gbit': 1e-9,
            'bps': 0.125,
            'kbps': 1.25e-4,
            'mbps': 1.25E-7,
            'gbps': 1.25e-10,
            'tbps': 1.25e-13
        },
        'IEC': {
            'gibit': 9.3132257461548E-10,
            'kibps': 1.220703125E-4,
            'mibps': 1.1920928955078E-7,
            'gibps': 1.1641532182694E-10,
            'tibps': 1.1368683772162E-13
        },
    }

    for unit, mul in unit_multiplier_map[unit_type].items():
        out = await TcFilter.delete(input_data=[{dent: [{
            'dev': port_with_rule,
            'direction': 'ingress'}]}])
        assert out[0][dent]['rc'] == 0, 'Failed to delete tc rule'

        tc_rule['action']['police']['rate'] = f'{frame_rate * mul}{unit}'
        tc_rule['action']['police']['burst'] = frame_rate + 1000

        # Add rule with new unit same rate
        out = await TcFilter.add(input_data=[{dent: [tc_rule]}])
        assert out[0][dent]['rc'] == 0, 'Failed to create tc rule'
        await asyncio.sleep(20)

        # 6 Verify RX rate on RX ports is as expected (rate is limited by the police pass rule).
        stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Port Statistics')
        for row in stats.Rows:
            if row['Port Name'] == tg_ports[0]:
                continue
            deviation = frame_rate * tolerance
            actual_rate = float(row['Rx. Rate (bps)'])
            err_msg = f'Expected {actual_rate} got : {frame_rate + deviation} and {frame_rate - deviation}' \
                      f' with unit {unit} and and mul {mul}'
            assert isclose(float(row['Rx. Rate (bps)']), frame_rate, rel_tol=tolerance), err_msg

    await tgen_utils_stop_traffic(tgen_dev)
