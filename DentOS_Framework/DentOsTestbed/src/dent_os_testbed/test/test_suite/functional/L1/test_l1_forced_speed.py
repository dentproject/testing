import pytest
import asyncio

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ethtool.ethtool import Ethtool
from dent_os_testbed.lib.onlp.onlp_system_info import OnlpSystemInfo


from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_dev_groups_from_config,
    tgen_utils_traffic_generator_connect,
    tgen_utils_get_loss
)


pytestmark = [pytest.mark.suite_functional_l1,
              pytest.mark.asyncio,
              pytest.mark.usefixtures("cleanup_bridges", "cleanup_tgen")]


@pytest.mark.parametrize("speed , duplex",
                         [
                            # (10, "full"),
                            # (10, "half"),
                            # (100, "full"),
                            # (100, "half")
                            # (1000, "full"),
                            # (1000, "half"),
                            (10000, "full"),
                         ])
async def test_l1_forced_speed_10_full_duplex(testbed, speed, duplex):
    """
    Test Name: test_bridging_admin_state_down_up
    Test Suite: suite_functional_bridging
    Test Overview: Verify that bridge is not learning entries with bridge entity admin state down.
    Test Procedure:
    1. Retrieve tgen and dent device info
    2. Create bridge entity
    3. Enslave ports to the created bridge entity
    4. Set up port duplex, speed
    5. Verify port duplex and speed per setup
    6. Set up traffic according to duplex mode
    7. Send traffic to rx_ports
    8. Verify received traffic on ports is as expected
    9. Transmitted rate equals received rate (and matches them configuration)
    """

    # 1. Retrieve tgen and dent device info
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print.error("The testbed does not have enough dent with tgen connections")
        return
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    bridge = "br0"

    # Check dut product name. If it supports the speed parameter
    model = await OnlpSystemInfo.show(input_data=[{device_host_name: [{}]}], parse_output=True)
    switch = model[0][device_host_name]['parsed_output']['product_name']
    if "AS5114" not in switch and speed < 1000:
        pytest.skip(f"Can not run test in device {switch}  with the speed: {speed}")

    # Check that there are at least minimum 2 ports with the provided speed parameter
    speed_ports = {}
    for port in ports:
        out = await Ethtool.show(input_data=[{device_host_name: [{"devname": port}]}],  parse_output=True)
        supported_speeds = '{}baseT/{}' if "TP" in out[0][device_host_name]['parsed_output']["supported_ports"] else '{}baseSR/{}'
        if supported_speeds.format(speed, duplex.capitalize()) in out[0][device_host_name]['result']:
            speed_ports[port] = {"speed": speed,
                                 "duplex": duplex}
    assert len(speed_ports) > 2, f"Need 2 ports with the same speed of {speed}"

    # 2. Create bridge entity
    out = await IpLink.add(input_data=[{device_host_name: [{
        "device": bridge,
        "type": "bridge",
       }]
    }])
    assert out[0][device_host_name]["rc"] == 0, f"Failed creating bridge."

    await IpLink.set(input_data=[{device_host_name: [{"device": bridge, "operstate": "up"}]}])
    assert out[0][device_host_name]["rc"] == 0, f"Failed setting bridge to state UP."

    # 3. Enslave ports to the created bridge entity
    out = await IpLink.set(input_data=[{device_host_name: [{
        "device": port,
        "operstate": "up",
        "master": bridge
    } for port in ports]}])
    assert out[0][device_host_name]["rc"] == 0, f"Failed setting link to state UP."

    # 4. Set up port duplex, speed
    out = await Ethtool.set(input_data=[{device_host_name: [{
        "devname": port,
        "speed": 10000,
        "autoneg": "off",
        "duplex": "Full"} for port in ports]}])
    assert out[0][device_host_name]["rc"] == 0, f"Failed setting port duplex, speed."

    # 5. Verify port duplex and speed per setup
    for port in ports:
        out = await Ethtool.show(input_data=[{device_host_name: [{"devname": port}]}],  parse_output=True)
        print(out)
        # check if port supports the speed tested
        assert 10000 == int(out[0][device_host_name]['parsed_output']['speed'][:-4]), "Failed speed test"
        assert "Full" == out[0][device_host_name]['parsed_output']['duplex'], "Failed duplex test"

    # 6. Set up traffic according to duplex mode
    dev_groups = tgen_utils_dev_groups_from_config(
        [{"ixp": tg_ports[0], "ip": "100.1.1.2", "gw": "100.1.1.6", "plen": 24, },
         {"ixp": tg_ports[1], "ip": "100.1.1.3", "gw": "100.1.1.6", "plen": 24, },
         {"ixp": tg_ports[2], "ip": "100.1.1.4", "gw": "100.1.1.6", "plen": 24, },
         {"ixp": tg_ports[3], "ip": "100.1.1.5", "gw": "100.1.1.6", "plen": 24, }])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    # TODO Add support for hals duplex streams

    supported_speed_ports = [name for name in speed_ports.keys()]
    first_port_index = ports.index(supported_speed_ports[0])
    second_port_index = ports.index(supported_speed_ports[1])

    streams = {f"{tg_ports[first_port_index]} --> {tg_ports[second_port_index]}": {
        "type": "raw",
        "ip_source": dev_groups[tg_ports[first_port_index]][0]["name"],
        "ip_destination": dev_groups[tg_ports[second_port_index]][0]["name"],
        "srcMac": "02:00:00:00:00:01",
        "dstMac": "02:00:00:00:00:02",
        "protocol": "802.1Q",
       }}

    streams.update({f"{tg_ports[second_port_index]} --> {tg_ports[first_port_index]}": {
        "type": "raw",
        "ip_source": dev_groups[tg_ports[second_port_index]][0]["name"],
        "ip_destination": dev_groups[tg_ports[first_port_index]][0]["name"],
        "srcMac": "02:00:00:00:00:02",
        "dstMac": "02:00:00:00:00:01",
        "protocol": "802.1Q",
       }})

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    # 7. Send traffic to rx_ports.
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(1)
    await tgen_utils_stop_traffic(tgen_dev)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(5)
    await tgen_utils_stop_traffic(tgen_dev)

    # 8. Verify traffic.
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")

    for row in stats.Rows:
        assert tgen_utils_get_loss(row) == 0.000, f'No traffic for traffic item :\
        {row["Traffic Item"]} on port {row["Rx Port"]}'

    # 8. Transmitted rate equals received rate (and matches them configuration)
    # TODO add check here for port rate
