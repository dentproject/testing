# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import time

import pytest

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.utils.test_utils.tb_utils import tb_reload_nw_and_flush_firewall
from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_create_devices_and_connect,
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_get_loss,
    tgen_utils_get_traffic_stats,
    tgen_utils_get_loss,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_protocols,
    tgen_utils_stop_traffic,
)

pytestmark = pytest.mark.suite_switching


@pytest.mark.asyncio
async def test_alpha_lab_switching_trunk_port(testbed):
    """
    Test Name: test_alpha_lab_switching_trunk_port
    Test Suite: suite_switching
    Test Overview: test switching on a trunk port
    Test Procedure:
    1. Validate trunk porting
    2. Configure 2 devices both with dot1q trunk enabled on multiple subinterfaces.
    3. send traffic down these interfaces
    4. traffic should be visible on appropriate vlan
    """
    tgen_dev, infra_devices = await tgen_utils_get_dent_devices_with_tgen(
        testbed, [DeviceType.INFRA_SWITCH], 1
    )
    if not tgen_dev or not infra_devices:
        print('The testbed does not have enough dent with tgen connections')
        return
    await tb_reload_nw_and_flush_firewall(infra_devices)
    devices_info = {}
    for dd in infra_devices:
        devices_info[dd.host_name] = [
            # 'count' is the number of endpoints
            {
                'vlan': 300,
                'name': 'POS',
                'count': 1,
            },
            {
                'vlan': 400,
                'name': 'ASSOC',
                'count': 1,
            },
        ]

    await tgen_utils_create_devices_and_connect(
        tgen_dev, infra_devices, devices_info, need_vlan=True
    )
    pos_src = []
    pos_dst = []
    assoc_src = []
    assoc_dst = []
    for dd in infra_devices:
        for swp in tgen_dev.links_dict[dd.host_name][1]:
            pos_src.append(f'{dd.host_name}_POS_{swp}')
            pos_dst.append(f'{dd.host_name}_POS_{swp}')
            assoc_src.append(f'{dd.host_name}_ASSOC_{swp}')
            assoc_dst.append(f'{dd.host_name}_ASSOC_{swp}')

    streams = {
        'tcp_ssh_pos_flow': {
            'ip_source': pos_src,
            'ip_destination': pos_dst,
            'protocol': 'ip',
            'ipproto': 'tcp',
            'dstPort': '22',
        },
        'tcp_ssh_assoc_flow': {
            'ip_source': assoc_src,
            'ip_destination': assoc_dst,
            'protocol': 'ip',
            'ipproto': 'tcp',
            'dstPort': '22',
        },
    }
    await tgen_utils_setup_streams(
        tgen_dev,
        pytest._args.config_dir + f'/{tgen_dev.host_name}/tgen_trunk_port',
        streams,
        force_update=True,
    )

    await tgen_utils_start_traffic(tgen_dev)
    sleep_time = 60 * 2
    tgen_dev.applog.info(f'zzZZZZZ({sleep_time})s')
    time.sleep(sleep_time)
    await tgen_utils_stop_traffic(tgen_dev)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) != 100.000, f'Failed>Loss percent: {row["Loss %"]}'
    await tgen_utils_stop_protocols(tgen_dev)
