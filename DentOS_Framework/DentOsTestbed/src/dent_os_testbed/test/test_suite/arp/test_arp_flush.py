import time

import pytest

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.lib.ip.ip_route import IpRoute
from dent_os_testbed.utils.test_utils.tb_utils import (
    tb_ping_device,
    tb_reload_nw_and_flush_firewall,
)
from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_connect_to_tgen,
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_protocols,
    tgen_utils_stop_traffic,
)

pytestmark = pytest.mark.suite_arp


async def check_ping_to_tgen_link(testbed, dev_groups, dent_dev):
    for peer in dent_dev.links_dict:
        # get the device from device name
        if dent_dev.host_name == peer or peer not in testbed.devices_dict:
            continue
        dev = testbed.devices_dict[peer]
        if (
            dev.type in [DeviceType.TRAFFIC_GENERATOR, DeviceType.INFRA_SWITCH]
            or not await dev.is_connected()
        ):
            continue
        for ep in dev_groups.values():
            ip = ep[0]['ip']
            out = await IpRoute.get(
                input_data=[{dev.host_name: [{'dst': f'{ip}', 'cmd_options': '-j'}]}]
            )
            dev.applog.info(f'Ran IpRoute.get {ip} out {out}')
            rc = await tb_ping_device(dev, f'{ip}', dump=True)
            if rc != 0:
                dev.applog.info(f'Failed to reach {ip} on {peer} {rc}')
                # assert 0, f"Failed to ping the tgen {ip} from {peer}"


@pytest.mark.asyncio
async def test_arp_flush_w_traffic(testbed):
    """
    Test Name: test_arp_flush_w_traffic
    Test Suite: suite_arp
    Test Overview: test ARP get learnt via VRRP.
    Test Procedure:
    1. setup dent switch with atleast two ixia ports on it
      1.1 get a dent switch
      1.2 configure the switch for h/w forwarding
    2. setup tgen
      2.1 get a tgen device
      2.2 connect to the ports
      2.3 setup traffic stream with a know SIP and DIP
    3. start the traffic
    4. ping the tgen from a switch thats is connected to tgen port dent switch
    5. clear arp in dent switch
    6. ping again to the tgen the ping should work
    7. stop the traffic
    """
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        print('The testbed does not have enough dent with tgen connections')
        return
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name

    # start from a clean state
    await tb_reload_nw_and_flush_firewall([dent_dev])

    dev_groups = await tgen_utils_connect_to_tgen(tgen_dev, dent_dev)
    streams = {
        'bgp': {
            'protocol': 'ip',
            'ipproto': 'tcp',
            'dstPort': '179',
        },
    }
    await tgen_utils_setup_streams(
        tgen_dev, pytest._args.config_dir + f'/{dent}/tgen_basic_config.ixncfg', streams
    )
    await tgen_utils_start_traffic(tgen_dev)
    # - check the traffic stats
    #  -- all the packets matching the SIP and DIP should be dropped.
    dent_dev.applog.info('zzzZZZ!! (10s)')
    time.sleep(10)
    await tgen_utils_stop_traffic(tgen_dev)
    await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')

    rc, out = await dent_dev.run_cmd('arp -n')
    dent_dev.applog.info(f'arp on {dent} rc {rc} out {out}')

    await check_ping_to_tgen_link(testbed, dev_groups, dent_dev)

    for _ in range(5):
        rc, out = await dent_dev.run_cmd('ip -s -s neig flush all')
        dent_dev.applog.info(f'Flushed the arp on {dent} rc {rc} out {out}')

    time.sleep(10)

    rc, out = await dent_dev.run_cmd('arp -n')
    dent_dev.applog.info(f'arp on {dent} rc {rc} out {out}')
    await check_ping_to_tgen_link(testbed, dev_groups, dent_dev)

    rc, out = await dent_dev.run_cmd('arp -n')
    dent_dev.applog.info(f'arp on {dent} rc {rc} out {out}')

    # end of Test
    await tgen_utils_stop_protocols(tgen_dev)
