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
    Test Name: test_bridging_no_fwd_port_down
    Test Suite: suite_functional_bridging
    Test Overview: This test comes to verify: no forwarding to port Down/Disable.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set br0 ageing time to 600 seconds [default is 300 seconds].
    3.  Set ports swp1, swp2, swp3, swp4 master br0.
    4.  Set entities swp1, swp2, swp3, swp4 UP state.
    5.  Set bridge br0 admin state UP.
    6.  Set ports swp1, swp2, swp3, swp4 learning ON.
    7.  Set ports swp1, swp2, swp3, swp4 flood OFF.
    8.  Send traffic to swp1 with sourse mac aa:bb:cc:dd:ee:11.
    9.  Set port swp1 admin state DOWN.
    10. Verify that entry not exist in mac table.
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
            {"device": bridge, "ageing_time": 600},
            {"device": port, "master": "br0", "operstate": "up"} for port in ports]},
            {"device": bridge, "operstate": "up"}])
    assert out[0][device_host_name]["rc"] == 0, f" Verify that ageing time set to '600', bridge and bridge entities set to 'UP' state and links enslaved to bridge.\n {out}"          
    
    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {"device": port, "learning": True, "flood": False} for port in ports]}])
    assert out[0][device_host_name]["rc"] == 0, f" Verify that entities set to learning 'ON' and flooding 'OFF' state.\n {out}"
    
    # Send traffic to swp1 with sourse mac aa:bb:cc:dd:ee:11 8 step

    out = await IpLink.set(
        input_data=[{device_host_name: [{"device": ports[0], "operstate": "down"}]}])
    assert out[0][device_host_name]["rc"] == 0, f" Verify that swp1 entity set to 'DOWN' state.\n {out}"

    # Verify that entry not exist in mac table 10 step
