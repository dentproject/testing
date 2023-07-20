import asyncio
import pytest
from math import isclose

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.mstpctl.mstpctl import Mstpctl

from dent_os_testbed.utils.test_utils.tgen_utils import (tgen_utils_get_dent_devices_with_tgen,
                                                         tgen_utils_setup_streams, tgen_utils_start_traffic,
                                                         tgen_utils_get_traffic_stats, tgen_utils_stop_traffic,
                                                         tgen_utils_dev_groups_from_config,
                                                         tgen_utils_traffic_generator_connect, )
pytestmark = [pytest.mark.suite_functional_lacp,
              pytest.mark.asyncio,
              pytest.mark.usefixtures('cleanup_tgen', 'cleanup_bonds', 'cleanup_bridges', 'enable_mstpd')]


@pytest.mark.parametrize('version', ['rstp', 'stp'])
async def test_lacp_loopback_detection(testbed, version):
    """
    Test Name: LACP STP/RSTP interaction
    Test Suite: suite_functional_lacp
    Test Overview: Test stp/rstp loopback detection
    Test Procedure:
    1. Create bridge bridge_1 and 6 bonds and set link up on them
    2. Enslave ports to bonds, bonds to bridges
    4. Set link up on all participant ports, bonds, bridges
    5. Wait until topology converges
    6. Send broadcast traffic for a random time between 30-60 seconds.
    7. Verify device remain stable afterwards (during storming). Verify there is a storming
    8. Set bridge stp_state to 1
    9. Verify that afterwards all bonds with the lowest number within a loopback connection are blocked.
    10. Verify that the rate on Ixia ports is 0 (storming has stopped)
    """
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip(
            'The testbed does not have enough dent with tgen connections')
    device = dent_devices[0]
    dent = device.host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    dut_ixia_ports = tgen_dev.links_dict[dent][1]
    bonds = {}
    for idx, port in enumerate(device.links_dict[dent][0] + device.links_dict[dent][1]):
        bonds[f'bond_{idx+1}'] = port
    bridge = 'bridge_1'
    wait_time = 40 if version == 'stp' else 20

    # 1. Create bridge entities and 6 bonds and set link up on them
    out = await IpLink.add(input_data=[{dent: [{'device': bond,
                                                'type': 'bond',
                                                'mode': '802.3ad'} for bond in bonds]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bond'

    out = await IpLink.add(input_data=[{dent: [{
        'device': bridge,
        'type': 'bridge',
        'stp_state': 0}]}])  # stp not enabled
    assert out[0][dent]['rc'] == 0, 'Failed to add bridge'

    # 2. Enslave ports according to the test's setup topology
    out = await IpLink.set(input_data=[
        {dent: [{'device': port_in_bond, 'operstate': 'down'} for port_in_bond in bonds.values()] +
               [{'device': port, 'operstate': 'down'} for port in dut_ixia_ports] +
               [{'device': bond, 'operstate': 'down'} for bond in bonds] +
               [{'device': bridge, 'operstate': 'down'}]
         }])
    assert out[0][dent]['rc'] == 0, 'Failed changing state of the interfaces to down'

    out = await IpLink.set(input_data=[
        {dent: [{'device': port, 'master': bond} for bond, port in bonds.items()] +
         [{'device': bond, 'master': bridge} for bond in bonds] +
         [{'device': port, 'master': bridge} for port in dut_ixia_ports]
         }])
    assert out[0][dent]['rc'] == 0, 'Failed changing state of the interfaces to up'

    # 4. Set link up on all participant ports, bonds, bridges
    out = await IpLink.set(input_data=[
        {dent: [{'device': port_in_bond, 'operstate': 'up'} for port_in_bond in bonds.values()] +
               [{'device': port, 'operstate': 'up'} for port in dut_ixia_ports] +
               [{'device': bond, 'operstate': 'up'} for bond in bonds] +
               [{'device': bridge, 'operstate': 'up'}]
         }])
    assert out[0][dent]['rc'] == 0, 'Failed changing state of the interfaces'

    # 5. Wait until topology converges
    await asyncio.sleep(wait_time)

    # 6. Send broadcast traffic for a random time between 30-60 seconds.
    dev_groups = tgen_utils_dev_groups_from_config((
        {'ixp': tg_ports[0], 'ip': '1.1.1.2', 'gw': '1.1.1.1', 'plen': 24},
        {'ixp': tg_ports[1], 'ip': '1.1.1.3', 'gw': '1.1.1.1', 'plen': 24},
        {'ixp': tg_ports[2], 'ip': '1.1.1.4', 'gw': '1.1.1.1', 'plen': 24},
        {'ixp': tg_ports[3], 'ip': '1.1.1.5', 'gw': '1.1.1.1', 'plen': 24},

    ))
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ixia_ports, dev_groups)
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

    # 7. Verify device remain stable afterwards (during storming).
    rc, out = await device.run_cmd("echo 'Hello World'")
    assert rc == 0, 'FAIL: DUT crashed due to storming'
    assert out.strip() == 'Hello World', f'Expected <Hello World> got {out}'

    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Port Statistics')
    # Verify there is storming
    for row in stats.Rows:
        if row['Port Name'] == tg_ports[0]:
            err_msg = f'Expected 1400 got : {float(row["Rx. Rate (Mbps)"])}'
            assert float(row['Rx. Rate (Mbps)']) > 1400, err_msg

    # 8. Set bridge stp_state to 1.
    out = await IpLink.set(input_data=[{dent: [{
        'device': bridge,
        'type': 'bridge',
        'stp_state': 1}]}])  # stp enabled
    assert out[0][dent]['rc'] == 0, 'Failed to enable stp on bridge'
    out = await Mstpctl.add(input_data=[{dent: [{'bridge': bridge}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bridge with mstpd'
    out = await Mstpctl.set(input_data=[{dent: [{
        'bridge': bridge,
        'parameter': 'forcevers',
        'version': version}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set stp/rstp version'
    await asyncio.sleep(wait_time)

    out = await Mstpctl.add(input_data=[{dent: [{'bridge': bridge}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bridge with mstpd'
    out = await Mstpctl.set(input_data=[{dent: [{
        'bridge': bridge,
        'parameter': 'forcevers',
        'version': version}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set stp/rstp version'
    out = await Mstpctl.show(input_data=[{dent: [
        {'parameter': 'portdetail',
         'bridge': bridge,
         'options': '-f json'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, f'Failed to get port detail of {bridge}'

    # 9. Verify that afterwards all bonds with the lowest number within a loopback connection are blocked.
    for dev in out[0][dent]['parsed_output']:
        if dev['port'] in list(bonds)[3:]:
            assert dev['state'] == 'discarding'
    await asyncio.sleep(wait_time)

    # 10. Verify that the rate on Ixia ports is 0 (storming has stopped)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Port Statistics')
    for row in stats.Rows:
        if row['Port Name'] == tg_ports[0]:
            err_msg = f'Expected 0 got : {float(row["Rx. Rate (Mbps)"])}'
            assert isclose(float(row['Rx. Rate (Mbps)']), 0.00, abs_tol=0.1), err_msg
