# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import time

import pytest

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.utils.test_utils.tb_utils import (
    tb_device_onie_install,
    tb_get_all_devices,
    tb_reset_ssh_connections,
)

pytestmark = pytest.mark.suite_provisioning


@pytest.mark.asyncio
async def test_alpha_lab_provisioning_install_os_over_usb(testbed):
    """
    Test Name: test_alpha_lab_provisioning_install_os_over_usb
    Test Suite: suite_provisioning
    Test Overview: test provisioning using USB
    Test Procedure:
    1. get the device that has USB
    2. start the onie-install from USB
    3. check for provisioning
    """
    if testbed.args.os_image_download_url is None:
        testbed.applog.info('OS Image Not provided')
        return
    os_image_download_url = testbed.args.os_image_download_url
    devices = await tb_get_all_devices(testbed)
    for dev in devices:
        # for each device
        #  if there is a USB bootable device inserted then
        #  mount the usb device cleanup the files
        rc, out = await dev.run_cmd('sudo fdisk  -l /dev/sdb')
        if rc != 0:
            continue
        #  download a copy of image to the USB
        #  do a onie-select install
        staging_path = '/media/INSTALLER/onie-installer-arm64'
        cmds = [
            'sudo -u root iptables -F',
            'sudo -u root tc filter delete block 1',
            'sudo -u root fsck -y /dev/sdb1',
            'sudo -u root mkdir /media/INSTALLER',
            'sudo -u root mount /dev/sdb1 /media/INSTALLER',
            f'sudo -u root rm -rf {staging_path}',
            'sudo -u root sync',
            f'sudo -u root wget {os_image_download_url} -O {staging_path}',
        ]
        for cmd in cmds:
            await dev.run_cmd(cmd)
        await tb_device_onie_install(dev)
        time.sleep(5 * 60)
        await tb_reset_ssh_connections(devices)
        # now check if we can make some connection to it.
        if not await dev.is_connected():
            assert 0, f'Device {dev.host_name} didnt boot up with new image from USB'
        return


@pytest.mark.asyncio
async def test_alpha_lab_provisioning_install_os_over_nw(testbed):
    """
    Test Name: test_alpha_lab_provisioning_install_os_over_nw
    Test Suite: suite_provisioning
    Test Overview: test OS over network
    Test Procedure:
    1. get and infra device
    2. do a onie-select install
    """
    #
    if not testbed.args.is_provisioned:
        testbed.applog.info('Skipping test since not on provisioned setup')
        return
    # pick a infra switch then run onie-select this should trigger the network based boot
    devices = await tb_get_all_devices(testbed)
    for dev in devices:
        if dev.type not in [DeviceType.INFRA_SWITCH]:
            continue
        # test just on this infra and should be good.
        await tb_device_onie_install(dev)
        time.sleep(10 * 60)
        await tb_reset_ssh_connections(devices)
        # now check if we can make some connection to it.
        if not await dev.is_connected():
            assert 0, f'Device {dev.host_name} didnt boot up with new image from USB'
        return
