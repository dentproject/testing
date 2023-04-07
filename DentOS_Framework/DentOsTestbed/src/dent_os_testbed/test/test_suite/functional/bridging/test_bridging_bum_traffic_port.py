import re
import pytest
import asyncio

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.test.test_suite.functional.bridging.bridging_packet_types import get_streams

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_get_loss,
)

from dent_os_testbed.utils.test_utils.tb_utils import (
    tb_device_tcpdump
)

pytestmark = [
    pytest.mark.suite_functional_bridging,
    pytest.mark.asyncio,
    pytest.mark.usefixtures('cleanup_bridges', 'cleanup_tgen', 'cleanup_ip_addrs')
]


async def test_bridging_bum_traffic_port_with_rif(testbed):
    """
    Test Name: test_bridging_bum_traffic_port_with_rif
    Test Suite: suite_functional_bridging
    Test Overview: Verify forwarding/drop/trap of different broadcast, unknown-unicast
                   and multicast traffic L2, IPv4 packet types.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1. Init ports.
    2. Configure IP addresses on ports.
    3. Set entities swp1, swp2, swp3, swp4 UP state.
    4. Get self MAC address on ingress port swp1.
    5. Start tcpdump capture on DUT ingress port.
    6. Send different types of packets from source TG.
    7. Analyze counters: a) TX vs RX counters according to expected values;
                         b) Trapped packets to CPU.
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        print('The testbed does not have enough dent with tgen connections')
        return
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 10
    prefix = '100.1.1.253'

    out = await IpAddress.add(input_data=[{device_host_name: [
        {'dev': ports[0], 'prefix': f'{prefix}/24'},
        {'dev': ports[1], 'prefix': '101.1.1.253/24'}]}])
    assert out[0][device_host_name]['rc'] == 0, f'Failed to add IP address to ports.\n{out}'

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': port, 'operstate': 'up'} for port in ports]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that entities set to 'UP' state.\n{out}"

    out = await IpLink.show(input_data=[{device_host_name: [{'device': ports[0], 'cmd_options': '-j'}]}],
                            parse_output=True)
    assert out[0][device_host_name]['rc'] == 0, f'Failed to display device attributes.\n{out}'

    dev_attributes = out[0][device_host_name]['parsed_output']
    self_mac = dev_attributes[0]['address']
    srcMac = '00:00:AA:00:00:01'

    address_map = (
        # swp port, tg port,    tg ip,     gw,        plen
        (ports[0], tg_ports[0], '1.1.1.2', '1.1.1.1', 24),
        (ports[1], tg_ports[1], '1.1.1.3', '1.1.1.1', 24)
    )

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': ip, 'gw': gw, 'plen': plen}
        for _, port, ip, gw, plen in address_map
    )

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    list_streams = get_streams(srcMac, self_mac, prefix, dev_groups, tg_ports)
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=list_streams)

    tcpdump = asyncio.create_task(tb_device_tcpdump(dent_dev, 'swp1', '-n', count_only=False, timeout=5, dump=True))

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Traffic Item Statistics')
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) == 100.000, \
            f"Verify that traffic from {row['Tx Port']} to {row['Rx Port']} not forwarded.\n{out}"

    await tcpdump
    print(f'TCPDUMP: packets={tcpdump.result()}')
    data = tcpdump.result()

    count_of_packets = re.findall(r'(\d+) packets (captured|received|dropped)', data)
    for count, type in count_of_packets:
        if type == 'received':
            assert int(count) > 0, 'Verify that packets are received by filter.\n'
        if type == 'captured' or type == 'dropped':
            assert int(count) == 0, 'Verify that packets are captured and dropped by kernel.\n'


async def test_bridging_bum_traffic_port_without_rif(testbed):
    """
    Test Name: test_bridging_bum_traffic_port_without_rif
    Test Suite: suite_functional_bridging
    Test Overview: Verify forwarding/drop/trap of different broadcast, unknown-unicast
                   and multicast traffic L2, IPv4 packet types.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1. Init ports.
    2. Set entities swp1, swp2, swp3, swp4 UP state.
    3. Get self MAC address on ingress port swp1.
    4. Start tcpdump capture on DUT ingress port.
    5. Send different types of packets from source TG.
    6. Analyze counters: a) TX vs RX counters according to expected values;
                         b) Trapped packets to CPU.
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        print('The testbed does not have enough dent with tgen connections')
        return
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 10
    prefix = '100.1.1.253'

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': port, 'operstate': 'up'} for port in ports]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that entities set to 'UP' state.\n{out}"

    out = await IpLink.show(input_data=[{device_host_name: [{'device': ports[0], 'cmd_options': '-j'}]}],
                            parse_output=True)
    assert out[0][device_host_name]['rc'] == 0, f'Failed to display device attributes.\n{out}'

    dev_attributes = out[0][device_host_name]['parsed_output']
    self_mac = dev_attributes[0]['address']
    srcMac = '00:00:AA:00:00:01'

    address_map = (
        # swp port, tg port,    tg ip,     gw,        plen
        (ports[0], tg_ports[0], '1.1.1.2', '1.1.1.1', 24),
        (ports[1], tg_ports[1], '1.1.1.3', '1.1.1.1', 24)
    )

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': ip, 'gw': gw, 'plen': plen}
        for _, port, ip, gw, plen in address_map
    )

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    list_streams = get_streams(srcMac, self_mac, prefix, dev_groups, tg_ports)
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=list_streams)

    tcpdump = asyncio.create_task(tb_device_tcpdump(dent_dev, 'swp1', '-n', count_only=False, timeout=5, dump=True))

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Traffic Item Statistics')
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) == 100.000, \
            f"Verify that traffic from {row['Tx Port']} to {row['Rx Port']} not forwarded.\n{out}"

    await tcpdump
    print(f'TCPDUMP: packets={tcpdump.result()}')
    data = tcpdump.result()

    count_of_packets = re.findall(r'(\d+) packets (captured|received|dropped)', data)
    for count, type in count_of_packets:
        if type == 'received':
            assert int(count) > 0, 'Verify that packets are received by filter.\n'
        if type == 'captured' or type == 'dropped':
            assert int(count) == 0, 'Verify that packets are captured and dropped by kernel.\n'
