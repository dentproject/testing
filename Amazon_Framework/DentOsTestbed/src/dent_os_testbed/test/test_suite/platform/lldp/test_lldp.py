import time

import pytest

from dent_os_testbed.lib.poe.poectl import Poectl
from dent_os_testbed.utils.test_suite.tb_utils import tb_get_device_object_from_dut

pytestmark = pytest.mark.suite_lldp


@pytest.mark.asyncio
async def test_lldp_neighor(testbed):
    for dis_dev in testbed.discovery_report.duts:
        dev = await tb_get_device_object_from_dut(testbed, dis_dev)
        if not dev:
            continue
        dev.applog.info(dis_dev.platform.lldp.interfaces)
