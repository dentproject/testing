import asyncio
import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.ethtool.ethtool import Ethtool

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_get_loss,
)

pytestmark = [
    pytest.mark.suite_functional_ipv4,
    pytest.mark.usefixtures("cleanup_ip_addrs", "cleanup_tgen", "enable_ipv4_forwarding"),
    pytest.mark.asyncio,
]


async def get_port_stats(dent, ports):
    stats = {}
    for port in ports:
        out = await Ethtool.show(input_data=[{dent: [
            {"devname": port, "options": "-S"}
        ]}], parse_output=True)
        assert out[0][dent]["rc"] == 0
        stats[port] = out[0][dent]["parsed_output"]
    return stats


@pytest.mark.usefixtures("change_port_mtu")
async def test_ipv4_oversized_mtu(testbed):
    """
    Test Name: test_ipv4_oversized_mtu
    Test Suite: suite_functional_ipv4
    Test Overview: Test IPv4 oversized mtu counters
    Test Procedure:
    1. Init interfaces
    2. Configure ports up
    3. Configure IP addrs
    4. Configure interfaces MTU to 1000
    5. Generate traffic with packet size 1200 and verify there's no reception due to MTU
    6. Verify oversized counter been incremented in port statistics
    """
    # 1. Init interfaces
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgen connections")
        return
    dent = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]
    traffic_duration = 10
    delayed_stats_update_time = 10
    address_map = (
        # swp port, tg port,    swp ip,    tg ip,     plen
        (ports[0], tg_ports[0], "1.1.1.1", "1.1.1.2", 24),
        (ports[1], tg_ports[1], "2.2.2.1", "2.2.2.2", 24),
        (ports[2], tg_ports[2], "3.3.3.1", "3.3.3.2", 24),
        (ports[3], tg_ports[3], "4.4.4.1", "4.4.4.2", 24),
    )
    tg_to_swp_map = {
        tg: swp for swp, tg, *_ in address_map
    }

    # 2. Configure ports up
    out = await IpLink.set(input_data=[{dent: [
        {"device": port, "operstate": "up"}
        for port, *_ in address_map
    ]}])
    assert out[0][dent]["rc"] == 0, "Failed to set port state UP"

    # 3. Configure IP addrs
    out = await IpAddress.add(input_data=[{dent: [
        {"dev": port, "prefix": f"{ip}/{plen}"}
        for port, _, ip, _, plen in address_map
    ]}])
    assert out[0][dent]["rc"] == 0, "Failed to add IP addr to port"

    dev_groups = tgen_utils_dev_groups_from_config(
        {"ixp": port, "ip": ip, "gw": gw, "plen": plen}
        for _, port, gw, ip, plen in address_map
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    streams = {
        f"{tg1} <-> {tg2}": {
            "type": "ipv4",
            "ip_source": dev_groups[tg1][0]["name"],
            "ip_destination": dev_groups[tg2][0]["name"],
            "protocol": "ip",
            "rate": "1000",  # pps
            "frameSize": 1200,
        } for tg1, tg2 in zip(tg_ports, reversed(tg_ports))
    }

    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # 4. Port mtu should be configured in the change_port_mtu fixture

    # 5. Generate traffic with packet size 1200
    old_stats = await get_port_stats(dent, (port for port, *_ in address_map))

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    await asyncio.sleep(delayed_stats_update_time)  # wait for delayed stats to update
    new_stats = await get_port_stats(dent, (port for port, *_ in address_map))

    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    for row in stats.Rows:
        # Verify there's no reception due to MTU
        loss = tgen_utils_get_loss(row)
        assert loss == 100, f"Expected loss: 100%, actual: {loss}%"

        # 6. Verify oversized counter been incremented in port statistics
        port = tg_to_swp_map[row["Tx Port"]]
        oversized = int(new_stats[port]["oversize"]) - int(old_stats[port]["oversize"])
        assert oversized == int(row["Tx Frames"])


@pytest.mark.xfail(reason="Device does not support fragmentation")
async def test_ipv4_fragmentation(testbed):
    """
    Test Name: test_ipv4_fragmentation
    Test Suite: suite_functional_ipv4
    Test Overview: Test IPv4 fragmentation
    Test Procedure:
    1. Init interfaces
    2. Configure ports up
    3. Configure IP addrs
    4. Generate Non-fragment/fragment traffic and verify reception
    """
    # 1. Init interfaces
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgen connections")
        return
    dent = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]
    traffic_duration = 10
    fragmented = 1522
    non_fragmented = 1420
    address_map = (
        # swp port, tg port,    swp ip,    tg ip,     plen
        (ports[0], tg_ports[0], "1.1.1.1", "1.1.1.2", 24),
        (ports[1], tg_ports[1], "2.2.2.1", "2.2.2.2", 24),
        (ports[2], tg_ports[2], "3.3.3.1", "3.3.3.2", 24),
        (ports[3], tg_ports[3], "4.4.4.1", "4.4.4.2", 24),
    )

    # 2. Configure ports up
    out = await IpLink.set(input_data=[{dent: [
        {"device": port, "operstate": "up"}
        for port, *_ in address_map
    ]}])
    assert out[0][dent]["rc"] == 0, "Failed to set port state UP"

    # 3. Configure IP addrs
    out = await IpAddress.add(input_data=[{dent: [
        {"dev": port, "prefix": f"{ip}/{plen}"}
        for port, _, ip, _, plen in address_map
    ]}])
    assert out[0][dent]["rc"] == 0, "Failed to add IP addr to port"

    dev_groups = tgen_utils_dev_groups_from_config(
        {"ixp": port, "ip": ip, "gw": gw, "plen": plen}
        for _, port, gw, ip, plen in address_map
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    streams = {
        f"{tg1} <-> {tg2} | frame size {size}": {
            "type": "ipv4",
            "ip_source": dev_groups[tg1][0]["name"],
            "ip_destination": dev_groups[tg2][0]["name"],
            "protocol": "ip",
            "rate": "1000",  # pps
            "frameSize": size,
            "bi_directional": True,
        } for tg1, tg2, size in ((tg_ports[0], tg_ports[1], non_fragmented),
                                 (tg_ports[2], tg_ports[3], fragmented))
    }

    # 4. Generate Non-fragment/fragment traffic and verify reception
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # Verify packet discarded/fwd
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)

        if str(non_fragmented) in row["Traffic Item"]:
            assert loss == 0, f"Expected loss: 0%, actual: {loss}%"
            assert row["Tx Frames"] == row["Rx Frames"], \
                f"Expected Tx Frames {row['Tx Frames']} to equal Rx Frames {row['Rx Frames']}"
        else:  # fragmented traffic
            assert int(row["Rx Frames"]) == int(row["Tx Frames"]) * 2, \
                f"Expected Rx Frames {row['Rx Frames']} to equal 2 * Tx Frames {2 * int(row['Tx Frames'])}"
