import pytest
import asyncio

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


async def test_port_isolation_incremental_mac_addresses(testbed):
    """
    Test Name: test_port_isolation_incremental_mac_addresses
    Test Suite: suite_functional_port_isolation
    Test Overview: Verify that isolated ports cannot send or receive packets containing
                   incremental destination mac addresses to or from each other but still
                   communicate normally with any other ports of the bridge.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1, swp2, swp3, swp4 master br0.
    3.  Set entities swp1, swp2, swp3, swp4 UP state.
    4.  Set bridge br0 admin state UP.
    5.  Set the first three bridge entities as isolated.
    6.  Set up the streams.
    7.  Transmit traffic by TG.
    8.  Verify traffic sent from isolated ports that was received on a non-isolated port only.
    9.  Verify traffic sent from a non-isolated port is received on all ports.
    10. Verify that all addresses have been learned.
    """

    bridge = 'br0'
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    ixia_vhost_mac_count = 4
    traffic_duration = 15
    pps_value = 4000
    mac_count = 5000
    tolerance = 0.8
    wait = 6

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
                'srcMac': {'type': 'increment',
                           'start': '40:ee:65:26:69:46',
                           'step': '00:00:00:00:10:00',
                           'count': mac_count},
                'dstMac': f'56:18:0b:25:41:b{x+1}',
                'frameSize': 1451,
                'rate': pps_value,
                'protocol': '0x0800',
                'type': 'raw'
            },
            'stream_1': {
                'ip_source': dev_groups[tg_ports[1]][0]['name'],
                'ip_destination': dev_groups[tg_ports[3-x if x < 2 else 0]][0]['name'],
                'srcMac': {'type': 'increment',
                           'start': '78:d5:fc:e5:42:85',
                           'step': '00:00:00:00:10:00',
                           'count': mac_count},
                'dstMac': f'f2:c9:74:75:45:3{x+5}',
                'frameSize': 1451,
                'rate': pps_value,
                'protocol': '0x9200',
                'type': 'raw'
            },
            'stream_2': {
                'ip_source': dev_groups[tg_ports[2]][0]['name'],
                'ip_destination': dev_groups[tg_ports[3-x if x <= 0 else 2-x]][0]['name'],
                'srcMac': {'type': 'increment',
                           'start': 'ea:c5:88:37:c9:6f',
                           'step': '00:00:00:00:10:00',
                           'count': mac_count},
                'dstMac': f'fa:f5:38:5e:1a:1{x+5}',
                'frameSize': 1451,
                'rate': pps_value,
                'protocol': '0x88a8',
                'type': 'raw'
            },
            'stream_3': {
                'ip_source': dev_groups[tg_ports[3]][0]['name'],
                'ip_destination': dev_groups[tg_ports[2-x]][0]['name'],
                'srcMac': {'type': 'increment',
                           'start': '28:de:d0:df:49:ca',
                           'step': '00:00:00:00:10:00',
                           'count': mac_count},
                'dstMac': f'6a:e7:c4:5b:02:d{x+1}',
                'frameSize': 1451,
                'rate': pps_value,
                'protocol': '0x0800',
                'type': 'raw'
            }
        }

        await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)
        await tgen_utils_start_traffic(tgen_dev)
        await asyncio.sleep(traffic_duration)
        await tgen_utils_stop_traffic(tgen_dev)
        await asyncio.sleep(wait)

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

        rc, out = await dent_dev.run_cmd("bridge fdb show br br0 | grep 'extern_learn.*offload' | wc -l")
        assert rc == 0, "Failed to grep 'extern_learn.*offload'."

        amount = int(out) - ixia_vhost_mac_count
        err_msg = f'Expected count of extern_learn offload entities: >{mac_count}*{tolerance}, Actual count: {amount}.'
        assert amount > mac_count*ixia_vhost_mac_count*tolerance, err_msg

        await tgen_utils_clear_traffic_items(tgen_dev)
