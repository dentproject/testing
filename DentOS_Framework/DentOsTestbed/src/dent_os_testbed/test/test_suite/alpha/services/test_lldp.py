# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#


import pytest

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.lib.lldp.lldp import Lldp
from dent_os_testbed.utils.test_utils.tb_utils import tb_get_all_devices

pytestmark = pytest.mark.suite_services


@pytest.mark.asyncio
async def test_alpha_lab_services_lldp(testbed):
    """
    Test Name: test_alpha_lab_services_lldp
    Test Suite: suite_services
    Test Overview: check for lldp services
    Test Procedure:
    1. check for lldp on infra devices
    """
    if not testbed.args.is_provisioned:
        testbed.applog.info('Skipping test since not on provisioned setup')
        return
    # Device should see LLDP advertisements, and display data in a properly formatted output
    # Connect LLDP devices, including cumulus devices
    # LLDP should accurately represent data
    devices = await tb_get_all_devices(testbed)
    for dev in devices:
        if dev.type not in [DeviceType.INFRA_SWITCH]:
            continue
        out = await Lldp.show(
            input_data=[{dev.host_name: [{'cmd_options': '-f json'}]}],
            parse_output=True,
        )
        dev.applog.info(out)
        assert out[0][dev.host_name]['rc'] == 0, f'Failed to get Lldp on {dev.host_name} {out}'
        assert len(
            out[0][dev.host_name]['parsed_output']
        ), f'No LLDP members on this device {dev.host_name}'
