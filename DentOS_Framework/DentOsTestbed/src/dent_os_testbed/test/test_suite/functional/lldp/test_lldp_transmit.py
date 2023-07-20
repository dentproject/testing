import pytest
import asyncio

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.lldp.lldp import Lldp

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_dev_groups_from_config,
    tgen_utils_traffic_generator_connect
)

from dent_os_testbed.utils.test_utils.tb_utils import tb_device_tcpdump
from dent_os_testbed.test.test_suite.functional.lldp.lldp_utils import (
    parse_lldp_pkt, get_lldp_statistic,
    verify_tx_lldp_fields, ERR_MSG_TX
)

pytestmark = [
    pytest.mark.suite_functional_lldp,
    pytest.mark.asyncio,
    pytest.mark.usefixtures('check_and_restore_lldp_service', 'cleanup_tgen')
]


@pytest.mark.parametrize('scenario', ['basic', 'mandatory', 'optional'])
async def test_lldp_transmitted(testbed, scenario):
    """
    Test Name: test_lldp_transmitted
    Test Suite: suite_functional_lldp
    Test Overview: Test Lldp transmitted with different scenarios
    Test Procedure:
    1. Init interfaces and set first DUT port up
    2. Enable first DUT port to transmmit lldp units
    3. Collect lldp units tx stats from first DUT port
    4. Configure lldp tx-interval to 2 sec
    5. Verify lldp unit was transmitted from DUT first port:
       basic: Verify that lldp tx stats incremented
       mandatory: Sniff and capture transmitted lldp packet, verify mandatory fields are as expected
       optional: Sniff and capture transmitted lldp packet, verify mandatory and optional fields are as expected
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dev_name = dent_devices[0].host_name
    dent_dev = dent_devices[0]
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]
    lldp_interval = 2
    wait_time = 3

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

    # 2.Enable first DUT port to transmmit lldp units
    out = await Lldp.configure(
        input_data=[{dev_name: [
            {'interface': dut_ports[0], 'ports': '', 'lldp': '', 'status': 'tx-only'}]}])
    assert not out[0][dev_name]['rc'], f'Failed to configure lldp status on port {dut_ports[0]}.\n{out}'
    # 3.Collect lldp units tx stats from first DUT port
    tx_before = await get_lldp_statistic(dev_name, dut_ports[0])

    # 4.Configure lldp tx-interval to 2 sec
    out = await Lldp.configure(
        input_data=[{dev_name: [
            {'lldp': '', 'tx-interval': lldp_interval}]}])
    assert not out[0][dev_name]['rc'], f'Failed to configure lldp tx-interval.\n{out}'

    # 5.Verify lldp unit was transmitted from DUT first port
    if scenario == 'basic':
        # basic: Verify that lldp tx stats incremented
        await asyncio.sleep(lldp_interval * wait_time)
        tx_after = await get_lldp_statistic(dev_name, dut_ports[0])
        assert tx_after >= tx_before + wait_time, f'tx_after {tx_after} != expected amount of pkts {tx_before + wait_time}'

    elif scenario == 'mandatory':
        # mandatory: Sniff and capture transmitted lldp packet, verify mandatory fields are as expected
        await verify_tx_lldp_fields(dev_name, dent_dev, dut_ports[0], lldp_interval)

    elif scenario == 'optional':
        # optional: Sniff and capture transmitted lldp packet, verify mandatory and optional fields are as expected
        await verify_tx_lldp_fields(dev_name, dent_dev, dut_ports[0], lldp_interval, optional_tlvs=True)


@pytest.mark.parametrize('scenario', ['disabled', 'port_down', 'interval'])
async def test_lldp_tx(testbed, scenario):
    """
    Test Name: test_lldp_tx
    Test Suite: suite_functional_lldp
    Test Overview: Test Lldp transmitted with different status scenarios
    Test Procedure:
    1. Init interfaces and set first DUT port up
    2. Set first DUT port down in case of tx_port_down
    3. Configure lldp status on first DUT port disabled/tx-only depending from scenario
    4. Configure lldp tx-interval to 2 sec
    5. Collect lldp units tx stats from first DUT port and sleep 6 sec
    6. Verify that lldp pkts weren't transmitted from DUT first port in case of scenarios: port_down, disabled
       port_down: Set first DUT port up, sleep interval time and verify that lldp pkt were sent from port
       interval: Verify that lldp pkts were transmitted from port
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dev_name = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]
    lldp_interval = 2
    wait_time = 3

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

    status = 'disabled' if scenario == 'disabled' else 'tx-only'
    # 2.Set first DUT port down in case of tx_port_down
    if scenario == 'port_down':
        out = await IpLink.set(
            input_data=[{dev_name: [
                {'device': dut_ports[0], 'operstate': 'down'}]}])
        assert not out[0][dev_name]['rc'], f"Verify {dut_ports[0]} set to 'DOWN' state.\n{out}"

    # 3.Configure lldp status on first DUT port disabled/tx-only depending from scenario
    # 4.Configure lldp tx-interval to 2 sec
    out = await Lldp.configure(
            input_data=[{dev_name: [
                {'interface': dut_ports[0], 'ports': '', 'lldp': '', 'status': status},
                {'lldp': '', 'tx-interval': lldp_interval}]}])
    assert not out[0][dev_name]['rc'], \
        f'Failed to configure lldp status on port {dut_ports[0]} and tx-interval.\n{out}'

    # 5.Collect lldp units tx stats from first DUT port and sleep 6 sec
    tx_before = await get_lldp_statistic(dev_name, dut_ports[0])
    await asyncio.sleep(lldp_interval * wait_time)

    # 6.Verify that lldp pkts weren't transmitted from DUT first port
    if scenario in ['disabled', 'port_down']:
        tx_after = await get_lldp_statistic(dev_name, dut_ports[0])
        assert tx_after == tx_before, f'tx_counter_after {tx_after} == tx_counters_before {tx_before}'

        if scenario == 'port_down':
            # tx_port_down: Set first DUT port up, sleep interval time and verify that lldp pkt were sent from port
            out = await IpLink.set(
                input_data=[{dev_name: [
                    {'device': dut_ports[0], 'operstate': 'up'}]}])
            assert not out[0][dev_name]['rc'], f"Verify {dut_ports[0]} set to 'UP' state.\n{out}"

            await asyncio.sleep(lldp_interval * (wait_time + 2))
            tx_after = await get_lldp_statistic(dev_name, dut_ports[0])
            assert tx_after >= tx_before + wait_time, \
                f'tx_counter_after {tx_after} >= tx_counters_before {tx_before + wait_time}'
    else:
        # tx_interval: Verify that lldp pkts were transmitted from port
        tx_after = await get_lldp_statistic(dev_name, dut_ports[0])
        assert tx_after >= tx_before + wait_time, f'tx_counter_after {tx_after} >= tx_counters_before {tx_before + wait_time}'


async def test_lldp_tx_hold(testbed):
    """
    Test Name: test_lldp_tx_hold
    Test Suite: suite_functional_lldp
    Test Overview: Test Lldp pkt have modified ttl value after setting tx-hold
    Test Procedure:
    1. Init interfaces and set first DUT port up
    2. Configure lldp status tx-only for first DUT port, tx-interval 2 sec and tx-hold 500 sec
    3. Verify that transmitted lldp packet have ttl value set to tx-hold * tx-interval
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dev_name = dent_devices[0].host_name
    dent_dev = dent_devices[0]
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]
    lldp_interval = 2
    tx_hold = 500

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

    # 2.Configure lldp status tx-only for first DUT port, tx-interval 2 sec and tx-hold 500 sec
    out = await Lldp.configure(
        input_data=[{dev_name: [
            {'lldp': '', 'tx-hold': tx_hold},
            {'interface': dut_ports[0], 'ports': '', 'lldp': '', 'status': 'tx-only'},
            {'lldp': '', 'tx-interval': lldp_interval}]}])
    assert not out[0][dev_name]['rc'], f'Failed to configure lldp status, tx-hold, tx-interval.\n{out}'

    # 3.Verify that transmitted lldp packet have ttl value set to tx-hold * tx-interval
    res = await tb_device_tcpdump(dent_dev, dut_ports[0], 'ether proto 0x88cc -vnne', timeout=lldp_interval + 1, dump=True)
    parsed_lldp = parse_lldp_pkt(['Time to Live TLV'], res)
    assert str(tx_hold * lldp_interval) in parsed_lldp['Time to Live TLV'], \
        ERR_MSG_TX.format(str(tx_hold * lldp_interval), 'Time to Live TLV', parsed_lldp['Time to Live TLV'])
