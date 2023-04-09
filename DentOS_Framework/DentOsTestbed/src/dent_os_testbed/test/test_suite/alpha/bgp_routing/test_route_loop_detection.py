# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import json
import time

import pytest

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.lib.frr.bgp import Bgp
from dent_os_testbed.lib.frr.route_map import RouteMap
from dent_os_testbed.utils.test_utils.bgp_routing_utils import (
    bgp_routing_get_local_as,
    bgp_routing_get_prefix_list,
)
from dent_os_testbed.utils.test_utils.tb_utils import (
    tb_reload_nw_and_flush_firewall,
    tb_reset_ssh_connections,
)
from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_create_bgp_devices_and_connect,
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
async def test_alpha_lab_bgp_routing_loop_detection(testbed):
    """
    Test Name: test_alpha_lab_bgp_routing_loop_detection
    Test Suite: suite_bgp_routing
    Test Overview: test BGP route loop detection
    Test Procedure:
    1. Test that AS route is filtered if learned from own ASN
    2. Validate 1 RSW does not see any prefixes from another RSW in the same
    3.  ASN (DIS router between the two)
    4. RSW should not have a prefix learned from its own ASN
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
    bgp_neighbors = {}
    tgen_as = 200
    br_ip = 30
    num_routes = 5
    await tb_reload_nw_and_flush_firewall(devices)
    for dd in devices:
        bgp_neighbors[dd.host_name] = {}
        for swp in tgen_dev.links_dict[dd.host_name][1]:
            bgp_neighbors[dd.host_name][swp] = {
                'num_route_ranges': 1,
                'local_as': tgen_as,
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

    # Reset the connections to make it work in pssh environment.
    await tb_reset_ssh_connections(devices)

    # install a route filter on the first device and block all ips on it
    d1 = devices[0]
    d1_as = await bgp_routing_get_local_as(d1)
    # lets start looking for another AS
    d2_as = d1_as
    for d2 in devices[1:]:
        d2_as = await bgp_routing_get_local_as(d2)
        if d1_as != d2_as:
            # found another device that has a different DS
            break
    inputs = bgp_routing_get_prefix_list(num_routes, d1.host_name)
    inputs.extend(
        [
            (
                RouteMap.configure,
                [
                    {
                        d1.host_name: [
                            {
                                'mapname': 'FROM-IXIA',
                                'options': {'permit': 10},
                                'match': {'ip-prefix': 'IXIA-ROUTES'},
                            }
                        ]
                    }
                ],
            ),
            (
                RouteMap.configure,
                [
                    {
                        d1.host_name: [
                            {
                                'mapname': 'FROM-IXIA',
                                'options': {'permit': 10},
                                'set': {'as-path': {'prepend': [tgen_as, d2_as, tgen_as]}},
                            }
                        ]
                    }
                ],
            ),
            (
                Bgp.configure,
                [
                    {
                        d1.host_name: [
                            {
                                'asn': d1_as,
                                'address-family': 'ipv4 unicast',
                                'neighbor': {
                                    'route-map': {'mapname': 'FROM-IXIA', 'options': {'in': ''}}
                                },
                                'group': 'IXIA',
                            }
                        ]
                    }
                ],
            ),
        ]
    )
    for input in inputs:
        out = await input[0](input_data=input[1])
        d1.applog.info(f'Ran command {input[0]} out {out}')

    # allow some time to take effect
    time.sleep(30)

    await tb_reset_ssh_connections(devices)

    # check community on all the devices it should be set to above.
    for dd in devices[1:]:
        d2_as = await bgp_routing_get_local_as(dd)
        if d1_as == d2_as:
            continue
        for i in range(num_routes):
            out = await Bgp.show(
                input_data=[
                    {
                        dd.host_name: [
                            {'type': 'ipv4', 'ip-address': f'30.0.{i}.0/24', 'options': 'json'}
                        ]
                    }
                ]
            )
            dd.applog.info(f'Ran command Bgp.show out {out}')
            route_info = json.loads(out[0][dd.host_name]['result'])
            if route_info:
                assert 0, f'30.0.{i}.0/24 Route still seen on {dd.host_name}'

    await tgen_utils_start_traffic(tgen_dev)
    # - check the traffic stats
    time.sleep(60)
    await tgen_utils_stop_traffic(tgen_dev)
    await tgen_utils_stop_traffic(tgen_dev)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        # if stream with dst 30.0.0.1 should have no traffic on it
        if '-30.0.0.1' not in row['Source/Dest Value Pair']:
            continue
        assert tgen_utils_get_loss(row) == 100.000, f'Failed>Loss percent: {row["Loss %"]}'

    await tgen_utils_stop_protocols(tgen_dev)
