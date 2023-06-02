import math
import pytest
import asyncio

from dent_os_testbed.test.test_suite.functional.storm_control.storm_control_utils import devlink_rate_value
from dent_os_testbed.utils.test_utils.cleanup_utils import cleanup_kbyte_per_sec_rate_value
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


async def test_storm_control_rule_set_for_br_and_unk_uc_traffic(testbed):
    """
    Test Name: test_storm_control_rule_set_for_br_and_unk_uc_traffic
    Test Suite: suite_functional_storm_control
    Test Overview: Verify Storm Control limits the rate of specific traffic types.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1, swp2 master br0.
    3.  Set entities swp1, swp2 UP state.
    4.  Set bridge br0 admin state UP.
    5.  Set up the following streams:
        - broadcast stream with random generated size of packet, on TX port;
        - multicast stream with random generated size of packet, on TX port;
        - unknown unicast stream with random generated size of packet, on TX port.
    6.  Set storm control rate limit of broadcast traffic on TX port.
    7.  Transmit continues traffic by TG.
    8.  Verify broadcast traffic is limited on RX port. Verify multicast and unknown unicast are not limited.
    9.  Disable storm control rate limit for broadcast traffic.
    10. Set storm control rate limit of unknown unicast traffic on TX port.
    11. Verify unknown unicast traffic is limited on RX port. Verify broadcast and multicast are not limited.
    """

    bridge = 'br0'
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    kbyte_value_unk_uc = 7229
    kbyte_value_bc = 21689
    traffic_duration = 15
    deviation = 0.10

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

    await devlink_rate_value(dev=f'pci/0000:01:00.0/{ports[0].replace("swp","")}',
                             name='bc_kbyte_per_sec_rate', value=kbyte_value_bc,
                             cmode='runtime', device_host_name=device_host_name, set=True, verify=True)

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
        — stream_1 —  |  — stream_2 —   |  — stream_3 —
        swp1 -> swp4  |  swp1 -> swp3   |  swp1 -> swp2
        """

        streams = {
            'stream_1': {
                'ip_source': dev_groups[tg_ports[0]][0]['name'],
                'ip_destination': dev_groups[tg_ports[3]][0]['name'],
                'srcIp': '147.126.111.32',
                'dstIp': '255.255.255.255',
                'srcMac': 'b2:ac:8f:b3:fb:2c',
                'dstMac': 'ff:ff:ff:ff:ff:ff',
                'frameSize': randrange(100, 1500),
                'frame_rate_type': 'line_rate',
                'rate': 30,
                'protocol': '0x0800',
                'type': 'raw'
            },
            'stream_2': {
                'ip_source': dev_groups[tg_ports[0]][0]['name'],
                'ip_destination': dev_groups[tg_ports[2]][0]['name'],
                'srcIp': '109.51.220.173',
                'dstIp': '224.33.57.130',
                'srcMac': '76:07:44:b7:38:07',
                'dstMac': '01:00:5E:21:39:82',
                'frameSize': randrange(100, 1500),
                'frame_rate_type': 'line_rate',
                'rate': 30,
                'protocol': '0x0800',
                'type': 'raw'
            },
            'stream_3': {
                'ip_source': dev_groups[tg_ports[0]][0]['name'],
                'ip_destination': dev_groups[tg_ports[1]][0]['name'],
                'srcMac': '98:ba:45:33:c7:ee',
                'dstMac': 'd2:15:8d:45:e1:1e',
                'frameSize': randrange(100, 1500),
                'frame_rate_type': 'line_rate',
                'rate': 30,
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
        assert math.isclose(kbyte_value_bc*1000,
                            float(collected['stream_1']['rx_rate']), rel_tol=deviation), \
            f"The rate is not limited by storm control, \
                        actual rate {kbyte_value_bc*1000} istead of {float(collected['stream_1']['rx_rate'])}."
        for x in range(2):
            assert math.isclose(float(collected[f'stream_{x+2}']['tx_rate']),
                                float(collected[f'stream_{x+2}']['rx_rate']), rel_tol=deviation), \
                f"The rate is limited by storm control, actual rate {float(collected[f'stream_{x+2}']['tx_rate'])} \
                    istead of {float(collected[f'stream_{x+2}']['rx_rate'])}."

        await devlink_rate_value(dev=f'pci/0000:01:00.0/{ports[0].replace("swp","")}',
                                 name='bc_kbyte_per_sec_rate', value=0,
                                 cmode='runtime', device_host_name=device_host_name, set=True, verify=True)

        await devlink_rate_value(dev=f'pci/0000:01:00.0/{ports[0].replace("swp","")}',
                                 name='unk_uc_kbyte_per_sec_rate', value=kbyte_value_unk_uc,
                                 cmode='runtime', device_host_name=device_host_name, set=True, verify=True)
        await asyncio.sleep(traffic_duration)

        # check the traffic stats
        stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Traffic Item Statistics')
        collected = {row['Traffic Item']:
                     {'tx_rate': row['Tx Rate (Bps)'], 'rx_rate': row['Rx Rate (Bps)']} for row in stats.Rows}
        for x in range(2):
            assert math.isclose(float(collected[f'stream_{x+1}']['tx_rate']),
                                float(collected[f'stream_{x+1}']['rx_rate']), rel_tol=deviation), \
                f"The rate is limited by storm control, actual rate {float(collected[f'stream_{x+1}']['tx_rate'])} \
                    istead of {float(collected[f'stream_{x+1}']['rx_rate'])}."
        assert math.isclose(kbyte_value_unk_uc*1000, float(collected['stream_3']['rx_rate']), rel_tol=deviation), \
            f"The rate is not limited by storm control, \
                        actual rate {kbyte_value_unk_uc*1000} istead of {float(collected['stream_3']['rx_rate'])}."
    finally:
        await tgen_utils_stop_traffic(tgen_dev)
        await cleanup_kbyte_per_sec_rate_value(dent_dev, tgen_dev, bc=True, unk_uc=True)
