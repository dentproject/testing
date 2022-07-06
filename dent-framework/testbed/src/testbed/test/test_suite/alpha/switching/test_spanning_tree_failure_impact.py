# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import time

import pytest

from testbed.Device import DeviceType
from testbed.utils.test_utils.tgen_utils import (
    tgen_utils_create_devices_and_connect,
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_protocols,
    tgen_utils_stop_traffic,
)

pytestmark = pytest.mark.suite_switching


@pytest.mark.asyncio
async def test_alpha_lab_switching_spanning_tree_failure_impact(testbed):
    """
    Test Name: test_alpha_lab_switching_spanning_tree_failure_impact
    Test Suite: suite_switching
    Test Overview: test stp failure
    Test Procedure:
    1. validate a port going down does not break connectivity with layer2 STP environment with redundancy
    2. create 3 trunks between a ring of 3 routers.
    3. pull a active linkspanning tree should fail gracefully
    """

    # TODO since its mostly manual skipping it for now.
    pass
