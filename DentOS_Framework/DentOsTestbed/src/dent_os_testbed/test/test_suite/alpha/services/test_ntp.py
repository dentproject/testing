# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#


import pytest

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.utils.test_utils.tb_utils import tb_device_check_services, tb_get_all_devices

pytestmark = pytest.mark.suite_services


@pytest.mark.asyncio
async def test_alpha_lab_services_ntp(testbed):
    """
    Test Name: test_alpha_lab_services_ntp
    Test Suite: suite_services
    Test Overview: test for ntp servcices on OOB and Dist devices
    Test Procedure:
    """
    if not testbed.args.is_provisioned:
        testbed.applog.info('Skipping test since not on provisioned setup')
        return
    # Several devices need to be NTP servers (OOBs and DIS), validate service can be run on the devices and
    #   clients can sync (see also ECU tests and provisioning tests for additional tests on this)
    # enable NTP service
    # Clients should be able to sync their clocks.
    #  Clients should also be able to see stable sync without a large number of shifts due to clocking issues
    #  CPU load should be low even under load (see client interoperability test section)
    devices = await tb_get_all_devices(testbed)
    for dev in devices:
        # these services should run on these devices
        if dev.type in [DeviceType.OUT_OF_BOUND_SWITCH, DeviceType.DISTRIBUTION_ROUTER]:
            await tb_device_check_services(dev, None, True, ['ntp.service'])
        # the ntp on others should have synced from one of the above OOB or DIST
        # TODO
