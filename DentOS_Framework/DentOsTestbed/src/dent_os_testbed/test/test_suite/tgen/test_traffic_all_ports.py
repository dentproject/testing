import time

import pytest

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.utils.test_utils.tb_utils import tb_reload_nw_and_flush_firewall
from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_create_devices_and_connect,
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_get_loss,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_protocols,
    tgen_utils_stop_traffic,
)

pytestmark = pytest.mark.suite_traffic


@pytest.mark.asyncio
async def test_all_ports_tgen_w_traffic(testbed):
    """
    Test Name: test_all_ports_tgen_w_traffic
    Test Suite: suite_traffic
    Test Overview: test traffic on all the ixia ports
    Test Procedure:
    1. get devices with ixia ports
    2. creates end point on each of them
    3. create traffic from each end point to all of them
    4. check stats on each of them should be traffic flowing
    """
    tgen_dev, devices = await tgen_utils_get_dent_devices_with_tgen(
        testbed,
        [
            DeviceType.DISTRIBUTION_ROUTER,
            DeviceType.INFRA_SWITCH,
            DeviceType.AGGREGATION_ROUTER,
        ],
        1,
    )
    if not tgen_dev or not devices:
        print('The testbed does not have enough dent with tgen connections')
        return
    await tb_reload_nw_and_flush_firewall(devices)

    devices_info = {}
    for dd in devices:
        devices_info[dd.host_name] = [
            # 'count' is the number of endpoints
            {
                'name': 'Pos',
                'count': 1,
            },
        ]
        # add vlan for infra devices
        if dd.type == DeviceType.INFRA_SWITCH:
            devices_info[dd.host_name][0]['vlan'] = 100

    await tgen_utils_create_devices_and_connect(tgen_dev, devices, devices_info, need_vlan=False)

    pos_src = []
    pos_dst = []
    for dd in devices:
        for swp in tgen_dev.links_dict[dd.host_name][1]:
            pos_src.append(f'{dd.host_name}_Pos_{swp}')
            pos_dst.append(f'{dd.host_name}_Pos_{swp}')

    streams = {
        'tcp_https_pos_flow': {
            'ip_source': pos_src,
            'ip_destination': pos_dst,
            'protocol': 'ip',
            'ipproto': 'tcp',
            'dstPort': '443',
        },
    }

    await tgen_utils_setup_streams(
        tgen_dev,
        pytest._args.config_dir + f'/{tgen_dev.host_name}/tgen_all_ports',
        streams,
        force_update=True,
    )

    await tgen_utils_start_traffic(tgen_dev)
    sleep_time = 60 * 2
    tgen_dev.applog.info(f'zzZZZZZ({sleep_time})s')
    time.sleep(sleep_time)
    await tgen_utils_stop_traffic(tgen_dev)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')

    # Traffic Verification
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) != 100.000, f'Failed>Loss percent: {row["Loss %"]}'

    await tgen_utils_stop_protocols(tgen_dev)
