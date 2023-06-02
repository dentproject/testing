import time
import pytest
import asyncio

from dent_os_testbed.lib.bridge.bridge_link import BridgeLink
from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_get_loss
)

from datetime import datetime

pytestmark = [
    pytest.mark.suite_functional_port_isolation,
    pytest.mark.asyncio,
    pytest.mark.usefixtures('cleanup_bridges', 'cleanup_tgen')
]


async def test_port_isolation_maximum_isolated_ports_on_bridge(testbed):
    """
    Test Name: test_port_isolation_maximum_isolated_ports_on_bridge
    Test Suite: suite_functional_port_isolation
    Test Overview: Verify that there is no limitation on the number of isolated ports
                   that can be defined on one bridge.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Verify the quantity of ports.
    2.  Init bridge entity br0.
    3.  Set ports swp1, swp2, swp3, swp4 master br0.
    4.  Set entities swp1, swp2, swp3, swp4 UP state.
    5.  Set bridge br0 admin state UP.
    6.  Verify the time it took for all ports to get up.
    7.  Set all bridge entities as isolated.
    8.  Set up the streams.
    9.  Transmit continues traffic by TG.
    10. Verify traffic sent from isolated ports that was not received on an isolated port.
    """

    bridge = 'br0'
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 15
    pps_value = 1000
    timeout = 30

    start_time = datetime.now()
    links_present = []
    rc, out = await dent_dev.run_cmd('ifconfig -a')
    assert rc == 0, "Failed to run the command 'ifconfig -a'."
    for port in ports:
        links_present.append(f'{port}:' in out)
    if not all(links_present):
        time.sleep(timeout)
        rc, out = await dent_dev.run_cmd('ifconfig -a')
        assert rc == 0, "Failed to run the command 'ifconfig -a'."
        for port in ports:
            links_present.append(f'{port}:' in out)
    assert all(links_present), 'Not all ports exist.'
    print(f'It took {datetime.now() - start_time} to verify ports presence.\n')

    out = await IpLink.add(
        input_data=[{device_host_name: [
            {'device': bridge, 'vlan_filtering': 1, 'type': 'bridge'}]}])
    err_msg = f"Verify that bridge created and vlan filtering set to 'ON'.\n{out}"
    assert out[0][device_host_name]['rc'] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': bridge, 'operstate': 'up'}]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that bridge set to 'UP' state.\n{out}"

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': port, 'master': bridge, 'operstate': 'up'} for port in ports]}])
    err_msg = f"Verify that bridge entities set to 'UP' state and links enslaved to bridge.\n{out}"
    assert out[0][device_host_name]['rc'] == 0, err_msg

    start_time = datetime.now()
    for _ in range(20):
        out = await IpLink.show(input_data=[{device_host_name: [{'cmd_options': '-j'}]}],
                                parse_output=True)
        assert out[0][device_host_name]['rc'] == 0, 'Failed to get links.'

        links = out[0][device_host_name]['parsed_output']
        links_up = []
        for port in ports:
            for link in links:
                if port in link['ifname']:
                    links_up.append(link['operstate'] == 'UP')
                    break
        if all(links_up):
            break
        time.sleep(timeout/6)
    else:
        assert all(links_up), "One of the ports, or even all of them, are not in the 'UP' state."
    print(f"It took {datetime.now() - start_time} to set entities to 'UP' state.\n")

    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {'device': port, 'isolated': True} for port in ports]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that all entities set to isolated state 'ON'.\n{out}"

    address_map = (
        # swp port, tg port,    tg ip,     gw,        plen
        (ports[0], tg_ports[0], '1.1.1.2', '1.1.1.1', 24),
        (ports[1], tg_ports[1], '1.1.1.3', '1.1.1.1', 24),
        (ports[2], tg_ports[2], '1.1.1.4', '1.1.1.1', 24),
        (ports[3], tg_ports[3], '1.1.1.5', '1.1.1.1', 24)
    )

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': ip, 'gw': gw, 'plen': plen}
        for _, port, ip, gw, plen in address_map
    )

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    """
    Set up the following streams:
    — stream_1 —  |  — stream_2 —  |  — stream_3 —
    swp1 -> swp2  |  swp1 -> swp3  |  swp1 -> swp4
    """

    streams = {
        f'stream_{dst}': {
            'ip_source': dev_groups[tg_ports[src]][0]['name'],
            'ip_destination': dev_groups[tg_ports[dst]][0]['name'],
            'srcMac': f'00:00:00:00:00:0{dst}',
            'dstMac': f'00:00:00:00:00:0{dst+1}',
            'frameSize': 64,
            'rate': pps_value,
            'protocol': '0x88a8',
            'type': 'raw'
        } for src, dst in ((0, 1), (0, 2), (0, 3))
    }

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)

    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) == 100.000, \
            f"Verify that traffic from {row['Tx Port']} to {row['Rx Port']} not forwarded.\n{out}"
