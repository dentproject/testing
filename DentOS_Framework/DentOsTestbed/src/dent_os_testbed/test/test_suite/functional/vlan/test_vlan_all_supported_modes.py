import asyncio

import pytest
from dent_os_testbed.utils.test_utils.tgen_utils import (tgen_utils_get_dent_devices_with_tgen,
                                                         tgen_utils_setup_streams, tgen_utils_start_traffic,
                                                         tgen_utils_stop_traffic, tgen_utils_get_traffic_stats,
                                                         tgen_utils_get_loss, tgen_utils_dev_groups_from_config,
                                                         tgen_utils_traffic_generator_connect, )
from dent_os_testbed.utils.test_utils.br_utils import (configure_bridge_setup, configure_vlan_setup,
                                                       get_traffic_port_vlan_mapping)

pytestmark = [pytest.mark.suite_functional_vlan,
              pytest.mark.asyncio,
              pytest.mark.usefixtures("cleanup_bridges", "cleanup_tgen")]

# VLAN tag number contained in the transmitted packet
packet_vids = ["X", 1, 2, 3, 4]
port_map = ({"port": 0, "settings": [{"vlan": 2, "untagged": False, "pvid": False},
                                     {"vlan": 3, "untagged": True, "pvid": False},
                                     {"vlan": 4, "untagged": True, "pvid": True}]},
            {"port": 1, "settings": [{"vlan": 2, "untagged": False, "pvid": False}]},
            {"port": 2, "settings": [{"vlan": 3, "untagged": True, "pvid": True}]},
            {"port": 3, "settings": [{"vlan": 4, "untagged": True, "pvid": True}]})


async def test_vlan_all_supported_modes_broadcast(testbed):
    """
    Test Name: Broadcast when all supported VLAN modes are configured
    Test Suite: suite_functional_vlan
    Test Overview: Test broadcast packet forwarding when all supported VLAN modes are configured
    Test Procedure:
    1. Initiate test params.
    2. Set links to vlans.
    3. Map receiving and non receiving dut_ports.
        Port 1 -> tx_port
        Ports 2, 3, 4 -> rx_ports
    4. Setup packet stream(s) for the broadcast packet:
    5. Send traffic to rx_ports.
    6. Verify traffic on receiving ports.
    """

    # 1. Initiate test params.
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip("The testbed does not have enough dent with tgen connections")
    device = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[device][0]
    dut_ports = tgen_dev.links_dict[device][1]

    await configure_bridge_setup(device, dut_ports)

    # 2. Set links to vlans.
    await configure_vlan_setup(device, port_map, dut_ports)

    # 3. Map receiving and non receiving dut_ports.
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

    # 4. Setup packet stream(s).
    streams = {f"traffic with VLAN ID: {vlan}": {
        "type": "raw",
        "protocol": "802.1Q",
        "ip_source": tx_ports,
        "ip_destination": rx_ports,
        "srcMac": "aa:bb:cc:dd:ee:ff",
        "dstMac": "ff:ff:ff:ff:ff:ff",
        "vlanID": vlan
    } for vlan in packet_vids if vlan != "X"}

    streams.update({"Untagged traffic": {
        "type": "raw",
        "protocol": "802.1Q",
        "ip_source": tx_ports,
        "ip_destination": rx_ports,
        "srcMac": "aa:bb:cc:dd:ee:ff",
        "dstMac": "ff:ff:ff:ff:ff:ff",
    }})

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    # 5. Send traffic to rx_ports.
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(5)
    await tgen_utils_stop_traffic(tgen_dev)

    # 6. Verify traffic.
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    ti_to_rx_port_map = get_traffic_port_vlan_mapping(streams, port_map, tg_ports)
    for row in stats.Rows:
        if row["Rx Port"] in ti_to_rx_port_map[row["Traffic Item"]]:
            assert tgen_utils_get_loss(row) == 0.000, \
                f'No traffic for traffic item : {row["Traffic Item"]} on port {row["Rx Port"]}'
        else:
            assert tgen_utils_get_loss(row) == 100.000, \
                f'Traffic leak for traffic item: {row["Traffic Item"]} on port {row["Rx Port"]}'


async def test_vlan_all_supported_modes_multicast(testbed):
    """
    Test Name: Multicast when all supported VLAN modes configured
    Test Suite: suite_functional_vlan
    Test Overview: Test multicast packet forwarding when all supported VLAN modes are configured
    Test Procedure:
    1. Initiate test params.
    2. Set links to vlans.
    3. Map receiving and non receiving dut_ports.
        Port 1 -> tx_port
        Ports 2, 3, 4 -> rx_ports
    4. Setup packet stream(s) for the multicast packet:
    5. Send traffic to rx_ports.
    6. Verify traffic on receiving ports.
    """

    # 1. Initiate test params.
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip("The testbed does not have enough dent with tgen connections")
    device = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[device][0]
    dut_ports = tgen_dev.links_dict[device][1]

    await configure_bridge_setup(device, dut_ports)

    # 2. Set links to vlans.
    await configure_vlan_setup(device, port_map, dut_ports)

    # 3. Map receiving and non receiving dut_ports.
    dev_groups = tgen_utils_dev_groups_from_config(
        [{"ixp": tg_ports[0], "ip": "100.1.1.2", "gw": "100.1.1.6", "plen": 24, },
         {"ixp": tg_ports[1], "ip": "100.1.1.3", "gw": "100.1.1.6", "plen": 24, },
         {"ixp": tg_ports[2], "ip": "100.1.1.4", "gw": "100.1.1.6", "plen": 24, },
         {"ixp": tg_ports[3], "ip": "100.1.1.5", "gw": "100.1.1.6", "plen": 24, }])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    tx_ports = dev_groups[tg_ports[0]][0]["name"]
    rx_ports = [dev_groups[tg_ports[3]][0]["name"],
                dev_groups[tg_ports[1]][0]["name"],
                dev_groups[tg_ports[2]][0]["name"]]

    # 4. Setup packet stream(s).
    streams = {f"traffic with VLAN ID: {vlan}": {
        "type": "raw",
        "rate": 10,
        "protocol": "802.1Q",
        "ip_source": tx_ports,
        "ip_destination": rx_ports,
        "srcMac": "aa:bb:cc:dd:ee:ff",
        "dstMac": "01:80:C2:00:00:00",
        "vlanID": vlan
    } for vlan in packet_vids if vlan != "X"}

    streams.update({"Untagged traffic": {
        "type": "raw",
        "rate": 10,
        "protocol": "802.1Q",
        "ip_source": tx_ports,
        "ip_destination": rx_ports,
        "srcMac": "aa:bb:cc:dd:ee:ff",
        "dstMac": "01:80:C2:00:00:00",
    }})

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    # 5. Send traffic to rx_ports.
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(5)
    await tgen_utils_stop_traffic(tgen_dev)

    # 6. Verify traffic.
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    ti_to_rx_port_map = get_traffic_port_vlan_mapping(streams, port_map, tg_ports)
    for row in stats.Rows:
        if row["Rx Port"] in ti_to_rx_port_map[row["Traffic Item"]]:
            assert tgen_utils_get_loss(row) == 0.000, \
                f'No traffic for traffic item : {row["Traffic Item"]} on port {row["Rx Port"]}'
        else:
            assert tgen_utils_get_loss(row) == 100.000, \
                f'Traffic leak for traffic item: {row["Traffic Item"]} on port {row["Rx Port"]}'


async def test_vlan_all_supported_modes_unicast(testbed):
    """
    Test Name: Unicast  when all supported VLAN modes configured
    Test Suite: suite_functional_vlan
    Test Overview:  Test unicast packet forwarding when all supported VLAN modes are configured
    Test Procedure:
    1. Initiate test params.
    2. Set links to vlans.
    3. Map receiving and non receiving dut_ports.
        Port 1 -> tx_port
        Port 2 -> rx_port
    4. Setup packet stream(s) for the unicast packet:
    5. Send traffic to rx_ports.
    6. Verify traffic.
    """

    # 1. Initiate test params.
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip("The testbed does not have enough dent with tgen connections")
    device = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[device][0]
    dut_ports = tgen_dev.links_dict[device][1]
    traffic_duration = 5
    tx_port = 0

    await configure_bridge_setup(device, dut_ports)

    # 2. Set links to vlans.
    await configure_vlan_setup(device, port_map, dut_ports)

    # 3. Map receiving and non receiving dut_ports.
    dev_groups = tgen_utils_dev_groups_from_config(
        [{"ixp": tg_ports[0], "ip": "100.1.1.2", "gw": "100.1.1.6", "plen": 24, },
         {"ixp": tg_ports[1], "ip": "100.1.1.3", "gw": "100.1.1.6", "plen": 24, },
         {"ixp": tg_ports[2], "ip": "100.1.1.4", "gw": "100.1.1.6", "plen": 24, },
         {"ixp": tg_ports[3], "ip": "100.1.1.5", "gw": "100.1.1.6", "plen": 24, }])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    tx_ports = dev_groups[tg_ports[0]][0]["name"]
    rx_ports = [dev_groups[tg_ports[x]][0]["name"] for x in range(1, 4)]

    mac = {tg_ports[idx]: f"02:00:00:00:00:0{idx + 1}" for idx in range(4)}

    vlan_to_mac = {
        2: "02:00:00:00:00:02",
        3: "02:00:00:00:00:03",
        4: "02:00:00:00:00:04",
        "X": "02:00:00:00:00:04",
        1: "02:00:00:00:00:04"
    }

    # 4. Setup packet stream(s).
    streams = {f"{tg_ports[0]} -> {vlan}": {
        "type": "raw",
        "protocol": "802.1Q",
        "ip_source": tx_ports,
        "ip_destination": rx_ports,
        "srcMac": mac[tg_ports[0]],
        "dstMac": vlan_to_mac[vlan],
        "vlanID": vlan,
    } for vlan in packet_vids if vlan != "X"}

    streams.update({f"{tg_ports[0]} -> X": {
        "type": "raw",
        "protocol": "802.1Q",
        "ip_source": tx_ports,
        "ip_destination": rx_ports,
        "srcMac": mac[tg_ports[0]],
        "dstMac": mac[tg_ports[3]]
    }})

    streams_to_learn = {}
    for port in port_map:
        if port["port"] == tx_port or isinstance(port["port"], int) is False:
            continue
        streams_to_learn.update({f"{tg_ports[port['port']]} -> {tg_ports[0]}": {
            "type": "raw",
            "protocol": "802.1Q",
            "ip_source": dev_groups[tg_ports[port['port']]][0]["name"],
            "ip_destination": dev_groups[tg_ports[tx_port]][0]["name"],
            "srcMac": vlan_to_mac[port['settings'][0]['vlan']],
            "dstMac": mac[tg_ports[0]],
            "vlanID": port['settings'][0]['vlan']
        }})

    streams.update(streams_to_learn)
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    # 5. Send traffic to rx_ports.
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(1)
    await tgen_utils_stop_traffic(tgen_dev)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # 6. Verify traffic.
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")

    ti_to_rx_port_map = get_traffic_port_vlan_mapping(streams, port_map, tg_ports)
    for row in stats.Rows:
        if row["Rx Port"] in ti_to_rx_port_map[row["Traffic Item"]]:
            assert tgen_utils_get_loss(row) == 0.000, \
                f'No traffic for traffic item : {row["Traffic Item"]} on port {row["Rx Port"]}'
        else:
            assert tgen_utils_get_loss(row) == 100.000, \
                f'Traffic leak for traffic item: {row["Traffic Item"]} on port {row["Rx Port"]}'
