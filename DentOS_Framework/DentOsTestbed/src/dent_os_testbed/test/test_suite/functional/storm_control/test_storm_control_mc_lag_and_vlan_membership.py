import pytest
import random
import asyncio

from dent_os_testbed.test.test_suite.functional.storm_control.storm_control_utils import devlink_rate_value
from dent_os_testbed.utils.test_utils.cleanup_utils import cleanup_kbyte_per_sec_rate_value
from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan
from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_get_loss
)

pytestmark = [
    pytest.mark.suite_functional_storm_control,
    pytest.mark.asyncio,
    pytest.mark.usefixtures('cleanup_bridges', 'cleanup_tgen', 'cleanup_bonds')
]


async def test_storm_control_mc_lag_and_vlan_membership(testbed):
    """
    Test Name: test_storm_control_mc_lag_and_vlan_membership
    Test Suite: suite_functional_storm_control
    Test Overview: Verify rate is limited according to the changes in Storm Control Rules.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Create a bond (bond1), set link UP state on it and enslave the first port connected to Ixia to it.
    2.  Create a bond (bond2), set link UP state on it and enslave the third port connected to Ixia to it.
    3.  Set entities swp1, swp2, swp3, swp4 UP state.
    4.  Init vlan aware bridge entity br0.
    5.  Set bridge br0 admin state UP.
    6.  Set ports swp2, swp4 master br0.
    7.  Set bonds bond1, bond2 master br0.
    8.  Set up the following streams:
        - Ixia port 4: multicast streams with random generated size of packet.
    9.  Transmit continues traffic by TG.
    10. Verify the RX rate on the RX port is as expected - the rate is limited by storm control.
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
    pps_value = 1000

    for x in range(2):
        out = await IpLink.add(
            input_data=[{device_host_name: [
                {'device': f'bond{x+1}', 'type': 'bond mode 802.3ad'}]}])
        err_msg = f"Verify that bond{x+1} created and type set to 'bond mode 802.3ad'.\n{out}"
        assert out[0][device_host_name]['rc'] == 0, err_msg

        out = await IpLink.set(
            input_data=[{device_host_name: [
                {'device': f'bond{x+1}', 'operstate': 'up'},
                {'device': ports[x if x == 0 else 2], 'operstate': 'down'},
                {'device': ports[x if x == 0 else 2], 'master': f'bond{x+1}'}]}])
        err_msg = f"Verify that bond{x+2} set to 'UP' state, {ports[x if x == 0 else 2]} set to 'DOWN' state \
            and enslave {ports[x if x == 0 else 2]} port connected to Ixia.\n{out}"
        assert out[0][device_host_name]['rc'] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': port, 'operstate': 'up'} for port in ports]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that entities set to 'UP' state.\n{out}"

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
            {'device': ports[x+1 if x == 0 else 3], 'master': bridge} for x in range(2)]}])
    err_msg = f'Verify that swp2 and swp4 bridge entities enslaved to bridge.\n{out}'
    assert out[0][device_host_name]['rc'] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': f'bond{x+1}', 'master': bridge} for x in range(2)]}])
    err_msg = f'Verify that bond1 and bond2 entities enslaved to bridge.\n{out}'
    assert out[0][device_host_name]['rc'] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': bridge, 'type': 'bridge', 'vlan_default_pvid': 0}]}])
    err_msg = f"Verify that vlan_default_pvid set to '0'.\n{out}"
    assert out[0][device_host_name]['rc'] == 0, err_msg

    out = await BridgeVlan.add(
        input_data=[{device_host_name: [
            {'device': ports[x+1 if x == 0 else 3], 'vid': f'{x+1}', 'untagged': True, 'pvid': True}
            for x in range(2)]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that entities added to vid '1' and '2'.\n{out}"

    out = await BridgeVlan.add(
        input_data=[{device_host_name: [
            {'device': f'bond{x+1}', 'vid': f'{x+1}', 'untagged': True, 'pvid': True}
            for x in range(2)]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that entities added to vid '1' and '2'.\n{out}"

    await devlink_rate_value(dev=f'pci/0000:01:00.0/{ports[0].replace("swp","")}',
                             name='unk_uc_kbyte_per_sec_rate', value=94404,
                             cmode='runtime', device_host_name=device_host_name, set=True, verify=True)
    await devlink_rate_value(dev=f'pci/0000:01:00.0/{ports[1].replace("swp","")}',
                             name='bc_kbyte_per_sec_rate', value=1210,
                             cmode='runtime', device_host_name=device_host_name, set=True, verify=True)
    await devlink_rate_value(dev=f'pci/0000:01:00.0/{ports[1].replace("swp","")}',
                             name='unreg_mc_kbyte_per_sec_rate', value=35099,
                             cmode='runtime', device_host_name=device_host_name, set=True, verify=True)
    await devlink_rate_value(dev=f'pci/0000:01:00.0/{ports[1].replace("swp","")}',
                             name='unk_uc_kbyte_per_sec_rate', value=37519,
                             cmode='runtime', device_host_name=device_host_name, set=True, verify=True)
    await devlink_rate_value(dev=f'pci/0000:01:00.0/{ports[2].replace("swp","")}',
                             name='bc_kbyte_per_sec_rate', value=32678,
                             cmode='runtime', device_host_name=device_host_name, set=True, verify=True)
    await devlink_rate_value(dev=f'pci/0000:01:00.0/{ports[2].replace("swp","")}',
                             name='unk_uc_kbyte_per_sec_rate', value=36309,
                             cmode='runtime', device_host_name=device_host_name, set=True, verify=True)
    await devlink_rate_value(dev=f'pci/0000:01:00.0/{ports[3].replace("swp","")}',
                             name='unreg_mc_kbyte_per_sec_rate', value=83511,
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
        — stream_1 —   |  — stream_2 —  |  — stream_3 —
        swp4 -> swp1   |  swp4 -> swp2  |  swp1 -> swp3
        """

        for x in range(3):
            streams = {
                f'stream_{x+1}_mc_swp4->swp{x+1}': {
                    'ip_source': dev_groups[tg_ports[3]][0]['name'],
                    'ip_destination': dev_groups[tg_ports[x]][0]['name'],
                    'srcMac': f'74:c9:fe:eb:d5:8{x+1}',
                    'dstMac': f'01:00:5E:3{x+1}:2e:7f',
                    'frameSize': random.randint(128, 512),
                    'rate': pps_value,
                    'protocol': '0x0800',
                    'type': 'raw'
                }
            }

            await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)
            await tgen_utils_start_traffic(tgen_dev)
            await asyncio.sleep(traffic_duration)

        # check the traffic stats
        stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
        expected_loss = {
            'stream_1_mc_swp4->swp1': 100,
            'stream_2_mc_swp4->swp2': 100,
            'stream_3_mc_swp4->swp3': 0
        }
        for row in stats.Rows:
            assert tgen_utils_get_loss(row) == expected_loss[row['Traffic Item']], \
                'Verify that traffic forwarded/not forwarded in accordance.'
    finally:
        await cleanup_kbyte_per_sec_rate_value(dent_dev, all_values=True)
