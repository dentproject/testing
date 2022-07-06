# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#


import pytest

from testbed.utils.test_utils.tb_utils import tb_collect_logs_from_devices

pytestmark = pytest.mark.suite_cleanup


@pytest.mark.asyncio
async def test_collect_logs(testbed):
    """
    Test Name: test_collect_logs
    Test Suite: suite_cleanup
    Test Overview: Collect the logs from the devices
    Test Procedure:
    1. Iterate through the discovered devices
    2. get all the vital log files and the files added by test cases.
      2.1 interfaces, frr.conf, messages, syslog, autoprovision, frr.log, dmesg
    """
    await tb_collect_logs_from_devices(testbed.devices)
