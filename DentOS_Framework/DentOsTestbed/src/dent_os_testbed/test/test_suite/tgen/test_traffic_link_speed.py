import json
import os
import time

import pytest

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.lib.ethtool.ethtool import Ethtool
from dent_os_testbed.lib.interfaces.interface import Interface
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

pytestmark = pytest.mark.suite_traffic


@pytest.mark.asyncio
async def test_tgen_link_speed_change(testbed):
    """
    Test Name: test_tgen_link_speed_change
    Test Suite: suite_traffic
    Test Overview: Test the link speed with traffic on a tgen port
    Test Procedure:
    1. setup the traffic with link across the infra switches
    2. bring down all the links between the infra that are 10G links
    3. set the speec on the inter infra links to reduced speed
    4. send traffic at line rate and check the rate at recieving end.
    """
    tgen_dev, infra_devices = await tgen_utils_get_dent_devices_with_tgen(
        testbed, [DeviceType.INFRA_SWITCH], 1
    )
    if not tgen_dev or not infra_devices or len(infra_devices) < 2:
        testbed.applog.info(
            'The testbed does not have enough dent with tgen connections or infra devices with tgen connections'
        )
        return

    # pick two devices
    infra_devices = infra_devices[:2]

    # get the links between the two infra devices
    infra1 = infra_devices[0]
    infra2 = infra_devices[1]

    # there has to be intra infra links
    if infra2.host_name not in infra1.links_dict:
        tgen_dev.applog.info(
            f'The two infras {infra1.host_name} and {infra2.host_name} are not connected to each other.'
        )
        return

    await tb_reload_nw_and_flush_firewall(infra_devices)
    # for dd in infra_devices:
    #    # bring down the links that are 10g links
    #    for swp in range(49, 53):
    #        link = f"swp{swp}"
    #        out = await IpLink.set(
    #            input_data=[{dd.host_name: [{"device": link, "operstate": "down"}]}],
    #        )
    #        assert out[0][dd.host_name]["rc"] == 0, f"Failed to down the link {link} {out}"

    devices_info = {}
    for dd in infra_devices:
        devices_info[dd.host_name] = [
            # 'count' is the number of endpoints
            {
                'vlan': 100,
                'name': 'Mgmt',
                'count': 1,
            },
        ]

    await tgen_utils_create_devices_and_connect(
        tgen_dev, infra_devices, devices_info, need_vlan=False
    )

    src = []
    dst = []
    for dd in infra_devices:
        swp = tgen_dev.links_dict[dd.host_name][1][0]
        # just need one link on each infra
        src.append(f'{dd.host_name}_Mgmt_{swp}')
        dst.append(f'{dd.host_name}_Mgmt_{swp}')
    # infra to infra traffic streams
    streams = {
        'tcp_ssh_mgmt_flow': {
            'ip_source': src,
            'ip_destination': dst,
            'protocol': 'ip',
            'ipproto': 'tcp',
            'dstPort': '22',
            'rate': 40000,
            'frameSize': 512,
        },
    }

    await tgen_utils_setup_streams(
        tgen_dev,
        pytest._args.config_dir + f'/{tgen_dev.host_name}/tgen_vlan_streams',
        streams,
        force_update=True,
    )

    speeds = [1000, 100, 10]
    rx_rates = [3, 1, 0]  # in kpps
    duration = 30

    for speed, rate in zip(speeds, rx_rates):
        # set the speed on the inter infra link
        for swp in infra1.links_dict[infra2.host_name][0]:
            out = await Ethtool.set(
                input_data=[
                    {infra1.host_name: [{'devname': swp, 'speed': speed, 'autoneg': 'on'}]}
                ],
            )
            infra1.applog.info(out)

        await tgen_utils_start_traffic(tgen_dev)
        time.sleep(duration)
        await tgen_utils_stop_traffic(tgen_dev)
        stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
        # add verification logic here.
        for crow in stats.Rows:
            cti = crow['Traffic Item']
            pair = crow['Source/Dest Value Pair']
            rx_rate = float(crow['Rx Frames']) / duration
            tx_rate = float(crow['Tx Frames']) / duration
            tgen_dev.applog.info(
                f'CTI {cti} pair {pair} Rx Rate {rx_rate} pps Tx Rate {tx_rate} pps'
            )
            if int(rx_rate / 10000) != rate:
                assert 0, f'Rate does not match {rx_rate} {rate}'

    await tgen_utils_stop_protocols(tgen_dev)
    # bring back up the links
    # for dd in infra_devices:
    #    # bring down the links that are 10g links
    #    for swp in range(49, 53):
    #        link = f"swp{swp}"
    #        out = await IpLink.set(
    #            input_data=[{dd.host_name: [{"device": link, "operstate": "up"}]}],
    #        )
    #        assert out[0][dd.host_name]["rc"] == 0, f"Failed to up the link {link} {out}"
