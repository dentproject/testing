import asyncio
import pytest
import json

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.constants import PLATFORMS_CONSTANTS
from dent_os_testbed.utils.FileHandlers.LocalFileHandler import LocalFileHandler

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_get_traffic_stats,
    tgen_utils_get_loss,
    tgen_utils_dev_groups_from_config,
    tgen_utils_traffic_generator_connect,
    tgen_utils_clear_traffic_items)
from dent_os_testbed.utils.test_utils.br_utils import (
    get_traffic_port_vlan_mapping,
    configure_bridge_setup,
    configure_vlan_setup)


pytestmark = [pytest.mark.suite_functional_vlan,
              pytest.mark.asyncio,
              pytest.mark.usefixtures('cleanup_tgen', 'cleanup_bridges')]


async def test_vlan_with_increment_macs(testbed):
    """
    Test Name: VLAN with increment mac
    Test Suite: suite_functional_vlan
    Test Overview: Test broadcast packet forwarding with incremented mac addresses
    Test Procedure:
    1. Create bridge. Set links, bridge to `up` state
    2. Enslave interfaces to the created bridge entity.
    3. Insert interfaces to VLAN
        Port 1: vlan 5,
                vlan 33,
                vlan 20
        Port 2: vlan 5
                vlan 33,
                vlan 20
        Port 3: vlan 5,
                vlan 33,
                vlan 20
        Port 4: vlan 5,
                vlan 33,
                vlan 20
    4. Set up streams with incremented MAC address (16000 | 32000), pps 15000
    5. Send traffic
    6. Verify no packet loss nor packet leak occurred and all transmitted traffic received
    7. Verify all MAC entries were learnt or re-learnt on the VLAN
    8. Repeat steps #4 - #7 for vlans 5, 33, 20
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print('The testbed does not have enough dent with tgn connections')
        return
    device = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[device][0]
    dut_ports = tgen_dev.links_dict[device][1]
    tolerance = 0.7  # fdb learning tolerance

    rc, model = await dent_devices[0].run_cmd('cat /etc/onl/platform')
    model = model.strip('\n')

    mac_table = LocalFileHandler(dent_devices[0].applog).read(PLATFORMS_CONSTANTS)
    mac_count = json.loads(mac_table)
    mac_count = mac_count[model]['fdb_size']
    packet_vids = [5, 33, 20]
    ageing_time = 30

    # 1. Create bridge. Set links, bridge to `up` state
    # 2. Enslave interfaces to the created bridge entity.
    await configure_bridge_setup(device, dut_ports)

    out = await IpLink.set(
        input_data=[{device: [{'device': 'br0', 'ageing_time': ageing_time*100, 'type': 'bridge'}]}])
    assert out[0][device]['rc'] == 0, f'Verify that ageing time set to {ageing_time}.'

    # 3. Insert interfaces to VLANs
    port_map = (
        {'port': 0, 'settings': [{'vlan': 5, 'untagged': False, 'pvid': True},
                                 {'vlan': 33, 'untagged': False, 'pvid': False},
                                 {'vlan': 20, 'untagged': False, 'pvid': False}]},

        {'port': 1, 'settings': [{'vlan': 5, 'untagged': False, 'pvid': True},
                                 {'vlan': 33, 'untagged': False, 'pvid': False},
                                 {'vlan': 20, 'untagged': False, 'pvid': False}]},

        {'port': 2, 'settings': [{'vlan': 5, 'untagged': False, 'pvid': True},
                                 {'vlan': 33, 'untagged': False, 'pvid': False},
                                 {'vlan': 20, 'untagged': False, 'pvid': False}]},

        {'port': 3, 'settings': [{'vlan': 5, 'untagged': False, 'pvid': True},
                                 {'vlan': 33, 'untagged': False, 'pvid': False},
                                 {'vlan': 20, 'untagged': False, 'pvid': False}]})

    await configure_vlan_setup(device, port_map, dut_ports)

    dev_groups = tgen_utils_dev_groups_from_config(
        [{'ixp': tg_ports[0], 'ip': '100.1.1.2', 'gw': '100.1.1.6', 'plen': 24, },
         {'ixp': tg_ports[1], 'ip': '100.1.1.3', 'gw': '100.1.1.6', 'plen': 24, },
         {'ixp': tg_ports[2], 'ip': '100.1.1.4', 'gw': '100.1.1.6', 'plen': 24, },
         {'ixp': tg_ports[3], 'ip': '100.1.1.5', 'gw': '100.1.1.6', 'plen': 24, }])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    tx_ports = dev_groups[tg_ports[0]][0]['name']
    rx_ports = dev_groups[tg_ports[1]][0]['name']

    # 4. Set up streams with incremented MAC address , pps 15000 and vlans 5, 33, 20
    for vlan in packet_vids:
        streams = {f'traffic with VLAN ID: {vlan}': {
            'type': 'raw',
            'protocol': '802.1Q',
            'ip_source': tx_ports,
            'ip_destination': rx_ports,
            'srcMac': {'type': 'increment',
                       'start': '02:00:00:00:ff:00',
                       'step': '00:00:00:00:10:00',
                       'count': mac_count},
            'dstMac': 'ff:ff:ff:ff:ff:ff',
            'rate': 15000,
            'vlanID': vlan
        }}

        await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

        # 5. Send traffic
        await tgen_utils_start_traffic(tgen_dev)
        await asyncio.sleep(15)
        await tgen_utils_stop_traffic(tgen_dev)
        await asyncio.sleep(10)
        # 6. Verify no packet loss nor packet leak occurred and all transmitted traffic received
        stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
        ti_to_rx_port_map = get_traffic_port_vlan_mapping(streams, port_map, tg_ports)
        for row in stats.Rows:
            if row['Rx Port'] in ti_to_rx_port_map[row['Traffic Item']]:
                assert tgen_utils_get_loss(row) == 0.000, \
                    f'Traffic leak for traffic item: {row["Traffic Item"]} on port {row["Rx Port"]}'
            else:
                assert tgen_utils_get_loss(row) == 100.000, \
                    f'No traffic for traffic item : {row["Traffic Item"]} on port {row["Rx Port"]}'

        # 7. Verify all MAC entries were learnt or re-learnt on the VLAN
        rc, number_of_macs = await dent_devices[0].run_cmd(
            f"bridge fdb show dev {dut_ports[0]} | grep 'vlan {vlan}' | wc -l")
        assert rc == 0, 'Failed getting learned vlans on the ports'
        assert int(number_of_macs.strip()) > (mac_count * tolerance),\
            f'Fail learning all macs with vlan: {vlan}expected {mac_count * tolerance} got {number_of_macs.strip()}'
        await asyncio.sleep(5)  # in order tgen_utils_stop_traffic() to finish on TG
        await tgen_utils_clear_traffic_items(tgen_dev)
