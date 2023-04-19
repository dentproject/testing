# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import time

import pytest

from dent_os_testbed.lib.frr.frr_ip_route import FrrIpRoute
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.utils.test_utils.tb_utils import tb_reload_nw_and_flush_firewall
from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_connect_to_tgen,
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_get_swp_info,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_protocols,
    tgen_utils_stop_traffic,
)

pytestmark = pytest.mark.suite_routing


@pytest.mark.asyncio
async def test_alpha_lab_static_routing_basic_static_route(testbed):
    """
    Test Name: test_alpha_lab_static_routing_basic_static_route
    Test Suite: suite_routing
    Test Overview: test basic static route
    Test Procedure:
    1. static routes should work
    2. load a static route on network device that is on a different path
    3. than the default route, and from a connected ECU trace out
    4. Traffic should follow the static route and not the default route
    """

    # 1. install a static route to tgen port
    # 2. then send the packet it should show up in tgen port.
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        print('The testbed does not have enough dent with tgen connections')
        return
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    swp_tgen_ports = tgen_dev.links_dict[dent][1]
    swp = swp_tgen_ports[1]

    out = await IpLink.show(
        input_data=[{dent: [{'device': swp, 'cmd_options': '-j'}]}],
    )

    swp_info = {}
    await tgen_utils_get_swp_info(dent_dev, swp, swp_info)
    sip = '.'.join(swp_info['ip'][:-1] + [str(int(swp[3:]) * 2)])

    await tb_reload_nw_and_flush_firewall([dent_dev])

    await tgen_utils_connect_to_tgen(tgen_dev, dent_dev)
    streams = {
        'bgp': {
            'dstIp': '100.0.0.10',
            'protocol': 'ip',
            'ipproto': 'tcp',
            'dstPort': '179',
        },
    }
    await tgen_utils_setup_streams(
        tgen_dev,
        pytest._args.config_dir + f'/{dent}/tgen_basic_static_route.ixncfg',
        streams,
    )

    # start from a clean state
    out = await FrrIpRoute.add(
        input_data=[{dent_dev.host_name: [{'network': '100.0.0.0/24', 'gateway': sip}]}]
    )
    dent_dev.applog.info(f'Ran command FrrIpRoute.add out {out}')

    await tgen_utils_start_traffic(tgen_dev)
    time.sleep(10)
    await tgen_utils_stop_traffic(tgen_dev)
    await tgen_utils_get_traffic_stats(tgen_dev)

    # add validation here.
    await tgen_utils_stop_protocols(tgen_dev)
