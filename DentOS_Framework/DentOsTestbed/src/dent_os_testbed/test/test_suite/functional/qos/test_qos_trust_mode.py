from datetime import datetime
import asyncio
import pytest
import random

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.dcb.dcb_app import DcbApp
from dent_os_testbed.lib.tc.tc_qdisc import TcQdisc
from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
)


pytestmark = [
    pytest.mark.suite_functional_qos,
    pytest.mark.usefixtures("cleanup_qdiscs", "cleanup_bridges",
                            "cleanup_dscp_prio", "cleanup_tgen"),
    pytest.mark.asyncio,
]


def bytes_to_mbit_per_s(bts, duration): return bts * 8.0 / 1024 / 1024 / duration
def dscp_to_raw(dscp): return f"{dscp << 2:02X}"
def raw_to_dscp(raw): return int(raw, base=16) >> 2


time_format = "%H:%M:%S.%f"
stats_table = {
    "ixia": {
        "title": "DSCP | PRIO | Rx Rate, Mbit | Expected, Mbit | Deviation, % | Duration, s",
        "row": "{:4} | {:4} | {:13.02f} | {:14.02f} | {:12.2f} | {:11.2f}",
    },
    "dut": {
        "title": "Band | PRIO | Statistics, bytes | Rate, Mbit | Expected, Mbit | Deviation, % | Duration, s",
        "row": "{:4} | {:4} | {:17} | {:10.02f} | {:14.02f} | {:12.1f} | {:11.2f}",
    },
}


@pytest.mark.parametrize("trust_mode", ["L2", "L3"])
@pytest.mark.parametrize("scheduler_type", ["sp", "wrr"])
async def test_qos_trust_mode(testbed, trust_mode, scheduler_type):
    """
    Test Name: test_qos_trust_mode
    Test Suite: suite_functional_qos
    Test Overview: Verify L2/L3 configuration is valid and shaper stats are as expected
    Test Procedure:
    1. Init interfaces
    2. Configure bridge and enslave TG ports to it
    3. Set all interfaces up
    4. Configure DSCP priority mapping or configure vlans on bridge members
    5. Configure ets qdisc on egress port: 8 bands - SP or WRR
    6. Configure tbf (shaper) qdisc for each band with max limit, burst and rate
    7. Configure 8 streams for each traffic class (dscp or pcp)
    8. Transmit traffic
    9. Verify scheduler statistics are matching the sent traffic
    """
    # 1. Init interfaces
    num_of_ports = 2
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], num_of_ports)
    if not tgen_dev or not dent_devices:
        pytest.skip("The testbed does not have enough dent with tgen connections")
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0][:num_of_ports]
    ports = tgen_dev.links_dict[dent][1][:num_of_ports]
    traffic_duration = 30  # sec
    num_of_bands = 8
    rate_mbit = 100  # Mbit/s
    tolerance = 10  # %
    bridge = "br0"
    handle = 10
    vlan = None

    # 2. Configure bridge and enslave TG ports to it
    out = await IpLink.add(input_data=[{dent: [
        {"name": bridge, "type": "bridge", "vlan_filtering": 1}
    ]}])
    assert out[0][dent]["rc"] == 0

    # 3. Set all interfaces up
    out = await IpLink.set(input_data=[{dent: [
        {"device": port, "operstate": "up", "master": bridge} for port in ports
    ] + [
        {"device": bridge, "operstate": "up"}
    ]}])
    assert out[0][dent]["rc"] == 0


    if trust_mode == "L3":
        # 4. Configure DSCP priority mapping
        dscp_prio_map = list(random.sample(range(64), num_of_bands))  # 8 random dscp values
        out = await DcbApp.add(input_data=[{dent: [
            {"dev": ports[0],
             "dscp_prio": [(dscp, prio) for prio, dscp in enumerate(dscp_prio_map)]}
        ]}])
        assert out[0][dent]["rc"] == 0
    else:
        # 4. Configure vlans on bridge members
        vlan = random.randint(2, 4095)
        out = await BridgeVlan.delete(input_data=[{dent: [
            {"device": port, "vid": 1} for port in ports
        ]}])
        assert out[0][dent]["rc"] == 0

        out = await BridgeVlan.add(input_data=[{dent: [
            {"device": port, "vid": vlan} for port in ports
        ]}])
        assert out[0][dent]["rc"] == 0

    # 5. Configure ets qdisc on egress port: 8 bands - SP or WRR
    root_qdisc = {
        "dev": ports[1],
        "root": True,
        "kind": "ets",
        "bands": num_of_bands,
        "strict": num_of_bands,
        "handle": handle,
        "priomap": reversed(range(num_of_bands)),
    }
    if scheduler_type == "wrr":
        del root_qdisc["strict"]
        root_qdisc["quanta"] = [6, 4, 3, 2, 1, 1, 1, 1]

    out = await TcQdisc.add(input_data=[{dent: [root_qdisc]}])
    assert out[0][dent]["rc"] == 0

    # 6. Configure tbf (shaper) qdisc for each band with max limit, burst and rate
    out = await TcQdisc.add(input_data=[{dent: [
        {"dev": ports[1],
         "kind": "tbf",
         "parent": f"{handle}:{num_of_bands - prio}",
         "handle": handle + num_of_bands - prio,
         "rate": f"{rate_mbit}Mbit",
         "burst": "1M",
         "limit": "1M"} for prio in range(num_of_bands)
    ]}])
    assert out[0][dent]["rc"] == 0

    out = await TcQdisc.show(input_data=[{dent: [
        {"dev": ports[1], "options": "-j"}
    ]}], parse_output=True)
    assert out[0][dent]["rc"] == 0
    assert all("offloaded" in qdisc and qdisc["offloaded"]
               for qdisc in out[0][dent]["parsed_output"]), \
        "Parent and leaf qdiscs should be offloaded"

    # 7. Configure 8 streams for each traffic class (dscp or pcp)
    tg0_ip = "1.1.1.1"
    tg1_ip = "1.1.1.2"
    plen = 24
    dev_groups = tgen_utils_dev_groups_from_config((
        {"ixp": tg_ports[0], "ip": tg0_ip, "gw": tg1_ip, "plen": plen, "vlan": vlan},
        {"ixp": tg_ports[1], "ip": tg1_ip, "gw": tg0_ip, "plen": plen, "vlan": vlan},
    ))
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    streams = {
        f"traffic": {
            "type": "ethernet",
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "protocol": "ip",
        }
    }
    if trust_mode == "L3":
        streams["traffic"]["dscp_ecn"] = {
            "type": "list",
            "list": [dscp_to_raw(dscp) for dscp in dscp_prio_map],
        }
    else:
        streams["traffic"]["type"] = "ethernetVlan"
        streams["traffic"]["vlanID"] = vlan
        streams["traffic"]["vlanPriority"] = {"type": "increment", "start": 0,
                                              "step": 1, "count": num_of_bands}

    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # 8. Transmit traffic
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # 9. Verify scheduler statistics are matching the sent traffic
    await asyncio.sleep(10)  # wait for ixia stats to update
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    status = []
    ixia_stats = {}
    tgen_dev.applog.info(stats_table["ixia"]["title"] if trust_mode == "L3" else
                         stats_table["ixia"]["title"].replace("DSCP", " PCP"))
    for row in stats.Rows:  # verify ixia stats
        if trust_mode == "L3":
            pcp_dscp = raw_to_dscp(row["IPv4 :Raw priority"])
            prio = dscp_prio_map.index(pcp_dscp)
        else:
            pcp_dscp = int(row["VLAN:VLAN Priority"])
            prio = pcp_dscp
        start = datetime.strptime(row["First TimeStamp"], time_format)
        end = datetime.strptime(row["Last TimeStamp"], time_format)
        actual_traffic_duration = (end - start).total_seconds()
        rx_bytes = int(row["Rx Bytes"])
        rx_mbit = bytes_to_mbit_per_s(rx_bytes, actual_traffic_duration)

        deviation = abs(1 - rx_mbit / rate_mbit) * 100
        status.append(deviation < tolerance)
        ixia_stats[prio] = (pcp_dscp, prio, rx_mbit, rate_mbit,
                            deviation, actual_traffic_duration)
    for _, vals in sorted(ixia_stats.items(), key=lambda x: x[0]):
        tgen_dev.applog.info(stats_table["ixia"]["row"].format(*vals))
    assert all(status), "Some streams were not transmitted as expected. See table above."

    out = await TcQdisc.show(input_data=[{dent: [
        {"dev": ports[1], "options": "-j -s"}
    ]}], parse_output=True)
    assert out[0][dent]["rc"] == 0

    status = []
    qd_stats = {}
    dent_dev.applog.info(stats_table["dut"]["title"])
    for qdisc in out[0][dent]["parsed_output"]:  # verify qdisc stats
        if qdisc["kind"] != "tbf":
            continue
        band = int(qdisc["parent"].split(":")[1])
        prio = num_of_bands - band
        actual_traffic_duration = ixia_stats[prio][-1]
        qd_bytes = int(qdisc["bytes"])
        qd_mbit = bytes_to_mbit_per_s(qd_bytes, actual_traffic_duration)

        deviation = abs(1 - qd_mbit / rate_mbit) * 100
        status.append(deviation < tolerance)
        qd_stats[prio] = (band, prio, qd_bytes, qd_mbit, rate_mbit,
                          deviation, actual_traffic_duration)
    for _, vals in sorted(qd_stats.items(), key=lambda x: x[0]):
        dent_dev.applog.info(stats_table["dut"]["row"].format(*vals))
    assert all(status), "Some streams were not transmitted as expected. See table above."
