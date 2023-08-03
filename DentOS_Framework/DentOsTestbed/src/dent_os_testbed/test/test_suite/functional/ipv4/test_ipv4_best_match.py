import asyncio
import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_route import IpRoute
from dent_os_testbed.lib.ip.ip_address import IpAddress

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_get_swp_info,
    tgen_utils_stop_traffic,
    tgen_utils_get_loss,
)

pytestmark = [
    pytest.mark.suite_functional_ipv4,
    pytest.mark.usefixtures('cleanup_ip_addrs', 'cleanup_tgen', 'enable_ipv4_forwarding'),
    pytest.mark.asyncio,
]


async def test_ipv4_bm_traffic_forwarding(testbed):
    """
    Test Name: test_ipv4_bm_traffic_forwarding
    Test Suite: suite_functional_ipv4
    Test Overview: Test best match traffic forwarding loopback interact
    Test Procedure:
    1. Set link up on all participant ports
    2. Configure ip addresses:
        - in first port connected to Ixia configure the same address&network
          with higher metric value than the address configured in the loopback
        - in second port connected to Ixia configure some random address
    3. Verify offload flag does not appear in the route of the first port connected to Ixia
    4. Prepare stream with SIP of second Ixia port neighbor and DIP of second Ixia port neighbor
    5. Transmit Traffic
    6. Verify traffic is not forwarded to first Ixia port neighbor
    7. Remove IP address from loopback interface
    8. Verify offload flag appear in the route of the first port connected to Ixia
    9. Verify traffic is forwarded to first Ixia port neighbor
    """
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0][:2]
    ports = tgen_dev.links_dict[dent][1][:2]
    traffic_duration = 10
    loopback = 'lo'

    port_mac = {}
    for port in ports:
        swp_info = {}
        await tgen_utils_get_swp_info(dent_dev, port, swp_info)
        port_mac[port] = swp_info['mac']

    address_map = (
        # swp port, tg port, swp ip, tg ip, plen, metric
        (ports[0], tg_ports[0], '20.1.1.1', '20.1.1.2', 24, 20),
        (ports[1], tg_ports[1], '192.168.1.1', '192.168.1.3', 24, None),
        (loopback, None, '20.1.1.1', None, 24, 10),
    )

    # 1. Set link up on all participant ports
    out = await IpLink.set(input_data=[{dent: [{'device': port, 'operstate': 'up'}
                                               for port in ports]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # 2. Configure ip addresses
    out = await IpAddress.add(input_data=[{dent: [
        {'dev': port, 'prefix': f'{ip}/{plen}'}
        for port, _, ip, _, plen, metric in address_map if not metric
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': ip, 'gw': gw, 'plen': plen}
        for _, port, gw, ip, plen, _ in address_map if port
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    out = await IpAddress.add(input_data=[{dent: [
        {'dev': port, 'prefix': f'{ip}/{plen}', 'metric': metric}
        for port, _, ip, _, plen, metric in address_map if metric
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    try:  # make sure that ip addr on loopback will be flushed

        # 3. Verify offload flag does not appear in the route of the first port connected to Ixia
        await asyncio.sleep(10)
        out = await IpRoute.show(input_data=[{dent: [
            {'cmd_options': '-j'}
        ]}], parse_output=True)
        assert out[0][dent]['rc'] == 0, 'Failed to get list of route entries'

        for ro in out[0][dent]['parsed_output']:
            if ro.get('dev', None) != ports[0]:
                continue
            assert not ro['flags'], 'Route should not have offload flag'

        # 4. Prepare stream with SIP of second Ixia port neighbor and DIP of first Ixia port neighbor
        streams = {
            f'{tg_ports[1]} -> {tg_ports[0]}': {
                'type': 'raw',
                'ip_source': dev_groups[tg_ports[1]][0]['name'],
                'ip_destination': dev_groups[tg_ports[0]][0]['name'],
                'protocol': 'ip',
                'srcIp': address_map[1][3],
                'dstIp': address_map[0][3],
                'srcMac': '02:00:00:00:00:01',
                'dstMac': port_mac[ports[1]],
                'rate': '1000',  # pps
            },
        }
        await tgen_utils_setup_streams(tgen_dev, None, streams)

        # 5. Transmit Traffic
        await tgen_utils_start_traffic(tgen_dev)
        await asyncio.sleep(traffic_duration)
        await tgen_utils_stop_traffic(tgen_dev)

        # 6. Verify traffic is not forwarded to first Ixia port neighbor
        await asyncio.sleep(5)
        stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Traffic Item Statistics')
        for row in stats.Rows:
            loss = tgen_utils_get_loss(row)
            assert loss == 100, f'Expected loss: 100%, actual: {loss}%'

    finally:
        # 7. Remove IP address from loopback interface
        out = await IpAddress.delete(input_data=[{dent: [
            {'dev': port, 'prefix': f'{ip}/{plen}'}
            for port, _, ip, _, plen, _ in address_map if port == loopback
        ]}])
        assert out[0][dent]['rc'] == 0, 'Failed to remove IP addr'

    # 8. Verify offload flag appear in the route of the first port connected to Ixia
    out = await IpRoute.show(input_data=[{dent: [
        {'cmd_options': '-j'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get list of route entries'

    for ro in out[0][dent]['parsed_output']:
        if ro.get('dev', None) != ports[0]:
            continue
        assert ro['flags'], 'Route should have offload flag'

    # 9. Verify traffic is forwarded to first Ixia port neighbor
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    await asyncio.sleep(5)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Traffic Item Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        assert loss == 0, f'Expected loss: 0%, actual: {loss}%'
