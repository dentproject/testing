import asyncio
import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.mstpctl.mstpctl import Mstpctl

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
)


pytestmark = [
    pytest.mark.suite_functional_stp,
    pytest.mark.usefixtures('cleanup_bridges', 'enable_mstpd'),
    pytest.mark.asyncio,
]


async def get_port_states(dent, bridges):
    stp_ports = {
        'direct_link': None,
        'indirect_link': None,
        'blocked_link': None
    }
    for br in bridges:
        out = await Mstpctl.show(input_data=[{dent: [{
            'bridge': br,
            'parameter': 'portdetail',
            'options': '-f json'}]}], parse_output=True)
        port_state = [port['state'] for port in out[0][dent]['parsed_output']]
        if 'forwarding' in port_state and 'discarding' in port_state:
            stp_ports['blocked_link'] = out[0][dent]['parsed_output'][port_state.index('discarding')]['port']
            stp_ports['direct_link'] = out[0][dent]['parsed_output'][port_state.index(
                'forwarding')]['port']
        port_role = [port['role'] for port in out[0][dent]['parsed_output']]
        if 'Root' in port_role and 'Designated' in port_role:
            stp_ports['indirect_link'] = out[0][dent]['parsed_output'][port_role.index('Root')]['port']
    return stp_ports


@pytest.mark.parametrize('version', ['stp', 'rstp'])
async def test_stp_topology_convergence_with_down_link(testbed, version):
    """
    Test Name: STP/RSTP selecting root bridge
    Test Suite: suite_functional_stp
    Test Overview: Test root bridge selection based on bridge priority
    Test Procedure:
    1. Create 3 bridge entities bonds and set link up on them
    2. Enslave ports to bridges
    3. Set link up on all participant ports, bridges
    4. Bring down the indirect link; verify the blocking port comes to forwarding after 51 seconds
    5. Bring back the indirect link and wait for the topology to re-converge.
    6. Bring down the direct link. Verify the blocking port comes to forwarding after 31 seconds
    7. Add one tgen port to some bridge
    8. Verify the port connected to tgen port transitions into forwarding state after 31 seconds

    """
    num_ports = 1
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], num_ports)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    device = dent_devices[0]
    dent = device.host_name
    loopback_ports = {}
    for idx, port in enumerate(device.links_dict[dent][0] + device.links_dict[dent][1]):
        loopback_ports[f'loopback_{idx+1}'] = port
    port_to_bridges = list(loopback_ports.values())
    dut_ports = tgen_dev.links_dict[dent][1][:num_ports]
    tg_ports = tgen_dev.links_dict[dent][0][:num_ports]

    bridges = {
        'bridge_1': port_to_bridges[:2],
        'bridge_2': port_to_bridges[2:4],
        'bridge_3': port_to_bridges[4:]
    }
    edge_and_direct_timeout = 31
    indirect_timeout = 51
    wait_time = 40 if version == 'stp' else 20
    bridge_names = list(bridges.keys())

    # 1. Create 3 bridge entities bonds and set link up on them
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

    # 3. Set link up on all participant ports, bridges
    out = await IpLink.set(input_data=[{dent: [{
        'device': port,
        'operstate': 'up'} for port in loopback_ports.values()]}])
    assert out[0][dent]['rc'] == 0, 'Failed setting loopback links to state up'
    out = await IpLink.set(input_data=[{dent: [{'device': bridge, 'operstate': 'up'} for bridge in bridges]}])
    assert out[0][dent]['rc'] == 0, 'Failed setting bridge to state up'

    await asyncio.sleep(wait_time)
    stp_ports = await get_port_states(dent, bridge_names)

    # 4. Bring down the indirect link. Verify the blocking port comes to forwarding after 51 seconds
    out = await IpLink.set(input_data=[{dent: [{
        'device': stp_ports['indirect_link'],
        'operstate': 'down'}]}])
    assert out[0][dent]['rc'] == 0, 'Failed setting interface to state down'
    await asyncio.sleep(indirect_timeout)

    out = await IpLink.show(input_data=[{dent: [
        {'device': stp_ports['blocked_link'],
         'cmd_options': '-j -d'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get port detail'
    err_msg = f'Port : {stp_ports["blocked_link"]} has to be in forwarding state'
    assert out[0][dent]['parsed_output'][0]['linkinfo']['info_slave_data']['state'] == 'forwarding', err_msg

    # 5. Bring back the indirect link and wait for the topology to re-converge.
    # 6. Bring down the direct link. Verify the blocking port comes to forwarding after 31 seconds

    out = await IpLink.set(input_data=[{
        dent: [
            {'device': stp_ports['direct_link'], 'operstate': 'down'},
            {'device': stp_ports['indirect_link'], 'operstate': 'up'},
        ]}
    ])
    assert out[0][dent]['rc'] == 0, 'Failed changing interface operstate'

    out = await IpLink.show(input_data=[{dent: [
        {'device': stp_ports['blocked_link'],
         'cmd_options': '-j -d'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to retrieve interface info'
    err_msg = f'Port : {stp_ports["blocked_link"]} has to be in forwarding state'
    assert out[0][dent]['parsed_output'][0]['linkinfo']['info_slave_data']['state'] == 'forwarding', err_msg

    out = await IpLink.set(input_data=[{dent: [{
        'device': stp_ports['direct_link'],
        'operstate': 'up'}]}])
    assert out[0][dent]['rc'] == 0, 'Failed setting interface to state up'

    await asyncio.sleep(edge_and_direct_timeout)

    # 7. Add one tgen port to some bridge
    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': f'1.1.1.{idx}', 'gw': '1.1.1.5', 'plen': 24}
        for idx, port in enumerate(tg_ports, start=1)
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)
    out = await IpLink.set(input_data=[{dent: [{
        'device': dut_ports[0],
        'master': bridge_names[1],
        }]}])
    assert out[0][dent]['rc'] == 0, 'Failed enslaving interface to bridge'

    out = await IpLink.set(input_data=[{dent: [{
        'device': dut_ports[0],
        'operstate': 'up'
    }]}])
    assert out[0][dent]['rc'] == 0, 'Failed setting interface to state up'

    # 8. Verify the port connected to tgen port transitions into forwarding state after 31 seconds
    await asyncio.sleep(indirect_timeout)
    out = await IpLink.show(input_data=[{dent: [
        {'device': dut_ports[0],
         'cmd_options': '-j -d'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to retrieve interface info'
    err_msg = f'Port : {dut_ports[0]} has to be in forwarding state'
    assert out[0][dent]['parsed_output'][0]['linkinfo']['info_slave_data']['state'] == 'forwarding', err_msg
