# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import copy
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
from testbed.utils.test_utils.tc_flower_utils import tcutil_get_tc_rule_stats
from testbed.utils.test_utils.tgen_utils import (
    tgen_utils_connect_to_tgen,
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
async def test_dentv2_acl_tcp_udp_icmp_chains(testbed):
    """
    Test Name: test_dentv2_acl_tcp_udp_icmp_chains
    Test Suite: suite_acl_scale
    Test Overview: To test multiple TC chains
    Test Procedure:
    1. Create two chains chain 0 for tcp/udp sport and dport and chain 1 for icmp type and code
      tc chain add block 1 ingress proto 802.1q chain 0 flower vlan_id 4095 vlan_ethtype ipv4  src_ip 0.0.0.0/32 dst_ip 0.0.0.0/32 ip_proto udp dst_port 65535 src_port 65535
      tc chain add block 1 ingress proto 802.1q chain 1 flower vlan_id 4095 vlan_ethtype ipv4  src_ip 0.0.0.0/32 dst_ip 0.0.0.0/32 ip_proto icmp type 0 code 0
      tc filter delete block 1 ingress chain 0
      tc filter delete block 1 ingress chain 1
      tc filter add block 1 ingress protocol ip pref 10 chain 0 flower skip_sw src_ip 10.0.0.10 dst_ip 20.0.0.10  ip_proto tcp dst_port 80 src_port 90 action pass
      tc filter add block 1 ingress protocol ip pref 20 chain 0 flower skip_sw src_ip 10.0.0.10 dst_ip 20.0.0.10  ip_proto tcp dst_port 80 action pass
      tc filter add block 1 ingress protocol ip pref 30 chain 0 flower skip_sw src_ip 10.0.0.10 dst_ip 20.0.0.10  ip_proto tcp action pass
      tc filter add block 1 ingress protocol ip pref 40 chain 0 flower skip_sw src_ip 10.0.0.10 dst_ip 20.0.0.10  ip_proto udp dst_port 80 src_port 90 action pass
      tc filter add block 1 ingress protocol ip pref 50 chain 0 flower skip_sw src_ip 10.0.0.10 dst_ip 20.0.0.10  ip_proto udp dst_port 80 action pass
      tc filter add block 1 ingress protocol ip pref 60 chain 0 flower skip_sw src_ip 10.0.0.10 dst_ip 20.0.0.10  ip_proto udp action pass
      tc filter add block 1 ingress protocol ip pref 70 chain 0 flower skip_sw src_ip 10.0.0.10 dst_ip 20.0.0.10  ip_proto icmp action goto chain 1
      tc filter add block 1 ingress protocol ip pref 80 chain 0 flower skip_sw src_ip 10.0.0.10 dst_ip 20.0.0.10  action pass

      tc filter add block 1 ingress protocol ip pref 10 chain 1 flower skip_sw src_ip 10.0.0.10 dst_ip 20.0.0.10  ip_proto icmp type 8 code 0 action pass
      tc filter add block 1 ingress protocol ip pref 20 chain 1 flower skip_sw src_ip 10.0.0.10 dst_ip 20.0.0.10  ip_proto icmp type 8 action pass
      tc filter add block 1 ingress protocol ip pref 30 chain 1 flower skip_sw src_ip 10.0.0.10 dst_ip 20.0.0.10  ip_proto icmp action pass
    2. create tgen traffic items that matches the above rules
    3. verify the rules got hit.
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
    swp = swp_tgen_ports[1]
    swp_info = {}
    await tgen_utils_get_swp_info(infra_dev, swp, swp_info)
    dip = ipaddress.ip_address(".".join(swp_info["ip"][:-1] + [str(int(swp[3:]) * 2)]))

    await tb_reload_nw_and_flush_firewall([infra_dev])
    # create the chains
    chains = {
        "0": {
            "filtertype": {
                "vlan_id": 4095,
                "vlan_ethtype": "ipv4",
                "src_ip": "0.0.0.0/32",
                "dst_ip": "0.0.0.0/32",
                "ip_proto": "tcp",
                "dst_port": 65535,
                "src_port": 65535,
            },
            "rules": [
                {
                    "pref": 10,
                    "action": "pass",
                    "filtertype": {
                        "ip_proto": "tcp",
                        "dst_port": 80,
                        "src_port": 90,
                    },
                },
                {
                    "pref": 20,
                    "action": "pass",
                    "filtertype": {
                        "ip_proto": "tcp",
                        "dst_port": 80,
                    },
                },
                {
                    "pref": 30,
                    "action": "pass",
                    "filtertype": {
                        "ip_proto": "tcp",
                    },
                },
                {
                    "pref": 40,
                    "action": "pass",
                    "filtertype": {
                        "ip_proto": "udp",
                        "dst_port": 80,
                        "src_port": 90,
                    },
                },
                {
                    "pref": 50,
                    "action": "pass",
                    "filtertype": {
                        "ip_proto": "udp",
                        "dst_port": 80,
                    },
                },
                {
                    "pref": 60,
                    "action": "pass",
                    "filtertype": {
                        "ip_proto": "udp",
                    },
                },
                {
                    "pref": 70,
                    "action": "goto chain 1",
                    "filtertype": {
                        "ip_proto": "icmp",
                    },
                },
                {
                    "pref": 80,
                    "action": "pass",
                    "filtertype": {},
                },
            ],
        },
        "1": {
            "filtertype": {
                "vlan_id": 4095,
                "vlan_ethtype": "ipv4",
                "src_ip": "0.0.0.0/32",
                "dst_ip": "0.0.0.0/32",
                "ip_proto": "icmp",
                "type": 0,
                "code": 0,
            },
            "rules": [
                {
                    "pref": 10,
                    "action": "pass",
                    "filtertype": {
                        "ip_proto": "icmp",
                        "type": 8,
                        "code": 0,
                    },
                },
                {
                    "pref": 20,
                    "action": "pass",
                    "filtertype": {
                        "ip_proto": "icmp",
                        "type": 8,
                    },
                },
                {
                    "pref": 30,
                    "action": "pass",
                    "filtertype": {
                        "ip_proto": "icmp",
                    },
                },
            ],
        },
    }
    for chain in chains.keys():
        input_data = [
            {
                dent: [
                    {
                        "block": "1",
                        "chain": chain,
                        "direction": "ingress",
                    },
                ],
            },
        ]
        await TcChain.delete(input_data=input_data)
        input_data[0][dent][0]["proto"] = "802.1q"
        input_data[0][dent][0]["filtertype"] = chains[chain]["filtertype"]
        await TcChain.add(input_data=input_data)
        # create the rules
        for rule in chains[chain]["rules"]:
            input_data[0][dent][0]["skip_sw"] = ""
            input_data[0][dent][0]["protocol"] = "ip"
            for k, v in rule.items():
                input_data[0][dent][0][k] = v
            input_data[0][dent][0]["filtertype"]["src_ip"] = sip
            input_data[0][dent][0]["filtertype"]["dst_ip"] = dip
            input_data[0][dent][0]["filtertype"]["skip_sw"] = ""
            await TcFilter.add(input_data=input_data)

    await tgen_utils_connect_to_tgen(tgen_dev, infra_dev)
    streams = {
        "tcp-sp-90-dp-80": {
            "protocol": "ip",
            "srcIp": sip,
            "dstIp": dip,
            "ipproto": "tcp",
            "dstPort": "80",
            "srcPort": "90",
        },
        "tcp-dp-80": {
            "protocol": "ip",
            "srcIp": sip,
            "dstIp": dip,
            "ipproto": "tcp",
            "dstPort": "80",
        },
        "tcp": {
            "protocol": "ip",
            "srcIp": sip,
            "dstIp": dip,
            "ipproto": "tcp",
        },
        "udp-sp-90-dp-80": {
            "protocol": "ip",
            "srcIp": sip,
            "dstIp": dip,
            "ipproto": "udp",
            "dstPort": "80",
            "srcPort": "90",
        },
        "udp-dp-80": {
            "protocol": "ip",
            "srcIp": sip,
            "dstIp": dip,
            "ipproto": "udp",
            "dstPort": "80",
        },
        "udp": {
            "protocol": "ip",
            "srcIp": sip,
            "dstIp": dip,
            "ipproto": "udp",
        },
        "icmp-t8-c0": {
            "protocol": "ip",
            "ipproto": "icmpv2",
            "srcIp": sip,
            "dstIp": dip,
            "icmpType": "8",
            "icmpCode": "0",
        },
        "icmp-t8-c1": {
            "protocol": "ip",
            "ipproto": "icmpv2",
            "srcIp": sip,
            "dstIp": dip,
            "icmpType": "8",
            "icmpCode": "1",
        },
        "icmp-t5": {
            "protocol": "ip",
            "ipproto": "icmpv1",
            "srcIp": sip,
            "dstIp": dip,
            "icmpType": "5",
        },
        "raw": {
            "protocol": "ip",
            "srcIp": sip,
            "dstIp": dip,
        },
    }

    await tgen_utils_setup_streams(
        tgen_dev,
        pytest._args.config_dir + f"/{dent}/tgen_tc_chain__basic_config.ixncfg",
        streams,
    )
    await tgen_utils_start_traffic(tgen_dev)
    time.sleep(10)
    await tgen_utils_stop_traffic(tgen_dev)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) != 100.000, f'Failed>Loss percent: {row["Loss %"]}'

    swp_tc_rules = {}
    await tcutil_get_tc_rule_stats(infra_dev, swp_tgen_ports, swp_tc_rules)

    await tgen_utils_stop_protocols(tgen_dev)
    for chain in chains.keys():
        input_data = [
            {
                dent: [
                    {
                        "block": "1",
                        "chain": chain,
                        "direction": "ingress",
                    },
                ],
            },
        ]
        await TcChain.delete(input_data=input_data)
