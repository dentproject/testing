# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import ipaddress
import json
import time
from itertools import islice
from json.decoder import JSONDecodeError

import pytest

from testbed.Device import DeviceType
from testbed.lib.tc.tc_chain import TcChain
from testbed.lib.tc.tc_filter import TcFilter
from testbed.utils.test_utils.tb_utils import (
    tb_get_all_devices,
    tb_reload_nw_and_flush_firewall,
)
from testbed.utils.test_utils.tgen_utils import (
    tgen_utils_create_devices_and_connect,
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_get_swp_info,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_protocols,
    tgen_utils_stop_traffic,
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
        print("The testbed does not have enough dent")
        return

    for dd in infra_devices:
        for swp in [link[0] for link in dd.links]:
            await TcFilter.add(
                input_data=[
                    {
                        dd.host_name: [
                            {
                                "block": 1,
                                "direction": "ingress",
                                "protocol": "ip",
                                "handle": 8314,
                                "pref": 1,
                                "filtertype": {
                                    "verbose": "",
                                    "skip_sw": "",
                                    "indev": swp,
                                    "ip_proto": "udp",
                                    "src_port": 53,
                                },
                                "action": {
                                    "police": {
                                        "rate": "1kbps",
                                        "burst": 100,
                                        "conform-exceed": "",
                                        "drop": "",
                                    }
                                },
                            }
                        ]
                    }
                ]
            )
            out = await TcFilter.show(
                input_data=[{dd.host_name: [{"block": 1, "options": "-json"}]}]
            )
            try:
                json_output = json.loads(out[0][dd.host_name]["result"])
            except JSONDecodeError as e:
                pytest.fail(f"json format error: {out[0][dd.host_name]['result']}")
