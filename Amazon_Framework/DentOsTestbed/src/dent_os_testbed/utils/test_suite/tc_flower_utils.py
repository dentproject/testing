import json

from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.iptables.ip_tables import IpTables
from dent_os_testbed.utils.test_suite.tgen_utils import tgen_utils_get_swp_info


async def tcutil_iptable_to_tc(dent_dev, swp_tgen_ports, iptable_rules):
    # - run the tc persistency  tools
    #  - iptables-save -t filter  > /tmp/iptables.rules
    #  - iptables-unroll /tmp/iptables.rules /tmp/iptables-unrolled.rules FORWARD
    #  - iptables-scoreboard /tmp/iptables-unrolled.rules /tmp/iptables-scoreboarded.rules FORWARD swp+
    #  - tc-flower-load --scoreboard  --shared-block /tmp/iptables-scoreboarded.rules FORWARD swp+
    #  - delete the rules from iptables
    ENVROOT = "/sputnik/env/IhmDentTcFlower/"
    cmds = [
        f"iptables-save -t filter  > /tmp/iptables.rules",
        f"{ENVROOT}/bin/execute_in_env  {ENVROOT}/bin/iptables-unroll --multi-interface --extended /tmp/iptables.rules /tmp/iptables-unrolled.rules FORWARD",
        f"{ENVROOT}/bin/execute_in_env  {ENVROOT}/bin/iptables-scoreboard /tmp/iptables-unrolled.rules /tmp/iptables-scoreboarded.rules FORWARD swp+",
        f"{ENVROOT}/bin/execute_in_env  {ENVROOT}/bin/tc-flower-load --offload --port-unroll 5 --scoreboard  --shared-block  --hack-vlan-arp --log-ignore --continue-suppress /tmp/iptables-scoreboarded.rules FORWARD swp+",
    ]
    dent_dev.files_to_collect.append("/tmp/iptables.rules")
    dent_dev.files_to_collect.append("/tmp/iptables-unrolled.rules")
    dent_dev.files_to_collect.append("/tmp/iptables-scoreboarded.rules")
    for cmd in cmds:
        dent_dev.applog.info(f"Running command {cmd}")
        try:
            rc, out = await dent_dev.run_cmd(cmd, sudo=True)
            assert rc == 0, f"Failed to run {cmd} output {out}"
            dent_dev.applog.info(out)
        except Exception as e:
            dent_dev.applog.info(str(e))
            raise e

    ## delete the IP rules.
    dent_dev.applog.info("Deleting iptable rule for FORWARD")
    out = await IpTables.flush(
        input_data=[
            {
                dent_dev.host_name: [
                    {
                        "table": "filter",
                        "chain": "FORWARD",
                    }
                ]
            }
        ]
    )
    dent_dev.applog.info(out)


async def tcutil_get_tc_rule_stats(dent_dev, swp_tgen_ports, swp_tc_rules):
    dent = dent_dev.host_name
    for swp in swp_tgen_ports:
        cmd = f"tc -j -stats filter show dev {swp} ingress"
        dent_dev.applog.info(f"Running command {cmd}")
        try:
            rc, out = await dent_dev.run_cmd(cmd, sudo=True)
            assert rc == 0, f"Failed to run {cmd} output {out}"
            # dent_dev.applog.info(out)
            tc_rules = json.loads(out)
            swp_tc_rules[swp] = []
            count = 1
            for rule in tc_rules:
                if "options" not in rule:
                    continue
                line = "{}. {} Pref {} protocol {} Key [ ".format(
                    count, swp, rule["pref"], rule["protocol"]
                )
                line += "indev {} ".format(rule["options"].get("indev", "swp+"))
                for k, v in rule["options"]["keys"].items():
                    line += f"{k}=={v},"
                line += "] Action ["
                for action in rule["options"]["actions"]:
                    line += "{} Pkt {} Bytes {} HW Pkt {} Bytes {}".format(
                        action["control_action"]["type"],
                        action["stats"].get("packets", 0),
                        action["stats"].get("bytes", 0),
                        action["stats"].get("hw_packets", 0),
                        action["stats"].get("hw_bytes", 0),
                    )
                line += "]"
                dent_dev.applog.info(line)
                swp_tc_rules[swp].append(rule)
                count += 1
        except Exception as e:
            dent_dev.applog.info(str(e))


async def tcutil_cleanup_tc_rules(dent_dev, swp_tgen_ports, swp_tc_rules):
    dent = dent_dev.host_name
    rc, out = await dent_dev.run_cmd("tc filter delete block 1", sudo=True)
    dent_dev.applog.info(f"{rc} {out}")


async def tcutil_tc_rules_to_tgen_streams(swp_tc_rules, streams, start, cnt):
    for swp, rules in swp_tc_rules.items():
        count = 0
        for rule in rules[start : start + cnt]:
            st = {
                "ep_source": [swp],
                "type": "ethernet",
                "srcIp": f"20.0.{swp[3:]}.2",
                "dstIp": f"20.0.{swp[3:]}.3",
                "rate": "10",
                "frameSize": "256",
            }
            st["type"] = "ethernetVlan" if rule["protocol"] == "802.1Q" else "ethernet"
            name = swp + "_"
            # this rule wont hit anyway
            if "indev" in rule["options"] and swp != rule["options"]["indev"]:
                continue
            for k, v in rule["options"]["keys"].items():
                if not isinstance(v, str) and not isinstance(v, int):
                    continue
                name += k + "_" + str(v) + "_"
                if k == "eth_type" and v == "ipv4":
                    st["protocol"] = "ip"
                if k == "ip_proto":
                    st["ipproto"] = v
                if k == "dst_ip":
                    st["dstIp"] = v.split("/")[0]
                    if "/" in v:
                        st["dstIp"] = st["dstIp"][:-1] + "1"
                if k == "src_ip":
                    st["srcIp"] = v.split("/")[0]
                    if "/" in v:
                        st["srcIp"] = st["srcIp"][:-1] + "1"
                if k == "dst_port":
                    st["dstPort"] = str(v)
                if k == "src_port":
                    st["srcPort"] = str(v)
                if k == "vlan_ethtype":
                    st["ethType"] = str(v)
                if k == "vlan_id":
                    st["vlanID"] = str(v)
            if name not in streams:
                count += 1
                if count > 128:
                    break
            streams[name] = st


async def tcutil_get_iptables_rule_stats(dent_dev, swp_iptables_rules):
    dent = dent_dev.host_name
    out = await IpTables.list(
        input_data=[
            {dent: [{"table": "filter", "chain": "INPUT", "cmd_options": "-n -v --line-numbers"}]}
        ],
        parse_output=True,
    )
    iptables_rules = out[0][dent]["parsed_output"]
    for chain, rules in iptables_rules.items():
        for r in rules:
            line = "{}. Key [".format(r["num"])
            for k, v in r["keys"].items():
                line += f"{k}=={v},"
                pass
            line += "] target {} ".format(r["target"])
            line += "Pkt {} Bytes {} ".format(r["packets"], r["bytes"])
            dent_dev.applog.info(line)
        swp_iptables_rules[chain] = rules


async def tcutil_iptables_rules_to_tgen_streams(
    dent_dev, swp_iptables_rules, chain, swp_tgen_ports, streams
):

    """
    - Get the Vlans on the interface
    - find a vlan that has a mac address
    """
    for rule in swp_iptables_rules[chain]:
        inp = rule["keys"]["in"].split(",")
        for swp in swp_tgen_ports:
            if swp not in inp and inp[0] != "swp+" and inp[0] != "*":
                continue
            swp_info = {}
            await tgen_utils_get_swp_info(dent_dev, swp, swp_info)
            swp_mac = swp_info["mac"]
            dev_gw = swp_info["ip"]
            dev_plen = swp_info["plen"]
            st = {
                "ep_source": [swp],
                "type": "raw",
                "srcMac": "00:10:00:00:00:01",
                "dstMac": swp_mac,
                "srcIp": ".".join(dev_gw[:-1] + [swp[3:]]),
                "dstIp": ".".join(dev_gw),
                "rate": "10",
                "frameSize": "256",
            }
            name = swp + "_"
            for k, v in rule["keys"].items():
                if k not in ["ipproto", "srcIp", "dstIp", "dstPort", "srcPort"]:
                    continue
                if v in ["0.0.0.0/0"]:
                    continue
                name += k + "_" + str(v) + "_"
                if "," in v:
                    v = v.split(",")[0]
                if "/" in v:
                    v = v.split("/")[0]
                    v = v[:-1] + "1"
                if v == "icmp":
                    v = "icmpv1"
                st[k] = v
            if name in streams:
                name += "1"
            streams[name] = st
            dent_dev.applog.info(f"Adding Stream {name} with keys {st.keys()}")
