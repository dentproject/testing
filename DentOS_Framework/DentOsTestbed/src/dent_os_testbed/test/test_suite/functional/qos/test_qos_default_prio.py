import asyncio
import pytest
import random

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.dcb.dcb_app import DcbApp
from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
)
from dent_os_testbed.test.test_suite.functional.qos.conftest import (
    verify_tgen_stats_per_port_per_tc,
    configure_dscp_map_and_verify,
    configure_def_prio_and_verify,
    configure_qdiscs_and_verify,
    get_qd_stats_delta,
    get_qd_stats,
    dscp_to_raw,
)


pytestmark = [
    pytest.mark.suite_functional_qos,
    pytest.mark.usefixtures('cleanup_qdiscs', 'cleanup_bridges', 'cleanup_dscp_prio'),
    pytest.mark.asyncio,
]


async def test_qos_default_prio(testbed):
    """
    Test Name: test_qos_default_prio
    Test Suite: suite_functional_qos
    Test Overview: Verify default priority behavior
    Test Procedure:
    1. Create 1Q bridge. Add ports to bridge. Set ports and bridge up
    2. Configure DSCP priorities. Add ETS with 8 strict TCs on ports
    3. Configure tagged L3 streams
    4. Send L3 packets with DSCP that are not in DSCP to TC map. Verify TBF statistic
    5. Configure two DSCP for same PCP priority. Send Traffic. Verify both DSCPs are counted to the correct TC
    6. Send packets. Verify number of priority packets received on default traffic class
    7. Configure default priority. Verify default priority changed
    8. Add new (smaller) default priority. Verify default priority did not change
    9. Add another (higher) default priority. Verify default priority changed
    10. Flush default priority and dscp-prio map. Verify default priority is zero
    """
    num_of_ports = 4
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], num_of_ports)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0][:num_of_ports]
    ports = tgen_dev.links_dict[dent][1][:num_of_ports]
    ingress_port, *egress_ports = ports
    vlan = random.randint(2, 4095)
    wait_for_qd_stats = 5  # sec
    traffic_duration = 30  # sec
    dscp_not_in_map = 63
    num_of_bands = 8
    tolerance = .10
    bridge = 'br0'

    tg_to_swp = {tg: swp for tg, swp in zip(tg_ports, ports)}

    # 1. Create 1Q bridge
    out = await IpLink.add(input_data=[{dent: [
        {'name': bridge, 'type': 'bridge', 'vlan_filtering': 1, 'vlan_default_pvid': 0}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create bridge'

    # Add ports to bridge
    # Set ports and bridge up
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up', 'master': bridge} for port in ports
    ] + [
        {'device': bridge, 'operstate': 'up'}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to enslave ports to bridge'

    out = await BridgeVlan.add(input_data=[{dent: [
        {'device': port,
         'vid': vlan,
         'pvid': True,
         'untagged': port in ports[:2]}
        for port in ports
    ]}])
    assert out[0][dent]['rc'] == 0, f'Failed to add ports {ports} to vlan {vlan}'

    # 2. Configure DSCP priorities.
    # 8 random dscp values
    dscp_prio_map = {dscp: tc for tc, dscp
                     in enumerate(random.sample(range(1, 60), num_of_bands))}
    await configure_dscp_map_and_verify(dent, {ingress_port: dscp_prio_map})

    # Add ETS with 8 strict TCs on ports
    await configure_qdiscs_and_verify(dent, ports, rate=['10Gbit'] * num_of_bands)

    # 3. Configure tagged L3 streams
    dev_groups = tgen_utils_dev_groups_from_config([
        {'ixp': tg_ports[host],
         'ip': f'1.1.1.{host + 1}',  # 1, 2, 3, 4
         'gw': f'1.1.1.{gw + 1}',    # 4, 3, 2, 1
         'plen': 24}
        for host, gw in zip(range(len(tg_ports)), reversed(range(len(tg_ports))))
    ])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    # 4. Send L3 packets with DSCP that are not in DSCP to TC map.
    dscp_to_send = {
        'type': 'list',
        'list': list(map(dscp_to_raw, list(dscp_prio_map.keys()) + [dscp_not_in_map])),
    }
    streams = {
        'traffic': {
            'type': 'ethernet',
            'ep_source': ingress_port,
            'protocol': 'ipv4',
            'frame_rate_type': 'line_rate',
            'rate': 1,  # %
            'dscp_ecn': dscp_to_send,
            'vlanID': vlan,
        },
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    qd_stats = await get_qd_stats(dent, egress_ports)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # Verify TBF statistic
    await asyncio.sleep(wait_for_qd_stats)
    qd_stats = await get_qd_stats_delta(dent, qd_stats)

    await verify_tgen_stats_per_port_per_tc(tgen_dev, qd_stats, tg_to_swp,
                                            dscp_prio_map=dscp_prio_map,
                                            num_of_tcs=num_of_bands,
                                            tol=tolerance)

    # 5. Configure two DSCP for same PCP priority
    dscp_prio_map[dscp_not_in_map] = num_of_bands - 1
    out = await DcbApp.add(input_data=[{dent: [
        {'dev': ingress_port, 'dscp_prio': [(dscp_not_in_map, dscp_prio_map[dscp_not_in_map])]}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add dscp prio mapping'

    # Send Traffic
    qd_stats = await get_qd_stats(dent, egress_ports)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # Verify both DSCPs are counted to the correct TC
    await asyncio.sleep(wait_for_qd_stats)
    qd_stats = await get_qd_stats_delta(dent, qd_stats)

    await verify_tgen_stats_per_port_per_tc(tgen_dev, qd_stats, tg_to_swp,
                                            dscp_prio_map=dscp_prio_map,
                                            num_of_tcs=num_of_bands,
                                            tol=tolerance)
    del dscp_prio_map[dscp_not_in_map]

    out = await DcbApp.flush(input_data=[{dent: [
        {'dev': port} for port in ports
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to flush dscp prio map'

    await configure_dscp_map_and_verify(dent, {ingress_port: dscp_prio_map})

    # 6. Send packets
    rand_l2_pcp, rand_l3_pcp = random.sample(range(1, 7), 2)  # get 2 random but different priorities
    streams = {
        'L2': {
            'type': 'ethernet',
            'ep_source': ingress_port,
            'frame_rate_type': 'line_rate',
            'rate': 1,  # %
        },
        'L3': {
            'type': 'ethernet',
            'ep_source': ingress_port,
            'frame_rate_type': 'line_rate',
            'rate': 1,  # %
            'protocol': 'ipv4',
            'dscp_ecn': dscp_to_send
        },
        'L2_tagged': {
            'type': 'ethernet',
            'ep_source': ingress_port,
            'frame_rate_type': 'line_rate',
            'rate': 1,  # %
            'vlanID': vlan,
            'vlanPriority': rand_l2_pcp,
        },
        'L3_tagged': {
            'type': 'ethernet',
            'ep_source': ingress_port,
            'frame_rate_type': 'line_rate',
            'rate': 1,  # %
            'protocol': 'ipv4',
            'dscp_ecn': dscp_to_send,
            'vlanID': vlan,
            'vlanPriority': rand_l3_pcp,
        },
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    qd_stats = await get_qd_stats(dent, egress_ports)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # Verify number of priority packets received on default traffic class
    await asyncio.sleep(wait_for_qd_stats)
    qd_stats = await get_qd_stats_delta(dent, qd_stats)

    await verify_tgen_stats_per_port_per_tc(tgen_dev, qd_stats, tg_to_swp,
                                            dscp_prio_map=dscp_prio_map,
                                            num_of_tcs=num_of_bands,
                                            tol=tolerance)

    # 7. Configure default priority. Verify default priority changed.
    def_prio = random.randint(1, 5)

    await configure_def_prio_and_verify(dent, ports, def_prio)

    qd_stats = await get_qd_stats(dent, egress_ports)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    await asyncio.sleep(wait_for_qd_stats)
    qd_stats = await get_qd_stats_delta(dent, qd_stats)

    await verify_tgen_stats_per_port_per_tc(tgen_dev, qd_stats, tg_to_swp,
                                            dscp_prio_map=dscp_prio_map,
                                            num_of_tcs=num_of_bands,
                                            def_prio=def_prio, tol=tolerance)

    # 8. Add new (smaller) default priority. Verify default priority did not change
    await configure_def_prio_and_verify(dent, ports, def_prio - 1)

    qd_stats = await get_qd_stats(dent, egress_ports)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    await asyncio.sleep(wait_for_qd_stats)
    qd_stats = await get_qd_stats_delta(dent, qd_stats)

    await verify_tgen_stats_per_port_per_tc(tgen_dev, qd_stats, tg_to_swp,
                                            dscp_prio_map=dscp_prio_map,
                                            num_of_tcs=num_of_bands,
                                            def_prio=def_prio, tol=tolerance)

    # 9. Add another (higher) default priority. Verify default priority changed
    await configure_def_prio_and_verify(dent, ports, def_prio + 1)

    qd_stats = await get_qd_stats(dent, egress_ports)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    await asyncio.sleep(wait_for_qd_stats)
    qd_stats = await get_qd_stats_delta(dent, qd_stats)

    await verify_tgen_stats_per_port_per_tc(tgen_dev, qd_stats, tg_to_swp,
                                            dscp_prio_map=dscp_prio_map,
                                            num_of_tcs=num_of_bands,
                                            def_prio=def_prio + 1, tol=tolerance)

    # 10. Flush default priority and dscp-prio map.
    out = await DcbApp.flush(input_data=[{dent: [
        {'dev': port} for port in ports
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to flush dscp prio map'

    for port in ports:
        out = await DcbApp.show(input_data=[{dent: [
            {'dev': port, 'options': '-j'}
        ]}], parse_output=True)
        assert out[0][dent]['rc'] == 0, 'Failed to get dscp-prio map'
        assert not out[0][dent]['parsed_output'], \
            'Default priority and dscp-prio should be flushed'

    qd_stats = await get_qd_stats(dent, egress_ports)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # Verify default priority is zero
    await asyncio.sleep(wait_for_qd_stats)
    qd_stats = await get_qd_stats_delta(dent, qd_stats)

    await verify_tgen_stats_per_port_per_tc(tgen_dev, qd_stats, tg_to_swp,
                                            num_of_tcs=num_of_bands,
                                            tol=tolerance)
