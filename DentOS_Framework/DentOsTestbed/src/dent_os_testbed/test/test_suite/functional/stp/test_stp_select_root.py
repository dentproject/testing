import asyncio
import pytest
from math import isclose

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.mstpctl.mstpctl import Mstpctl

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_get_traffic_stats,
    tgen_utils_stop_traffic
)
from dent_os_testbed.test.test_suite.functional.stp.stp_utils import (
    get_rand_mac,
    PortRole,
)

pytestmark = [
    pytest.mark.suite_functional_stp,
    pytest.mark.usefixtures('cleanup_bridges', 'cleanup_tgen', 'enable_mstpd'),
    pytest.mark.asyncio,
    pytest.mark.parametrize('version', ['stp', 'rstp']),
]


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
        out = await IpLink.set(input_data=[{dent: [
            {'device': bridge,
             'address': mac}]}])
        assert out[0][dent]['rc'] == 0, 'Failed to change MAC address'

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
    assert out[0][dent]['rc'] == 0, 'Failed to change priority of the bridge'

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
    out = await IpLink.set(input_data=[{dent: [{'device': port, 'operstate': 'down'} for port in loopback_ports.values()]}])
    assert out[0][dent]['rc'] == 0, 'Failed setting links to state down'

    for bridge, ports in bridges.items():
        out = await IpLink.set(input_data=[{dent: [{'device': port, 'master': bridge} for port in ports]}])
        assert out[0][dent]['rc'] == 0, 'Failed enslaving ports to bridge'

    # 3. Change the MAC addresses for all bridges
    for bridge, mac in zip(bridge_names, hw_mac):
        out = await IpLink.set(input_data=[{dent: [
            {'device': bridge,
             'address': mac}]}])
        assert out[0][dent]['rc'] == 0, 'Failed to change MAC address'

    # 4. Set link up on all participant ports, bridges
    out = await IpLink.set(input_data=[{dent: [{'device': port, 'operstate': 'up'} for port in loopback_ports.values()]}])
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
    assert out[0][dent]['parsed_output'][0]['root-port'] != '', f'Bridge {bridge_names[1]} is a root bridge'

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
        ]}])
    assert out[0][dent]['rc'] == 0, 'Failed setting bridge priority'

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


async def test_stp_root_bridge_based_on_mac(testbed, version):
    """
    Test Name: test_stp_root_bridge
    Test Suite: suite_functional_stp
    Test Overview: Verify root bridge with lowest MAC
    Test Procedure:
    1. Create bridge entity with STP enabled
    2. Enslave port to the bridge
    3. Change the MAC addresses the bridge as follows 66:XX:XX:XX:XX:XX
    4. Set link up on all participant ports
    5. Transmit BDPU with root-id=bridge-id=00:44:XX:XX:XX:XX" wait until topology fully converges
    6. Verify the bridge is not a root bridge
    7. Change the highest MAC bridge to a MAC with lower value then the root bridge.
    8. Verify the bridge is a root bridge
    """
    num_ports = 4
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], num_ports)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_device = dent_devices[0]
    dent = dent_device.host_name
    tg_ports = tgen_dev.links_dict[dent][0][:num_ports]
    ports = tgen_dev.links_dict[dent][1][:num_ports]
    bridge = 'br0'
    root_mac = get_rand_mac('00:44:XX:XX:XX:XX')

    # 1.  Create bridge entity with STP enabled
    out = await IpLink.add(input_data=[{dent: [
        {'device': bridge, 'type': 'bridge', 'stp_state': 1}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bridge'

    # 2.Enslave port to the bridge
    out = await IpLink.set(input_data=[{dent: [
        {'device': port,
         'master': bridge} for port in ports]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # 3. Change the MAC addresses for all bridges
    out = await IpLink.set(input_data=[{dent: [
        {'device': bridge,
         'address': '66:DA:78:12:DC:68'}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to change MAC address'

    out = await Mstpctl.add(input_data=[{dent: [{'bridge': bridge}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bridge'

    out = await Mstpctl.set(input_data=[{dent: [
        {'parameter': 'forcevers', 'bridge': bridge, 'version': version}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to enable stp/rstp'

    # 4. Set link up on all participant ports
    out = await IpLink.set(input_data=[{dent: [
        {'device': port,
         'operstate': 'up'} for port in ports]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    out = await IpLink.set(input_data=[{dent: [
        {'device': bridge,
         'operstate': 'up'}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set bridge to state UP'

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': f'1.1.1.{idx}', 'gw': '1.1.1.5', 'plen': 24}
        for idx, port in enumerate(tg_ports, start=1)
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    # 5. Transmit BDPU with root-id=bridge-id=00:44:XX:XX:XX:XX" wait ~40 seconds until topology fully converges
    stp = {
        'rootIdentifier': f'8000{root_mac.replace(":", "")}',
        'bridgeIdentifier': f'8000{root_mac.replace(":", "")}',
        'portIdentifier': '8002',
        'messageAge': 1 << 8,
        'frameSize': 100,
    }
    rstp = {
        'agreement': 1,
        'forwarding': 1,
        'learning': 1,
        'portRole': PortRole.DESIGNATED.value,
        'proposal': 1,
        'protocol': '0027',
    } if version == 'rstp' else {}
    streams = {
        # BPDU stream with higher prio than bridge from port#0
        f'{ports[0]} {version}': {
            'type': 'bpdu',
            'version': version,
            'ep_source': ports[0],
            'rate': 1,  # pps
            'allowSelfDestined': True,
            'srcMac': root_mac,
            **stp,
            **rstp,
        }
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(40)
    # don't stop

    # 6. Verify the bridge is not a root bridge
    out = await Mstpctl.show(input_data=[{dent: [
        {'parameter': 'bridge',
         'bridge': bridge,
         'options': '-f json'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get bridge detail'
    assert out[0][dent]['parsed_output'][0]['root-port'] != '', f'Bridge { bridge} is not a root bridge'

    # 7. Change the highest MAC bridge to a MAC with lower value then the root bridge.
    out = await IpLink.set(input_data=[{dent: [
        {'device': bridge,
         'address': get_rand_mac('00:22:XX:XX:XX:XX')}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to change MAC address'

    # 8. Verify the bridge is a root bridge
    out = await Mstpctl.show(input_data=[{dent: [
        {'parameter': 'bridge',
         'bridge': bridge,
         'options': '-f json'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get bridge detail'
    assert out[0][dent]['parsed_output'][0]['root-port'] == '', f'Bridge { bridge} is not a root bridge'


async def test_stp_select_root_port_on_cost(testbed, version):
    """
    Test Name: test_stp_select_root_port_on_cost
    Test Suite: suite_functional_stp
    Test Overview: Verify root port slection based on port cost
    Test Procedure:
    1. Create bridge entity with STP enabled
    2. Enslave port to the bridge
    3. Change the MAC addresses the bridge
    4. Set link up on all participant ports, bridge
    5. Create streams. Send traffic
    6. Verify port 2 state is blocking
    7. Verify traffic is forwarded to port 1 and that port 2 doesn't receive any traffic
    8. Change the cost of the blocked port to a cost less of the default set
    9. Transmit the traffic
    10. Verify traffic is forwarded to port 2 and that port 1 doesn't receive any traffic
    """
    num_ports = 4
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], num_ports)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_device = dent_devices[0]
    dent = dent_device.host_name
    tg_ports = tgen_dev.links_dict[dent][0][:num_ports]
    ports = tgen_dev.links_dict[dent][1][:num_ports]
    bridge = 'br0'
    root_mac = get_rand_mac('00:44:XX:XX:XX:XX')
    rand_mac = get_rand_mac('00:66:XX:XX:XX:XX')
    convergence_time_s = 40 if version == 'stp' else 20
    rate_bps = 300_000_000  # 300Mbps
    traffic = 'data traffic'
    tolerance = 0.05
    newCost = 1 if version == 'stp' else 16

    # 1. Create bridge entity with STP enabled
    out = await IpLink.add(input_data=[{dent: [
        {'device': bridge, 'type': 'bridge', 'stp_state': 1}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bridge'

    # 2. Enslave port to the bridge
    out = await IpLink.set(input_data=[{dent: [
        {'device': port,
         'master': bridge} for port in ports]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # 3. Change the MAC addresses the bridge
    out = await IpLink.set(input_data=[{dent: [
        {'device': bridge,
         'address': '22:BB:4D:85:E7:098'}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to change MAC address'

    out = await Mstpctl.add(input_data=[{dent: [{'bridge': bridge}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bridge'

    out = await Mstpctl.set(input_data=[{dent: [
        {'parameter': 'forcevers', 'bridge': bridge, 'version': version}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to enable stp/rstp'

    # 4. Set link up on all participant ports, bridge
    out = await IpLink.set(input_data=[{dent: [
        {'device': port,
         'operstate': 'up'} for port in ports]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    out = await IpLink.set(input_data=[{dent: [
        {'device': bridge,
         'operstate': 'up'}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set bridge to state UP'

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': f'1.1.1.{idx}', 'gw': '1.1.1.5', 'plen': 24}
        for idx, port in enumerate(tg_ports, start=1)
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    # 5. Setup streams
    stp = {
        'rootIdentifier': f'8000{root_mac.replace(":", "")}',
        'bridgeIdentifier': f'8000{root_mac.replace(":", "")}',
        'portIdentifier': '8002',
        'messageAge': 1 << 8,
        'frameSize': 100,
    }
    rstp = {
        'agreement': 1,
        'forwarding': 1,
        'learning': 1,
        'portRole': PortRole.DESIGNATED.value,
        'proposal': 1,
        'protocol': '0027',
    } if version == 'rstp' else {}
    streams = {
        f'{ports[0]} {version}': {
            'type': 'bpdu',
            'version': version,
            'ep_source': ports[0],
            'ep_destination': ports[0],
            'rate': 1,  # pps
            'allowSelfDestined': True,
            'srcMac': root_mac,
            **stp,
            **rstp,
        },
        f'{ports[1]} {version}': {
            'type': 'bpdu',
            'version': version,
            'ep_source': ports[1],
            'ep_destination': ports[1],
            'rate': 1,  # pps
            'allowSelfDestined': True,
            'srcMac': rand_mac,
            **stp,
            **rstp,
            'bridgeIdentifier': f'8000{rand_mac.replace(":", "")}',
        },
        traffic: {
            'type': 'ethernet',
            'ep_source': ports[2],
            'frame_rate_type': 'bps_rate',
            'srcMac': get_rand_mac('00:11:XX:XX:XX:XX'),
            'rate': rate_bps,
        },
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)
    await tgen_utils_start_traffic(tgen_dev)
    # don't stop
    await asyncio.sleep(convergence_time_s)

    # 6. Verify port 2 state is blocking
    out = await Mstpctl.show(input_data=[{dent: [
        {'parameter': 'portdetail',
         'bridge': bridge,
         'options': '-f json'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get port detail of '
    ports_state = [bond['state'] for bond in out[0][dent]['parsed_output']]
    assert 'discarding' == ports_state[1], 'Bridge  does not have a blocking port'

    # 7. Verify traffic is forwarded to port 1 and that port 2 doesn't receive any traffic
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        if row['Traffic Item'] == traffic and row['Rx Port'] == tg_ports[1]:
            err_msg = f'Expected 0.0 got : {float(row["Rx Rate (Mbps)"])}'
            assert isclose(float(row['Rx Rate (Mbps)']), 0.0, abs_tol=tolerance), err_msg
        if row['Traffic Item'] == traffic and row['Rx Port'] == tg_ports[0]:
            err_msg = f'Expected 300 got : {float(row["Rx Rate (Mbps)"])}'
            assert isclose(float(row['Rx Rate (Mbps)']), 300, rel_tol=tolerance), err_msg
    await tgen_utils_stop_traffic(tgen_dev)

    # 8. Change the cost of the blocked port to a cost less of the default set
    out = await Mstpctl.set(input_data=[{dent: [
        {'parameter': 'portpathcost',
         'bridge': bridge,
         'port': ports[1],
         'priority': newCost}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to change priority of the bridge'
    await asyncio.sleep(convergence_time_s)

    out = await Mstpctl.show(input_data=[{dent: [
        {'parameter': 'portdetail',
         'bridge': bridge,
         'options': '-f json'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get port detail of '
    ports_state = [bond['state'] for bond in out[0][dent]['parsed_output']]
    assert 'discarding' != ports_state[1], 'Bridge  does not have a blocking port'

    # 9. Transmit the traffic
    await tgen_utils_start_traffic(tgen_dev)
    # don't stop
    await asyncio.sleep(convergence_time_s)

    # 10. Verify traffic is forwarded to port 2 and that port 1 doesn't receive any traffic
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        if row['Traffic Item'] == traffic and row['Rx Port'] == tg_ports[0]:
            err_msg = f'Expected 0.0 got : {float(row["Rx Rate (Mbps)"])}'
            assert isclose(float(row['Rx Rate (Mbps)']), 0.0, abs_tol=tolerance), err_msg
        if row['Traffic Item'] == traffic and row['Rx Port'] == tg_ports[1]:
            err_msg = f'Expected 300 got : {float(row["Rx Rate (Mbps)"])}'
            assert isclose(float(row['Rx Rate (Mbps)']), 300, rel_tol=tolerance), err_msg
