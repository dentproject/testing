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

pytestmark = pytest.mark.suite_acl_scale


@pytest.mark.asyncio
async def test_dentv2_acl_scale_validation(testbed):
    """
    Test Name: test_dentv2_acl_scale_validation
    Test Suite: suite_acl_scale
    Test Overview: Test ACL scale with validation
    Test Procedure:
    1. Create vlan endpoint devices
    2. create tc rules that match the streams
    3. create the tcp/ip streams
    4. validte for traffic loss
    """
    tgen_dev, infra_devices = await tgen_utils_get_dent_devices_with_tgen(
        testbed, [DeviceType.INFRA_SWITCH], 2
    )
    if not tgen_dev or not infra_devices:
        print("The testbed does not have enough dent with tgen connections")
        return

    await tb_reload_nw_and_flush_firewall(infra_devices)

    devices_info = {}
    for dd in infra_devices:
        devices_info[dd.host_name] = [
            # 'count' is the number of endpoints
            {
                "vlan": 500,
                "name": "CHAIN0",
                "count": 1,
            },
            {
                "vlan": 600,
                "name": "CHAIN1",
                "count": 1,
            },
            {
                "vlan": 400,
                "name": "CHAIN2",
                "count": 1,
            },
        ]

    chain0_src = []
    chain0_dst = []
    chain1_src = []
    chain1_dst = []
    chain2_src = []
    chain2_dst = []
    for dd in infra_devices:
        for swp in tgen_dev.links_dict[dd.host_name][1]:
            await tb_reset_qdisc(dd, swp, "ingress")

            chain0_src.append(f"{dd.host_name}_CHAIN0_{swp}")
            chain0_dst.append(f"{dd.host_name}_CHAIN0_{swp}")
            chain1_src.append(f"{dd.host_name}_CHAIN1_{swp}")
            chain1_dst.append(f"{dd.host_name}_CHAIN1_{swp}")
            chain2_src.append(f"{dd.host_name}_CHAIN2_{swp}")
            chain2_dst.append(f"{dd.host_name}_CHAIN2_{swp}")
            chain_input = {
                "dev": swp,
                "chain": "0",
                "direction": "ingress",
                "proto": "802.1q",
                "filtertype": {
                    "vlan_id": 4095,
                    "vlan_ethtype": "ipv4",
                    "src_ip": "0.0.0.0/32",
                    "dst_ip": "0.0.0.0/32",
                    "ip_proto": "tcp",
                },
            }
            for chain_num in range(3):
                chain_input["chain"] = f"{chain_num}"
                if chain_num == 1:
                    chain_input["filtertype"]["dst_port"] = 65535
                if chain_num == 2:
                    chain_input["filtertype"]["src_port"] = 65535
                out = await TcChain.add(input_data=[{dd.host_name: [chain_input]}])
                assert out[0][dd.host_name]["rc"] == 0, out

            out = await TcFilter.add(
                input_data=[
                    {
                        dd.host_name: [
                            {
                                "dev": swp,
                                "chain": "0",
                                "direction": "ingress",
                                "protocol": "802.1q",
                                "pref": 1,
                                "action": "drop",
                                "filtertype": {
                                    "skip_sw": "",
                                    "vlan_id": 500,
                                    "vlan_ethtype": "ipv4",
                                },
                            },
                            {
                                "dev": swp,
                                "chain": 0,
                                "direction": "ingress",
                                "protocol": "802.1q",
                                "pref": 2,
                                "action": "goto chain 1",
                                "filtertype": {
                                    "skip_sw": "",
                                    "vlan_id": 600,
                                    "vlan_ethtype": "ipv4",
                                    "ip_proto": "tcp",
                                },
                            },
                            {
                                "dev": swp,
                                "chain": 0,
                                "direction": "ingress",
                                "protocol": "802.1q",
                                "pref": 3,
                                "action": "goto chain 2",
                                "filtertype": {
                                    "skip_sw": "",
                                    "vlan_id": 400,
                                    "vlan_ethtype": "ipv4",
                                    "ip_proto": "udp",
                                },
                            },
                        ]
                    }
                ]
            )
            assert out[0][dd.host_name]["rc"] == 0, out
            out = await TcFilter.add(
                input_data=[
                    {
                        dd.host_name: [
                            {
                                "dev": swp,
                                "chain": "1",
                                "direction": "ingress",
                                "protocol": "802.1q",
                                "pref": 4,
                                "action": "drop",
                                "filtertype": {
                                    "skip_sw": "",
                                    "vlan_id": 600,
                                    "vlan_ethtype": "ipv4",
                                    "ip_proto": "tcp",
                                    "dst_port": 80,
                                },
                            }
                        ]
                    }
                ]
            )
            assert out[0][dd.host_name]["rc"] == 0, out
            out = await TcFilter.add(
                input_data=[
                    {
                        dd.host_name: [
                            {
                                "dev": swp,
                                "chain": "2",
                                "direction": "ingress",
                                "protocol": "802.1q",
                                "pref": 5,
                                "action": "drop",
                                "filtertype": {
                                    "skip_sw": "",
                                    "vlan_id": 400,
                                    "vlan_ethtype": "ipv4",
                                    "ip_proto": "udp",
                                    "src_port": 100,
                                },
                            }
                        ]
                    }
                ]
            )
            assert out[0][dd.host_name]["rc"] == 0, out
    streams = {
        "tcp_flow_chain0": {
            "ip_source": chain0_src,
            "ip_destination": chain0_dst,
            "vlanID": 500,
            "protocol": "ip",
            "ipproto": "tcp",
        },
        "tcp_http_flow_chain1": {
            "ip_source": chain1_src,
            "ip_destination": chain1_dst,
            "vlanID": 600,
            "protocol": "ip",
            "ipproto": "tcp",
            "dstPort": "80",
        },
        "udp_flow_chain2": {
            "ip_source": chain2_src,
            "ip_destination": chain2_dst,
            "vlanID": 400,
            "protocol": "ip",
            "ipproto": "udp",
            "srcPort": "100",
        },
    }

    await tgen_utils_create_devices_and_connect(
        tgen_dev, infra_devices, devices_info, need_vlan=True
    )
    await tgen_utils_setup_streams(
        tgen_dev,
        pytest._args.config_dir + f"/{tgen_dev.host_name}/tgen_acl_scale_validation",
        streams,
        force_update=True,
    )
    await tgen_utils_start_traffic(tgen_dev)
    sleep_time = 60 * 2
    tgen_dev.applog.info(f"zzZZZZZ({sleep_time})s")
    time.sleep(sleep_time)
    # await tgen_utils_stop_traffic(tgen_dev)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    # Traffic Verification
    for row in stats.Rows:
        assert float(row["Loss %"]) == 100.000, f'Failed>Loss percent: {row["Loss %"]}'

    await tgen_utils_stop_protocols(tgen_dev)

    # Delete the chain and all the rules it holds
    for dd in infra_devices:
        for swp in tgen_dev.links_dict[dd.host_name][1]:
            for chain_num in range(3):
                await TcChain.delete(
                    input_data=[
                        {dd.host_name: [{"dev": swp, "chain": chain_num, "direction": "ingress"}]}
                    ]
                )
            tb_restore_qdisc(dd, swp, "ingress")
