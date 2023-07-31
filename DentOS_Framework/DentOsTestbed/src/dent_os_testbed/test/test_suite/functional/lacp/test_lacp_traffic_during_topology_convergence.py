import asyncio
import pytest
from math import isclose

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.mstpctl.mstpctl import Mstpctl
from dent_os_testbed.lib.ethtool.ethtool import Ethtool

from dent_os_testbed.utils.test_utils.tgen_utils import (tgen_utils_get_dent_devices_with_tgen,
                                                         tgen_utils_setup_streams, tgen_utils_start_traffic,
                                                         tgen_utils_stop_traffic, tgen_utils_get_traffic_stats,
                                                         tgen_utils_dev_groups_from_config,
                                                         tgen_utils_traffic_generator_connect, )
pytestmark = [pytest.mark.suite_functional_lacp,
              pytest.mark.asyncio,
              pytest.mark.usefixtures('cleanup_tgen', 'cleanup_bonds', 'cleanup_bridges', 'enable_mstpd')]


@pytest.mark.parametrize('version', ['stp', 'rstp'])
async def test_lacp_traffic_during_topology_convergence(testbed, version):
    """
    Test Name: LACP STP/RSTP interaction
    Test Suite: suite_functional_lacp
    Test Overview: Test lacp during stp/rstp topology convergence
    Test Procedure:
    1. Create 3 bridge entities and 6 bonds and set link up on them
    2. Enslave ports to bonds, bonds to bridges
    3. Change all bridges MAC addresses
    4. Set link up on all participant ports, bonds, bridges
    5. Send broadcast traffic for a random time between 30-60 seconds.
    6. Verify device remain stable afterwards (during storming)
    7. Verify there is a storming
    8. Set bridge stp_state to 1
    9. Verify the bridge root is bridge_2 by the lowest MAC rule. Verify other bridges
    do not consider themselves as root-bridge
    10. Verify bridge_1 has a blocking bond
    11 .Verify bridge_3 do not have any blocking bond
    12. Verify that the rate on other tgen ports is 0 (storming has stopped)
    13. Send broadcast traffic for a random time between 30-60 seconds
    14. Verify that traffic is flooded to other tgen ports
    15. Stop the traffic; Verify there is no storming"
    """
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip(
            'The testbed does not have enough dent with tgen connections')
    device = dent_devices[0]
    dent = device.host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    dut_tgen_ports = tgen_dev.links_dict[dent][1]
    bonds = {}
    for idx, port in enumerate(device.links_dict[dent][0] + device.links_dict[dent][1]):
        bonds[f'bond_{idx+1}'] = port
    bond_to_bridges = list(bonds.keys())
    bridges = {
        'bridge_1': bond_to_bridges[:2],
        'bridge_2': bond_to_bridges[2:4],
        'bridge_3': bond_to_bridges[4:]
    }
    hw_mac = ['44:AA:98:EA:D2:43', '00:45:34:43:56:55', '22:0A:D1:68:4E:B9']
    bridge_names = list(bridges.keys())
    tolerance = 0.15
    wait_time = 40 if 'version' == 'stp' else 20
    expected_rate = 0.14  # multiplied by port speed
    # 1. Create 3 bridge entities and 6 bonds and set link up on them
    out = await IpLink.add(input_data=[{dent: [{'device': bond,
                                                'type': 'bond',
                                                'mode': '802.3ad'} for bond in bonds]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bond'

    out = await IpLink.add(input_data=[{dent: [{
        'device': bridge,
        'type': 'bridge',
        'stp_state': 0} for bridge in bridges]}])  # stp not enabled
    assert out[0][dent]['rc'] == 0, 'Failed to add bridge'

    # 2. Enslave ports to bonds, bonds to bridges
    out = await IpLink.set(input_data=[
        {dent: [{'device': port, 'operstate': 'down'} for port in bonds.values()] +
               [{'device': bond, 'operstate': 'down'} for bond in bonds] +
               [{'device': bridge, 'operstate': 'down'} for bridge in bridges] +
               [{'device': port, 'operstate': 'down'} for port in dut_tgen_ports]
         }])
    assert out[0][dent]['rc'] == 0, 'Failed changing state of the interfaces to down'

    out = await IpLink.set(input_data=[{dent: [{'device': port, 'master': bond}]} for bond, port in bonds.items()])
    assert out[0][dent]['rc'] == 0, 'Failed enslaving bonds'

    for bridge, lags in bridges.items():
        out = await IpLink.set(input_data=[{dent: [{'device': lag, 'master': bridge} for lag in lags]}])
        assert out[0][dent]['rc'] == 0, f'Failed enslaving lag to {bridge}'

    out = await IpLink.set(input_data=[
        {dent: [{'device': dut_tgen_ports[0], 'master': bridge_names[0]}] +
               [{'device': dut_tgen_ports[1], 'master': bridge_names[1]}]
         }])
    assert out[0][dent]['rc'] == 0, 'Failed enslaving port'

    # 3. Change the MAC addresses for all bridges
    for bridge, mac in zip(bridge_names, hw_mac):
        rc, _ = await device.run_cmd(f'ifconfig {bridge} hw ether {mac}')
        assert rc == 0, 'Failed to change MAC address'

    # 4. Set link up on all participant ports, bonds, bridges
    out = await IpLink.set(input_data=[
        {dent: [{'device': port, 'operstate': 'up'} for port in bonds.values()] +
               [{'device': bond, 'operstate': 'up'} for bond in bonds] +
               [{'device': bridge, 'operstate': 'up'} for bridge in bridges] +
               [{'device': port, 'operstate': 'up'} for port in dut_tgen_ports]
         }])
    assert out[0][dent]['rc'] == 0, 'Failed changing state of the interfaces to up'

    # 5.Send broadcast traffic for a random time between 30-60 seconds.
    dev_groups = tgen_utils_dev_groups_from_config((
        {'ixp': tg_ports[0], 'ip': '1.1.1.2', 'gw': '1.1.1.1', 'plen': 24},
        {'ixp': tg_ports[1], 'ip': '1.1.1.3', 'gw': '1.1.1.1', 'plen': 24},
        {'ixp': tg_ports[2], 'ip': '1.1.1.4', 'gw': '1.1.1.1', 'plen': 24},
        {'ixp': tg_ports[3], 'ip': '1.1.1.5', 'gw': '1.1.1.1', 'plen': 24},

    ))
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_tgen_ports, dev_groups)
    tx_ports = dev_groups[tg_ports[0]][0]['name']
    rx_ports = [dev_groups[tg_ports[1]][0]['name'],
                dev_groups[tg_ports[2]][0]['name'],
                dev_groups[tg_ports[3]][0]['name']]
    streams = {
        f'{rx_ports} -> Broadcast': {
            'type': 'raw',
            'ip_source': tx_ports,
            'ip_destination': rx_ports,
            'srcMac': 'aa:bb:cc:dd:ee:ff',
            'dstMac': 'ff:ff:ff:ff:ff:ff',
            'frame_rate_type': 'line_rate',
            'rate': 5
        }
    }

    try:
        await tgen_utils_setup_streams(tgen_dev, None, streams)
    except AssertionError as e:
        if 'LAG' in str(e):
            pytest.skip(str(e))
        else:
            raise  # will re-raise the AssertionError
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(wait_time)
    await tgen_utils_stop_traffic(tgen_dev)
    # 6. Verify device remain stable afterwards (during storming)
    rc, out = await device.run_cmd("echo 'Hello World'")
    assert rc == 0, 'FAIL: DUT crashed due to storming'
    assert out.strip() == 'Hello World', f'Expected <Hello World> got {out}'
    await asyncio.sleep(wait_time)

    # 7. Verify there is a storming
    out = await Ethtool.show(input_data=[{dent: [{'devname': dut_tgen_ports[2]}]}],  parse_output=True)
    speed = int(out[0][dent]['parsed_output']['speed'][:-4])
    expected_rate = round(int(expected_rate * speed), 2)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Port Statistics')
    for row in stats.Rows:
        if row['Port Name'] in tg_ports[:2]:
            err_msg = f'Expected {int(expected_rate * speed)} got : {float(row["Rx. Rate (Mbps)"])}'
            assert float(row['Rx. Rate (Mbps)']) > expected_rate, err_msg

    # 8. Set bridge stp_state to 1.
    out = await IpLink.set(input_data=[{dent: [{
        'device': bridge,
        'type': 'bridge',
        'stp_state': 1} for bridge in bridge_names]}])
    assert out[0][dent]['rc'] == 0, 'Failed to enable stp on bridge'

    out = await Mstpctl.add(input_data=[{dent: [{'bridge': bridge} for bridge in bridges]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bridge with mstpd'

    out = await Mstpctl.set(input_data=[{dent: [{
        'bridge': bridge,
        'parameter': 'forcevers',
        'version': version} for bridge in bridges]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set stp/rstp version'

    # 9. Wait for convergence
    await asyncio.sleep(wait_time)

    # 10. Verify the bridge root is bridge_1 by the lowest MAC rule; verify other bridges
    # do not consider themselves as root-bridge
    out = await Mstpctl.show(input_data=[{dent: [
        {'parameter': 'bridge',
         'bridge': bridge_names[1],
         'options': '-f json'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get bridge detail'

    assert out[0][dent]['parsed_output'][0][
        'root-port'] == '', f'Bridge { bridge_names[1]} is not a root bridge'
    # Other bridges do not consider themselves as root bridge
    for bridge in [bridge_names[0], bridge_names[2]]:
        out = await Mstpctl.show(input_data=[{dent: [
            {'parameter': 'bridge',
             'bridge': bridge,
             'options': '-f json'}]}], parse_output=True)
        assert out[0][dent]['rc'] == 0, 'Failed to get bridge detail'
        assert out[0][dent]['parsed_output'][0][
            'root-port'] != '', f'Bridge { bridge_names[0]} or {bridge_names[2]} is a root bridge'

    # 11. Verify bridge_1 has a blocking bond
    out = await Mstpctl.show(input_data=[{dent: [
        {'parameter': 'portdetail',
         'bridge': bridge_names[0],
         'options': '-f json'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, f'Failed to get port detail of {bridge_names[1]}'
    ports_state = [bond['state'] for bond in out[0][dent]['parsed_output']]
    assert 'discarding' in ports_state, f'Bridge {bridge_names[0]} does not have a blocking port'

    # 12. Verify bridge_3 do not have any blocking port.
    out = await Mstpctl.show(input_data=[{dent: [
        {'parameter': 'portdetail',
         'bridge': bridge_names[2],
         'options': '-f json'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, f'Failed to get port detail of {bridge_names[2]}'
    ports_state = [bond['state'] for bond in out[0][dent]['parsed_output']]
    assert 'discarding' not in ports_state, f'Bridge {bridge_names[2]} does not have a blocking port'

    # 13. Verify that the rate on other tgen ports is 0 (storming has stopped)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Port Statistics')

    for row in stats.Rows:
        if row['Port Name'] in [tg_ports[1], tg_ports[0]]:
            err_msg = f'Expected 0.0 got : {float(row["Rx. Rate (Mbps)"])}'
            assert isclose(float(row['Rx. Rate (Mbps)']), 0.00, abs_tol=tolerance), err_msg

    # 14. Send broadcast traffic for a random time between 30-60 seconds.
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(wait_time)

    # 15. Verify that traffic is flooded to other tgen  ports
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Port Statistics')
    for row in stats.Rows:
        if row['Port Name'] == tg_ports[1]:
            err_msg = f'Expected 1400 got : {float(row["Rx. Rate (Mbps)"])}'
            assert isclose(float(row['Rx. Rate (Mbps)']), expected_rate, rel_tol=tolerance), err_msg

    # 16. Stop the traffic. Verify there is no storming
    await tgen_utils_stop_traffic(tgen_dev)
    await asyncio.sleep(10)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Port Statistics')
    for row in stats.Rows:
        err_msg = f'Expected 0 got : {float(row["Rx. Rate (Mbps)"])}'
        assert isclose(float(row['Rx. Rate (Mbps)']), 0.00, abs_tol=tolerance), err_msg
