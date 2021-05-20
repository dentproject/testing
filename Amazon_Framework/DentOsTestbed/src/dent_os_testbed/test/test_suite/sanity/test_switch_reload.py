# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import json
import time

import progressbar
import pytest

from dent_os_testbed.lib.interfaces.interface import Interface
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.test.test_suite.sanity.test_check_links import check_and_validate_switch_links
from dent_os_testbed.utils.test_suite.tb_utils import tb_get_all_devices, tb_reset_ssh_connections

pytestmark = pytest.mark.suite_system_wide_testing


@pytest.mark.asyncio
async def test_switch_reload_all(testbed):
    """Reload the switch"""
    dut_state = {}
    devices = await tb_get_all_devices(testbed)
    for dev in devices:
        dev.applog.info("Performing the reload")
        out = await Interface.reload(input_data=[{dev.host_name: [{"options": "-a"}]}])
        if out[0][dev.host_name]["rc"] == 0:
            dev.applog.info(out)
        else:
            dev.applog.error(out)
    for dev in devices:
        out = await IpLink.show(
            input_data=[{dev.host_name: [{"cmd_options": "-j"}]}],
        )
        assert out[0][dev.host_name]["rc"] == 0, f"Failed to get Links on {dev.host_name}"
        links = json.loads(out[0][dev.host_name]["result"])
        links = {l["ifname"]: l for l in links}
        host = dev.host_name
        dut_state[host] = links
        # check to see if the ports are up
        for i in range(1, 49):
            if f"swp{i}" not in links:
                assert 0, f"Link swp{i} not seen on {host}"

    for i in range(1, 5):
        testbed.applog.info(
            f"********************** Reboot_ALL ITERATION {i} ************************"
        )
        await check_and_validate_switch_links(testbed)
        for dev in devices:
            out = await IpLink.show(
                input_data=[{dev.host_name: [{"cmd_options": "-j"}]}],
            )
            assert out[0][dev.host_name]["rc"] == 0, f"Failed to get Links on {dev.host_name}"
            links = json.loads(out[0][dev.host_name]["result"])
            links = {l["ifname"]: l for l in links}
            host = dev.host_name

            # compare here
            for k, v in dut_state[host].items():
                dev.applog.info(
                    "{} Link {} state prev {} current {}".format(
                        host, k, v["operstate"], links[k]["operstate"]
                    )
                )
                # enable this to enable check other links as well
                # if v["operstate"] != links[k]["operstate"]:
                #    assert 0, "{} Link {} state not same prev {} current {}".format(
                #        host, k, v["operstate"], links[k]["operstate"]
                #    )

        for dev in devices:
            rc, out = await dev.run_cmd(f"shutdown -r +1", sudo=True)

        await tb_reset_ssh_connections(devices)
        testbed.applog.info("zzzZZZ! (5min)")
        for i in progressbar.progressbar(range(5)):
            time.sleep(60)


@pytest.mark.asyncio
async def test_switch_reload_one_switch(testbed):
    """Reload the switch"""
    dut_state = {}
    devices = await tb_get_all_devices(testbed)
    for dev in devices:
        dev.applog.info("Performing the reload")
        out = await Interface.reload(input_data=[{dev.host_name: [{"options": "-a"}]}])
        if out[0][dev.host_name]["rc"] == 0:
            dev.applog.info(out)
        else:
            dev.applog.error(out)
    for dev in devices:
        out = await IpLink.show(
            input_data=[{dev.host_name: [{"cmd_options": "-j"}]}],
        )
        assert out[0][dev.host_name]["rc"] == 0, f"Failed to get Links on {dev.host_name}"
        links = json.loads(out[0][dev.host_name]["result"])
        links = {l["ifname"]: l for l in links}
        host = dev.host_name
        dut_state[host] = links
        # check to see if the ports are up
        for i in range(1, 49):
            if f"swp{i}" not in links:
                assert 0, f"Link swp{i} not seen on {host}"

    for i in range(1, 5):
        testbed.applog.info(
            f"********************** Reboot_ONE ITERATION {i} ************************"
        )
        for dev in devices:
            # reboot this node
            rc, out = await dev.run_cmd(f"shutdown -r +1", sudo=True)
            await tb_reset_ssh_connections(devices)
            testbed.applog.info("zzzZZZ! (5min)")
            for i in progressbar.progressbar(range(5)):
                time.sleep(60)
            # now check the links on all the nodes.
            await check_and_validate_switch_links(testbed)
            for dev1 in devices:
                out = await IpLink.show(
                    input_data=[{dev1.host_name: [{"cmd_options": "-j"}]}],
                )
                assert out[0][dev1.host_name]["rc"] == 0, f"Failed to get Links on {dev1.host_name}"
                links = json.loads(out[0][dev1.host_name]["result"])
                links = {l["ifname"]: l for l in links}
                host = dev1.host_name

                # compare here
                for k, v in dut_state[host].items():
                    dev1.applog.info(
                        "{} Link {} state prev {} current {}".format(
                            host, k, v["operstate"], links[k]["operstate"]
                        )
                    )
                    # enable to check non essential links as well
                    # if v["operstate"] != links[k]["operstate"]:
                    #    assert 0, "{} Link {} state not same prev {} current {}".format(
                    #        host, k, v["operstate"], links[k]["operstate"]
                    #    )
