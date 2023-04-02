import re
import pytest
import asyncio

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.test.test_suite.functional.bridging.bridging_packet_types import get_streams

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_get_loss
)

from dent_os_testbed.utils.test_utils.tb_utils import (
    tb_device_tcpdump
)

pytestmark = [
    pytest.mark.suite_functional_bridging,
    pytest.mark.asyncio,
    pytest.mark.usefixtures("cleanup_bridges", "cleanup_tgen", "cleanup_ip_addrs")
]


async def test_bridging_bum_traffic_bridge_with_rif(testbed):
    """
    Test Name: test_bridging_bum_traffic_bridge_with_rif
    Test Suite: suite_functional_bridging
    Test Overview: Verify forwarding/drop/trap of different broadcast, unknown-unicast
                   and multicast traffic L2, IPv4 packet types within the same bridge domain.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1. Init bridge entity br0.
    2. Set ports swp1, swp2, swp3, swp4 master br0.
    3. Set entities swp1, swp2, swp3, swp4 UP state.
    4. Set bridge br0 admin state UP.
    5. Set ip address on bridge.
    6. Get self MAC address on ingress port swp1.
    7. Start tcpdump capture on DUT ingress port.
    8. Send different types of packets from source TG.
    9. Analyze counters: a) TX vs RX counters according to expected values;
                         b) Trapped packets to CPU.
    """

    bridge = "br0"
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip("The testbed does not have enough dent with tgen connections")
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 10
    prefix = "100.1.1.253"

    out = await IpLink.add(
        input_data=[{device_host_name: [
            {"device": bridge, "type": "bridge"}]}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify that bridge created.\n{out}"

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {"device": bridge, "operstate": "up"}]}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify that bridge set to 'UP' state.\n{out}"

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {"device": port, "master": bridge, "operstate": "up"} for port in ports]}])
    err_msg = f"Verify that bridge entities set to 'UP' state and links enslaved to bridge.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    out = await IpAddress.add(
        input_data=[{device_host_name: [
            {"dev": bridge, "prefix": f"{prefix}/24"}]}])
    assert out[0][device_host_name]["rc"] == 0, f"Failed to add IP address to bridge.\n{out}"

    out = await IpLink.show(input_data=[{device_host_name: [{"device": ports[0], "cmd_options": "-j"}]}],
                            parse_output=True)
    assert out[0][device_host_name]["rc"] == 0, f"Failed to display device attributes.\n{out}"

    dev_attributes = out[0][device_host_name]["parsed_output"]
    self_mac = dev_attributes[0]["address"]
    srcMac = "00:00:AA:00:00:01"

    address_map = (
        # swp port, tg port,    tg ip,     gw,        plen
        (ports[0], tg_ports[0], "1.1.1.2", "1.1.1.1", 24),
        (ports[1], tg_ports[1], "1.1.1.3", "1.1.1.1", 24)
    )

    dev_groups = tgen_utils_dev_groups_from_config(
        {"ixp": port, "ip": ip, "gw": gw, "plen": plen}
        for _, port, ip, gw, plen in address_map
    )

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    list_streams = get_streams(srcMac, self_mac, prefix, dev_groups, tg_ports)
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=list_streams)

    tcpdump = asyncio.create_task(tb_device_tcpdump(dent_dev, "swp1", "-n", count_only=False, timeout=5, dump=True))

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    expected_loss = {
        "Bridged_UnknownL2UC": 0,
        "BridgedLLDP": 100,
        "LACPDU": 100,
        "IPv4ToMe": 100,
        "ARP_Request_BC": 0,
        "ARP_Reply": 100,
        "IPv4_Broadcast": 0,
        "IPV4_SSH": 100,
        "IPV4_Telnet": 100,
        "Host_to_Host_IPv4": 100,
        "IPv4_ICMP_Request": 100,
        "IPv4_DCHP_BC": 0,
        "IPv4_Reserved_MC": 0,
        "IPv4_All_Systems_on_this_Subnet": 0,
        "IPv4_All_Routers_on_this_Subnet": 0,
        "IPv4_OSPFIGP": 0,
        "IPv4_RIP2_Routers": 0,
        "IPv4_EIGRP_Routers": 0,
        "IPv4_DHCP_Server/Relay_Agent": 0,
        "IPv4_VRRP": 0,
        "IPv4_IGMP": 0,
        "IPV4_BGP": 100
    }
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) == expected_loss[row["Traffic Item"]], \
            "Verify that traffic from swp1 to swp2 forwarded/not forwarded in accordance."

    await tcpdump
    print(f"TCPDUMP: packets={tcpdump.result()}")
    data = tcpdump.result()

    count_of_packets = re.findall(r"(\d+) packets (captured|received|dropped)", data)
    for count, type in count_of_packets:
        if type == "received":
            assert int(count) > 0, "Verify that packets are received by filter."
        if type == "captured" or type == "dropped":
            assert int(count) >= 0, "Verify that packets are captured and dropped by kernel."


async def test_bridging_bum_traffic_bridge_without_rif(testbed):
    """
    Test Name: test_bridging_bum_traffic_bridge_without_rif
    Test Suite: suite_functional_bridging
    Test Overview: Verify forwarding/drop/trap of different broadcast, unknown-unicast
                   and multicast traffic L2, IPv4 packet types within the same bridge domain.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1. Init bridge entity br0.
    2. Set ports swp1, swp2, swp3, swp4 master br0.
    3. Set entities swp1, swp2, swp3, swp4 UP state.
    4. Set bridge br0 admin state UP.
    5. Get self MAC address on ingress port swp1.
    6. Start tcpdump capture on DUT ingress port.
    7. Send different types of packets from source TG.
    8. Analyze counters: a) TX vs RX counters according to expected values;
                         b) Trapped packets to CPU.
    """

    bridge = "br0"
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip("The testbed does not have enough dent with tgen connections")
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 10
    prefix = "100.1.1.253"

    out = await IpLink.add(
        input_data=[{device_host_name: [
            {"device": bridge, "type": "bridge"}]}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify that bridge created.\n{out}"

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {"device": bridge, "operstate": "up"}]}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify that bridge set to 'UP' state.\n{out}"

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {"device": port, "master": bridge, "operstate": "up"} for port in ports]}])
    err_msg = f"Verify that bridge entities set to 'UP' state and links enslaved to bridge.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    out = await IpLink.show(input_data=[{device_host_name: [{"device": ports[0], "cmd_options": "-j"}]}],
                            parse_output=True)
    assert out[0][device_host_name]["rc"] == 0, f"Failed to display device attributes.\n{out}"

    dev_attributes = out[0][device_host_name]["parsed_output"]
    self_mac = dev_attributes[0]["address"]
    srcMac = "00:00:AA:00:00:01"

    address_map = (
        # swp port, tg port,    tg ip,     gw,        plen
        (ports[0], tg_ports[0], "1.1.1.2", "1.1.1.1", 24),
        (ports[1], tg_ports[1], "1.1.1.3", "1.1.1.1", 24)
    )

    dev_groups = tgen_utils_dev_groups_from_config(
        {"ixp": port, "ip": ip, "gw": gw, "plen": plen}
        for _, port, ip, gw, plen in address_map
    )

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    list_streams = get_streams(srcMac, self_mac, prefix, dev_groups, tg_ports)
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=list_streams)

    tcpdump = asyncio.create_task(tb_device_tcpdump(dent_dev, "swp1", "-n", count_only=False, timeout=5, dump=True))

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    expected_loss = {
        "Bridged_UnknownL2UC": 0,
        "BridgedLLDP": 100,
        "LACPDU": 100,
        "IPv4ToMe": 100,
        "ARP_Request_BC": 0,
        "ARP_Reply": 100,
        "IPv4_Broadcast": 0,
        "IPV4_SSH": 100,
        "IPV4_Telnet": 100,
        "Host_to_Host_IPv4": 100,
        "IPv4_ICMP_Request": 100,
        "IPv4_DCHP_BC": 0,
        "IPv4_Reserved_MC": 0,
        "IPv4_All_Systems_on_this_Subnet": 0,
        "IPv4_All_Routers_on_this_Subnet": 0,
        "IPv4_OSPFIGP": 0,
        "IPv4_RIP2_Routers": 0,
        "IPv4_EIGRP_Routers": 0,
        "IPv4_DHCP_Server/Relay_Agent": 0,
        "IPv4_VRRP": 0,
        "IPv4_IGMP": 0,
        "IPV4_BGP": 100
    }
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) == expected_loss[row["Traffic Item"]], \
            "Verify that traffic from swp1 to swp2 forwarded/not forwarded in accordance."

    await tcpdump
    print(f"TCPDUMP: packets={tcpdump.result()}")
    data = tcpdump.result()

    count_of_packets = re.findall(r"(\d+) packets (captured|received|dropped)", data)
    for count, type in count_of_packets:
        if type == "received":
            assert int(count) > 0, "Verify that packets are received by filter."
        if type == "captured" or type == "dropped":
            assert int(count) >= 0, "Verify that packets are captured and dropped by kernel."
