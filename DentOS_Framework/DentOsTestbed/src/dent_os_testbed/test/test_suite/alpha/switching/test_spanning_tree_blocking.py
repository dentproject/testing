# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#


import pytest


pytestmark = pytest.mark.suite_switching


@pytest.mark.asyncio
async def test_alpha_lab_switching_spanning_tree_blocking(testbed):
    """
    Test Name: test_alpha_lab_switching_spanning_tree_blocking
    Test Suite: suite_switching
    Test Overview: test stp blocking
    Test Procedure:
    1. Validate spanning tree blocks switches pluged into host ports
    2. Connect another switch into a host port on a RSW or infra switch
    3. Port should switch to blocking/disabled
      TODO it is manual test so skipping it.
    """
    pass
