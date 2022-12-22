import time
import pytest

from dent_os_testbed.constants import DEFAULT_LOGGER
from dent_os_testbed.Device import DeviceType
from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan
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

pytestmark = pytest.mark.suite_bridging


@pytest.mark.asyncio
async def test_bridging(testbed):
    """
    Test Name: test_briging
    Test Suite: suite_bridging
    Test Overview: Configuration
    Test Procedure:
    1. Create VLAN-unaware bridges
    2. Create links/ports
    3. Add bridge members
    4. UP bridge&links
    """

    logger = AppLogger(DEFAULT_LOGGER)
    dev = await tb_get_all_devices(testbed)
    logger.info("Devices:", dev)

    dut = dev[0]
    bridge = "br0"

    out = await IpLink.add(
        input_data=[{dut.host.name: [{"device": bridge, "type": "bridge"}]}])
    assert out[0][dut.host_name]["rc"] == 0, out

    out = await IpLink.set(
        input_data=[{dut.host_name: [{"device": bridge, "operstate": "up"}]}])
    assert out[0][dut.host_name]["rc"] == 0, out

    out = await IpLink.add(
        input_data=[{dut.host_name: [{"device": "veth10", "type": "veth"}]}],
        input_data=[{dut.host_name: [{"device": "veth11", "type": "veth"}]}],
        input_data=[{dut.host_name: [{"device": "veth12", "type": "veth"}]}],
        input_data=[{dut.host_name: [{"device": "veth13", "type": "veth"}]}])
    assert out[0][dut.host_name]["rc"] == 0, out

    out = await IpLink.set(
        input_data=[{dut.host_name: [{"device": "veth10", "master": "br1"}]}],
        input_data=[{dut.host_name: [{"device": "veth11", "master": "br1"}]}],
        input_data=[{dut.host_name: [{"device": "veth12", "master": "br1"}]}],
        input_data=[{dut.host_name: [{"device": "veth13", "master": "br1"}]}])
    assert out[0][dut.host_name]["rc"] == 0, out

    out = await IpLink.set(
        input_data=[{dut.host_name: [{"device": "veth10", "operstate": "up"}]}],
        input_data=[{dut.host_name: [{"device": "veth11", "operstate": "up"}]}],
        input_data=[{dut.host_name: [{"device": "veth12", "operstate": "up"}]}],
        input_data=[{dut.host_name: [{"device": "veth13", "operstate": "up"}]}])
    assert out[0][dut.host_name]["rc"] == 0, out