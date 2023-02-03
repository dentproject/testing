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
    tgen_utils_get_loss
)

pytestmark = [
    pytest.mark.suite_functional_bridging, 
    pytest.mark.asyncio,
    pytest.mark.usefixtures("cleanup_bridges", "cleanup_tgen")
]

async def test_bridging_ageing_refresh(testbed):
    """
    Test Name: test_bridging_ageing_refresh
    Test Suite: suite_functional_bridging
    Test Overview: Verify that bridge ageing time refreshes after re-sending traffic.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set bridge br0 admin state UP.
    3.  Set br0 ageing time to 40 seconds [default is 300 seconds].
    4.  Set ports swp1, swp2, swp3, swp4 master br0.
    5.  Set entities swp1, swp2, swp3, swp4 UP state.
    6.  Set ports swp1, swp2, swp3, swp4 learning ON.
    7.  Send traffic to swp1 with sourse mac aa:bb:cc:dd:ee:11.
    8.  Wait for 0.5-0.75 AT, and check that entry exists.
    9.  Send traffic again, and check if it forwarded.
    10. Wait for 0.9 AT and verify that entry still exist.
    11. Wait 2 AT - entry should be deleted.
    """

    bridge = "br0"
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgen connections")
        return
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 5
    ageing_time = 40

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
            {"device": bridge, "ageing_time": ageing_time*100, "type": "bridge"}]}])
    err_msg = f"Verify that ageing time set to '40'.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {"device": port, "master": bridge, "operstate": "up"} for port in ports]}])
    err_msg = f"Verify that bridge entities set to 'UP' state and links enslaved to bridge.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {"device": port, "learning": True} for port in ports]}])
    err_msg = f"Verify that entities set to learning 'ON' state.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    address_map = (
        #swp port, tg port,     tg ip,      gw        plen
        (ports[0], tg_ports[0], "1.1.1.2", "1.1.1.1", 24),
        (ports[1], tg_ports[1], "2.2.2.2", "2.2.2.1", 24)
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
            "dstMac": "aa:bb:cc:dd:ee:12",
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

    await asyncio.sleep(0.75*ageing_time)

    out = await BridgeFdb.show(input_data=[{device_host_name: [{"options": "-j"}]}],
                               parse_output=True)
    assert out[0][device_host_name]["rc"] == 0, "Failed to get fdb entry.\n"

    fdb_entries = out[0][device_host_name]["parsed_output"]
    learned_macs = [en["mac"] for en in fdb_entries if "mac" in en]
    err_msg = f"Verify that entry exist in mac table.\n"
    assert "aa:bb:cc:dd:ee:11" in learned_macs, err_msg

    await tgen_utils_start_traffic(tgen_dev)
    
    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Traffic Item Statistics")
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) == 0.000, \
        f"Verify that traffic from {row['Tx Port']} to {row['Rx Port']} forwarded.\n{out}"

    await asyncio.sleep(0.9*ageing_time)

    out = await BridgeFdb.show(input_data=[{device_host_name: [{"options": "-j"}]}],
                               parse_output=True)
    assert out[0][device_host_name]["rc"] == 0, "Failed to get fdb entry.\n"

    fdb_entries = out[0][device_host_name]["parsed_output"]
    learned_macs = [en["mac"] for en in fdb_entries if "mac" in en]
    err_msg = f"Verify that entry exist in mac table.\n"
    assert "aa:bb:cc:dd:ee:11" in learned_macs, err_msg

    await tgen_utils_stop_traffic(tgen_dev)

    await asyncio.sleep(2*ageing_time)

    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Traffic Item Statistics")
    for row in stats.Rows:
        assert float(row["Loss %"]) == 0.000, f'Failed>Loss percent: {row["Loss %"]}'

    out = await BridgeFdb.show(input_data=[{device_host_name: [{"options": "-j"}]}],
                               parse_output=True)
    assert out[0][device_host_name]["rc"] == 0, "Failed to get fdb entry.\n"

    fdb_entries = out[0][device_host_name]["parsed_output"]
    unlearned_macs = [en["mac"] for en in fdb_entries if "mac" in en]
    err_msg = f"Verify that entry doesn't exist due to expired ageing time for that entry.\n"
    assert "aa:bb:cc:dd:ee:11" not in unlearned_macs, err_msg

    await tgen_utils_stop_protocols(tgen_dev)


async def test_bridging_ageing_under_continue(testbed):
    """
    Test Name: test_bridging_ageing_under_continue
    Test Suite: suite_functional_bridging
    Test Overview: Verify that bridge learning entries appear with continuous traffic after ageing time expired.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set br0 ageing time to 10 seconds [default is 300 seconds].
    3.  Set ports swp1, swp2, swp3, swp4 master br0.
    4.  Set bridge br0 admin state UP.
    5.  Set entities swp1, swp2, swp3, swp4 UP state.
    6.  Set ports swp1, swp2, swp3, swp4 learning ON.
    7.  Set ports swp1, swp2, swp3, swp4 flood OFF.
    8.  Send continuous traffic to swp1, swp2, swp3, swp4 with sourse macs 
        aa:bb:cc:dd:ee:11 aa:bb:cc:dd:ee:12 
        aa:bb:cc:dd:ee:13 aa:bb:cc:dd:ee:14 accordingly.
    9.  Delaying 3 AT.
    10. Verify that entries exist due to continuous traffic.
    """

    bridge = "br0"
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print.error(
            "The testbed does not have enough dent with tgen connections")
        return
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    ageing_time = 10

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
            {"device": bridge, "ageing_time": ageing_time*100, "type": "bridge"}]}])
    err_msg = f"Verify that ageing time set to '10'.\n{out}"
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
    await asyncio.sleep(3*ageing_time)

    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Traffic Item Statistics")
    for row in stats.Rows:
        assert float(row["Tx Frames"]) > 0.000, f'Failed>Ixia should transmit traffic: {row["Tx Frames"]}'

    out = await BridgeFdb.show(input_data=[{device_host_name: [{"options": "-j"}]}],
                               parse_output=True)
    assert out[0][device_host_name]["rc"] == 0, "Failed to get fdb entry.\n"

    fdb_entries = out[0][device_host_name]["parsed_output"]
    learned_macs = [en["mac"] for en in fdb_entries if "mac" in en]
    for mac in list_macs:
        err_msg = f"Verify that entries exist due to continues traffic.\n"
        assert mac in learned_macs, err_msg

    await tgen_utils_stop_protocols(tgen_dev)
