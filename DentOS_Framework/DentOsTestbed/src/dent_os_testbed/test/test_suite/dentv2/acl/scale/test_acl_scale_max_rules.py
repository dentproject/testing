# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import copy
import ipaddress
import time
from itertools import islice

import pytest

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.lib.tc.tc_chain import TcChain
from dent_os_testbed.lib.tc.tc_filter import TcFilter
from dent_os_testbed.lib.tc.tc_qdisc import TcQdisc
from dent_os_testbed.utils.test_utils.tb_utils import (
    tb_reload_nw_and_flush_firewall,
    tb_reset_qdisc,
    tb_restore_qdisc,
)
from dent_os_testbed.utils.test_utils.tgen_utils import (
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
async def test_dentv2_acl_scale_max_rules_20B(testbed):
    """
    Test Name: test_dentv2_acl_scale_max_rules_20B
    Test Suite: suite_acl_scale
    Test Overview: test max rules of size 20Bytes each
    Test Procedure:
    1. create chain 0,1,2 with ipv4 src and tcp dst port
    2. Make the size of chain rules 20B
    3. create max rules and pass traffic to test if the rules get hit
    """

    tgen_dev, infra_devices = await tgen_utils_get_dent_devices_with_tgen(
        testbed, [DeviceType.INFRA_SWITCH], 2
    )
    if not tgen_dev or not infra_devices:
        print("The testbed does not have enough dent with tgen connections")
        return
    infra_dev = infra_devices[0]
    dent = infra_dev.host_name
    swp_tgen_ports = tgen_dev.links_dict[dent][1]
    swp = swp_tgen_ports[0]
    swp_info = {}
    await tgen_utils_get_swp_info(infra_dev, swp, swp_info)
    sip = ipaddress.ip_address(".".join(swp_info["ip"][:-1] + [str(int(swp[3:]) * 2)]))

    await tb_reload_nw_and_flush_firewall(infra_devices)

    for chain_num in range(3):  # TODO: Might need to re-structure if the test takes too long
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
                    "vlan_id": 600,
                    "vlan_ethtype": "ipv4",
                    "ip_proto": "tcp",
                    "dst_port": 23,
                },
            }
        ]
        stream_input = {
            "vlanID": 600,
            "protocol": "ip",
            "ipproto": "tcp",
            "dstPort": "23",
        }
        await _test_dentv2_acl_scale_max_rules_helper(
            tgen_dev, infra_devices, chain_input, filter_input, stream_input
        )


@pytest.mark.asyncio
async def test_dentv2_acl_scale_max_rules_40B(testbed):
    """
    Test Name: test_dentv2_acl_scale_max_rules_40B
    Test Suite: suite_acl_scale
    Test Overview: test ACL scale per chain of 40B
    Test Procedure:
    1. create chain 0,1,2 with ipv4 src and tcp dst port
    2. Make the size of chain rules 40B
    3. create max rules and pass traffic to test if the rules get hit
    """
    tgen_dev, infra_devices = await tgen_utils_get_dent_devices_with_tgen(
        testbed, [DeviceType.INFRA_SWITCH], 2
    )
    if not tgen_dev or not infra_devices:
        print("The testbed does not have enough dent with tgen connections")
        return
    infra_dev = infra_devices[0]
    dent = infra_dev.host_name
    swp_tgen_ports = tgen_dev.links_dict[dent][1]
    swp = swp_tgen_ports[1]
    swp_info = {}
    await tgen_utils_get_swp_info(infra_dev, swp, swp_info)
    sip = ipaddress.ip_address(".".join(swp_info["ip"][:-1] + [str(int(swp[3:]) * 2)]))

    await tb_reload_nw_and_flush_firewall(infra_devices)

    for chain_num in range(3):  # TODO: Might need to re-structure if the test takes too long
        chain_input = [
            {
                "dev": swp,
                "chain": f"{chain_num}",
                "direction": "ingress",
                "proto": "802.1q",
                "filtertype": {
                    "vlan_id": 4095,
                    "vlan_ethtype": "ipv4",
                    "src_mac": "00:00:00:00:00:00",
                    "dst_mac": "00:00:00:00:00:00",
                    "src_ip": "0.0.0.0/32",
                    "dst_ip": "0.0.0.0/32",
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
                    "vlan_id": 600,
                    "vlan_ethtype": "ipv4",
                    "ip_proto": "tcp",
                    "dst_port": 23,
                },
            }
        ]
        stream_input = {
            "protocol": "ip",
            "vlanID": 600,
            "ipproto": "tcp",
            "dstPort": "23",
        }
        await _test_dentv2_acl_scale_max_rules_helper(
            tgen_dev, infra_devices, chain_input, filter_input, stream_input
        )


@pytest.mark.asyncio
async def test_dentv2_acl_scale_max_rules_60B(testbed):
    """
    Test Name: test_dentv2_acl_scale_max_rules_60B
    Test Suite: suite_acl_scale
    Test Overview: test ACL scale per chain of 60Byte size
    Test Procedure:
    1. create chain 0,1,2 with ipv4 src and tcp dst port
    2. Make the size of chain rules 60B
    3. create max rules and pass traffic to test if the rules get hit
    """
    tgen_dev, infra_devices = await tgen_utils_get_dent_devices_with_tgen(
        testbed, [DeviceType.INFRA_SWITCH], 2
    )
    if not tgen_dev or not infra_devices:
        print("The testbed does not have enough dent with tgen connections")
        return
    infra_dev = infra_devices[0]
    dent = infra_dev.host_name
    swp_tgen_ports = tgen_dev.links_dict[dent][1]
    swp = swp_tgen_ports[1]
    swp_info = {}
    await tgen_utils_get_swp_info(infra_dev, swp, swp_info)
    sip = ipaddress.ip_address(".".join(swp_info["ip"][:-1] + [str(int(swp[3:]) * 2)]))

    await tb_reload_nw_and_flush_firewall(infra_devices)

    for chain_num in range(3):  # TODO: Might need to re-structure if the test takes too
        chain_input = [
            {
                "dev": swp,
                "chain": f"{chain_num}",
                "direction": "ingress",
                "proto": "802.1q",
                "filtertype": {
                    "vlan_id": 4095,
                    "vlan_ethtype": "ipv4",
                    "src_mac": "00:00:00:00:00:00",
                    "dst_mac": "00:00:00:00:00:00",
                    "arp_sha": "00:00:00:00:00:00",
                    "arp_tha": "00:00:00:00:00:00",
                    "src_ip": "0.0.0.0/32",
                    "dst_ip": "0.0.0.0/32",
                    "enc_src_ip": "0.0.0.0/32",
                    "enc_dst_ip": "0.0.0.0/32",
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
                    "vlan_id": 600,
                    "vlan_ethtype": "ipv4",
                    "ip_proto": "tcp",
                    "dst_port": 23,
                },
            }
        ]
        stream_input = {
            "protocol": "ip",
            "vlanID": 600,
            "ipproto": "tcp",
            "dstPort": "23",
        }
        await _test_dentv2_acl_scale_max_rules_helper(
            tgen_dev, infra_devices, chain_input, filter_input, stream_input
        )


async def _test_dentv2_acl_scale_max_rules_helper(
    tgen_dev, infra_devices, chain_input, filter_input, stream_input
):
    # Create the chain and the max rules for that chain on all devices
    # Run traffic and check if rules are hit
    # Delete the chain and all the rules it holds

    chain_num = int(chain_input[0]["chain"])
    devices_info = {}
    for dd in infra_devices:
        devices_info[dd.host_name] = [
            # 'count' is the number of endpoints
            {
                "vlan": 600,
                "name": f"CHAIN{chain_num}",
                "count": 1,
            },
        ]
    ip_src = []
    ip_dst = []
    num_rules_dict = {}
    for dd in infra_devices:
        for swp in tgen_dev.links_dict[dd.host_name][1]:
            await tb_reset_qdisc(dd, swp, "ingress")
            chain_input[0]["dev"] = swp
            filter_input[0]["dev"] = swp
            ip_src.append(f"{dd.host_name}_CHAIN{chain_num}_{swp}")
            ip_dst.append(f"{dd.host_name}_CHAIN{chain_num}_{swp}")

            if chain_num > 0:  # Install goto filters in chain 0
                chain_input[0]["chain"] = 0
                out = await TcChain.add(input_data=[{dd.host_name: chain_input}])
                assert out[0][dd.host_name]["rc"] == 0, out
                chain_input[0]["chain"] = chain_num

                goto_filter = copy.deepcopy(filter_input)
                del goto_filter[0]["filtertype"]["dst_port"]
                goto_filter[0]["chain"] = 0
                goto_filter[0]["action"] = f"goto chain {chain_num}"
                out = await TcFilter.add(input_data=[{dd.host_name: goto_filter}])
                assert out[0][dd.host_name]["rc"] == 0, out
                filter_input[0]["pref"] += 1
                del goto_filter

            out = await TcChain.add(input_data=[{dd.host_name: chain_input}])
            assert out[0][dd.host_name]["rc"] == 0, out

        num_rules_dict[dd.host_name] = {}
        hit_max_rules = False
        while not hit_max_rules:
            for swp in tgen_dev.links_dict[dd.host_name][1]:
                num_rules_dict[dd.host_name].setdefault(swp, 0)
                filter_input[0]["dev"] = swp
                out = await TcFilter.add(input_data=[{dd.host_name: filter_input}])
                if out[0][dd.host_name]["rc"] != 0:
                    hit_max_rules = True
                    break
                filter_input[0]["pref"] += 1
                num_rules_dict[dd.host_name][swp] += 1
            filter_input[0]["filtertype"]["dst_port"] += 1

    streams = {}
    port = stream_input["dstPort"]
    for ip in ip_src:
        host_name, _, swp = ip.split("_")
        stream_input["dstPort"] = {
            "type": "increment",
            "start": port,
            "step": 1,
            "count": num_rules_dict[host_name][swp] - 1,
        }
        stream_input["ip_source"] = [ip]
        stream_input["ip_destination"] = ip_dst
        streams[f"{host_name}_tcp_flow_{swp}"] = stream_input.copy()

    for streams_chunk in chunks(streams, 256):
        await tgen_utils_create_devices_and_connect(
            tgen_dev, infra_devices, devices_info, need_vlan=True
        )
        await tgen_utils_setup_streams(
            tgen_dev,
            pytest._args.config_dir + f"/{tgen_dev.host_name}/tgen_acl_scale_max_rules",
            streams_chunk,
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
            await TcChain.delete(
                input_data=[
                    {
                        dd.host_name: [
                            {
                                "dev": swp,
                                "chain": chain_num,
                                "direction": "ingress",
                            }
                        ]
                    }
                ]
            )
            if chain_num > 0:  # Delete goto filters
                await TcChain.delete(
                    input_data=[{dd.host_name: [{"dev": swp, "chain": 0, "direction": "ingress"}]}]
                )
            await tb_restore_qdisc(dd, swp, "ingress")


def chunks(data, SIZE=10000):
    it = iter(data)
    for i in range(0, len(data), SIZE):
        yield {k: data[k] for k in islice(it, SIZE)}
