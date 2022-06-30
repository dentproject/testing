import time
from itertools import islice

import pytest

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.lib.bridge.bridge_link import BridgeLink
from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.utils.test_utils.tb_utils import tb_reload_nw_and_flush_firewall
from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_create_devices_and_connect,
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_protocols,
    tgen_utils_stop_traffic,
)

pytestmark = pytest.mark.suite_vlan_port_isolation


@pytest.mark.asyncio
async def test_dentv2_vlan_port_isolation_max_scale(testbed):
    """
    Test Name: test_dentv2_vlan_port_isolation_max_scale
    Test Suite: suite_vlan_port_isolation
    Test Overview: test vlan port isolation with max vlans
    Test Procedure:
    1. configure maximum advertized vlan in a isolated bridge
    2. send traffic among them
    """
    max_vlan_count = 4094
    tgen_dev, infra_devices = await tgen_utils_get_dent_devices_with_tgen(
        testbed, [DeviceType.INFRA_SWITCH], 2
    )
    if not tgen_dev or not infra_devices:
        print("The testbed does not have enough dent with tgen connections")
        return
    await tb_reload_nw_and_flush_firewall(infra_devices)
    devices_info = {}
    # TODO Currently creating devices with ixia fails because there is no ip with vlans, need to find a fix
    for dd in infra_devices:
        devices_info[dd.host_name] = [
            # 'count' is the number of endpoints
            {
                "vlan": 100,
                "name": "MGMT",
                "count": 1,
            },
        ]

    mgmt_src = []
    mgmt_dst = []
    for dd in infra_devices:
        # Create bridge br0 and put tgen ports on it
        await IpLink.delete(input_data=[{dd.host_name: [{"device": "bridge"}]}])
        await IpLink.delete(input_data=[{dd.host_name: [{"device": "br0"}]}])
        out = await IpLink.add(
            input_data=[{dd.host_name: [{"device": "br0", "type": "bridge", "vlan_filtering": 1}]}]
        )
        assert out[0][dd.host_name]["rc"] == 0, out
        out = await IpLink.set(input_data=[{dd.host_name: [{"device": "br0", "operstate": "up"}]}])
        assert out[0][dd.host_name]["rc"] == 0, out
        for swp in tgen_dev.links_dict[dd.host_name][1]:
            mgmt_src.append(f"{dd.host_name}_MGMT_{swp}")
            mgmt_dst.append(f"{dd.host_name}_MGMT_{swp}")
            await IpLink.set(input_data=[{dd.host_name: [{"device": swp, "nomaster": ""}]}])
            out = await IpLink.set(input_data=[{dd.host_name: [{"device": swp, "master": "br0"}]}])
            assert out[0][dd.host_name]["rc"] == 0, out
            await BridgeLink.set(input_data=[{dd.host_name: [{"device": swp, "isolated": True}]}])
            for i in range(max_vlan_count):
                out = await BridgeVlan.add(
                    input_data=[
                        {
                            dd.host_name: [
                                {"device": swp, "vid": i + 1, "pvid": "", "untagged": True}
                            ]
                        }
                    ]
                )
    ep_src = list(map(lambda x: f"{x.split('_')[0]}:{x.split('_')[2]}", mgmt_src))
    ep_dst = list(map(lambda x: f"{x.split('_')[0]}:{x.split('_')[2]}", mgmt_dst))
    streams = {}
    for i in range(max_vlan_count):  # vlan id = i+1
        streams[f"tcp_ssh_vlan{i+1}_flow"] = {
            "type": "raw",
            "srcIp": "20.0.0.1",
            "dstIp": "10.0.0.1",
            "vlanID": f"{i+1}",
            # "ep_source": ep_src,
            # "ep_destination": ep_dst,
            "protocol": "802.1Q",
            "ipproto": "tcp",
            "dstPort": "22",
        }

    for streams_chunk in chunks(streams, 110):
        await tgen_utils_create_devices_and_connect(
            tgen_dev, infra_devices, devices_info, need_vlan=True
        )
        await tgen_utils_setup_streams(
            tgen_dev,
            pytest._args.config_dir + f"/{tgen_dev.host_name}/tgen_port_isolation_max_scale",
            streams_chunk,
            force_update=True,
        )

        await tgen_utils_start_traffic(tgen_dev)
        sleep_time = 60 * 2
        tgen_dev.applog.info(f"zzZZZZZ({sleep_time})s")
        time.sleep(sleep_time)
        # await tgen_utils_stop_traffic(tgen_dev)
        stats = await tgen_utils_get_traffic_stats(tgen_dev, "Traffic Item Statistics")

        # Traffic Verification
        for row in stats.Rows:
            assert float(row["Loss %"]) == 100.000, f'Failed>Loss percent: {row["Loss %"]}'

        await tgen_utils_stop_protocols(tgen_dev)


@pytest.mark.asyncio
async def test_dentv2_vlan_port_isolation_max_perf(testbed):
    """
    Test Name: test_dentv2_vlan_port_isolation_max_perf
    Test Suite: suite_vlan_port_isolation
    Test Overview: test vlan port isolation with max performance
    Test Procedure:
    1. Set the ports to isolated mode and measure time it takes to take effect
    """

    tgen_dev, infra_devices = await tgen_utils_get_dent_devices_with_tgen(
        testbed, [DeviceType.INFRA_SWITCH], 1
    )
    if not tgen_dev or not infra_devices:
        print("The testbed does not have enough dent with tgen connections")
        return
    await tb_reload_nw_and_flush_firewall(infra_devices)
    # Measure time for isolated flag to take effect
    for dd in infra_devices:
        for swp in tgen_dev.links_dict[dd.host_name][1]:
            starttime = time.time()
            await BridgeLink.set(input_data=[{dd.host_name: [{"device": swp, "isolated": True}]}])
            endtime = time.time()
            tgen_dev.applog.info(
                f"Time to set isolated flag for {swp} on {dd.host_name}: {endtime-starttime}s"
            )


def chunks(data, SIZE=256):
    it = iter(data)
    for i in range(0, len(data), SIZE):
        yield {k: data[k] for k in islice(it, SIZE)}
