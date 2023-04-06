# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import time

import pytest

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.lib.bridge.bridge_link import BridgeLink
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.iptables.ip_tables import IpTables
from dent_os_testbed.utils.test_utils.tb_utils import tb_reload_nw_and_flush_firewall
from dent_os_testbed.utils.test_utils.tc_flower_utils import (
    tcutil_cleanup_tc_rules,
    tcutil_get_iptables_rule_stats,
    tcutil_get_tc_rule_stats,
    tcutil_iptable_to_tc,
)
from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_clear_traffic_stats,
    tgen_utils_connect_to_tgen,
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_get_swp_info,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_protocols,
    tgen_utils_stop_traffic,
)

pytestmark = pytest.mark.suite_vlan_port_isolation


@pytest.mark.asyncio
async def test_dentv2_vlan_port_isolation_firewall(testbed):
    """
    Test Name: test_dentv2_vlan_port_isolation_firewall
    Test Suite: suite_vlan_port_isolation
    Test Overview: Test vlan port isolation with firewall config
    Test Procedure:
    1. Configure a single VLAN-aware bridge
    2. Modify the firewall to work with isolated bridge
    3. Set firewall rules that accept packets from the VLAN
    4. Verify that isolated ports cannot communicate in the VLAN
    """

    tgen_dev, infra_devices = await tgen_utils_get_dent_devices_with_tgen(
        testbed, [DeviceType.INFRA_SWITCH], 2
    )
    if not tgen_dev or not infra_devices:
        print('The testbed does not have enough dent with tgen connections')
        return
    infra_dev = infra_devices[0]
    infra = infra_dev.host_name
    swp_tgen_ports = tgen_dev.links_dict[infra][1]

    await tb_reload_nw_and_flush_firewall(infra_devices)

    await tgen_utils_connect_to_tgen(tgen_dev, infra_dev)

    swp = swp_tgen_ports[0]
    streams = {
        # create a raw vlan stream
        'https_vlan': {
            'srcIp': f'20.0.{swp[3:]}.2',
            'dstIp': f'20.0.{swp[3:]}.1',
            'srcMac': '00:11:01:00:00:01',
            'dstMac': '00:12:01:00:00:01',
            'type': 'raw',
            'rate': '10',
            'frameSize': '256',
            'protocol': '802.1Q',
            'vlanID': '100',
            'ipproto': 'tcp',
            'dstPort': '443',
        },
    }

    # Create bridge br0 and put tgen ports on it
    await IpLink.delete(input_data=[{infra: [{'device': 'bridge'}]}])
    await IpLink.delete(input_data=[{infra: [{'device': 'br0'}]}])
    out = await IpLink.add(
        input_data=[{infra: [{'device': 'br0', 'type': 'bridge', 'vlan_filtering': 1}]}]
    )
    assert out[0][infra]['rc'] == 0, out
    out = await IpLink.set(input_data=[{infra: [{'device': 'br0', 'operstate': 'up'}]}])
    assert out[0][infra]['rc'] == 0, out

    iptable_rules = {}
    for swp in swp_tgen_ports:
        await IpLink.set(input_data=[{infra: [{'device': swp, 'nomaster': ''}]}])
        out = await IpLink.set(input_data=[{infra: [{'device': swp, 'master': 'br0'}]}])
        assert out[0][infra]['rc'] == 0, out
        await BridgeLink.set(input_data=[{infra: [{'device': swp, 'isolated': True}]}])
        iptable_rules[swp] = [
            {
                'table': 'filter',
                'chain': 'FORWARD',
                'protocol': 'tcp',
                'dport': '443',
                'target': 'ACCEPT -m comment --comment "TC:--vlan-tag TC:100"',
            },
        ]
        infra_dev.applog.info(f'Adding iptable rule for {swp}')
        out = await IpTables.append(input_data=[{infra: iptable_rules[swp]}])
        infra_dev.applog.info(out)

    await tgen_utils_setup_streams(
        tgen_dev,
        pytest._args.config_dir + f'/{tgen_dev.host_name}/tgen_port_isolation_firewall',
        streams,
        force_update=True,
    )
    # perform the rule translation
    await tcutil_iptable_to_tc(infra_dev, swp_tgen_ports, iptable_rules)
    await tgen_utils_clear_traffic_stats(tgen_dev)
    await tgen_utils_start_traffic(tgen_dev)

    sleep_time = 60 * 2
    tgen_dev.applog.info(f'zzZZZZZ({sleep_time})s')
    time.sleep(sleep_time)
    # await tgen_utils_stop_traffic(tgen_dev)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Traffic Item Statistics')

    # Traffic Verification
    for row in stats.Rows:
        assert float(row['Loss %']) == 100.000, f'Failed>Loss percent {row["Loss %"]}'

    swp_tc_rules = {}
    await tcutil_get_tc_rule_stats(infra_dev, swp_tgen_ports, swp_tc_rules)

    await tgen_utils_stop_protocols(tgen_dev)
    # cleanup
    await tb_reload_nw_and_flush_firewall(infra_devices)
    out = await IpTables.flush(
        input_data=[
            {
                infra: [
                    {
                        'table': 'filter',
                    }
                ]
            }
        ]
    )
    infra_dev.applog.info(out)
