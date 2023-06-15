import asyncio
import pytest
import json

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.tc.tc_qdisc import TcQdisc
from dent_os_testbed.lib.tc.tc_chain import TcChain
from dent_os_testbed.constants import PLATFORMS_CONSTANTS
from dent_os_testbed.lib.bridge.bridge_link import BridgeLink
from dent_os_testbed.utils.FileHandlers.LocalFileHandler import LocalFileHandler

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
    pytest.mark.suite_functional_table_size,
    pytest.mark.asyncio,
]


# Creates 10_000 route entries
fill_route_table_cmd = """
for x in `seq 40`
do
    for y in `seq 250`
    do
        ip ro add dev {} 1.1.$x.$y
    done
done"""


# Creates `count` acl rules
fill_acl_table_cmd = """
for x in `seq {count}`
do
    tc filter add dev {port} ingress flower action pass
done"""


async def get_table_sizes(dent_device):
    rc, model = await dent_device.run_cmd('cat /etc/onl/platform')
    assert rc == 0, 'Failed to get device platform name'
    model = model.strip('\n')
    table_sizes = LocalFileHandler(dent_device.applog).read(PLATFORMS_CONSTANTS)
    return json.loads(table_sizes)[model]


@pytest.mark.usefixtures('cleanup_ip_addrs')
async def test_ipv4_route_table_fill(testbed):
    """
    Test Name: test_ipv4_route_table_fill
    Test Suite: suite_functional_table_size
    Test Overview: Test filling up the routing table
    Test Procedure:
    1. Init interfaces
    2. Configure port
    3. Fill up route table
    4. Verify amount of route entries with matching mask
    """
    # 1. Init interfaces
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 1)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    port = tgen_dev.links_dict[dent][1][0]
    expected_route_entries = (await get_table_sizes(dent_dev))['route_table_size']

    # 2. Configure port up
    out = await IpLink.set(input_data=[{dent: [{'device': port, 'operstate': 'up'}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # 3. Fill up route table
    rc, out = await dent_dev.run_cmd(fill_route_table_cmd.format(port))
    assert rc == 0, 'Failed to fill routing table'

    # 4. Verify amount of route entries with matching mask
    rc, out = await dent_dev.run_cmd('ip route | grep rt_offload | wc -l')
    assert rc == 0, 'Failed to get number of offloaded route entries'
    assert int(out) >= expected_route_entries, \
        f'Device should support {expected_route_entries} offloaded routing entries, ' \
        f'but only offloaded {out}'


@pytest.mark.usefixtures('cleanup_bridges', 'cleanup_tgen')
async def test_bridging_mac_table_size(testbed):
    """
    Test Name: test_bridging_mac_table_size
    Test Suite: suite_functional_table_size
    Test Overview: Verify amount of extern_learn offload entities in the mac table.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1, swp2, swp3, swp4 master br0.
    3.  Set bridge br0 admin state UP.
    4.  Set entities swp1, swp2, swp3, swp4 UP state.
    5.  Set ports swp1, swp2, swp3, swp4 learning ON.
    6.  Send traffic for filling bridge address table.
    7.  Verify amount of extern_learn offload entities.
    """
    num_tg_ports = 2
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], num_tg_ports)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 10
    mac_count = 4000
    bridge = 'br0'

    out = await IpLink.add(
        input_data=[{device_host_name: [
            {'device': bridge, 'type': 'bridge'}]}])
    assert out[0][device_host_name]['rc'] == 0, f'Verify that bridge created.\n{out}'

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': bridge, 'operstate': 'up'}]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that bridge set to 'UP' state.\n{out}"

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': port, 'master': bridge, 'operstate': 'up'} for port in ports]}])
    assert out[0][device_host_name]['rc'] == 0, \
        f"Verify that bridge entities set to 'UP' state and links enslaved to bridge.\n{out}"

    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {'device': port, 'learning': True} for port in ports]}])
    assert out[0][device_host_name]['rc'] == 0, \
        f"Verify that entities set to learning 'ON' state.\n{out}"

    dev_groups = tgen_utils_dev_groups_from_config([
        {'ixp': tg_ports[0], 'ip': '1.1.1.1', 'gw': '1.1.1.2', 'plen': 24},
        {'ixp': tg_ports[1], 'ip': '1.1.1.2', 'gw': '1.1.1.1', 'plen': 24},
    ])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    streams = {
        'streamA': {
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcMac': {'type': 'increment',
                       'start': '00:00:00:00:00:35',
                       'step': '00:00:00:00:10:00',
                       'count': mac_count},
            'dstMac': 'aa:bb:cc:dd:ee:11',
            'type': 'raw',
            'frame_rate_type': 'line_rate',
            'rate': 1,  # %
        }
    }
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        assert loss == 0, f'Expected loss: 0%, actual: {loss}%'

    rc, out = await dent_dev.run_cmd("bridge fdb show br br0 | grep 'extern_learn.*offload' | wc -l")
    assert rc == 0, "Failed to grep 'extern_learn.*offload'."

    amount = int(out) - num_tg_ports
    assert amount == mac_count, \
        f'Expected count of extern_learn offload entities: 4000, Actual count: {amount}'


@pytest.mark.usefixtures('cleanup_qdiscs')
async def test_acl_table_size(testbed):
    """
    Test Name: test_acl_table_size
    Test Suite: suite_functional_table_size
    Test Overview: Test filling up the acl table
    Test Procedure:
    1. Init interfaces
    2. Create ingress qdisc
    3. Fill up acl table using a default chain
    4. Verify amount of acl rules
    5. Clear acl table
    6. Fill up acl table using a non-default chain
    7. Verify amount of acl rules
    """
    # 1. Init interfaces
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 1)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    port = tgen_dev.links_dict[dent][1][0]
    size = await get_table_sizes(dent_dev)
    handle = 10
    sw_rules = 100

    # 2. Create ingress qdisc
    out = await TcQdisc.add(input_data=[{dent: [
        {'dev': port, 'direction': 'ingress', 'handle': handle}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create qdisc'

    # 3. Fill up acl table using a default chain
    rule_count = size['max_acl_rules']
    rc, out = await asyncio.wait_for(
        dent_dev.run_cmd(fill_acl_table_cmd.format(port=port, count=rule_count + sw_rules)),
        timeout=3*60)  # 3mins
    assert rc == 0, 'Failed to fill acl table'

    # 4. Verify amount of acl rules
    rc, out = await dent_dev.run_cmd(f'tc filter show dev {port} ingress | grep in_hw_count | wc -l')
    assert rc == 0, 'Failed to get number of acl rules in hw'
    assert int(out) == rule_count, \
        f'Number of offloaded rules ({out}) does not match number of created rules ({rule_count})'

    rc, out = await dent_dev.run_cmd(f'tc filter show dev {port} ingress | grep used_hw_stats | wc -l')
    assert rc == 0, 'Failed to get number of acl rules with counters'
    assert int(out) == rule_count, \
        f'Number of offloaded rules with counters ({out}) does not match expected number ({rule_count})'

    # 5. Clear acl table
    out = await TcQdisc.delete(input_data=[{dent: [
        {'dev': port, 'direction': 'ingress', 'handle': handle}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create qdisc'

    out = await TcQdisc.add(input_data=[{dent: [
        {'dev': port, 'direction': 'ingress', 'handle': handle}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create qdisc'

    # 6. Fill up acl table using a non-default chain
    out = await TcChain.add(input_data=[{dent: [
        {'dev': port, 'direction': 'ingress', 'chain': 0, 'filtertype': {}}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to create qdisc'

    rule_count = size['max_acl_rules_chain']
    rc, out = await asyncio.wait_for(
        dent_dev.run_cmd(fill_acl_table_cmd.format(port=port, count=rule_count + sw_rules)),
        timeout=10*60)  # 10mins
    assert rc == 0, 'Failed to fill acl table'

    # 7. Verify amount of acl rules
    rc, out = await dent_dev.run_cmd(f'tc f show dev {port} ingress | grep in_hw_count | wc -l')
    assert rc == 0, 'Failed to get number of acl rules in hw'
    assert int(out) == rule_count, \
        f'Number of offloaded rules ({out}) does not match number of created rules ({rule_count})'

    rc, out = await dent_dev.run_cmd(f'tc f show dev {port} ingress | grep used_hw_stats | wc -l')
    assert rc == 0, 'Failed to get number of acl rules with counters'
    assert int(out) == rule_count, \
        f'Number of offloaded rules with counters ({out}) does not match expected number ({rule_count})'
