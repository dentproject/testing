# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import json
import os
import re
import time

import pytest

from dent_os_testbed.utils.test_suite.tb_utils import tb_get_device_object_from_dut

pytestmark = pytest.mark.suite_cleanup


def console_log_analyzer(dev, file):
    # check for back trace
    pattern = re.compile("------------[ cut here ]------------")
    for line in open(file):
        for match in re.finditer(pattern, line):
            print(line)
            return -1
    return 0


@pytest.mark.asyncio
async def test_collect_logs(testbed):
    """
    1. iterate thru the devices and get the logs
    2. collect the logs from the online device.
    """
    if not testbed.discovery_report:
        testbed.applog.info(
            f"Discovery report not present, +" "skipping run_test in {test_collect_logs.__func__}"
        )
        return
    files = [
        "/etc/network/interfaces",
        "/etc/frr/frr.conf",
        "/var/log/messages",
        "/var/log/syslog",
        "/var/log/autoprovision",
        "/var/log/frr/frr.log",
        "/var/tmp/dmesg",
        "/var/tmp/boot-0.log",
    ]
    file_analyzers = {
        "/var/tmp/boot-0.log": console_log_analyzer,
    }

    # copy to temp so that everyone can read
    for dev in testbed.discovery_report.duts:
        device = await tb_get_device_object_from_dut(testbed, dev)
        if not device:
            continue
        await device.run_cmd("dmesg > /var/tmp/dmesg", sudo=True)
        await device.run_cmd("journalctl -b 0 > /var/tmp/boot-0.log", sudo=True)
        for f in files + device.files_to_collect:
            fname = f.split("/")[-1]
            await device.run_cmd(f"cp {f} /tmp/{fname}", sudo=True)
            await device.run_cmd(f"chmod 755 /tmp/{fname}", sudo=True)

    for dev in testbed.discovery_report.duts:
        device = await tb_get_device_object_from_dut(testbed, dev)
        if not device:
            continue
        for f in files + device.files_to_collect:
            l_f = f.split("/")[-1]
            r_f = os.path.join("/tmp", l_f)
            l_f = os.path.join(device.serial_logs_base_dir, l_f)
            device.applog.info("Getting the remote file " + r_f)
            device.applog.info(f"Copying file {r_f} to {l_f}")
            try:
                await device.scp(l_f, r_f, remote_to_local=True)
                if f in file_analyzers:
                    ret = file_analyzers[f](device, l_f)
                    assert ret == 0, f"Found Errors in {f} on {device.host_name}"
            except Exception as e:
                device.applog.error(str(e))
