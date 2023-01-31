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
    tgen_utils_stop_protocols,
    tgen_utils_stop_traffic,
    tgen_utils_dev_groups_from_config,
    tgen_utils_traffic_generator_connect,
)

pytestmark = pytest.mark.suite_functional_bridging


@pytest.mark.asyncio
async def test_bridging_fdb_flush_on_down(testbed):
    """
    Test Name: test_bridging_fdb_flush_on_down
    Test Suite: suite_functional_bridging
    Test Overview: Verify that fdb enries are removed when port goes to the down state.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1, swp2, swp3, swp4 master br0.
    3.  Set bridge br0 admin state UP.
    4.  Set entities swp1, swp2, swp3, swp4 UP state.
    5.  Set ports swp1, swp2, swp3, swp4 learning ON.
    6.  Set ports swp1, swp2, swp3, swp4 flood OFF.
    7.  Send traffic to swp1 with sourse mac aa:bb:cc:dd:ee:11.
    8.  Verify fdb entry on swp1 in mac table.
    9.  Set port swp2 admin state DOWN.
    10. Verify that entry does not exist in mac table.
    """

    bridge = "br0"
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        print.error(
            "The testbed does not have enough dent with tgen connections")
        return
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 5

    out = await IpLink.add(
        input_data=[{device_host_name:  [
            {"device": bridge, "type": "bridge"}]}])
    err_msg = f"Verify that bridge created.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_host_name:  [
            {"device": bridge, "operstate": "up"}]}])
    err_msg = f"Verify that bridge set to 'UP' state.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_host_name:  [
            {"device": port, "master": bridge, "operstate": "up"} for port in ports]}])
    err_msg = f"Verify that bridge entities set to 'UP' state and links enslaved to bridge.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    out = await BridgeLink.set(
        input_data=[{device_host_name:  [
            {"device": port, "learning": True, "flood": False} for port in ports]}])
    err_msg = f"Verify that entities set to learning 'ON' and flooding 'OFF' state.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    address_map = (
        #swp port, tg port,     tg ip,      gw          plen
        (ports[0], tg_ports[0], "11.0.0.1", "11.0.0.2", 24),
        (ports[1], tg_ports[1], "11.0.0.2", "11.0.0.1", 24)
    )

    dev_groups = tgen_utils_dev_groups_from_config(
        {"ixp": port, "ip": ip, "gw": gw, "plen": plen}
        for _, port, ip, gw, plen in address_map
    )

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    streams = {
        "bridge": {
            "ip_source": dev_groups[tg_ports[1]][0]["name"],
            "ip_destination": dev_groups[tg_ports[0]][0]["name"],
            "srcMac": "aa:bb:cc:dd:ee:11",
            "dstMac": "ff:ff:ff:ff:ff:ff",
            "type": "raw",
            "protocol": "802.1Q",
        }
    }

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Traffic Item Statistics")
    for row in stats.Rows:
        assert float(row["Loss %"]) == 0.000, f'Failed>Loss percent: {row["Loss %"]}'

    out = await BridgeFdb.show(input_data=[{device_host_name: [{"options": "-j"}]}],
                               parse_output=True)
    assert out[0][device_host_name]["rc"] == 0, "Failed to get fdb entry.\n"

    fdb_entries = out[0][device_host_name]["parsed_output"]
    learned_macs = [en["mac"] for en in fdb_entries if "mac" in en]
    err_msg = f"Verify that entry exist in mac table.\n"
    assert "aa:bb:cc:dd:ee:11" in learned_macs, err_msg

    out = await IpLink.set(
        input_data=[{device_host_name:  [
            {"device": ports[1], "operstate": "down"}]}])
    err_msg = f"Verify that swp2 entity set to 'DOWN' state.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    out = await BridgeFdb.show(input_data=[{device_host_name: [{"options": "-j"}]}],
                               parse_output=True)
    assert out[0][device_host_name]["rc"] == 0, "Failed to get fdb entry.\n"

    fdb_entries = out[0][device_host_name]["parsed_output"]
    unlearned_macs = [en["mac"] for en in fdb_entries if "mac" in en]
    err_msg = f"Verify that entry does not exist in mac table.\n"
    assert "aa:bb:cc:dd:ee:11" not in unlearned_macs, err_msg

    await tgen_utils_stop_protocols(tgen_dev)
