import pytest
import asyncio

from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan
from dent_os_testbed.lib.bridge.bridge_fdb import BridgeFdb
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
    tgen_utils_get_loss,
)

pytestmark = [
    pytest.mark.suite_functional_bridging,
    pytest.mark.asyncio,
    pytest.mark.usefixtures('cleanup_bridges', 'cleanup_tgen')
]


async def test_bridging_relearning_on_different_vlans(testbed):
    """
    Test Name: test_bridging_relearning_on_different_vlans
    Test Suite: suite_functional_bridging
    Test Overview: Verify that mac addresses relearning on different vlans.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1. Init bridge entity br0.
    2. Set br0 ageing time to 600 seconds [default is 300 seconds].
    3. Set ports swp1, swp2, swp3, swp4 master br0.
    4. Set bridge br0 admin state UP.
    5. Set entities swp1, swp2, swp3, swp4 UP state.
    6. Add interfaces to vlans swp1, swp2, swp3 --> vlan 2,3.
    7. Send traffic and verify that entries have been learned on different vlans.
    8. Verify that entries have been removed from swp1 due to mac move to swp4.
    """

    bridge = 'br0'
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    ageing_time = 600
    traffic_duration = 5

    out = await IpLink.add(
       input_data=[{device_host_name: [
           {'device': bridge, 'type': 'bridge'}]}])
    assert out[0][device_host_name]['rc'] == 0, f'Verify that bridge created.\n{out}'

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': bridge, 'operstate': 'up'}]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that bridge set to 'UP' state.\n{out}"

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': bridge, 'ageing_time': ageing_time*100, 'type': 'bridge'}]}])
    err_msg = f"Verify that ageing time set to '600'.\n{out}"
    assert out[0][device_host_name]['rc'] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': port, 'master': bridge, 'operstate': 'up'} for port in ports]}])
    err_msg = f"Verify that bridge entities set to 'UP' state and links enslaved to bridge.\n{out}"
    assert out[0][device_host_name]['rc'] == 0, err_msg

    out = await BridgeVlan.add(
        input_data=[{device_host_name: [
            {'device': ports[x], 'vid': 2, 'vid': 3 } for x in range(3)]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that interfaces added to vlans '2' and '3'.\n{out}"

    address_map = (
        # swp port, tg port,    tg ip,     gw,        plen
        (ports[0], tg_ports[0], '1.1.1.2', '1.1.1.1', 24),
        (ports[1], tg_ports[1], '1.1.1.3', '1.1.1.1', 24),
        (ports[2], tg_ports[2], '1.1.1.4', '1.1.1.1', 24),
        (ports[3], tg_ports[3], '1.1.1.5', '1.1.1.1', 24),
    )

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': ip, 'gw': gw, 'plen': plen}
        for _, port, ip, gw, plen in address_map
    )

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    for x in range(3):
        streams = {
            'bridge_1': {
                'ip_source': dev_groups[tg_ports[x]][0]['name'],
                'ip_destination': dev_groups[tg_ports[3]][0]['name'],
                'srcMac': 'aa:bb:cc:dd:ee:11',
                'dstMac': 'aa:bb:cc:dd:ee:13',
                'type': 'raw',
                'protocol': '802.1Q',
                'vlanID': 2,
            },
            'bridge_2': {
                'ip_source': dev_groups[tg_ports[x]][0]['name'],
                'ip_destination': dev_groups[tg_ports[3]][0]['name'],
                'srcMac': 'aa:bb:cc:dd:ee:12',
                'dstMac': 'aa:bb:cc:dd:ee:14',
                'type': 'raw',
                'protocol': '802.1Q',
                'vlanID': 3,
            }
        }

        await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

        await tgen_utils_start_traffic(tgen_dev)
        await asyncio.sleep(traffic_duration)
        await tgen_utils_stop_traffic(tgen_dev)

        # check the traffic stats
        stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Traffic Item Statistics')
        for row in stats.Rows:
            loss = tgen_utils_get_loss(row)
            assert loss == 0, f'Expected loss: 0%, actual: {loss}%'

        out = await BridgeFdb.show(input_data=[{device_host_name: [{'options': '-j'}]}], parse_output=True)
        assert out[0][device_host_name]['rc'] == 0, f'Failed to get fdb entry.\n'

        fdb_entries = out[0][device_host_name]['parsed_output']
        learned_macs = [en['mac'] for en in fdb_entries if 'mac' in en]
        err_msg = f'Verify that source macs have been learned.\n'
        assert streams['bridge_1']['srcMac'] and streams['bridge_2']['srcMac'] in learned_macs, err_msg
        if x != 2:
            await tgen_utils_clear_traffic_items(tgen_dev)

    out = await BridgeFdb.show(input_data=[{device_host_name: [{'device': ports[0], 'options': '-j'}]}], parse_output=True)
    assert out[0][device_host_name]['rc'] == 0, f'Failed to get fdb entry.\n'

    fdb_entries = out[0][device_host_name]['parsed_output']
    learned_macs = [en['mac'] for en in fdb_entries if 'mac' in en]
    assert streams['bridge_1']['srcMac'] and streams['bridge_2']['srcMac'] not in learned_macs, err_msg
