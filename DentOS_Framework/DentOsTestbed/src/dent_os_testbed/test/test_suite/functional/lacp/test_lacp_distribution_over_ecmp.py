import asyncio
from math import isclose
import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.ip.ip_route import IpRoute
from dent_os_testbed.lib.ip.ip_neighbor import IpNeighbor


from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_get_swp_info,
)

pytestmark = [pytest.mark.suite_functional_lacp,
              pytest.mark.asyncio,
              pytest.mark.usefixtures('cleanup_tgen', 'cleanup_bonds', 'cleanup_bridges',
                                      'enable_ipv4_forwarding')]


async def test_lacp_ecmp_distribution_over_lag(testbed):
    """
    Test Name: LACP routing
    Test Suite: suite_functional_lacp
    Test Overview: Test ecmp distribution over lacp
    Test Procedure:
    1. Enable IPv4 forwarding
    2. Create 3 bonds
    3. Enslave
        DUT port <==> tgen port 1 to bond 1
        DUT port <==>  tgen port 2 to bond 2
        DUT port <==> tgen port 3 to bond 3
        DUT port <==>  tgen port 4 to bond 3
    4. Set link up on all participant ports
    5. Configure ip addresses in each LAG and configure route 10.1.1.0/24 via 2 bonds
    6. Setup one stream with destination IP 10.1.1.1
    7. Transmit traffic
    8. Verify no traffic loss; traffic distribution
    """
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    device = dent_devices[0]
    dent = device.host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]
    bonds = [f'bond_{idx}' for idx in range(1, 4)]
    tgen_lag_1 = ('LAG_0', [tg_ports[0]])
    tgen_lag_2 = ('LAG_1', [tg_ports[1]])
    tgen_lag_3 = ('LAG_2', tg_ports[2:])
    rate = 10000
    tolerance = 0.10

    # 1. Enable IPv4 forwarding
    # 2. Create 3 bonds
    out = await IpLink.add(input_data=[{dent: [{'device': bond, 'type': 'bond', 'mode': '802.3ad'} for bond in bonds]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bond'

    out = await IpLink.set(input_data=[{dent: [{'device': bond, 'operstate': 'up'} for bond in bonds]}])
    assert out[0][dent]['rc'] == 0, 'Failed setting bond to state up'

    # 3. Enslave DUT port <==> tgen port 1 to bond 1
    # DUT port <==>  tgen port2 to bond 2
    # DUT port <==> tgen port 3 to bond 2
    # DUT port <==>  tgen port 4 to bond 3
    out = await IpLink.set(input_data=[
        {dent: [{'device': port, 'operstate': 'down'} for port in ports] +
               [{'device': ports[0], 'master': bonds[0]}] +
               [{'device': ports[1], 'master': bonds[1]}] +
               [{'device': port, 'master': bonds[2]} for port in ports[2:]] +
               [{'device': port, 'operstate': 'up'} for port in ports]
         }])
    assert out[0][dent]['rc'] == 0, 'Failed changing state of the interfaces'

    # 5. Configure ip addresses in each LAG and configure route 10.1.1.0/24 via bridge
    for id, bond in enumerate(bonds, start=1):
        out = await IpAddress.add(input_data=[{dent: [{'dev': bond, 'prefix': f'{id}.{id}.{id}.{id}/24'}]}])
        assert out[0][dent]['rc'] == 0, f'Failed adding IP address to {bond}'

    # Add static arp entries to bond_2 and bond_3
    out = await IpNeighbor.add(input_data=[
        {dent: [{'dev': 'bond_2', 'address': '2.2.2.3', 'lladdr': '00:AD:20:B2:A7:75'},
                {'dev': 'bond_3', 'address': '3.3.3.4', 'lladdr': '00:59:CD:1E:83:1B'}]
         }])
    assert out[0][dent]['rc'] == 0, 'Failed adding ip neighbor'

    out = await IpRoute.add(input_data=[{dent: [
        {'dst': '10.1.1.0/24', 'nexthop': [{'via': '2.2.2.3', 'weight': 1}, {'via': '3.3.3.4', 'weight': 1}]}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add ip route'

    # 6. Setup one stream with DIP 10.1.1.1
    dev_groups = tgen_utils_dev_groups_from_config((
        {'ixp': tgen_lag_1[0], 'ip': '1.1.1.2', 'gw': '1.1.1.1', 'plen': 24, 'lag_members': tgen_lag_1[1]},
        {'ixp': tgen_lag_2[0], 'ip': '2.2.2.3', 'gw': '2.2.2.1', 'plen': 24, 'lag_members': tgen_lag_2[1]},
        {'ixp': tgen_lag_3[0], 'ip': '3.3.3.4', 'gw': '3.3.3.1', 'plen': 24, 'lag_members': tgen_lag_3[1]}
    ))

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)
    swp_info = {}
    await tgen_utils_get_swp_info(device, bonds[0], swp_info)
    bond_1_mac = swp_info['mac']

    streams = {
        f'{tg_ports[0]} -> 10.1.1.1': {
            'type': 'raw',
            'ip_source': dev_groups[tgen_lag_1[0]][0]['name'],
            'ip_destination': dev_groups[tgen_lag_3[0]][0]['name'],
            'protocol': 'ip',
            'dstMac': bond_1_mac,
            'srcMac': 'aa:bb:cc:dd:ee:ff',
            'srcIp': '1.1.1.10',
            'dstIp': {'type': 'increment',
                      'start': '10.1.1.1',
                      'step':  '0.0.0.1',
                      'count': 100},
            'rate': rate
        }
    }
    # 7. Transmit traffic
    try:
        await tgen_utils_setup_streams(tgen_dev, None, streams)
    except AssertionError as e:
        if 'LAG' in str(e):
            pytest.skip(str(e))
        else:
            raise  # will re-raise the AssertionError
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(10)
    await tgen_utils_stop_traffic(tgen_dev)
    await asyncio.sleep(10)

    # 8. Verify no traffic loss; traffic distribution
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Port Statistics')
    tx_packets = sum([int(row['Frames Tx.']) for row in stats.Rows if row['Port Name'] in tgen_lag_1[1]])
    for row in stats.Rows:
        if row['Port Name'] not in tgen_lag_3[1]:
            continue
        err_msg = f'Expected packets  {row["Valid Frames Rx."]}, actual packets: {tx_packets / 4}'
        assert isclose(int(row['Valid Frames Rx.']), tx_packets / 4, rel_tol=tolerance), err_msg
    total_received = sum([int(row['Valid Frames Rx.']) for row in stats.Rows])
    assert isclose(total_received, tx_packets, rel_tol=tolerance),\
        f'Expected packets  {total_received}, actual packets: {tx_packets}'
