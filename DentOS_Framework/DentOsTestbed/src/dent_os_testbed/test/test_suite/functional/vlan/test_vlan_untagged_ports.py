import asyncio
import pytest

from dent_os_testbed.utils.test_utils.tgen_utils import (tgen_utils_get_dent_devices_with_tgen,
                                                         tgen_utils_setup_streams, tgen_utils_start_traffic,
                                                         tgen_utils_stop_traffic, tgen_utils_get_traffic_stats,
                                                         tgen_utils_get_loss, tgen_utils_dev_groups_from_config,
                                                         tgen_utils_traffic_generator_connect, )
from dent_os_testbed.utils.test_utils.br_utils import (configure_bridge_setup, configure_vlan_setup,
                                                       get_traffic_port_vlan_mapping)


port_map = ({'port': 0, 'settings': [{'vlan': 2, 'untagged': True, 'pvid': True}]},
            {'port': 1, 'settings': [{'vlan': 2, 'untagged': True, 'pvid': True}]},
            {'port': 2, 'settings': [{'vlan': 2, 'untagged': True, 'pvid': True}]},
            {'port': 3, 'settings': [{'vlan': 2, 'untagged': True, 'pvid': True}]})

pytestmark = [pytest.mark.suite_functional_vlan,
              pytest.mark.asyncio,
              pytest.mark.usefixtures('cleanup_bridges', 'cleanup_tgen')]


@pytest.mark.parametrize('traffic_type', ['broadcast', 'multicast', 'unicast'])
async def test_vlan_untagged_ports_with_(testbed, traffic_type):
    """
    Test Name: VLAN untagged ports
    Test Suite: suite_functional_vlan
    Test Overview: Test packet forwarding with VLAN untagged ports
    Test Procedure:
    1. Initiate test params.
    2. Set links to vlans.
    3. Map receiving and non receiving dut_ports.
    4. Setup packet stream(s) for the packet.
    5. Send traffic to rx_ports.
    6. Verify traffic on receiving ports.
    """

    # 1. Initiate test params.
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    device = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[device][0]
    dut_ports = tgen_dev.links_dict[device][1]

    await configure_bridge_setup(device, dut_ports)

    # 2. Set links to vlans.
    await configure_vlan_setup(device, port_map, dut_ports)

    # 3. Map receiving and non receiving dut_ports.
    dev_groups = tgen_utils_dev_groups_from_config(
        [{'ixp': tg_ports[0], 'ip': '100.1.1.2', 'gw': '100.1.1.6', 'plen': 24, },
         {'ixp': tg_ports[1], 'ip': '100.1.1.3', 'gw': '100.1.1.6', 'plen': 24, },
         {'ixp': tg_ports[2], 'ip': '100.1.1.4', 'gw': '100.1.1.6', 'plen': 24, },
         {'ixp': tg_ports[3], 'ip': '100.1.1.5', 'gw': '100.1.1.6', 'plen': 24, }])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    tx_ports = dev_groups[tg_ports[0]][0]['name']
    rx_ports = [dev_groups[tg_ports[1]][0]['name'],
                dev_groups[tg_ports[2]][0]['name'],
                dev_groups[tg_ports[3]][0]['name']]

    mac_addr = {tg_ports[idx]: f'02:00:00:00:00:0{idx + 1}' for idx in range(4)}
    tx_port_mac = mac_addr[tg_ports[0]]

    # 4. Setup packet stream(s).
    if traffic_type == 'multicast':
        streams = {'Untagged multicast traffic': {
            'type': 'raw',
            'protocol': '802.1Q',
            'rate': 50,
            'ip_source': tx_ports,
            'ip_destination': rx_ports,
            'srcMac': tx_port_mac,
            'dstMac': '01:80:C2:00:00:00',
        }}

    elif traffic_type == 'unicast':
        streams = {'Untagged unicast stream': {
            'type': 'raw',
            'protocol': '802.1Q',
            'ip_source': tx_ports,
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcMac': tx_port_mac,
            'dstMac': mac_addr[tg_ports[3]]
        }}
        # Learning mac's stream
        streams.update({'Learning stream': {
            'type': 'raw',
            'protocol': '802.1Q',
            'ip_source': dev_groups[tg_ports[1]][0]['name'],
            'ip_destination': dev_groups[tg_ports[0]][0]['name'],
            'srcMac': mac_addr[tg_ports[1]],
            'dstMac': tx_port_mac
        }})
    else:
        streams = {'Untagged broadcast traffic': {
            'type': 'raw',
            'protocol': '802.1Q',
            'ip_source': tx_ports,
            'ip_destination': rx_ports,
            'srcMac': tx_port_mac,
            'dstMac': 'ff:ff:ff:ff:ff:ff'
        }}

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    # 5. Send traffic to rx_ports.
    if traffic_type == 'unicast':
        # Send traffic to learn MAC
        await tgen_utils_start_traffic(tgen_dev)
        await asyncio.sleep(1)
        await tgen_utils_stop_traffic(tgen_dev)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(5)
    await tgen_utils_stop_traffic(tgen_dev)

    # 6. Verify traffic.
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    ti_to_rx_port_map = get_traffic_port_vlan_mapping(streams, port_map, tg_ports)
    for row in stats.Rows:
        if row['Rx Port'] in ti_to_rx_port_map[row['Traffic Item']]:
            assert tgen_utils_get_loss(row) == 0.000, \
                f'No traffic for traffic item : {row["Traffic Item"]} on port {row["Rx Port"]}'
        else:
            assert tgen_utils_get_loss(row) == 100.000, \
                f'Traffic leak for traffic item: {row["Traffic Item"]} on port {row["Rx Port"]}'
