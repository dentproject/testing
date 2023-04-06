import asyncio
import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.ip.ip_neighbor import IpNeighbor

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


async def test_ipv4_en_dis_fwd(testbed):
    """
    Test Name: test_ipv4_en_dis_fwd
    Test Suite: suite_functional_ipv4
    Test Overview: Test enabling/disabling IPv4 forward
    Test Procedure:
    1. Init interfaces
    2. Configure ports up
    3. Configure IP addrs
    4. Transmit traffic with ip fwd enabled, verify traffic routed properly
    5. Disable IPv4 forwarding
    6. Flush neighbor (ARP) table
    7. Transmit traffic with ip fwd disabled, verify traffic not routed because neighbors were not resolved
    """
    # 1. Init interfaces
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip("The testbed does not have enough dent with tgen connections")
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]
    traffic_duration = 10

    # 2. Configure ports up
    out = await IpLink.set(input_data=[{dent: [{"device": port, "operstate": "up"}
                                               for port in ports]}])
    assert out[0][dent]["rc"] == 0, "Failed to set port state UP"

    # 3. Configure IP addrs
    address_map = (
        # swp port, tg port,    swp ip,    tg ip,     plen
        (ports[0], tg_ports[0], "1.1.1.1", "1.1.1.2", 24),
        (ports[1], tg_ports[1], "2.2.2.1", "2.2.2.2", 24),
        (ports[2], tg_ports[2], "3.3.3.1", "3.3.3.2", 24),
        (ports[3], tg_ports[3], "4.4.4.1", "4.4.4.2", 24),
    )

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

    # 4. Transmit traffic with ip fwd enabled, verify traffic routed properly
    streams = {
        f"{tg_ports[0]} <-> {tg_ports[1]}": {
            "type": "ipv4",
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "protocol": "ip",
            "rate": "1000",  # pps
            "bi_directional": True,
        },
        f"{tg_ports[2]} <-> {tg_ports[3]}": {
            "type": "ipv4",
            "ip_source": dev_groups[tg_ports[2]][0]["name"],
            "ip_destination": dev_groups[tg_ports[3]][0]["name"],
            "protocol": "ip",
            "rate": "1000",  # pps
            "bi_directional": True,
        },
    }

    await tgen_utils_setup_streams(tgen_dev, None, streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        assert loss == 0, f"Expected loss: 0%, actual: {loss}%"

    # 5. Disable IPv4 forwarding
    rc, out = await dent_dev.run_cmd(f"sysctl -n net.ipv4.ip_forward=0")
    assert rc == 0, "Failed to disable ip forwarding"

    # 6. Flush neighbor (ARP) table
    out = await IpNeighbor.flush(input_data=[{dent: [
        {"device": port} for port in ports
    ]}])
    assert out[0][dent]["rc"] == 0, "Failed to flush arp table"

    # 7. Transmit traffic with ip fwd disabled
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # Verify traffic not routed because neighbors were not resolved
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        assert loss == 100, f"Expected loss: 100%, actual: {loss}%"
