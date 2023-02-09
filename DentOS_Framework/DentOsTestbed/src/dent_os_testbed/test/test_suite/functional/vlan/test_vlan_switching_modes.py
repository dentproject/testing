import asyncio
import pytest

from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan
from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_get_traffic_stats,
    tgen_utils_get_loss,
    tgen_utils_dev_groups_from_config,
    tgen_utils_traffic_generator_connect)
from dent_os_testbed.utils.test_utils.br_utils import (
    get_traffic_port_vlan_mapping,
    configure_bridge_setup,
    configure_vlan_setup)


pytestmark = [pytest.mark.suite_functional_vlan,
              pytest.mark.asyncio,
              pytest.mark.usefixtures("cleanup_bridges", "cleanup_tgen")]


async def test_vlan_switching_vlan_modes_via_cli(testbed):
    """
    Test Name: Switching port vlan modes via cli
    Test Suite: suite_functional_vlan
    Test Overview: Test broadcast packet forwarding after changing vlan port modes via cli
    Test Procedure:
    1. Create bridge; links. Set bridge, links to `up` state
    2. Set links to vlans per first configuration of VLAN modes.
        Port 1: vlan 2
                vlan 3, untagged,
                vlan 4, untagged, pvid
        Port 2: vlan 2
        Port 3: vlan 3 untagged
        Port 4: vlan 4, untagged, pvid
    3. Setup broadcast packet stream(s) with vlans 1, 2, 3, 4 and untagged stream
    4. Send traffic.
    5. Verify traffic per first configuration of VLAN modes.
    6. Remove dut ports from the VLAN's of the first configuration.
    7. Set links to new vlans per second configuration of vlan modes
        Port 1: vlan 5, untagged, pvid
                vlan 101, tagged,
                vlan 4094, untagged,
        Port 2: vlan 5, untagged, pvid
        Port 3: vlan 101, untagged, pvid
        Port 4: vlan 4094, untagged, pvid
    8. Setup broadcast packet stream(s) with vlans 0, 5, 101, 500, 4094 and untagged stream
    9. Send traffic.
    10. Verify traffic per second configuration of VLAN modes.
    """

    # 1. Create bridge; links. Set bridge, links to `up`
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgn connections")
        return
    device = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[device][0]
    dut_ports = tgen_dev.links_dict[device][1]

    packet_vids = ["X", 1, 2, 3, 4]
    port_map = ({"port": 0, "settings": [{"vlan": 2, "untagged": False, "pvid": False},
                                         {"vlan": 3, "untagged": True, "pvid": False},
                                         {"vlan": 4, "untagged": True, "pvid": True}]},
                {"port": 1, "settings": [{"vlan": 2, "untagged": False, "pvid": False}]},
                {"port": 2, "settings": [{"vlan": 3, "untagged": True, "pvid": True}]},
                {"port": 3, "settings": [{"vlan": 4, "untagged": True, "pvid": True}]})

    await configure_bridge_setup(device, dut_ports)

    # 2. Set links to vlans per first configuration of VLAN modes.
    await configure_vlan_setup(device, port_map, dut_ports)

    dev_groups = tgen_utils_dev_groups_from_config(
        [{"ixp": tg_ports[0], "ip": "100.1.1.2", "gw": "100.1.1.6", "plen": 24, },
         {"ixp": tg_ports[1], "ip": "100.1.1.3", "gw": "100.1.1.6", "plen": 24, },
         {"ixp": tg_ports[2], "ip": "100.1.1.4", "gw": "100.1.1.6", "plen": 24, },
         {"ixp": tg_ports[3], "ip": "100.1.1.5", "gw": "100.1.1.6", "plen": 24, }])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    tx_ports = dev_groups[tg_ports[0]][0]["name"]
    rx_ports = [dev_groups[tg_ports[1]][0]["name"],
                dev_groups[tg_ports[2]][0]["name"],
                dev_groups[tg_ports[3]][0]["name"]]

    # 3. Setup packet stream(s) per first configuration of VLAN modes.
    streams = {f"Traffic with VLAN ID: {vlan}": {
        "type": "raw",
        "protocol": "802.1Q",
        "ip_source": tx_ports,
        "ip_destination": rx_ports,
        "srcMac": "aa:bb:cc:dd:ee:ff",
        "dstMac": "ff:ff:ff:ff:ff:ff",
        "vlanID": vlan
    } for vlan in packet_vids if vlan != "X"}

    streams["Untagged traffic"] = {
        "type": "raw",
        "ip_source": tx_ports,
        "ip_destination": rx_ports,
        "srcMac": "aa:bb:cc:dd:ee:ff",
        "dstMac": "ff:ff:ff:ff:ff:ff",
    }

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    # 4. Send traffic.
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(5)
    await tgen_utils_stop_traffic(tgen_dev)

    # 5. Verify traffic per first configuration of VLAN modes.
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    ti_to_rx_port_map = get_traffic_port_vlan_mapping(streams, port_map, tg_ports)
    for row in stats.Rows:
        if row["Rx Port"] in ti_to_rx_port_map[row["Traffic Item"]]:
            assert tgen_utils_get_loss(row) == 0.000, \
                f'No traffic for traffic item : {row["Traffic Item"]} on port {row["Rx Port"]}'
        else:
            assert tgen_utils_get_loss(row) == 100.000, \
                f'Traffic leak for traffic item: {row["Traffic Item"]} on port {row["Rx Port"]}'

    # 6. Remove dut ports from the VLAN's of the first configuration.
    for port in port_map:
        out = await BridgeVlan.delete(input_data=[{device: [{
            "device": dut_ports[port["port"]],
            "vid": settings["vlan"]
        }] for settings in port["settings"]}])
        assert out[0][device]["rc"] == 0, f"Failed removing vlan from {port}"

    # 7. Set links to new vlans per second configuration of vlan modes
    second_packet_vids = ['X', 0, 5, 101, 500, 4094]
    second_conf_port_map = ({"port": 0, "settings": [{"vlan": 5, "untagged": True, "pvid": True},
                                                     {"vlan": 101, "untagged": False, "pvid": False},
                                                     {"vlan": 4094, "untagged": True, "pvid": False}]},
                            {"port": 1, "settings": [{"vlan": 5, "untagged": True, "pvid": True}]},
                            {"port": 2, "settings": [{"vlan": 101, "untagged": True, "pvid": True}]},
                            {"port": 3, "settings": [{"vlan": 4094, "untagged": True, "pvid": True}]})
    await configure_vlan_setup(device, second_conf_port_map, dut_ports)

    # 8. Setup packet stream(s) for the second configuration.
    second_conf_streams = {f"New configuration traffic with VLAN ID: {vlan}": {
        "type": "raw",
        "protocol": "802.1Q",
        "ip_source": tx_ports,
        "ip_destination": rx_ports,
        "srcMac": "aa:bb:cc:dd:ee:ff",
        "dstMac": "ff:ff:ff:ff:ff:ff",
        "vlanID": vlan
    } for vlan in second_packet_vids if vlan != "X"}

    second_conf_streams["New configuration untagged traffic"] = {
        "type": "raw",
        "ip_source": tx_ports,
        "ip_destination": rx_ports,
        "srcMac": "aa:bb:cc:dd:ee:ff",
        "dstMac": "ff:ff:ff:ff:ff:ff",
    }

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=second_conf_streams)

    # 9. Send traffic
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(5)
    await tgen_utils_stop_traffic(tgen_dev)

    # 10. Verify traffic.
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    ti_to_rx_port_map_second_conf = get_traffic_port_vlan_mapping(second_conf_streams, second_conf_port_map, tg_ports)

    for row in stats.Rows:
        # Skipping traffic items of the first configuration
        if row["Traffic Item"] in streams.keys():
            continue
        if row["Rx Port"] in ti_to_rx_port_map_second_conf[row["Traffic Item"]]:
            assert tgen_utils_get_loss(row) == 0.000, \
                f'No traffic for traffic item : {row["Traffic Item"]} on port {row["Rx Port"]}'
        else:
            assert tgen_utils_get_loss(row) == 100.000, \
                f'Traffic leak for traffic item: {row["Traffic Item"]} on port {row["Rx Port"]}'
