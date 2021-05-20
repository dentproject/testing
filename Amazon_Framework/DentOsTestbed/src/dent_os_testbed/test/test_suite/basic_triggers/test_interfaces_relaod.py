# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import re
import time

import pytest

from dent_os_testbed.lib.interfaces.interface import Interface
from dent_os_testbed.utils.decorators import TestCaseSetup
from dent_os_testbed.utils.test_suite.tb_utils import tb_get_device_object_from_dut

pytestmark = pytest.mark.suite_basic_trigger

# @TestCaseSetup(perf_thresholds={"CPU": {"usr": (0.0, 50.0)}})
@pytest.mark.asyncio
async def test_reload_interface(testbed):
    """
    1. Create list of dummy inteface file list
    2. upload it to the switch
    3. do a reload
    """
    if not testbed.discovery_report:
        testbed.applog.info("Discovery report not available, skipping test_switch_reload")
        return

    for i, dev in enumerate(testbed.discovery_report.duts):
        device = await tb_get_device_object_from_dut(testbed, dev)
        if not device:
            continue
        device.applog.info(
            "{} has {} interface".format(
                testbed.discovery_report.duts[i].device_id,
                len(dev.network.layer1.links),
            )
        )
        fname = "interfaces." + dev.device_id
        old_fname = "interfaces." + dev.device_id + ".old"
        fp = open(fname, "w")
        for obj in dev.network.layer1.links.filter(fn=lambda x: re.compile("swp*").match(x.ifname)):
            fp.write("auto " + obj.ifname + "\n")
            fp.write("   link-down yes\n")
        fp.close()

        # copy the original file
        device.applog.info("Getting the original interface file")
        await device.scp(old_fname, "/etc/network/interfaces", remote_to_local=True)
        device.applog.info("Uploading the interface config")
        await device.scp(fname, "/etc/network/interfaces")

        # do a reload
        device.applog.info("Performing the reload")
        out = await Interface.reload(input_data=[{dev.device_id: [{"options": "-a"}]}])
        if out[0][dev.device_id]["rc"] == 0:
            device.applog.info(out)
        else:
            device.applog.error(out)
        time.sleep(4)
        # copy back the original file.
        device.applog.info("Reverting to the original file")
        await device.scp(old_fname, "/etc/network/interfaces")
        # do a reload with old interfce file
        device.applog.info("Reloading interface")
        out = await Interface.reload(input_data=[{dev.device_id: [{"options": "-a"}]}])
        time.sleep(4)
