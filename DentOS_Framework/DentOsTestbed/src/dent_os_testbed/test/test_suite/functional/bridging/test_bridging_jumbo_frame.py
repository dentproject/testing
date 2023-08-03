import pytest
import asyncio

from dent_os_testbed.lib.bridge.bridge_fdb import BridgeFdb
from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_get_loss
)

pytestmark = [
    pytest.mark.suite_functional_bridging,
    pytest.mark.asyncio,
    pytest.mark.usefixtures('cleanup_bridges', 'cleanup_tgen', 'cleanup_mtu')
]


MAX_MTU = 9000


@pytest.mark.parametrize('mtu', [1510, 8998, 9000, 9002])
async def test_bridging_jumbo_frame_size(testbed, mtu):
    """
    Test Name: test_bridging_frame_max_size
    Test Suite: suite_functional_bridging
    Test Overview: Verifying that jumbo frames of max size are learned and forwarded.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1. Add bridge
    2. Enslave ports
    3. Set jumbo frame MTU size (1510|8998|9000|9002) on ports
    4. Set streams frameSize (1510|8998|9000|9002)
    5. Send traffic
    6. Verify that traffic is forwarded (or dropped if packet size is > 9000)
    7. Verify that addresses are learned (or not learned if packet size is > 9000)
    """
    bridge = 'br0'
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]
    traffic_duration = 10
    should_fail = mtu > MAX_MTU

    # 1. Add bridge
    out = await IpLink.add(input_data=[{dent: [
        {'device': bridge, 'type': 'bridge'}
    ]}])
    assert out[0][dent]['rc'] == 0, f'Verify that bridge created.\n{out}'

    # 2. Enslave ports
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'master': bridge, 'operstate': 'up'} for port in ports
    ] + [
        {'device': bridge, 'operstate': 'up'}
    ]}])
    assert out[0][dent]['rc'] == 0, \
        f'Verify that bridge is set to UP and ports are enslaved.\n{out}'

    # 3. Set jumbo frame MTU size (1510|8998|9000|9002) on ports
    # (only MTU with even size is supported)
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'mtu': mtu} for port in ports
    ]}])
    if should_fail:
        assert out[0][dent]['rc'] != 0, \
            f'Verify that bridge failed to set jumbo frame size to {mtu}.\n{out}'
    else:
        assert out[0][dent]['rc'] == 0, \
            f'Verify that bridge jumbo frame size set to {mtu}.\n{out}'

    dev_groups = tgen_utils_dev_groups_from_config([
        {'ixp': tg_ports[0], 'ip': '1.1.1.1', 'gw': '1.1.1.5', 'plen': 24},
        {'ixp': tg_ports[1], 'ip': '1.1.1.2', 'gw': '1.1.1.5', 'plen': 24},
        {'ixp': tg_ports[2], 'ip': '1.1.1.3', 'gw': '1.1.1.5', 'plen': 24},
        {'ixp': tg_ports[3], 'ip': '1.1.1.4', 'gw': '1.1.1.5', 'plen': 24},
    ])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    # 4. Set streams frameSize (1510|8998|9000|9002)
    list_macs = ['aa:bb:cc:dd:ee:11', 'aa:bb:cc:dd:ee:12',
                 'aa:bb:cc:dd:ee:13', 'aa:bb:cc:dd:ee:14']
    streams = {
        f'bridge_{dst + 1}': {
            'ip_source': dev_groups[tg_ports[src]][0]['name'],
            'ip_destination': dev_groups[tg_ports[dst]][0]['name'],
            'srcMac': list_macs[src],
            'dstMac': list_macs[dst],
            'type': 'raw',
            'frameSize': mtu,
        } for src, dst in ((3, 0), (2, 1), (1, 2), (0, 3))
    }
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    # 5. Send traffic
    # first send traffic to learn MACs
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(5)
    await tgen_utils_stop_traffic(tgen_dev)
    await asyncio.sleep(5)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # check the traffic stats
    await asyncio.sleep(5)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) == (100 if should_fail else 0), \
            f"Verify that traffic from {row['Tx Port']} to {row['Rx Port']} forwarded.\n{out}"

    # 7. Verify that addresses are learned (or not learned if packet size is > 9000)
    out = await BridgeFdb.show(input_data=[{dent: [{'options': '-j'}]}],
                               parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get fdb entry.'

    learned_macs = [entry['mac'] for entry in out[0][dent]['parsed_output'] if 'mac' in entry]
    if should_fail:
        assert all(mac not in learned_macs for mac in list_macs), \
            'Verify that source macs have not been learned'
    else:
        assert all(mac in learned_macs for mac in list_macs), \
            'Verify that source macs have been learned'
