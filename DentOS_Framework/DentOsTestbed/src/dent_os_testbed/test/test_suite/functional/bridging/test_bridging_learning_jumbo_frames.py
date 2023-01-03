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
    Test Name: test_bridging_jumbo_frames
    Test Suite: suite_functional_bridging
    Test Overview: This test comes to verify: addresses are learned on bridge 
                   with jumbo frames.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1 swp2 swp3 swp4 master br0.
    3.  Set max jumbo frame size support on ports swp1 swp2 swp3 swp4.
    4.  Set ports swp1 swp2 swp3 swp4 learning ON.
    5.  Set ports swp1 swp2 swp3 swp4 flood OFF.
    6.  Set bridge br0 admin state UP.
    7.  Set entities swp1, swp2, swp3, swp4 UP state.
    8.  Send traffic with max jumbo frame size.
    9.  Verify that address have been learned.
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

    out = await IpLink.set(
        input_data=[{device_host_name: [{"device": f"{ports[0]}", "mtu": 9500}]}],
        input_data=[{device_host_name: [{"device": f"{ports[1]}", "mtu": 9500}]}],
        input_data=[{device_host_name: [{"device": f"{ports[2]}", "mtu": 9500}]}],
        input_data=[{device_host_name: [{"device": f"{ports[3]}", "mtu": 9500}]}])
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

    # Send traffic and Verify 8-9 steps
