import asyncio
import re

from random import randint, choice
from math import isclose
from ipaddress import IPv4Network

from dent_os_testbed.lib.ip.ip_route import IpRoute
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.interfaces.interface import Interface

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_clear_traffic_stats,
    tgen_utils_get_traffic_stats,
    tgen_utils_poll,
)

from dent_os_testbed.test.test_suite.functional.devlink.devlink_utils import (
    verify_cpu_traps_rate_code_avg, CPU_STAT_CODE_ACL_CODE_3)

IFUPDOWN_CONF = '/etc/network/ifupdown2/ifupdown2.conf'
IFUPDOWN_BACKUP = '/etc/network/ifupdown2/ifupdown2.bak'
INTERFACES_FILE = '/etc/network/interfaces.d/cfg-file-1'
IPV4_TEMPLATE = \
    """

    auto {name}
    iface {name} inet {inet}
    """

ECMP_TEMPLATE = \
    """

    up ip route add {net} {nexthops}
    """

BRIDGE_TEMPLATE = \
    """

    auto {bridge}
    iface {bridge} inet static
        bridge-ports {ports}
    """

VLAN_DEV_TEMPLATE = \
    """

    auto {name}
    iface {name} inet static
        vlan-id {vid}
        vlan-raw-device {bridge}
    """

FDB_TEMPLATE = \
    """

            up bridge fdb add {mac} dev {port} master static vlan {vlan}
    """

LACP_TEMPLATE = \
    """

    auto {bond}
    iface {bond} inet static
        bond-slaves {member_ports}
        bond-mode 802.3ad
    """

ARP_TEMPLATE = \
    """

    up ip neigh add {ip} lladdr {mac} dev {port}
    """


def config_qdist_temp(dev, block_num, direction='ingress'):
    """
    Setup ifupdown2 config for qdist
    Args:
        dev (str): Device name
        blockNum (str/int): Shared block num or port name
        direction (str): Direction to set ingress/egress
    Returns:
        Ifupdown2 qdist config in string representation
    """
    template = ''
    if isinstance(block_num, int):
        template += f'post-up tc qdisc add dev {dev} {direction}_block {block_num} {direction}\n'
        template += f'down tc qdisc del dev {dev} {direction}_block {block_num} {direction}\n'
    else:
        template += f'post-up tc qdisc add dev {dev} {direction}\n'
        template += f'down tc qdisc del dev {dev} {direction}\n'
    return template


def config_bridge_temp(bridge, ports, vlan_aware=False, pvid=None, vlans=None, stp=None, hwaddress=None):
    """
    Setup ifupdown2 config for bridge device
    Args:
        bridge (str): Bridge device name
        ports (list): Bridge member ports
        vlan_aware (bool): Sets bridge to vlan-aware
        pvid (int): Bridge pvid to set
        vlans (list): Bridge vlans to set
        stp(bool): Set bridge stp
        hwaddress(str): Bridge mac address
    Returns:
        Ifupdown2 bridge config in string representation
    """
    result = BRIDGE_TEMPLATE.format(bridge=bridge, ports=' '.join(ports))
    if vlan_aware:
        result += 'bridge-vlan-aware yes\n'
    if pvid:
        result += f'bridge-pvid {pvid}\n'
    if type(vlans) is list:
        result += f'bridge-vids {" ".join(map(str, vlans))}\n'
    if stp:
        result += 'bridge-stp yes\n'
    if hwaddress:
        result += f'hwaddress {hwaddress}\n'
    return result


def config_ipv4_temp(name, inet, ipaddr=None):
    """
    Setup ifupdown2 config for port device
    Args:
        name (str): Port name
        inet (str): Device inet type
        ipaddr (str): Ipv4 address to configure
    Returns:
        Ifupdown2 port config in string representation
    """
    res = IPV4_TEMPLATE.format(name=name, inet=inet)
    if ipaddr:
        res += f'address {ipaddr}\n'
    return res


def config_acl_rule_temp(tc_rule):
    """
    Setup ifupdown2 config for acl rule
    Args:
        tc_rule (dict): Dict with tcutil_generate_rule_with_random_selectors output
    Returns:
        Ifupdown2 acl rule config in string representation
    """
    cmd = 'post-up tc filter add '
    if tc_rule.get('dev'):
        if isinstance(tc_rule['dev'], str):
            cmd += f'dev {tc_rule["dev"]} '
        elif isinstance(tc_rule['dev'], int):
            cmd += f'block {tc_rule["dev"]} '
    if tc_rule.get('direction'):
        cmd += f'{tc_rule["direction"]} '
    if tc_rule.get('pref'):
        cmd += f'pref {tc_rule["pref"]} '
    if tc_rule.get('protocol'):
        cmd += f'protocol {tc_rule["protocol"]} '
    if 'filtertype' in tc_rule:
        if type(tc_rule['filtertype']) is dict:
            cmd += 'flower '
            for field, value in tc_rule['filtertype'].items():
                cmd += '{} {} '.format(field, value)
    if 'action' in tc_rule.keys():
        if 'trap' in tc_rule['action']:
            cmd += 'action trap '
        if 'police' in tc_rule['action']:
            cmd += 'action police '
            for field, value in tc_rule['action']['police'].items():
                cmd += '{} {} '.format(field, value)
        if 'pass' in tc_rule['action']:
            cmd += 'action pass '
        if 'drop' in tc_rule['action']:
            cmd += 'action drop '
    return cmd + '\n'


def random_mac():
    return ':'.join(['02'] + [f'{randint(0, 255):02x}' for _ in range(5)])


def config_ecmp_temp(route, nexthops):
    """
    Setup ifupdown2 config for ecmp route
    Args:
        route (str): Ipv4 route to set as ecmp
        nexthops (list): List of nexthops
    Returns:
        Ifupdown2 ecmp config in string representation
    """
    nexthops_str = ' '.join('nexthop via ' + str(neigh) for neigh in nexthops)
    return ECMP_TEMPLATE.format(net=route, nexthops=nexthops_str)


def gen_random_ip_net(multicast=False):
    """
    Generate random ip network with prefix /8-24
    Args:
        multicast (bool): If True generates multicast route
    Returns:
        IPv4Network object and maximum available host's in network
    """
    first_octet = randint(224, 239) if multicast else randint(10, 200)
    ip = f'{first_octet}.{randint(1, 250)}.{randint(1, 250)}.{randint(1, 250)}/{randint(8, 24)}'
    net = IPv4Network(ip, strict=False)
    return IPv4Network(net.with_prefixlen, strict=True), randint(10, 2**(32 - net.prefixlen))


async def reboot_and_wait(dent_dev):
    """
    Reboot DUT and wait for it to come back
    Args:
        dent_dev (str): Dut name
    """
    await dent_dev.reboot()
    await asyncio.sleep(30)

    async def _verify(dut):
        is_up = await dut.is_connected()
        assert is_up, 'DUT is not up'

    await tgen_utils_poll(dent_dev, _verify, dut=dent_dev,
                          interval=15, timeout=300)

    # https://github.com/dentproject/dentOS/issues/152#issuecomment-973264204
    rc, _ = await dent_dev.run_cmd('/lib/platform-config/current/onl/bin/onlpdump', sudo=True)
    assert not rc, f'Failed to run onlpdump {rc}'


async def write_reload_check_ifupdown_config(dent_dev, config_to_wtite, default_interfaces_configfile):
    """
    Write, Reload and check ifupdown2 config
    Args:
        dent_dev (obj): Dut device object
        config_to_wtite (str): String of ifupdown2 config to write
        default_interfaces_configfile (str): File patch where config will be written to
    """

    # Write desirable ifupdwon2 config to a default_interfaces_configfile
    rc, _ = await dent_dev.run_cmd(f"echo -e '{config_to_wtite}' >> {default_interfaces_configfile}")
    assert not rc, f'Failed to write ifupdown2 config to a {default_interfaces_configfile}'

    # Verify (ifquery) no errors in configuration file
    out = await Interface.query(input_data=[{dent_dev.host_name: [
        {'options': f'-a -i {default_interfaces_configfile}'
         }]}])
    assert 'error' not in out[0][dent_dev.host_name]['result'], 'Error spotted in output of ifquery'
    assert not out[0][dent_dev.host_name]['rc'], 'Ifquery failed'

    # Apply (ifreload) ifupdown configuration
    out = await Interface.reload(input_data=[{dent_dev.host_name: [{'options': '-a -v'}]}])
    assert not out[0][dent_dev.host_name]['rc'], 'Failed to reload config'

    # Check (ifquery --check) running vs actual configuration
    out = await Interface.query(input_data=[{dent_dev.host_name: [
        {'options': f'-a -c -i {default_interfaces_configfile}'
         }]}])
    assert not out[0][dent_dev.host_name]['rc'], 'Ifquery failed'


async def verify_ip_address_routes(dev_name, address_map, ecmp_route):
    """
    Verify ip addresses asigned, routes added and ecmp route offloaded
    Args:
        dev_name (str): Dut name
        address_map (list): Address map list
        ecmp_route (str): Ipv4 route addresses used as ECMP
    """
    out = await IpRoute.show(input_data=[{dev_name: [{'cmd_options': '-j -4'}]}], parse_output=True)
    assert not out[0][dev_name]['rc'], 'Failed to get routes'
    routes = out[0][dev_name]['parsed_output']

    out = await IpAddress.show(input_data=[{dev_name: [{'cmd_options': '-j -4'}]}], parse_output=True)
    assert not out[0][dev_name]['rc'], 'Failed to get IPv4 addresses'
    ip_addrs = out[0][dev_name]['parsed_output']

    for port, _, ip, _, plen in address_map:
        for ip_addr in ip_addrs:
            if port == ip_addr['ifname']:
                assert f'{ip}/{plen}' == f'{ip_addr["addr_info"][0]["local"]}/{ip_addr["addr_info"][0]["prefixlen"]}', \
                    f'{ip}/{plen} != {ip_addr["addr_info"][0]["local"]}/{ip_addr["addr_info"][0]["prefixlen"]}'
        for ro in routes:
            try:
                if ro['dev'] == port:
                    assert str(IPv4Network(f'{ip}/{plen}', strict=False)) == ro['dst'], \
                        f'Route not found {str(IPv4Network(f"{ip}/{plen}", strict=False))}'
            except KeyError:
                pass
            if ro['dst'] == str(ecmp_route):
                assert 'rt_offload' in ro['flags'], f'Ecmp route {ecmp_route} is not offloaded'


async def start_and_stop_stream(tgen_dev, traffic_duration, sleep_time=15):
    """
    Start traffic for a traffic duration and stop it
    Args:
        tgen_dev (obj): Traffic Genearotor object
        traffic_duration (int): Time duration for sending traffic
        sleep_time (int): Time to sleep after traffic sent (for stats stabilization)
    """
    await tgen_utils_clear_traffic_stats(tgen_dev)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)
    await asyncio.sleep(sleep_time)


def format_mac(port, vlan, offset=0):
    """
    Format Mac address based on port name and vlan
    Args:
        port (str): Dut port name
        vlan (int): Vlan id
        offset (int): Mac address offset
    Returns:
        Formated Mac address
    """
    reg_exp = re.compile(r'(\d+)$')
    port, vlan = (i if isinstance(i, int) else int(reg_exp.search(i).groups()[0]) for i in [port, vlan])
    mac_int = port * 0x100000000 + vlan * 0x10000 + offset
    mac_str = '{:012X}'.format(mac_int)
    return ':'.join(x + y for x, y in zip(mac_str[::2], mac_str[1::2]))


def inc_mac(mac, offset):
    """
    Increment Mac address
    Args:
        mac (str): Mac address
        offset (int): Mac address offset
    Returns:
        Incremented Mac address
    """
    mac_hex = '{:012X}'.format(int(mac.replace(':', ''), 16) + offset)
    return ':'.join(x+y for x, y in zip(mac_hex[::2], mac_hex[1::2]))


async def check_vlan_members(dev_name, dut_ports, vlans, pvid=1):
    """
    Check bridge members vlans
    Args:
        dev_name (str): Dut name
        dut_ports (list): Dut ports
        vlans (list): List of vlans to check
        pvid (int): Expected pvid to check
    """
    out = await BridgeVlan.show(input_data=[{dev_name: [{'cmd_options': '-j'}]}], parse_output=True)
    assert not out[0][dev_name]['rc'], f'Failed show bridge vlans.\n{out}'
    parsed = out[0][dev_name]['parsed_output']

    for p_vlans in parsed:
        if p_vlans['ifname'] in dut_ports:
            for vlan in p_vlans['vlans']:
                if vlan['vlan'] == pvid:
                    assert vlan['flags'] == ['PVID', 'Egress Untagged'], f'Unexpected vlan flags {vlan["flags"]}'
                assert vlan['vlan'] in vlans + [pvid], f'Expected vlan {vlan["vlan"]} not in {vlans + [pvid]}'


async def check_member_devices(dev_name, device_members, status='UP'):
    """
    Check device and members status
    Args:
        dev_name (str): Dut name
        device_members (dict): Dict with mapping of device and its members to check
        status (str): Expected status to check
    """
    await asyncio.sleep(15)
    for dev, members in device_members.items():
        out = await IpLink.show(input_data=[{dev_name: [{'device': dev, 'cmd_options': '-j'}]}], parse_output=True)
        assert not out[0][dev_name]['rc'], 'Failed to get port info'
        parsed = out[0][dev_name]['parsed_output']

        assert parsed[0]['ifname'] == dev and parsed[0]['operstate'] == status, f'Unexpected status for device {dev}'

        if members:
            out = await IpLink.show(input_data=[{dev_name: [{'device': dev, 'master': '', 'cmd_options': '-j'}]}], parse_output=True)
            assert not out[0][dev_name]['rc'], 'Failed to get member ports info'
            parsed = out[0][dev_name]['parsed_output']
            for link in parsed:
                assert link['ifname'] in members and link['operstate'] == status, \
                    f'Unexpected member port {link["ifname"]} or state {link["operstate"]}'


async def delete_rule(dent_dev, rule, config_file):
    """
    Delete Acl rule from ifupdown2 config
    Args:
        dent_dev (obj): Dut object
        rule (str): Acl rule to remove
        config_file (str): Path to ifupdown2 config
    """
    cmd = f"sed -i -e 's/.*{rule[:-1]}//g' {config_file}"
    rc, _ = await dent_dev.run_cmd(cmd, sudo=True)
    assert not rc, f'Failed to delete rule {rule} from {config_file}'


async def add_rule(dent_dev, before_rule, added_rule, config_file):
    """
    Add Acl rule to ifupdown2 config
    Args:
        dent_dev (obj): Dut object
        before_rule (str): Acl rule before which to insert added_rule
        added_rule (str): Acl rule to add
        config_file (str): Path to ifupdown2 config
    """
    cmd = f"sed -i '/^{before_rule[:-1]}/i {added_rule}' {config_file}"
    rc, _ = await dent_dev.run_cmd(cmd, sudo=True)
    assert not rc, f'Failed to add rule in {config_file}'


def update_rules(first_rule, second_rule, first_action, second_action, pref, rate_bps):
    """
    Update Acl rules dictionary in case of trap action
    Args:
        first_rule (dict): First Acl rule dict
        second_rule (dict): Second Acl rule dict
        first_action (str): First Acl rule action
        second_action (str): Second Acl rule action
        pref (int): Priority of first Acl rule
        rate_bps (int): Rate in bps to set in case of policer action
    """
    second_rule['action'] = second_action
    second_rule['pref'] = pref + 10000

    for rule, action in zip([first_rule, second_rule], [first_action, second_action]):
        if action == 'trap':
            policeTrap = choice([True, False])
            if policeTrap:
                rule['action'] = {'trap': '',
                                  'police': {'rate': f'{rate_bps}bps', 'burst': f'{rate_bps + 1000}', 'conform-exceed': '', 'drop': ''}}


async def verify_traffic_by_highest_prio(tgen_dev, dent_dev, rule, tx_port, rx_port, exp_rate_pps,
                                         deviation=0.1, cpu_code=CPU_STAT_CODE_ACL_CODE_3):
    """
    Verify traffic handled according to highest Acl rule
    Args:
        tgen_dev (obj): Traffic generator object
        dent_dev (obj): Dut device object
        rule (str): Rule action
        tx_port (str): Tx Port
        rx_port (str): Rx Port
        exp_rate_pps (int): Expected rate pps in case of trap policer rule
        deviation (float): Deviation percent
        cpu_stat_code (int): Cpu code to read counters from
    """
    stats = await tgen_utils_get_traffic_stats(tgen_dev, stats_type='Port Statistics')
    if rule == 'drop':
        for row in stats.Rows:
            if row['Port Name'] == rx_port:
                # There may be some pkt traversing on port, add a deviation of pkt's amount
                assert int(row['Valid Frames Rx. Rate']) <= 50, \
                    f'Current rate {row["Valid Frames Rx. Rate"]} exceeds expected rate 0'
    elif rule == 'pass':
        tx_rate = [row['Frames Tx. Rate'] for row in stats.Rows if row['Port Name'] == tx_port]
        for row in stats.Rows:
            if row['Port Name'] == rx_port:
                res = isclose(int(tx_rate[0]), int(row['Valid Frames Rx. Rate']), rel_tol=deviation)
                assert res, f'Current rate {row["Valid Frames Rx. Rate"]} exceeds expected rate {tx_rate[0]}'
    else:
        try:
            await verify_cpu_traps_rate_code_avg(dent_dev, cpu_code, exp_rate_pps)
        except AssertionError:
            await asyncio.sleep(10)  # Policer rate may be unstable, sleep and try again
            await verify_cpu_traps_rate_code_avg(dent_dev, cpu_code, exp_rate_pps)


async def verify_ifupdown_config(dent_dev, config_file, timeout=60):
    async def _verify(dent, config_file):
        out = await Interface.query(input_data=[{dent: [
            {'options': f'-a -c -i {config_file}'}
        ]}])
        assert not out[0][dent]['rc'], 'Ifquery failed'

    await tgen_utils_poll(dent_dev, _verify, dent=dent_dev.host_name, config_file=config_file,
                          interval=15, timeout=timeout)
