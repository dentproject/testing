from random import choice
from math import isclose

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
        if rule_selectors['want_ip']:
            streams[name]['srcIp'] = tc_rule_copy['filtertype']['src_ip']
            streams[name]['dstIp'] = tc_rule_copy['filtertype']['dst_ip']
        if rule_selectors['want_port']:
            streams[name]['srcPort'] = tc_rule_copy['filtertype']['src_port']
            streams[name]['dstPort'] = tc_rule_copy['filtertype']['dst_port']
        if tc_rule_copy['protocol'] not in ['ipv6', 'ipv4', 'ip', '802.1q']:
            streams[name]['protocol'] = tc_rule_copy['protocol']


async def verify_cpu_traps_rate_code_avg(dent_dev, cpu_stat_code, exp_rate, counter_type='sw', deviation=DEVIATION):
    """
    Verify cpu trap average rate is equal to expected rate including deviation
    Args:
        dent_dev: Dent device
        cpu_stat_code (str): Cpu code to read counters from
        exp_rate (float): Expected rate value
        counter_type (str): Type of counters to read (sw or hw)
        deviation (float): Deviation percentage
    """
    rc, out = await dent_dev.run_cmd(f'get_cpu_traps_rate_code_avg {cpu_stat_code} {counter_type}')
    assert not rc, f'get_cpu_traps_rate_code_avg failed with rc {rc}'
    actual_rate = int(out.strip())
    res = isclose(exp_rate, actual_rate, rel_tol=deviation)
    assert res, f'Current rate {actual_rate} exceeds expected rate {exp_rate} including deviation {deviation}'


async def verify_devlink_cpu_traps_rate_avg(dent_dev, trap_code, exp_rate, deviation=DEVIATION):
    """
    Verify cpu trap average rate is equal to expected rate including deviation
    Args:
        dent_dev: Dent device
        trap_code (str): Trap code for devlink trap show command
        exp_rate (float): Expected rate value
        deviation (float): Deviation percentage
    """
    rc, out = await dent_dev.run_cmd(f'get_devlink_cpu_traps_rate_avg {trap_code}')
    assert not rc, f'get_devlink_cpu_traps_rate_avg failed with rc {rc}'
    actual_rate = int(out.strip())
    res = isclose(exp_rate, actual_rate, rel_tol=deviation)
    assert res, f'Current rate {actual_rate} exceeds expected rate {exp_rate} including deviation {deviation}'
