import asyncio
from math import isclose
import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.ip.ip_route import IpRoute
from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan

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
              pytest.mark.usefixtures('cleanup_vrfs', 'cleanup_tgen', 'cleanup_bonds',
                                      'cleanup_bridges', 'cleanup_vrf_table_ids',
                                      'cleanup_routes', 'enable_ipv4_forwarding')]


async def test_lacp_routing_over_lag_vrf_vlan_device(testbed):
    """
    Test Name: LACP routing
    Test Suite: suite_functional_lacp
    Test Overview: Test routing over vrf's
    Test Procedure:
    1. Create 3 bonds and 2 vrf tables
    2. Enslave
        DUT port <==> tgen port 1 to bond 1
        DUT port <==>  tgen port 2 to bond 2
        DUT port <==> tgen port 3 to bond 3
        DUT port <==>  tgen port 4 to bond 3
    3. Set link up on all participant ports
    4. Configure ip addresses in each LAG and configure route 10.1.1.0/24 via 2 vrf's
    5. Setup one stream with destination IP 10.1.1.1
    6. Transmit traffic
    7. Verify traffic received on active bond2 port in vrf0 and not received on vrf1
    """
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip(
            'The testbed does not have enough dent with tgen connections')
    device = dent_devices[0]
    dent = device.host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]
    bonds = [f'bond_{idx}' for idx in range(1, 4)]
    tgen_lag_1 = ('LAG_0', [tg_ports[0]])
    tgen_lag_2 = ('LAG_1', [tg_ports[1]])
    tgen_lag_3 = ('LAG_2', tg_ports[2:])
    vrf_1 = 'vrf0'
    vrf_2 = 'vrf1'
    vid = 10
    bridge = 'bridge_0'
    vlan_device = f'{bridge}.{vid}'
    rate = 10000

    # 1. Create 3 bonds and a bridge
    out = await IpLink.add(input_data=[{dent: [{
        'device': bridge,
        'type': 'bridge',
        'vlan_filtering': 1,
        'vlan_default_pvid': 10,
    }]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bridge'

    out = await IpLink.set(input_data=[{dent: [{'device': bridge, 'operstate': 'up'}]}])
    assert out[0][dent]['rc'] == 0, 'Failed setting bridge to state up'

    # Bridge to vlan id
    out = await BridgeVlan.add(input_data=[{dent: [{'device': bridge, 'vid': vid, 'self': True}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add vlan on device'

    out = await IpLink.add(input_data=[{dent: [{'device': bond, 'type': 'bond', 'mode': '802.3ad'} for bond in bonds]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bond'

    out = await IpLink.set(input_data=[{dent: [{'device': bond, 'operstate': 'up'} for bond in bonds]}])
    assert out[0][dent]['rc'] == 0, 'Failed setting bond to state up'

    # Create 2 VRF tables
    for vrf, table_id in zip([vrf_1, vrf_2], [10, 20]):
        out = await IpLink.add(input_data=[{dent: [{'dev': vrf, 'type': 'vrf', 'table': table_id}]}])
        assert out[0][dent]['rc'] == 0, 'Failed to add vrf'

        out = await IpLink.set(input_data=[{dent: [{'device': vrf, 'operstate': 'up'}]}])
        assert out[0][dent]['rc'] == 0, 'Failed setting vrf to up state'

        out = await IpRoute.add(
            input_data=[{dent: [{'table': table_id, 'type': 'unreachable', 'table_id': 'default'}]}])
        assert out[0][dent]['rc'] == 0, 'Failed adding route'

    # 2. Enslave DUT port <==> tgen port 1 to bond 1
    # DUT port <==>  tgen port2 to bond 2
    # DUT port <==> tgen port 3 to bond 3
    # DUT port <==>  tgen port 4 to bond 3
    out = await IpLink.set(input_data=[
        {dent: [{'device': port, 'operstate': 'down'} for port in ports] +
               [{'device': ports[0], 'master': bonds[0]}] +
               [{'device': ports[1], 'master': bonds[1]}] +
               [{'device': port, 'master': bonds[2]} for port in ports[2:]] +
               [{'device': bonds[2], 'master': bridge}]
         }])
    assert out[0][dent]['rc'] == 0, 'Failed changing state of the interfaces'

    # VLAN device
    out = await IpLink.add(input_data=[{dent: [
        {'link': bridge,
         'name': vlan_device,
         'type': 'vlan',
         'id': vid}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add vlan device'
    out = await IpLink.set(input_data=[{dent: [{'device': vlan_device, 'operstate': 'up'}]}])
    assert out[0][dent]['rc'] == 0, 'Failed setting vlan device to state up'

    #  Enslave bond1 and bond2 to vrf1 and bond3 to vrf2
    out = await IpLink.set(input_data=[
        {dent: [{'device': bonds[0], 'master': vrf_1}] +
               [{'device': vlan_device, 'master': vrf_1}] +
               [{'device': bonds[1], 'master': vrf_2}]
         }])
    assert out[0][dent]['rc'] == 0, 'Failed enslaving bonds to vrfs'

    # 3. Set link up on all participant ports
    out = await IpLink.set(input_data=[{dent: [{'device': port, 'operstate': 'up'} for port in ports]}])
    assert out[0][dent]['rc'] == 0, f'Failed setting {ports[0]} to state up'

    # 4. Configure ip addresses in each LAG and configure route 10.1.1.0/24 via bridge
    out = await IpAddress.add(input_data=[
        {dent: [{'dev': bonds[0], 'prefix': '1.1.1.1/24'}] +
               [{'dev': vlan_device, 'prefix': '2.2.2.1/24'}] +
               [{'dev': bonds[1], 'prefix': '2.2.2.1/24'}]
         }])
    assert out[0][dent]['rc'] == 0, 'Failed adding IP address to bonds'

    out = await IpRoute.add(input_data=[{dent: [{'vrf': vrf_1,
                                                 'dst': '10.1.1.0/24',
                                                 'via': '2.2.2.3'}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add ip route'

    out = await IpRoute.add(input_data=[{dent: [{'vrf': vrf_2,
                                                 'dst': '10.1.1.0/24',
                                                 'via': '2.2.2.3'}]}])

    assert out[0][dent]['rc'] == 0, 'Failed to add ip route'

    # 5. Setup one stream with DIP 10.1.1.1, and one with 2.2.2.3
    dev_groups = tgen_utils_dev_groups_from_config((
        {'ixp': tgen_lag_1[0], 'ip': '1.1.1.2', 'gw': '1.1.1.1',
         'plen': 24, 'lag_members': tgen_lag_1[1]},
        {'ixp': tgen_lag_3[0], 'ip': '2.2.2.3', 'gw': '2.2.2.1',
         'plen': 24, 'lag_members': tgen_lag_3[1]},
        {'ixp': tgen_lag_2[0], 'ip': '3.3.3.4', 'gw': '3.3.3.1',
         'plen': 24, 'lag_members': tgen_lag_2[1]}
    ))
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)
    swp_info = {}
    await tgen_utils_get_swp_info(device, bonds[0], swp_info)
    bond_1_mac = swp_info['mac']

    streams = {
        f'{tgen_lag_1[0]} -> {[tgen_lag_2[0], tgen_lag_3[0]]}': {
            'type': 'raw',
            'ip_source': dev_groups[tgen_lag_1[0]][0]['name'],
            'ip_destination': [dev_groups[tgen_lag_3[0]][0]['name'], dev_groups[tgen_lag_2[0]][0]['name']],
            'protocol': 'ip',
            'dstMac': bond_1_mac,
            'srcMac': 'aa:bb:cc:dd:ee:ff',
            'srcIp': '1.1.1.10',
            'dstIp': {'type': 'increment',
                      'start': '10.1.1.1',
                      'step': '0.0.0.1',
                      'count': 100},
            'rate': rate
        }
    }
    # 6. Transmit traffic
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
    await asyncio.sleep(25)

    # 7. Verify traffic received on active bond2 port in vrf0 and not received on vrf1
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Port Statistics')
    tx_packets = sum([int(row['Frames Tx.'])
                      for row in stats.Rows if row['Port Name'] in tgen_lag_1[1]])
    total_received_bond_3 = sum([int(row['Valid Frames Rx.'])
                                 for row in stats.Rows if row['Port Name'] in tgen_lag_3[1]])
    err_msg = f'Expected packets  {tx_packets}, actual packets: {total_received_bond_3}'
    assert isclose(total_received_bond_3 /
                   len(tgen_lag_2[1]), tx_packets / len(tgen_lag_2[1]), rel_tol=0.05), err_msg

    total_received_bond_2 = sum([int(row['Valid Frames Rx.'])
                                 for row in stats.Rows if row['Port Name'] in tgen_lag_2[1]])
    err_msg = f'Expected packets  {0.0}, actual packets: {total_received_bond_2}'
    assert total_received_bond_2 < 50, err_msg
