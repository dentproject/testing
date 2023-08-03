import math
import pytest
import asyncio
import random

from dent_os_testbed.test.test_suite.functional.storm_control.storm_control_utils import devlink_rate_value
from dent_os_testbed.test.test_suite.functional.storm_control.storm_control_utils import tc_filter_add
from dent_os_testbed.utils.test_utils.cleanup_utils import cleanup_kbyte_per_sec_rate_value
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
    tgen_utils_stop_traffic
)


pytestmark = [
    pytest.mark.suite_functional_storm_control,
    pytest.mark.asyncio,
    pytest.mark.usefixtures('cleanup_bridges', 'cleanup_tgen', 'cleanup_qdiscs')
]


async def test_storm_control_interaction_policer_rules(testbed, define_bash_utils):
    """
    Test Name: test_storm_control_interaction_policer_rules
    Test Suite: suite_functional_storm_control
    Test Overview: Verify that Policer rules (dynamic and data paths) take precedence over Storm Control rules.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Set entities swp1, swp2, swp3, swp4 UP state.
    2.  Set a storm control rate limit for all types of traffic on all ports.
    3.  Create an ingress qdisc on each TX port and define a dynamic policer trap rule for each qdisc.
    4.  Set up streams.
    5.  Transmit continues traffic from all ports simultaneously.
    6.  Verify that the CPU trapped packet rate is according to police trap rules (Storm Control has no effect).
    7.  Delete the rule from all ports' qdisc.
    8.  Init bridge entity br0.
    9.  Set bridge br0 admin state UP.
    10. Set ports swp1, swp2, swp3, swp4 master br0.
    11. Set entities swp1, swp2, swp3, swp4 UP state.
    12. Define a police pass rule for each qdisc that matches the selectors.
    13. Transmit continues traffic.
    14. Verify the RX rate on ports is according to policer dp limit rules (Storm Control has no effect).
    """

    bridge = 'br0'
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    size_packets = random.randint(500, 1000)
    traffic_duration = 15
    expected_rate = 4000
    cpu_stat_code = 195
    counter_type = 'sw'
    deviation = 0.10

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': port, 'operstate': 'up'} for port in ports]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that entities set to 'UP' state.\n{out}"

    params = [
        {'port': ports[0], 'name': 'unk_uc_kbyte_per_sec_rate', 'value': 37686},
        {'port': ports[1], 'name': 'unreg_mc_kbyte_per_sec_rate', 'value': 109413},
        {'port': ports[2], 'name': 'bc_kbyte_per_sec_rate', 'value': 75373}
    ]
    for value in params:
        await devlink_rate_value(dev=f'pci/0000:01:00.0/{value["port"].replace("swp","")}',
                                 name=value['name'], value=value['value'],
                                 cmode='runtime', device_host_name=device_host_name, set=True, verify=True)

    try:
        out = await TcQdisc.add(
            input_data=[{device_host_name: [
                {'dev': port, 'kind': 'ingress'} for port in ports[:3]]}])
        assert out[0][device_host_name]['rc'] == 0, f'Failed to configure ingress qdisc.\n{out}'

        await tc_filter_add(dev=ports[0], vlan_id=853, src_mac='10:62:5a:cf:ab:39', dst_mac='34:1e:60:35:58:ac',
                            rate='14836kbit', burst=15836, device_host_name=device_host_name)
        await tc_filter_add(dev=ports[1], vlan_id=2830, src_mac='98:92:be:4c:c8:53', dst_mac='01:00:5E:51:14:af',
                            rate='14836kbit', burst=15836, device_host_name=device_host_name)
        await tc_filter_add(dev=ports[2], vlan_id=2454, src_mac='54:84:c3:74:89:37', dst_mac='ff:ff:ff:ff:ff:ff',
                            rate='14836kbit', burst=15836, device_host_name=device_host_name)

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
        — stream_1 —  |  — stream_2 —  |  — stream_3 —  |  - stream_4 -
        swp1 -> swp4  |  swp2 -> swp4  |  swp3 -> swp4  |  swp3 -> swp4
                                                           swp3 -> swp2
                                                           swp3 -> swp1
        """

        streams = {
            'stream_1': {
                'ip_source': dev_groups[tg_ports[0]][0]['name'],
                'ip_destination': dev_groups[tg_ports[3]][0]['name'],
                'srcMac': '10:62:5a:cf:ab:39',
                'dstMac': '34:1e:60:35:58:ac',
                'frameSize': size_packets,
                'frame_rate_type': 'line_rate',
                'rate': 100,
                'protocol': '0x8100',
                'type': 'raw',
                'vlanID': 853
            },
            'stream_2': {
                'ip_source': dev_groups[tg_ports[1]][0]['name'],
                'ip_destination': dev_groups[tg_ports[3]][0]['name'],
                'srcMac': '98:92:be:4c:c8:53',
                'dstMac': '01:00:5E:51:14:af',
                'frameSize': size_packets,
                'frame_rate_type': 'line_rate',
                'rate': 100,
                'protocol': '0x8100',
                'type': 'raw',
                'vlanID': 2830
            },
            'stream_3': {
                'ip_source': dev_groups[tg_ports[2]][0]['name'],
                'ip_destination': dev_groups[tg_ports[3]][0]['name'],
                'srcMac': '54:84:c3:74:89:37',
                'dstMac': 'ff:ff:ff:ff:ff:ff',
                'frameSize': size_packets,
                'frame_rate_type': 'line_rate',
                'rate': 100,
                'protocol': '0x8100',
                'type': 'raw',
                'vlanID': 2454
            }
        }
        streams.update({
            f'stream_4_swp3->swp{4-x if x <= 0 else 3-x}': {
                'ip_source': dev_groups[tg_ports[2]][0]['name'],
                'ip_destination': dev_groups[tg_ports[3-x if x <= 0 else 2-x]][0]['name'],
                'srcMac': f'e4:c7:7f:{x+6}e:60:2b',
                'dstMac': f'01:00:5E:19:bd:a{x+5}',
                'frameSize': size_packets,
                'frame_rate_type': 'line_rate',
                'rate': 100,
                'protocol': '0x0800',
                'type': 'raw',
                'vlanID': 2830
            } for x in range(3)
        })

        await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)
        await tgen_utils_start_traffic(tgen_dev)
        await asyncio.sleep(traffic_duration)

        rc, out = await dent_dev.run_cmd(f'get_cpu_traps_rate_code_avg {cpu_stat_code} {counter_type}')
        assert not rc, f'get_cpu_traps_rate_code_avg failed with rc {rc}'
        err_msg = 'Failed: CPU trapped packet rate does not meet police trap rules.'
        assert math.isclose(int(out.strip()), expected_rate, rel_tol=deviation/2), err_msg

        await tgen_utils_stop_traffic(tgen_dev)

        out = await TcFilter.delete(
            input_data=[{device_host_name: [
                {'dev': port, 'direction': 'ingress', 'pref': '49152'} for port in ports[:3]]}])
        assert out[0][device_host_name]['rc'] == 0, f'Failed to configure ingress qdisc.\n{out}'

        out = await IpLink.add(
            input_data=[{device_host_name: [
                {'device': bridge, 'type': 'bridge', 'vlan_default_pvid': 0}]}])
        assert out[0][device_host_name]['rc'] == 0, f"Verify that vlan_default_pvid set to '0'.\n{out}"

        out = await IpLink.set(
            input_data=[{device_host_name: [
                {'device': bridge, 'operstate': 'up'}]}])
        assert out[0][device_host_name]['rc'] == 0, f"Verify that bridge set to 'UP' state.\n{out}"

        out = await IpLink.set(
            input_data=[{device_host_name: [
                {'device': port, 'master': bridge, 'operstate': 'up'} for port in ports]}])
        err_msg = f"Verify that bridge entities set to 'UP' state and links enslaved to bridge.\n{out}"
        assert out[0][device_host_name]['rc'] == 0, err_msg

        await tc_filter_add(dev=ports[0], vlan_id=853, src_mac='10:62:5a:cf:ab:39', dst_mac='34:1e:60:35:58:ac',
                            rate='18972709bps', burst=18973709, device_host_name=device_host_name)
        await tc_filter_add(dev=ports[1], vlan_id=2830, src_mac='98:92:be:4c:c8:53', dst_mac='01:00:5E:51:14:af',
                            rate='18972709bps', burst=18973709, device_host_name=device_host_name)
        await tc_filter_add(dev=ports[2], vlan_id=2454, src_mac='54:84:c3:74:89:37', dst_mac='ff:ff:ff:ff:ff:ff',
                            rate='18972709bps', burst=18973709, device_host_name=device_host_name)

        await tgen_utils_start_traffic(tgen_dev)
        await asyncio.sleep(traffic_duration)

        # check the traffic stats
        stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Traffic Item Statistics')
        collected = {row['Traffic Item']:
                     {'tx_rate': row['Tx Rate (Bps)'], 'rx_rate': row['Rx Rate (Bps)']} for row in stats.Rows}
        assert all(math.isclose(float(collected[f'stream_4_swp3->swp{4-x if x <= 0 else 3-x}']['tx_rate']),
                   float(collected[f'stream_4_swp3->swp{4-x if x <= 0 else 3-x}']['rx_rate']),
                   rel_tol=deviation) for x in range(3)), 'Failed: the rate is limited by storm control.'
    finally:
        await tgen_utils_stop_traffic(tgen_dev)
        await cleanup_kbyte_per_sec_rate_value(dent_dev, tgen_dev, all_values=True)
