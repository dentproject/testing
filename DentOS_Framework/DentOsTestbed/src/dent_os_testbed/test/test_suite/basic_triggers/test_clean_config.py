import asyncio
import os

import pytest

from dent_os_testbed.lib.os.service import Service
from dent_os_testbed.utils.test_utils.tb_utils import (
    check_asyncio_results,
    tb_clean_config,
    tb_get_all_devices,
)

pytestmark = pytest.mark.suite_clean_config


async def disable_ztp(device):
    await device.run_cmd('rm -f /etc/network/if-up.d/ntpdate || true')
    for s in ['snmpd']:
        input_data = [{device.host_name: [{'name': s}]}]
        await Service.stop(
            input_data=input_data,
        )
        await Service.disable(
            input_data=input_data,
        )


async def setup_dent_tools(device, package):
    # copy on to the device.
    await device.scp(package, '~/staging.tar.gz')
    # extract the artifacts
    await device.run_cmd('tar xvf staging.tar.gz')
    # install the tc tool chain
    await device.run_cmd('./tc_install.sh &> /dev/null')
    # install the poe tool chain
    await device.run_cmd('./poe_install.sh &> /dev/null')
    # install the stress package tool chain
    await device.run_cmd('./stress_install.sh &> /dev/null')


@pytest.mark.asyncio
async def test_clean_config(testbed):
    """
    Test Name: test_clean_config
    Test Suite: suite_clean_config
    Test Overview: Clean Configure the reachable devices. Note: this should used only with non provisioned devices
    Test Procedure:
    1. get all the reachable devices
    2. disable ZTP
    3. setup tc, poe, stress packages
    """

    devices = await tb_get_all_devices(testbed)
    cos = []
    for device in devices:
        cos.append(disable_ztp(device))
    results = await asyncio.gather(*cos, return_exceptions=True)
    check_asyncio_results(results, 'disable_ztp')

    # Run only if required.
    package = '/home/neteng/staging/staging.tar.gz'
    if os.path.exists(package):
        cos = []
        for device in devices:
            cos.append(setup_dent_tools(device, package))
        results = await asyncio.gather(*cos, return_exceptions=True)
        check_asyncio_results(results, 'setup_dent_tools')

    await tb_clean_config(testbed)
