import asyncio
import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink
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
    configure_bridge_setup,
    configure_vlan_setup,
    get_traffic_port_vlan_mapping)

pytestmark = [pytest.mark.suite_functional_vlan,
              pytest.mark.asyncio,
              pytest.mark.usefixtures("cleanup_bridges", "cleanup_tgen")]

packet_vids = ['X', 1, 2]  # VLAN tag number contained in the transmitted packet
port_map = ({"port": 0, "settings": [{"vlan": 1, "untagged": True, "pvid": True}]},
            {"port": 1, "settings": [{"vlan": 1, "untagged": True, "pvid": True}]},
            {"port": 2, "settings": [{"vlan": 1, "untagged": True, "pvid": True}]},
            {"port": 3, "settings": [{"vlan": 1, "untagged": True, "pvid": True}]})


def set_up_traffic_streams(traffic_type, tg_ports, dev_groups):
    tx_ports = dev_groups[tg_ports[0]][0]["name"]
    rx_ports = [dev_groups[tg_ports[1]][0]["name"],
                dev_groups[tg_ports[2]][0]["name"],
                dev_groups[tg_ports[3]][0]["name"]]

    src_mac = "02:00:00:00:00:01"
    dst_mac = {"broadcast": "ff:ff:ff:ff:ff:ff",
               "multicast": "01:80:C2:00:00:00",
               "unknown_unicast": "02:00:00:00:00:02",
               "unicast": "02:00:00:00:00:04"}

    if traffic_type == "unicast":
        streams = {f"{tg_ports[0]} -> {vlan}": {
            "type": "raw",
            "protocol": "802.1Q",
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": [dev_groups[tg_ports[3]][0]["name"]],
            "src_mac": src_mac,
            "dst_mac": dst_mac[traffic_type],
            "vlanID": vlan
        } for vlan in packet_vids if vlan != "X"}

        streams[f"{tg_ports[0]} -> X"] = {
            "type": "raw",
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": [dev_groups[tg_ports[3]][0]["name"]],
            "src_mac": src_mac,
            "dst_mac": dst_mac[traffic_type]
        }
        streams[f'{tg_ports[3]} -> {tg_ports[0]}'] = {
            "type": "raw",
            "protocol": "802.1Q",
            "ip_source": dev_groups[tg_ports[3]][0]["name"],
            "ip_destination": dev_groups[tg_ports[0]][0]["name"],
            "src_mac":  dst_mac[traffic_type],
            "dst_mac": src_mac,
            "vlanID": 1
        }
        return streams

    streams = {f"Traffic with VLAN ID: {vlan}": {
            "type": "raw",
            "protocol": "802.1Q",
            "ip_source": tx_ports,
            "ip_destination": rx_ports,
            "src_mac": src_mac,
            "dst_mac": dst_mac[traffic_type],
            "vlanID": vlan
        } for vlan in packet_vids if vlan != "X"}
    streams["Untagged traffic"] = {
        "type": "raw",
        "ip_source": tx_ports,
        "ip_destination": rx_ports,
        "src_mac": src_mac,
        "dst_mac": dst_mac[traffic_type]
    }
    if traffic_type == "multicast":
        for stream in streams:
            streams[stream].update({"rate": 50})
    return streams


@pytest.mark.parametrize("traffic_type", ["broadcast", "multicast", "unicast", "unknown_unicast"])
async def test_vlan_default_configuration_with_(testbed, traffic_type):
    """
    Test Name: VLAN default configuration
    Test Suite: suite_functional_vlan
    Test Overview: Test packet forwarding with VLAN default configuration
    Test Procedure:
    1. Configure bridge
    2. Enslave links to bridge and set to 'up' state
    3. Setup packet stream(s)
        - stream with vlan 1, 2
        - untagged stream
    4. Send traffic
    5. Verify traffic loss on receiving port(s) per packet type
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgn connections")
        return
    device = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[device][0]
    dut_ports = tgen_dev.links_dict[device][1]
    bridge = "br0"

    # 1. Configure bridge
    out = await IpLink.add(input_data=[{device: [{
        "device": bridge,
        "type": "bridge",
        "vlan_filtering": 1
        }]
    }])
    assert out[0][device]["rc"] == 0, f"Failed creating bridge."

    await IpLink.set(input_data=[{device: [{"device": bridge, "operstate": "up"}]}])
    assert out[0][device]["rc"] == 0, f"Failed setting bridge to state UP."

    # 2. Enslave links to bridge and set to 'up' state
    out = await IpLink.set(input_data=[{device: [{
        "device": port,
        "operstate": "up",
        "master": bridge
    } for port in dut_ports]}])
    assert out[0][device]["rc"] == 0, f"Failed setting link to state UP."

    # Configure ixia ports
    dev_groups = tgen_utils_dev_groups_from_config([
        {"ixp": tg_ports[0], "ip": "100.1.1.2", "gw": "100.1.1.6", "plen": 24, },
        {"ixp": tg_ports[1], "ip": "100.1.1.3", "gw": "100.1.1.6", "plen": 24, },
        {"ixp": tg_ports[2], "ip": "100.1.1.4", "gw": "100.1.1.6", "plen": 24, },
        {"ixp": tg_ports[3], "ip": "100.1.1.5", "gw": "100.1.1.6", "plen": 24, }])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    # 3. Setup packet stream(s) with specified vlan tags/untagged
    streams = set_up_traffic_streams(traffic_type, tg_ports, dev_groups)

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    # 4. Send traffic
    # Sending traffic to learn MAC addresses for unicast traffic
    if traffic_type == "unicast":
        await tgen_utils_start_traffic(tgen_dev)
        await asyncio.sleep(1)
        await tgen_utils_stop_traffic(tgen_dev)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(5)
    await tgen_utils_stop_traffic(tgen_dev)

    # 5. Verify traffic loss on rx_ports per port_map configuration and packet type
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    ti_to_rx_port_map = get_traffic_port_vlan_mapping(streams, port_map, tg_ports)
    for row in stats.Rows:
        if row["Rx Port"] in ti_to_rx_port_map[row["Traffic Item"]]:
            assert tgen_utils_get_loss(row) == 0.000, \
                f'No traffic for traffic item : {row["Traffic Item"]} on port {row["Rx Port"]}'
        else:
            assert tgen_utils_get_loss(row) == 100.000, \
                f'Traffic leak for traffic item: {row["Traffic Item"]} on port {row["Rx Port"]}'


async def test_vlan_basic_functionality(testbed):
    """
    Test Name: VLAN basic functionality
    Test Suite: suite_functional_vlan
    Test Overview: Test VLAN basic functionality with broadcast packet forwarding
    Test Procedure:
    1. Configure bridge; enslave ports to bridge. Set bridge, ports to `up` state
    2. Set links to vlans: all ports untagged, mixed vlans
        Ports 1, 2, 3 : VLAN 1, untagged, pvid
        Port 4: VLAN 2, untagged
    4. Setup broadcast packet stream(s) without VLAN tag
    5. Send traffic
    6. Verify traffic:
        - traffic loss on port 4
        - no traffic loss on port 2, 3
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgn connections")
        return
    device = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[device][0]
    dut_ports = tgen_dev.links_dict[device][1]

    # 1. Configures bridge; enslave ports to bridge. Set bridge, ports to `up` state
    await configure_bridge_setup(device, dut_ports)

    # 2. Set links to vlans per port_map configuration (all ports untagged, mixed vlans)
    port_setup = ({"port": 0, "settings": [{"vlan": 1, "untagged": True, "pvid": True}]},
                  {"port": 1, "settings": [{"vlan": 1, "untagged": True, "pvid": True}]},
                  {"port": 2, "settings": [{"vlan": 1, "untagged": True, "pvid": True}]},
                  {"port": 3, "settings": [{"vlan": 2, "untagged": True, "pvid": False}]})

    await configure_vlan_setup(device, port_setup, dut_ports)

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

    # 3. Setup broadcast packet stream(s) without VLAN tag.
    streams = {f"Untagged traffic": {
        "type": "raw",
        "ip_source": tx_ports,
        "ip_destination": rx_ports,
        "srcMac": "02:00:00:00:00:01",
        "dstMac": "ff:ff:ff:ff:ff:ff"
    }}

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    # 5. Send traffic
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(5)
    await tgen_utils_stop_traffic(tgen_dev)

    # 6. Verify traffic
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    ti_to_rx_port_map = get_traffic_port_vlan_mapping(streams, port_map, tg_ports)
    for row in stats.Rows:
        if row["Rx Port"] in ti_to_rx_port_map[row["Traffic Item"]]:
            assert tgen_utils_get_loss(row) == 0.000, \
                f'No traffic for traffic item : {row["Traffic Item"]} on port {row["Rx Port"]}'
        else:
            assert tgen_utils_get_loss(row) == 100.000, \
                f'Traffic leak for traffic item: {row["Traffic Item"]} on port {row["Rx Port"]}'


async def test_vlan_changing_default_pvid(testbed):
    """
    Test Name: Changing default VLAN pvid
    Test Suite: suite_functional_vlan
    Test Overview: Test broadcast packet forwarding with non-default pvid
    Test Procedure:
    1. Configure bridge; enslave ports to bridge. Set bridge, ports to `up` state
    2. Add ports to VLANs: all ports untagged, same vlans
        Ports 1, 2, 3, 4 : vlan 4094, untagged, pvid
    3. Setup broadcast packet streams: untagged, tagged with port VLAN, tagged with wrong VLAN
    4. Send traffic
    5. Verify traffic:
        - traffic loss on all ports for traffic with wrong VLAN;
        - no traffic loss on all ports for traffic with port VLAN;
        - no traffic loss on all ports for untagged traffic
    """

    # 1. Configure bridge; enslave ports to bridge. Set bridge, ports to `up` state
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgn connections")
        return
    device = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[device][0]
    dut_ports = tgen_dev.links_dict[device][1]
    vlans = ['X', 4094, 2]  # VLAN tag number contained in the transmitted packet
    non_default_pvid = vlans[-1]

    await configure_bridge_setup(device, dut_ports, default_pvid=non_default_pvid)

    # 2. Set links to vlans per port_map configuration (all ports untagged, same vlan)
    port_setup = ({"port": 0, "settings": [{"vlan": 4094, "untagged": True, "pvid": True}]},
                  {"port": 1, "settings": [{"vlan": 4094, "untagged": True, "pvid": True}]},
                  {"port": 2, "settings": [{"vlan": 4094, "untagged": True, "pvid": True}]},
                  {"port": 3, "settings": [{"vlan": 4094, "untagged": True, "pvid": True}]})
    await configure_vlan_setup(device, port_setup, dut_ports)

    dev_groups = tgen_utils_dev_groups_from_config([
        {"ixp": tg_ports[0], "ip": "100.1.1.2", "gw": "100.1.1.6", "plen": 24},
        {"ixp": tg_ports[1], "ip": "100.1.1.3", "gw": "100.1.1.6", "plen": 24},
        {"ixp": tg_ports[2], "ip": "100.1.1.4", "gw": "100.1.1.6", "plen": 24},
        {"ixp": tg_ports[3], "ip": "100.1.1.5", "gw": "100.1.1.6", "plen": 24}])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    tx_ports = dev_groups[tg_ports[0]][0]["name"]
    rx_ports = [dev_groups[tg_ports[1]][0]["name"],
                dev_groups[tg_ports[2]][0]["name"],
                dev_groups[tg_ports[3]][0]["name"]]

    # 3. Setup broadcast packet streams: untagged, tagged with port VLAN, tagged with wrong VLAN
    streams = {f"Traffic with VLAN ID: {vlan}": {
        "type": "raw",
        "protocol": "802.1Q",
        "ip_source": tx_ports,
        "ip_destination": rx_ports,
        "src_mac": "02:00:00:00:00:01",
        "dst_mac": "ff:ff:ff:ff:ff:ff",
        "vlanID": vlan
    } for vlan in packet_vids if vlan != "X"}

    streams["Untagged traffic"] = {
        "type": "raw",
        "ip_source": tx_ports,
        "ip_destination": rx_ports,
        "src_mac": "02:00:00:00:00:01",
        "dst_mac": "ff:ff:ff:ff:ff:ff"
    }

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    # 4. Send traffic
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(5)
    await tgen_utils_stop_traffic(tgen_dev)

    # 5. Verify traffic
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    ti_to_rx_port_map = get_traffic_port_vlan_mapping(streams, port_map, tg_ports, default_pvid=non_default_pvid)
    for row in stats.Rows:
        if row["Rx Port"] in ti_to_rx_port_map[row["Traffic Item"]]:
            assert tgen_utils_get_loss(row) == 0.000, \
                f'No traffic for traffic item : {row["Traffic Item"]} on port {row["Rx Port"]}'
        else:
            assert tgen_utils_get_loss(row) == 100.000, \
                f'Traffic leak for traffic item: {row["Traffic Item"]} on port {row["Rx Port"]}'
