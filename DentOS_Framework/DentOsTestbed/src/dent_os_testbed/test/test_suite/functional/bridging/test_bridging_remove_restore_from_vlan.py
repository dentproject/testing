import pytest
import asyncio

from dent_os_testbed.lib.bridge.bridge_link import BridgeLink
from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan
from dent_os_testbed.lib.bridge.bridge_fdb import BridgeFdb
from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_get_loss,
    tgen_utils_dev_groups_from_config,
    tgen_utils_traffic_generator_connect,
)

pytestmark = [
    pytest.mark.suite_functional_bridging,
    pytest.mark.asyncio,
    pytest.mark.usefixtures("cleanup_bridges", "cleanup_tgen")
]

async def test_bridging_remove_restore_from_vlan(testbed):
    """
    Test Name: test_bridging_remove_restore_from_vlan
    Test Suite: suite_functional_bridging
    Test Overview: Verify removing and restoring a port with a bridge address entry by it's vlan.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0 with vlan filtering ON.
    2.  Set ports swp1, swp2, swp3, swp4 master br0.
    3.  Set entities swp1, swp2, swp3, swp4 UP state.
    4.  Set bridge br0 admin state UP.
    5.  Set ports swp1, swp2, swp3, swp4 learning OFF.
    6.  Set ports swp1, swp2, swp3, swp4 flood OFF.
    7.  Add interfaces to vlans swp1, swp2, swp3 --> vlan 2.
    8.  Adding static FDB entry aa:bb:cc:dd:ee:11 for swp1 with vlan 2.
    9.  Removing swp1 from vlan 2.
    10. Verify that swp1 entry aa:bb:cc:dd:ee:11 vlan 2 has not been removed from the address table.
    11. Adding swp1 back to vlan 2.
    12. Send traffic from swp3 to swp1 with dst mac aa:bb:cc:dd:ee:11 and vlan 2.
    13. Verify that packet is recieved on swp1 and there is no traffic on swp2.
    """

    bridge = "br0"
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 3)
    if not tgen_dev or not dent_devices:
        pytest.skip("The testbed does not have enough dent with tgen connections")
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 5

    out = await IpLink.add(
        input_data=[{device_host_name: [
            {"device": bridge, "vlan_filtering": 1, "type": "bridge"}]}])
    err_msg = f"Verify that bridge created and vlan filtering set to 'ON'.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

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
            {"device": port, "learning": False, "flood": False} for port in ports]}])
    err_msg = f"Verify that entities set to learning 'OFF' and flooding 'OFF' state.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    out = await BridgeVlan.add(
        input_data=[{device_host_name: [
            {"device": port, "vid": 2} for port in ports]}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify that interfaces added to vlans '2'.\n{out}"

    out = await BridgeFdb.add(
        input_data=[{device_host_name: [
            {"device": ports[0], "lladdr": "aa:bb:cc:dd:ee:11", "master": True, "static": True, "vlan": 2}]}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify that FDB static entries added.\n{out}"

    out = await BridgeVlan.delete(
        input_data=[{device_host_name: [{"device": ports[0], "vid": 2}]}])
    assert out[0][device_host_name]["rc"] == 0, f" Verify that interface deleted from vlan '2'.\n{out}"

    out = await BridgeFdb.show(input_data=[{device_host_name: [{"options": "-j"}]}],
                               parse_output=True)
    assert out[0][device_host_name]["rc"] == 0, f"Failed to get fdb entry.\n"

    fdb_entries = out[0][device_host_name]["parsed_output"]
    learned_macs = [en["mac"] for en in fdb_entries if "mac" in en]
    err_msg = f"Verify that entry has not been removed from the address table.\n"
    assert "aa:bb:cc:dd:ee:11" in learned_macs, err_msg

    out = await BridgeVlan.add(
        input_data=[{device_host_name: [{"device": ports[0], "vid": 2}]}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify that interfaces added to vlans '2'.\n {out}"

    address_map = (
        # swp port, tg port,    tg ip,     gw,        plen
        (ports[0], tg_ports[0], "1.1.1.2", "1.1.1.1", 24),
        (ports[1], tg_ports[1], "1.1.1.3", "1.1.1.1", 24),
        (ports[2], tg_ports[2], "1.1.1.4", "1.1.1.1", 24),
    )

    dev_groups = tgen_utils_dev_groups_from_config(
        {"ixp": port, "ip": ip, "gw": gw, "plen": plen}
        for _, port, ip, gw, plen in address_map
    )

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    streams = {
        "bridge_1": {
            "ip_source": dev_groups[tg_ports[2]][0]["name"],
            "ip_destination": dev_groups[tg_ports[0]][0]["name"],
            "srcMac": "aa:bb:cc:dd:ee:12",
            "dstMac": "aa:bb:cc:dd:ee:11",
            "type": "raw",
            "protocol": "802.1Q",
            "vlanID": 2,
        },
    }

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    for row in stats.Rows:
        if row["Traffic Item"] == "bridge_1" and row["Rx Port"] == tg_ports[0]:
            assert tgen_utils_get_loss(row) == 000.000, \
                f"Verify that traffic from swp3 to swp1 forwarded.\n"
        if row["Traffic Item"] == "bridge_1" and row["Rx Port"] == tg_ports[1]:
            assert tgen_utils_get_loss(row) == 100.000, \
                f"Verify that traffic from swp3 to swp2 not forwarded.\n"
