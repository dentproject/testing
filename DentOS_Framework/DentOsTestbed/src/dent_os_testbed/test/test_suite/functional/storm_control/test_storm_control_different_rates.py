import math
import pytest
import asyncio

from dent_os_testbed.test.test_suite.functional.storm_control.storm_control_utils import devlink_rate_value
from dent_os_testbed.utils.test_utils.cleanup_utils import cleanup_kbyte_per_sec_rate_value
from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan
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
    pytest.mark.usefixtures('cleanup_bridges', 'cleanup_tgen')
]


async def set_rates(kbyte_value_stream, ports, device_host_name):
    params = [
        {'port': ports[0], 'name': 'bc_kbyte_per_sec_rate', 'value': kbyte_value_stream[0]},
        {'port': ports[0], 'name': 'unreg_mc_kbyte_per_sec_rate', 'value': kbyte_value_stream[1]},
        {'port': ports[0], 'name': 'unk_uc_kbyte_per_sec_rate', 'value': kbyte_value_stream[2]},
        {'port': ports[1], 'name': 'bc_kbyte_per_sec_rate', 'value': kbyte_value_stream[3]},
        {'port': ports[2], 'name': 'unreg_mc_kbyte_per_sec_rate', 'value': kbyte_value_stream[4]},
        {'port': ports[3], 'name': 'unk_uc_kbyte_per_sec_rate', 'value': kbyte_value_stream[5]}
    ]
    for value in params:
        await devlink_rate_value(dev=f'pci/0000:01:00.0/{value["port"].replace("swp","")}',
                                 name=value['name'], value=value['value'],
                                 cmode='runtime', device_host_name=device_host_name, set=True, verify=True)


async def verify_rates(kbyte_value_stream, tgen_dev, correlation, deviation):
    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Traffic Item Statistics')
    collected = {row['Traffic Item']:
                 {'tx_rate': row['Tx Rate (Bps)'], 'rx_rate': row['Rx Rate (Bps)']} for row in stats.Rows}
    rate_value = {
        'stream_1_swp1->swp2': kbyte_value_stream[0],
        'stream_2_swp1->swp2': kbyte_value_stream[1],
        'stream_3_swp1->swp2': kbyte_value_stream[2],
        'stream_4_swp2->swp1': kbyte_value_stream[3],
        'stream_5_swp3->swp4': kbyte_value_stream[4],
        'stream_6_swp4->swp3': kbyte_value_stream[5]
    }
    for stream, value in rate_value.items():
        assert math.isclose(value*correlation*1000, float(collected[stream]['rx_rate']), rel_tol=deviation), \
            f'Failed: the rate is not limited by storm control for {rate_value}.'


async def test_storm_control_different_rates(testbed):
    """
    Test Name: test_storm_control_different_rates
    Test Suite: suite_functional_storm_control
    Test Overview: Verify rate is limited according to the changes in Storm Control Rules.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Set entities swp1, swp2, swp3, swp4 UP state.
    2.  Init vlan aware bridge entity br0.
    3.  Set bridge br0 admin state UP.
    4.  Set ports swp1, swp2, swp3, swp4 master br0.
    5.  Add swp1 and swp2 to the same vlan. Add swp3 and swp4 to another vlan.
    6.  Set up the following streams:
        Ixia port 1: broadcast, multicast and unknown unicast streams, with random generated size of packet;
        Ixia port 2: broadcast stream, with random generated size of packet;
        Ixia port 3: multicast stream, with random generated size of packet;
        Ixia port 4: unknown unicast stream, with random generated size of packet.
    7.  Set a storm control rate limit for all types of traffic on all ports.
    8.  Transmit continues traffic by TG.
    9.  Verify the RX rate on the RX port is as expected - the rate is limited by storm control.
    10. Change storm control rates for all ports.
    11. Verify the RX rate on the RX port is as expected - the rate is limited by storm control.
    12. Change storm control rates for all ports again.
    13. Verify the RX rate on the RX port is as expected - the rate is limited by storm control.
    14. Disable storm control for all ports.
    15. Verify the RX rate on the RX port is as expected - the rate is not limited by storm control.
    """

    bridge = 'br0'
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 15
    correlation = 0.33
    deviation = 0.10
    kbyte_value_stream = [randrange(start, end+1) for start, end in [(1500, 1700), (2800, 3000), (3800, 4000),
                          (4500, 4700), (1000, 1200), (5100, 5300)]]

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': port, 'operstate': 'up'} for port in ports]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that entities set to 'UP' state.\n{out}"

    out = await IpLink.add(
        input_data=[{device_host_name: [
            {'device': bridge, 'vlan_filtering': 1, 'vlan_default_pvid': 0, 'type': 'bridge'}]}])
    err_msg = f"Verify that bridge created, vlan filtering set to 'ON' and vlan_default_pvid set to '0'.\n{out}"
    assert out[0][device_host_name]['rc'] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': bridge, 'operstate': 'up'}]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that bridge set to 'UP' state.\n{out}"

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': port, 'master': bridge} for port in ports]}])
    err_msg = f'Verify that bridge entities enslaved to bridge.\n{out}'
    assert out[0][device_host_name]['rc'] == 0, err_msg

    out = await BridgeVlan.add(
        input_data=[{device_host_name: [
            {'device': ports[x], 'vid': f'{1 if x<2 else 2}', 'untagged': True, 'pvid': True}
            for x in range(4)]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that entities added to vid '1' and '2'.\n{out}"

    # set a storm control rate limits
    await set_rates(kbyte_value_stream, ports, device_host_name)

    try:
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
        — stream_1 —  |  — stream_2 —   |  — stream_3 —  |  — stream_4 —  |  — stream_5 —  |  — stream_6 —
        swp1 -> swp4  |  swp1 -> swp4   |  swp1 -> swp4  |  swp2 -> swp4  |  swp3 -> swp4  |  swp4 -> swp3

        — stream_1 —  |  — stream_2 —   |  — stream_3 —  |  — stream_4 —  |  — stream_5 —  |  — stream_6 —
        swp1 -> swp3  |  swp1 -> swp3   |  swp1 -> swp3  |  swp2 -> swp3  |  swp3 -> swp2  |  swp4 -> swp2

        — stream_1 —  |  — stream_2 —   |  — stream_3 —  |  — stream_4 —  |  — stream_5 —  |  — stream_6 —
        swp1 -> swp2  |  swp1 -> swp2   |  swp1 -> swp2  |  swp2 -> swp1  |  swp3 -> swp1  |  swp4 -> swp1
        """

        streams = {
            f'stream_1_swp1->swp{4-x}': {
                'ip_source': dev_groups[tg_ports[0]][0]['name'],
                'ip_destination': dev_groups[tg_ports[3-x]][0]['name'],
                'srcMac': f'16:ea:c3:{x+5}d:1e:ec',
                'dstMac': 'ff:ff:ff:ff:ff:ff',
                'frameSize': randrange(100, 1500),
                'frame_rate_type': 'line_rate',
                'rate': 5,
                'protocol': '0x0800',
                'type': 'raw'
            } for x in range(3)
        }
        streams.update({
            f'stream_2_swp1->swp{4-x}': {
                'ip_source': dev_groups[tg_ports[0]][0]['name'],
                'ip_destination': dev_groups[tg_ports[3-x]][0]['name'],
                'srcIp': f'3.6.92.20{x+1}',
                'dstIp': f'228.68.176.2{x+11}',
                'srcMac': f'36:11:3d:38:9a:{x+5}e',
                'dstMac': f'01:00:5E:4{x+4}:b0:d3',
                'frameSize': randrange(100, 1500),
                'frame_rate_type': 'line_rate',
                'rate': 5,
                'protocol': '0x0800',
                'type': 'raw'
            } for x in range(3)
        })
        streams.update({
            f'stream_3_swp1->swp{4-x}': {
                'ip_source': dev_groups[tg_ports[0]][0]['name'],
                'ip_destination': dev_groups[tg_ports[3-x]][0]['name'],
                'srcMac': f'72:88:c5:ec:f5:0{x+5}',
                'dstMac': f'92:ff:e{x+6}:07:88:a2',
                'frameSize': randrange(100, 1500),
                'frame_rate_type': 'line_rate',
                'rate': 5,
                'protocol': '0x0800',
                'type': 'raw'
            } for x in range(3)
        })
        streams.update({
            f'stream_4_swp2->swp{4-x if x < 2 else 1}': {
                'ip_source': dev_groups[tg_ports[1]][0]['name'],
                'ip_destination': dev_groups[tg_ports[3-x if x < 2 else 0]][0]['name'],
                'srcMac': f'84:fc:70:36:2a:7{x+3}',
                'dstMac': 'ff:ff:ff:ff:ff:ff',
                'frameSize': randrange(100, 1500),
                'frame_rate_type': 'line_rate',
                'rate': 5,
                'protocol': '0x0800',
                'type': 'raw'
            } for x in range(3)
        })
        streams.update({
            f'stream_5_swp3->swp{4-x if x <= 0 else 3-x}': {
                'ip_source': dev_groups[tg_ports[2]][0]['name'],
                'ip_destination': dev_groups[tg_ports[3-x if x <= 0 else 2-x]][0]['name'],
                'srcMac': f'e4:c7:7f:{x+6}e:60:2b',
                'dstMac': f'01:00:5E:19:bd:a{x+5}',
                'frameSize': randrange(100, 1500),
                'frame_rate_type': 'line_rate',
                'rate': 5,
                'protocol': '0x9100',
                'type': 'raw'
            } for x in range(3)
        })
        streams.update({
            f'stream_6_swp4->swp{3-x}': {
                'ip_source': dev_groups[tg_ports[3]][0]['name'],
                'ip_destination': dev_groups[tg_ports[2-x]][0]['name'],
                'srcMac': f'70:c5:30:7c:ef:f{x+5}',
                'dstMac': f'00:8{x+5}:4f:1b:80:91',
                'frameSize': randrange(100, 1500),
                'frame_rate_type': 'line_rate',
                'rate': 5,
                'protocol': '0x88a8',
                'type': 'raw'
            } for x in range(3)
        })

        await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)
        await tgen_utils_start_traffic(tgen_dev)
        await asyncio.sleep(traffic_duration)

        # verify the rate is limited
        await verify_rates(kbyte_value_stream, tgen_dev, correlation, deviation)

        for _ in range(2):
            # change storm control rates for all ports twice
            await set_rates(kbyte_value_stream, ports, device_host_name)
            await asyncio.sleep(traffic_duration)

            # verify the rate is limited
            await verify_rates(kbyte_value_stream, tgen_dev, correlation, deviation)

        # disable storm control for all ports
        await cleanup_kbyte_per_sec_rate_value(dent_dev, tgen_dev, all_values=True)
        await asyncio.sleep(traffic_duration)

        # verify the rate is not limited
        stream_names = ['stream_1_swp1->swp2', 'stream_2_swp1->swp2', 'stream_3_swp1->swp2',
                        'stream_4_swp2->swp1', 'stream_5_swp3->swp4', 'stream_6_swp4->swp3']
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
