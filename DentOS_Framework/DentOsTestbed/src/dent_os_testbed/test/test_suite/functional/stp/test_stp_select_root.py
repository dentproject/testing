import asyncio
import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.mstpctl.mstpctl import Mstpctl
from dent_os_testbed.utils.test_utils.tgen_utils import tgen_utils_get_dent_devices_with_tgen

pytestmark = [pytest.mark.suite_functional_stp,
              pytest.mark.asyncio,
              pytest.mark.usefixtures('cleanup_tgen', 'cleanup_bonds', 'cleanup_bridges', 'enable_mstpd')]


@pytest.mark.parametrize('version', ['stp', 'rstp'])
async def test_stp_select_root_bridge(testbed, version):
    """
    Test Name: STP/RSTP selecting root bridge
    Test Suite: suite_functional_stp
    Test Overview: Test root bridge selection based on bridge priority
    Test Procedure:
    1. Create 3 bridge entities and set link up on them
    2. Enslave ports to bridges
    3. Change the MAC addresses for all bridges.
    4. Set link up on all participant ports, bridges. Change priority of the bridges
    5. Wait until topology converges
    6. Verify the bridge root is br1 by the lowest MAC rule
        Verify other bridges do not consider themselves as root-bridge
    7. Verify bridge_2 has a blocking port
    8. Verify bridge_1 doesn't have any blocking port.
    9. Change the highest bridge priority to a priority with lower value then the root bridge.
    10. Wait  for topology to re-build.
    11. Verify bridge_2 has a blocking port and is not the same port as before
    12.Verify bridge_2 has a blocking port
    13.Verify bridge_1 does not have a blocking port
    """
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    device = dent_devices[0]
    dent = device.host_name
    loopback_ports = {}
    for idx, port in enumerate(device.links_dict[dent][0] + device.links_dict[dent][1]):
        loopback_ports[f'loopback_{idx+1}'] = port
    port_to_bridges = list(loopback_ports.values())
    bridges = {
        'bridge_1': port_to_bridges[:2],
        'bridge_2': port_to_bridges[2:4],
        'bridge_3': port_to_bridges[4:]
    }
    wait_time = 40 if version == 'stp' else 20
    bridge_names = list(bridges.keys())
    bridges_priorities = [2, 3, 4]
    hw_mac = ['44:DD:D2:85:22:A4', '22:67:05:4B:CC:25', '00:97:03:21:D9:68']

    # 1. Create 3 bridge entities4  bonds and set link up on them
    out = await IpLink.add(input_data=[{dent: [{
        'device': bridge,
        'type': 'bridge',
        'vlan_filstering': 0,
        'stp_state': 1} for bridge in bridges]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bridge'

    out = await Mstpctl.add(input_data=[{dent: [{'bridge': bridge} for bridge in bridges]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bridge with mstpd'

    out = await Mstpctl.set(input_data=[{dent: [{
        'bridge': bridge,
        'parameter': 'forcevers',
        'version': version} for bridge in bridges]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set stp/rstp version'

    # 2. Enslave ports to bridges
    out = await IpLink.set(input_data=[{dent: [{
        'device': port,
        'operstate': 'down'} for port in loopback_ports.values()]}])
    assert out[0][dent]['rc'] == 0, 'Failed setting links to state down'

    for bridge, ports in bridges.items():
        out = await IpLink.set(input_data=[{dent: [{'device': port, 'master': bridge} for port in ports]}])
        assert out[0][dent]['rc'] == 0, 'Failed enslaving ports'

    # 3. Change the MAC addresses for all bridges
    for bridge, mac in zip(bridge_names, hw_mac):
        rc, _ = await device.run_cmd(f'ifconfig {bridge} hw ether {mac}')
        assert rc == 0, 'Failed to change MAC address'

    # 4. Set link up on all participant ports, bridges
    out = await IpLink.set(input_data=[{dent: [{
        'device': port,
        'operstate': 'up'} for port in loopback_ports.values()]}])
    assert out[0][dent]['rc'] == 0, 'Failed setting loopback links to state up'
    out = await IpLink.set(input_data=[{dent: [{'device': bridge, 'operstate': 'up'} for bridge in bridges]}])
    assert out[0][dent]['rc'] == 0, 'Failed setting bridge to state up'

    for bridge, priority in zip(bridge_names, bridges_priorities):
        out = await Mstpctl.set(input_data=[{dent: [
            {'parameter': 'treeprio',
             'bridge': bridge,
             'mstid': 0,
             'priority': priority}
        ]}])
        assert out[0][dent]['rc'] == 0, 'Failed setting bridge priority'

    # 5. Wait until topology converges
    await asyncio.sleep(wait_time)

    # 6. Verify the bridge root is bridge_1 by the lowest MAC rule;
    # verify other bridges do not consider themselves as root-bridge
    out = await Mstpctl.show(input_data=[{dent: [
        {'parameter': 'bridge',
         'bridge': bridge_names[0],
         'options': '-f json'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get bridge detail'
    assert out[0][dent]['parsed_output'][0]['root-port'] == '', f'Bridge { bridge_names[0]} is not a root bridge'
    # Other bridges do not consider themselves as root bridge
    for bridge in bridge_names:
        out = await Mstpctl.show(input_data=[{dent: [
                {'parameter': 'bridge',
                 'bridge': bridge,
                 'options': '-f json'}]}], parse_output=True)
        assert out[0][dent]['rc'] == 0, 'Failed to get bridge detail'
        assert out[0][dent]['parsed_output'][0][
                   'root-port'] != '', f'Bridge {bridge_names[1]} or {bridge_names[2]} is a root bridge'

    # 7. Verify bridge_3 has a blocking port
    out = await Mstpctl.show(input_data=[{dent: [
        {'parameter': 'portdetail',
         'bridge': bridge_names[2],
         'options': '-f json'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, f'Failed to get port detail of {bridge_names[1]}'
    ports_state = [port['state'] for port in out[0][dent]['parsed_output']]
    assert 'discarding' in ports_state, f'Bridge {bridge_names[2]} does not have a blocking port'

    # 8.Verify bridge_2 doesn’t have any blocking port.
    out = await Mstpctl.show(input_data=[{dent: [
        {'parameter': 'portdetail',
         'bridge': bridge_names[1],
         'options': '-f json'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, f'Failed to get port detail of {bridge_names[1]}'
    ports_state = [port['state'] for port in out[0][dent]['parsed_output']]
    assert 'discarding' not in ports_state, f'Bridge {bridge_names[1]} does have a blocking port'

    # 9. Change the highest bridge priority to a priority with lower value then the root bridge.
    out = await Mstpctl.set(input_data=[{dent: [
            {'parameter': 'treeprio',
             'bridge': bridge_names[2],
             'mstid': 0,
             'priority': 1}
        ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to change priority of the bridge'  # failing for some reason

    # 10. Wait for topology to re-build.
    await asyncio.sleep(wait_time)

    # 11.Verify bridge_3 has become the new root bridge.
    out = await Mstpctl.show(input_data=[{dent: [
        {'parameter': 'bridge',
         'bridge': bridge_names[2],
         'options': '-f json'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get bridge detail'
    assert out[0][dent]['parsed_output'][0]['root-port'] == '', f'Bridge { bridge_names[2]} is a root bridge'
    # Bridge_1 is not a root bridge
    out = await Mstpctl.show(input_data=[{dent: [
        {'parameter': 'bridge',
         'bridge': bridge_names[0],
         'options': '-f json'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get bridge detail'
    assert out[0][dent]['parsed_output'][0]['root-port'] != '', f'Bridge { bridge_names[0]} is not a root bridge'

    # 12.Verify bridge_2 has a blocking port
    out = await Mstpctl.show(input_data=[{dent: [
        {'parameter': 'portdetail',
         'bridge': bridge_names[1],
         'options': '-f json'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, f'Failed to get port detail of {bridge_names[1]}'
    ports_state = [port['state'] for port in out[0][dent]['parsed_output']]
    assert 'discarding' in ports_state, f'Bridge {bridge_names[0]} does have a blocking port'

    # 13.Verify bridge_1 does not have a blocking port
    out = await Mstpctl.show(input_data=[{dent: [
        {'parameter': 'portdetail',
         'bridge': bridge_names[0],
         'options': '-f json'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, f'Failed to get port detail of {bridge_names[1]}'
    ports_state = [port['state'] for port in out[0][dent]['parsed_output']]
    assert 'discarding' not in ports_state, f'Bridge {bridge_names[0]} does have a blocking port'


@pytest.mark.parametrize('version', ['stp', 'rstp'])
async def test_stp_select_root_port(testbed, version):
    """
    Test Name: STP/RSTP selecting root port
    Test Suite: suite_functional_stp
    Test Overview: Test root port in selected by the port having the lowest priority number.
    Test Procedure:
    1. Create 2 bridge entities and set link up on them
    2. Enslave ports to bridges
    3. Change the MAC addresses for all bridges.
    4. Set link up on all participant ports, bridges
    5. Wait until topology converges
    6. Verify the bridge root is bridge_1 by the lowest MAC rule
    Verify other bridges do not consider themselves as root-bridge
    7. Verify bridge_2 has a blocking port
    8. Change the priority of the port in bridge_1 which is connected to the blocking port in bridge_2
    to a priority value less than the default set
    9. Wait for topology to re-build.
    10. Verify bridge_2 has a blocking port and is not the same port as before
    """
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    device = dent_devices[0]

    dent = device.host_name
    loopback_ports = {}
    for idx, port in enumerate(device.links_dict[dent][0][:2] + device.links_dict[dent][1][:2]):
        loopback_ports[f'loopback_{idx+1}'] = port
    port_to_bridges = list(loopback_ports.values())
    bridges = {
        'bridge_1': port_to_bridges[:2],
        'bridge_2': port_to_bridges[2:]
    }
    wait_time = 40 if version == 'stp' else 20
    bridge_names = list(bridges.keys())
    hw_mac = ['22:AA:98:EA:D2:43', '44:0A:D1:68:4E:B9']

    # 1. Create 2 bridge entities 4 ports and set link up on them
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

    # 2. Enslave ports to bridges
    out = await IpLink.set(
        input_data=[{dent: [{'device': port, 'operstate': 'down'} for port in loopback_ports.values()]}])
    assert out[0][dent]['rc'] == 0, 'Failed setting links to state down'

    for bridge, ports in bridges.items():
        out = await IpLink.set(input_data=[{dent: [{'device': port, 'master': bridge} for port in ports]}])
        assert out[0][dent]['rc'] == 0, 'Failed enslaving ports to bridge'

    # 3. Change the MAC addresses for all bridges
    for bridge, mac in zip(bridge_names, hw_mac):
        rc, _ = await device.run_cmd(f'ifconfig {bridge} hw ether {mac}')
        assert rc == 0, 'Failed to change MAC address'

    # 4. Set link up on all participant ports, bridges
    out = await IpLink.set(
        input_data=[{dent: [{'device': port, 'operstate': 'up'} for port in loopback_ports.values()]}])
    assert out[0][dent]['rc'] == 0, 'Failed setting loopback links to state up'
    out = await IpLink.set(input_data=[{dent: [{'device': bridge, 'operstate': 'up'} for bridge in bridges]}])
    assert out[0][dent]['rc'] == 0, 'Failed setting bridge to state up'

    # 5. Wait until topology converges
    await asyncio.sleep(wait_time)

    # 6. Verify the bridge root is bridge_1 by the lowest MAC rule
    # verify other bridges do not consider themselves as root-bridge
    out = await Mstpctl.show(input_data=[{dent: [
        {'parameter': 'bridge',
         'bridge': bridge_names[0],
         'options': '-f json'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get bridge detail'
    assert out[0][dent]['parsed_output'][0]['root-port'] == '', f'Bridge { bridge_names[0]} is not a root bridge'
    # Other bridges do not consider themselves as root bridge
    out = await Mstpctl.show(input_data=[{dent: [
            {'parameter': 'bridge',
             'bridge': bridge_names[1],
             'options': '-f json'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get bridge detail'
    assert out[0][dent]['parsed_output'][0][
               'root-port'] != '', f'Bridge {bridge_names[1]} or {bridge_names[2]} is a root bridge'

    # 7. Verify bridge_2 has a blocking port
    out = await Mstpctl.show(input_data=[{dent: [
        {'parameter': 'portdetail',
         'bridge': bridge_names[1],
         'options': '-f json'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, f'Failed to get port detail of {bridge_names[1]}'
    ports_state = [port['state'] for port in out[0][dent]['parsed_output']]
    assert 'discarding' in ports_state, f'Bridge {bridge_names[1]} does not have a blocking port'
    for port in out[0][dent]['parsed_output']:
        if port['state'] == 'discarding':
            blocking_port = port['port']

    # 8. Change the priority of the port in bridge_1 which is connected to the blocking port in bridge_2 to
    # a priority value less than the default set
    out = await Mstpctl.set(input_data=[{dent: [
        {'parameter': 'treeportprio',
         'bridge': bridge_names[0],
         'port': list(loopback_ports.values())[1],
         'mstid': 0,
         'priority': 7}
        ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed setting bridge priority'
    # assert out[0][dent]['rc'] == 0, 'Failed to change priority of the bridge'  # RC = '-1', but command succeeds

    # 9. Wait for topology to re-build.
    await asyncio.sleep(wait_time)

    # 10. Verify bridge_2 has a blocking port and is not the same port as before
    out = await Mstpctl.show(input_data=[{dent: [
        {'parameter': 'portdetail',
         'bridge': bridge_names[1],
         'options': '-f json'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, f'Failed to get port detail of {bridge_names[1]}'
    ports_state = [port['state'] for port in out[0][dent]['parsed_output']]
    assert 'discarding' in ports_state, f'Bridge {bridge_names[1]} does have a blocking port'

    new_blocking_port = ''
    for port in out[0][dent]['parsed_output']:
        if port['state'] == 'discarding':
            new_blocking_port = port['port']
    assert new_blocking_port != blocking_port, f'Expected {blocking_port} != {new_blocking_port}'
