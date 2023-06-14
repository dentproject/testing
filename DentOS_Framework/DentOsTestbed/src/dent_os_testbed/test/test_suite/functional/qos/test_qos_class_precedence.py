from math import isclose as is_close
import asyncio
import pytest
import random

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
    tgen_utils_get_loss,
)
from dent_os_testbed.test.test_suite.functional.qos.conftest import (
    configure_dscp_map_and_verify,
    configure_qdiscs_and_verify,
    get_qd_stats_delta,
    get_qd_stats,
    dscp_to_raw,
)
from dent_os_testbed.utils.test_utils.data.tgen_constants import (
    TRAFFIC_ITEM_NAME,
    RX_FRAMES,
)


pytestmark = [
    pytest.mark.suite_functional_qos,
    pytest.mark.usefixtures('cleanup_qdiscs', 'cleanup_bridges', 'cleanup_dscp_prio'),
    pytest.mark.asyncio,
]


@pytest.mark.parametrize('trust_mode', ['L2', 'L3'])
async def test_qos_class_precedence(testbed, trust_mode):
    """
    Test Name: test_qos_class_precedence
    Test Suite: suite_functional_qos
    Test Overview: Verify traffic with higher prio has precedence over traffic with lower prio
    Test Procedure:
    1. Init test params
    2. Configure bridge and enslave TG ports to it
    3. Set all interfaces to up state
    4. Configure Qdisk on egress port:8 ETS bands
    5. Configure a tbf(shaper) for each band with max limit, burst and rate
    6. Configure 2 streams (with high and low priority) on 2 ingress ports (>100% utilization)
    7. Transmit traffic
    8. Verify that high priority stream has no losses
    9. Configure a medium priority
    10. Transmit traffic and verify medium and high priority streams have no losses
    """
    # 1. Init test params
    num_of_ports = 3
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], num_of_ports)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0][:num_of_ports]
    ports = tgen_dev.links_dict[dent][1][:num_of_ports]
    *ingress_ports, egress_port = ports
    wait_for_qd_stats = 5  # sec
    traffic_duration = 30  # sec
    num_of_bands = 8
    tolerance = 10  # %
    bridge = 'br0'

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
        prio_dscp_map = {tc: dscp for dscp, tc in dscp_prio_map.items()}
        await configure_dscp_map_and_verify(dent, {port: dscp_prio_map for port in ingress_ports})
    else:
        dscp_prio_map = {}
        vlan = random.randint(2, 4095)
        out = await BridgeVlan.delete(input_data=[{dent: [
            {'device': port, 'vid': 1} for port in ports
        ]}])
        assert out[0][dent]['rc'] == 0, 'Failed to remove default vlan'

        out = await BridgeVlan.add(input_data=[{dent: [
            {'device': port, 'vid': vlan} for port in ports
        ]}])
        assert out[0][dent]['rc'] == 0, f'Failed to add ports {ports} to vlan {vlan}'

    # 4. Configure Qdisk on egress port:8 ETS bands
    # 5. Configure a tbf(shaper) for each band with max limit, burst and rate
    await configure_qdiscs_and_verify(dent, [egress_port], ['10Gbit'] * num_of_bands)

    # 6. Configure 2 streams (with high and low priority) on 2 ingress ports (>100% utilization)
    dev_groups = tgen_utils_dev_groups_from_config((
        {'ixp': tg, 'ip': f'1.1.1.{idx}', 'gw': '1.1.1.10', 'plen': 24, 'vlan': vlan}
        for idx, tg in enumerate(tg_ports, start=1)
    ))
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    low_prio, med_prio, high_prio = sorted(random.sample(range(1, num_of_bands), 3))
    streams = {
        'high priority traffic': {
            'type': 'ethernet',
            'ip_source': (dev_groups[tg_ports[0]][0]['name'],
                          dev_groups[tg_ports[1]][0]['name']),
            'ip_destination': dev_groups[tg_ports[2]][0]['name'],
            'protocol': 'ipv4',
            'frame_rate_type': 'line_rate',
            'rate': 20,  # % per port, 40% total
        },
        'low priority traffic': {
            'type': 'ethernet',
            'ip_source': (dev_groups[tg_ports[0]][0]['name'],
                          dev_groups[tg_ports[1]][0]['name']),
            'ip_destination': dev_groups[tg_ports[2]][0]['name'],
            'protocol': 'ipv4',
            'frame_rate_type': 'line_rate',
            'rate': 40,  # % per port, 80% total
        },
    }
    if trust_mode == 'L3':
        streams['high priority traffic']['dscp_ecn'] = dscp_to_raw(prio_dscp_map[high_prio])
        streams['low priority traffic']['dscp_ecn'] = dscp_to_raw(prio_dscp_map[low_prio])
    else:
        streams['high priority traffic']['vlanID'] = vlan
        streams['high priority traffic']['vlanPriority'] = high_prio
        streams['low priority traffic']['vlanID'] = vlan
        streams['low priority traffic']['vlanPriority'] = low_prio

    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # 7. Transmit traffic
    qd_stats = await get_qd_stats(dent, [egress_port])
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # 8. Verify that high priority stream has no losses
    await asyncio.sleep(wait_for_qd_stats)
    qd_stats = await get_qd_stats_delta(dent, qd_stats)
    tg_stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in tg_stats.Rows:
        loss = tgen_utils_get_loss(row)
        if 'low' in row[TRAFFIC_ITEM_NAME]:
            assert loss > 0, 'Expected traffic loss'
        else:  # high prio
            assert loss == 0, f'Expected loss: 0%, actual: {loss}%'
            band = num_of_bands - high_prio
            assert is_close(qd_stats[egress_port][band]['packets'],
                            int(row[RX_FRAMES]), rel_tol=tolerance), \
                f'Expected qdisc stats to be {row[RX_FRAMES]}, but got {qd_stats[egress_port][band]}'

    # 9. Configure a medium priority stream
    streams = {
        'medium priority traffic': {
            'type': 'ethernet',
            'ip_source': (dev_groups[tg_ports[0]][0]['name'],
                          dev_groups[tg_ports[1]][0]['name']),
            'ip_destination': dev_groups[tg_ports[2]][0]['name'],
            'protocol': 'ipv4',
            'frame_rate_type': 'line_rate',
            'rate': 20,  # % per port, 40% total
        },
    }
    if trust_mode == 'L3':
        streams['medium priority traffic']['dscp_ecn'] = dscp_to_raw(prio_dscp_map[med_prio])
    else:
        streams['medium priority traffic']['vlanID'] = vlan
        streams['medium priority traffic']['vlanPriority'] = med_prio

    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # 10. Transmit traffic and verify medium and high priority streams have no losses
    qd_stats = await get_qd_stats(dent, [egress_port])
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    await asyncio.sleep(wait_for_qd_stats)
    qd_stats = await get_qd_stats_delta(dent, qd_stats)
    tg_stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in tg_stats.Rows:
        loss = tgen_utils_get_loss(row)
        if 'low' in row[TRAFFIC_ITEM_NAME]:
            assert loss > 0, 'Expected traffic loss'
            continue

        # high & medium prio
        assert loss == 0, f'Expected loss: 0%, actual: {loss}%'
        if 'high' in row[TRAFFIC_ITEM_NAME]:
            band = num_of_bands - high_prio
        else:
            band = num_of_bands - med_prio
        assert is_close(qd_stats[egress_port][band]['packets'],
                        int(row[RX_FRAMES]), rel_tol=tolerance), \
            f'Expected qdisc stats to be {row[RX_FRAMES]}, but got {qd_stats[egress_port][band]}'
