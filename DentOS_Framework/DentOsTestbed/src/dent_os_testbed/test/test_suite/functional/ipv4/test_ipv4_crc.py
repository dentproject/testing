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


async def test_ipv4_checksum(testbed):
    """
    Test Name: test_ipv4_checksum
    Test Suite: suite_functional_ipv4
    Test Overview: Test IPv4 checksum behaviour
    Test Procedure:
    1. Init interfaces
    2. Configure ports up
    3. Configure IP addrs
    4. Generate traffic with Valid/Invalid checksum and verify packet discarded/fwd
    """
    # 1. Init interfaces
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip("The testbed does not have enough dent with tgen connections")
    dent = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]
    traffic_duration = 10
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
        f"{tg1} <-> {tg2} {'bad' if crc else 'good'} crc": {
            "type": "ipv4",
            "ip_source": dev_groups[tg1][0]["name"],
            "ip_destination": dev_groups[tg2][0]["name"],
            "protocol": "ip",
            "rate": "1000",  # pps
            "bi_directional": True,
            "bad_crc": crc,
        } for tg1, tg2, crc in ((tg_ports[0], tg_ports[1], True),
                                (tg_ports[2], tg_ports[3], False))
    }

    # 4. Generate traffic with Valid/Invalid checksum
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    old_stats = await get_port_stats(dent, (port for port, *_ in address_map))

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    await asyncio.sleep(traffic_duration)  # wait for delayed stats to update
    new_stats = await get_port_stats(dent, (port for port, *_ in address_map))

    # Verify packet discarded/fwd
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        port = tg_to_swp_map[row["Tx Port"]]

        if "good" in row["Traffic Item"]:
            assert loss == 0, f"Expected loss: 0%, actual: {loss}%"
            assert old_stats[port]["bad_crc"] == new_stats[port]["bad_crc"], \
                "Bad CRC counter should not change for valid CRC traffic"
        else:  # bad crc
            assert loss == 100, f"Expected loss: 100%, actual: {loss}%"
            counter = int(new_stats[port]["bad_crc"]) - int(old_stats[port]["bad_crc"])
            assert counter == int(row["Tx Frames"]), \
                f"Expected Bad CRC counter to be {row['Tx Frames']}, not {counter}"
