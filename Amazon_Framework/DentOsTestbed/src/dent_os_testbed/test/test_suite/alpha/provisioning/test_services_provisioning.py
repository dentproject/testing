# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import time

import pytest

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.utils.test_utils.sanity_utils import check_ntp_sync, check_services
from dent_os_testbed.utils.test_utils.tb_utils import (
    tb_device_onie_install,
    tb_get_all_devices,
    tb_reset_ssh_connections,
)

pytestmark = pytest.mark.suite_provisioning


@pytest.mark.asyncio
async def test_alpha_lab_provisioning_services_ntp(testbed):
    if not testbed.args.use_pssh:
        testbed.applog.info(f"Skipping test since not on provisioned setup")
        return
    # pick a infra switch then run onie-select this should trigger the network based boot
    devices = await tb_get_all_devices(testbed)
    for dev in devices:
        if dev.type not in [DeviceType.INFRA_SWITCH]:
            continue
        # test just on this infra and should be good.
        # delete the files for
        await tb_device_onie_install(dev)
        time.sleep(10 * 60)
        await tb_reset_ssh_connections(devices)
        # now check if we can make some connection to it.
        if not await dev.is_connected():
            assert 0, f"Device {dev.host_name} didnt boot up with new image from USB"
        # check ntp sync has happened
        rc = await check_ntp_sync(dev, None)
        assert rc, f"NTP Sync has failed."


@pytest.mark.asyncio
async def test_alpha_lab_provisioning_services_dhcp(testbed):
    if not testbed.args.use_pssh:
        testbed.applog.info(f"Skipping test since not on provisioned setup")
        return
    # pick a infra switch then run onie-select this should trigger the network based boot
    devices = await tb_get_all_devices(testbed)
    for dev in devices:
        if dev.type not in [DeviceType.INFRA_SWITCH]:
            continue
        # test just on this infra and should be good.
        # delete the files for
        await tb_device_onie_install(dev)
        time.sleep(15 * 60)
        await tb_reset_ssh_connections(devices)
        # now check if we can make some connection to it.
        if not await dev.is_connected():
            assert 0, f"Device {dev.host_name} didnt boot up with new image from USB"
        # check if the dhcp service is up and running
        rc = await check_services(dev, None)
        assert rc, f"NTP Sync has failed."
