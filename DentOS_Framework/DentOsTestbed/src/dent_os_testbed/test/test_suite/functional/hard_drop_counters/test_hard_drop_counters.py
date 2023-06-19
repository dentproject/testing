import asyncio
import pytest

from random import choice, randint
from math import isclose
from ipaddress import IPv4Network

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.ip.ip_neighbor import IpNeighbor

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_clear_traffic_items,
    tgen_utils_get_swp_info,
    tgen_utils_get_traffic_stats,
)

pytestmark = [
    pytest.mark.suite_functional_hard_drop_counters,
    pytest.mark.usefixtures('define_bash_utils', 'cleanup_ip_addrs'),
    pytest.mark.asyncio,
]

DROP_COUNTERS_MAP = {
    'ip_uc_dip_da_mismatch_': 138,
    'illegal_ipv4_hdr_checksum_': 137,
    'illegal_ipv4_hdr_length_': 137,
    'illegal_ip_addr_dip_zero_': 136,
    'illegal_ip_addr_host_sip_': 136,
    'illegal_ip_addr_host_dip_': 136,
    'ip_sip_is_zero_': 145,
}


async def get_illegal_drop_streams(dent_dev, dev_groups, tg_ports, dut_port, mac, tg_ip, size=1000, rate=100):
    """
    Generate L3 drop streams
    """
    def gen_random_ipv4(multicast=False):
        first_octet = randint(224, 239) if multicast else randint(1, 223)
        return f'{first_octet}.{randint(1, 250)}.{randint(1, 250)}.{randint(1, 250)}'

    swp_info = {}
    await tgen_utils_get_swp_info(dent_dev, dut_port, swp_info)
    zero_ip = '0.0.0.0'
    ip_proto = choice(['', 'tcp', 'udp'])
    src_port = randint(1, 65535)
    dst_port = randint(1, 65535)

    return {
        f'ip_uc_dip_da_mismatch_{dut_port}': {
            'type': 'raw',
            'protocol': 'ip',
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcMac': mac,
            'dstMac': swp_info['mac'],
            'frameSize': size,
            'srcIp': tg_ip,
            'dstIp': gen_random_ipv4(multicast=True),
            'ttl': '64',
            'rate': rate,
            'frame_rate_type': 'line_rate',
            },
        f'illegal_ipv4_hdr_checksum_{dut_port}': {
            'type': 'raw',
            'protocol': 'ip',
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcMac': mac,
            'dstMac': swp_info['mac'],
            'frameSize': size,
            'srcIp': tg_ip,
            'dstIp': gen_random_ipv4(),
            'ttl': '64',
            'ipproto': ip_proto,
            'dstPort': dst_port,
            'srcPort': src_port,
            'ipv4Checksum': '0',
            'rate': rate,
            'frame_rate_type': 'line_rate',
            },
        f'illegal_ipv4_hdr_length_{dut_port}': {
            'type': 'raw',
            'protocol': 'ip',
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcMac': mac,
            'dstMac': swp_info['mac'],
            'frameSize': size,
            'srcIp': tg_ip,
            'dstIp': gen_random_ipv4(),
            'ttl': '64',
            'ipproto': ip_proto,
            'dstPort': dst_port,
            'srcPort': src_port,
            'ipv4HeaderLength': choice(range(4)),
            'rate': rate,
            'frame_rate_type': 'line_rate',
            },
        f'illegal_ip_addr_dip_zero_{dut_port}': {
            'type': 'raw',
            'protocol': 'ip',
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcMac': mac,
            'dstMac': swp_info['mac'],
            'frameSize': size,
            'srcIp': tg_ip,
            'dstIp': zero_ip,
            'ttl': '64',
            'rate': rate,
            'frame_rate_type': 'line_rate',
            },
        f'illegal_ip_addr_host_sip_{dut_port}': {
            'type': 'raw',
            'protocol': 'ip',
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcMac': mac,
            'dstMac': swp_info['mac'],
            'frameSize': size,
            'srcIp': '127.0.0.1',
            'dstIp': gen_random_ipv4(),
            'ttl': '64',
            'rate': rate,
            'frame_rate_type': 'line_rate',
            },
        f'illegal_ip_addr_host_dip_{dut_port}': {
            'type': 'raw',
            'protocol': 'ip',
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcMac': mac,
            'dstMac': swp_info['mac'],
            'frameSize': size,
            'srcIp': tg_ip,
            'dstIp': '127.0.0.1',
            'ttl': '64',
            'rate': rate,
            'frame_rate_type': 'line_rate',
            },
        f'ip_sip_is_zero_{dut_port}': {
            'type': 'raw',
            'protocol': 'ip',
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcMac': mac,
            'dstMac': swp_info['mac'],
            'frameSize': size,
            'srcIp': zero_ip,
            'dstIp': tg_ip,
            'ttl': '64',
            'rate': rate,
            'frame_rate_type': 'line_rate',
            },
    }


def random_mac():
    return ':'.join(['02'] + [f'{randint(0, 255):02x}' for _ in range(5)])


async def verify_drop_rate_avg(dent_dev, cpu_stat_code, exp_rate, deviation=0.1, logs=False):
    """
    Verify average drop rate is as expected
    Args:
        dent_dev: Dent device
        cpu_stat_code (str): Cpu code to read counters from
        exp_rate (float): Expected rate value
        deviation (float): Deviation percentage
    """
    rc, out = await dent_dev.run_cmd(f'get_drops_rate_code_avg {cpu_stat_code}')
    assert not rc, f'get_drops_rate_code_avg failed with rc {rc}'
    actual_rate = int(out.strip())
    res = isclose(exp_rate, actual_rate, rel_tol=deviation)
    if logs:
        dent_dev.applog.info(f'Drop rate {actual_rate} expected {exp_rate} for stat_code {cpu_stat_code}')
    assert res, f'Current drop rate {actual_rate} exceeds expected rate {exp_rate} including deviation {deviation}'


async def get_drop_counters(dent_dev):
    """
    Get hard drop counters
    Args:
        dent_dev: Dent device
    Returns:
        Dict with L3 stat_codes and amount of droped pkts
    """
    rc, out = await dent_dev.run_cmd('cat /sys/kernel/debug/prestera/hw_counters/drops/cpu_code_stats')
    assert not rc, f'Failed to read all hw counters \n{out}'
    out = out.replace('\x00', '')
    counters = {}
    if out:
        for line in out.splitlines():
            stat_code, pkts = line.split(':')
            counters[int(stat_code)] = int(pkts)
    return counters


def verify_expected_counters(counters_old, counters_new):
    """
    Verify that only expected L3 hard_drop counters are increment
    Args:
        counters_old (dict): Dict with old drop counters
        counters_new (dict): Dict with new drop counters taken after
    """
    for cpu_code, dropped in counters_new.items():
        if cpu_code in DROP_COUNTERS_MAP.values():
            if cpu_code in counters_old:
                assert dropped > counters_old[cpu_code], f'Counetrs after {dropped} are not greater than counters before {counters_old[cpu_code]} for {dropped}'
            else:
                continue
        else:
            if cpu_code in counters_old:
                assert dropped == counters_old[cpu_code], f'Unexpected counters were incremeneted, before {counters_old[cpu_code]} after {dropped} for {cpu_code}'
            else:
                pytest.fail(f'Unexpected counters were incremented {cpu_code}, {dropped}, counters before {counters_old}')


@pytest.mark.parametrize('ports_num', [1, 3])
async def test_hw_drop_l3(testbed, ports_num):
    """
    Test Name: test_hw_drop_l3
    Test Suite: suite_functional_hard_drop_counters
    Test Overview: Test L3 hard_drop counters with 1/3 ports
    Test Procedure:
    1. Set link up on interfaces on all participant ports
    2. Configure ip address on ports and connect devices
    3. Add Static Arp entry on the first and second ports connected to ixia
    4. Set up streams matching all L3 invalid packets types on tx ports
    5. Transmit traffic and verify drop counters updated according to the rate packets sent
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dev_name = dent_devices[0].host_name
    dent_dev = dent_devices[0]
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]
    frame_size = randint(128, 1400)
    macs = {port: random_mac() for port in dut_ports}
    ip_network = IPv4Network('2.2.2.0/24')

    # 1.Set link up on interfaces on all participant ports
    out = await IpLink.set(
        input_data=[{dev_name: [
            {'device': port, 'operstate': 'up'} for port in dut_ports]}])
    err_msg = f"Verify that ports {dut_ports} set to 'UP' state.\n{out}"
    assert not out[0][dev_name]['rc'], err_msg

    # 2.Configure ip address on ports and connect devices
    addr_map = []
    for p_indx in range(ports_num):
        ip_addr = ip_network[1]
        if ports_num == 1 or p_indx == 2:
            addr_map.append((dut_ports[p_indx], tg_ports[p_indx], str(ip_addr + 1), str(ip_addr), ip_network.prefixlen,
                             str(ip_network.broadcast_address), macs[dut_ports[p_indx]]))
            addr_map.append((
                dut_ports[p_indx + 1], tg_ports[p_indx + 1], '0.0.0.0',
                '0.0.0.1', 24, '0.0.0.255', macs[dut_ports[p_indx + 1]]))
        else:
            addr_map.append((
                dut_ports[p_indx], tg_ports[p_indx], str(ip_addr + 1),
                str(ip_addr), ip_network.prefixlen, str(ip_network.broadcast_address), macs[dut_ports[p_indx]]))
        ip_network = IPv4Network(f'{ip_network[0] + 256}/{ip_network.prefixlen}')

    out = await IpAddress.add(input_data=[{dev_name: [
        {'dev': port, 'prefix': f'{ip}/{plen}', 'broadcast': broadcast}
        for port, _, _, ip, plen, broadcast, _ in addr_map]}])
    assert not out[0][dev_name]['rc'], f'Failed to add IP addr to ports \n{out}'

    dev_groups = tgen_utils_dev_groups_from_config(
        [{'ixp': tg_port, 'ip': tg_ip, 'gw': gw, 'plen': plen}
         for _, tg_port, tg_ip, gw, plen, _, _ in addr_map])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    # 3.Add Static Arp entry on the first and second ports connected to ixia
    out = await IpNeighbor.add(input_data=[{dev_name: [
        {'dev': port, 'address': nei_ip, 'lladdr': lladdr}
        for port, _, nei_ip, _, _, _, lladdr in addr_map[:ports_num]
    ]}])
    assert not out[0][dev_name]['rc'], 'Failed to add static arp entries'

    # 4.Set up streams matching all L3 invalid packets types on tx ports
    streams = {}
    for p_indx in range(ports_num):
        src_dst_ports = [tg_ports[p_indx], tg_ports[p_indx ^ 1]]
        port_streams = await get_illegal_drop_streams(dent_dev, dev_groups, src_dst_ports, dut_ports[p_indx],
                                                      macs[dut_ports[p_indx]], addr_map[p_indx][2], size=frame_size)
        streams.update(port_streams)
    # Update ip_sip_is_zero_ when 1 port (tg_port[1] will be as tx_port)
    if ports_num == 1:
        swp_info = {}
        await tgen_utils_get_swp_info(dent_dev, dut_ports[1], swp_info)
        streams[f'ip_sip_is_zero_{dut_ports[0]}']['ip_source'] = dev_groups[tg_ports[1]][0]['name']
        streams[f'ip_sip_is_zero_{dut_ports[0]}']['ip_destination'] = dev_groups[tg_ports[0]][0]['name']
        streams[f'ip_sip_is_zero_{dut_ports[0]}']['dstMac'] = swp_info['mac']
        streams[f'ip_sip_is_zero_{dut_ports[0]}']['srcMac'] = macs[dut_ports[1]]

    # 5.Transmit traffic and verify drop counters updated according to the rate packets sent
    for stream_name in DROP_COUNTERS_MAP:
        streams_to_apply = {name: streams[name] for name in streams if name.startswith(stream_name)}
        await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams_to_apply)
        await tgen_utils_start_traffic(tgen_dev)
        await asyncio.sleep(15)
        stats = await tgen_utils_get_traffic_stats(tgen_dev)
        exp_rate = sum([int(row['Frames Tx. Rate']) for row in stats.Rows])
        await verify_drop_rate_avg(dent_dev, DROP_COUNTERS_MAP[stream_name], exp_rate)
        await tgen_utils_stop_traffic(tgen_dev)
        await asyncio.sleep(6)
        await tgen_utils_clear_traffic_items(tgen_dev)


async def test_hw_drop_l3_exp_counters(testbed):
    """
    Test Name: test_hw_drop_l3_exp_counters
    Test Suite: suite_functional_hard_drop_counters
    Test Overview: Test that only expected L3 hard_drop counters are incremented
    Test Procedure:
    1. Get all hard drop counters
    2. Set link up on interfaces on all participant ports
    3. Configure ip address on ports and connect devices
    4. Add Static Arp entry on the first and second ports connected to ixia
    5. Set up streams matching all L3 invalid packets types on tx ports
    6. Transmit traffic and verify that only expected drop counters get incremented
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dev_name = dent_devices[0].host_name
    dent_dev = dent_devices[0]
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]
    frame_size = randint(128, 1400)
    macs = {port: random_mac() for port in dut_ports}

    # 1.Get all hard drop counters
    counters_old = await get_drop_counters(dent_dev)

    # 2.Set link up on interfaces on all participant ports
    out = await IpLink.set(
        input_data=[{dev_name: [
            {'device': port, 'operstate': 'up'} for port in dut_ports]}])
    err_msg = f"Verify that ports {dut_ports} set to 'UP' state.\n{out}"
    assert not out[0][dev_name]['rc'], err_msg

    # 3.Configure ip address on ports and connect devices
    addr_map = [(dut_ports[0], tg_ports[0], '3.3.3.1', '3.3.3.3', 24, '3.3.3.255', macs[dut_ports[0]]),
                (dut_ports[1], tg_ports[1], '0.0.0.1', '0.0.0.0', 24, '0.0.0.255', macs[dut_ports[1]])]

    out = await IpAddress.add(input_data=[{dev_name: [
        {'dev': port, 'prefix': f'{ip}/{plen}', 'broadcast': broadcast}
        for port, _, _, ip, plen, broadcast, _ in addr_map]}])
    assert not out[0][dev_name]['rc'], f'Failed to add IP addr to ports \n{out}'

    dev_groups = tgen_utils_dev_groups_from_config(
        [{'ixp': tg_port, 'ip': tg_ip, 'gw': gw, 'plen': plen}
         for _, tg_port, tg_ip, gw, plen, _, _ in addr_map])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    # 4.Add Static Arp entry on the first and second ports connected to ixia
    out = await IpNeighbor.add(input_data=[{dev_name: [
        {'dev': port, 'address': nei_ip, 'lladdr': lladdr}
        for port, _, nei_ip, _, _, _, lladdr in addr_map
    ]}])
    assert not out[0][dev_name]['rc'], 'Failed to add static arp entries'

    # 5.Set up streams matching all L3 invalid packets types on tx ports
    # 6.Transmit traffic and verify that only expected drop counters get incremented
    streams = {}
    port_streams = await get_illegal_drop_streams(dent_dev, dev_groups, tg_ports[:2], dut_ports[0],
                                                  macs[dut_ports[0]], addr_map[0][2], size=frame_size, rate=10)
    streams.update(port_streams)
    # Update ip_sip_is_zero_ when 1 port (tg_port[1] will be as tx_port)
    swp_info = {}
    await tgen_utils_get_swp_info(dent_dev, dut_ports[1], swp_info)
    streams[f'ip_sip_is_zero_{dut_ports[0]}']['ip_source'] = dev_groups[tg_ports[1]][0]['name']
    streams[f'ip_sip_is_zero_{dut_ports[0]}']['ip_destination'] = dev_groups[tg_ports[0]][0]['name']
    streams[f'ip_sip_is_zero_{dut_ports[0]}']['dstMac'] = swp_info['mac']
    streams[f'ip_sip_is_zero_{dut_ports[0]}']['srcMac'] = macs[dut_ports[1]]

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(10)
    counters_new = await get_drop_counters(dent_dev)
    verify_expected_counters(counters_old, counters_new)
    await tgen_utils_stop_traffic(tgen_dev)
