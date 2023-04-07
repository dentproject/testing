# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#


import pytest


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
