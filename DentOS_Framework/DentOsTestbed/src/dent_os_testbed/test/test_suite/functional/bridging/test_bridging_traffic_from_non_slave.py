import pytest

from dent_os_testbed.lib.bridge.bridge_link import BridgeLink
from dent_os_testbed.constants import DEFAULT_LOGGER
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.logger.Logger import AppLogger
from dent_os_testbed.lib.bridge.bridge_fdb import BridgeFdb
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
    Test Name: test_bridging_traffic_from_non_slave
    Test Suite: suite_functional_bridging
    Test Overview: This test comes to verify: sending traffic from non slave port 
                   to enslaved port and verifying traffic is not forward.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
1.  Init bridge entity br0.
    2.  Set ports swp1, swp2, swp3, swp4 master br0.
    3.  Set entities swp1, swp2, swp3, swp4 UP state.
    4.  Set bridge br0 admin state UP.
    5.  Set ports swp1, swp2, swp3, swp4 learning OFF.
    6.  Set ports swp1, swp2, swp3, swp4 flood OFF.
    7.  Adding FDB static entries for ports swp1, swp2, swp3, swp4.
    8.  Setting swp1 to nomaster.
    9.  Send traffic by TG.
    10. Verify that is not being forward from nomaster to slave port.
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

    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {"device": port, "learning": False, "flood": False} for port in ports]}])
    assert out[0][device_host_name]["rc"] == 0, f" Verify that entities set to learning 'OFF' and flooding 'OFF' state.\n {out}"
    
    out = await BridgeFdb.add(
        input_data=[{device_host_name: [
            {"device": ports[0], 'lladdr':'46:8e:45:97:13:87'},
            {"device": ports[1], 'lladdr':'46:8e:45:97:13:87'},
            {"device": ports[2], 'lladdr':'46:8e:45:97:13:87'},
            {"device": ports[3], 'lladdr':'46:8e:45:97:13:87'}]}])
    assert out[0][device_host_name]["rc"] == 0, f" Verify that FDB static entries added.\n {out}"

    out = await IpLink.set(
        input_data=[{device_host_name: [{"device": ports[0], "nomaster": True}]}])
    assert out[0][device_host_name]["rc"] == 0, f" Verify that swp1 entity set to 'nomaster'.\n {out}"
   
    # Send traffic and verify 9-10 steps
