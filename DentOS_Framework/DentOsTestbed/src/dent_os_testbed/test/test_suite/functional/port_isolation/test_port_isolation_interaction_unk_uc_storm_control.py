import pytest
import asyncio

from dent_os_testbed.test.test_suite.functional.storm_control.storm_control_utils import verify_expected_rx_rate
from dent_os_testbed.test.test_suite.functional.storm_control.storm_control_utils import devlink_rate_value
from dent_os_testbed.utils.test_utils.cleanup_utils import cleanup_kbyte_per_sec_rate_value
from dent_os_testbed.lib.bridge.bridge_link import BridgeLink
from dent_os_testbed.lib.ip.ip_link import IpLink
from random import randrange

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_get_loss
)

pytestmark = [
    pytest.mark.suite_functional_port_isolation,
    pytest.mark.asyncio,
    pytest.mark.usefixtures('cleanup_bridges', 'cleanup_tgen')
]


async def test_port_isolation_interaction_unk_uc_storm_control(testbed):
    """
    Test Name: test_port_isolation_interaction_unk_uc_storm_control
    Test Suite: suite_functional_port_isolation
    Test Overview: Verify traffic is limited on isolated ports.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1, swp2, swp3, swp4 master br0.
    3.  Set entities swp1, swp2, swp3, swp4 UP state.
    4.  Set bridge br0 admin state UP.
    5.  Set the first three bridge entities as isolated.
    6.  Set up the following streams with random generated size of packet:
            - unknown unicast stream on the first (isolated) TG port
            - stream on the fourth (non-isolated) port
    7.  Set storm control rate limit of unknown unicast stream.
    8.  Transmit continues traffic by TG.
    9.  Verify traffic sent from isolated ports that was received and limited by
        storm control on a non-isolated port only.
    10. Verify traffic sent from a non-isolated port is received and limited by
        storm control on all ports.
    """

    bridge = 'br0'
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    kbyte_value = [15277, 97367]
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

    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {'device': port, 'isolated': True} for port in ports[:3]]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that entities set to isolated state 'ON'.\n{out}"

    await devlink_rate_value(dev=f'pci/0000:01:00.0/{ports[0].replace("swp","")}',
                             name='unk_uc_kbyte_per_sec_rate', value=kbyte_value[0],
                             cmode='runtime', device_host_name=device_host_name, set=True, verify=True)
    await devlink_rate_value(dev=f'pci/0000:01:00.0/{ports[3].replace("swp","")}',
                             name='unk_uc_kbyte_per_sec_rate', value=kbyte_value[1],
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
        — stream_1-3 —  |  — stream_4-6 —
         swp1 -> swp4   |   swp4 -> swp3
         swp1 -> swp3   |   swp4 -> swp2
         swp1 -> swp2   |   swp4 -> swp1
        """

        streams = {
                f'stream_{x+1}': {
                    'ip_source': dev_groups[tg_ports[0]][0]['name'],
                    'ip_destination': dev_groups[tg_ports[3-x]][0]['name'],
                    'srcMac': f'16:ea:c3:{x+5}d:1e:ec',
                    'dstMac': f'3e:f4:7a:e8:10:3{x+1}',
                    'frameSize': randrange(100, 1500),
                    'frame_rate_type': 'line_rate',
                    'rate': 100,
                    'protocol': '0x0800',
                    'type': 'raw'
                } for x in range(3)
            }
        streams.update({
                f'stream_{x+4}': {
                    'ip_source': dev_groups[tg_ports[3]][0]['name'],
                    'ip_destination': dev_groups[tg_ports[2-x]][0]['name'],
                    'srcMac': f'84:fc:70:36:2a:7{x+3}',
                    'dstMac': f'68:16:3d:2e:b4:c{x+5}',
                    'frameSize': randrange(100, 1500),
                    'frame_rate_type': 'line_rate',
                    'rate': 100,
                    'protocol': '0x0800',
                    'type': 'raw'
                } for x in range(3)
            })

        await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)
        await tgen_utils_start_traffic(tgen_dev)
        await asyncio.sleep(traffic_duration)

        # check the traffic stats
        stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Port Statistics')
        await verify_expected_rx_rate(kbyte_value[0], stats,
                                      rx_ports=[streams['stream_1']['ip_destination']], deviation=deviation)
        for x in range(3):
            await verify_expected_rx_rate(kbyte_value[1], stats,
                                          rx_ports=[streams[f'stream_{x+4}']['ip_destination']], deviation=deviation)

        # check the traffic stats
        stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
        for row in stats.Rows:
            for x in range(2):
                if row['Traffic Item'] == f'stream_{x+2}':
                    assert tgen_utils_get_loss(row) == 100.000, \
                        f"Verify that traffic from {row['Tx Port']} to {row['Rx Port']} not forwarded.\n{out}"
    finally:
        await tgen_utils_stop_traffic(tgen_dev)
        await cleanup_kbyte_per_sec_rate_value(dent_dev, tgen_dev, bc=True)
