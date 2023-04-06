from collections import namedtuple
import asyncio
import pytest
import random

from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_get_egress_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
)
from dent_os_testbed.test.test_suite.functional.qos.conftest import (
    configure_dscp_map_and_verify,
    dscp_to_raw,
    raw_to_dscp,
)
from dent_os_testbed.test.test_suite.functional.qos.constants import (
    RAW_DSCP,
    TX_PORT,
    RX_PORT,
    TX_FRAMES,
    RX_FRAMES,
    EGRESS_TRACKING,
)


pytestmark = [
    pytest.mark.suite_functional_qos,
    pytest.mark.usefixtures('cleanup_qdiscs', 'cleanup_bridges', 'cleanup_dscp_prio'),
    pytest.mark.asyncio,
]


async def test_qos_dscp_remarking(testbed):
    """
    Test Name: test_qos_dscp_remarking
    Test Suite: suite_functional_qos
    Test Overview: Verify dscp remarking is working as expected
    Test Procedure:
    1. Init interfaces
    2. Configure bridge and enslave TG ports to it
    3. Set all interfaces up
    4. Configure DSCP priority mapping
    5. Configure 8 streams for each dscp
    6. Transmit traffic
    7. Verify egress packets have respective DSCP value assigned
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
    traffic_duration = 10  # sec
    num_of_bands = 8
    bridge = 'br0'

    tg_to_swp = {tg: swp for tg, swp in zip(tg_ports, ports)}

    table_headers = ['RX port', 'RX packets', 'RX DSCP', 'TX port', 'TX packets',
                     'TX DSCP', 'Prio', 'DSCP expected', 'DSCP correct', 'Loss']
    table_columns = [header.replace(' ', '_').lower() for header in table_headers]
    table_row_format = '{:<7} | {:10} | {:7} | {:<7} | {:10} | {:7} | {:^4} | {:13} | {!s:^12} | {!s:^4}'
    table_row = namedtuple('table_row', table_columns)

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

    # 4. Configure DSCP priority mapping
    dscp_prio_map = {port: {dscp: prio
                            for prio, dscp in enumerate(random.sample(range(64), num_of_bands))}
                     for port in ports}
    prio_dscp_map = {port: {prio: dscp for dscp, prio in priomap.items()}
                     for port, priomap in dscp_prio_map.items()}
    await configure_dscp_map_and_verify(dent, dscp_prio_map)

    # 5. Configure 8 streams for each dscp
    dev_groups = tgen_utils_dev_groups_from_config((
        {'ixp': port, 'ip': f'1.1.1.{idx}', 'gw': f'1.1.1.{len(tg_ports) - idx + 1}', 'plen': 24}
        for idx, port in enumerate(tg_ports, start=1)
    ))
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    streams = {
        f"dscp [{','.join(map(str, dscp_prio_map[swp]))}]": {
            'type': 'ipv4',
            'ip_source': dev_groups[tg][0]['name'],
            'dscp_ecn': {
                'type': 'list',
                'list': list(map(dscp_to_raw, dscp_prio_map[swp])),
            },
            'egress_track_by': 'dscp',
        } for swp, tg in zip(ports, tg_ports)
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # 6. Transmit traffic
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # 7. Verify egress packets have respective DSCP value assigned
    tg_stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    status = []
    for row in tg_stats.Rows:
        ingress_port = tg_to_swp[row[TX_PORT]]
        egress_port = tg_to_swp[row[RX_PORT]]
        dscp_sent = raw_to_dscp(row[RAW_DSCP])
        prio = dscp_prio_map[ingress_port][dscp_sent]
        dscp_expected = prio_dscp_map[egress_port][prio]
        egress_stats = await tgen_utils_get_egress_stats(tgen_dev, row)
        for idx, e_row in enumerate(egress_stats.Rows):
            if idx == 0:
                tx = int(e_row[TX_FRAMES])
                continue
            dscp_received = int(e_row[EGRESS_TRACKING])
            rx = int(e_row[RX_FRAMES])

            status.append(table_row(ingress_port, tx, dscp_sent,
                                    egress_port, rx, dscp_received,
                                    prio, dscp_expected,
                                    dscp_received == dscp_expected,
                                    not (tx == rx)))
    tgen_dev.applog.info(' | '.join(table_headers))
    for vals in sorted(status, key=lambda r: (r.rx_port, r.tx_port, r.prio)):
        tgen_dev.applog.info(table_row_format.format(*vals))

    assert all(stats.dscp_correct and not stats.loss for stats in status), \
        'Some streams were not transmitted as expected. See table above.'
