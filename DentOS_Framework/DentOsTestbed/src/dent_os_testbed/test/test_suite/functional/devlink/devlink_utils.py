import asyncio

from random import choice, randint
from math import isclose

from dent_os_testbed.utils.test_utils.tgen_utils import tgen_utils_get_swp_info


CPU_MAX_PPS = 4000
CPU_STAT_CODE_ACL_CODE_3 = '195'
DEVIATION = 0.1
RATE_UNITS = {
        'bit':  1,
        'kbit': 1_000,
        'gbit': 1_000_000_000,
        'bps':  1 * 8,
        'kbps': 1_000 * 8,
        'mbps': 1_000_000 * 8,
        'gbps': 1_000_000_000 * 8,
        'tbps': 1_000_000_000_000 * 8,
    }
SCT_MAP = {
        'stp': {'exp': 200, 'cpu_code': 26},
        'lacp': {'exp': 200, 'cpu_code': 27},
        'lldp': {'exp': 200, 'cpu_code': 28},
        'dhcp': {'exp': 100, 'cpu_code': 33},
        'arp_bc': {'exp': 100, 'cpu_code': 5},
        'arp_response': {'exp': 300, 'cpu_code': 188},
        'router_mc': {'exp': 100, 'cpu_code': 29},
        'ssh': {'exp': 1000, 'cpu_code': 207},
        'telnet': {'exp': 200, 'cpu_code': 208},
        'bgp': {'exp': 1000, 'cpu_code': 206},
        'local_route': {'exp': 10000, 'cpu_code': 161},
        'mac_to_me': {'exp': 100, 'cpu_code': 65},
        'ip_bc_mac': {'exp': 100, 'cpu_code': 19},
        'icmp': {'exp': 100, 'cpu_code': 209},
        'vrrp': {'exp': 200, 'cpu_code': 30},
        'acl_code_3': {'exp': 4000, 'cpu_code': 195},
    }


async def get_cpu_traps_rate_code_avg(dent_dev, cpu_stat_code, counter_type):
    """
    Execute bash func get_cpu_traps_rate_code_avg on DUT and parse output
    Args:
        dent_dev: Dent device
        cpu_stat_code (str): Cpu code to read counters from
        counter_type (str): Type of counters to read (sw or hw)
    Returns:
        Average rate of cpu trap
    """
    rc, out = await dent_dev.run_cmd(f'get_cpu_traps_rate_code_avg {cpu_stat_code} {counter_type}')
    assert not rc, f'get_cpu_traps_rate_code_avg failed with rc {rc}'
    return int(out.strip())


async def get_devlink_cpu_traps_rate_avg(dent_dev, trap_code):
    """
    Execute bash func get_devlink_cpu_traps_rate_avg on DUT and parse output
    Args:
        dent_dev: Dent device
        trap_code: Trap code for devlink trap show command
    Returns:
        Average rate of cpu trap
    """
    rc, out = await dent_dev.run_cmd(f'get_devlink_cpu_traps_rate_avg {trap_code}')
    assert not rc, f'get_devlink_cpu_traps_rate_avg failed with rc {rc}'
    return int(out.strip())


def randomize_rule_by_src_dst_field(tc_rule, rule_selectors):
    """
    Randomize applying rule by choosing src/dst field
    Args:
        tc_rule (dict): Dict with tc_rule
        rule_selectors (dict): Dict with rule selectors
    """
    mac, ip, port = choice(['src_mac', 'dst_mac', 'both']), choice(['src_ip', 'dst_ip', 'both']), choice(['src_port', 'dst_port', 'both'])

    if mac in ['src_mac', 'dst_mac']:
        del tc_rule['filtertype'][mac]
    if rule_selectors['want_ip']:
        if ip in ['src_ip', 'dst_ip']:
            del tc_rule['filtertype'][ip]
    if rule_selectors['want_port']:
        if port in ['src_port', 'dst_port']:
            del tc_rule['filtertype'][port]


def overwrite_src_dst_stream_fields(streams, tc_rule_copy, rule_selectors):
    """
    Overwrite streams src/dst fields for mac, ip and ports
    Args:
        streams (dict): Dict with streams configuration
        tc_rule_copy (dict): Copied original tc_rule
        rule_selectors (dict): Dict with rule selectors
    """
    stream_names = list(streams.keys())
    for name in stream_names:
        streams[name]['srcMac'] = tc_rule_copy['filtertype']['src_mac']
        streams[name]['dstMac'] = tc_rule_copy['filtertype']['dst_mac']
        if rule_selectors['want_vlan']:
            streams[name]['vlanID'] = tc_rule_copy['filtertype']['vlan_id']
        if rule_selectors['want_ip']:
            streams[name]['srcIp'] = tc_rule_copy['filtertype']['src_ip']
            streams[name]['dstIp'] = tc_rule_copy['filtertype']['dst_ip']
        if rule_selectors['want_port']:
            streams[name]['srcPort'] = tc_rule_copy['filtertype']['src_port']
            streams[name]['dstPort'] = tc_rule_copy['filtertype']['dst_port']
            streams[name]['ipproto'] = tc_rule_copy['filtertype']['ip_proto']
        if tc_rule_copy['protocol'] not in ['ipv6', 'ipv4', 'ip', '802.1q']:
            streams[name]['protocol'] = tc_rule_copy['protocol']


async def verify_cpu_traps_rate_code_avg(dent_dev, cpu_stat_code, exp_rate, counter_type='sw', deviation=DEVIATION, logs=False):
    """
    Verify cpu trap average rate is equal to expected rate including deviation
    Args:
        dent_dev: Dent device
        cpu_stat_code (str): Cpu code to read counters from
        exp_rate (float): Expected rate value
        counter_type (str): Type of counters to read (sw or hw)
        deviation (float): Deviation percentage
    """
    actual_rate = await get_cpu_traps_rate_code_avg(dent_dev, cpu_stat_code, counter_type)
    res = isclose(exp_rate, actual_rate, rel_tol=deviation)
    if logs:
        dent_dev.applog.info(f'CPU rate {actual_rate} expected {exp_rate} for stat_code {cpu_stat_code}')
    assert res, f'Current rate {actual_rate} exceeds expected rate {exp_rate} for cpu stat code {cpu_stat_code}'


async def verify_devlink_cpu_traps_rate_avg(dent_dev, trap_code, exp_rate, deviation=DEVIATION, logs=False):
    """
    Verify cpu trap average rate is equal to expected rate including deviation
    Args:
        dent_dev: Dent device
        trap_code (str): Trap code for devlink trap show command
        exp_rate (float): Expected rate value
        deviation (float): Deviation percentage
    """
    actual_rate = await get_devlink_cpu_traps_rate_avg(dent_dev, trap_code)
    res = isclose(exp_rate, actual_rate, rel_tol=deviation)
    if logs:
        dent_dev.applog.info(f'CPU rate {actual_rate} expected {exp_rate} for trap_code {trap_code}')
    assert res, f'Current rate {actual_rate} exceeds expected rate {exp_rate} for trap_code {trap_code}'


async def get_sct_streams(dent_dev, dev_groups, tg_ports, dut_port, rate=5000, pkt_size=150):
    def random_mac():
        return ':'.join(['02'] + [f'{randint(0, 255):02x}' for _ in range(5)])

    res = {}
    zero_ip = '0.0.0.0'
    tg_port_ip = dev_groups[tg_ports[0]][0]['ip']
    await tgen_utils_get_swp_info(dent_dev, dut_port, res)
    my_broadcast = '.'.join(res['broadcast'])
    my_ip = '.'.join(res['ip'])
    my_mac = res['mac']

    return {
        f'stp_{dut_port}': {
            'type': 'raw',
            'protocol': 'ip',
            'frameSize': pkt_size,
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcMac': random_mac(),
            'dstMac': '01:80:C2:00:00:00',
            'rate': SCT_MAP['stp']['exp'] + rate
        },
        f'lacp_{dut_port}': {
            'type': 'raw',
            'protocol': '0x8809',
            'frameSize': pkt_size,
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcMac': random_mac(),
            'dstMac': '01:80:c2:00:00:02',
            'rate': SCT_MAP['lacp']['exp'] + rate,
        },
        f'lldp_{dut_port}': {
            'type': 'raw',
            'protocol': '0x88cc',
            'frameSize': pkt_size,
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcMac': random_mac(),
            'dstMac': '01:80:c2:00:00:0e',
            'rate': SCT_MAP['lldp']['exp'] + rate,
        },
        f'dhcp_{dut_port}': {
            'type': 'raw',
            'protocol': 'ip',
            'frameSize': pkt_size,
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcMac': random_mac(),
            'dstMac': 'ff:ff:ff:ff:ff:ff',
            'srcIp': zero_ip,
            'dstIp': '255.255.255.255',
            'ipproto': 'udp',
            'dstPort': '68',
            'srcPort': '67',
            'rate': SCT_MAP['dhcp']['exp'] + rate,
        },
        f'arp_bc_{dut_port}': {
            'type': 'raw',
            'protocol': '0x806',
            'frameSize': pkt_size,
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcMac': random_mac(),
            'dstMac': 'ff:ff:ff:ff:ff:ff',
            'rate': SCT_MAP['arp_bc']['exp'] + rate,
        },
        f'arp_response_{dut_port}': {
            'type': 'raw',
            'protocol': '0x806',
            'frameSize': pkt_size,
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcMac': random_mac(),
            'dstMac': my_mac,
            'rate': SCT_MAP['arp_response']['exp'] + rate,
        },
        f'router_mc_{dut_port}': {
            'type': 'raw',
            'protocol': 'ip',
            'frameSize': pkt_size,
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcMac': '00:00:00:00:00:01',
            'dstMac': '00:00:00:00:00:02',
            'srcIp': zero_ip,
            'dstIp': '224.0.0.2',
            'rate': SCT_MAP['router_mc']['exp'] + rate,
        },
        f'ssh_{dut_port}': {
            'type': 'raw',
            'protocol': 'ip',
            'frameSize': pkt_size,
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcMac': '00:00:00:00:00:01',
            'dstMac': my_mac,
            'srcIp': zero_ip,
            'dstIp': my_ip,
            'ipproto': 'tcp',
            'dstPort': '22',
            'srcPort': '0',
            'rate': SCT_MAP['ssh']['exp'] + rate,
        },
        f'telnet_{dut_port}': {
            'type': 'raw',
            'protocol': 'ip',
            'frameSize': pkt_size,
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcMac': '00:00:00:00:00:01',
            'dstMac': my_mac,
            'srcIp': zero_ip,
            'dstIp': my_ip,
            'ipproto': 'tcp',
            'dstPort': '23',
            'srcPort': '0',
            'rate': SCT_MAP['telnet']['exp'] + rate,
        },
        f'bgp_{dut_port}': {
            'type': 'raw',
            'protocol': 'ip',
            'frameSize': pkt_size,
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcMac': '00:00:00:00:00:01',
            'dstMac': my_mac,
            'srcIp': zero_ip,
            'dstIp': my_ip,
            'ipproto': 'tcp',
            'dstPort': '179',
            'srcPort': '179',
            'rate': SCT_MAP['bgp']['exp'] + rate,
        },
        f'local_route_{dut_port}': {
            'type': 'raw',
            'protocol': 'ip',
            'frameSize': pkt_size,
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcMac': '00:00:00:00:00:01',
            'dstMac': my_mac,
            'srcIp': zero_ip,
            'dstIp': my_ip,
            'rate': SCT_MAP['local_route']['exp'] + rate,
        },
        f'mac_to_me_{dut_port}': {
            'type': 'raw',
            'protocol': '0x0000',
            'frameSize': pkt_size,
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcMac': random_mac(),
            'dstMac': my_mac,
            'rate': SCT_MAP['mac_to_me']['exp'] + rate,
        },
        f'icmp_{dut_port}': {
            'type': 'raw',
            'protocol': 'ip',
            'frameSize': pkt_size,
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcMac': '00:00:00:00:00:01',
            'dstMac': my_mac,
            'srcIp': tg_port_ip,
            'dstIp': my_ip,
            'ipproto': 'icmpv2',
            'icmpType': '8',
            'icmpCode': '0',
            'rate': SCT_MAP['icmp']['exp'] + rate,
        },
        f'ip_bc_mac_{dut_port}': {
            'type': 'raw',
            'protocol': 'ip',
            'frameSize': pkt_size,
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcMac': '00:00:00:00:00:01',
            'dstMac': 'ff:ff:ff:ff:ff:ff',
            'srcIp': tg_port_ip,
            'dstIp': my_broadcast,
            'rate': SCT_MAP['ip_bc_mac']['exp'] + rate,
        },
        f'vrrp_{dut_port}': {
            'type': 'raw',
            'protocol': 'ip',
            'frameSize': pkt_size,
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcMac': '00:00:5e:00:01:2c',
            'dstMac': '01:00:5e:00:00:12',
            'l3Proto': '112',
            'srcIp': tg_port_ip,
            'dstIp': '224.0.0.18',
            'ttl': '255',
            'rate': SCT_MAP['vrrp']['exp'] + rate
        }
    }


async def verify_cpu_rate(dent_dev, exp_rate_pps):
    await asyncio.gather(
        verify_cpu_traps_rate_code_avg(dent_dev, CPU_STAT_CODE_ACL_CODE_3, exp_rate_pps, logs=True),
        verify_devlink_cpu_traps_rate_avg(dent_dev, 'acl_code_3', exp_rate_pps, logs=True),
    )
