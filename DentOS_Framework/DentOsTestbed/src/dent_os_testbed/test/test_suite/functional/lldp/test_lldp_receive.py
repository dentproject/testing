import pytest
import asyncio

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.lldp.lldp import Lldp

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_dev_groups_from_config,
    tgen_utils_traffic_generator_connect,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
)

from dent_os_testbed.test.test_suite.functional.lldp.lldp_utils import (
    get_lldp_stream, get_neighbors_info,
    verify_rx_lldp_fields,
    get_lldp_statistic,
    build_lldp_optional_pkt,
)

pytestmark = [
    pytest.mark.suite_functional_lldp,
    pytest.mark.asyncio,
    pytest.mark.usefixtures('check_and_restore_lldp_service', 'cleanup_tgen'),
]


@pytest.mark.parametrize('scenario', ['basic', 'mandatory', 'optional', 'ttl'])
async def test_lldp_received(testbed, scenario):
    """
    Test Name: test_lldp_received
    Test Suite: suite_functional_lldp
    Test Overview: Test lldp received in different scenarios
    Test Procedure:
    1. Init interfaces and set first DUT port up
    2. Enable first DUT port to recieve lldp units
    3. Setup lldp packet for trasmitting to first DUT port
       In case of ttl scenario set ttl to 20
    4. Transmit lldp packet to first DUT port
    5. Verifying lldp packet have been received on first DUT port
       basic: Verify that DUT received lldp packet based on port rx stats
       mandatory: Verify that DUT learned lldp neighbour and have all mandatory TLVs as expected
       ttl: Verify that DUT learned lldp neighbour and have all mandatory TLVs as expected,
            and that after sleep of ttl time neighbour will be absent
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dev_name = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]
    count = 6

    # 1.Init interfaces and set first DUT port up
    out = await IpLink.set(
        input_data=[{dev_name: [
            {'device': dut_ports[0], 'operstate': 'up'}]}])
    assert not out[0][dev_name]['rc'], f"Verify {dut_ports[0]} set to 'UP' state.\n{out}"

    dev_groups = tgen_utils_dev_groups_from_config(
        [{'ixp': tg_ports[0], 'ip': '10.0.0.3', 'gw': '10.0.0.1', 'plen': 24},
         {'ixp': tg_ports[1], 'ip': '11.0.0.3', 'gw': '11.0.0.1', 'plen': 24}
         ])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    # 2.Enable first DUT port to recieve lldp units
    out = await Lldp.configure(
        input_data=[{dev_name: [
            {'interface': dut_ports[0], 'ports': '', 'lldp': '', 'status': 'rx-only'}]}])
    assert not out[0][dev_name]['rc'], f'Failed to configure lldp status on port {dut_ports[0]}.\n{out}'

    # 3.Setup lldp packet for trasmitting to first DUT port
    # In case of ttl scenario set ttl to 20
    chassis = '00:19:2f:a7:b2:8d'
    port = 'Uplink to Spine 1'
    port_subtype = 1
    ttl = 120
    lldp = {
            'chassisLen': (len(chassis.replace(':', '')) // 2) + 1,
            'chassisSubtype': 4,
            'chassisVarLen': len(chassis.replace(':', '')) // 2,
            'chassisId': chassis.replace(':', ''),
            'portLen': (len(port.encode().hex()) // 2) + 1,
            'portSubtype': port_subtype,
            'portVarLen': len(port.encode().hex()) // 2,
            'portId': port.encode().hex(),
            'ttlLen': 2,
            'ttlVal': ttl,
    }
    if scenario == 'ttl':
        chassis = '00:00:00:11:11:11'
        port = '00:00:00:00:00:07'
        ttl = 20
        port_subtype = 3
        lldp.update({
            'chassisId': chassis.replace(':', ''),
            'portLen': (len(port.replace(':', '')) // 2) + 1,
            'portSubtype': port_subtype,
            'portVarLen': len(port.replace(':', '')) // 2,
            'portId': port.replace(':', ''),
            'ttlVal': ttl,
        })
    elif scenario == 'optional':
        port = '00:02:03:00:00:07'
        port_desc = 'GigabitEthernet8'
        sys_name = 'S2.cisco.com'
        sys_desc = 'Cisco IOS Software, C3560 Software (C3560-ADVIPSERVICESK9-M), Version 12.2(44)SE, RELEASE SOFTWARE (fc1)'
        mgmt = '10.5.225.52'
        capabilities = {'Bridge': True, 'Router': False}
        lldp_hex = build_lldp_optional_pkt(chassis, port, ttl, port_desc=port_desc, sys_name=sys_name,
                                           sys_desc=sys_desc, capability=20, enabled_capability=4, mgmt_ip=mgmt)

        lldp_stream = {'lldp_optional': {
            'type': 'custom',
            'protocol': '88cc',
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcMac': 'aa:bb:cc:dd:ee:11',
            'dstMac': '01:80:c2:00:00:0e',
            'rate': 2,
            'frameSize': 512,
            'transmissionControlType': 'fixedPktCount',
            'frameCount': 6,
            'customLength': len(lldp_hex) // 2,
            'customData': lldp_hex}
        }
    if scenario != 'optional':
        lldp_stream = get_lldp_stream(dev_groups[tg_ports[0]][0]['name'], dev_groups[tg_ports[1]][0]['name'], lldp, count=count)
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=lldp_stream)

    # Get lldp rx stats from port
    rx_before = await get_lldp_statistic(dev_name, dut_ports[0], stats='rx')
    # 4.Transmit lldp packet to first DUT port
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(10)

    # 5.Verifying lldp packet have been received on first DUT port
    if scenario in ['mandatory', 'ttl', 'optional']:
        # mandatory: Verify that DUT learned lldp neighbour and have all mandatory TLVs as expected
        # According to RFC 802.1AB there are 3 mandatory TLVs: chassisTlv, portTlv, ttlTlv
        if scenario in ['mandatory', 'ttl']:
            await verify_rx_lldp_fields(dev_name, dut_ports[0], chassis, port, port_subtype, ttl)

            if scenario == 'ttl':
                # Verify that after sleep of ttl time neighbour will be absent
                await asyncio.sleep(ttl)
                neighbor_info = await get_neighbors_info(dev_name, port=dut_ports[0])
                assert not neighbor_info, f'lldp neighbout still exist.\n{out}'

        elif scenario == 'optional':
            await verify_rx_lldp_fields(dev_name, dut_ports[0], chassis, port, 3, ttl, sys_name=sys_name,
                                        port_desc=port_desc, sys_desc=sys_desc, mgmt_ip=mgmt, capabilities=capabilities)

    # basic: Verify that DUT received lldp packet based on port rx stats
    elif scenario == 'basic':
        rx_after = await get_lldp_statistic(dev_name, dut_ports[0], stats='rx')
        assert rx_after == rx_before + count, f'rx_after {rx_after} != expected amount of pkts {rx_before + count}'


@pytest.mark.parametrize('scenario', ['disable', 'port_down_up'])
async def test_lldp_rx(testbed, scenario):
    """
    Test Name: test_lldp_rx
    Test Suite: suite_functional_lldp
    Test Overview: Test lldp received with port status disable/port down
    Test Procedure:
    1. Init interfaces and set first DUT port up
    2. Set lldp status on first DUT port to disabled/port down and status rx-only
    3. Setup lldp packet for trasmitting to first DUT port and transmit stream
    4. Verifying lldp packet haven't been received on first DUT port
       port_down_up scenario: Verify after port set up and resending traffic that lldp pkt will be received with all mandatory fields
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dev_name = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]

    # 1.Init interfaces and set first DUT port up
    out = await IpLink.set(
        input_data=[{dev_name: [
            {'device': dut_ports[0], 'operstate': 'up'}]}])
    assert not out[0][dev_name]['rc'], f"Verify {dut_ports[0]} set to 'UP' state.\n{out}"

    dev_groups = tgen_utils_dev_groups_from_config(
        [{'ixp': tg_ports[0], 'ip': '10.0.0.3', 'gw': '10.0.0.1', 'plen': 24},
         {'ixp': tg_ports[1], 'ip': '11.0.0.3', 'gw': '11.0.0.1', 'plen': 24}
         ])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    # 2.Set lldp status on first DUT port to disabled/port down and status rx-only
    if scenario == 'disable':
        out = await Lldp.configure(
            input_data=[{dev_name: [
                {'interface': dut_ports[0], 'ports': '', 'lldp': '', 'status': 'disabled'}]}])
        assert not out[0][dev_name]['rc'], f'Failed to configure lldp status on port {dut_ports[0]}.\n{out}'

    elif scenario == 'port_down_up':
        out = await IpLink.set(
            input_data=[{dev_name: [
                {'device': dut_ports[0], 'operstate': 'down'}]}])
        assert not out[0][dev_name]['rc'], f"Verify {dut_ports[0]} set to 'DOWN' state.\n{out}"

        out = await Lldp.configure(
            input_data=[{dev_name: [
                {'interface': dut_ports[0], 'ports': '', 'lldp': '', 'status': 'rx-only'}]}])
        assert not out[0][dev_name]['rc'], f'Failed to configure lldp status on port {dut_ports[0]}.\n{out}'

    # 3.Setup lldp packet for trasmitting to first DUT port and transmit stream
    chassis = 'a2:2c:38:b8:9c:a6'
    port = 'Ethernet0/13'
    ttl = 120
    port_subtype = 5
    lldp = {
            'chassisLen': (len(chassis.replace(':', '')) // 2) + 1,
            'chassisSubtype': 4,
            'chassisVarLen': len(chassis.replace(':', '')) // 2,
            'chassisId': chassis.replace(':', ''),
            'portLen': (len(port.encode().hex()) // 2) + 1,
            'portSubtype': port_subtype,
            'portVarLen': len(port.encode().hex()) // 2,
            'portId': port.encode().hex(),
            'ttlLen': 2,
            'ttlVal': ttl
    }
    lldp_stream = get_lldp_stream(dev_groups[tg_ports[0]][0]['name'], dev_groups[tg_ports[1]][0]['name'], lldp)
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=lldp_stream)

    if scenario == 'disable':
        await tgen_utils_start_traffic(tgen_dev)
        await asyncio.sleep(10)

    # 4.Verifying lldp packet haven't been received on first DUT port
    neighbor_info = await get_neighbors_info(dev_name, port=dut_ports[0])
    assert not neighbor_info, f'LLDP neighbout still exist.\n{out}'

    # port_down_up scenario: Verify after port set up and resending traffic that lldp pkt will be received with all mandatory fields
    if scenario == 'port_down_up':
        out = await IpLink.set(
            input_data=[{dev_name: [
                {'device': dut_ports[0], 'operstate': 'up'}]}])
        assert not out[0][dev_name]['rc'], f"Verify {dut_ports[0]} set to 'UP' state.\n{out}"

        await tgen_utils_start_traffic(tgen_dev)
        await asyncio.sleep(10)
        await verify_rx_lldp_fields(dev_name, dut_ports[0], chassis, port, port_subtype, ttl)


async def test_lldp_max_neighbours(testbed):
    """
    Test Name: test_lldp_max_neighbours
    Test Suite: suite_functional_lldp
    Test Overview: Verify that lldp will have amount of neighbours equal to max-neighbors configured in lldp
    Test Procedure:
    1. Init interfaces and set first DUT port up
    2. Set lldp status on first DUT port rx-only, get max-neighbors configured in lldp
    3. Setup incremented lldp packet for trasmitting to first DUT port and transmit stream
    4. Verify that lldp will have configured amount of max-neighbors
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dev_name = dent_devices[0].host_name
    dent_dev = dent_devices[0]
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]

    # 1.Init interfaces and set first DUT port up
    out = await IpLink.set(
        input_data=[{dev_name: [
            {'device': dut_ports[0], 'operstate': 'up'}]}])
    assert not out[0][dev_name]['rc'], f"Verify {dut_ports[0]} set to 'UP' state.\n{out}"

    dev_groups = tgen_utils_dev_groups_from_config(
        [{'ixp': tg_ports[0], 'ip': '10.0.0.3', 'gw': '10.0.0.1', 'plen': 24},
         {'ixp': tg_ports[1], 'ip': '11.0.0.3', 'gw': '11.0.0.1', 'plen': 24}]
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    # 2.Set lldp status on first DUT port rx-only, get max-neighbors configured in lldp
    out = await Lldp.configure(
            input_data=[{dev_name: [
                {'interface': dut_ports[0], 'ports': '', 'lldp': '', 'status': 'rx-only'}]}])
    assert not out[0][dev_name]['rc'], \
        f'Failed to configure lldp status on port {dut_ports[0]}.\n{out}'

    out = await Lldp.show_lldpcli(
        input_data=[{dev_name: [
            {'running-configuration': '', 'cmd_options': '-f json'}]}], parse_output=True)
    assert not out[0][dev_name]['rc'], f'Failed to show LLDP neighbors.\n{out}'
    max_neighbors = int(out[0][dev_name]['parsed_output']['configuration']['config']['max-neighbors'])

    # 3.Setup incremented lldp packet for trasmitting to first DUT port and transmit stream
    chassis = '01:01:01:01:01:01'
    port_val = '02:02:02:02:02:02'
    step = '00:00:00:00:00:10'
    count = max_neighbors + 5

    lldp = {
            'chassisLen': (len(chassis.replace(':', '')) // 2) + 1,
            'chassisSubtype': 4,
            'chassisVarLen': len(chassis.replace(':', '')) // 2,
            'chassisId': {
                'type': 'increment',
                'start': chassis.replace(':', ''),
                'step': step.replace(':', ''),
                'count': count,
            },
            'portLen': (len(port_val.replace(':', '')) // 2) + 1,
            'portSubtype': 3,
            'portVarLen': len(port_val.replace(':', '')) // 2,
            'portId': {
                'type': 'increment',
                'start': port_val.replace(':', ''),
                'step': step.replace(':', ''),
                'count': count,
            },
            'ttlLen': 2,
            'ttlVal': 240,
        }

    lldp_stream = get_lldp_stream(dev_groups[tg_ports[0]][0]['name'], dev_groups[tg_ports[1]][0]['name'], lldp, rate=count, count=count)
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=lldp_stream)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(10)

    # 4.Verify that lldp will have configured amount of max-neighbors
    rc, out = await dent_dev.run_cmd('lldpcli show neighbors | grep RID | wc -l')
    assert not rc, f'Failed to run cmd lldpcli show neighbors {rc}'
    assert int(out.strip()) == max_neighbors, f'Current neighbors amount {int(out.strip())} is not equal to expected {max_neighbors}'
