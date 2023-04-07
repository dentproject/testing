# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#


import pytest

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.utils.test_utils.tb_utils import tb_device_check_services, tb_get_all_devices

pytestmark = pytest.mark.suite_services


@pytest.mark.asyncio
async def test_alpha_lab_services_dhcp(testbed):
    """
    Test Name: test_alpha_lab_services_dhcp
    Test Suite: suite_services
    Test Overview: test for DHCP service
    Test Procedure:
    1. check for dhcp services on OOB and infra devices
    """
    if not testbed.args.is_provisioned:
        testbed.applog.info(f'Skipping test since not on provisioned setup')
        return
    # Several devices need to be DHCP servers (OOBs and RSWs), validate service
    #   can be run on the devices (see also ECU tests and provisioning tests for additional tests on this)
    # enable DHCP service
    # Clients should be able to gain an IP address, and any other dhcp options sent (see client section
    #   of interoperability)
    devices = await tb_get_all_devices(testbed)
    for dev in devices:
        # these services should run on these devices
        if dev.type in [DeviceType.INFRA_SWITCH, DeviceType.ROUTER_SWITCH]:
            await tb_device_check_services(dev, None, True, ['isc-dhcp-server.service'])
        if dev.type in [DeviceType.OUT_OF_BOUND_SWITCH]:
            await tb_device_check_services(dev, None, True, ['onie-dhcp.service'])
        # verification TODO
        # check the leases given out of these devices and check if they match with other devices on the n/w
