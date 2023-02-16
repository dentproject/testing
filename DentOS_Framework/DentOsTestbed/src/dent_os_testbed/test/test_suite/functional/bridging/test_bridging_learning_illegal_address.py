import pytest
import asyncio

from dent_os_testbed.lib.bridge.bridge_fdb import BridgeFdb
from dent_os_testbed.lib.bridge.bridge_link import BridgeLink
from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_dev_groups_from_config,
    tgen_utils_traffic_generator_connect,
    tgen_utils_get_loss
)

pytestmark = [
    pytest.mark.suite_functional_bridging,
    pytest.mark.asyncio,
    pytest.mark.usefixtures("cleanup_bridges", "cleanup_tgen")
]

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
    7.  Send traffic by TG with illegal address.
    8.  Verify that illegal address haven't been learned.
    """

    bridge = "br0"
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgen connections")
        return
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 5

    out = await IpLink.add(
        input_data=[{device_host_name: [
            {"device": bridge, "type": "bridge"}]}])
    err_msg = f"Verify that bridge created.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {"device": bridge, "operstate": "up"}]}])
    err_msg = f"Verify that bridge set to 'UP' state.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

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
        #swp port, tg port,     tg ip,     gw,        plen
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
                f"Verify that traffic from swp4 to swp1 forwarded.\n"
        if row["Traffic Item"] == "broadcast" and row["Rx Port"] == tg_ports[2]:
            assert tgen_utils_get_loss(row) == 100.000, \
                f"Verify that traffic from swp2 to swp3 not forwarded.\n"
        if row["Traffic Item"] == "multicast_1" and row["Rx Port"] == tg_ports[1]:
            assert tgen_utils_get_loss(row) == 100.000, \
                f"Verify that traffic from swp3 to swp2 not forwarded.\n"
        if row["Traffic Item"] == "multicast_2" and row["Rx Port"] == tg_ports[3]:
            assert tgen_utils_get_loss(row) == 100.000, \
                f"Verify that traffic from swp1 to swp4 not forwarded.\n"

    out = await BridgeFdb.show(input_data=[{device_host_name: [{"options": "-j"}]}],
                               parse_output=True)
    assert out[0][device_host_name]["rc"] == 0, f"Failed to get fdb entry.\n"

    fdb_entries = out[0][device_host_name]["parsed_output"]
    learned_macs = [en["mac"] for en in fdb_entries if "mac" in en]
    illegal_address = ["00:00:00:00:00:00", "ff:ff:ff:ff:ff:ff", "01:00:00:00:00:00"]
    for mac in illegal_address:
        err_msg = f"Verify that source macs have not been learned due to illegal address.\n"
        assert mac not in learned_macs, err_msg
