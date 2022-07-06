import time

import pytest

from testbed.lib.ip.ip_link import IpLink
from testbed.lib.poe.poectl import Poectl
from testbed.utils.test_utils.tb_utils import tb_get_all_devices

pytestmark = pytest.mark.suite_alpha_poe


@pytest.mark.asyncio
async def test_alpha_lab_poe_enable_disable_ports(testbed):
    """
    Test Name: test_alpha_lab_poe_enable_disable_ports
    Test Suite: suite_alpha_poe
    Test Overview: test poe ports enable/disable
    Test Procedure:
    1. get all the reachable devices
    2. for all the poe ports check disabled ports then enable them.
    """
    for dev in await tb_get_all_devices(testbed):
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
async def test_alpha_lab_poe_enable_disable_all_ports(testbed):
    """
    Test Name: test_alpha_lab_poe_enable_disable_all_ports
    Test Suite: suite_alpha_poe
    Test Overview: test disable all ports
    Test Procedure:
    1. get all the connected devices
    2. disable/enable all the poe ports
    """

    for dev in await tb_get_all_devices(testbed):
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
        ports = out[0][dev.host_name]["parsed_output"]
        for port in ports:
            assert port["status"] != "disabled", f"Failed to enabled {first}-{last} {dev.host_name}"


@pytest.mark.asyncio
async def test_alpha_lab_poe_enable_disable_connected_ports(testbed):
    """
    Test Name: test_alpha_lab_poe_enable_disable_connected_ports
    Test Suite: suite_alpha_poe
    Test Overview: enable/disable connected ports.
    Test Procedure:
    """

    """
    - look for switch that have ports connected
    - disable the port and the port should go down
    - the endpoint on the other end should go down
    -
    """

    for dev in await tb_get_all_devices(testbed):
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
            # assert ports[0]["operstate"] == "UP", f"Link is not UP {dev.host_name}"

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
            time.sleep(5)

            out = await IpLink.show(
                input_data=[{dev.host_name: [{"device": port["swp"], "cmd_options": "-j"}]}],
                parse_output=True,
            )
            assert out[0][dev.host_name]["rc"] == 0
            ports = out[0][dev.host_name]["parsed_output"]
            # assert ports[0]["operstate"] == "UP", f"Link is not UP {dev.host_name}"
