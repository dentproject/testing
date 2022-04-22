# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import time

import pytest

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.lib.frr.frr_ip_route import FrrIpRoute
from dent_os_testbed.utils.test_utils.tb_utils import tb_reload_nw_and_flush_firewall
from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_util_flap_bgp_peer,
    tgen_utils_create_bgp_devices_and_connect,
    tgen_utils_create_devices_and_connect,
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_get_loss,
    tgen_utils_get_swp_info,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_protocols,
    tgen_utils_stop_traffic,
)

pytestmark = pytest.mark.suite_routing


@pytest.mark.asyncio
async def test_alpha_lab_static_routing_floating_vs_bgp_route(testbed):
    """
    Test Name: test_alpha_lab_static_routing_floating_vs_bgp_route
    Test Suite: suite_routing
    Test Overview: test static and bgp route
    Test Procedure:
    1. Validate route administrative distance
    2. Set up a route to come from bgp, and one add a static route with a higher administrative distance.
    3. shut down bgp peer
    4. recover bgp peer
    5. While BGP route is present it should be selected path.
    6. Once BGP vanishes should switch to floating route
    7. on recovery it should return to bgp path
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

    # let d1 = devices[0] and d2 = devices[1]
    # configure a static route on d1 for all the routes advertised by d2 towards d1 itself
    # send the traffic the bgp route should be effective
    # now stop the bgp route from d2
    # send the traffic now the traffic should take the static route with lower admin distance

    for d1 in devices[1:]:
        swp_info = {}
        swp_tgen_ports = tgen_dev.links_dict[d1.host_name][1]
        swp = swp_tgen_ports[0]
        await tgen_utils_get_swp_info(d1, swp, swp_info)
        sip = ".".join(swp_info["ip"][:-1] + ["2"])

        for i in range(num_routes):
            out = await FrrIpRoute.add(
                input_data=[
                    {d1.host_name: [{"network": f"30.0.{i}.0/24", "gateway": sip, "distance": 240}]}
                ]
            )
            d1.applog.info(f"Ran command FrrIpRoute.add out {out}")

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
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) != 100.000, f'Failed>Loss percent: {row["Loss %"]}'
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Traffic Item Statistics")

    await tgen_util_flap_bgp_peer(tgen_dev, src[0][:-1] + " 1", skip_up=True)
    tgen_dev.applog.info(f"Triggering flap on {tgen_dev.host_name}")

    await tgen_utils_start_traffic(tgen_dev)
    # - check the traffic stats
    time.sleep(60)
    await tgen_utils_stop_traffic(tgen_dev)
    await tgen_utils_stop_traffic(tgen_dev)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    for row in stats.Rows:
        # if stream with dst 30.0.0.1 should have no traffic on it
        if "-30.0.0.1" not in row["Source/Dest Value Pair"]:
            continue
        assert tgen_utils_get_loss(row) == 100.000, f'Failed>Loss percent: {row["Loss %"]}'
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Traffic Item Statistics")

    await tgen_utils_stop_protocols(tgen_dev)
