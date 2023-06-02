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

pytestmark = [
    pytest.mark.suite_functional_policer,
    pytest.mark.usefixtures('cleanup_bridges', 'cleanup_qdiscs', 'cleanup_tgen'),
    pytest.mark.asyncio,
]


async def test_policer_interaction_span(testbed):
    """
    Test Name: Policer interaction with span
    Test Suite: suite_functional_policer
    Test Overview: Verify rate per port with policer and mirred port
    Test Procedure:
    1. Create a bridge entity and set link up on it.
    2. Set link up on interfaces on all participant ports. Enslave all participant ports to the bridge.
    3. Create an ingress qdisc on first port connected to Ixia port and add a rule with selectors and
        add also a mirred rule
    4. Prepare a matching stream for TX port and mirred port
    5. Transmit traffic from the TX port
    6. Verify RX rate on RX ports is as expected (by the police pass rule)
        and that in the mirred port equals sum of police rate and transmitted rate multiplied by number of RX ports
    7. Transmit traffic from mirred port
    8. Verify RX rate on RX ports is as expected (not affected by the police pass rule)
        and verify traffic also flows to the TX port
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
    mirred_port = ports[1]
    bridge = 'bridge0'
    police_rate = 50_000_000  # bitps
    transmit_rate = 100_000_000
    tolerance = 0.10
    match_all_pref = 200
    rule_pref = 300

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
    assert out[0][dent]['rc'] == 0, 'Failed setting link to state UP.'

    # 3. Create an ingress qdisc on first port connected to TGEN port and add a rule with selectors and
    # add also a mirred rule
    out = await TcQdisc.add(input_data=[{dent: [{'dev': port_with_rule, 'direction': 'ingress'}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create a qdisc'

    rc, out = await device.run_cmd(f'tc filter add dev {port_with_rule} ingress pref {match_all_pref} matchall skip_sw \
                                   action mirred egress mirror dev {mirred_port}')
    assert rc == 0, 'Failed to configure ingress matchall.'

    rule = {'dev': port_with_rule,
            'action': {'police': {'rate': police_rate, 'burst': police_rate + 100000, 'conform-exceed': 'drop'}},
            'direction': 'ingress',
            'protocol': 'ip',
            'skip_sw': True,
            'filtertype': {'src_mac': '02:05:0e:11:9c:a8',
                           'dst_mac': '02:dd:57:ee:81:88',
                           'src_ip': '106.38.228.165',
                           'dst_ip': '123.179.185.167'},
            'pref': rule_pref}

    out = await TcFilter.add(input_data=[{dent: [rule]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create tc rule'

    out = await TcFilter.show(input_data=[{dent: [{
        'dev': port_with_rule,
        'direction': 'ingress',
        'options': '-j'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get tc rule'

    # 4. Prepare a matching stream for TX port and mirred port

    dev_groups = tgen_utils_dev_groups_from_config((
        {'ixp': tg_ports[0], 'ip': '1.1.1.1', 'gw': '1.1.1.10', 'plen': 24},
        {'ixp': tg_ports[1], 'ip': '1.1.1.2', 'gw': '1.1.1.10', 'plen': 24},
        {'ixp': tg_ports[2], 'ip': '1.1.1.3', 'gw': '1.1.1.10', 'plen': 24},
        {'ixp': tg_ports[3], 'ip': '1.1.1.4', 'gw': '1.1.1.10', 'plen': 24}
    ))

    stream1 = {f'stream_{port_with_rule}': {'ip_source': dev_groups[tg_ports[0]][0]['name'],
                                            'ip_destination': [dev_groups[tg_ports[1]][0]['name'],
                                                               dev_groups[tg_ports[2]][0]['name'],
                                                               dev_groups[tg_ports[3]][0]['name']],
                                            'type': 'raw',
                                            'srcIp': '106.38.228.165',
                                            'dstIp': '123.179.185.167', 'rate': transmit_rate,
                                            'frameSize': 256,
                                            'frame_rate_type': 'bps_rate',
                                            'dstMac': '02:dd:57:ee:81:88',
                                            'srcMac': '02:05:0e:11:9c:a8',
                                            'protocol': 'ip'}}

    stream2 = {f'stream_{mirred_port}': {'ip_source': dev_groups[tg_ports[1]][0]['name'],
                                         'ip_destination': [dev_groups[tg_ports[0]][0]['name'],
                                                            dev_groups[tg_ports[2]][0]['name'],
                                                            dev_groups[tg_ports[3]][0]['name']],
                                         'type': 'raw',
                                         'srcIp': '106.38.228.165',
                                         'dstIp': '123.179.185.167',
                                         'rate': transmit_rate,
                                         'frameSize': 256,
                                         'frame_rate_type': 'bps_rate',
                                         'dstMac': '02:dd:57:ee:81:88',
                                         'srcMac': '02:05:0e:11:9c:a8',
                                         'protocol': 'ip'}
               }

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)
    await tgen_utils_setup_streams(tgen_dev, None, stream1)

    # 5. Transmit traffic from the TX port
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(15)

    # 6. Verify RX rate on RX ports is as expected (by the police pass rule)
    # and that in the mirred port equals sum of police rate and transmitted rate multiplied by number of RX ports
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Port Statistics')
    for row in stats.Rows:
        if row['Port Name'] == tg_ports[0]:
            assert isclose(float(row['Rx. Rate (bps)']), 0), f'Expected 0.0 got : {float(row["Rx. Rate (bps)"])}'
            continue
        if row['Port Name'] == tg_ports[1]:
            device.applog.info(f'Verifying rate for the mirred port {row["Port Name"]}')
            mirred_port_rate = transmit_rate * (len(dev_groups) - 1) + police_rate
            err_msg = f'Expected {mirred_port_rate} got : {float(row["Rx. Rate (bps)"])}'
            assert isclose(float(row['Rx. Rate (bps)']), mirred_port_rate, rel_tol=tolerance), err_msg
            continue
        device.applog.info(f'Verifying rate for the port {row["Port Name"]}')
        err_msg = f'Expected {police_rate} got : {float(row["Rx. Rate (bps)"])}'
        assert isclose(float(row['Rx. Rate (bps)']), police_rate, rel_tol=tolerance), err_msg

    await tgen_utils_stop_traffic(tgen_dev)
    # Add stream to mirred port
    await tgen_utils_setup_streams(tgen_dev, None, stream2)

    # 7. Transmit traffic from mirred port
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(15)

    # 8. Verify RX rate on RX ports is as expected (not affected by the police pass rule)
    # and verify traffic also flows to the TX port
    for row in stats.Rows:
        if row['Port Name'] == tg_ports[0]:
            err_msg = f'Expected {transmit_rate * 3} got : {float(row["Rx. Rate (bps)"])}'
            device.applog.info(f'Verifying rate for the port {row["Port Name"]}')
            assert isclose(float(row['Rx. Rate (bps)']), transmit_rate * 3, rel_tol=tolerance), err_msg
            continue
        device.applog.info(f'Verifying rate for the port {row["Port Name"]}')
        mirred_port_rate = transmit_rate * (len(dev_groups) - 1) + police_rate
        err_msg = f'Expected {mirred_port_rate} got : {float(row["Rx. Rate (bps)"])}'
        assert isclose(float(row['Rx. Rate (bps)']), mirred_port_rate, rel_tol=tolerance), err_msg
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        if row['Traffic Item'] == f'stream_{mirred_port}':
            device.applog.info(f'Verifying rate for the port {row["Rx Port"]} and stream stream_{mirred_port}')
            err_msg = f'Expected {transmit_rate} got : {float(row["Rx Rate (bps)"])}'
            assert isclose(float(row['Rx Rate (bps)']), transmit_rate, rel_tol=tolerance), err_msg
    await tgen_utils_stop_traffic(tgen_dev)
