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
    tgen_utils_get_loss,
)
pytestmark = [pytest.mark.suite_functional_lacp,
              pytest.mark.asyncio,
              pytest.mark.usefixtures('cleanup_tgen', 'cleanup_bonds', 'cleanup_bridges',
                                      'enable_ipv4_forwarding')]


async def test_lacp_routing_over_vlan_device(testbed):
    """
    Test Name: LACP routing
    Test Suite: suite_functional_lacp
    Test Overview: Test lacp routing over vlan device
    Test Procedure:
    1. Enable IPv4 forwarding
    2. Create bridge and 2 bonds
    3. Enslave DUT port <==> tgen port 1 to bond1
        # DUT port <==>  tgen port2 to bond 2
        # DUT port <==> tgen port 3 to bond 2
        # DUT port <==>  tgen port 4 to bond 2
    4. Enslave bond2 to bridge
    5. Set link up on all participant ports
    6. Configure ip addresses in each LAG and configure route 10.1.1.0/24 via vlan device
    7. Setup one stream with DIP 10.1.1.1, and one with 2.2.2.3
    8. Transmit traffic
    9. Verify no traffic loss
    """
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip(
            'The testbed does not have enough dent with tgen connections')
    device = dent_devices[0]
    dent = device.host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]
    bridge = 'bridge_0'
    bond_1 = 'bond_1'
    bond_2 = 'bond_2'
    vid = 10
    vlan_device = f'{bridge}.{vid}'
    lag = 'LAG_1'
    # 1. Enable IPv4 forwarding
    # 2. Create bridge and 2 bonds
    out = await IpLink.add(input_data=[{dent: [{
        'device': bridge,
        'type': 'bridge',
        'vlan_filtering': 1,
        'vlan_default_pvid': vid,
    }]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bridge'

    out = await IpLink.set(input_data=[{dent: [{'device': bridge, 'operstate': 'up'}]}])
    assert out[0][dent]['rc'] == 0, 'Failed setting bridge to state up'

    out = await BridgeVlan.add(input_data=[{dent: [{'device': bridge, 'vid': vid, 'self': True}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add vlan on device'

    out = await IpLink.add(input_data=[{dent: [
        {'device': bond,
         'type': 'bond',
         'mode': '802.3ad'} for bond in [bond_1, bond_2]]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bond'

    out = await IpLink.set(input_data=[{dent: [{'device': bond, 'operstate': 'up'} for bond in [bond_1, bond_2]]}])
    assert out[0][dent]['rc'] == 0, 'Failed setting bond to state up'

    # 3. Enslave DUT port <==> tgen port 1 to bond 1
    # DUT port <==>  tgen port2 to bond 2
    # DUT port <==> tgen port 3 to bond 2
    # DUT port <==>  tgen port 4 to bond 2
    out = await IpLink.set(input_data=[
        {dent: [{'device': port, 'operstate': 'down'} for port in ports] +
               [{'device': ports[0], 'master': bond_1}] +
               [{'device': port, 'master': bond_2} for port in ports[1:]] +
               [{'device': bond_2, 'master': bridge}] +
               [{'device': port, 'operstate': 'up'} for port in ports]
         }])
    assert out[0][dent]['rc'] == 0, 'Failed setting links to state down'

    out = await IpLink.add(input_data=[{dent: [
        {'link': bridge,
         'name': vlan_device,
         'type': 'vlan',
         'id': vid}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add vlan device'

    out = await IpLink.set(input_data=[{dent: [{'device': vlan_device, 'operstate': 'up'}]}])
    assert out[0][dent]['rc'] == 0, 'Failed setting vlan device to state up'

    # 6. Configure ip addresses in each LAG and configure route 10.1.1.0/24 via vlan device
    out = await IpAddress.add(input_data=[
        {dent: [{'dev': bond_1, 'prefix': '1.1.1.1/24'}] +
               [{'dev': vlan_device, 'prefix': '2.2.2.2/24'}]
         }])
    assert out[0][dent]['rc'] == 0, f'Failed adding IP address to {bond_1}'

    out = await IpRoute.add(input_data=[{dent: [{'dst': '10.1.1.0/24', 'via': '2.2.2.3'}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add ip route'

    # 7. Setup one stream with DIP 10.1.1.1, and one with 2.2.2.3
    dev_groups = tgen_utils_dev_groups_from_config((
        {'ixp': tg_ports[0], 'ip': '1.1.1.2', 'gw': '1.1.1.1', 'plen': 24},
        {'ixp': lag, 'ip': '2.2.2.3', 'gw': '2.2.2.1',
            'plen': 24, 'lag_members': tg_ports[1:]}
    ))

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    swp_info = {}
    await tgen_utils_get_swp_info(device, bond_1, swp_info)
    bridge_mac = swp_info['mac']

    streams = {
        f'{tg_ports[0]} -> 10.1.1.1/24': {
            'type': 'raw',
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[lag][0]['name'],
            'protocol': 'ip',
            'dstMac': bridge_mac,
            'srcMac': 'aa:bb:cc:dd:ee:ff',
            'dstIp': '10.1.1.1',
            'srcIp': '1.1.1.10',
            'frame_rate_type': 'line_rate',
            'rate': '100'
        },
        f'{tg_ports[0]} -> 2.2.2.3/24 (bridge IP)': {
            'type': 'raw',
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[lag][0]['name'],
            'protocol': 'ip',
            'srcMac': 'aa:bb:cc:dd:ee:ff',
            'dstMac': bridge_mac,
            'srcIp': '1.1.1.10',
            'dstIp': '2.2.2.3',
            'frame_rate_type': 'line_rate',
            'rate': '100'
        },
    }
    # 8. Transmit traffic
    try:
        await tgen_utils_setup_streams(tgen_dev, None, streams)
    except AssertionError as e:
        if 'LAG' in str(e):
            pytest.skip(str(e))
        else:
            raise  # will re-raise the AssertionError
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(25)
    await tgen_utils_stop_traffic(tgen_dev)

    # 9. Verify no traffic loss
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Traffic Item Statistics')
    for row in stats.Rows:
        err_msg = f"Expected 0.00 loss, actual {float(row['Loss %'])}"
        assert isclose(tgen_utils_get_loss(row), 0.00, abs_tol=0.1), err_msg
