# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import time

import pytest

from testbed.Device import DeviceType
from testbed.utils.test_utils.tb_utils import (
    tb_device_onie_install,
    tb_get_all_devices,
    tb_reset_ssh_connections,
)

pytestmark = pytest.mark.suite_provisioning


@pytest.mark.asyncio
async def test_alpha_lab_provisioning_config_install_over_nw(testbed):
    """
    Test Name: test_alpha_lab_provisioning_config_install_over_nw
    Test Suite: suite_provisioning
    Test Overview: test provisioning over network install
    Test Procedure:
    1. get an infra switch
    2. do a onie-select install on this device
    3. check for config files
    """
    if not testbed.args.is_provisioned:
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
        # check for configs downloaded here
        config_file_list = [
            "/etc/ntp.conf",
            "/etc/frr/frr.conf",
            "/etc/dhcp/dhcpd.conf",
            "/etc/frr/daemons",
            "/etc/hostname",
            "/etc/frr/vtysh.conf",
            "/etc/hosts",
            "/etc/resolv.conf",
            "/etc/network/interfaces",
            "/etc/ssh/sshd_config",
        ]
        for cfg in config_file_list:
            rc, out = await dev.run_cmd(f"sudo -u root ls {cfg}")
            assert rc == 0, f"Could not find the config file {cfg} on {dev.host_name}"
        return
