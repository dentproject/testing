import pytest
import asyncio
from random import randint

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
    get_lldp_stream, random_mac,
    get_lldp_statistic,
    verify_rx_lldp_fields,
    verify_tx_lldp_fields,
    get_neighbors_info
)

pytestmark = [
    pytest.mark.suite_functional_lldp,
    pytest.mark.asyncio,
    pytest.mark.usefixtures('check_and_restore_lldp_service', 'cleanup_tgen')
]


@pytest.mark.usefixtures('cleanup_bridges')
async def test_lldp_bridge(testbed):
    """
    Test Name: test_lldp_bridge
    Test Suite: suite_functional_lldp
    Test Overview: Test lldp transmitted and received with port in bridge
    Test Procedure:
    1. Create bridge device
    2. Add 4 ports to bridge
    3. Set bridge and first added port to up
    4. Init interfaces
    5. Configure lldp tx-interval to 2 sec
    6. Collect tx stats and set first DUT port to lldp status rx-and-tx
    7. Setup lldp packet for trasmitting to first DUT port and start sending
    8. Verify lldp pkt received and mandatory fields are as expected
    9. Verify lldp pkt's were transmitted with all fields set as expected
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dev_name = dent_devices[0].host_name
    dent_dev = dent_devices[0]
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]
    bridge = 'br0'
    lldp_interval = 2
    wait = 5

    # 1.Create bridge device
    out = await IpLink.add(
        input_data=[{dev_name: [
            {'device': bridge, 'type': 'bridge'}]}])
    err_msg = f'Verify that bridge created and vlan filtering set successful\n{out}'
    assert not out[0][dev_name]['rc'], err_msg
    # 2.Add 4 ports to bridge
    out = await IpLink.set(
        input_data=[{dev_name: [
            {'device': port, 'master': bridge} for port in dut_ports]}])
    assert not out[0][dev_name]['rc'], f'Verify {dut_ports} set master to {bridge}.\n{out}'
    # 3.Set bridge and first added port to up
    out = await IpLink.set(
        input_data=[{dev_name: [
            {'device': device, 'operstate': 'up'} for device in [dut_ports[0], bridge]]}])
    assert not out[0][dev_name]['rc'], f"Verify devices set to 'UP'.\n{out}"
    # 4.Init interfaces
    dev_groups = tgen_utils_dev_groups_from_config(
        [{'ixp': tg_ports[0], 'ip': '10.0.0.3', 'gw': '10.0.0.1', 'plen': 24},
         {'ixp': tg_ports[1], 'ip': '11.0.0.3', 'gw': '11.0.0.1', 'plen': 24},
         {'ixp': tg_ports[2], 'ip': '12.0.0.3', 'gw': '12.0.0.1', 'plen': 24},
         {'ixp': tg_ports[3], 'ip': '13.0.0.3', 'gw': '13.0.0.1', 'plen': 24}]
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)
    # 5.Configure lldp tx-interval to 2 sec
    out = await Lldp.configure(
        input_data=[{dev_name: [
            {'lldp': '', 'tx-interval': lldp_interval}]}])
    assert not out[0][dev_name]['rc'], f'Failed to configure lldp tx-interval {lldp_interval}.\n{out}'

    # 6.Collect tx stats and set first DUT port to lldp status rx-and-tx
    tx_before = await get_lldp_statistic(dev_name, dut_ports[0])
    out = await Lldp.configure(
        input_data=[{dev_name: [
            {'interface': dut_ports[0], 'ports': '', 'lldp': '', 'status': 'rx-and-tx'}]}])
    assert not out[0][dev_name]['rc'], f'.\n{out}'

    # 7.Setup lldp packet for trasmitting to first DUT port and start sending
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
            'ttlVal': ttl,
    }
    lldp_stream = get_lldp_stream(dev_groups[tg_ports[0]][0]['name'], dev_groups[tg_ports[1]][0]['name'], lldp)
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=lldp_stream)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(lldp_interval * wait)

    # 8.Verify lldp pkt received and mandatory fields are as expected
    await verify_rx_lldp_fields(dev_name, dut_ports[0], chassis, port, port_subtype, ttl)

    # 9.Verify lldp pkt's were transmitted with all fields set as expected
    tx_after = await get_lldp_statistic(dev_name, dut_ports[0])
    assert tx_after >= tx_before + wait, f'tx_after {tx_after} >= tx_before {tx_before}'
    await verify_tx_lldp_fields(dev_name, dent_dev, dut_ports[0], lldp_interval, optional_tlvs=True)


async def test_lldp_enable_disable_ports(testbed):
    """
    Test Name: test_lldp_enable_disable_ports
    Test Suite: suite_functional_lldp
    Test Overview: Test lldp transmitted and received with multiple ports set to lldp status rx-and-tx/disabled
    Test Procedure:
    1. Set 4 ports up and Init interfaces
    2. Configure lldp tx-interval to 2 sec
    3. Configure lldp ports to disabled/rx-and-tx state
    4. Setup 4 lldp streams with different params and start transmitting traffic
    5. Verify that ports with lldp status disabled won't transmit and receive lldp packets,
       ports with status rx-and-tx transmitted and received lldp pkts
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dev_name = dent_devices[0].host_name
    dent_dev = dent_devices[0]
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]
    tx_interval = 2

    # 1.Set 4 ports up and Init interfaces
    out = await IpLink.set(
        input_data=[{dev_name: [
            {'device': port, 'operstate': 'up'} for port in dut_ports]}])
    assert not out[0][dev_name]['rc'], f"Verify {dut_ports} set to 'UP' state.\n{out}"

    dev_groups = tgen_utils_dev_groups_from_config(
        [{'ixp': tg_ports[0], 'ip': '10.0.0.3', 'gw': '10.0.0.1', 'plen': 24},
         {'ixp': tg_ports[1], 'ip': '11.0.0.3', 'gw': '11.0.0.1', 'plen': 24},
         {'ixp': tg_ports[2], 'ip': '12.0.0.3', 'gw': '12.0.0.1', 'plen': 24},
         {'ixp': tg_ports[3], 'ip': '13.0.0.3', 'gw': '13.0.0.1', 'plen': 24}]
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)
    # 2.Configure lldp tx-interval to 2 sec
    out = await Lldp.configure(
        input_data=[{dev_name: [
            {'lldp': '', 'tx-interval': tx_interval}]}])
    assert not out[0][dev_name]['rc'], f'Failed to configure lldp tx-interval {tx_interval}.\n{out}'

    # 3.Configure lldp ports to disabled/rx-and-tx state
    out = await Lldp.configure(
        input_data=[{dev_name: [
            {'interface': port, 'ports': '', 'lldp': '', 'status': 'rx-and-tx' if indx % 2 else 'disabled'}
            for indx, port in enumerate(dut_ports)]}])
    assert not out[0][dev_name]['rc'], f'Failed to configure lldp status on port {dut_ports}.\n{out}'

    # 4.Setup 4 lldp streams with different params and start transmitting traffic
    lldps_verify = {}
    streams = {}
    for index, port in enumerate(dut_ports):
        chassis = random_mac()
        port_val = random_mac()
        ttl = randint(160, 200)

        lldps_verify.update({port: {
            'chassis': chassis,
            'port': port_val,
            'ttl': ttl}
        })
        src = tg_ports[index]
        dst = tg_ports[index ^ 1]
        lldp = {
            'chassisLen': (len(chassis.replace(':', '')) // 2) + 1,
            'chassisSubtype': 4,
            'chassisVarLen': len(chassis.replace(':', '')) // 2,
            'chassisId': chassis.replace(':', ''),
            'portLen': (len(port_val.replace(':', '')) // 2) + 1,
            'portSubtype': 3,
            'portVarLen': len(port_val.replace(':', '')) // 2,
            'portId': port_val.replace(':', ''),
            'ttlLen': 2,
            'ttlVal': ttl
        }
        lldp_stream = get_lldp_stream(dev_groups[src][0]['name'], dev_groups[dst][0]['name'], lldp, src_mac=random_mac(), name=index)
        streams.update(lldp_stream)

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(10)

    # 5.Verify that ports with lldp status disabled won't transmit and receive lldp packets,
    #   ports with status rx-and-tx transmitted and recievd lldp pkts
    for indx, port in enumerate(dut_ports):
        tx_before = await get_lldp_statistic(dev_name, port)
        neighbors = await get_neighbors_info(dev_name, port=port)

        if not indx % 2:
            assert port not in neighbors, f'Unexpected result, neighbour should be absent for {port}.\n{neighbors}'
        else:
            await verify_rx_lldp_fields(dev_name, port, lldps_verify[port]['chassis'],
                                        lldps_verify[port]['port'], 3, lldps_verify[port]['ttl'])

        await asyncio.sleep(tx_interval * 3)
        tx_after = await get_lldp_statistic(dev_name, port)
        if not indx % 2:
            assert tx_before == tx_after, f'tx_after {tx_after} are not equal to tx_before before {tx_before}'
        else:
            assert tx_after >= tx_before + 3, f'tx_after {tx_after} are not >= tx_before counters {tx_before}'
            await verify_tx_lldp_fields(dev_name, dent_dev, port, tx_interval, optional_tlvs=True)


@pytest.mark.usefixtures('cleanup_bonds')
async def test_lldp_lag(testbed):
    """
    Test Name: test_lldp_lag
    Test Suite: suite_functional_lldp
    Test Overview: Test lldp transmitted and received with port in lag
    Test Procedure:
    1. Create lag device and set first DUT port to down
    2. Add first port from DUT to lag
    3. Set first port DUT and lag device to up state
    4. Init interfaces
    5. Configure lldp tx-interval 2 sec, bond-slave-src-mac-type real and lldp status rx-and-tx
    6. Setup lldp packet for trasmitting to first DUT port and start sending
    7. Verify lldp pkt received and mandatory fields are as expected
    8. Verify lldp pkt's were transmitted with all fields as expected
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dev_name = dent_devices[0].host_name
    dent_dev = dent_devices[0]
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]
    lldp_interval = 2
    bond1 = 'bond1'
    wait = 5

    # 1.Create lag device and set first DUT port to down
    out = await IpLink.add(
        input_data=[{dev_name: [
            {'name': bond1, 'type': 'bond', 'mode': '802.3ad'}]}])
    err_msg = f'Verify that {bond1} was successfully added. \n{out}'
    assert not out[0][dev_name]['rc'], err_msg

    out = await IpLink.set(
        input_data=[{dev_name: [
            {'device': dut_ports[0], 'operstate': 'down'}]}])
    assert not out[0][dev_name]['rc'], f"Verify {dut_ports[0]} set to 'DOWN' state.\n{out}"

    # 2.Add first port from DUT to lag
    out = await IpLink.set(
        input_data=[{dev_name: [
            {'device': dut_ports[0], 'master': bond1}]}])
    err_msg = f'Verify that {dut_ports[0]} set to master .\n{out}'
    assert not out[0][dev_name]['rc'], err_msg

    # 3.Set first port DUT and lag device to up state
    out = await IpLink.set(
        input_data=[{dev_name: [
            {'device': dev, 'operstate': 'up'} for dev in [dut_ports[0], bond1]]}])
    assert not out[0][dev_name]['rc'], f"Verify {dut_ports[0]} and {bond1} set to 'UP' state.\n{out}"
    # 4.Init interfaces
    dev_groups = tgen_utils_dev_groups_from_config(
        [{'ixp': bond1, 'ip': '10.0.0.3', 'gw': '10.0.0.1', 'plen': 24, 'lag_members': [tg_ports[0]]},
         {'ixp': tg_ports[1], 'ip': '11.0.0.3', 'gw': '11.0.0.1', 'plen': 24}]
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    # 5.Configure lldp tx-interval 2 sec, bond-slave-src-mac-type real and lldp status rx-and-tx
    out = await Lldp.configure(
        input_data=[{dev_name: [
            {'lldp': '', 'tx-interval': lldp_interval}]}])
    assert not out[0][dev_name]['rc'], f'Failed to configure lldp tx-interval {lldp_interval}.\n{out}'

    out = await Lldp.configure(
        input_data=[{dev_name: [
            {'system': 'bond-slave-src-mac-type real'}]}])
    assert not out[0][dev_name]['rc'], f'Failed to configure lldp .\n{out}'

    tx_before = await get_lldp_statistic(dev_name, dut_ports[0])
    out = await Lldp.configure(
        input_data=[{dev_name: [
            {'interface': dut_ports[0], 'ports': '', 'lldp': '', 'status': 'rx-and-tx'}]}])
    assert not out[0][dev_name]['rc'], f'Failed to configure lldp status on port {dut_ports[0]}.\n{out}'

    # 6.Setup lldp packet for trasmitting to first DUT port and start sending
    chassis = random_mac()
    port = 'FastEthernet/19'
    ttl = 110
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
    lldp_stream = get_lldp_stream(dev_groups[bond1][0]['name'], dev_groups[tg_ports[1]][0]['name'], lldp)

    try:
        await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=lldp_stream)
    except AssertionError as e:
        if 'LAG' in str(e):
            pytest.skip(str(e))
        else:
            raise  # will re-raise the AssertionError

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(lldp_interval * wait)

    # 7.Verify lldp pkt received and mandatory fields are as expected
    await verify_rx_lldp_fields(dev_name, dut_ports[0], chassis, port, port_subtype, ttl)

    # 8.Verify lldp pkt's were transmitted with all fields as expected
    tx_after = await get_lldp_statistic(dev_name, dut_ports[0])
    assert tx_after >= tx_before + wait, f'tx_after {tx_after} >= tx_before {tx_before}'
    await verify_tx_lldp_fields(dev_name, dent_dev, dut_ports[0], lldp_interval, optional_tlvs=True)
