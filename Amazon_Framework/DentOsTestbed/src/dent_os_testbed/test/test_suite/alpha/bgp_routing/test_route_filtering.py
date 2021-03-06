# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import json
import time

import pytest

from dent_os_testbed.Device import DeviceType
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
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_protocols,
    tgen_utils_stop_traffic,
)

pytestmark = pytest.mark.suite_bgp_routing


@pytest.mark.asyncio
async def test_alpha_lab_bgp_routing_route_filtering(testbed):
    # validate that routes can be filtered with prefix-list and route-map
    # create a prefix list with a select route, apply it to a deny entry
    #  on an inbound route-map from provider.
    # validate route cannot be seen in table

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
        print("The testbed does not have enough dent with tgen connections")
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
                "num_route_ranges": 1,
                "local_as": 200,
                "hold_timer": 10,
                "update_interval": 3,
                "route_ranges": [
                    {
                        "number_of_routes": num_routes,
                        "first_route": f"{br_ip}.0.0.1",
                    },
                ],
            }
        br_ip += 10
    await tgen_utils_create_bgp_devices_and_connect(tgen_dev, devices, bgp_neighbors)

    src = []
    dst = []
    for dd in devices:
        for swp in tgen_dev.links_dict[dd.host_name][1]:
            src.append(f"{dd.host_name}_{swp}")
            dst.append(f"{dd.host_name}_{swp}")

    # create mesh stream.
    streams = {
        "stream1": {
            "type": "bgp",
            "bgp_source": src,
            "bgp_destination": dst,
            "protocol": "ip",
            "ipproto": "tcp",
        },
    }

    await tgen_utils_setup_streams(
        tgen_dev,
        pytest._args.config_dir + f"/{tgen_dev.host_name}/tgen_bgp_route_flap_config.ixncfg",
        streams,
        force_update=True,
    )

    await tgen_utils_start_traffic(tgen_dev)
    # - check the traffic stats
    time.sleep(60)
    await tgen_utils_stop_traffic(tgen_dev)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Port Statistics")

    # install a route filter on the first device and block all ips on it
    d1 = devices[0]
    d1_as = await bgp_routing_get_local_as(d1)
    cmds = bgp_routing_get_prefix_list(num_routes)
    cmds.extend(
        [
            f"vtysh -c 'conf terminal' -c 'route-map FROM-IXIA deny 10' -c 'match ip address prefix-list IXIA-ROUTES'",
            f"vtysh -c 'conf terminal' -c 'router bgp {d1_as}' -c 'address-family ipv4 unicast' -c 'neighbor IXIA route-map FROM-IXIA in'",
        ]
    )
    for cmd in cmds:
        rc, out = await d1.run_cmd(cmd, sudo=True)
        d1.applog.info(f"Ran command {cmd} rc {rc} out {out}")

    for dd in devices:
        for i in range(num_routes):
            cmd = f"vtysh -c 'show bgp ipv4 30.0.{i}.0/24 json'"
            rc, out = await dd.run_cmd(cmd, sudo=True)
            dd.applog.info(f"Ran command {cmd} rc {rc} out {out}")
            route_info = json.loads(out)
            if route_info:
                assert 0, f"30.0.{i}.0/24 Route still seen on {dd.host_name}"

    await tgen_utils_start_traffic(tgen_dev)
    # - check the traffic stats
    time.sleep(60)
    await tgen_utils_stop_traffic(tgen_dev)
    await tgen_utils_stop_traffic(tgen_dev)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Port Statistics")

    await tgen_utils_stop_protocols(tgen_dev)
