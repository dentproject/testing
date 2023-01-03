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
from dent_os_testbed.lib.bridge.bridge_fdb import BridgeFdb
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
    Test Name: test_bridging_remove_restore_from_vlan
    Test Suite: suite_functional_bridging
    Test Overview: This test comes to verify: removing and restoring 
                   a port with a bridge address entry by it's vlan.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0 with vlan filtering ON.
    2.  Set ports swp1 swp2 swp3 swp4 master br0.
    3.  Set ports swp1 swp2 swp3 swp4 learning OFF.
    4.  Set ports swp1 swp2 swp3 swp4 flood OFF.
    5.  Set bridge br0 admin state UP.
    6.  Set entities swp1, swp2, swp3, swp4 UP state.
    7.  Add interfaces to vlans swp1 swp2 swp3 --> vlan 2.
    8.  Adding static FDB entry aa:bb:cc:dd:ee:11 for swp1 with vlan 2.
    9.  Removing swp1 from vlan 2.
    10. Verify that swp1 entry aa:bb:cc:dd:ee:11 vlan 2 has not been removed from the address table.
    11. Adding swp1 back to vlan 2.
    12. Send traffic with src mac aa:bb:cc:dd:ee:11 and vlan 2.
    13. Verify that reception on swp1.
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

    await IpLink.delete(input_data=[{device_host_name: [{"device": "bridge"}]}])
    await IpLink.delete(input_data=[{device_host_name: [{"device": "br0"}]}])
    out = await IpLink.add(
        input_data=[{device_host_name: [{"device": "br0", "type": "bridge", "vlan_filtering": 1}]}])
    assert out[0][device_host_name]["rc"] == 0, out

    out = await IpLink.set(
        input_data=[{device_host_name: [{"device": f"{ports[0]}", "master": "br0"}]}],
        input_data=[{device_host_name: [{"device": f"{ports[1]}", "master": "br0"}]}],
        input_data=[{device_host_name: [{"device": f"{ports[2]}", "master": "br0"}]}],
        input_data=[{device_host_name: [{"device": f"{ports[3]}", "master": "br0"}]}])
    assert out[0][device_host_name]["rc"] == 0, out

    out = await BridgeLink.set(
        input_data=[{device_host_name: [{"device": f"{ports[0]}", "learning": False}]}],
        input_data=[{device_host_name: [{"device": f"{ports[1]}", "learning": False}]}],
        input_data=[{device_host_name: [{"device": f"{ports[2]}", "learning": False}]}],
        input_data=[{device_host_name: [{"device": f"{ports[3]}", "learning": False}]}])
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
    
    out = await BridgeVlan.add(
        input_data=[{device_host_name: [
            {"device": f"{ports[0]}", "vid": 2},
            {"device": f"{ports[1]}", "vid": 2},
            {"device": f"{ports[2]}", "vid": 2},
            {"device": f"{ports[3]}", "vid": 2}]}])
    assert out[0][device_host_name]["rc"] == 0, out

    out = await BridgeFdb.add(
        input_data=[{device_host_name: [{"lladdr": "aa:bb:cc:dd:ee:11"}]}])
    assert out[0][device_host_name]["rc"] == 0, out

    out = await BridgeFdb.delete(
        input_data=[{device_host_name: [{"device": f"{ports[0]}", "vid": 2}]}])
    assert out[0][device_host_name]["rc"] == 0, out
    
    #11. Verify that swp1 entry aa:bb:cc:dd:ee:11 vlan 2 has not been removed from the address table.
    
    out = await BridgeFdb.add(
        input_data=[{device_host_name: [{"device": f"{ports[0]}", "vid": 2}]}])
    assert out[0][device_host_name]["rc"] == 0, out

    #13. Send traffic with src mac aa:bb:cc:dd:ee:11 and vlan 2.
    #14. Verify that reception on swp1.
