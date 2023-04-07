from math import isclose as is_close
import random
import json

from dent_os_testbed.lib.iptables.ip_tables import IpTables
from dent_os_testbed.lib.tc.tc_filter import TcFilter
from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_swp_info,
    tgen_utils_get_loss,
)


async def tcutil_iptable_to_tc(dent_dev, swp_tgen_ports, iptable_rules, extra_args=''):
    # - run the tc persistency  tools
    #  - iptables-save -t filter  > /tmp/iptables.rules
    #  - iptables-unroll /tmp/iptables.rules /tmp/iptables-unrolled.rules FORWARD
    #  - iptables-scoreboard /tmp/iptables-unrolled.rules /tmp/iptables-scoreboarded.rules FORWARD swp+
    #  - tc-flower-load --scoreboard  --shared-block /tmp/iptables-scoreboarded.rules FORWARD swp+
    #  - delete the rules from iptables
    # check if there is a path else check if there is petunia
    PREFIX=''
    rc, out = await dent_dev.run_cmd('ls /sputnik/env/IhmDentTcFlower/', sudo=True)
    if rc == 0:
        PREFIX = '/sputnik/env/IhmDentTcFlower/bin/execute_in_env /sputnik/env/IhmDentTcFlower/bin/'
    cmds = [
        f'iptables-save -t filter  > /tmp/iptables.rules',
        f'{PREFIX}iptables-unroll --multi-interface --extended /tmp/iptables.rules /tmp/iptables-unrolled.rules FORWARD',
        f'{PREFIX}iptables-scoreboard /tmp/iptables-unrolled.rules /tmp/iptables-scoreboarded.rules FORWARD swp+',
        f'{PREFIX}tc-flower-load -v {extra_args} --offload --port-unroll 5 --scoreboard  --shared-block  --hack-vlan-arp --log-ignore --continue-suppress /tmp/iptables-scoreboarded.rules FORWARD swp+',
    ]
    dent_dev.files_to_collect.append('/tmp/iptables.rules')
    dent_dev.files_to_collect.append('/tmp/iptables-unrolled.rules')
    dent_dev.files_to_collect.append('/tmp/iptables-scoreboarded.rules')
    for cmd in cmds:
        dent_dev.applog.info(f'Running command {cmd}')
        try:
            rc, out = await dent_dev.run_cmd(cmd, sudo=True)
            assert rc == 0, f'Failed to run {cmd} output {out}'
            dent_dev.applog.info(out)
        except Exception as e:
            dent_dev.applog.info(str(e))
            raise e

    ## delete the IP rules.
    dent_dev.applog.info('Deleting iptable rule for FORWARD')
    out = await IpTables.flush(
        input_data=[
            {
                dent_dev.host_name: [
                    {
                        'table': 'filter',
                        'chain': 'FORWARD',
                    }
                ]
            }
        ]
    )
    dent_dev.applog.info(out)


async def tcutil_get_tc_rule_stats(dent_dev, swp_tgen_ports, swp_tc_rules):
    dent = dent_dev.host_name
    chain = '0'
    for swp in swp_tgen_ports:
        try:
            out = await TcFilter.show(
                input_data=[
                    {
                        dent: [
                            {
                                'options': '-j -stats',
                                'dev': swp,
                                'direction': 'ingress',
                            }
                        ]
                    }
                ]
            )
            rc, out = out[0][dent]['rc'], out[0][dent]['result']
            assert rc == 0, f'Failed to show tc filter {out}'
            # dent_dev.applog.info(out)
            tc_rules = json.loads(out)
            swp_tc_rules[swp] = []
            count = 1
            for rule in tc_rules:
                if 'options' not in rule:
                    continue
                if 'chain' in rule:
                    chain = rule['chain']
                line = '{}. {} Pref {} Chain {} protocol {} Key [ '.format(
                    count, swp, rule['pref'], chain, rule['protocol']
                )
                line += 'indev {} '.format(rule['options'].get('indev', 'swp+'))
                for k, v in rule['options']['keys'].items():
                    line += f'{k}=={v},'
                line += '] Action ['
                for action in rule['options']['actions']:
                    line += '{} Pkt {} Bytes {} HW Pkt {} Bytes {}'.format(
                        action['control_action']['type'],
                        action['stats'].get('packets', 0),
                        action['stats'].get('bytes', 0),
                        action['stats'].get('hw_packets', 0),
                        action['stats'].get('hw_bytes', 0),
                    )
                line += ']'
                dent_dev.applog.info(line)
                swp_tc_rules[swp].append(rule)
                count += 1
        except Exception as e:
            dent_dev.applog.info(str(e))


async def tcutil_cleanup_tc_rules(dent_dev, swp_tgen_ports, swp_tc_rules):
    dent = dent_dev.host_name
    out = await TcFilter.delete(
        input_data=[
            {
                dent: [
                    {
                        'block': 1,
                    }
                ]
            }
        ]
    )


def tcutil_tc_rules_to_tgen_streams(swp_tc_rules, streams=None, start=0, cnt=None,
                                    frame_rate_pps=10, frame_size=256):
    """
    - swp_tc_rules:   dict
    - streams:        streams dict that will be modified
    - start:          used to specify the first rule index, from which the streams will be created
    - cnt:            used to specify the number of streams to be created
    - frame_rate_pps: frame rate for each stream
    - frame_size:     packet size for each stream

    Expects swp_tc_rules to be a dict:
    {
        swp_port: { *output from TcFilter.show()* },
        ...
    }

    Returns a dict with streams that match the TC rules:
    {
        stream_1: { *stream that matches rule #1* },
        stream_2: { *stream that matches rule #2* },
        ...
    }
    """
    if streams is None:
        streams = {}
    for swp, rules in swp_tc_rules.items():
        count = 0
        end = start + cnt if cnt else len(rules)
        for rule in rules[start:end]:
            if 'options' not in rule:
                continue
            st = {
                'ep_source': [swp],
                'type': 'ethernet',
                'srcIp': f'20.0.{swp[3:]}.2',
                'dstIp': f'20.0.{swp[3:]}.3',
                'rate': frame_rate_pps,
                'frameSize': frame_size,
            }
            st['type'] = 'ethernetVlan' if rule['protocol'] == '802.1Q' else 'ethernet'
            name = swp
            # this rule wont hit anyway
            if 'indev' in rule['options'] and swp != rule['options']['indev']:
                continue
            for k, v in rule['options']['keys'].items():
                if not isinstance(v, str) and not isinstance(v, int):
                    continue
                name += '_' + k + '_' + str(v)
                if k == 'eth_type' and v == 'ipv4':
                    st['protocol'] = 'ip'
                if k == 'ip_proto':
                    st['ipproto'] = v
                if k == 'dst_ip':
                    st['dstIp'] = v.split('/')[0]
                    if '/' in v:
                        st['dstIp'] = st['dstIp'][:-1] + '1'
                if k == 'src_ip':
                    st['srcIp'] = v.split('/')[0]
                    if '/' in v:
                        st['srcIp'] = st['srcIp'][:-1] + '1'
                if k == 'dst_port':
                    st['dstPort'] = str(v)
                if k == 'src_port':
                    st['srcPort'] = str(v)
                if k == 'vlan_ethtype':
                    st['ethType'] = str(v)
                if k == 'vlan_id':
                    st['vlanID'] = str(v)
                if k == 'dst_mac':
                    st['type'] = 'raw'
                    st['dstMac'] = str(v)
                if k == 'src_mac':
                    st['type'] = 'raw'
                    st['srcMac'] = str(v)
            if name not in streams:
                count += 1
                if count > 128:
                    break
            streams[name] = st
    return streams


async def tcutil_get_iptables_rule_stats(dent_dev, swp_iptables_rules):
    dent = dent_dev.host_name
    out = await IpTables.list(
        input_data=[
            {dent: [{'table': 'filter', 'chain': 'INPUT', 'cmd_options': '-n -v --line-numbers'}]}
        ],
        parse_output=True,
    )
    iptables_rules = out[0][dent]['parsed_output']
    for chain, rules in iptables_rules.items():
        for r in rules:
            line = '{}. Key ['.format(r['num'])
            for k, v in r['keys'].items():
                line += f'{k}=={v},'
                pass
            line += '] target {} '.format(r['target'])
            line += 'Pkt {} Bytes {} '.format(r['packets'], r['bytes'])
            dent_dev.applog.info(line)
        swp_iptables_rules[chain] = rules


async def tcutil_iptables_rules_to_tgen_streams(
    dent_dev, swp_iptables_rules, chain, swp_tgen_ports, streams
):

    """
    - Get the Vlans on the interface
    - find a vlan that has a mac address
    """
    for rule in swp_iptables_rules[chain]:
        inp = rule['keys']['in'].split(',')
        for swp in swp_tgen_ports:
            if swp not in inp and inp[0] != 'swp+' and inp[0] != '*':
                continue
            swp_info = {}
            await tgen_utils_get_swp_info(dent_dev, swp, swp_info)
            swp_mac = swp_info['mac']
            dev_gw = swp_info['ip']
            dev_plen = swp_info['plen']
            st = {
                'ep_source': [swp],
                'type': 'raw',
                'srcMac': '00:10:00:00:00:01',
                'dstMac': swp_mac,
                'srcIp': '.'.join(dev_gw[:-1] + [swp[3:]]),
                'dstIp': '.'.join(dev_gw),
                'rate': '10',
                'frameSize': '256',
            }
            name = swp + '_'
            for k, v in rule['keys'].items():
                if k not in ['ipproto', 'srcIp', 'dstIp', 'dstPort', 'srcPort']:
                    continue
                if v in ['0.0.0.0/0']:
                    continue
                name += k + '_' + str(v) + '_'
                if ',' in v:
                    v = v.split(',')[0]
                if '/' in v:
                    v = v.split('/')[0]
                    v = v[:-1] + '1'
                if v == 'icmp':
                    v = 'icmpv1'
                st[k] = v
            if name in streams:
                name += '1'
            streams[name] = st
            dent_dev.applog.info(f'Adding Stream {name} with keys {st.keys()}')


def tcutil_generate_rule_with_random_selectors(
    port, pref=None, want_mac=False, want_vlan=False, want_ip=False, want_tcp=False,
    want_port=False, want_icmp=False, action=None, direction='ingress',
    skip_sw=False, skip_hw=False, want_proto=True,
):
    """
    Creates a single tc rule with specified selectors:
    - port:       swp port (mandatory)
    - pref:       rule priority
    - want_mac:   generate src_mac and dst_mac selectors
    - want_vlan:  generate vlan_id and vlan_ethtype selectors
    - want_ip:    generate src_ip and dst_ip selectors
    - want_port:  generate src_port and dst_port selectors (relevant for want_ip=True)
    - want_tcp:   if True ip_proto will be 'tcp', else 'udp' (relevant for want_port=True)
    - want_icmp:  ip_proto will be 'icmp', generate icmp code and type selectors (relevant for want_vlan=False)
    - action:     [list | str], desired rule action
    - direction:  [ingress | egress]
    - skip_sw:    add skip_sw flag
    - skip_hw:    add skip_hw flag
    - want_proto: generate protocol selector
    """
    def random_mac():
        return ':'.join(['02'] + [f'{random.randint(0, 255):02x}' for _ in range(5)])

    def random_ip():
        return '.'.join(map(str, [random.randint(11, 126), random.randint(0, 255),
                                  random.randint(0, 255), random.randint(1, 250)]))

    def random_icmp_type():
        return random.choice((0, 3, 4, 5, 8, 11, 12, 13, 14, 15, 16, 17, 18))
    ip_protocols = ('ip', 'ipv4', '0x0800')
    vlan_protocols = ('0x8100', '0x88a8', '802.1q')

    if want_vlan:
        protocols = vlan_protocols
    elif want_ip:
        protocols = ip_protocols
    else:
        protocols = (f'0x9{random.randint(1, 3)}00',)

    if action is None:
        action_list = ('pass', 'drop', 'trap')
    elif type(action) is str:
        action_list = (action, )
    else:
        action_list = action

    filter_t = {}
    rule = {
        'dev': port,
        'action': random.choice(action_list),
        'direction': direction,
        'protocol': random.choice(protocols),
        'filtertype': filter_t,
    }
    if skip_sw:
        filter_t['skip_sw'] = ''
    if skip_hw:
        filter_t['skip_hw'] = ''
    if pref is not None:
        rule['pref'] = pref
    if want_mac:
        filter_t['src_mac'] = random_mac()
        filter_t['dst_mac'] = random_mac()
    if not want_proto:
        del rule['protocol']
        return rule
    if want_vlan:
        filter_t['vlan_id'] = random.randint(1, 4095)
        if want_ip:
            filter_t['vlan_ethtype'] = random.choice(ip_protocols)
        else:
            filter_t['vlan_ethtype'] = f'0x9{random.randint(1, 3)}00'
    if want_ip:
        filter_t['src_ip'] = random_ip()
        filter_t['dst_ip'] = random_ip()
        if want_port:
            filter_t['ip_proto'] = 'tcp' if want_tcp else 'udp'
            filter_t['src_port'] = random.randint(1, 65535)
            filter_t['dst_port'] = random.randint(1, 65535)
        elif want_icmp and not want_vlan:
            filter_t['ip_proto'] = 'icmp'
            filter_t['code'] = random.randint(0, 255)
            filter_t['type'] = random_icmp_type()
    return rule


async def tcutil_get_tc_stats_pref_map(dent, port, is_block=False):
    """
    Returns tc stats of all port (or block) rules, grouped by pref:
    {
        pref: {
            action: pass | trap | drop,
            bytes: X,
            packets: Y,
            ...
        },
        ...
    }
    """
    type_ = 'block' if is_block else 'dev'
    out = await TcFilter.show(input_data=[{dent: [
        {type_: port, 'direction': 'ingress', 'options': '-j -s'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get tc stats'
    return {int(r['pref']): {'action': r['options']['actions'][0]['control_action']['type'],
                             **r['options']['actions'][0]['stats']}
            for r in out[0][dent]['parsed_output'] if 'options' in r}


async def tcutil_verify_tc_stats(dev, tx_packets, tc_stats, rule_action=None,
                                 stats_type='hw', tolerance=0.05):
    """
    Checks that drops counter and hw/sw/packets counters of a tc rule is correct.
    - dev:         used for logging
    - tx_packets:  packets, that matched the rule
    - tc_stats:    dict of packets, hw_packets, drops, bytes
    - rule_action: pass | drop | trap
    - stats_type:  str or list [hw | sw]
    - tolerance:   max acceptable deviation
    """
    action = tc_stats.get('action', 'pass')
    if rule_action is not None:
        action = rule_action
    expected_stats = {
        'drops': tx_packets if action == 'drop' else 0,
        'packets': tx_packets,
        'hw_packets': tx_packets,
    }
    if 'sw' in stats_type and 'hw' in stats_type:
        if action == 'drop':
            expected_stats['sw_packets'] = 0
        else:
            expected_stats['packets'] *= 2
            expected_stats['sw_packets'] = tx_packets
    if 'hw' not in stats_type or tx_packets == 0:
        del expected_stats['hw_packets']

    for field, expected in expected_stats.items():
        dev.applog.info(f'Rule {action = }, Tx Frames = {tx_packets}, ' +
                        f'{field} = {tc_stats[field]}, {expected = }, max {tolerance = }')
        assert is_close(int(tc_stats[field]), expected, rel_tol=tolerance), \
            f'Expected {field} to be {expected}, but got {tc_stats[field]} (max {tolerance = })'


async def tcutil_verify_tgen_stats(dev, row, rule_action='pass',
                                   actual_pps=10_000, tolerance=0.05):
    """
    Checks that Ixia stats for a specific traffic item is correct based on
    the matched rule.
    - dev:         used for logging
    - row:         Ixia stats row
    - rule_action: pass | drop | trap
    - actual_pps:  used for calculating traffic duration
    - tolerance:   max acceptable deviation
    """
    max_acl_pps = 4000  # acl traps have a max rate of 4000 pps
    loss = tgen_utils_get_loss(row)
    tx_packets = int(row['Tx Frames'])
    expected_loss = 0
    if rule_action == 'drop':
        expected_loss = 100
    if rule_action == 'trap':
        traffic_duration = tx_packets / actual_pps
        expected_loss = (1 - max_acl_pps / (tx_packets / traffic_duration)) * 100
        expected_loss = max(min(expected_loss, 100), 0)  # limit values to 0..100

    dev.applog.info(f"Traffic item: {row['Traffic Item']}\n" +
                    f"Tx Frames: {tx_packets}, Rx Frames: {row['Rx Frames']}, " +
                    f'{loss = }, {expected_loss = :.3f} (max {tolerance = })')
    assert is_close(loss, expected_loss, rel_tol=tolerance), \
        f'Expected loss: {expected_loss:.3f}%, actual: {loss}%'
