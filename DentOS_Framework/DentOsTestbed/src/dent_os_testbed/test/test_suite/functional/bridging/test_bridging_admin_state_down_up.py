#!/usr/lib/env python3.6
# Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import time
import asyncio
import pytest

from dent_os_testbed.lib.bridge.bridge_link import BridgeLink
from dent_os_testbed.constants import DEFAULT_LOGGER
from dent_os_testbed.Device import DeviceType
from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.logger.Logger import AppLogger
from dent_os_testbed.utils.test_utils.tb_utils import (
    tb_get_all_devices,
    tb_reload_nw_and_flush_firewall
)
from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_create_devices_and_connect,
    tgen_utils_stop_traffic,
    tgen_utils_stop_protocols,
    tgen_utils_start_traffic,
    tgen_utils_setup_streams,
    tgen_utils_get_traffic_stats,
    tgen_utils_get_loss,
)

pytestmark = pytest.mark.suite_functional_bridging


@pytest.mark.asyncio
async def test_bridging(testbed):
    """
    Test Name: test_bridging_admin_state_down_up
    Test Suite: suite_functional_bridging
    Test Overview: This test comes to verify: bridge is not learning 
                   entries with bridge entity admin state down.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1 swp2 swp3 swp4 master br0.
    3.  Set ports swp1 swp2 swp3 swp4 learning ON.
    4.  Set ports swp1 swp2 swp3 swp4 flood OFF.
    5.  Set bridge br0 admin state UP.
    6.  Set entities swp1, swp2, swp3, swp4 UP state.

    7.  Set bridge br0 admin state DOWN.
    8.  Send traffic to swp1 with src mac aa:bb:cc:dd:ee:11.
    9.  Verify that src mac aa:bb:cc:dd:ee:11 haven't been learned for swp1.
    10. Send traffic to swp2 with src mac aa:bb:cc:dd:ee:12.
    11. Verify that src mac aa:bb:cc:dd:ee:12 haven't been learned for swp2.
    12. Send traffic to swp3 with src mac aa:bb:cc:dd:ee:13.
    13. Verify that mac aa:bb:cc:dd:ee:13 haven't been learned for swp3.
    14. Send traffic to swp4 with src mac aa:bb:cc:dd:ee:14.
    15. Verify that src mac aa:bb:cc:dd:ee:14 haven't been learned for swp4.

    16. Set bridge br0 admin state UP.
    17. Send traffic to swp1 with src mac aa:bb:cc:dd:ee:11.
    18. Verify that src mac aa:bb:cc:dd:ee:11 have been learned for swp1.
    19. Send traffic to swp2 with src mac aa:bb:cc:dd:ee:12.
    20. Verify that src mac aa:bb:cc:dd:ee:12 have been learned for swp2.
    21. Send traffic to swp3 with src mac aa:bb:cc:dd:ee:13.
    22. Verify that mac aa:bb:cc:dd:ee:13 have been learned for swp3.
    23. Send traffic to swp4 with src mac aa:bb:cc:dd:ee:14.
    24. Verify that src mac aa:bb:cc:dd:ee:14 have been learned for swp4.
    """

    logger = AppLogger(DEFAULT_LOGGER)
    dev = await tb_get_all_devices(testbed)
    logger.info("Devices:", dev)

    bridge = "br0"
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        logger.error("The testbed does not have enough dent eith tgn connections")
        return
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    #tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]

    out = await IpLink.add(
        input_data=[{device_host_name: [{"device": bridge, "type": "bridge"}]}])
    assert out[0][device_host_name]["rc"] == 0, out

    out = await IpLink.set(
        input_data=[{device_host_name: [{"device": f"{ports[0]}", "master": "br0"}]}],
        input_data=[{device_host_name: [{"device": f"{ports[1]}", "master": "br0"}]}],
        input_data=[{device_host_name: [{"device": f"{ports[2]}", "master": "br0"}]}],
        input_data=[{device_host_name: [{"device": f"{ports[3]}", "master": "br0"}]}])
    assert out[0][device_host_name]["rc"] == 0, out

    out = await BridgeLink.set(
        input_data=[{device_host_name: [{"device": f"{ports[0]}", "learning": True}]}],
        input_data=[{device_host_name: [{"device": f"{ports[1]}", "learning": True}]}],
        input_data=[{device_host_name: [{"device": f"{ports[2]}", "learning": True}]}],
        input_data=[{device_host_name: [{"device": f"{ports[3]}", "learning": True}]}])
    assert out[0][device_host_name]["rc"] == 0, out

    out = await BridgeLink.set(
        input_data=[{device_host_name: [{"device": f"{ports[0]}", "flood": False}]}],
        input_data=[{device_host_name: [{"device": f"{ports[1]}", "flood": False}]}],
        input_data=[{device_host_name: [{"device": f"{ports[2]}", "flood": False}]}],
        input_data=[{device_host_name: [{"device": f"{ports[3]}", "flood": False}]}])
    assert out[0][device_host_name]["rc"] == 0, out

    out = await IpLink.set(
        input_data=[{device_host_name: [{"device": bridge, "operstate": "up"}]}])
    assert out[0][device_host_name]["rc"] == 0, out

    out = await IpLink.set(
        input_data=[{device_host_name: [{"device": f"{ports[0]}", "operstate": "up"}]}],
        input_data=[{device_host_name: [{"device": f"{ports[1]}", "operstate": "up"}]}],
        input_data=[{device_host_name: [{"device": f"{ports[2]}", "operstate": "up"}]}],
        input_data=[{device_host_name: [{"device": f"{ports[3]}", "operstate": "up"}]}])
    assert out[0][device_host_name]["rc"] == 0, out

    out = await IpLink.set(
        input_data=[{device_host_name: [{"device": bridge, "operstate": "down"}]}])
    assert out[0][device_host_name]["rc"] == 0, out

    # Send traffic and Verify 8-15 steps

    out = await IpLink.set(
        input_data=[{device_host_name: [{"device": bridge, "operstate": "up"}]}])
    assert out[0][device_host_name]["rc"] == 0, out

    # Send traffic and Verify 17-24 steps
