import asyncio
import pytest
import random
import copy

from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan
from dent_os_testbed.lib.tc.tc_filter import TcFilter
from dent_os_testbed.lib.tc.tc_qdisc import TcQdisc
from dent_os_testbed.lib.ip.ip_link import IpLink


from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
)
from dent_os_testbed.utils.test_utils.tc_flower_utils import (
    tcutil_generate_rule_with_random_selectors,
    tcutil_tc_rules_to_tgen_streams,
    tcutil_get_tc_stats_pref_map,
    tcutil_verify_tgen_stats,
    tcutil_verify_tc_stats,
)


pytestmark = [
    pytest.mark.suite_functional_acl,
    pytest.mark.usefixtures("cleanup_qdiscs", "cleanup_tgen", "cleanup_bridges"),
    pytest.mark.asyncio,
]


def get_rule_with_all_selectors(port, pref, action, vlan, is_block):
    rule = tcutil_generate_rule_with_random_selectors(
        port=port, pref=pref, want_mac=True, want_vlan=vlan != 0,
        want_ip=True, want_port=True, action=action, skip_sw=True,
    )
    if is_block:
        rule["block"] = rule.pop("dev")
    if vlan:
        rule["protocol"] = "802.1q"
        rule["filtertype"]["vlan_ethtype"] = "ip"
        rule["filtertype"]["vlan_id"] = vlan
    else:
        rule["protocol"] = "ip"
    return rule


def get_streams_that_do_not_match_rule(rule_matched_stream, list_of_selectors):
    def update_mac(mac):
        mac_list = mac.split(":")
        part = int(mac_list[-1], base=16)
        part += 1 if part < 250 else -1
        mac_list[-1] = f"{part:02x}"
        return ":".join(mac_list)

    def update_ip(ip):
        ip_list = ip.split(".")
        part = int(ip_list[-1])
        part += 1 if part < 250 else -1
        ip_list[-1] = str(part)
        return ".".join(ip_list)

    def update_int(number):
        n = int(number)
        return str(n + 1 if n < 4000 else n - 1)

    selector_map = {
        "src_mac":  ("srcMac",   update_mac),
        "dst_mac":  ("dstMac",   update_mac),
        "src_ip":   ("srcIp",    update_ip),
        "dst_ip":   ("dstIp",    update_ip),
        "src_port": ("srcPort",  update_int),
        "dst_port": ("dstPort",  update_int),
        "vlan_id":  ("vlanID",   update_int),
    }
    stream_name = next(iter(rule_matched_stream.keys()))
    unmatched_streams = {}

    for sel in list_of_selectors:
        if sel not in selector_map:
            continue
        field_name, update_func = selector_map[sel]
        stream = copy.copy(rule_matched_stream[stream_name])
        if field_name not in stream:
            continue
        stream[field_name] = update_func(stream[field_name])
        unmatched_streams[stream_name + f"_unmatch_{field_name}"] = stream

    return unmatched_streams


@pytest.mark.parametrize("action", ["pass", "drop", "trap"])
@pytest.mark.parametrize("use_tagged_traffic", ["tagged", "untagged"])
@pytest.mark.parametrize("qdisc_type", ["shared_block", "port"])
async def test_acl_all_selectors(testbed, action, use_tagged_traffic, qdisc_type):
    """
    Test Name: test_acl_all_selectors
    Test Suite: suite_functional_acl
    Test Overview: Check that all TC selectors are working correctly
    Test Procedure:
    1. Initiate test params
    2. Create bridge and set link up on it (vlan aware or vlan unaware)
    3. Enslave interfaces and set link up
    4. Add vlans to DUT ports
    5. Create ingress qdisc (port or shared block)
    6. Create rule-matched traffic
    7. Prepare streams that do not match the rule (one unmatched stream for each selector)
    9. Send Traffic from the first TG port
    10. Verify "pass" and "trap" traffic was forwarded, "drop" was dropped
    """
    # 1. Initiate test params
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip("The testbed does not have enough dent with tgen connections")
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0][:2]
    ports = tgen_dev.links_dict[dent][1][:2]
    port_with_rule = ports[0]

    use_shared_block = qdisc_type == "shared_block"
    is_vlan_aware = use_tagged_traffic == "tagged"

    vlan = random.randint(1, 4095) if is_vlan_aware else 0
    tc_stats_update_time = 5
    traffic_duration = 10
    rate_pps = 10_000
    pref = 49000
    block = 1
    bridge = "br0"
    list_of_selectors = ("src_mac", "dst_mac", "vlan_id",
                         "src_ip", "dst_ip", "src_port", "dst_port")
    name = port_with_rule if not use_shared_block else block

    # 2. Create bridge and set link up on it (vlan aware or vlan unaware)
    config = {"name": bridge, "type": "bridge"}
    if is_vlan_aware:
        config["vlan_filtering"] = 1
        config["vlan_default_pvid"] = 0
    out = await IpLink.add(input_data=[{dent: [config]}])
    assert out[0][dent]["rc"] == 0, "Failed to create bridge"

    # 3. Enslave interfaces and set link up
    out = await IpLink.set(input_data=[{dent: [
        {"device": port, "operstate": "up", "master": bridge} for port in ports
    ] + [
        {"device": bridge, "operstate": "up"}
    ]}])
    assert out[0][dent]["rc"] == 0, "Failed to set port state UP"

    # 4. Add vlans to DUT ports
    if is_vlan_aware:
        out = await BridgeVlan.add(input_data=[{dent: [
            {"device": port, "vid": vlan, "untagged": False} for port in ports
        ]}])
        assert out[0][dent]["rc"] == 0, "Failed to set port state UP"

    # 5. Create ingress qdisc (port or shared block)
    config = {"dev": port_with_rule, "ingress_block": block, "direction": "ingress"}
    if use_shared_block:
        tc_target = "block"
    else:
        del config["ingress_block"]
        tc_target = "dev"

    out = await TcQdisc.add(input_data=[{dent: [config]}])
    assert out[0][dent]["rc"] == 0, "Failed to create qdisc"

    # 6. Create rule-matched traffic
    tc_rule = get_rule_with_all_selectors(name, pref, action, vlan, use_shared_block)
    out = await TcFilter.add(input_data=[{dent: [tc_rule]}])
    assert out[0][dent]["rc"] == 0, "Failed to create tc rules"

    out = await TcFilter.show(input_data=[{dent: [
        {tc_target: name, "direction": "ingress", "pref": pref, "options": "-j"}
    ]}], parse_output=True)
    assert out[0][dent]["rc"] == 0, "Failed to get tc rule"

    streams = tcutil_tc_rules_to_tgen_streams(
        {port_with_rule: out[0][dent]["parsed_output"]},
        frame_rate_pps=rate_pps)

    # 7. Prepare streams that do not match the rule (one unmatched stream for each selector)
    rule_unmatched_streams = get_streams_that_do_not_match_rule(streams, list_of_selectors)
    streams.update(rule_unmatched_streams)

    dev_groups = tgen_utils_dev_groups_from_config(
        {"ixp": port, "ip": f"1.1.1.{idx}", "gw": "1.1.1.10",
         "plen": 24, "vlan": vlan if is_vlan_aware else None}
        for idx, port in enumerate(tg_ports, start=1)
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # 9. Send Traffic from the first TG port
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # 10. Verify "pass" and "trap" traffic was forwarded, "drop" was dropped
    ixia_stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")

    for row in ixia_stats.Rows:
        act = action
        if "unmatch" not in row["Traffic Item"]:  # there should be exactly 1 such traffic item
            tx_frames = int(row["Tx Frames"])
        else:  # traffic items that should not be matched by any tc rule
            act = "pass"
        # traffic item with a different vlan id should have 100% loss
        if is_vlan_aware and "unmatch_vlanID" in row["Traffic Item"]:
            act = "drop"
        await tcutil_verify_tgen_stats(tgen_dev, row, act, rate_pps)

    await asyncio.sleep(tc_stats_update_time)  # wait for tc stats to update
    tc_stats = await tcutil_get_tc_stats_pref_map(dent, name, use_shared_block)
    await tcutil_verify_tc_stats(dent_dev, tx_frames, tc_stats[pref])
