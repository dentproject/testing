from math import isclose as is_close
import asyncio
import pytest
import random

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan

from dent_os_testbed.utils.test_utils.cleanup_utils import cleanup_qdiscs
from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
)
from dent_os_testbed.test.test_suite.functional.qos.conftest import (
    verify_tgen_stats_per_port_per_tc,
    configure_dscp_map_and_verify,
    configure_qdiscs_and_verify,
    get_tc_from_stats_row,
    get_traffic_duration,
    bytes_to_mbit_per_s,
    get_qd_stats_delta,
    get_qd_stats,
    dscp_to_raw,
)
from dent_os_testbed.utils.test_utils.data.tgen_constants import (
    RX_BYTES,
)


pytestmark = [
    pytest.mark.suite_functional_qos,
    pytest.mark.usefixtures('cleanup_qdiscs', 'cleanup_bridges', 'cleanup_dscp_prio'),
    pytest.mark.asyncio,
]


@pytest.mark.parametrize('trust_mode', ['L2', 'L3'])
async def test_qos_shaper(testbed, trust_mode):
    """
    Test Name: test_qos_shaper
    Test Suite: suite_functional_qos
    Test Overview: Verify shaper is working as expected
    Test Procedure:
    1. Init test params
    2. Configure bridge and enslave TG ports to it
    3. Set all interfaces to up state
    4. Configure Qdisk on egress port:8 ETS bands
    5. Configure 8 PCP/DSCP streams
    6. Send traffic and verify the rate on egress port is matching the ingress
    7. Configure a tbf(shaper) for each band with rate/burst lower then port max rate/burst
    8. Transmit traffic
    9. Verify scheduler statistics are matching the expected
    """
    # 1. Init test params
    num_of_ports = 2
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], num_of_ports)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0][:num_of_ports]
    ports = tgen_dev.links_dict[dent][1][:num_of_ports]
    ingress_port, egress_port = ports
    wait_for_qd_stats = 5  # sec
    traffic_duration = 30  # sec
    num_of_bands = 8
    tolerance = 10  # %
    bridge = 'br0'

    tg_to_swp = {tg: swp for tg, swp in zip(tg_ports, ports)}

    # 2. Configure bridge and enslave TG ports to it
    out = await IpLink.add(input_data=[{dent: [
        {'name': bridge, 'type': 'bridge', 'vlan_filtering': 1}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create bridge'

    # 3. Set all interfaces to up state
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up', 'master': bridge} for port in ports
    ] + [
        {'device': bridge, 'operstate': 'up'}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to enslave ports to bridge'

    if trust_mode == 'L3':
        vlan = None
        # 8 random dscp values
        dscp_prio_map = {dscp: tc for tc, dscp
                         in enumerate(random.sample(range(64), num_of_bands))}
        await configure_dscp_map_and_verify(dent, {ingress_port: dscp_prio_map})
    else:
        dscp_prio_map = {}
        vlan = random.randint(2, 4094)
        out = await BridgeVlan.delete(input_data=[{dent: [
            {'device': port, 'vid': 1} for port in ports
        ]}])
        assert out[0][dent]['rc'] == 0, 'Failed to remove default vlan'

        out = await BridgeVlan.add(input_data=[{dent: [
            {'device': port, 'vid': vlan} for port in ports
        ]}])
        assert out[0][dent]['rc'] == 0, f'Failed to add ports {ports} to vlan {vlan}'

    # 4. Configure Qdisk on egress port:8 ETS bands
    await configure_qdiscs_and_verify(dent, [egress_port], ['10Gbit'] * num_of_bands)

    # 5. Configure 8 PCP/DSCP streams
    tg0_ip = '1.1.1.1'
    tg1_ip = '1.1.1.2'
    plen = 24
    dev_groups = tgen_utils_dev_groups_from_config((
        {'ixp': tg_ports[0], 'ip': tg0_ip, 'gw': tg1_ip, 'plen': plen, 'vlan': vlan},
        {'ixp': tg_ports[1], 'ip': tg1_ip, 'gw': tg0_ip, 'plen': plen, 'vlan': vlan},
    ))
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    streams = {
        'traffic': {
            'type': 'ethernet',
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'protocol': 'ip',
            'frame_rate_type': 'line_rate',
            'rate': 10,  # %
        }
    }
    if trust_mode == 'L3':
        streams['traffic']['dscp_ecn'] = {
            'type': 'list',
            'list': list(map(dscp_to_raw, dscp_prio_map)),
        }
    else:
        streams['traffic']['vlanID'] = vlan
        streams['traffic']['vlanPriority'] = {'type': 'increment', 'start': 0,
                                              'step': 1, 'count': num_of_bands}

    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # 6. Send traffic and verify the rate on egress port is matching the ingress
    qd_stats = await get_qd_stats(dent, [egress_port])
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    await asyncio.sleep(wait_for_qd_stats)
    qd_stats = await get_qd_stats_delta(dent, qd_stats)

    await verify_tgen_stats_per_port_per_tc(tgen_dev, qd_stats, tg_to_swp,
                                            dscp_prio_map=dscp_prio_map,
                                            num_of_tcs=num_of_bands,
                                            tol=tolerance)

    # 7. Configure a tbf(shaper) for each band with rate/burst lower then port max rate/burst
    await cleanup_qdiscs(dent_dev)

    rate_mbit = [random.randint(50, 125) for _ in range(num_of_bands)]
    await configure_qdiscs_and_verify(dent, [egress_port], [f'{x}Mbit' for x in rate_mbit])

    # 8. Transmit traffic
    qd_stats = await get_qd_stats(dent, [egress_port])
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # 9. Verify scheduler statistics are matching the expected
    await asyncio.sleep(wait_for_qd_stats)
    qd_stats = await get_qd_stats_delta(dent, qd_stats)
    tg_stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in tg_stats.Rows:
        tc = get_tc_from_stats_row(row, dscp_prio_map)
        band = num_of_bands - tc
        actual_traffic_duration = get_traffic_duration(row)
        rx_bytes = int(row[RX_BYTES])
        tg_rate_mbit = bytes_to_mbit_per_s(rx_bytes, actual_traffic_duration)
        qd_rate_mbit = bytes_to_mbit_per_s(qd_stats[egress_port][band]['bytes'],
                                           actual_traffic_duration)

        assert is_close(tg_rate_mbit, rate_mbit[tc], rel_tol=tolerance), \
            f'Expected rate {rate_mbit[tc]}, actual {tg_rate_mbit} ({tc = })'
        assert is_close(qd_rate_mbit, rate_mbit[tc], rel_tol=tolerance), \
            f'Expected rate {rate_mbit[tc]}, actual {qd_rate_mbit} ({tc = })'
