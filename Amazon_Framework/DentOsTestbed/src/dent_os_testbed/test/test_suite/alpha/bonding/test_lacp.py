# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import time

import pytest

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.utils.test_utils.bonding_utils import (
    bonding_get_interconnected_infra_devices,
    bonding_setup,
)
from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_create_devices_and_connect,
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_protocols,
    tgen_utils_stop_traffic,
)

pytestmark = pytest.mark.suite_bonding


@pytest.mark.asyncio
async def test_alpha_lab_bonding_lacp(testbed):
    """
    Test Name: test_alpha_lab_bonding_lacp
    Test Suite: suite_bonding
    Test Overview: test bond LACP
    Test Procedure:
    1. LACP bonded link
    2. Add LACP onto the bonded link between infra routers
    3. No issues in traffic passing through it
    """
    tgen_dev, infra_devices = await tgen_utils_get_dent_devices_with_tgen(
        testbed, [DeviceType.INFRA_SWITCH], 1
    )
    if not tgen_dev or not infra_devices:
        print("The testbed does not have enough dent with tgen connections")
        return

    # get the infra devices that are inter connected to each other.
    infra_devices = await bonding_get_interconnected_infra_devices(testbed, infra_devices)
    if not infra_devices:
        print("The testbed does not have enough infra devices with interconnected links")
        return

    await bonding_setup(infra_devices)

    # Enable LACP and check the traffic
    # ip link add bond0 type bond
    # ip link set bond0 type bond mode 802.3ad
    # ip link set swp47 down
    # ip link set swp47 master bond0
    # ip link set swp48 down
    # ip link set swp48 master bond0
    # ip link set bond0 up
    # cat /proc/net/bonding/bond0
    # MII Status: up  <<<<<<< this will show up
    for dd in infra_devices:
        for cmd in [
            "ip link del bond0 type bond || true",
            "ip link add bond0 type bond",
            "ip link set bond0 type bond mode 802.3ad",
        ]:
            rc, out = await dd.run_cmd(cmd, sudo=True)
            assert rc == 0, f"failed to run {cmd} rc {rc} out {out}"
        for dd2, links in dd.links_dict.items():
            if dd2 not in testbed.devices_dict:
                continue
            if testbed.devices_dict[dd2].type != DeviceType.INFRA_SWITCH:
                continue
            for swp in links[0]:
                for cmd in [
                    f"ip link set {swp} down",
                    f"ip link set {swp} master bond0",
                    f"ip link set {swp} up",
                ]:
                    rc, out = await dd.run_cmd(cmd, sudo=True)
                    dd.applog.info(f"Ran {cmd} with rc {rc} {out}")

        for cmd in [
            f"ip link set bond0 up",
            f"brctl addif bridge bond0",
            f"bridge vlan add dev bond0 vid 100",
        ]:
            rc, out = await dd.run_cmd(cmd, sudo=True)
            dd.applog.info(f"Ran {cmd} with rc {rc} {out}")

    for dd in infra_devices:
        cmd = "cat /proc/net/bonding/bond0"
        rc, out = await dd.run_cmd(cmd, sudo=True)
        dd.applog.info(f"Bond interface status {out}")

    devices_info = {}
    for dd in infra_devices:
        devices_info[dd.host_name] = [
            # 'count' is the number of endpoints
            {
                "vlan": 100,
                "name": "MGMT",
                "count": 1,
            },
        ]

    await tgen_utils_create_devices_and_connect(
        tgen_dev, infra_devices, devices_info, need_vlan=False
    )
    mgmt_src = []
    mgmt_dst = []
    for dd1 in infra_devices:
        for dd2 in infra_devices:
            if dd1 == dd2:
                continue
            for swp1 in tgen_dev.links_dict[dd1.host_name][1]:
                for swp2 in tgen_dev.links_dict[dd2.host_name][1]:
                    mgmt_src.append(f"{dd1.host_name}_MGMT_{swp1}")
                    mgmt_dst.append(f"{dd2.host_name}_MGMT_{swp2}")

    streams = {
        "tcp_ssh_mgmt_flow": {
            "ip_source": mgmt_src,
            "ip_destination": mgmt_dst,
            "protocol": "ip",
            "ipproto": "tcp",
            "dstPort": "22",
        },
    }
    await tgen_utils_setup_streams(
        tgen_dev,
        pytest._args.config_dir + f"/{tgen_dev.host_name}/tgen_static_trunk",
        streams,
        force_update=True,
    )

    await tgen_utils_start_traffic(tgen_dev)
    sleep_time = 60 * 2
    tgen_dev.applog.info(f"zzZZZZZ({sleep_time})s")
    time.sleep(sleep_time)
    # await tgen_utils_stop_traffic(tgen_dev)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")

    # TODO add verification here

    await tgen_utils_stop_protocols(tgen_dev)
    await bonding_setup(infra_devices, state="up")
