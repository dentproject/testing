import json
import os
import time

import pytest

from testbed.Device import DeviceType
from testbed.lib.interfaces.interface import Interface
from testbed.lib.os.service import Service
from testbed.utils.test_utils.tb_utils import (
    tb_clean_config,
    tb_flap_links,
    tb_reload_nw_and_flush_firewall,
)
from testbed.utils.test_utils.tgen_utils import (
    tgen_util_flap_bgp_peer,
    tgen_utils_clear_traffic_stats,
    tgen_utils_create_bgp_devices_and_connect,
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_protocols,
    tgen_utils_stop_traffic,
)

pytestmark = pytest.mark.suite_bgp_routes

TRIGGER_FLAP_LINK = "FLAP_LINK"
TRIGGER_FLAP_BGP_ROUTE = "FLAP_BGP_ROUTE"
TRIGGER_RESTART_NETWORKING = "RESTART_NETWORKING"
TRIGGER_IFRELOAD = "IFRELOAD"


async def do_trigger(tgen_dev, src, devices, trigger):
    if trigger in [TRIGGER_FLAP_LINK, TRIGGER_RESTART_NETWORKING, TRIGGER_IFRELOAD]:
        device = devices.pop(0)
        tgen_dev.applog.info(f"Triggering Device trigger {trigger} on {device.host_name}")
        if trigger == TRIGGER_FLAP_LINK:
            tgen_dev.applog.info(f"Triggering Port Flap in {device.host_name}")
            await tb_flap_links(device, "swp")
        elif trigger == TRIGGER_RESTART_NETWORKING:
            services = [
                # "networking",
                "frr.service",
            ]
            for s in services:
                out = await Service.restart(
                    input_data=[{device.host_name: [{"name": s}]}],
                )
                assert (
                    out[0][device.host_name]["rc"] == 0
                ), f"Failed to restart the service {s} {out}"
        elif trigger == TRIGGER_IFRELOAD:
            out = await Interface.reload(input_data=[{device.host_name: [{"options": "-a"}]}])
            assert out[0][device.host_name]["rc"] == 0, f"Failed to ifreload -a "
            device.applog.info(out)
        else:
            tgen_dev.applog.info(f"unknown trigger {trigger} on {device.host_name}")
        # put the device back to the end
        devices.append(device)
    elif trigger == TRIGGER_FLAP_BGP_ROUTE:
        port = src.pop(0)
        await tgen_util_flap_bgp_peer(tgen_dev, port)
        tgen_dev.applog.info(f"Triggering {trigger} on {tgen_dev.host_name}")
        src.append(port)


@pytest.mark.asyncio
async def test_bgp_route_and_interface_flap(testbed):
    """
    Test Name: test_bgp_route_and_interface_flap
    Test Suite: suite_bgp_routes
    Test Overview: Simulate BGP sessions and test interface flaps
    Test Procedure:
    - remove bond interface on all devices TODO once fixed update the configs
    - start with clean slate.
    - Create a bgp peer on all the devices that has a tgen connection
    - router bgp 65534
         ...
         neighbor IXIA peer-group
         neighbor IXIA remote-as 200
         neighbor IXIA timers 3 10
         neighbor 10*<dut>.0.<swp>.2 peer-group IXIA
         neighbor 10*<dut>.0.<swp>.2 peer-group IXIA
         !
         address-family ipv4 unicast
          ...
          neighbor IXIA soft-reconfiguration inbound
         exit-address-family
    - create a simple ipv4 interface 10*<dut>.0.<swp>.1/30 on the tgen links
    - IXIA configuration
      - add simple IP 10*<dut>.0.<swp>.2/32
      - add BGP protocol on all the interfaces
        - ipv4 peers
          - enable peer, type externel, interfaces-connected, num of neighbors,
            DUT IP - 10*<dut>.0.<swp>.32 num_of_route_ranges=1 local as 200
            hold timer 10 update interval 3
      - route ranges
       - for each route ranges on each interface
         - create routes - 30*<dut>.0.0.1/24 100 routes
    - perform ifreload and check if the traffic is lost
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
    if not tgen_dev or not devices:
        print("The testbed does not have enough dent with tgen connections")
        return
    devices_info = {}
    bgp_neighbors = {}
    br_ip = 30
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
                        "number_of_routes": 100,
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

    # after traffic is stopped
    # triggers = [TRIGGER_FLAP_LINK, TRIGGER_FLAP_BGP_ROUTE, TRIGGER_RESTART_NETWORKING, TRIGGER_IFRELOAD]
    triggers = [
        # TRIGGER_FLAP_LINK,
        TRIGGER_FLAP_BGP_ROUTE,
    ]
    # triggers when traffic is running
    ttriggers = [TRIGGER_IFRELOAD]
    count = 10
    while count:
        """
        - For each triggers test the traffic is working or not.
        """
        # do the actual testing here.
        await tgen_utils_start_traffic(tgen_dev)
        # - check the traffic stats
        time.sleep(60)
        if ttriggers:
            trigger = ttriggers.pop(0)
            await do_trigger(tgen_dev, src, devices, trigger)
            ttriggers.append(trigger)
        time.sleep(60)
        await tgen_utils_stop_traffic(tgen_dev)
        stats = await tgen_utils_get_traffic_stats(tgen_dev, "Port Statistics")
        # verify here.
        for row in stats.Rows:
            # if the loss is more than 10% then fail the test
            diff = int(row["Frames Tx."]) - int(row["Valid Frames Rx."])
            loss = diff / (int(row["Frames Tx."]) * 1.0) * 100.0
            if loss > 10.0:
                assert 0, f"Loss {loss} > threshold 10.0%"
        # analyze logs
        trigger = triggers.pop(0)
        await do_trigger(tgen_dev, src, devices, trigger)
        # move to the next trigger
        triggers.append(trigger)
        time.sleep(60)
        count -= 1

    await tgen_utils_stop_protocols(tgen_dev)

    # create streams
