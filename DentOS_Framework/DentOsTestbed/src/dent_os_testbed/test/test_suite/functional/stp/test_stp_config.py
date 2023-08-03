import asyncio
import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.bridge.bridge_link import BridgeLink

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_clear_traffic_items,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
)

from dent_os_testbed.test.test_suite.functional.stp.stp_utils import (
    get_rand_mac,
    poll,
)


pytestmark = [
    pytest.mark.suite_functional_stp,
    pytest.mark.usefixtures('cleanup_bridges', 'cleanup_tgen', 'disable_mstpd'),
    pytest.mark.asyncio,
]


async def get_topo_state(dent, bridge_members):
    """
    bridge_members:
    {
        bridge: [port, port, ...],
        ...
    }
    """
    ports = [port for members in bridge_members.values() for port in members]
    bridges = [bridge for bridge in bridge_members]

    out = await IpLink.show(input_data=[{dent: [{'cmd_options': '-d -j'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    port_state = {
        info['ifname']: info['linkinfo'].get('info_slave_data')
        for info in out[0][dent]['parsed_output']
        if info['ifname'] in ports
    }
    bridge_state = {
        info['ifname']: info['linkinfo'].get('info_data')
        for info in out[0][dent]['parsed_output']
        if info['ifname'] in bridges
    }

    root_port = {}
    for bridge, members in bridge_members.items():
        for port in members:
            if bridge_state[bridge]['root_port'] == int(port_state[port]['no'], base=16):
                root_port[bridge] = port
                break
        else:
            root_port[bridge] = None

    root_bridge = [bridge for bridge, port in root_port.items() if port is None]
    assert len(root_bridge) == 1, 'Expected only 1 root bridge'

    return {
        'root_bridge': root_bridge[0],
        'root_port': root_port,
        'bridge_state': bridge_state,
        'port_state': port_state,
    }


async def test_stp_bpdu_guard(testbed):
    """
    Test Name: test_stp_bpdu_guard
    Test Suite: suite_functional_stp
    Test Overview: Verify BDPU guard basic functionality works as expected
    Test Procedure:
    1. Add bridge
    2. Enslave ports
    3. Setup BPDU stream
    4. Enable BDPU guard
    5. Send BDPU traffic
    6. Verify the port becomes disabled/discarding
    """
    num_ports = 1
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], num_ports)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_device = dent_devices[0]
    dent = dent_device.host_name
    tg_ports = tgen_dev.links_dict[dent][0][:num_ports]
    port = tgen_dev.links_dict[dent][1][0]
    bridge = 'br0'
    bridge_mac = get_rand_mac('22:XX:XX:XX:XX:XX')
    root_mac = get_rand_mac('44:XX:XX:XX:XX:XX')
    convergence_time_s = 40

    # 1. Add bridge
    out = await IpLink.add(input_data=[{dent: [
        {'device': bridge, 'type': 'bridge', 'stp_state': 1}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bridge'

    # 2. Enslave ports
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up', 'master': bridge}
    ] + [
        {'device': bridge, 'operstate': 'up', 'address': bridge_mac}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': tg_port, 'ip': f'1.1.1.{idx}', 'gw': '1.1.1.5', 'plen': 24}
        for idx, tg_port in enumerate(tg_ports, start=1)
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, [port], dev_groups)

    # 3. Setup BPDU stream
    stp = {
        'rootIdentifier': f'8000{root_mac.replace(":", "")}',
        'bridgeIdentifier': f'8000{root_mac.replace(":", "")}',
        'portIdentifier': '8002',
        'messageAge': 1 << 8,
        'frameSize': 100,
    }
    streams = {
        f'{port} stp': {
            'type': 'bpdu',
            'version': 'stp',
            'ep_source': port,
            'ep_destination': port,
            'rate': 1,  # pps
            'allowSelfDestined': True,
            'srcMac': root_mac,
            **stp,
        },
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # 4. Enable BDPU guard
    out = await BridgeLink.set(input_data=[{dent: [
        {'guard': True, 'device': port}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to enable bpdu guard'

    # 5. Send BDPU traffic
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(convergence_time_s)
    # don't stop

    # 6. Verify the port becomes disabled/discarding
    out = await BridgeLink.show(input_data=[{dent: [
        {'device': port, 'options': '-j'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get port detail'

    assert out[0][dent]['parsed_output'][0]['state'] == 'disabled', \
        f'Expected port {port} state to be \'disabled\''


async def test_stp_forward_delay(testbed):
    """
    Test Name: test_stp_forward_delay
    Test Suite: suite_functional_stp
    Test Overview: Verify BDPU filter basic functionality works as expected
    Test Procedure:
    1. Add bridges
    2. Create ring topology
    3. Wait until topology converges
    4. Bring down the indirect link
       - Verify the blocking port becomes forwarding
    5. Set forward delay and bring back the indirect link
       - Verify topology is re-build with the same settings as initially
    """
    poll_timeout_s = 40 * 2  # convergence time + tolerance
    num_loopbacks = 3
    forward_delay = 400  # 4s
    max_age = 600  # 6s

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 0)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_device = dent_devices[0]
    dent = dent_device.host_name

    # [[A0, B0, ...], [A1, B1, ...]]
    loopbacks = dent_device.links_dict.get(dent, [])[:2]
    # [(A0, A1), (B0, B1), ...]
    loopbacks = list(zip(*[iter([port for link in zip(*loopbacks) for port in link])]*2))[:num_loopbacks]
    if len(loopbacks) < num_loopbacks:
        pytest.skip(f'Dent {dent_device} does not have enough loopback connections {loopbacks}')

    bridges = [f'br{idx}' for idx in range(num_loopbacks)]
    loopback_ports = [port for link in loopbacks for port in link]
    loopback_ports.append(loopback_ports.pop(0))
    # {'br0': [A1, B0], 'br1': [B1, C0], ...}
    bridge_members = {
        bridge: [port for port in link]
        for bridge, link in zip(bridges, zip(*[iter(loopback_ports)]*2))
    }

    # 1. Add bridges
    out = await IpLink.add(input_data=[{dent: [
        {'device': bridge, 'type': 'bridge', 'stp_state': 1}
        for bridge in bridges
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bridge'

    # 2. Create ring topology
    """
          br0         br1
        A1   B0 --- B1   C0
         |               |
         +--- A0   C1 ---+
                br2
    """
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up', 'master': bridge}
        for bridge, members in bridge_members.items() for port in members
    ] + [
        {'device': bridge, 'operstate': 'up'}
        for bridge in bridges
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # 3. Wait until topology converges
    """ Example:
    br2 is the root port
    A1 is the root port for br0
    C0 is the root port for br1
    B1 is blocked due to STP
          br0         br1
       *A1*  B0 --- XX  *C0*
         |               |
         +--- A0   C1 ---+
               *br2*
    """
    async def get_topo_with_blocked_port(dent, bridge_members):
        topo = await get_topo_state(dent, bridge_members)

        blocked_port = [port for port, state in topo['port_state'].items()
                        if state['state'] == 'blocking']
        assert len(blocked_port) == 1, 'Expected only 1 blocked port'
        blocked_port = blocked_port[0]
        assert all([state['state'] == 'forwarding' for port, state in topo['port_state'].items()
                    if port != blocked_port]), \
            'Expected ports to be \'forwarding\''
        return {
            **topo,
            'blocked_port': blocked_port,
        }

    await poll(dent_device, get_topo_with_blocked_port, timeout=poll_timeout_s,
               dent=dent, bridge_members=bridge_members)
    topo = await get_topo_with_blocked_port(dent, bridge_members)

    # 4. Bring down the indirect link
    """
    Set A1 down so that:
    B0 becomes root port for br0
    B1 is no longer blocking
    br2 is still the root bridge
          br0         br1
        XX  *B0*--- B1  *C0*
         |               |
         +--- A0   C1 ---+
               *br2*
    """
    other_bridge = [
        bridge for bridge, members in bridge_members.items()
        if bridge != topo['root_bridge'] and topo['blocked_port'] not in members
    ][0]

    out = await IpLink.set(input_data=[{dent: [
        {'device': topo['root_port'][other_bridge], 'operstate': 'down'}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state DOWN'

    # Verify the blocking port becomes forwarding
    async def check_new_topo(dent, bridge_members, old_topo):
        new_topo = await get_topo_state(dent, bridge_members)

        assert new_topo['root_bridge'] == old_topo['root_bridge'], \
            'Did not expect root bridge to change'
        assert new_topo['port_state'][old_topo['blocked_port']]['state'] == 'forwarding', \
            f'Port {old_topo["blocked_port"]} should be \'forwarding\''

    await poll(dent_device, check_new_topo, timeout=poll_timeout_s,
               dent=dent, bridge_members=bridge_members, old_topo=topo)

    # 5. Set forward delay and bring back the indirect link
    out = await IpLink.set(input_data=[{dent: [
        {'device': topo['root_bridge'],
         'forward_delay': forward_delay,
         'max_age': max_age},
        {'device': topo['root_port'][other_bridge],
         'operstate': 'up'}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to update bridge parameters'

    # Verify topology is re-build with the same settings as initially
    async def check_new_topo(dent, bridge_members, old_topo):
        new_topo = await get_topo_state(dent, bridge_members)

        new_blocked_port = [port for port, state in new_topo['port_state'].items() if state['state'] == 'blocking']
        assert len(new_blocked_port) == 1, 'Expected only 1 blocked port'
        new_blocked_port = new_blocked_port[0]
        assert new_blocked_port == old_topo['blocked_port'], \
            f'Expected {old_topo["blocked_port"]} to be blocked, not {new_blocked_port}'
        assert new_topo['root_bridge'] == old_topo['root_bridge'], \
            'Did not expect root bridge to change'
        assert all([state['state'] == 'forwarding' for port, state in new_topo['port_state'].items()
                    if port != new_blocked_port]), \
            'Expected ports to be \'forwarding\''

    await poll(dent_device, check_new_topo, timeout=poll_timeout_s / 2, interval=5,
               dent=dent, bridge_members=bridge_members, old_topo=topo)


async def test_stp_max_age(testbed):
    """
    Test Name: test_stp_max_age
    Test Suite: suite_functional_stp
    Test Overview: Verify BDPU filter basic functionality works as expected
    Test Procedure:
    1. Add bridge
    2. Enslave ports
    3. Setup streams:
       - BPDU stream with higher prio than bridge from port#0
       - BPDU stream with higher prio than bridge from port#1
    4. Send traffic
    5. Verify port state becomes forwarding after 20s
    6. Change BPDU stream max age to 6
    7. Verify port state becomes forwarding after 6s
    """
    num_ports = 3
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], num_ports)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_device = dent_devices[0]
    dent = dent_device.host_name
    tg_ports = tgen_dev.links_dict[dent][0][:num_ports]
    ports = tgen_dev.links_dict[dent][1][:num_ports]
    bridge = 'br0'
    bridge_mac = get_rand_mac('22:XX:XX:XX:XX:XX')
    root_mac = get_rand_mac('02:XX:XX:XX:XX:XX')
    rand_mac = get_rand_mac('04:XX:XX:XX:XX:XX')
    blocking_time_s = 30
    max_age_s = 6

    # 1. Add bridge
    out = await IpLink.add(input_data=[{dent: [
        {'device': bridge, 'type': 'bridge', 'stp_state': 1}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bridge'

    # 2. Enslave ports
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up', 'master': bridge}
        for port in ports
    ] + [
        {'device': bridge, 'operstate': 'up', 'address': bridge_mac}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': tg_port, 'ip': f'1.1.1.{idx}', 'gw': '1.1.1.5', 'plen': 24}
        for idx, tg_port in enumerate(tg_ports, start=1)
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    # 3. Setup streams:
    stp = {
        'rootIdentifier': f'8000{root_mac.replace(":", "")}',
        'portIdentifier': '8002',
        'messageAge': 1 << 8,
        'frameSize': 100,
    }
    streams = {
        # BPDU stream with higher prio than bridge from port#0
        f'{ports[0]} stp': {
            'type': 'bpdu',
            'version': 'stp',
            'ep_source': ports[0],
            'ep_destination': ports[0],
            'rate': 1,  # pps
            'allowSelfDestined': True,
            'srcMac': root_mac,
            **stp,
            'bridgeIdentifier': f'8000{root_mac.replace(":", "")}',
        },
        # BPDU stream with higher prio than bridge from port#1
        f'{ports[1]} stp': {
            'type': 'bpdu',
            'version': 'stp',
            'ep_source': ports[1],
            'ep_destination': ports[1],
            'rate': 1,  # pps
            'allowSelfDestined': True,
            'srcMac': rand_mac,
            **stp,
            'bridgeIdentifier': f'8000{rand_mac.replace(":", "")}',
        },
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # 4. Send traffic
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(20)
    # don't stop

    out = await IpLink.show(input_data=[{dent: [
        {'cmd_options': '-j -d'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get port detail'
    device_state = {
        link['ifname']: link['linkinfo'].get('info_slave_data') or link['linkinfo'].get('info_data')
        for link in out[0][dent]['parsed_output']
        if link['ifname'] in ports + [bridge]
    }
    assert device_state[bridge]['root_port'] != 0, 'Bridge should not be root'
    assert device_state[ports[1]]['state'] == 'blocking', 'Port should be blocking'

    # 5. Verify port state becomes forwarding after 20s
    await tgen_utils_stop_traffic(tgen_dev)

    async def check_that_port_is_not_blocking(dent, port):
        out = await IpLink.show(input_data=[{dent: [
            {'device': port, 'cmd_options': '-j -d'}
        ]}], parse_output=True)
        assert out[0][dent]['rc'] == 0, 'Failed to get port detail'
        assert out[0][dent]['parsed_output'][0]['linkinfo']['info_slave_data']['state'] != 'blocking', \
            f'Port {port} should not be blocked'

    await poll(dent_device, check_that_port_is_not_blocking, timeout=blocking_time_s,
               interval=5, dent=dent, port=ports[1])

    # 6. Change BPDU stream max age to 6
    await tgen_utils_clear_traffic_items(tgen_dev)

    stp.update({'maxAge': max_age_s << 8})
    [traffic_item.update(stp) for traffic_item in streams.values()]
    await tgen_utils_setup_streams(tgen_dev, None, streams)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(20)

    out = await IpLink.show(input_data=[{dent: [
        {'cmd_options': '-j -d'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get port detail'
    device_state = {
        link['ifname']: link['linkinfo'].get('info_slave_data') or link['linkinfo'].get('info_data')
        for link in out[0][dent]['parsed_output']
        if link['ifname'] in ports + [bridge]
    }
    assert device_state[bridge]['root_port'] != 0, 'Bridge should not be root'
    assert device_state[ports[1]]['state'] == 'blocking', 'Port should be blocking'

    # 7. Verify port state becomes forwarding after 6s
    await tgen_utils_stop_traffic(tgen_dev)

    await poll(dent_device, check_that_port_is_not_blocking, timeout=blocking_time_s / 2,
               interval=2, dent=dent, port=ports[1])


async def test_stp_root_guard(testbed):
    """
    Test Name: test_stp_root_guard
    Test Suite: suite_functional_stp
    Test Overview: Verify BDPU guard basic functionality works as expected
    Test Procedure:
    1. Add bridge
    2. Enslave ports
    3. Setup BPDU stream
    4. Send traffic
    5. Verify port is root
    6. Enable root guard (restrict port role)
    7. Verify port is no longer root
    """
    num_ports = 1
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], num_ports)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_device = dent_devices[0]
    dent = dent_device.host_name
    tg_ports = tgen_dev.links_dict[dent][0][:num_ports]
    port = tgen_dev.links_dict[dent][1][0]
    bridge = 'br0'
    bridge_mac = get_rand_mac('22:XX:XX:XX:XX:XX')
    root_mac = get_rand_mac('02:XX:XX:XX:XX:XX')
    convergence_time_s = 40

    # 1. Add bridge
    out = await IpLink.add(input_data=[{dent: [
        {'device': bridge, 'type': 'bridge', 'stp_state': 1}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bridge'

    # 2. Enslave ports
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up', 'master': bridge}
    ] + [
        {'device': bridge, 'operstate': 'up', 'address': bridge_mac}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': tg_port, 'ip': f'1.1.1.{idx}', 'gw': '1.1.1.5', 'plen': 24}
        for idx, tg_port in enumerate(tg_ports, start=1)
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, [port], dev_groups)

    # 3. Setup BPDU stream
    stp = {
        'rootIdentifier': f'8000{root_mac.replace(":", "")}',
        'bridgeIdentifier': f'8000{root_mac.replace(":", "")}',
        'portIdentifier': '8002',
        'messageAge': 1 << 8,
        'frameSize': 100,
    }
    streams = {
        f'{port} stp': {
            'type': 'bpdu',
            'version': 'stp',
            'ep_source': port,
            'ep_destination': port,
            'rate': 1,  # pps
            'allowSelfDestined': True,
            'srcMac': root_mac,
            **stp,
        },
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # 4. Send traffic
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(convergence_time_s)
    # don't stop

    # 5. Verify port is root
    out = await IpLink.show(input_data=[{dent: [
        {'device': bridge, 'cmd_options': '-j -d'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get port detail'

    assert out[0][dent]['parsed_output'][0]['linkinfo']['info_data']['root_port'] != 0, \
        f'Expected port {port} to be the root port'

    # 6. Enable root guard (restrict port role)
    out = await BridgeLink.set(input_data=[{dent: [
        {'device': port, 'root_block': True}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to get enable root guard'
    await asyncio.sleep(convergence_time_s)

    # 7. Verify port is no longer root
    out = await IpLink.show(input_data=[{dent: [
        {'device': bridge, 'cmd_options': '-j -d'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get port detail'

    assert out[0][dent]['parsed_output'][0]['linkinfo']['info_data']['root_port'] == 0, \
        f'Expected port {port} to be the root port'
