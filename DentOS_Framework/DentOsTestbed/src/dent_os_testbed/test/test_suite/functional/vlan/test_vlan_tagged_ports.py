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
    tgen_utils_traffic_generator_connect)

from dent_os_testbed.utils.test_utils.br_utils import (
    configure_bridge_setup,
    configure_vlan_setup,
    get_traffic_port_vlan_mapping)

pytestmark = [pytest.mark.suite_functional_vlan,
              pytest.mark.asyncio,
              pytest.mark.usefixtures("cleanup_bridges", "cleanup_tgen")]


@pytest.mark.parametrize("traffic_type", ["broadcast", "multicast", "unicast"])
async def test_vlan_tagged_ports_with_(testbed, traffic_type):
    """
    Test Name: VLAN tagged ports
    Test Suite: suite_functional_vlan
    Test Overview: Test packet forwarding with VLAN tagged ports
    Test Procedure:
    1. Configure bridge; enslave ports to bridge. Set bridge, ports to `up` state
    2. Set links to vlans per configuration (all ports tagged, mixed vlans)
        Port 1: vlan 22
                vlan 23,
                vlan 24, untagged, pvid
        Port 2:vlan 22
                vlan 23,
                vlan 24, untagged, pvid
        Port 3: vlan 22
                vlan 23,
                vlan 24, untagged, pvid
        Port 4:vlan 22
                vlan 23,
                vlan 24, untagged, pvid
    3. Setup broadcast packet stream(s) with vlans 1, 22, 23, 24 and untagged stream
    4. Send traffic
    5. Verify no packet loss and all transmitted traffic received based on packet type
    """

    # 1. Configure bridge; enslave ports to bridge. Set bridge, ports to `up` state
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgn connections")
        return
    device = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[device][0]
    dut_ports = tgen_dev.links_dict[device][1]

    await configure_bridge_setup(device, dut_ports)

    # 2. Set links to vlans per port_map configuration (all ports tagged, mixed vlans)
    packet_vids = ["X", 1, 22, 23, 24]  # VLAN tag number contained in the transmitted packet
    port_map = ({"port": 0, "settings": [{"vlan": 22, "untagged": False, "pvid": False},
                                         {"vlan": 23, "untagged": False, "pvid": False},
                                         {"vlan": 24, "untagged": False, "pvid": True}]},

                {"port": 1, "settings": [{"vlan": 22, "untagged": False, "pvid": False},
                                         {"vlan": 23, "untagged": False, "pvid": False},
                                         {"vlan": 24, "untagged": False, "pvid": True}]},

                {"port": 2, "settings": [{"vlan": 22, "untagged": False, "pvid": False},
                                         {"vlan": 23, "untagged": False, "pvid": False},
                                         {"vlan": 24, "untagged": False, "pvid": True}]},

                {"port": 3, "settings": [{"vlan": 22, "untagged": False, "pvid": False},
                                         {"vlan": 23, "untagged": False, "pvid": False},
                                         {"vlan": 24, "untagged": False, "pvid": True}]})

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
    mac = [f"02:00:00:00:00:0{idx + 1}" for idx in range(4)]

    # 3. Setup untagged, tagged (based on specified vlans) packet stream(s) per packet type
    if traffic_type == "broadcast":
        streams = {f"Traffic with VLAN ID: {vlan}": {
            "type": "raw",
            "protocol": "802.1Q",
            "ip_source": tx_ports,
            "ip_destination": rx_ports,
            "srcMac": mac[0],
            "dstMac": "ff:ff:ff:ff:ff:ff",
            "vlanID": vlan
        } for vlan in packet_vids if vlan != "X"}

        streams["Untagged traffic"] = {
            "type": "raw",
            "protocol": "802.1Q",
            "ip_source": tx_ports,
            "ip_destination": rx_ports,
            "srcMac": mac[0],
            "dstMac": "ff:ff:ff:ff:ff:ff"
        }
    elif traffic_type == "multicast":
        streams = {f"Traffic with VLAN ID: {vlan}": {
            "type": "raw",
            "protocol": "802.1Q",
            "rate": 10,
            "ip_source": tx_ports,
            "ip_destination": rx_ports,
            "srcMac": mac[0],
            "dstMac": "01:80:C2:00:00:00",
            "vlanID": vlan
        } for vlan in packet_vids if vlan != "X"}
        streams["Untagged traffic"] = {
            "type": "raw",
            "rate": 10,
            "protocol": "802.1Q",
            "ip_source": tx_ports,
            "ip_destination": rx_ports,
            "srcMac": mac[0],
            "dstMac": "01:80:C2:00:00:00"
        }
    else:
        streams = {}
        streams_to_learn = {}
        for vlan in packet_vids:
            streams.update({f"VLAN {vlan} from {mac[src]} to --> {mac[dst]}": {
                    "ip_source": dev_groups[tg_ports[src]][0]["name"],
                    "ip_destination": dev_groups[tg_ports[dst]][0]["name"],
                    "srcMac": mac[src],
                    "dstMac": mac[dst],
                    "type": "raw",
                    "vlan": vlan,
                    "protocol": "802.1Q"
                    } for src, dst in ((0, 1), (0, 2), (0, 3))
                })
            for port in port_map:
                if port["port"] == 0 or isinstance(vlan, int) is False:
                    continue
                streams_to_learn[f"From {tg_ports[port['port']]} -> {tg_ports[0]}: VLAN : {vlan} learning"] = {
                    "type": "raw",
                    "protocol": "802.1Q",
                    "ip_source": dev_groups[tg_ports[port['port']]][0]["name"],
                    "ip_destination": dev_groups[tg_ports[0]][0]["name"],
                    "srcMac": mac[port['port']],
                    "dstMac": mac[0],
                    "vlanID": vlan
                }
        streams.update(streams_to_learn)

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    # 4. Send traffic
    if traffic_type == "unicast":
        # Send traffic to learn MAC addresses
        await tgen_utils_start_traffic(tgen_dev)
        await asyncio.sleep(1)
        await tgen_utils_stop_traffic(tgen_dev)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(5)
    await tgen_utils_stop_traffic(tgen_dev)

    # 5. Verify traffic
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    ti_to_rx_port_map = get_traffic_port_vlan_mapping(streams, port_map, tg_ports)
    for row in stats.Rows:
        if row["Rx Port"] in ti_to_rx_port_map[row["Traffic Item"]]:
            assert tgen_utils_get_loss(row) == 0.000, \
                f'No traffic for traffic item : {row["Traffic Item"]} on port {row["Rx Port"]}'
        else:
            assert tgen_utils_get_loss(row) == 100.000, \
                f'Traffic leak for traffic item: {row["Traffic Item"]} on port {row["Rx Port"]}'
