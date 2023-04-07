from collections import namedtuple
import asyncio
import pytest
import random

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.tc.tc_qdisc import TcQdisc
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
from dent_os_testbed.test.test_suite.functional.qos.constants import (
    RAW_DSCP,
    PCP,
    RX_BYTES,
)
from dent_os_testbed.test.test_suite.functional.qos.conftest import (
    configure_dscp_map_and_verify,
    configure_qdiscs_and_verify,
    get_traffic_duration,
    bytes_to_mbit_per_s,
    dscp_to_raw,
    raw_to_dscp,
)


pytestmark = [
    pytest.mark.suite_functional_qos,
    pytest.mark.usefixtures('cleanup_qdiscs', 'cleanup_bridges', 'cleanup_dscp_prio'),
    pytest.mark.asyncio,
]


@pytest.mark.parametrize('trust_mode', ['L2', 'L3'])
@pytest.mark.parametrize('scheduler_type', ['sp', 'wrr'])
async def test_qos_trust_mode(testbed, trust_mode, scheduler_type):
    """
    Test Name: test_qos_trust_mode
    Test Suite: suite_functional_qos
    Test Overview: Verify L2/L3 configuration is valid and shaper stats are as expected
    Test Procedure:
    1. Init interfaces
    2. Configure bridge and enslave TG ports to it
    3. Set all interfaces up
    4. Configure DSCP priority mapping or configure vlans on bridge members
    5. Configure ets qdisc on egress port: 8 bands - SP or WRR
    6. Configure tbf (shaper) qdisc for each band with max limit, burst and rate
    7. Configure 8 streams for each traffic class (dscp or pcp)
    8. Transmit traffic
    9. Verify scheduler statistics are matching the sent traffic
    """
    # 1. Init interfaces
    num_of_ports = 2
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], num_of_ports)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0][:num_of_ports]
    ports = tgen_dev.links_dict[dent][1][:num_of_ports]
    traffic_duration = 30  # sec
    num_of_bands = 8
    tolerance = 10  # %
    bridge = 'br0'

    table_tg_headers = ['DSCP' if trust_mode == 'L3' else ' PCP',
                        'PRIO', 'Rx Rate, Mbit',
                        'Loss, %', 'Duration, s', 'Status']
    table_tg_columns = ['dscp_pcp', 'prio', 'rx_rate', 'loss', 'duration', 'status']
    table_tg_row_format = '{:4} | {:4} | {:13.02f} | {:7.2f} | {:11.2f} | {!s:6}'
    table_tg_row = namedtuple('table_tg_row', table_tg_columns)

    table_swp_headers = ['Band', 'PRIO', 'Statistics, bytes', 'Rate, Mbit',
                         'Expected, Mbit', 'Deviation, %', 'Duration, s', 'Status']
    table_swp_columns = ['band', 'prio', 'bytes', 'rate', 'expected_rate', 'deviation', 'duration', 'status']
    table_swp_row_format = '{:4} | {:4} | {:17} | {:10.02f} | {:14.02f} | {:12.1f} | {:11.2f} | {!s:6}'
    table_swp_row = namedtuple('table_swp_row', table_swp_columns)

    # 2. Configure bridge and enslave TG ports to it
    out = await IpLink.add(input_data=[{dent: [
        {'name': bridge, 'type': 'bridge', 'vlan_filtering': 1}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create bridge'

    # 3. Set all interfaces up
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up', 'master': bridge} for port in ports
    ] + [
        {'device': bridge, 'operstate': 'up'}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to enslave ports to bridge'

    if trust_mode == 'L3':
        # 4. Configure DSCP priority mapping
        vlan = None
        # 8 random dscp values
        dscp_prio_map = {dscp: tc for tc, dscp
                         in enumerate(random.sample(range(1, 64), num_of_bands))}
        await configure_dscp_map_and_verify(dent, {ports[0]: dscp_prio_map})
    else:
        # 4. Configure vlans on bridge members
        vlan = random.randint(2, 4095)
        out = await BridgeVlan.delete(input_data=[{dent: [
            {'device': port, 'vid': 1} for port in ports
        ]}])
        assert out[0][dent]['rc'] == 0, 'Failed to remove default vlan'

        out = await BridgeVlan.add(input_data=[{dent: [
            {'device': port, 'vid': vlan} for port in ports
        ]}])
        assert out[0][dent]['rc'] == 0, f'Failed to add ports {ports} to vlan {vlan}'

    # 5. Configure ets qdisc on egress port: 8 bands - SP or WRR
    # 6. Configure tbf (shaper) qdisc for each band with max limit, burst and rate
    if scheduler_type == 'wrr':
        quanta = sorted((random.randint(1, 10) for _ in range(num_of_bands)), reverse=True)
        await configure_qdiscs_and_verify(dent, [ports[1]],
                                          ['10Gbit'] * num_of_bands,
                                          quanta=quanta)
    else:
        await configure_qdiscs_and_verify(dent, [ports[1]],
                                          ['10Gbit'] * num_of_bands)

    # 7. Configure 8 streams for each traffic class (dscp or pcp)
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
            'rate': 30,  # %
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

    # 8. Transmit traffic
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # 9. Verify scheduler statistics are matching the sent traffic
    await asyncio.sleep(10)  # wait for tgen stats to update
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    tg_stats = [None] * num_of_bands
    tgen_dev.applog.info(' | '.join(table_tg_headers))
    for row in stats.Rows:  # verify tgen stats
        if trust_mode == 'L3':
            pcp_dscp = raw_to_dscp(row[RAW_DSCP])
            prio = dscp_prio_map[pcp_dscp]
        else:
            pcp_dscp = int(row[PCP])
            prio = pcp_dscp
        actual_traffic_duration = get_traffic_duration(row)
        rx_bytes = int(row[RX_BYTES])
        rx_mbit = bytes_to_mbit_per_s(rx_bytes, actual_traffic_duration)

        loss = tgen_utils_get_loss(row)
        tg_stats[prio] = table_tg_row(pcp_dscp, prio, rx_mbit,
                                      loss, actual_traffic_duration,
                                      loss < tolerance)
    for vals in tg_stats:
        tgen_dev.applog.info(table_tg_row_format.format(*vals))

    out = await TcQdisc.show(input_data=[{dent: [
        {'dev': ports[1], 'options': '-j -s'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get qdisc statistics'

    qd_stats = [None] * num_of_bands
    dent_dev.applog.info(' | '.join(table_swp_headers))
    for qdisc in out[0][dent]['parsed_output']:  # verify qdisc stats
        if qdisc['kind'] != 'tbf':
            continue
        band = int(qdisc['parent'].split(':')[1])
        prio = num_of_bands - band
        actual_traffic_duration = tg_stats[prio].duration
        tg_mbit = tg_stats[prio].rx_rate
        qd_bytes = int(qdisc['bytes'])
        qd_mbit = bytes_to_mbit_per_s(qd_bytes, actual_traffic_duration)

        deviation = abs(1 - qd_mbit / tg_mbit) * 100
        qd_stats[prio] = table_swp_row(band, prio, qd_bytes, qd_mbit, tg_mbit,
                                       deviation, actual_traffic_duration,
                                       deviation < tolerance)
    for vals in qd_stats:
        dent_dev.applog.info(table_swp_row_format.format(*vals))
    msg = 'Some streams were not transmitted as expected. See table above.'
    assert all(stats.status for stats in tg_stats), msg
    assert all(stats.status for stats in qd_stats), msg
