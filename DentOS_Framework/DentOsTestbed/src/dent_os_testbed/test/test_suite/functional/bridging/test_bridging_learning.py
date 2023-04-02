import pytest
import asyncio

from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan
from dent_os_testbed.lib.bridge.bridge_link import BridgeLink
from dent_os_testbed.lib.bridge.bridge_fdb import BridgeFdb
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
    pytest.mark.suite_functional_bridging,
    pytest.mark.asyncio,
    pytest.mark.usefixtures("cleanup_bridges", "cleanup_tgen")
]


async def test_bridging_learning_address(testbed):
    """
    Test Name: test_bridging_learning_address
    Test Suite: suite_functional_bridging
    Test Overview: Verify that bridge dynamic entries learning.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1, swp2, swp3, swp4 master br0.
    3.  Set bridge br0 admin state UP.
    4.  Set entities swp1, swp2, swp3, swp4 UP state.
    5.  Set ports swp1, swp2, swp3, swp4 learning ON.
    6.  Set ports swp1, swp2, swp3, swp4 flood OFF.
    7.  Send traffic to swp1, swp2, swp3, swp4 with source macs
        aa:bb:cc:dd:ee:11 aa:bb:cc:dd:ee:12
        aa:bb:cc:dd:ee:13 aa:bb:cc:dd:ee:14 accordingly.
    8.  Verify that addresses have been learned.
    """

    bridge = "br0"
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip("The testbed does not have enough dent with tgen connections")
    device_host_name = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 5

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

    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {"device": port, "learning": True, "flood": False} for port in ports]}])
    err_msg = f"Verify that entities set to learning 'ON' and flooding 'OFF' state.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    address_map = (
        # swp port, tg port,    tg ip,     gw,        plen
        (ports[0], tg_ports[0], "1.1.1.2", "1.1.1.1", 24),
        (ports[1], tg_ports[1], "2.2.2.2", "2.2.2.1", 24),
        (ports[2], tg_ports[2], "3.3.3.2", "3.3.3.1", 24),
        (ports[3], tg_ports[3], "4.4.4.2", "4.4.4.1", 24),
    )

    dev_groups = tgen_utils_dev_groups_from_config(
        {"ixp": port, "ip": ip, "gw": gw, "plen": plen}
        for _, port, ip, gw, plen in address_map
    )

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    list_macs = ["aa:bb:cc:dd:ee:11", "aa:bb:cc:dd:ee:12",
                 "aa:bb:cc:dd:ee:13", "aa:bb:cc:dd:ee:14"]

    streams = {
        f"bridge_{dst + 1}": {
            "ip_source": dev_groups[tg_ports[src]][0]["name"],
            "ip_destination": dev_groups[tg_ports[dst]][0]["name"],
            "srcMac": list_macs[src],
            "dstMac": list_macs[dst],
            "type": "raw",
            "protocol": "802.1Q",
        } for src, dst in ((3, 0), (2, 1), (1, 2), (0, 3))
    }

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Traffic Item Statistics")
    for row in stats.Rows:
        assert int(row["Tx Frames"]) > 0, f'Failed>Ixia should transmit traffic: {row["Tx Frames"]}'

    out = await BridgeFdb.show(input_data=[{device_host_name: [{"options": "-j"}]}],
                               parse_output=True)
    assert out[0][device_host_name]["rc"] == 0, "Failed to get fdb entry."

    fdb_entries = out[0][device_host_name]["parsed_output"]
    learned_macs = [en["mac"] for en in fdb_entries if "mac" in en]
    for mac in list_macs:
        err_msg = "Verify that source macs have been learned."
        assert mac in learned_macs, err_msg


async def test_bridging_learning_address_rate(testbed):
    """
    Test Name: test_bridging_learning_address_rate
    Test Suite: suite_functional_bridging
    Test Overview: Verify that no one's packets were flooded into port 3.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1, swp2, swp3, swp4 master br0.
    3.  Set entities swp1, swp2, swp3, swp4 UP state.
    4.  Set bridge br0 admin state UP.
    5.  Send traffic to swp1 to learn source increment address
        00:00:00:00:00:35 with step '00:00:00:00:10:00' and count 1500.
    6.  Send traffic to swp2 with destination increment address
        00:00:00:00:00:35 with step '00:00:00:00:10:00' and count 1500.
    7.  Verify that there was not flooding to swp3.
    """

    bridge = "br0"
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 3)
    if not tgen_dev or not dent_devices:
        pytest.skip("The testbed does not have enough dent with tgen connections")
    device_host_name = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 5
    mac_count = 1500
    pps_value = 1000

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
    err_msg = f"Verify that bridge, bridge entities set to 'UP' state.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    address_map = (
        # swp port, tg port,    tg ip,     gw,        plen
        (ports[0], tg_ports[0], "1.1.1.2", "1.1.1.1", 24),
        (ports[1], tg_ports[1], "1.1.1.3", "1.1.1.1", 24),
        (ports[2], tg_ports[2], "1.1.1.4", "1.1.1.1", 24)
    )

    dev_groups = tgen_utils_dev_groups_from_config(
        {"ixp": port, "ip": ip, "gw": gw, "plen": plen}
        for _, port, ip, gw, plen in address_map
    )

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    streams = {
        "streamA": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcMac": {"type": "increment",
                       "start": "00:00:00:00:00:35",
                       "step": "00:00:00:00:10:00",
                       "count": mac_count},
            "dstMac": "aa:bb:cc:dd:ee:11",
            "protocol": "802.1Q",
            "rate": pps_value,
            "type": "raw",
        },
        "streamB": {
            "ip_source": dev_groups[tg_ports[1]][0]["name"],
            "ip_destination": dev_groups[tg_ports[0]][0]["name"],
            "srcMac": "aa:bb:cc:dd:ee:12",
            "dstMac": {"type": "increment",
                       "start": "00:00:00:00:00:35",
                       "step": "00:00:00:00:10:00",
                       "count": mac_count},
            "protocol": "802.1Q",
            "rate": pps_value,
            "type": "raw",
        }
    }

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    for row in stats.Rows:
        if row["Traffic Item"] == "streamA" and row["Rx Port"] == tg_ports[0]:
            assert tgen_utils_get_loss(row) == 0.000, \
                "Verify that traffic from swp2 to swp1 forwarded."
        if row["Traffic Item"] == "streamB" and row["Rx Port"] == tg_ports[1]:
            assert tgen_utils_get_loss(row) == 0.000, \
                "Verify that traffic from swp3 to swp2 forwarded."
        if row["Rx Port"] == tg_ports[2]:
            assert tgen_utils_get_loss(row) == 100.000, \
                "Verify that traffic to swp3 not forwarded."


async def test_bridging_learning_illegal_address(testbed):
    """
    Test Name: test_bridging_learning_illegal_address
    Test Suite: suite_functional_bridging
    Test Overview: Verify that bridge is not learning illegal address.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1, swp2, swp3, swp4 master br0.
    3.  Set entities swp1, swp2, swp3, swp4 UP state.
    4.  Set bridge br0 admin state UP.
    5.  Set ports swp1, swp2, swp3, swp4 learning ON.
    6.  Set ports swp1, swp2, swp3, swp4 flood OFF.
    7.  Send traffic by TG with illegal addresses.
    8.  Verify that illegal addresses haven't been learned.
    """

    bridge = "br0"
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip("The testbed does not have enough dent with tgen connections")
    device_host_name = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 5

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

    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {"device": port, "learning": True, "flood": False} for port in ports]}])
    err_msg = f"Verify that entities set to learning 'ON' and flooding 'OFF' state.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    address_map = (
        # swp port, tg port,    tg ip,     gw,        plen
        (ports[0], tg_ports[0], "1.1.1.2", "1.1.1.1", 24),
        (ports[1], tg_ports[1], "2.2.2.2", "2.2.2.1", 24),
        (ports[2], tg_ports[2], "3.3.3.2", "3.3.3.1", 24),
        (ports[3], tg_ports[3], "4.4.4.2", "4.4.4.1", 24),
    )

    dev_groups = tgen_utils_dev_groups_from_config(
        {"ixp": port, "ip": ip, "gw": gw, "plen": plen}
        for _, port, ip, gw, plen in address_map
    )

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    streams = {
        "all_zeros": {
            "ip_source": dev_groups[tg_ports[3]][0]["name"],
            "ip_destination": dev_groups[tg_ports[0]][0]["name"],
            "srcMac": "00:00:00:00:00:00",
            "dstMac": "01:00:00:00:00:00",
            "type": "raw",
            "protocol": "802.1Q",
        },
        "broadcast": {
            "ip_source": dev_groups[tg_ports[1]][0]["name"],
            "ip_destination": dev_groups[tg_ports[2]][0]["name"],
            "srcMac": "ff:ff:ff:ff:ff:ff",
            "dstMac": "01:00:00:00:00:00",
            "type": "raw",
            "protocol": "802.1Q",
        },
        "multicast_1": {
            "ip_source": dev_groups[tg_ports[2]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcMac": "01:00:00:00:00:00",
            "dstMac": "33:aa:aa:aa:aa:aa",
            "type": "raw",
            "protocol": "802.1Q",
        },
        "multicast_2": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[3]][0]["name"],
            "srcMac": "01:00:00:00:00:00",
            "dstMac": "ff:ff:ff:ff:ff:ff",
            "type": "raw",
            "protocol": "802.1Q",
        },
    }

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    for row in stats.Rows:
        if row["Traffic Item"] == "all_zeros" and row["Rx Port"] == tg_ports[0]:
            assert tgen_utils_get_loss(row) == 0.000, \
                "Verify that traffic from swp4 to swp1 forwarded."
        if row["Traffic Item"] == "broadcast" and row["Rx Port"] == tg_ports[2]:
            assert tgen_utils_get_loss(row) == 100.000, \
                "Verify that traffic from swp2 to swp3 not forwarded."
        if row["Traffic Item"] == "multicast_1" and row["Rx Port"] == tg_ports[1]:
            assert tgen_utils_get_loss(row) == 100.000, \
                "Verify that traffic from swp3 to swp2 not forwarded."
        if row["Traffic Item"] == "multicast_2" and row["Rx Port"] == tg_ports[3]:
            assert tgen_utils_get_loss(row) == 100.000, \
                "Verify that traffic from swp1 to swp4 not forwarded."

    out = await BridgeFdb.show(input_data=[{device_host_name: [{"options": "-j"}]}],
                               parse_output=True)
    assert out[0][device_host_name]["rc"] == 0, "Failed to get fdb entry."

    fdb_entries = out[0][device_host_name]["parsed_output"]
    learned_macs = [en["mac"] for en in fdb_entries if "mac" in en]
    illegal_address = ["00:00:00:00:00:00", "ff:ff:ff:ff:ff:ff", "01:00:00:00:00:00"]
    for mac in illegal_address:
        err_msg = "Verify that source macs have not been learned due to illegal address."
        assert mac not in learned_macs, err_msg


async def test_bridging_relearning_on_different_vlans(testbed):
    """
    Test Name: test_bridging_relearning_on_different_vlans
    Test Suite: suite_functional_bridging
    Test Overview: Verify that mac addresses relearning on different vlans.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1. Init bridge entity br0.
    2. Set br0 ageing time to 600 seconds [default is 300 seconds].
    3. Set ports swp1, swp2, swp3, swp4 master br0.
    4. Set bridge br0 admin state UP.
    5. Set entities swp1, swp2, swp3, swp4 UP state.
    6. Add interfaces to vlans swp1, swp2, swp3 --> vlan 2,3.
    7. Send traffic and verify that entries have been learned on different vlans.
    8. Verify that entries have been removed from swp1 due to mac move to swp4.
    """

    bridge = "br0"
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip("The testbed does not have enough dent with tgen connections")
    device_host_name = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    ageing_time = 600
    traffic_duration = 5

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
            {"device": bridge, "ageing_time": ageing_time*100, "type": "bridge"}]}])
    err_msg = f"Verify that ageing time set to '600'.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {"device": port, "master": bridge, "operstate": "up"} for port in ports]}])
    err_msg = f"Verify that bridge entities set to 'UP' state and links enslaved to bridge.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    for x in range(3):
        out = await BridgeVlan.add(
            input_data=[{device_host_name: [
                {"device": ports[x], "vid": 2},
                {"device": ports[x], "vid": 3}]}])
        assert out[0][device_host_name]["rc"] == 0, f"Verify that interfaces added to vlans '2' and '3'.\n{out}"

    address_map = (
        # swp port, tg port,    tg ip,     gw,        plen
        (ports[0], tg_ports[0], "1.1.1.2", "1.1.1.1", 24),
        (ports[1], tg_ports[1], "1.1.1.3", "1.1.1.1", 24),
        (ports[2], tg_ports[2], "1.1.1.4", "1.1.1.1", 24),
        (ports[3], tg_ports[3], "1.1.1.5", "1.1.1.1", 24),
    )

    dev_groups = tgen_utils_dev_groups_from_config(
        {"ixp": port, "ip": ip, "gw": gw, "plen": plen}
        for _, port, ip, gw, plen in address_map
    )

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    for x in range(3):
        streams = {
            "bridge_1": {
                "ip_source": dev_groups[tg_ports[x]][0]["name"],
                "ip_destination": dev_groups[tg_ports[3]][0]["name"],
                "srcMac": "aa:bb:cc:dd:ee:11",
                "dstMac": "aa:bb:cc:dd:ee:13",
                "type": "raw",
                "protocol": "802.1Q",
                "vlanID": 2,
            },
            "bridge_2": {
                "ip_source": dev_groups[tg_ports[x]][0]["name"],
                "ip_destination": dev_groups[tg_ports[3]][0]["name"],
                "srcMac": "aa:bb:cc:dd:ee:12",
                "dstMac": "aa:bb:cc:dd:ee:14",
                "type": "raw",
                "protocol": "802.1Q",
                "vlanID": 3,
            }
        }

        await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

        await tgen_utils_start_traffic(tgen_dev)
        await asyncio.sleep(traffic_duration)
        await tgen_utils_stop_traffic(tgen_dev)

        # check the traffic stats
        stats = await tgen_utils_get_traffic_stats(tgen_dev, "Traffic Item Statistics")
        for row in stats.Rows:
            loss = tgen_utils_get_loss(row)
            assert loss == 0, f"Expected loss: 0%, actual: {loss}%"

        out = await BridgeFdb.show(input_data=[{device_host_name: [{"options": "-j"}]}],
                                   parse_output=True)
        assert out[0][device_host_name]["rc"] == 0, "Failed to get fdb entry."

        fdb_entries = out[0][device_host_name]["parsed_output"]
        learned_macs = [en["mac"] for en in fdb_entries if "mac" in en]
        err_msg = "Verify that source macs have been learned."
        assert streams["bridge_1"]["srcMac"] and streams["bridge_2"]["srcMac"] in learned_macs, err_msg
        if x != 2:
            await tgen_utils_clear_traffic_items(tgen_dev)

    out = await BridgeFdb.show(input_data=[{device_host_name: [{"device": ports[0], "options": "-j"}]}],
                               parse_output=True)
    assert out[0][device_host_name]["rc"] == 0, "Failed to get fdb entry."

    fdb_entries = out[0][device_host_name]["parsed_output"]
    learned_macs = [en["mac"] for en in fdb_entries if "mac" in en]
    assert streams["bridge_1"]["srcMac"] and streams["bridge_2"]["srcMac"] not in learned_macs, err_msg
