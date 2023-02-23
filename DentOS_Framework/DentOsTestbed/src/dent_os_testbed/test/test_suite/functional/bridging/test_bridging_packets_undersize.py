import pytest
import asyncio

from dent_os_testbed.lib.bridge.bridge_link import BridgeLink
from dent_os_testbed.lib.bridge.bridge_fdb import BridgeFdb
from dent_os_testbed.lib.ethtool.ethtool import Ethtool
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

async def get_port_stats(device_host_name, ports):
    stats = {}
    for port in ports:
        out = await Ethtool.show(input_data=[{device_host_name: [
            {"devname": port, "options": "-S"}
        ]}], parse_output=True)
        assert out[0][device_host_name]["rc"] == 0
        stats[port] = out[0][device_host_name]["parsed_output"]
    return stats


async def test_bridging_packets_undersize(testbed):
    """
    Test Name: test_bridging_packets_undersize
    Test Suite: suite_functional_bridging
    Test Overview: Verify that traffic with undersized packets aren't learned.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1, swp2, swp3, swp4 master br0.
    3.  Set entities swp1, swp2, swp3, swp4 UP state.
    4.  Set bridge br0 admin state UP.
    5.  Set ports swp1, swp2, swp3, swp4 learning ON.
    6.  Set ports swp1, swp2, swp3, swp4 flood OFF.
    7.  Set streams frameSize 48.
    8.  Send traffic for bridge to learn addresses.
    9.  Verify that addresses haven't been learned due to undersized packet.
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
            "rate": 1000,
            "frameSize": 48,
        } for src, dst in ((3, 0), (2, 1), (1, 2), (0, 3))
    }

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    old_stats = await get_port_stats(device_host_name, (port for port, *_ in address_map))

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    new_stats = await get_port_stats(device_host_name, (port for port, *_ in address_map))

    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Traffic Item Statistics")
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        assert loss == 100, f"Expected loss: 100%, actual: {loss}%"

    # check quantity of undersized packets
    for row, port in zip(stats.Rows, old_stats.keys()):
        undersized = int(new_stats[port]["undersize"]) - int(old_stats[port]["undersize"])
        err_msg = f"Verify that quantity of undersized packets is correct.\n"
        assert int(row["Tx Frames"]) == undersized, err_msg

    out = await BridgeFdb.show(input_data=[{device_host_name: [{"options": "-j"}]}],
                               parse_output=True)
    assert out[0][device_host_name]["rc"] == 0, f"Failed to get fdb entry.\n"

    fdb_entries = out[0][device_host_name]["parsed_output"]
    learned_macs = [en["mac"] for en in fdb_entries if "mac" in en]
    for mac in list_macs:
        err_msg = f"Verify that source macs have not been learned due to undersized packet.\n"
        assert mac not in learned_macs, err_msg
