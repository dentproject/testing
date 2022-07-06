import json
import time

import pytest

from testbed.lib.ip.ip_link import IpLink
from testbed.lib.ip.ip_route import IpRoute
from testbed.utils.decorators import TestCaseSetup
from testbed.utils.test_utils.tb_utils import tb_get_device_object_from_dut

pytestmark = pytest.mark.suite_iproute2


# @TestCaseSetup(
#     perf_thresholds={
#         "CPU": {"idle": (50.0, 100.0)},
#         "Memory": {"MemTotal": (0, 81308160)},
#         "Process": {"all": {"VmPeak": (0, 114680)}, "sshd": {"VmPeak": (0, 114680)}},
#     },
# )


@pytest.mark.asyncio
async def test_route_add_del(testbed):
    """
    Test Name: test_route_add_del
    Test Suite: suite_iproute2
    Test Overview: test ip route add
    Test Procedure:
    1. add a 10.20.30.40 route to the default gateway
    2. display the route
    3. delete the route
    """

    for dev in testbed.discovery_report.duts:
        dev = await tb_get_device_object_from_dut(testbed, dev)
        if not dev:
            continue
        out = await IpRoute.show(
            input_data=[{dev.host_name: [{"dst": "default", "cmd_options": "-j"}]}],
            parse_output=True,
        )
        assert out[0][dev.host_name]["rc"] == 0, f"No Default route on {dev.host_name}"
        default_route = out[0][dev.host_name]["parsed_output"]
        # delete any old route.
        out = await IpRoute.delete(
            input_data=[{dev.host_name: [{"dst": "10.20.30.40"}]}],
        )
        out = await IpRoute.add(
            input_data=[
                {dev.host_name: [{"dst": "10.20.30.40", "via": default_route[0]["gateway"]}]}
            ],
        )
        # assert out[0][dev.host_name]["rc"] == 0
        print(out)
        out = await IpRoute.show(
            input_data=[{dev.host_name: [{"dst": "10.20.30.40", "cmd_options": "-j"}]}],
        )
        assert out[0][dev.host_name]["rc"] == 0
        print(out)
        out = await IpRoute.delete(
            input_data=[{dev.host_name: [{"dst": "10.20.30.40"}]}],
        )
        # assert out[0][dev.host_name]["rc"] == 0
        print(out)
        out = await IpRoute.show(
            input_data=[{dev.host_name: [{"dst": "10.20.30.40", "cmd_options": "-j"}]}],
        )
        # assert out[0][dev.host_name]["rc"] == 0
        print(out)


# @TestCaseSetup(
#     perf_thresholds={
#         "CPU": {"idle": (50.0, 100.0)},
#         "Memory": {"MemTotal": (0, 81308160)},
#         "Process": {"all": {"VmPeak": (0, 114680)}, "sshd": {"VmPeak": (0, 114680)}},
#     },
# )
@pytest.mark.asyncio
async def test_link_up_down(testbed):
    """
    Test Name: test_link_up_down
    Test Suite: suite_iproute2
    Test Overview: test link up and down
    Test Procedure:
    1. get the list of discovered devices
    2. get the link status of all the links
    3. get a link that is UP
    4. bring down the link and check to see if the link went down
    5. bring back the link UP and check if the link came back up again.
    """

    if testbed.args.is_provisioned:
        testbed.applog.info(f"Skipping test since on provisioned setup")
        return

    for dev in testbed.discovery_report.duts:
        dev = await tb_get_device_object_from_dut(testbed, dev)
        if not dev:
            continue
        out = await IpLink.show(
            input_data=[{dev.host_name: [{"cmd_options": "-j"}]}],
        )
        assert out[0][dev.host_name]["rc"] == 0
        links = json.loads(out[0][dev.host_name]["result"])
        # Get a swp port that is up
        link = ""
        for l in links:
            if "sw" in l["ifname"] and l["operstate"] == "UP":
                link = l["ifname"]
                break
        if link == "":
            print("Not even single swp is UP")
            return

        out = await IpLink.show(
            input_data=[{dev.host_name: [{"device": link, "cmd_options": "-j"}]}],
        )
        assert out[0][dev.host_name]["rc"] == 0
        print(out)
        out = await IpLink.set(
            input_data=[{dev.host_name: [{"device": link, "operstate": "down"}]}],
        )
        assert out[0][dev.host_name]["rc"] == 0
        print(out)
        # wait for it to come down
        time.sleep(5)
        out = await IpLink.show(
            input_data=[{dev.host_name: [{"device": link, "cmd_options": "-j"}]}],
        )
        assert out[0][dev.host_name]["rc"] == 0
        print(out)
        out = await IpLink.set(
            input_data=[{dev.host_name: [{"device": link, "operstate": "up"}]}],
        )
        assert out[0][dev.host_name]["rc"] == 0
        print(out)
        # wait for it to come up
        time.sleep(5)
        out = await IpLink.show(
            input_data=[{dev.host_name: [{"device": link, "cmd_options": "-j"}]}],
        )
        assert out[0][dev.host_name]["rc"] == 0
        print(out)
