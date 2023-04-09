# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import json
from json.decoder import JSONDecodeError

import pytest

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.lib.tc.tc_filter import TcFilter
from dent_os_testbed.utils.test_utils.tb_utils import (
    tb_get_all_devices,
)

pytestmark = pytest.mark.suite_acl_performance


@pytest.mark.asyncio
async def test_dentv2_acl_perf_json_fix(testbed):
    """
    Test Name: test_dentv2_acl_perf_json_fix
    Test Suite: suite_acl_performance
    Test Overview: test if the json output bug for policer in tc is fixed
    Test Procedure:
    1. check the fix for json output when a rate limiter is added to the tc action
    """

    devices = await tb_get_all_devices(testbed)
    infra_devices = []
    for dd in devices:
        if dd.type in [DeviceType.INFRA_SWITCH]:
            infra_devices.append(dd)
    if not infra_devices:
        print('The testbed does not have enough dent')
        return

    for dd in infra_devices:
        for swp in [link[0] for link in dd.links]:
            await TcFilter.add(
                input_data=[
                    {
                        dd.host_name: [
                            {
                                'block': 1,
                                'direction': 'ingress',
                                'protocol': 'ip',
                                'handle': 8314,
                                'pref': 1,
                                'filtertype': {
                                    'verbose': '',
                                    'skip_sw': '',
                                    'indev': swp,
                                    'ip_proto': 'udp',
                                    'src_port': 53,
                                },
                                'action': {
                                    'police': {
                                        'rate': '1kbps',
                                        'burst': 100,
                                        'conform-exceed': '',
                                        'drop': '',
                                    }
                                },
                            }
                        ]
                    }
                ]
            )
            out = await TcFilter.show(
                input_data=[{dd.host_name: [{'block': 1, 'options': '-json'}]}]
            )
            try:
                json.loads(out[0][dd.host_name]['result'])
            except JSONDecodeError:
                pytest.fail(f"json format error: {out[0][dd.host_name]['result']}")
