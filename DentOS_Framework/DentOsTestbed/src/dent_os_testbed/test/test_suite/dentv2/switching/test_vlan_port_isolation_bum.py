# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import time

import pytest

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.lib.bridge.bridge_link import BridgeLink
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.utils.test_utils.tb_utils import tb_reload_nw_and_flush_firewall
from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_create_devices_and_connect,
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_protocols,
)

pytestmark = pytest.mark.suite_vlan_port_isolation


@pytest.mark.asyncio
async def test_dentv2_vlan_port_isolation_bum(testbed):
    """
    Test Name: test_dentv2_vlan_port_isolation_bum
    Test Suite: suite_vlan_port_isolation
    Test Overview: tet vlan port isolation for BUM traffic
    Test Procedure:
    1. Configure a single VLAN-aware bridge
    2. Send BUM traffic to the ports
    3. Verify that isolated ports cannot communicate across VLANs
    """

    tgen_dev, infra_devices = await tgen_utils_get_dent_devices_with_tgen(
        testbed, [DeviceType.INFRA_SWITCH], 2
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
                'vlan': 100,
                'name': 'MGMT',
                'count': 1,
            },
        ]

    await tgen_utils_create_devices_and_connect(
        tgen_dev, infra_devices, devices_info, need_vlan=False
    )
    mgmt_src = []
    mgmt_dst = []
    for dd in infra_devices:
        # Create bridge br0 and put tgen ports on it
        await IpLink.delete(input_data=[{dd.host_name: [{'device': 'bridge'}]}])
        await IpLink.delete(input_data=[{dd.host_name: [{'device': 'br0'}]}])
        out = await IpLink.add(
            input_data=[{dd.host_name: [{'device': 'br0', 'type': 'bridge', 'vlan_filtering': 1}]}]
        )
        assert out[0][dd.host_name]['rc'] == 0, out
        out = await IpLink.set(input_data=[{dd.host_name: [{'device': 'br0', 'operstate': 'up'}]}])
        assert out[0][dd.host_name]['rc'] == 0, out
        for swp in tgen_dev.links_dict[dd.host_name][1]:
            mgmt_src.append(f'{dd.host_name}_MGMT_{swp}')
            mgmt_dst.append(f'{dd.host_name}_MGMT_{swp}')
            await IpLink.set(input_data=[{dd.host_name: [{'device': swp, 'nomaster': ''}]}])
            out = await IpLink.set(input_data=[{dd.host_name: [{'device': swp, 'master': 'br0'}]}])
            assert out[0][dd.host_name]['rc'] == 0, out
            await BridgeLink.set(input_data=[{dd.host_name: [{'device': swp, 'isolated': True}]}])

    ep_src = list(map(lambda x: f"{x.split('_')[0]}:{x.split('_')[2]}", mgmt_src))
    ep_dst = list(map(lambda x: f"{x.split('_')[0]}:{x.split('_')[2]}", mgmt_dst))
    # TODO: Send BUM traffic
    streams = {
        'L2_bum_multicast': {
            'protocol': '802.1Q',
            'ep_source': ep_src,
            'ep_destination': ep_dst,
            # "srcIp": "10.0.0.1",
            # "dstIp": "224.0.1.1",
            'srcMac': 'aa:bb:cc:dd:ee:ff',
            'dstMac': '01:00:5e:00:01:01',
            'type': 'raw',
        },
        'L2_bum_broadcast': {
            # "srcIp": "10.0.0.1",
            # "dstIp": "20.0.0.1",
            'srcMac': 'aa:bb:cc:dd:ee:ff',
            'dstMac': 'ff:ff:ff:ff:ff:ff',
            'type': 'raw',
            'protocol': '802.1Q',
        },
    }
    await tgen_utils_setup_streams(
        tgen_dev,
        pytest._args.config_dir + f'/{tgen_dev.host_name}/tgen_port_isolation_bum',
        streams,
        force_update=True,
    )

    await tgen_utils_start_traffic(tgen_dev)
    sleep_time = 60 * 2
    tgen_dev.applog.info(f'zzZZZZZ({sleep_time})s')
    time.sleep(sleep_time)
    # await tgen_utils_stop_traffic(tgen_dev)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Traffic Item Statistics')

    # Traffic Verification
    for row in stats.Rows:
        assert float(row['Loss %']) == 100.000, f'Failed>Loss percent: {row["Loss %"]}'

    await tgen_utils_stop_protocols(tgen_dev)
