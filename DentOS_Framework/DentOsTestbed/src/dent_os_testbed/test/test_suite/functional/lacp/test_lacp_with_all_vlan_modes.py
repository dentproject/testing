import asyncio
from math import isclose
import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_clear_traffic_items,
)

pytestmark = [pytest.mark.suite_functional_lacp,
              pytest.mark.asyncio,
              pytest.mark.usefixtures('cleanup_tgen', 'cleanup_bonds', 'cleanup_bridges')]


async def test_lacp_all_vlan_modes(testbed):
    """
    Test Name: LACP with VLAN
    Test Suite: suite_functional_lacp
    Test Overview: Test lacp with tagged/untagged traffic
    Test Procedure:
    1. Create 3 bonds and a bridge
    2. Enslave
        DUT port <==> tgen port 1 to bond 1
        DUT port <==>  tgen port 2 to bond 2
        DUT port <==> tgen port 3 to bond 3
        DUT port <==>  tgen port 4 to bond 3
    3. Set link up on all participant ports
    4. Add bond_1 to VLAN 2 (tagged) and to 4 (pvid untagged), bond_2 to VLAN 2 (tagged), and bond_3 to 4 (pvid)
    5. Setup one stream with uknown unicast untagged
    6. Transmit traffic
    7. Verify traffic received on ports within the bond_3
    8. Setup one stream with uknown unicast, tagged VLAN 2
    9. Verify traffic received on ports within the bond_2
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
    bridge = 'bridge_1'
    rate = 10000

    # 1. Create 3 bonds and a bridge
    out = await IpLink.add(input_data=[{dent: [{'device': bridge, 'type': 'bridge',
                                                'vlan_filtering': 1,
                                                'vlan_default_pvid': 0}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bridge'
    out = await IpLink.set(input_data=[{dent: [{'device': bridge, 'operstate': 'up'}]}])
    assert out[0][dent]['rc'] == 0, 'Failed setting bridge to up state'

    out = await IpLink.add(input_data=[{dent: [{'device': bond, 'type': 'bond', 'mode': '802.3ad'} for bond in bonds]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add a bond'

    # 2. Enslave DUT port <==> tgen port 1 to bond 1
    # DUT port <==>  tgen port2 to bond 2
    # DUT port <==> tgen port 3 to bond 2
    # DUT port <==>  tgen port 4 to bond 3
    out = await IpLink.set(input_data=[
        {dent: [{'device': port, 'operstate': 'down'} for port in ports] +
               [{'device': ports[0], 'master': bonds[0]}] +
               [{'device': ports[1], 'master': bonds[1]}] +
               [{'device': port, 'master': bonds[2]} for port in ports[2:]] +
               [{'device': bond, 'master': bridge} for bond in bonds]
         }])
    assert out[0][dent]['rc'] == 0, 'Failed setting links to state down'

    # 3. Set link up on all participant ports
    out = await IpLink.set(input_data=[
        {dent: [{'device': port, 'operstate': 'up'} for port in ports] +
               [{'device': bond, 'operstate': 'up'} for bond in bonds]
         }])
    assert out[0][dent]['rc'] == 0, 'Failed setting interfaces to state up'

    # 4. Add bond_1 to VLAN 2 (tagged) and to 4 (pvid untagged), bond_2 to VLAN 2 (tagged), and bond_3 to 4 (pvid)
    out = await BridgeVlan.add(input_data=[
        {dent: [{'device': bonds[0], 'vid': 2}] +
               [{'device': bonds[0], 'vid': 4, 'pvid': True, 'untagged': True}] +
               [{'device': bonds[1], 'vid': 2}] +
               [{'device': bonds[2], 'vid': 4, 'pvid': True}]
         }])
    assert out[0][dent]['rc'] == 0, 'Failed adding interfaces to VLAN'

    # 5. Setup one stream with uknown unicast untagged
    dev_groups = tgen_utils_dev_groups_from_config((
        {'ixp': tgen_lag_1[0], 'ip': '1.1.1.2', 'gw': '1.1.1.1', 'plen': 24, 'lag_members': tgen_lag_1[1]},
        {'ixp': tgen_lag_2[0], 'ip': '2.2.2.3', 'gw': '2.2.2.1', 'plen': 24, 'lag_members': tgen_lag_2[1]},
        {'ixp': tgen_lag_3[0], 'ip': '3.3.3.4', 'gw': '3.3.3.1', 'plen': 24, 'lag_members': tgen_lag_3[1]}
    ))

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    streams = {
        f'From {bonds[0]} -> untagged': {
            'type': 'raw',
            'ip_source': dev_groups[tgen_lag_1[0]][0]['name'],
            'ip_destination': [dev_groups[tgen_lag_3[0]][0]['name'], dev_groups[tgen_lag_2[0]][0]['name']],
            'protocol': '802.1Q',
            'srcMac': 'aa:bb:cc:dd:ee:ff',
            'dstMac': '22:A8:9B:BD:BE:C1',
            'rate': rate,
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

    # 7. Verify traffic received on ports within the bond_3
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Port Statistics')
    tx_packets = sum([int(row['Frames Tx.']) for row in stats.Rows if row['Port Name'] in tgen_lag_1[1]])
    total_received = sum([int(row['Valid Frames Rx.']) for row in stats.Rows if row['Port Name'] in tgen_lag_3[1]])
    assert isclose(total_received, tx_packets, rel_tol=0.05), f'Expected: {tx_packets}, actual: {total_received}'

    await tgen_utils_clear_traffic_items(tgen_dev)
    streams = {
        f'From {bonds[0]} -> tagged VLAN 2': {
            'type': 'raw',
            'ip_source': dev_groups[tgen_lag_1[0]][0]['name'],
            'ip_destination': [dev_groups[tgen_lag_3[0]][0]['name'], dev_groups[tgen_lag_2[0]][0]['name']],
            'protocol': '802.1Q',
            'srcMac': 'aa:bb:cc:dd:ee:ff',
            'dstMac': '22:A8:9B:BD:BE:C2',
            'rate': rate,
            'vlanID': 2
        }
    }
    # 8. Setup one stream with uknown unicast, tagged VLAN 2
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(10)
    await tgen_utils_stop_traffic(tgen_dev)
    await asyncio.sleep(25)

    # 9. Verify traffic received on ports within the bond_2
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Port Statistics')
    tx_packets = sum([int(row['Frames Tx.']) for row in stats.Rows if row['Port Name'] in tgen_lag_1[1]])
    total_received = sum([int(row['Valid Frames Rx.']) for row in stats.Rows if row['Port Name'] in tgen_lag_2[1]])
    assert isclose(total_received, tx_packets, rel_tol=0.05), f'Expected: {tx_packets}, actual: {total_received}'
