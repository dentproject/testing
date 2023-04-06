# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import json
import time

import pytest

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.lib.frr.bgp import Bgp
from dent_os_testbed.utils.test_utils.bgp_routing_utils import (
    bgp_routing_get_local_as,
    bgp_routing_get_prefix_list,
)
from dent_os_testbed.utils.test_utils.tb_utils import tb_reload_nw_and_flush_firewall
from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_util_flap_bgp_peer,
    tgen_utils_create_bgp_devices_and_connect,
    tgen_utils_create_devices_and_connect,
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_get_loss,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_protocols,
    tgen_utils_stop_traffic,
)

pytestmark = pytest.mark.suite_bgp_routing


@pytest.mark.asyncio
async def test_alpha_lab_bgp_routing_timers(testbed):
    """
    Test Name: test_alpha_lab_bgp_routing_timers
    Test Suite: suite_bgp_routing
    Test Overview: test BGP routing timer
    Test Procedure:
    1. test BGP timers
    2. Adjust bgp timers to minimum allowable
    3. Validate session and route stability
    """
    tgen_dev, devices = await tgen_utils_get_dent_devices_with_tgen(
        testbed,
        [
            DeviceType.DISTRIBUTION_ROUTER,
            # DeviceType.INFRA_SWITCH,
            DeviceType.AGGREGATION_ROUTER,
        ],
        1,
    )
    if not tgen_dev or not devices or len(devices) < 2:
        print('The testbed does not have enough dent with tgen connections')
        return
    devices_info = {}
    bgp_neighbors = {}
    br_ip = 30
    num_routes = 5
    await tb_reload_nw_and_flush_firewall(devices)
    for dd in devices:
        bgp_neighbors[dd.host_name] = {}
        for swp in tgen_dev.links_dict[dd.host_name][1]:
            bgp_neighbors[dd.host_name][swp] = {
                'num_route_ranges': 1,
                'local_as': 200,
                'hold_timer': 10,
                'update_interval': 3,
                'route_ranges': [
                    {
                        'number_of_routes': num_routes,
                        'first_route': f'{br_ip}.0.0.1',
                    },
                ],
            }
        br_ip += 10
    await tgen_utils_create_bgp_devices_and_connect(tgen_dev, devices, bgp_neighbors)

    src = []
    dst = []
    for dd in devices:
        for swp in tgen_dev.links_dict[dd.host_name][1]:
            src.append(f'{dd.host_name}_{swp}')
            dst.append(f'{dd.host_name}_{swp}')

    # create mesh stream.
    streams = {
        'stream1': {
            'type': 'bgp',
            'bgp_source': src,
            'bgp_destination': dst,
            'protocol': 'ip',
            'ipproto': 'tcp',
        },
    }

    await tgen_utils_setup_streams(
        tgen_dev,
        pytest._args.config_dir + f'/{tgen_dev.host_name}/tgen_bgp_route_flap_config.ixncfg',
        streams,
        force_update=True,
    )

    await tgen_utils_start_traffic(tgen_dev)
    # - check the traffic stats
    time.sleep(60)
    await tgen_utils_stop_traffic(tgen_dev)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) != 100.000, f'Failed>Loss percent: {row["Loss %"]}'

    # install a route filter on the first device and block all ips on it
    d1 = devices[0]
    d1_as = await bgp_routing_get_local_as(d1)
    test_keep_alive = 2
    test_hold = 6
    inputs = [
        [
            {
                d1.host_name: [
                    {
                        'asn': d1_as,
                        'neighbor': {'options': {'timers': f'{test_keep_alive} {test_hold}'}},
                        'group': 'IXIA',
                    }
                ]
            }
        ],
    ]
    for input in inputs:
        out = await Bgp.configure(input_data=input)
        d1.applog.info(f'Ran Bgp.configure out {out}')

    # allow some time to take effect
    time.sleep(30)

    # check community on all the devices it should be set to above.
    for dd in devices[:1]:
        for i in range(num_routes):
            out = await Bgp.show(
                input_data=[{dd.host_name: [{'neighbors': {}, 'options': 'json'}]}]
            )
            dd.applog.info(f'Ran Bgp.show neighbors out {out}')
            neighbors = json.loads(out[0][dd.host_name]['result'])
            if not neighbors:
                assert 0, f'No Neighbors on  {dd.host_name}'
            for neighbor in neighbors.values():
                if neighbor['peerGroup'] != 'IXIA':
                    continue
                # check what is the configured timers?
                if (
                    neighbor['bgpTimerConfiguredHoldTimeMsecs'] != test_hold * 1000
                    or neighbor['bgpTimerConfiguredKeepAliveIntervalMsecs']
                    != test_keep_alive * 1000
                ):
                    msg = f'Timers misconfigured on {dd.host_name}'
                    dd.applog.info(msg)
                    # assert 0, msg

    await tgen_utils_start_traffic(tgen_dev)
    # - check the traffic stats
    time.sleep(60)
    await tgen_utils_stop_traffic(tgen_dev)
    await tgen_utils_stop_traffic(tgen_dev)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) != 100.000, f'Failed>Loss percent: {row["Loss %"]}'

    await tgen_utils_stop_protocols(tgen_dev)
