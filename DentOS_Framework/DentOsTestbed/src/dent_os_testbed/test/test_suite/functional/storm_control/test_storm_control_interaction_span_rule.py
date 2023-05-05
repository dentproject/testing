import math
import pytest
import asyncio

from dent_os_testbed.test.test_suite.functional.storm_control.storm_control_utils import devlink_rate_value
from dent_os_testbed.utils.test_utils.cleanup_utils import cleanup_kbyte_per_sec_rate_value
from dent_os_testbed.lib.tc.tc_qdisc import TcQdisc
from dent_os_testbed.lib.ip.ip_link import IpLink
from random import randrange

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic
)

pytestmark = [
    pytest.mark.suite_functional_storm_control,
    pytest.mark.asyncio,
    pytest.mark.usefixtures('cleanup_bridges', 'cleanup_tgen', 'cleanup_qdiscs')
]


async def set_rates(kbyte_value_stream, ports, device_host_name):
    params = [
        {'port': ports[0], 'name': 'unk_uc_kbyte_per_sec_rate', 'value': kbyte_value_stream[0]},
        {'port': ports[0], 'name': 'unreg_mc_kbyte_per_sec_rate', 'value': kbyte_value_stream[1]},
        {'port': ports[0], 'name': 'bc_kbyte_per_sec_rate', 'value': kbyte_value_stream[2]}
    ]
    for value in params:
        await devlink_rate_value(dev=f'pci/0000:01:00.0/{value["port"].replace("swp","")}',
                                 name=value['name'], value=value['value'],
                                 cmode='runtime', device_host_name=device_host_name, set=True, verify=True)


async def test_storm_control_interaction_span_rule(testbed):
    """
    Test Name: test_storm_control_interaction_span_rule
    Test Suite: suite_functional_storm_control
    Test Overview: Verify rate is not limited by Storm Control due to the mirred rule.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set bridge br0 admin state UP.
    3.  Set ports swp1, swp2, swp3, swp4 master br0.
    4.  Set entities swp1, swp2, swp3, swp4 UP state.
    5.  Set storm control rate limit rule for all streams.
    6.  Define a SPAN rule with a source port.
    7.  Set up the following streams:
        - broadcast with random generated size of packet;
        - multicast with random generated size of packet;
        - unknown unicast with random generated size of packet.
    8.  Transmit continues traffic by TG.
    9.  Verify the RX rate on the RX port is as expected - the rate is limited according to storm control limits.
        Echamine the impact of the SPAN rule.
    10. Disable storm control rate limit rule for all streams.
    12. Verify the RX rate on the RX port is as expected - the rate is not limited by storm control.
    """

    bridge = 'br0'
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    size_packets = randrange(500, 1000)
    traffic_duration = 15
    deviation = 0.10
    kbyte_value_stream = [randrange(start, end+1) for start, end in [(1500, 1700), (3800, 4000), (5100, 5300)]]

    out = await IpLink.add(
        input_data=[{device_host_name: [
            {'device': bridge, 'vlan_filtering': 1, 'type': 'bridge'}]}])
    err_msg = f"Verify that bridge created and vlan filtering set to 'ON'.\n{out}"
    assert out[0][device_host_name]['rc'] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': bridge, 'operstate': 'up'}]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that bridge set to 'UP' state.\n{out}"

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': port, 'master': bridge, 'operstate': 'up'} for port in ports]}])
    err_msg = f"Verify that bridge entities set to 'UP' state and links enslaved to bridge.\n{out}"
    assert out[0][device_host_name]['rc'] == 0, err_msg

    # set a storm control rate limits
    await set_rates(kbyte_value_stream, ports, device_host_name)

    try:
        out = await TcQdisc.add(
            input_data=[{device_host_name: [
                {'dev': ports[0], 'kind': 'ingress'}]}])
        assert out[0][device_host_name]['rc'] == 0, f'Failed to configure ingress qdisc.\n{out}'

        rc, out = await dent_dev.run_cmd(f'tc filter add dev {ports[0]} ingress matchall skip_sw action mirred \
            egress mirror dev {ports[1]}')
        assert rc == 0, 'Failed to configure ingress matchall.'

        address_map = (
            # swp port, tg port,    tg ip,     gw,        plen
            (ports[0], tg_ports[0], '1.1.1.2', '1.1.1.1', 24),
            (ports[1], tg_ports[1], '1.1.1.3', '1.1.1.1', 24),
            (ports[2], tg_ports[2], '1.1.1.4', '1.1.1.1', 24),
            (ports[3], tg_ports[3], '1.1.1.5', '1.1.1.1', 24)
        )

        dev_groups = tgen_utils_dev_groups_from_config(
            {'ixp': port, 'ip': ip, 'gw': gw, 'plen': plen}
            for _, port, ip, gw, plen in address_map
        )

        await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

        """
        Set up the following streams:
        — stream_1 —  |  — stream_2 —  |  — stream_3 —  |
        swp1 -> swp2  |  swp1 -> swp3  |  swp1 -> swp4  |
        """

        streams = {
            'stream_1': {
                'ip_source': dev_groups[tg_ports[0]][0]['name'],
                'ip_destination': dev_groups[tg_ports[1]][0]['name'],
                'srcMac': '10:62:5a:cf:ab:39',
                'dstMac': '34:1e:60:35:58:ac',
                'frameSize': size_packets,
                'frame_rate_type': 'line_rate',
                'rate': 33,
                'protocol': '0x0800',
                'type': 'raw'
            },
            'stream_2': {
                'ip_source': dev_groups[tg_ports[0]][0]['name'],
                'ip_destination': dev_groups[tg_ports[2]][0]['name'],
                'srcMac': '98:92:be:4c:c8:53',
                'dstMac': '01:00:5E:51:14:af',
                'frameSize': size_packets,
                'frame_rate_type': 'line_rate',
                'rate': 33,
                'protocol': '0x0800',
                'type': 'raw'
            },
            'stream_3': {
                'ip_source': dev_groups[tg_ports[0]][0]['name'],
                'ip_destination': dev_groups[tg_ports[3]][0]['name'],
                'srcMac': '54:84:c3:74:89:37',
                'dstMac': 'ff:ff:ff:ff:ff:ff',
                'frameSize': size_packets,
                'frame_rate_type': 'line_rate',
                'rate': 33,
                'protocol': '0x0800',
                'type': 'raw'
            }
        }

        await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)
        await tgen_utils_start_traffic(tgen_dev)
        await asyncio.sleep(traffic_duration)

        # check the traffic stats
        stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Traffic Item Statistics')
        collected = {row['Traffic Item']:
                     {'tx_rate': row['Tx Rate (Bps)'], 'rx_rate': row['Rx Rate (Bps)']} for row in stats.Rows}
        assert math.isclose(float(collected['stream_1']['tx_rate']),
                            float(collected['stream_1']['rx_rate']), rel_tol=deviation), \
            'Failed: the rate is limited by storm control due to mirred rule.'
        for x in range(2):
            assert math.isclose(kbyte_value_stream[x+1]*1000,
                                float(collected[f'stream_{x+2}']['rx_rate']), rel_tol=deviation), \
                'Failed: the rate is not limited by storm control.'

        # disable storm control for all streams
        await cleanup_kbyte_per_sec_rate_value(dent_dev, tgen_dev, all_values=True)
        await asyncio.sleep(traffic_duration)

        # verify the rate is not limited
        stream_names = [key for key in streams]
        stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Traffic Item Statistics')
        collected = {row['Traffic Item']:
                     {'tx_rate': row['Tx Rate (Bps)'], 'rx_rate': row['Rx Rate (Bps)']} for row in stats.Rows}
        for stream in stream_names:
            if stream in collected:
                rates = collected[stream]
                tx_rate = float(rates['tx_rate'])
                rx_rate = float(rates['rx_rate'])
                err_msg = 'Failed: the rate is limited by storm control.'
                assert math.isclose(tx_rate, rx_rate, rel_tol=deviation), err_msg
    finally:
        await tgen_utils_stop_traffic(tgen_dev)
        await cleanup_kbyte_per_sec_rate_value(dent_dev, tgen_dev, all_values=True)
