# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import time

import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_route import IpRoute
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
async def test_alpha_lab_static_routing_kernel_route_on_table(testbed):
    """
    Test Name: test_alpha_lab_static_routing_kernel_route_on_table
    Test Suite: suite_routing
    Test Overview: test kernel route
    Test Procedure:
    1. Kernel route impact on table
    2. test interaction of a kernel route on network
    3. on ma1 set up dhcp server to send ip and default route and monitor
    4.  install a static route to tgen port
    5.. then send the packet it should show up in tgen port.
    """
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        print('The testbed does not have enough dent with tgen connections')
        return
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    swp = 'ma1'

    await IpLink.show(
        input_data=[{dent: [{'device': swp, 'cmd_options': '-j'}]}],
    )

    swp_info = {}
    await tgen_utils_get_swp_info(dent_dev, swp, swp_info)
    sip = '.'.join(swp_info['ip'][:-1] + [str(int(swp[3:]) * 2)])

    # start from a clean state
    await IpRoute.add(
        input_data=[
            {
                dent_dev.host_name: [
                    {'dst': '100.0.0.0/24', 'via': f'{sip}', 'dev': swp, 'protocol': 'kernel'}
                ]
            }
        ],
    )
    # TODO this is failing check with RUSS

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
    await tgen_utils_start_traffic(tgen_dev)
    time.sleep(10)
    await tgen_utils_stop_traffic(tgen_dev)
    await tgen_utils_get_traffic_stats(tgen_dev)

    # add validation here. No psckets should come to iXIA check iptables to get the stats.
    #
    await tgen_utils_stop_protocols(tgen_dev)
