import asyncio
import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_address import IpAddress

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_setup_streams,
)
from dent_os_testbed.utils.test_utils.tb_utils import (
    tb_ping_device,
)

pytestmark = [
    pytest.mark.suite_functional_ipv4,
    pytest.mark.usefixtures("cleanup_ip_addrs", "cleanup_tgen"),
    pytest.mark.asyncio,
]


async def test_ipv4_addr(testbed):
    """
    Test Name: test_ipv4_addr
    Test Suite: suite_functional_ipv4
    Test Overview: Test IPv4 static address
    Test Procedure:
    1. Init interfaces
    2. Configure IP addrs
    3. Configure ports up
    4. Generate ping on the ip interfaces and verify reception
    """
    # 1. Init interfaces
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgen connections")
        return
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]

    # 2. Configure IP addrs
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

    # 3. Configure ports up
    out = await IpLink.set(input_data=[{dent: [
        {"device": port, "operstate": "up"}
        for port, *_ in address_map
    ]}])
    assert out[0][dent]["rc"] == 0, "Failed to set port state UP"

    # 4. Generate ping on the ip interfaces and verify reception
    await tgen_utils_setup_streams(tgen_dev, None, streams={"dummy": {"type": "raw"}})

    out = await asyncio.gather(*[tb_ping_device(dent_dev, addr, pkt_loss_treshold=0, dump=True)
                                 for _, _, _, addr, _ in address_map])
    for rc in out:
        assert rc == 0, "Some pings did not have a reply"
