import pytest
import asyncio

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ethtool.ethtool import Ethtool

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_update_l1_config,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_get_loss
)

pytestmark = [pytest.mark.suite_functional_l1,
              pytest.mark.asyncio,
              pytest.mark.usefixtures("cleanup_bridges", "cleanup_tgen")]


async def test_l1_mixed_speed(testbed):
    """
    Test Name: test_l1_mixed_speed
    Test Suite: suite_functional_l1
    Test Overview: Verify traffic with mixed speed on ports
    Test Procedure:
    1. Init bridge entity br0.
    2. Enslave ports to bridge br0
    3. Configure dut ports:
        Port 1:
            speed -> 1000
            autoneg -> Off
            duplex -> full
        Port 2:
            speed -> 100
            autoneg -> on
            duplex -> half
        Port 3:
            speed -> 10
            autoneg -> Off
            duplex -> half
        Port 4:
            autoneg -> off
            advertise -> 0x004
    4. Send traffic from Port 1 with bits per second rate of 9_000_000
    5. Verify no packet loss occurred and all transmitted traffic received.
    """

    bridge = "br0"
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip("The testbed does not have enough dent with tgen connections")
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    timeout = 10

    # 1. Init bridge entity br0.
    out = await IpLink.add(input_data=[{device_host_name: [{"device": bridge, "type": "bridge"}]}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify that bridge created."

    out = await IpLink.set(input_data=[{device_host_name: [{"device": bridge, "operstate": "up"}]}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify that bridge set to 'UP' state."

    # 2. Enslave ports to bridge br0
    out = await IpLink.set(input_data=[{device_host_name: [
        {"device": port,
         "operstate": "up",
         "master": bridge} for port in ports]}])
    err_msg = f"Verify that bridge entities set to 'UP' state and links enslaved to bridge."
    assert out[0][device_host_name]["rc"] == 0, err_msg

    # 3. Configure dut ports
    out = await Ethtool.set(input_data=[{device_host_name: [
        {"devname": ports[0],
         "speed": 1000,
         "autoneg": "off",
         "duplex": "full"}]}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify port settings has been changed "

    out = await Ethtool.set(input_data=[{device_host_name: [{
        "devname": ports[1],
        "speed": 100,
        "autoneg": "on",
        "duplex": "half"}]}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify port settings has been changed "

    out = await Ethtool.set(input_data=[{device_host_name: [{
        "devname": ports[2],
        "speed": 10,
        "autoneg": "off",
        "duplex": "full"}]}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify port settings has been changed "

    out = await Ethtool.set(input_data=[{device_host_name: [{
        "devname": ports[3],
        "autoneg": "off",
        "advertise": "0x004"}]}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify port settings has been changed "

    dev_groups = tgen_utils_dev_groups_from_config(
        [{"ixp": tg_ports[0], "ip": "100.1.1.2", "gw": "100.1.1.6", "plen": 24},
         {"ixp": tg_ports[1], "ip": "100.1.1.3", "gw": "100.1.1.6", "plen": 24},
         {"ixp": tg_ports[2], "ip": "100.1.1.4", "gw": "100.1.1.6", "plen": 24},
         {"ixp": tg_ports[3], "ip": "100.1.1.5", "gw": "100.1.1.6", "plen": 24}])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    # Set autoneg on all connected IXIA ports
    await tgen_utils_update_l1_config(tgen_dev, tg_ports, speed=None, autoneg=True)
    await asyncio.sleep(timeout)

    # 4. Send traffic by TG with  bits per second rate of 9_000_000
    streams = {
        f"{tg_ports[0]} --> {tg_ports[1], tg_ports[2],tg_ports[3]}": {
            "type": "ethernet",
            "ep_source": ports[0],
            "ep_destination": ports[1:],
            "frame_rate_type": "bps_rate",
            "rate": 9000000
        }
    }

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(timeout)
    await tgen_utils_stop_traffic(tgen_dev)

    # 5. Verify no packet loss occurred and all transmitted traffic received.
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) == 0.000, \
            f"Verify that traffic from {row['Tx Port']} to {row['Rx Port']} forwarded."
