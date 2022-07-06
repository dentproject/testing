import json
import os
import time

import pytest

from testbed.lib.interfaces.interface import Interface
from testbed.lib.os.service import Service
from testbed.utils.test_utils.tb_utils import (
    tb_device_check_health,
    tb_flap_links,
    tb_get_all_devices,
    tb_reset_ssh_connections,
)

pytestmark = pytest.mark.suite_system_wide_testing

TRIGGER_FLAP_LINK = "FLAP_LINK"
TRIGGER_RESTART_SERVICES = "RESTART_SERVICES"
TRIGGER_IFRELOAD = "IFRELOAD"


async def do_trigger(testbed, trigger_obj):
    trigger = trigger_obj[0]
    device = trigger_obj[1].pop(0)
    if trigger == TRIGGER_FLAP_LINK:
        device.applog.info(f"Triggering Port Flap in {device.host_name}")
        await tb_flap_links(device, "swp")
    elif trigger == TRIGGER_RESTART_SERVICES:
        services = [
            # "frr.service",
            "IhmDentTcFlower",
            # "networking",
        ]
        for s in services:
            input_data = [{device.host_name: [{"name": s}]}]
            out = await Service.show(
                input_data=input_data,
            )
            if out[0][device.host_name]["rc"]:
                device.applog.info(f"{s} not running on {device.host_name}")
                continue
            out = await Service.restart(
                input_data=input_data,
            )
            assert out[0][device.host_name]["rc"] == 0, f"Failed to restart the service {s} {out}"
            device.applog.info("zzZZZ(60s)")
            time.sleep(60)
            out = await Service.show(
                input_data=input_data,
            )
            assert (
                out[0][device.host_name]["rc"] == 0
            ), f" service didnt come up {s} {out} on {device.host_name}"
    elif trigger == TRIGGER_IFRELOAD:
        out = await Interface.reload(input_data=[{device.host_name: [{"options": "-a"}]}])
        assert out[0][device.host_name]["rc"] == 0, f"Failed to ifreload -a "
        device.applog.info(out)
    else:
        device.applog.info(f"unknown trigger {trigger} on {device.host_name}")
    # put the device back to the end
    trigger_obj[1].append(device)
    trigger_obj[2] += 1


@pytest.mark.asyncio
async def test_system_wide_restart_and_service_reloads(testbed):
    """
    Test Name: test_system_wide_restart_and_service_reloads
    Test Suite: suite_system_wide_testing
    Test Overview: To test restarting services (DentTcFlower) and ifreload
    Test Procedure:
     1. Get all the the reachable devices
     2. get health of each of the devices
     3. In each iteration restart the services and ifreload on a single dvice
     4. check the health and it should match before the restart
    """
    devices = []
    prev_dut_state = {}
    for dev in await tb_get_all_devices(testbed):
        if dev.os != "dentos":
            testbed.applog.info(f"Skipping {dev.host_name} since its {dev.os}")
            continue
        prev_dut_state[dev.host_name] = await tb_device_check_health(dev, None, False)
        devices.append(dev)

    # after traffic is stopped
    trigger_types = [
        # TRIGGER_FLAP_LINK,
        TRIGGER_RESTART_SERVICES,
        TRIGGER_IFRELOAD,
    ]
    triggers = []
    for trigger in trigger_types:
        t = [trigger, [], 1]
        for dev in devices:
            t[1].append(dev)
        triggers.append(t)

    count = 10
    while count:
        """
        - For each triggers test the traffic is working or not.
        """
        # check the system

        # analyze logs
        trigger = triggers.pop(0)
        await do_trigger(testbed, trigger)
        testbed.applog.info(f"zzzZZZ Iteration {count} next trigger {triggers[0]}")
        time.sleep(60)
        # check the system state
        await tb_reset_ssh_connections(devices)
        for device in devices:
            # disconnect and try now
            await tb_device_check_health(device, prev_dut_state[device.host_name], True)
        triggers.append(trigger)
        count -= 1
