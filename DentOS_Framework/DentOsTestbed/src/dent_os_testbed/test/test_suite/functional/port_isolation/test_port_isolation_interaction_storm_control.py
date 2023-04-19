import pytest
import random
import asyncio

from dent_os_testbed.utils.test_utils.cleanup_utils import cleanup_kbyte_per_sec_rate_value
from dent_os_testbed.lib.devlink.devlink_port import DevlinkPort
from dent_os_testbed.lib.bridge.bridge_link import BridgeLink
from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_clear_traffic_items,
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


async def devlink_rate_value(dev, name, value, cmode=False, device_host_name=True,
                             set_and_verify=False, verify=False):
    if set_and_verify:
        # set kbyte_per_sec_rate value
        out = await DevlinkPort.set(input_data=[{device_host_name: [
            {'dev': dev, 'name': name, 'value': value, 'cmode': cmode}]}])
        assert out[0][device_host_name]['rc'] == 0, f"Failed to set rate value '{value}'.\n{out}"

        # verify kbyte_per_sec_rate value
        out = await DevlinkPort.show(input_data=[{device_host_name: [
            {'options': '-j', 'dev': dev, 'name': name}]}], parse_output=True)
        err_msg = f"Failed to execute the command 'DevlinkPort.show'.\n{out}"
        assert out[0][device_host_name]['rc'] == 0, err_msg
        devlink_info = out[0][device_host_name]['parsed_output']
        kbyte_value = devlink_info['param'][dev][0]['values'][0]['value']
        assert kbyte_value == value, f"Verify that storm control rate configured is '{value}' kbps.\n"

    if verify:
        # verify kbyte_per_sec_rate value
        out = await DevlinkPort.show(input_data=[{device_host_name: [
            {'options': '-j', 'dev': dev, 'name': name}]}], parse_output=True)
        err_msg = f"Failed to execute the command 'DevlinkPort.show'.\n{out}"
        assert out[0][device_host_name]['rc'] == 0, err_msg
        devlink_info = out[0][device_host_name]['parsed_output']
        kbyte_value = devlink_info['param'][dev][0]['values'][0]['value']
        assert kbyte_value == value, f"Verify that storm control rate configured is '{value}' kbps.\n"


async def test_port_isolation_interaction_storm_control(testbed):
    """
    Test Name: test_port_isolation_interaction_storm_control
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
            - unicast stream on the first (isolated) TG port
            - multicast stream on the second (isolated) TG port
            - broadcast stream on the third (isolated) TG port
            - stream on the fourth (non-isolated) port
    7.  Set storm control rate limit of broadcast, multicast and unknown unicast
        traffic on one isolated port and one non-isolated port.
    8.  Transmit traffic by TG.
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
    traffic_duration = 10
    pps_value = 1000

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

    await devlink_rate_value(dev='pci/0000:01:00.0/1', name='unreg_mc_kbyte_per_sec_rate',
                             value=30277, cmode='runtime', device_host_name=device_host_name, set_and_verify=True)
    await devlink_rate_value(dev='pci/0000:01:00.0/4', name='unreg_mc_kbyte_per_sec_rate',
                             value=105367, cmode='runtime', device_host_name=device_host_name, set_and_verify=True)

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
    — stream_0 —  |  — stream_1 —   |  — stream_2 —  |  — stream_3 —
    swp1 -> swp4  |  swp2 -> swp4   |  swp3 -> swp4  |  swp4 -> swp3

    — stream_0 —  |  — stream_1 —   |  — stream_2 —  |  — stream_3 —
    swp1 -> swp3  |  swp2 -> swp3   |  swp3 -> swp2  |  swp4 -> swp2

    — stream_0 —  |  — stream_1 —   |  — stream_2 —  |  — stream_3 —
    swp1 -> swp2  |  swp2 -> swp1   |  swp3 -> swp1  |  swp4 -> swp1
    """

    for x in range(3):
        streams = {
            'stream_0': {
                'ip_source': dev_groups[tg_ports[0]][0]['name'],
                'ip_destination': dev_groups[tg_ports[3-x]][0]['name'],
                'srcMac': '28:be:0d:47:eb:2b',
                'dstMac': '1c:99:9f:fb:63:15',
                'frameSize': random.randint(128, 512),
                'rate': pps_value,
                'protocol': '0x0800',
                'type': 'raw'
            },
            'stream_1': {
                'ip_source': dev_groups[tg_ports[1]][0]['name'],
                'ip_destination': dev_groups[tg_ports[3-x if x < 2 else 0]][0]['name'],
                'srcIp': '147.147.96.74',
                'dstIp': '229.112.223.59',
                'srcMac': 'f2:de:a4:35:bd:4b',
                'dstMac': '01:00:5E:70:df:3b',
                'frameSize': random.randint(128, 512),
                'rate': pps_value,
                'protocol': '0x0800',
                'type': 'raw'
            },
            'stream_2': {
                'ip_source': dev_groups[tg_ports[2]][0]['name'],
                'ip_destination': dev_groups[tg_ports[3-x if x <= 0 else 2-x]][0]['name'],
                'srcMac': '2a:3e:13:88:e5:6d',
                'dstMac': 'ff:ff:ff:ff:ff:ff',
                'frameSize': random.randint(128, 512),
                'rate': pps_value,
                'protocol': '0x0800',
                'type': 'raw'
            },
            'stream_3': {
                'ip_source': dev_groups[tg_ports[3]][0]['name'],
                'ip_destination': dev_groups[tg_ports[2-x]][0]['name'],
                'srcMac': 'ea:f9:ca:10:1d:b6',
                'dstMac': 'ba:2e:c5:2c:fa:8d',
                'frameSize': random.randint(128, 512),
                'rate': pps_value,
                'protocol': '0x0800',
                'type': 'raw'
            }
        }

        await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)
        await tgen_utils_start_traffic(tgen_dev)
        await asyncio.sleep(traffic_duration)
        await tgen_utils_stop_traffic(tgen_dev)

        if x == 0:
            expected_loss = {
                'stream_0': 0,
                'stream_1': 0,
                'stream_2': 0,
                'stream_3': 0
            }
        else:
            expected_loss = {
                'stream_0': 100,
                'stream_1': 100,
                'stream_2': 100,
                'stream_3': 0
            }
        # check the traffic stats
        stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
        for row in stats.Rows:
            assert tgen_utils_get_loss(row) == expected_loss[row['Traffic Item']], \
                'Verify that traffic is forwarded/not forwarded in accordance.'

        await tgen_utils_clear_traffic_items(tgen_dev)

    await cleanup_kbyte_per_sec_rate_value(dent_dev, unreg_mc=True)
