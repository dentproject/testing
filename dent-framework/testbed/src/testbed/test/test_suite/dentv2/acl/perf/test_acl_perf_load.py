# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import ipaddress
import time
from itertools import islice

import pytest

from testbed.Device import DeviceType
from testbed.lib.tc.tc_chain import TcChain
from testbed.lib.tc.tc_filter import TcFilter
from testbed.lib.tc.tc_qdisc import TcQdisc
from testbed.utils.test_utils.tb_utils import (
    tb_get_all_devices,
    tb_reload_nw_and_flush_firewall,
    tb_reset_qdisc,
    tb_restore_qdisc,
)
from testbed.utils.test_utils.tgen_utils import (
    tgen_utils_create_devices_and_connect,
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_get_swp_info,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_protocols,
    tgen_utils_stop_traffic,
)

pytestmark = pytest.mark.suite_acl_performance


@pytest.mark.asyncio
async def test_dentv2_acl_perf_load_default(testbed):
    """
    Test Name: test_dentv2_acl_perf_load_default
    Test Suite: suite_acl_performance
    Test Overview: Test ACL performance
    Test Procedure:
    1. Create max rules on default chain
    2. Check the load and unload times for installing rules
    """
    devices = await tb_get_all_devices(testbed)
    infra_devices = []
    for dd in devices:
        if dd.type in [DeviceType.INFRA_SWITCH]:
            infra_devices.append(dd)
    if not infra_devices:
        print("The testbed does not have enough dent")
        return
    infra_dev = infra_devices[0]
    swp = infra_dev.links[0][0]
    sip = ipaddress.ip_address("10.0.0.1")

    await tb_reload_nw_and_flush_firewall(infra_devices)

    filter_input = [
        {
            "dev": swp,
            # "chain": f"FORWARD",
            "direction": "ingress",
            "protocol": "802.1q",
            "pref": 1,
            "action": "drop",
            "filtertype": {
                "skip_sw": "",
                "vlan_id": 100,
                "vlan_ethtype": "ipv4",
                "src_ip": sip,
                "ip_proto": "tcp",
                "dst_port": 17,
            },
        }
    ]
    await _test_dentv2_acl_perf_load_helper(infra_devices, None, filter_input)


@pytest.mark.asyncio
async def test_dentv2_acl_perf_load_chains(testbed):
    """
    Test Name: test_dentv2_acl_perf_load_chains
    Test Suite: suite_acl_performance
    Test Overview: test the ACL performance per chain
    Test Procedure:
    1. create chain 0,1,2 with ipv4 src and tcp dst port
    2. create max rules on each chain and check the load/unload time
    """
    devices = await tb_get_all_devices(testbed)
    infra_devices = []
    for dd in devices:
        if dd.type in [DeviceType.INFRA_SWITCH]:
            infra_devices.append(dd)
    if not infra_devices:
        print("The testbed does not have enough dent")
        return
    infra_dev = infra_devices[0]
    swp = infra_dev.links[0][0]
    sip = ipaddress.ip_address("10.0.0.1")

    await tb_reload_nw_and_flush_firewall(infra_devices)

    for chain_num in range(3):
        chain_input = [
            {
                "dev": swp,
                "chain": f"{chain_num}",
                "direction": "ingress",
                "proto": "802.1q",
                "filtertype": {
                    "vlan_id": 4095,
                    "vlan_ethtype": "ipv4",
                    "src_ip": "0.0.0.0/32",
                    "ip_proto": "tcp",
                    "dst_port": 65535,
                },
            }
        ]
        filter_input = [
            {
                "dev": swp,
                "chain": f"{chain_num}",
                "direction": "ingress",
                "protocol": "802.1q",
                "pref": 1,
                "action": "drop",
                "filtertype": {
                    "skip_sw": "",
                    "vlan_id": 100,
                    "vlan_ethtype": "ipv4",
                    "src_ip": sip,
                    "ip_proto": "tcp",
                    "dst_port": 17,
                },
            }
        ]
        await _test_dentv2_acl_perf_load_helper(infra_devices, chain_input, filter_input)


async def _test_dentv2_acl_perf_load_helper(infra_devices, chain_input, filter_input):
    # Create the chain and the max rules for that chain on all devices
    # Delete the chain and all the rules it holds

    for dd in infra_devices:
        for swp in [link[0] for link in dd.links]:
            await tb_reset_qdisc(dd, swp, "ingress")
            filter_input[0]["dev"] = swp
            filter_input[0]["pref"] = 1

            if chain_input:
                chain_input[0]["dev"] = swp
                out = await TcChain.add(input_data=[{dd.host_name: chain_input}])
                assert out[0][dd.host_name]["rc"] == 0, out

            loadtime = 0
            num_rules = 0
            while True:
                starttime = time.time()
                out = await TcFilter.add(input_data=[{dd.host_name: filter_input}])
                endtime = time.time()
                if out[0][dd.host_name]["rc"] != 0:
                    break
                loadtime += endtime - starttime  # Capture load time for each rule
                filter_input[0]["pref"] += 1
                filter_input[0]["filtertype"]["src_ip"] += 1
                num_rules += 1

            # Delete the chain and all the rules it holds
            unloadtime = 0
            starttime = time.time()
            if chain_input:
                await TcChain.delete(
                    input_data=[
                        {
                            dd.host_name: [
                                {
                                    "dev": swp,
                                    "chain": chain_input[0]["chain"],
                                    "direction": "ingress",
                                }
                            ]
                        }
                    ]
                )
            else:
                # Default chain
                await TcFilter.delete(
                    input_data=[
                        {
                            dd.host_name: [
                                {
                                    "dev": swp,
                                    "direction": "ingress",
                                }
                            ]
                        }
                    ]
                )
            endtime = time.time()
            unloadtime += endtime - starttime
            tb_restore_qdisc(dd, swp, "ingress")
            assert loadtime < 166, f"Load time: {loadtime}s, num rules: {num_rules}"
            assert unloadtime < 20, f"Unload time: {unloadtime}s"
