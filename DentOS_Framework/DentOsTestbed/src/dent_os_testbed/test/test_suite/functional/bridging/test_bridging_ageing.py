import asyncio
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
async def test_bridging_refresh(testbed):
    """
    Test Name: test_bridging_ageing_refresh
    Test Suite: suite_functional_bridging
    Test Overview: This test comes to verify: bridge ageing time refreshes after re-sending traffic.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set br0 ageing time to 40 seconds [default is 300 seconds].
    3.  Set ports swp1, swp2, swp3, swp4 master br0.
    4.  Set entities swp1, swp2, swp3, swp4 UP state.
    5.  Set bridge br0 admin state UP.
    6.  Set ports swp1, swp2, swp3, swp4 learning ON.
    7.  Set ports swp1, swp2, swp3, swp4 flood OFF.
    8.  Send traffic to swp1 with sourse mac aa:bb:cc:dd:ee:11.
    9.  Delaying for 50 seconds.
    10. Send traffic to swp1 again with sourse mac aa:bb:cc:dd:ee:11 for refreshing br0 
        ageing time to be set back to 40 seconds for that entry.
    11. Delaying for 20 seconds.
    12. Verify that entry still exist.
    13. Delaying for 50 seconds.
    14. Verify that entry still doesn't exist due to expired ageing time for that entry.
    """

    logger = AppLogger(DEFAULT_LOGGER)
    dev = await tb_get_all_devices(testbed)
    logger.info("Devices:", dev)

    bridge = "br0"
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        logger.error(
            "The testbed does not have enough dent eith tgn connections")
        return
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    # tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]

    out = await IpLink.add(
        input_data=[{device_host_name: [{"device": bridge, "type": "bridge"}]}])
    assert out[0][device_host_name]["rc"] == 0, f" Verify that bridge created.\n {out}"

    out = await IpLink.set(
        input_data=[{device_host_name:  [
            {"device": bridge, "ageing_time": 40},
            {"device": port, "master": "br0", "operstate": "up"} for port in ports]},
            {"device": bridge, "operstate": "up"}])
    assert out[0][device_host_name]["rc"] == 0, f" Verify that ageing time set to '40', bridge and bridge entities set to 'UP' state and links enslaved to bridge.\n {out}"        
    
    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {"device": port, "learning": True, "flood": False} for port in ports]}])
    assert out[0][device_host_name]["rc"] == 0, f" Verify that entities set to learning 'ON' and flooding 'OFF' state.\n {out}"

    # Send traffic to swp1 with sourse mac aa:bb:cc:dd:ee:11 8 step

    await asyncio.sleep(50)

    # Send traffic to swp1 again with sourse mac aa:bb:cc:dd:ee:11 for refreshing br0
    # ageing time to be set back to 40 seconds for that entry 10 step

    await asyncio.sleep(20)

    # Verify that entry still exist 12 step

    await asyncio.sleep(50)

    # Verify that entry still doesn't exist due to expired ageing time for that entry 14 step


@pytest.mark.asyncio
async def test_bridging_under_continue(testbed):
    """
    Test Name: test_bridging_ageing_under_continue
    Test Suite: suite_functional_bridging
    Test Overview: This test comes to verify: bridge learning entries still appear with 
                   continues traffic after ageing time expired.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set br0 ageing time to 10 seconds [default is 300 seconds].
    3.  Set ports swp1, swp2, swp3, swp4 master br0.
    4.  Set entities swp1, swp2, swp3, swp4 UP state.
    5.  Set bridge br0 admin state UP.
    6.  Set ports swp1, swp2, swp3, swp4 learning ON.
    7.  Set ports swp1, swp2, swp3, swp4 flood OFF.
    8.  Continues traffic sending to swp1, swp2, swp3, swp4 with sourse macs 
        aa:bb:cc:dd:ee:11 aa:bb:cc:dd:ee:12 aa:bb:cc:dd:ee:13 aa:bb:cc:dd:ee:14 accordingly.
    9.  Delaying for 10 seconds.
    10. Verify that entries still exist due to continues traffic.
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
            {"device": bridge, "ageing_time": 10},
            {"device": port, "master": "br0", "operstate": "up"} for port in ports]},
            {"device": bridge, "operstate": "up"}])
    assert out[0][device_host_name]["rc"] == 0, f" Verify that ageing time set to '10', bridge and bridge entities set to 'UP' state and links enslaved to bridge.\n {out}"
    
    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {"device": port, "learning": True, "flood": False} for port in ports]}])
    assert out[0][device_host_name]["rc"] == 0, f" Verify that entities set to learning 'ON' and flooding 'OFF' state.\n {out}"
    
    # Continues traffic sending to swp1, swp2, swp3, swp4 with sourse macs 
    # aa:bb:cc:dd:ee:11 aa:bb:cc:dd:ee:12 aa:bb:cc:dd:ee:13 aa:bb:cc:dd:ee:14 accordingly 8 step

    await asyncio.sleep(10)

    # Verify that entries still exist due to continues traffic 10 step
