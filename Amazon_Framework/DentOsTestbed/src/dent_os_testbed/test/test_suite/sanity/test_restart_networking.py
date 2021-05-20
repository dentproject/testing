import json
import os
import time

import pytest

from dent_os_testbed.lib.interfaces.interface import Interface
from dent_os_testbed.utils.test_suite.tb_utils import (
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
            "IhmDentTcFlower.service",
            # "networking",
        ]
        for s in services:
            rc, out = await device.run_cmd(f"systemctl status {s}", sudo=True)
            if rc != 0:
                device.applog.info(f"{s} not running on {device.host_name}")
                continue
            rc, out = await device.run_cmd(f"systemctl restart {s}", sudo=True)
            assert rc == 0, f"Failed to restart the service {s} {out}"
            device.applog.info("zzZZZ(60s)")
            time.sleep(60)
            rc, out = await device.run_cmd(f"systemctl status {s}", sudo=True)
            assert rc == 0, f" service didnt come up {s} {out} on {device.host_name}"
    elif trigger == TRIGGER_IFRELOAD:
        rc, out = await device.run_cmd(f"ifreload -a", sudo=True)
        assert rc == 0, f"Failed to ifreload -a {rc} {out} on {device.host_name}"
        device.applog.info(out)
    else:
        device.applog.info(f"unknown trigger {trigger} on {device.host_name}")
    # put the device back to the end
    trigger_obj[1].append(device)
    trigger_obj[2] += 1


@pytest.mark.asyncio
async def test_system_wide_restart_and_service_reloads(testbed):
    """
    - on each device
    -  do the following trigger
      - reboot
      - restaert networking
      -
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

    count = 25
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
