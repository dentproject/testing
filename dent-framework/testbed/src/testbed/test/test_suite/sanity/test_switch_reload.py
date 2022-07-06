# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import json
import time

import pytest

from testbed.lib.interfaces.interface import Interface
from testbed.lib.ip.ip_link import IpLink
from testbed.lib.os.system import System
from testbed.test.test_suite.sanity.test_check_links import check_and_validate_switch_links
from testbed.utils.test_utils.tb_utils import (
    tb_check_all_devices_are_connected,
    tb_get_all_devices,
    tb_reset_ssh_connections,
)

pytestmark = pytest.mark.suite_system_wide_testing


@pytest.mark.asyncio
async def test_switch_reload_all(testbed):
    """
    Test Name: test_switch_reload_all
    Test Suite: suite_system_wide_testing
    Test Overview: reload all the devices and expect the links to come back UP
    Test Procedure:
    1. get all the reachable devices
    2. get the link status of the links for each device
    3. reload all the devices
    4. check if all the links that were UP before reboot came back UP
    5. repeat this atleast 5 times.
    """
    dut_state = {}
    bgp_state = {}

    assert (
        await tb_check_all_devices_are_connected(testbed.devices) == True
    ), "All devices are not connected"

    devices = await tb_get_all_devices(testbed)
    for dev in devices:
        dev.applog.info("Performing the reload")
        out = await Interface.reload(input_data=[{dev.host_name: [{"options": "-a"}]}])
        if out[0][dev.host_name]["rc"] == 0:
            dev.applog.info(out)
        else:
            dev.applog.error(out)

    # wait for a min to settle down
    time.sleep(60)

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
        for i in range(1, 24):
            if f"swp{i}" not in links:
                assert 0, f"Link swp{i} not seen on {host}"
        cmd = "sudo vtysh -c 'show ip bgp summ json'"
        rc, out = await dev.run_cmd(cmd)
        assert rc == 0, f"Could not run the {cmd}"
        bgp_state[host] = json.loads(out)

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

            cmd = "sudo vtysh -c 'show ip bgp summ json'"
            rc, out = await dev.run_cmd(cmd)
            assert rc == 0, f"Could not run the {cmd}"
            data = json.loads(out)
            peers = data["ipv4Unicast"]["peers"]
            for k,v in bgp_state[host]["ipv4Unicast"]["peers"].items():
                if v["state"] in ["Connect", "Active"]:
                    # no need to check these out.
                    continue
                if v["state"] != peers[k]["state"]:
                    assert 0, "peer {} state has changed from {} to {}".format(k, v["state"], peers[k]["state"])

            # compare here
            for k, v in dut_state[host].items():
                dev.applog.info(
                    "{} Link {} state prev {} current {}".format(
                        host, k, v["operstate"], links[k]["operstate"]
                    )
                )
                ## enable this to enable check other links as well
                #if v["operstate"] != links[k]["operstate"]:
                #    assert 0, "{} Link {} state not same prev {} current {}".format(
                #        host, k, v["operstate"], links[k]["operstate"]
                #    )

        for dev in devices:
            await System.shutdown(input_data=[{dev.host_name: [{"options": "-r +1"}]}])

        await tb_reset_ssh_connections(devices)
        testbed.applog.info("zzzZZZ! (5min)")
        for i in range(5):
            time.sleep(60)


@pytest.mark.asyncio
async def test_switch_reload_one_switch(testbed):
    """
    Test Name: test_switch_reload_one_switch
    Test Suite: suite_system_wide_testing
    Test Overview: reload one switch at a time and check the link status
    Test Procedure:
    1. get all the reachable devices
    2. get the link status of the links for each device
    3. reload one of the devices
    4. check if all the links that were UP before reboot came back UP
    5. repeat this atleast 5 times on different switches.
    """
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
        for i in range(1, 24):
            if f"swp{i}" not in links:
                assert 0, f"Link swp{i} not seen on {host}"

    for i in range(1, 5):
        testbed.applog.info(
            f"********************** Reboot_ONE ITERATION {i} ************************"
        )
        for dev in devices:
            # reboot this node
            out = await System.shutdown(input_data=[{dev.host_name: [{"options": "-r +1"}]}])
            await tb_reset_ssh_connections(devices)
            testbed.applog.info("zzzZZZ! (5min)")
            for i in range(5):
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


async def get_link_operstate(host_name, link):
    if host_name == "tgen":
        return "UP"
    out = await IpLink.show(
        input_data=[{host_name: [{"device": link, "cmd_options": "-j"}]}],
        parse_output=True,
    )
    assert out[0][host_name]["rc"] == 0
    # bond interface parent will take care of the UP/DOWN
    if (
        out[0][host_name]["parsed_output"][0]["operstate"] == "DOWN"
        and "SLAVE" in out[0][host_name]["parsed_output"][0]["flags"]
    ):
        return "UP"
    return out[0][host_name]["parsed_output"][0]["operstate"]


@pytest.mark.asyncio
async def _test_switch_reload_disr1_switch(testbed):
    dev_name = "dis_r1"
    if dev_name not in testbed.devices_dict:
        msg = f"SJC DISR2 could not be found cannot proceed "
        testbed.applog.info(msg)
        return
    dev = testbed.devices_dict[dev_name]

    cmd = "sudo onlpdump -S"
    rc, out = await dev.run_cmd(cmd)

    out = await IpLink.show(
        input_data=[{dev.host_name: [{"cmd_options": "-j"}]}],
    )
    assert out[0][dev.host_name]["rc"] == 0, f"Failed to get Links on {dev.host_name}"
    prev_links = json.loads(out[0][dev.host_name]["result"])
    prev_links = {l["ifname"]: l for l in prev_links}

    cmd = "sudo vtysh -c 'show ip bgp summ json'"
    rc, out = await dev.run_cmd(cmd)
    assert rc == 0, f"Could not run the {cmd}"
    prev_bgp = json.loads(out)

    for i in range(1, 2000):
        testbed.applog.info(
            f"********************** Reboot_ALL ITERATION {i} ************************"
        )
        #await System.shutdown(input_data=[{dev.host_name: [{"options": "-r +1"}]}])
        cmd = "for i in {1..8};do ip link set swp${i} down; done;"
        #cmd = "ip link set swp4 down"
        rc, out = await dev.run_cmd(cmd)
        assert rc == 0, f"Could not run the {cmd}"
        #
        time.sleep(2)
        cmd = "for i in {1..8};do ip link set swp${i} up; done;"
        #cmd = "ip link set swp4 up"
        rc, out = await dev.run_cmd(cmd)
        time.sleep(2)
        #
        # assert rc == 0, f"Could not run the {cmd}"
        #await tb_reset_ssh_connections([dev])
        #testbed.applog.info("zzzZZZ! (4min)")
        #for i in range(4):
        time.sleep(15)

        cmd = "sudo onlpdump -S"
        rc, out = await dev.run_cmd(cmd)
        out = await IpLink.show(
            input_data=[{dev.host_name: [{"cmd_options": "-j"}]}],
        )
        assert out[0][dev.host_name]["rc"] == 0, f"Failed to get Links on {dev.host_name}"
        cur_links = json.loads(out[0][dev.host_name]["result"])
        cur_links = {l["ifname"]: l for l in cur_links}
        for k, v in prev_links.items():
            dev.applog.info(
                "{} Link {} state prev {} current {}".format(
                    dev.host_name, k, v["operstate"], cur_links[k]["operstate"]
                )
            )
            # enable this to enable check other links as well
            if v["operstate"] != cur_links[k]["operstate"]:
                assert 0, "{} Link {} state not same prev {} current {}".format(
                    dev.host_name, k, v["operstate"], cur_links[k]["operstate"]
                )

        cmd = "vtysh -c 'show ip bgp summ json'"
        rc, out = await dev.run_cmd(cmd)
        assert rc == 0, f"Could not run the {cmd}"
        data = json.loads(out)
        peers = data["ipv4Unicast"]["peers"]
        #for swp in [ "15", "16", "17", "18","19", "20", "39", "40", "41", "42", "43", "44" ]:
        #   operstate = await get_link_operstate(dev.host_name, f"swp{swp}")
        #   assert operstate == "UP" , f"Link swp{swp} not UP operstate is  {operstate}"
        #   ip = f"10.2.{swp}.74"
        #   if ip not in peers:
        #       assert 0, f"Could not find the peer {i}"
        #   if peers[ip]["state"] != "Established":
        #       assert 0, f"peer {i} has no BGP established"

        for k,v in prev_bgp["ipv4Unicast"]["peers"].items():
            if v["state"] in ["Connect", "Active"]:
                # no need to check these out.
                continue
            if v["state"] != peers[k]["state"]:
                assert 0, "peer {} state has changed from {} to {}".format(k, v["state"], peers[k]["state"])
