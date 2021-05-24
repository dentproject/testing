# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import time

import pytest

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.utils.test_utils.bonding_utils import (
    bonding_get_interconnected_infra_devices,
    bonding_setup,
)

pytestmark = pytest.mark.suite_bonding


@pytest.mark.asyncio
async def test_alpha_lab_bonding_min_links(testbed):
    # get the infra devices that are inter connected to each other.
    infra_devices = await bonding_get_interconnected_infra_devices(testbed, testbed.devices)
    if not infra_devices:
        print("The testbed does not have enough infra devices with interconnected links")
        return

    await bonding_setup(infra_devices)

    # test minimum links function
    # ip link add bond0 type bond
    # ip link set bond0 type bond mode active-backup min_links 2
    # ip link set swp47 down
    # ip link set swp47 master bond0
    # ip link set swp48 down
    # ip link set swp48 master bond0
    # ip link set bond0 up
    # Set 2 minimum links,
    # kill a link
    # the port channel interface should drop
    for dd in infra_devices:
        for cmd in [
            "ip link del bond0 type bond || true",
            "ip link add bond0 type bond",
            "ip link set bond0 type bond mode 802.3ad min_links 2",
        ]:
            rc, out = await dd.run_cmd(cmd, sudo=True)
            assert rc == 0, f"failed to run {cmd} rc {rc} out {out}"
        for dd2, links in dd.links_dict.items():
            if dd2 not in testbed.devices_dict:
                continue
            if testbed.devices_dict[dd2].type != DeviceType.INFRA_SWITCH:
                continue
            for swp in links[0]:
                for cmd in [
                    f"ip link set {swp} down",
                    f"ip link set {swp} master bond0",
                    f"ip link set {swp} up",
                ]:
                    rc, out = await dd.run_cmd(cmd, sudo=True)
                    dd.applog.info(f"Ran {cmd} with rc {rc} {out}")
        for cmd in [
            f"ip link set bond0 up",
            f"brctl addif bridge bond0",
            f"bridge vlan add dev bond0 vid 100",
        ]:
            rc, out = await dd.run_cmd(cmd, sudo=True)
            dd.applog.info(f"Ran {cmd} with rc {rc} {out}")
    # cat /proc/net/bonding/bond0
    # ~ (tunkated output)
    # MII Status: up  <<<<<<< this will show down
    # ~
    # Min links: 2  <<<<<<< this will show as 2 vs 0
    # ~
    for dd in infra_devices:
        cmd = "cat /proc/net/bonding/bond0"
        rc, out = await dd.run_cmd(cmd, sudo=True)
        dd.applog.info(f"Bond interface status {out}")
        # TODO add verification from the output
    await bonding_setup(infra_devices, state="up")
