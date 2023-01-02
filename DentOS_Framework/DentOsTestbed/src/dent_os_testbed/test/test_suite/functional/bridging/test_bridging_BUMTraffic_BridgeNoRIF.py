#!/usr/lib/env python3.6
# Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import time
import asyncio
import pytest

from dent_os_testbed.constants import DEFAULT_LOGGER
from dent_os_testbed.Device import DeviceType
from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.logger.Logger import AppLogger
from dent_os_testbed.utils.test_utils.tb_utils import (
    tb_ping_device,
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
    Test Name: test_bridging_BUMTraffic_BridgeNoRIF
    Test Suite: suite_functional_bridging
    Test Overview: Check forwarding different bridged packets within the same 
                   bridge domain.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1 swp2 swp3 swp4 master br0.
    3.  Set bridge br0 admin state UP.
    4.  Set entities swp1, swp2, swp3, swp4 UP state.
    5.  Start tcpdump capture on DUT ingress port.
    6.  Clear TG counters.
    7.  Send different types of packets (IPv6 MC, IPv4 BC + MC) from src TG.
    8.  Set stream utilization according to TG streams mode. If parallel - 
        share 100% WS between streams else each stream will sent in MAX rate.
    9.  If TG stream mode is 'serial' change stream transmit mode to 'Advance 
        to next stream' and add inter-stream gap.
    10. Analyze counters taking in account the traffic type that was sent vs. 
        expected value + trapped and mirrored.
    """

    logger = AppLogger(DEFAULT_LOGGER)
    dev = await tb_get_all_devices(testbed)
    logger.info("Devices:", dev)

    dut = dev[0]
    bridge = "br0"

    out = await IpLink.add(
    input_data=[{dut.host.name: [{"device": bridge, "type": "bridge"}]}])
    assert out[0][dut.host_name]["rc"] == 0, out

    out = await IpLink.set(
            input_data=[{dut.host_name: [{"device": "swp1", "master": "br0"}]}],
            input_data=[{dut.host_name: [{"device": "swp2", "master": "br0"}]}],
            input_data=[{dut.host_name: [{"device": "swp3", "master": "br0"}]}],
            input_data=[{dut.host_name: [{"device": "swp4", "master": "br0"}]}])
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

    rc = await tb_ping_device(dev, f"{dut.ip}", dump=True)
    if rc != 0:
        dev.applog.info(f"Failed to reach {dut.host_name} {rc}")
        return False
    return True

    #6-10 steps
    #NOT CLEAR