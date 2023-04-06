import asyncio
import pytest

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_get_traffic_stats,
    tgen_utils_get_loss,
    tgen_utils_dev_groups_from_config,
    tgen_utils_traffic_generator_connect,
    tgen_utils_get_egress_stats)

from dent_os_testbed.utils.test_utils.br_utils import (
    configure_bridge_setup,
    configure_vlan_setup)

pytestmark = [pytest.mark.suite_functional_vlan,
              pytest.mark.asyncio,
              pytest.mark.usefixtures('cleanup_bridges', 'cleanup_tgen')]


async def test_vlan_priority_tag(testbed):
    """
    Test Name: VLAN priority
    Test Suite: suite_functional_vlan
    Test Overview: Test packet forwarding with VLAN priority
    Test Procedure:
    1. Create bridge and set links to `Up` state
    2. Add two ports to the same VLAN in trunk  mode.
    3. Setup packet stream(s) for the unicast packet with packet vlan and priority.
    4. Send traffic.
    5. Verify no traffic loss on receiving port.
    6. Verify priority was not stripped from the packet.
    """

    # 1. Create bridge and set links to `Up` state
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    device = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[device][0]
    dut_ports = tgen_dev.links_dict[device][1]
    vlan_priority = 6
    vlan_id = 5

    await configure_bridge_setup(device, dut_ports)

    # 2. Insert links to VLAN's per port_map config
    port_map = ({'port': 0, 'settings': [{'vlan': vlan_id, 'untagged': False, 'pvid': True}]},
                {'port': 1, 'settings': [{'vlan': vlan_id, 'untagged': False, 'pvid': True}]})
    await configure_vlan_setup(device, port_map, dut_ports)

    dev_groups = tgen_utils_dev_groups_from_config(
        [{'ixp': tg_ports[0], 'ip': '100.1.1.2', 'gw': '100.1.1.6', 'plen': 24},
         {'ixp': tg_ports[1], 'ip': '100.1.1.3', 'gw': '100.1.1.6', 'plen': 24}])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    # 3. Setup packet stream(s) for the unicast packet with packet vlan and priority specified
    #  Enable egress tracking for the vlan and pcp
    tx_ports = dev_groups[tg_ports[0]][0]['name']
    rx_ports = dev_groups[tg_ports[1]][0]['name']

    streams = {f'Traffic with VLAN priority': {
        'type': 'raw',
        'protocol': '802.1Q',
        'ip_source': tx_ports,
        'ip_destination': rx_ports,
        'srcMac': '02:00:00:00:00:01',
        'dstMac': '02:00:00:00:00:02',
        'vlanID': vlan_id,
        'frame_rate_type': 'line_rate',
        'rate': 95,
        'vlanPriority': vlan_priority,
        'egress_track_by': ['vlan', 'pcp']
    }}

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    # 4. Send traffic
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(15)
    await tgen_utils_stop_traffic(tgen_dev)

    # 5. Verify no traffic loss on receiving ports.
    # 6. Verify priority was not stripped from the packet.
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) == 0.000, \
            f'No traffic for traffic item : {row["Traffic Item"]} on port {row["Rx Port"]}'
        egress_stats = await tgen_utils_get_egress_stats(tgen_dev, row)
        for idx, ege_row in enumerate(egress_stats.Rows):
            if idx == 0:
                continue
            assert int(ege_row['Egress Tracking 2']) == vlan_priority, 'No/Wrong VLAN priority in the packet'
            assert int(ege_row['Rx Frames']) == int(row['Tx Frames']), f'Traffic loss with vlan: {vlan_id}' \
                                                                       f'and vlan priority: {vlan_priority}'
