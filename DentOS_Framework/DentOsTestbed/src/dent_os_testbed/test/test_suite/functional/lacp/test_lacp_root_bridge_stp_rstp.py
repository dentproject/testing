import asyncio
import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.mstpctl.mstpctl import Mstpctl
from dent_os_testbed.utils.test_utils.tgen_utils import tgen_utils_get_dent_devices_with_tgen

pytestmark = [pytest.mark.suite_functional_lacp,
              pytest.mark.asyncio,
              pytest.mark.usefixtures('cleanup_bonds', 'cleanup_bridges', 'enable_mstpd')]


@pytest.mark.parametrize('version', ['stp', 'rstp'])
async def test_lacp_root_bridge_selection_stp(testbed, version):
    """
    Test Name: LACP STP/RSTP interaction
    Test Suite: suite_functional_lacp
    Test Overview: Test root bridge selection based on MAC rule
    Test Procedure:
    1. Create 3 bridge entities and 6 bonds and set link up on them
    2. Enslave ports according to the test's setup topology
    3. Change the MAC addresses for all bridges.
    4. Set link up on all participant ports
    5. Wait until topology converges
    6. Verify the bridge root is bridge_1 by the lowest MAC rule. Other bridges are not root bridges
    7. Verify bridge_3 has a blocking port
    8. Verify bridge_1 doesn't have any blocking port.
    9. Change bridge_3 priority to a priority with lower value then the root bridge.
    10. Wait ~10 seconds for topology to re-build.
    11. Verify bridge_3 has become the new root bridge.
    12. Verify bridge_2 has a blocking port
    13  Verify bridge_1 doesn't have any blocking port.
    """
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip(
            'The testbed does not have enough dent with tgen connections')
    device = dent_devices[0]
    dent = device.host_name

    bonds = {}
    for idx, port in enumerate(device.links_dict[dent][0] + device.links_dict[dent][1]):
        bonds[f'bond_{idx+1}'] = port

    bond_to_bridges = list(bonds.keys())
    bridges = {
        'bridge_1': bond_to_bridges[:2],
        'bridge_2': bond_to_bridges[2:4],
        'bridge_3': bond_to_bridges[4:]
    }
    bridge_names = list(bridges.keys())
    hw_mac = ['22:AA:98:EA:D2:43', '44:0A:D1:68:4E:B9', '66:2A:31:66:1C:CD']
    time_to_wait = 40 if version == 'stp' else 20

    # 1. Create 3 bridge entities and 6 bonds and set link up on them
    out = await IpLink.add(input_data=[{dent: [{'device': bond,
                                                'type': 'bond',
                                                'mode': '802.3ad'} for bond in bonds]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bond'

    out = await IpLink.add(input_data=[{dent: [{
        'device': bridge,
        'type': 'bridge',
        'stp_state': 1} for bridge in bridges]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bridge'

    out = await Mstpctl.add(input_data=[{dent: [{'bridge': bridge} for bridge in bridges]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bridge with mstpd'

    out = await Mstpctl.set(input_data=[{dent: [{
        'bridge': bridge,
        'parameter': 'forcevers',
        'version': version} for bridge in bridges]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set stp/rstp version'

    # 2. Enslave ports according to the test's setup topology
    out = await IpLink.set(input_data=[
        {dent: [{'device': port, 'operstate': 'down'} for port in bonds.values()] +
               [{'device': bond, 'operstate': 'down'} for bond in bonds] +
               [{'device': bridge, 'operstate': 'down'} for bridge in bridges]
         }])
    assert out[0][dent]['rc'] == 0, 'Failed setting interfaces to state down'

    out = await IpLink.set(input_data=[{dent: [{'device': port, 'master': bond}]} for bond, port in bonds.items()])
    assert out[0][dent]['rc'] == 0, 'Failed enslaving port to bond'

    for bridge, lags in bridges.items():
        out = await IpLink.set(input_data=[{dent: [{'device': lag, 'master': bridge} for lag in lags]}])
        assert out[0][dent]['rc'] == 0, f'Failed enslaving lag to {bridge}'

    # 3. Change the MAC addresses for all bridges
    for bridge, mac in zip(bridge_names, hw_mac):
        rc, _ = await device.run_cmd(f'ifconfig {bridge} hw ether {mac}')
        assert rc == 0, 'Failed to change MAC address'

    # 4. Set link up on all participant ports
    out = await IpLink.set(input_data=[
        {dent: [{'device': port, 'operstate': 'up'} for port in bonds.values()] +
               [{'device': bond, 'operstate': 'up'} for bond in bonds] +
               [{'device': bridge, 'operstate': 'up'} for bridge in bridges]
         }])
    assert out[0][dent]['rc'] == 0, 'Failed setting interfaces to state up'

    for bridge, bonds in bridges.items():
        out = await Mstpctl.set(input_data=[{dent: [{
            'bridge': bridge,
            'parameter': 'portpathcost',
            'port': bond,
            'cost': 1000} for bond in bonds]}])
        assert out[0][dent]['rc'] == 0, 'Failed setting port pathcost'

    # 5. Wait until topology converges
    await asyncio.sleep(time_to_wait)
    # 6. Verify the bridge root is bridge_1 by the lowest MAC rule
    out = await Mstpctl.show(input_data=[{dent: [
        {'parameter': 'bridge',
         'bridge': bridge_names[0],
         'options': '-f json'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get bridge detail'

    assert out[0][dent]['parsed_output'][0][
        'root-port'] == '', f'Bridge { bridge_names[0]} is not a root bridge'
    # Other bridges do not consider themselves as root bridge
    for bridge in bridge_names[1:]:
        out = await Mstpctl.show(input_data=[{dent: [
            {'parameter': 'bridge',
             'bridge': bridge,
             'options': '-f json'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get bridge detail'
    assert out[0][dent]['parsed_output'][0]['root-port'] != '', f'Bridge {bridge} is a root bridge'

    # 7. Verify bridge_3 has a blocking port
    out = await Mstpctl.show(input_data=[{dent: [
        {'parameter': 'portdetail',
         'bridge': bridge_names[2],
         'options': '-f json'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, f'Failed to get port detail of {bridge_names[2]}'
    ports_state = [bond['state'] for bond in out[0][dent]['parsed_output']]
    assert 'discarding' in ports_state, f'Bridge {bridge_names[2]} does not have a blocking port'

    # 8.Verify bridge_1 do not have any blocking port.
    out = await Mstpctl.show(input_data=[{dent: [
        {'parameter': 'portdetail',
         'bridge': bridge_names[0],
         'options': '-f json'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, f'Failed to get port detail of {bridge_names[0]}'
    ports_state = [bond['state'] for bond in out[0][dent]['parsed_output']]
    assert 'discarding' not in ports_state, f'Bridge {bridge_names[0]} does have a blocking port'

    # 9. Change bridge_3 priority to a priority with lower value then the root bridge.
    out = await Mstpctl.set(input_data=[{dent: [
        {'parameter': 'treeprio',
         'bridge': bridge_names[2],
         'mstid': 0,
         'priority': 1}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to change priority of the bridge'

    # 10 Wait seconds for topology to re-build.
    await asyncio.sleep(time_to_wait)

    # 11 Verify bridge_3 has become the new root bridge.
    out = await Mstpctl.show(input_data=[{dent: [
        {'parameter': 'bridge',
         'bridge': bridge_names[2],
         'options': '-f json'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, f'Failed to get detail of {bridge_names[2]}'
    assert out[0][dent]['parsed_output'][0]['root-port'] == '', f'Bridge {bridge_names[2]} is not a root bridge'

    # bridge_1 and bridge_2 do not consider themselves as root-bridge
    for bridge in bridge_names[:2]:
        out = await Mstpctl.show(input_data=[{dent: [
            {'parameter': 'bridge',
             'bridge': bridge,
             'options': '-f json'}]}], parse_output=True)
        assert out[0][dent]['rc'] == 0, f'Failed to get detail of {bridge}'
        assert out[0][dent]['parsed_output'][0]['root-port'] != '', f'Bridge {bridge} is a root bridge'

    # 12. Verify bridge_2 has a blocking port
    out = await Mstpctl.show(input_data=[{dent: [
        {'parameter': 'portdetail',
         'bridge': bridge_names[1],
         'options': '-f json'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, f'Failed to get port detail of {bridge_names[1]}'
    ports_state = [bond['state'] for bond in out[0][dent]['parsed_output']]
    assert 'discarding' in ports_state, f'Bridge {bridge_names[1]} does have a blocking port'

    # 13 Verify bridge_1 doesn’t have any blocking port.
    out = await Mstpctl.show(input_data=[{dent: [
        {'parameter': 'portdetail',
         'bridge': bridge_names[0],
         'options': '-f json'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, f'Failed to get port detail of {bridge_names[0]}'
    ports_state = [bond['state'] for bond in out[0][dent]['parsed_output']]
    assert 'discarding' not in ports_state, f'Bridge {bridges[0]} does have a blocking port'
