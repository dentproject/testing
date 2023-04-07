import pytest
import asyncio

from dent_os_testbed.lib.bridge.bridge_link import BridgeLink
from dent_os_testbed.lib.bridge.bridge_fdb import BridgeFdb
from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_get_loss,
    tgen_utils_dev_groups_from_config,
    tgen_utils_traffic_generator_connect,
)

pytestmark = [
    pytest.mark.suite_functional_bridging,
    pytest.mark.asyncio,
    pytest.mark.usefixtures('cleanup_bridges', 'cleanup_tgen')
]


async def test_bridging_backward_forwarding(testbed):
    """
    Test Name: test_bridging_backward_forwarding
    Test Suite: suite_functional_bridging
    Test Overview: Verify that traffic with learned source mac is not being backward forwarding
                   to the transmitting port which the address has been learned for.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1, swp2, swp3, swp4 master br0.
    3.  Set bridge br0 admin state UP.
    4.  Set entities swp1, swp2, swp3, swp4 UP state.
    5.  Set ports swp1, swp2, swp3, swp4 learning ON.
    6.  Set ports swp1, swp2, swp3, swp4 flood OFF.
    7.  Traffic streamA sending to swp1 with source mac aa:bb:cc:dd:ee:11 and
        destination mac ff:ff:ff:ff:ff:ff for swp1 to learn source address.
    8.  Traffic streamB sending to swp1 with source mac aa:bb:cc:dd:ee:12 and
        destination mac aa:bb:cc:dd:ee:11.
    9.  Verify that there was no backward forwarding to swp1 from streamA.
    10. Verify that source mac aa:bb:cc:dd:ee:11 have been learned on swp1 from streamA.
    11. Verify that there was no backward forwarding back to swp1 from streamB.
    """

    bridge = 'br0'
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
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
            {'device': port, 'master': bridge, 'operstate': 'up'} for port in ports]}])
    err_msg = f"Verify that bridge entities set to 'UP' state and links enslaved to bridge.\n{out}"
    assert out[0][device_host_name]['rc'] == 0, err_msg

    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {'device': port, 'learning': True, 'flood': False} for port in ports]}])
    err_msg = f"Verify that entities set to learning 'ON' and flooding 'OFF' state.\n{out}"
    assert out[0][device_host_name]['rc'] == 0, err_msg

    address_map = (
        # swp port, tg port,    tg ip,     gw,        plen
        (ports[0], tg_ports[0], '1.1.1.2', '1.1.1.1', 24),
        (ports[0], tg_ports[0], '1.1.1.3', '1.1.1.1', 24),
    )

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': ip, 'gw': gw, 'plen': plen}
        for _, port, ip, gw, plen in address_map
    )

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    streams = {
        'streamA': {
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[0]][1]['name'],
            'srcMac': 'aa:bb:cc:dd:ee:11',
            'dstMac': 'ff:ff:ff:ff:ff:ff',
            'type': 'raw',
            'protocol': '802.1Q',
        },
        'streamB': {
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[0]][1]['name'],
            'srcMac': 'aa:bb:cc:dd:ee:12',
            'dstMac': 'aa:bb:cc:dd:ee:11',
            'type': 'raw',
            'protocol': '802.1Q',
        },
    }

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Traffic Item Statistics')
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) == 100.000, \
            f"Verify that traffic from {row['Tx Port']} to {row['Rx Port']} not forwarded.\n{out}"

    out = await BridgeFdb.show(input_data=[{device_host_name: [{'options': '-j'}]}],
                               parse_output=True)
    assert out[0][device_host_name]['rc'] == 0, f'Failed to get fdb entry.\n'

    fdb_entries = out[0][device_host_name]['parsed_output']
    learned_macs = [en['mac'] for en in fdb_entries if 'mac' in en]
    list_macs = ['aa:bb:cc:dd:ee:11', 'aa:bb:cc:dd:ee:12']
    for mac in list_macs:
        err_msg = f'Expected MACs are not found in FDB, but found MACs:{out}\n'
        assert mac in learned_macs, err_msg
