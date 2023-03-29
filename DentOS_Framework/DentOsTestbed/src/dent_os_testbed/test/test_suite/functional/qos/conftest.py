import pytest_asyncio
from math import isclose as is_close
from datetime import datetime

from dent_os_testbed.lib.dcb.dcb_app import DcbApp
from dent_os_testbed.lib.tc.tc_qdisc import TcQdisc

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_get_traffic_stats,
    tgen_utils_get_loss,
)

from dent_os_testbed.test.test_suite.functional.qos.constants import (
    RAW_DSCP,
    PCP,
    RX_PORT,
    TX_FRAMES,
    RX_BYTES,
    TRAFFIC_START,
    TRAFFIC_END,
)


@pytest_asyncio.fixture()
async def cleanup_dscp_prio(testbed):
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgen connections")
        return
    dent = dent_devices[0].host_name
    ports = tgen_dev.links_dict[dent][1]

    yield  # Run the test

    await DcbApp.flush(input_data=[{dent: [{"dev": port} for port in ports]}])


def dscp_to_raw(dscp):
    return f"{dscp << 2:02X}"


def raw_to_dscp(raw):
    return int(raw, base=16) >> 2


def bytes_to_mbit_per_s(bts, duration):
    return bts * 8.0 / 1024 / 1024 / duration


def get_traffic_duration(row):
    time_format = "%H:%M:%S.%f"
    start = datetime.strptime(row[TRAFFIC_START], time_format)
    end = datetime.strptime(row[TRAFFIC_END], time_format)
    return (end - start).total_seconds()


async def configure_dscp_map_and_verify(dent, dscp_prio_map):
    out = await DcbApp.add(input_data=[{dent: [
        {"dev": port,
         "dscp_prio": list(priomap.items())}
        for port, priomap in dscp_prio_map.items()
    ]}])
    assert out[0][dent]["rc"] == 0, "Failed to add dscp prio mapping"

    for port, priomap in dscp_prio_map.items():
        out = await DcbApp.show(input_data=[{dent: [
            {"dev": port, "options": "-j", "dscp_prio": True}
        ]}], parse_output=True)
        assert out[0][dent]["rc"] == 0, "Failed to get dscp prio mapping"

        configured = out[0][dent]["parsed_output"]["dscp_prio"]
        for dscp_exp, prio_exp in priomap.items():
            for dscp_conf, prio_conf in configured:
                if prio_exp == prio_conf and dscp_exp == dscp_conf:
                    break
            else:
                raise AssertionError(f"Expected dscp-prio mapping: {priomap}, but configured: {configured}")


async def configure_def_prio_and_verify(dent, ports, default_prio):
    out = await DcbApp.add(input_data=[{dent: [
        {"dev": port, "default_prio": [default_prio]} for port in ports
    ]}])
    assert out[0][dent]["rc"] == 0, "Failed to add dscp prio mapping"

    for port in ports:
        out = await DcbApp.show(input_data=[{dent: [
            {"dev": port, "options": "-j", "default_prio": True}
        ]}], parse_output=True)
        assert out[0][dent]["rc"] == 0, "Failed to get dscp prio mapping"

        configured = out[0][dent]["parsed_output"]["default_prio"]
        assert default_prio in configured, \
            f"Port {port} should have configured default priority {default_prio}"


async def get_qd_stats(dent, ports):
    """Returns tbf stats grouped by port and band"""
    out = await TcQdisc.show(input_data=[{dent: [{"options": "-j -s"}]}], parse_output=True)
    assert out[0][dent]["rc"] == 0, "Failed to get qdisc statistics"
    stats = {port: {} for port in ports}
    for qd in out[0][dent]["parsed_output"]:
        if qd["kind"] != "tbf" or qd["dev"] not in ports:
            continue
        band = int(qd["parent"].split(":")[1])
        stats[qd["dev"]][band] = {
            key: int(qd[key]) for key in ("bytes", "packets", "drops")
        }
    return stats


async def get_qd_stats_delta(dent, old_stats):
    """
    Returns the difference between current tbf stats (packets, bytes, drops)
    and provided tbf stats. New stats are grouped by port and band.
    """
    new_stats = await get_qd_stats(dent, old_stats.keys())
    for port in new_stats:
        for band in new_stats[port]:
            for key in ("bytes", "packets", "drops"):
                new_stats[port][band][key] -= old_stats[port][band][key]
    return new_stats


def get_tc_from_stats_row(row, dscp_prio_map=None, def_prio=0):
    """
    The traffic class of the packet is based on the packet`s pcp and dscp,
    trust mode of the device (L2 or L3), and if the device is in L3 trust mode
    the TC depends on the dscp-prio map.
    L2 mode (default):
      The TC only depends on VLAN tag PCP. IF the packet is untagged then it
      is assigned the default priority.
    L3 mode:
      The TC depends only on the dscp-prio map (even if the packets is tagged).
      If the packet`s dscp is not in the priomap then the packet is assigned
      the default priority.
    """
    if not dscp_prio_map:
        dscp_prio_map = {}
        trust_mode = "l2"
    else:
        trust_mode = "l3"

    if RAW_DSCP in row.Columns and row[RAW_DSCP] and trust_mode == "l3":
        dscp = raw_to_dscp(row[RAW_DSCP])
        if dscp not in dscp_prio_map:
            return def_prio
        else:
            return dscp_prio_map[dscp]
    elif PCP in row.Columns and row[PCP] and trust_mode == "l2":
        return int(row[PCP])
    return def_prio


async def verify_tgen_stats_per_port_per_tc(tgen_dev, qd_stats, tg_to_swp, dscp_prio_map=None,
                                            tg_stats=None, def_prio=0, num_of_tcs=8, tol=.10):
    """
    Verify that there are no losses.
    Verify that tbf stats are correct.
    """
    per_port_stats = {}
    if tg_stats is None:
        tg_stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")

    for row in tg_stats.Rows:
        loss = tgen_utils_get_loss(row)
        assert loss == 0, f"Expected loss: 0%, actual: {loss}%"

        tc = get_tc_from_stats_row(row, dscp_prio_map, def_prio)

        swp = tg_to_swp[row[RX_PORT]]
        if swp not in per_port_stats:
            per_port_stats[swp] = [{"bytes": 0, "packets": 0} for _ in range(num_of_tcs)]

        per_port_stats[swp][tc]["bytes"] += int(row[RX_BYTES])
        per_port_stats[swp][tc]["packets"] += int(row[TX_FRAMES])

    for port in qd_stats:
        for tc in range(num_of_tcs):
            band = num_of_tcs - tc
            qdisc = qd_stats[port][band]
            stats = per_port_stats[port][tc]
            for key in ("bytes", "packets"):
                assert is_close(qdisc[key], stats[key], rel_tol=tol), \
                    f"Expected qdisc {key} to be {stats[key]}, but got {qdisc[key]} ({tc = })"


async def configure_qdiscs_and_verify(dent, ports, rate, handle=10, quanta=None):
    num_of_bands = len(rate)
    config = [
        {"dev": port,
         "root": True,
         "kind": "ets",
         "bands": num_of_bands,
         "strict": num_of_bands,
         "handle": handle,
         "priomap": reversed(range(num_of_bands))}
        for port in ports
    ]
    if quanta is not None:
        for qd in config:
            if len(quanta) == num_of_bands:
                del qd["strict"]
            else:
                qd["strict"] -= len(quanta)
            qd["quanta"] = quanta
    out = await TcQdisc.add(input_data=[{dent: config}])
    assert out[0][dent]["rc"] == 0, "Failed to configure root qdisc"

    out = await TcQdisc.add(input_data=[{dent: [
        {"dev": port,
         "kind": "tbf",
         "parent": f"{handle}:{num_of_bands - prio}",
         "handle": handle + num_of_bands - prio,
         "rate": _rate,
         "burst": "1M",
         "limit": "1M"}
        for prio, _rate in enumerate(rate)
        for port in ports
    ]
    }])
    assert out[0][dent]["rc"] == 0, "Failed to configure leaf qdiscs"

    out = await TcQdisc.show(input_data=[{dent: [{"options": "-j"}]}], parse_output=True)
    assert out[0][dent]["rc"] == 0, "Failed to get qdiscs"
    assert all(qdisc.get("offloaded")
               for qdisc in out[0][dent]["parsed_output"]
               if qdisc["dev"] in ports), \
        "Parent and leaf qdiscs should be offloaded"
