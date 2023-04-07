# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import json

import pytest

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.utils.test_utils.tb_utils import tb_get_all_devices

pytestmark = pytest.mark.suite_switching


@pytest.mark.asyncio
async def test_alpha_lab_switching_spanning_tree(testbed):
    """
    Test Name: test_alpha_lab_switching_spanning_tree
    Test Suite: suite_switching
    Test Overview: test switching spanning tree
    Test Procedure:
    1. configure spanning tree
    2. Turn up spanning tree between switches
    3. Spanning tree should turn up and function
    """

    # brctl addbr dev
    # brctl addif dev swp*
    # brctl stp dev on
    # brctl show stp dev
    # brctl stp dev off

    for dd in await tb_get_all_devices(testbed):
        if dd.type != DeviceType.INFRA_SWITCH:
            continue
        # do this on infra switches only
        for cmd in [
            'brctl delbr test_br || true',
            'brctl addbr test_br',
            'brctl stp test_br on',
        ]:
            rc, out = await dd.run_cmd(cmd, sudo=True)
            assert rc == 0, f'failed to run {cmd} rc {rc} out {out}'
        for dd2, links in dd.links_dict.items():
            if (
                dd2 not in testbed.devices_dict
                or testbed.devices_dict[dd2].type != DeviceType.INFRA_SWITCH
            ):
                continue
            for swp in links[0]:
                cmd = f'bridge -j link show dev {swp}'
                rc, out = await dd.run_cmd(cmd, sudo=True)
                dd.applog.info(f'Ran command {cmd} rc {rc} out {out}')
                assert rc == 0, f'failed to run {cmd} rc {rc} out {out}'
                # delete from the old bridge if any
                data = json.loads(out)
                if 'master' in data:
                    br = data['master']
                    cmd = f'brctl delif {br} {swp}'
                    rc, out = await dd.run_cmd(cmd, sudo=True)
                    assert rc == 0, f'failed to run {cmd} rc {rc} out {out}'
                for cmd in [
                    f'ip link set {swp} nomaster',
                    f'brctl addif test_br {swp}',
                ]:
                    rc, out = await dd.run_cmd(cmd, sudo=True)
                    dd.applog.info(f'Ran command {cmd} rc {rc} out {out}')
                    assert rc == 0, f'failed to run {cmd} rc {rc} out {out}'
        for cmd in [
            f'brctl show test_br',
            f'brctl showstp test_br',
            f'brctl delbr test_br',
        ]:
            rc, out = await dd.run_cmd(cmd, sudo=True)
            dd.applog.info(f'Ran command {cmd} rc {rc} out {out}')
