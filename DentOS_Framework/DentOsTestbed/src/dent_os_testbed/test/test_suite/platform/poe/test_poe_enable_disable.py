import time

import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.poe.poectl import Poectl
from dent_os_testbed.utils.test_utils.tb_utils import tb_get_device_object_from_dut

pytestmark = pytest.mark.suite_poe


@pytest.mark.asyncio
async def test_poe_link_enable_disable_one_port(testbed):
    """
    Test Name: test_poe_link_enable_disable_one_port
    Test Suite: suite_poe
    Test Overview: test enable and disable one poe port
    Test Procedure:
    1. for all the discovered devices and one poe ports
    2. if the port is poe disabled then enabled it
    3. disable the poe port and check if it got disabled
    """
    for dev in testbed.discovery_report.duts:
        dev = await tb_get_device_object_from_dut(testbed, dev)
        if not dev:
            continue
        out = await Poectl.show(
            input_data=[{dev.host_name: [{"cmd_options": "-j -a"}]}],
            parse_output=True,
        )
        if out[0][dev.host_name]["rc"] != 0:
            dev.applog.info(f"{dev.host_name} Not a POE device")
            continue
        ports = out[0][dev.host_name]["parsed_output"]
        for data in ports:
            port = data["swp"]
            if data["status"] == "disabled":
                out = await Poectl.enable(
                    input_data=[{dev.host_name: [{"port": data["swp"]}]}],
                )
                assert (
                    out[0][dev.host_name]["rc"] == 0
                ), f"Failed to enable POE port {dev.host_name}"
                time.sleep(2)
            out = await Poectl.disable(
                input_data=[{dev.host_name: [{"port": data["swp"]}]}],
            )
            assert out[0][dev.host_name]["rc"] == 0, f"Failed to disable POE port {dev.host_name}"
            time.sleep(2)
            out = await Poectl.show(
                input_data=[{dev.host_name: [{"port": data["swp"], "cmd_options": "-j"}]}],
                parse_output=True,
            )
            assert out[0][dev.host_name]["rc"] == 0, f"Failed to show POE port {dev.host_name}"
            new_info = out[0][dev.host_name]["parsed_output"]
            assert (
                new_info[0]["status"] == "disabled"
            ), f"Failed to disable poe_port-{port} {dev.host_name}"
            # checkif the state looks good.
            out = await Poectl.enable(
                input_data=[{dev.host_name: [{"port": data["swp"]}]}],
            )
            assert out[0][dev.host_name]["rc"] == 0, f"Failed to enable POE port {dev.host_name}"
            time.sleep(2)


@pytest.mark.asyncio
async def test_poe_link_enable_disable_all_ports(testbed):
    """
    Test Name: test_poe_link_enable_disable_all_ports
    Test Suite: suite_poe
    Test Overview: enable and disable all poe ports
    Test Procedure:
    1. for all the discovered devices and for all the poe ports
    2. if the port is poe disabled then enabled it
    3. disable the poe port and check if it got disabled
    """
    for dev in testbed.discovery_report.duts:
        dev = await tb_get_device_object_from_dut(testbed, dev)
        if not dev:
            continue
        out = await Poectl.show(
            input_data=[{dev.host_name: [{"cmd_options": "-j -a"}]}],
            parse_output=True,
        )
        if out[0][dev.host_name]["rc"] != 0:
            dev.applog.info(f"{dev.host_name} Not a POE device")
            continue
        ports = out[0][dev.host_name]["parsed_output"]
        first = ports[0]["swp"]
        last = ports[-1]["swp"]
        out = await Poectl.disable(
            input_data=[{dev.host_name: [{"port": f"{first}-{last}"}]}],
        )
        assert out[0][dev.host_name]["rc"] == 0, f"Failed to disable POE port {dev.host_name}"
        out = await Poectl.show(
            input_data=[{dev.host_name: [{"port": f"{first}-{last}", "cmd_options": "-j"}]}],
            parse_output=True,
        )
        assert out[0][dev.host_name]["rc"] == 0, f"Failed to show {dev.host_name}"

        ports = out[0][dev.host_name]["parsed_output"]
        for port in ports:
            assert port["status"] == "disabled", f"Failed to disable {first}-{last} {dev.host_name}"

        out = await Poectl.enable(
            input_data=[{dev.host_name: [{"port": f"{first}-{last}"}]}],
        )
        assert out[0][dev.host_name]["rc"] == 0, f"Failed to enable POE port {dev.host_name}"
        out = await Poectl.show(
            input_data=[{dev.host_name: [{"port": f"{first}-{last}", "cmd_options": "-j"}]}],
            parse_output=True,
        )
        assert out[0][dev.host_name]["rc"] == 0, f"Failed to show {dev.host_name}"
        for port in ports:
            assert port["status"] != "disabled", f"Failed to enabled {first}-{last} {dev.host_name}"


@pytest.mark.asyncio
async def test_poe_link_enable_disable_connected_ports(testbed):
    """
    Test Name: test_poe_link_enable_disable_connected_ports
    Test Suite: suite_poe
    Test Overview: Enable and disable the connected poe ports
    Test Procedure:
    1. look for switch that have ports connected
    2. disable the port and the port should go down
    3. the endpoint on the other end should go down
    """

    for dev in testbed.discovery_report.duts:
        dev = await tb_get_device_object_from_dut(testbed, dev)
        if not dev:
            continue
        out = await Poectl.show(
            input_data=[{dev.host_name: [{"cmd_options": "-j -a"}]}],
            parse_output=True,
        )
        if out[0][dev.host_name]["rc"] != 0:
            dev.applog.info(f"{dev.host_name} Not a POE device")
            continue
        ports = out[0][dev.host_name]["parsed_output"]
        for port in ports:
            if port["status"] != "connected":
                continue
            out = await IpLink.show(
                input_data=[{dev.host_name: [{"device": port["swp"], "cmd_options": "-j"}]}],
                parse_output=True,
            )
            assert out[0][dev.host_name]["rc"] == 0
            ports = out[0][dev.host_name]["parsed_output"]
            assert ports[0]["operstate"] == "UP", f"Link is not UP {dev.host_name}"

            out = await Poectl.disable(
                input_data=[{dev.host_name: [{"port": port["swp"]}]}],
            )
            assert out[0][dev.host_name]["rc"] == 0, f"Failed to disable POE port {dev.host_name}"
            time.sleep(5)
            out = await IpLink.show(
                input_data=[{dev.host_name: [{"device": port["swp"], "cmd_options": "-j"}]}],
                parse_output=True,
            )
            assert out[0][dev.host_name]["rc"] == 0
            ports = out[0][dev.host_name]["parsed_output"]
            assert ports[0]["operstate"] != "UP", f"Link is still UP {dev.host_name}"

            out = await Poectl.enable(
                input_data=[{dev.host_name: [{"port": port["swp"]}]}],
            )
            assert out[0][dev.host_name]["rc"] == 0, f"Failed to disable POE port {dev.host_name}"
            time.sleep(30)

            out = await IpLink.show(
                input_data=[{dev.host_name: [{"device": port["swp"], "cmd_options": "-j"}]}],
                parse_output=True,
            )
            assert out[0][dev.host_name]["rc"] == 0
            ports = out[0][dev.host_name]["parsed_output"]
            assert ports[0]["operstate"] == "UP", f"Link is not UP {dev.host_name}"
