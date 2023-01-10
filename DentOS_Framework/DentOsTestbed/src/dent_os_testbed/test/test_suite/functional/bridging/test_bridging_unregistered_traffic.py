import pytest

from dent_os_testbed.lib.bridge.bridge_link import BridgeLink
from dent_os_testbed.constants import DEFAULT_LOGGER
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.logger.Logger import AppLogger
from dent_os_testbed.utils.test_utils.tb_utils import (
    tb_get_all_devices,
    tb_reload_nw_and_flush_firewall
)
from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_create_devices_and_connect,
    tgen_utils_stop_traffic,
    tgen_utils_stop_protocols,
    tgen_utils_start_traffic,
    tgen_utils_setup_streams,
    tgen_utils_get_traffic_stats,
    tgen_utils_get_loss,
)

pytestmark = pytest.mark.suite_functional_bridging


@pytest.mark.asyncio
async def test_bridging(testbed):
    """
    Test Name: test_bridging_unregistered_traffic
    Test Suite: suite_functional_bridging
    Test Overview: This test comes to verify: bridge flooding behaviour of unregistered IPv4/IPv6 MC packets.
    Unregistered {ipv} traffic conditions:
            - MAC DA is Multicast (but not Broadcast)
            - MAC DA has the {ipv} MAC prefix {mac_range}
            - Packet Destination {ipv} address is in the {ipv} Multicast address range ({ip_range})
            - FDB destination lookup does not find a matching entry
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1, swp2, swp3, swp4 master br0.
    3.  Set entities swp1, swp2, swp3, swp4 UP state.
    4.  Set bridge br0 admin state UP.
    5.  Clear TG counters.
    6.  Send Unregistered IPv6 MC traffic from TG#1.
    7.  Verify that traffic flooded to all ports that are members in br0.
    8.  Disable multicast flooding on the ports.
    9.  Clear TG counters.
    10. Send Unregistered IPv6 MC traffic from TG#1.
    11. Verify that traffic was not flooded/forwarded to any of the mc disabled ports.
    12. Enable back multicast flooding on the ports.
    13. Clear TG counters.
    14. Send Unregistered IPv6 MC traffic from TG#1.x
    15. Verify that traffic flooded to all ports that are members in br0.
    """

    logger = AppLogger(DEFAULT_LOGGER)
    dev = await tb_get_all_devices(testbed)
    logger.info("Devices:", dev)

    bridge = "br0"
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        logger.error("The testbed does not have enough dent eith tgn connections")
        return
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    #tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]

    out = await IpLink.add(
        input_data=[{device_host_name: [{"device": bridge, "type": "bridge"}]}])
    assert out[0][device_host_name]["rc"] == 0, f" Verify that bridge created.\n {out}"

    out = await IpLink.set(
        input_data=[{device_host_name:  [
            {"device": port, "master": "br0", "operstate": "up"} for port in ports]},
            {"device": bridge, "operstate": "up"}])
    assert out[0][device_host_name]["rc"] == 0, f" Verify that bridge, bridge entities set to 'UP' state and links enslaved to bridge.\n {out}"

    # Clear TG counters 5 step
    # Send Unregistered IPv6 MC traffic from TG#1 6 step
    # Verify that traffic flooded to all ports that are members in br0 7 step

    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {"device": port, "flood": False} for port in ports]}])
    assert out[0][device_host_name]["rc"] == 0,  f" Verify that entities set to flooding 'OFF' state.\n {out}" 

    # Clear TG counters 9 step
    # Send Unregistered IPv6 MC traffic from TG#1 10 step
    # Verify that traffic was not flooded/forwarded to any of the mc disabled ports 11 step

    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {"device": port, "flood": True} for port in ports]}])
    assert out[0][device_host_name]["rc"] == 0, f" Verify that entities set to flooding 'ON' state.\n {out}" 

    # Clear TG counters 12 step
    # Send Unregistered IPv6 MC traffic from TG#1 13 step
    # Verify that traffic flooded to all ports that are members in br0 14 step
