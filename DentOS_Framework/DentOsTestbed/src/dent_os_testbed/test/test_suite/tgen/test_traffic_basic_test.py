import time

import pytest

from dent_os_testbed.lib.iptables.ip_tables import IpTables
from dent_os_testbed.utils.test_utils.tb_utils import tb_reload_nw_and_flush_firewall
from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_connect_to_tgen,
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_get_loss,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_protocols,
    tgen_utils_stop_traffic,
)

pytestmark = pytest.mark.suite_traffic


@pytest.mark.asyncio
async def test_basic_tgen_w_traffic(testbed):
    """
    Test Name: test_basic_tgen_w_traffic
    Test Suite: suite_traffic
    Test Overview: Test traffic on a single device with two tgen ports
    Test Procedure:
    1. setup dent switch
      - get a dent switch
      - configure the switch for h/w forwarding
    2. setup tgen
      - get a tgen device
      - connect to the ports
      - setup traffic stream with a know SIP and DIP
    3. start the traffic
    4. check the traffic stats
      - there shouldnt be any loss
    5. stop the traffic
    """
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgen connections")
        return
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    swp_tgen_ports = tgen_dev.links_dict[dent][1]

    # start from a clean state
    await tb_reload_nw_and_flush_firewall([dent_dev])

    await tgen_utils_connect_to_tgen(tgen_dev, dent_dev)
    streams = {
        "bgp": {
            "protocol": "ip",
            "ipproto": "tcp",
            "dstPort": "179",
        },
    }
    await tgen_utils_setup_streams(
        tgen_dev, pytest._args.config_dir + f"/{dent}/tgen_basic_config.ixncfg", streams
    )
    await tgen_utils_start_traffic(tgen_dev)
    # - check the traffic stats
    #  -- all the packets matching the SIP and DIP should be dropped.
    dent_dev.applog.info("zzzZZZ!! (20s)")
    time.sleep(20)
    await tgen_utils_stop_traffic(tgen_dev)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    # Traffic Verification
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) != 100.000, f'Failed>Loss percent: {row["Loss %"]}'

    # end of Test
    await tgen_utils_stop_protocols(tgen_dev)
