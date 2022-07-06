# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import time

import pytest

from testbed.Device import DeviceType
from testbed.utils.test_utils.tb_utils import tb_reload_nw_and_flush_firewall
from testbed.utils.test_utils.tgen_utils import (
    tgen_utils_create_devices_and_connect,
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_get_loss,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_protocols,
    tgen_utils_stop_traffic,
)

pytestmark = pytest.mark.suite_switching


@pytest.mark.asyncio
async def test_alpha_lab_switching_vlan_access_via_trunk_port(testbed):
    """
    Test Name: test_alpha_lab_switching_vlan_access_via_trunk_port
    Test Suite: suite_switching
    Test Overview: test switching on trunk port
    Test Procedure:
    1. Validate device on an access port can communicate through an upstream trunk.
    2. configure an access port on switch 1 connect host1 to it
    3. configure a trunk port between switch1 and switch2
    4. configure an access port on switch2 connect host2 on it
    5. Validate host1 and host2 can communicate
    """

    tgen_dev, infra_devices = await tgen_utils_get_dent_devices_with_tgen(
        testbed, [DeviceType.INFRA_SWITCH], 1
    )
    if not tgen_dev or not infra_devices:
        print("The testbed does not have enough dent with tgen connections")
        return
    await tb_reload_nw_and_flush_firewall(infra_devices)
    devices_info = {}
    for dd in infra_devices:
        devices_info[dd.host_name] = [
            # 'count' is the number of endpoints
            {
                "vlan": 100,
                "name": "MGMT",
                "count": 1,
            },
        ]

    await tgen_utils_create_devices_and_connect(
        tgen_dev, infra_devices, devices_info, need_vlan=False
    )
    mgmt_src = []
    mgmt_dst = []
    for dd in infra_devices:
        for swp in tgen_dev.links_dict[dd.host_name][1]:
            mgmt_src.append(f"{dd.host_name}_MGMT_{swp}")
            mgmt_dst.append(f"{dd.host_name}_MGMT_{swp}")

    streams = {
        "tcp_ssh_mgmt_flow": {
            "ip_source": mgmt_src,
            "ip_destination": mgmt_dst,
            "protocol": "ip",
            "ipproto": "tcp",
            "dstPort": "22",
        },
    }
    await tgen_utils_setup_streams(
        tgen_dev,
        pytest._args.config_dir + f"/{tgen_dev.host_name}/tgen_access_port",
        streams,
        force_update=True,
    )

    await tgen_utils_start_traffic(tgen_dev)
    sleep_time = 60 * 2
    tgen_dev.applog.info(f"zzZZZZZ({sleep_time})s")
    time.sleep(sleep_time)
    await tgen_utils_stop_traffic(tgen_dev)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) != 100.000, f'Failed>Loss percent: {row["Loss %"]}'
    await tgen_utils_stop_protocols(tgen_dev)
