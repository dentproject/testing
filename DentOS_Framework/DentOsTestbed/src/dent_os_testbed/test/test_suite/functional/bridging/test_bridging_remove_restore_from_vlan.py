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
    1-2.  Init bridge entity br0 with vlan filtering ON.
    3.  Set ports swp1 swp2 swp3 swp4 master br0.
    4.  Set ports swp1 swp2 swp3 swp4 learning OFF.
    5.  Set ports swp1 swp2 swp3 swp4 flood OFF.
    6.  Set bridge br0 admin state UP.
    7.  Set entities swp1, swp2, swp3, swp4 UP state.
    8.  Add interfaces to vlans swp1 swp2 swp3 --> vlan 2.
    9.  Adding static FDB entry aa:bb:cc:dd:ee:11 for swp1 with vlan 2.
    10. Removing swp1 from vlan 2.
    11. Verify that swp1 entry aa:bb:cc:dd:ee:11 vlan 2 has not been removed from the address table.
    12. Adding swp1 back to vlan 2.
    13. Send traffic with src mac aa:bb:cc:dd:ee:11 and vlan 2.
    14. Verify that reception on swp1.
    """

    logger = AppLogger(DEFAULT_LOGGER)
    dev = await tb_get_all_devices(testbed)
    logger.info("Devices:", dev)

    dut = dev[0]
    bridge = "br0"

    await IpLink.delete(input_data=[{dut.host_name: [{"device": "bridge"}]}])
    await IpLink.delete(input_data=[{dut.host_name: [{"device": "br0"}]}])
    out = await IpLink.add(
        input_data=[{dut.host_name: [{"device": "br0", "type": "bridge", "vlan_filtering": 1}]}])
    assert out[0][dut.host_name]["rc"] == 0, out

    out = await IpLink.set(
        input_data=[{dut.host_name: [{"device": "swp1", "master": "br0"}]}],
        input_data=[{dut.host_name: [{"device": "swp2", "master": "br0"}]}],
        input_data=[{dut.host_name: [{"device": "swp3", "master": "br0"}]}],
        input_data=[{dut.host_name: [{"device": "swp4", "master": "br0"}]}])
    assert out[0][dut.host_name]["rc"] == 0, out

    out = await BridgeLink.set(
        input_data=[{dut.host_name: [{"device": "swp1", "learning": False}]}],
        input_data=[{dut.host_name: [{"device": "swp2", "learning": False}]}],
        input_data=[{dut.host_name: [{"device": "swp3", "learning": False}]}],
        input_data=[{dut.host_name: [{"device": "swp4", "learning": False}]}])
    assert out[0][dut.host_name]["rc"] == 0, out

    out = await BridgeLink.set(
        input_data=[{dut.host_name: [{"device": "swp1", "flood": False}]}],
        input_data=[{dut.host_name: [{"device": "swp2", "flood": False}]}],
        input_data=[{dut.host_name: [{"device": "swp3", "flood": False}]}],
        input_data=[{dut.host_name: [{"device": "swp4", "flood": False}]}])
    assert out[0][dut.host_name]["rc"] == 0, out

    out = await IpLink.set(
        input_data=[{dut.host_name: [{"device": bridge, "operstate": "up"}]}])
    assert out[0][dut.host_name]["rc"] == 0, out

    out = await IpLink.set(
        input_data=[{dut.host_name: [{"device": "swp1", "operstate": "up"}]}],
        input_data=[{dut.host_name: [{"device": "swp2", "operstate": "up"}]}],
        input_data=[{dut.host_name: [{"device": "swp3", "operstate": "up"}]}],
        input_data=[{dut.host_name: [{"device": "swp4", "operstate": "up"}]}])
    assert out[0][dut.host_name]["rc"] == 0, out
    
    out = await BridgeVlan(
        input_data=[{dut.host_name: [{"device": "swp1", "vid": 2}]}],
        input_data=[{dut.host_name: [{"device": "swp2", "vid": 2}]}],
        input_data=[{dut.host_name: [{"device": "swp3", "vid": 2}]}])
    assert out[0][dut.host_name]["rc"] == 0, out
    
    out = await BridgeFdb.add(
        input_data=[{dut.host_name: [{"device": "swp1", "vid": 2}]}])
    assert out[0][dut.host_name]["rc"] == 0, out
    
    #9.  Adding static FDB entry aa:bb:cc:dd:ee:11 for swp1 with vlan 2.
    """
    out = await BridgeFdb.add(
            input_data=[
                {
                    # device 1
                    "test_dev1": [
                        {
                            "lladdr": "aa:bb:cc:dd:ee:11",
                            #"static":True,

                            'dev':'string',
                            'lladdr':'mac_t',
                            'local':'undefined',
                            'static':'undefined',
                            'dynamic':'undefined',
                            'self':'bool',
                            'master':'bool',
                            'router':'bool',
                            'use':'bool',
                            'extern_learn':'bool',
                            'sticky':'bool',
                            'dst':'ip_addr_t',
                            'src_vni':'undefined',
                            'vni':'int',
                            'port':'int',
                            'via':'string',
                            'options':'string',
                        }
                    ],
                   
                }
            ],
            device_obj={"test_dev1": dv1},
        )
    """
    out = await BridgeFdb.delete(
        input_data=[{dut.host_name: [{"device": "swp1", "vid": 2}]}])
    assert out[0][dut.host_name]["rc"] == 0, out
    
    #11. Verify that swp1 entry aa:bb:cc:dd:ee:11 vlan 2 has not been removed from the address table.
    
    out = await BridgeFdb.add(
        input_data=[{dut.host_name: [{"device": "swp1", "vid": 2}]}])
    assert out[0][dut.host_name]["rc"] == 0, out

    #13. Send traffic with src mac aa:bb:cc:dd:ee:11 and vlan 2.
    #14. Verify that reception on swp1.