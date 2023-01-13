import json
import time

import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.iptables.ip_tables import IpTables
from dent_os_testbed.utils.test_utils.tb_utils import tb_reload_nw_and_flush_firewall
from dent_os_testbed.utils.test_utils.tc_flower_utils import (
    tcutil_cleanup_tc_rules,
    tcutil_get_iptables_rule_stats,
    tcutil_get_tc_rule_stats,
    tcutil_iptable_to_tc,
)
from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_clear_traffic_stats,
    tgen_utils_connect_to_tgen,
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_get_swp_info,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_protocols,
    tgen_utils_stop_traffic,
)

pytestmark = pytest.mark.suite_tc_flower


@pytest.mark.asyncio
async def test_tc_flower_persistency_w_traffic(testbed):
    """
    Test Name: test_tc_flower_persistency_w_traffic
    Test Suite: suite_tc_flower
    Test Overview: Test tc flower tool with traffic
    Test Procedure:
    1. setup dent switch
      - get a dent switch with two ixia ports on it
      - configure the switch for h/w forwarding
    2. setup tgen
      - get a tgen device
      - connect to the ports
      - setup traffic stream with a know SIP and DIP
    3. start the traffic
    4. install iptables rules in filter table at FORWARD stage
      to drop the packet matching SIP and DIP
      - iptables -t filter -A FORWARD -i swp1 -s SIP -d DIP -j DROP
    5. check the traffic stats
      - there shouldnt be any loss
    6. run the tc persistency  tools
      - iptables-save -t filter  > /tmp/iptables.rules
      - iptables-unroll /tmp/iptables.rules /tmp/iptables-unrolled.rules FORWARD
      - iptables-slice /tmp/iptables-unrolled.rules /tmp/iptables-sliced.rules FORWARD
      - tc-flower-load /tmp/iptables-sliced.rules FORWARD
    7. check the traffic stats
      -- all the packets matching the SIP and DIP should be dropped.
    """
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgen connections")
        return
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    swp_tgen_ports = tgen_dev.links_dict[dent][1]

    await tb_reload_nw_and_flush_firewall([dent_dev])

    await tgen_utils_connect_to_tgen(tgen_dev, dent_dev)

    # get a link and mac address
    swp = swp_tgen_ports[0]
    out = await IpLink.show(
        input_data=[{dent: [{"device": swp, "cmd_options": "-j"}]}],
    )
    dent_dev.applog.info(out)
    assert out[0][dent]["rc"] == 0
    link = json.loads(out[0][dent]["result"])
    swp_mac = link[0]["address"]

    streams = {
        "bgp": {
            "protocol": "ip",
            "ipproto": "tcp",
            "dstPort": "179",
        },
        "ssh": {
            "protocol": "ip",
            "ipproto": "tcp",
            "dstPort": "22",
        },
        "https": {
            "protocol": "ip",
            "ipproto": "tcp",
            "dstPort": "443",
        },
        # create a raw vlan stream
        "https_vlan": {
            "srcIp": f"20.0.{swp[3:]}.2",
            "dstIp": f"20.0.{swp[3:]}.1",
            "srcMac": "00:11:01:00:00:01",
            "dstMac": "00:12:01:00:00:01",
            "type": "raw",
            "rate": "10",
            "frameSize": "256",
            "protocol": "802.1Q",
            "vlanID": "100",
            "ipproto": "tcp",
            "dstPort": "443",
        },
        "dns": {
            "protocol": "ip",
            "ipproto": "udp",
            "dstPort": "53",
        },
        "ntp": {
            "protocol": "ip",
            "ipproto": "udp",
            "dstPort": "123",
        },
        "dhcp": {
            "protocol": "ip",
            "ipproto": "udp",
            "srcPort": 67,
            "dstPort": "68",
        },
        "mqtt": {
            "protocol": "ip",
            "ipproto": "tcp",
            "dstPort": "8883",
        },
        "ztp": {
            "protocol": "ip",
            "ipproto": "tcp",
            "dstPort": "8080",
        },
        "bum": {"protocol": "ip", "srcIp": "10.0.0.1", "dstIp": "224.0.1.1", "type": "ethernet"},
        "icmp": {
            "protocol": "ip",
            "ipproto": "icmpv1",
            "srcIp": "10.0.0.2",
            "dstIp": "10.0.0.1",
            "type": "ethernet",
        },
        "mac": {
            "protocol": "ip",
            "ipproto": "udp",
            "srcIp": f"20.0.{swp[3:]}.2",
            "dstIp": f"20.0.{swp[3:]}.1",
            "srcMac": "00:11:01:00:00:01",
            "dstMac": swp_mac,
            "type": "raw",
            "rate": "10",
            "frameSize": "256",
        },
    }
    await tgen_utils_setup_streams(
        tgen_dev,
        pytest._args.config_dir + f"/{dent}/tgen_tc_basic_config.ixncfg",
        streams,
    )
    await tgen_utils_start_traffic(tgen_dev)
    time.sleep(10)
    await tgen_utils_stop_traffic(tgen_dev)
    stats = await tgen_utils_get_traffic_stats(tgen_dev)
    # check for no packet loss

    # - install iptables rules in filter table at FORWARD stage
    #  to drop the packet matching SIP and DIP
    #  - iptables -t filter -A FORWARD -i swp1 -s SIP -d DIP -j DROP
    iptable_rules = {}
    for swp in swp_tgen_ports:
        swp_info = {}
        await tgen_utils_get_swp_info(dent_dev, swp, swp_info)
        sip = ".".join(swp_info["ip"][:-1] + [str(int(swp[3:]) * 2)])
        iptable_rules[swp] = [
            {
                "table": "filter",
                "chain": "FORWARD",
                "in-interface": swp,
                "source": sip,
                "protocol": "tcp",
                "dport": "179",
                "target": "ACCEPT",
            },
            {
                "table": "filter",
                "chain": "FORWARD",
                "in-interface": swp,
                "protocol": "tcp",
                "dport": "179",
                "target": "DROP",
            },
            {
                "table": "filter",
                "chain": "FORWARD",
                "in-interface": swp,
                "source": sip,
                "protocol": "tcp",
                "dport": "22",
                "target": "ACCEPT",
            },
            {
                "table": "filter",
                "chain": "FORWARD",
                "in-interface": swp,
                "protocol": "tcp",
                "dport": "22",
                "target": "DROP",
            },
            # this is for check vlan(100) only packets
            {
                "table": "filter",
                "chain": "FORWARD",
                "in-interface": swp,
                # "source": sip,
                "protocol": "tcp",
                "dport": "443",
                "target": 'ACCEPT -m comment --comment "TC:--vlan-tag TC:100"',
            },
            {
                "table": "filter",
                "chain": "FORWARD",
                "in-interface": swp,
                "source": sip,
                "protocol": "tcp",
                "dport": "443",
                "target": "ACCEPT",
            },
            {
                "table": "filter",
                "chain": "FORWARD",
                "in-interface": swp,
                "protocol": "tcp",
                "dport": "443",
                "target": "DROP",
            },
            {
                "table": "filter",
                "chain": "FORWARD",
                "in-interface": swp,
                "source": sip,
                "protocol": "udp",
                "dport": "53",
                "target": "ACCEPT",
            },
            {
                "table": "filter",
                "chain": "FORWARD",
                "in-interface": swp,
                "protocol": "udp",
                "dport": "53",
                "target": "DROP",
            },
            {
                "table": "filter",
                "chain": "FORWARD",
                "in-interface": swp,
                "source": sip,
                "protocol": "udp",
                "dport": "123",
                "target": "ACCEPT",
            },
            {
                "table": "filter",
                "chain": "FORWARD",
                "in-interface": swp,
                "protocol": "udp",
                "dport": "123",
                "target": "DROP",
            },
            {
                "table": "filter",
                "chain": "FORWARD",
                "in-interface": swp,
                "source": sip,
                "protocol": "udp",
                "sport": "67",
                "dport": "68",
                "target": "ACCEPT",
            },
            {
                "table": "filter",
                "chain": "FORWARD",
                "in-interface": swp,
                "protocol": "udp",
                "sport": "67",
                "dport": "68",
                "target": "DROP",
            },
            {
                "table": "filter",
                "chain": "FORWARD",
                "in-interface": swp,
                "source": sip,
                "protocol": "tcp",
                "dport": "8080",
                "target": "ACCEPT",
            },
            {
                "table": "filter",
                "chain": "FORWARD",
                "in-interface": swp,
                "protocol": "tcp",
                "dport": "8080",
                "target": "DROP",
            },
            {
                "table": "filter",
                "chain": "FORWARD",
                "in-interface": swp,
                "destination": "224.0.1.0/24",
                "target": "DROP",
            },
            {
                "table": "filter",
                "chain": "FORWARD",
                "in-interface": swp,
                "protocol": "icmp",
                "target": "DROP",
            },
            {
                "table": "filter",
                "chain": "INPUT",
                "in-interface": swp,
                "protocol": "udp",
                "mac-source": "00:10:00:00:00:01",
                "target": 'LOG --log-prefix " MAC Rule: INPUT-RULE#0 "',
            },
            {
                "table": "filter",
                "chain": "FORWARD",
                "in-interface": swp,
                "target": "ACCEPT",
            },
        ]
        dent_dev.applog.info(f"Adding iptable rule for {swp}")
        out = await IpTables.append(input_data=[{dent: iptable_rules[swp]}])
        dent_dev.applog.info(out)
    # out = await IpTables.list(input_data=[{dent: [{"table": "filter", "chain": "FORWARD",}]}])
    # dent_dev.applog.info(out)

    await tgen_utils_clear_traffic_stats(tgen_dev)
    await tgen_utils_start_traffic(tgen_dev)
    # - check the traffic stats
    #  - there shouldnt be any loss
    time.sleep(10)
    await tgen_utils_stop_traffic(tgen_dev)
    stats = await tgen_utils_get_traffic_stats(tgen_dev)
    # TODO no drop should be seen

    # perform the rule translation
    await tcutil_iptable_to_tc(dent_dev, swp_tgen_ports, iptable_rules)
    await tgen_utils_clear_traffic_stats(tgen_dev)
    await tgen_utils_start_traffic(tgen_dev)
    # - check the traffic stats
    #  -- all the packets matching the SIP and DIP should be dropped.
    time.sleep(30)
    await tgen_utils_stop_traffic(tgen_dev)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    # TODO verify stats should drop all packets now.
    swp_tc_rules = {}
    await tcutil_get_tc_rule_stats(dent_dev, swp_tgen_ports, swp_tc_rules)

    ## verify the rules stats
    # for swp, data in swp_tc_rules.items():
    #    for r in data[1:]:
    #        assert r["options"]["actions"][0]["stats"]["hw_packets"], f"Rules not hit on {swp} {r}"
    swp_iptables_rules = {}
    await tcutil_get_iptables_rule_stats(dent_dev, swp_iptables_rules)

    # end of Test
    await tgen_utils_stop_protocols(tgen_dev)
    # cleanup
    await tcutil_cleanup_tc_rules(dent_dev, swp_tgen_ports, swp_tc_rules)
    out = await IpTables.flush(
        input_data=[
            {
                dent: [
                    {
                        "table": "filter",
                    }
                ]
            }
        ]
    )
    dent_dev.applog.info(out)
