import asyncio
import json
import os
import time
import re
import pytest

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.lib.interfaces.interface import Interface
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.onlp.onie import Onie
from dent_os_testbed.lib.os.cpu_usage import CpuUsage
from dent_os_testbed.lib.os.disk_free import DiskFree
from dent_os_testbed.lib.os.memory_usage import MemoryUsage
from dent_os_testbed.lib.os.service import Service
from dent_os_testbed.lib.os.system import System
from dent_os_testbed.lib.tc.tc_qdisc import TcQdisc
from dent_os_testbed.utils.Utils import check_asyncio_results
from dent_os_testbed.lib.ethtool.ethtool import Ethtool

from pyvis.network import Network


async def tb_clean_config_device(d):
    config_file_list = [
        ['NTP', '/etc/ntp.conf'],
        ['QUAGGA_CONFIG', '/etc/frr/frr.conf'],
        ['DHCP', '/etc/dhcp/dhcpd.conf'],
        ['QUAGGA_DAEMONS', '/etc/frr/daemons'],
        ['HOSTNAME', '/etc/hostname'],
        ['QUAGGA_VTYSH', '/etc/frr/vtysh.conf'],
        ['HOSTS', '/etc/hosts'],
        ['RESOLV', '/etc/resolv.conf'],
        ['NETWORK_INTERFACES', '/etc/network/interfaces'],
        ['SSHD_CONF', '/etc/ssh/sshd_config'],
        ['KEEPALIVED_CONF', '/etc/keepalived/keepalived.conf'],
        ['CUMULUS_FIREWALL_RULES', '~/'],
    ]
    for src, dst in config_file_list:
        file = f'{pytest._args.config_dir}/{d.host_name}/{src}'
        if not os.path.exists(file):
            d.applog.info(f'Cannot find {file}')
            continue
        # copy only if there is a remote file.
        rc, out = await d.run_cmd(f'ls {dst}', sudo=True)
        if rc == 0:
            out = await d.scp(file, dst)
    out = await Interface.reload(input_data=[{d.host_name: [{'options': '-a'}]}])
    d.applog.info(out)
    # restart the service
    services = [
        #    "networking",
        'frr.service',
    ]
    for s in services:
        out = await Service.restart(
            input_data=[{d.host_name: [{'name': s}]}],
        )
        assert out[0][d.host_name]['rc'] == 0, f'Failed to restart the service {s} {out}'

    # await d.reboot()
    # device_up = await d.is_connected()
    # if device_up:
    #    print(“Device is up!”)


async def tb_clean_config(testbed):
    cos = []
    for d in testbed.devices:
        if d.type == DeviceType.TRAFFIC_GENERATOR:
            continue
        if not await d.is_connected():
            continue
        cos.append(tb_clean_config_device(d))
    results = await asyncio.gather(*cos, return_exceptions=True)
    check_asyncio_results(results, 'tb_clean_config')


async def tb_flap_links(dev, ports):
    """
    - flap links that match ports
    - get a list of ports on the device
    """
    out = await IpLink.show(
        input_data=[{dev.host_name: [{'cmd_options': '-j'}]}],
    )
    assert out[0][dev.host_name]['rc'] == 0, f'Failed to get Links on {dev.host_name} {out}'
    links = json.loads(out[0][dev.host_name]['result'])
    link = ''
    for l in links:
        link = l['ifname']
        if not link or l['operstate'] == 'UP':
            continue
        if ports and not l['ifname'].startswith(ports):
            continue
        if link == '':
            print('Not even single swp is UP')
            return
        out = await IpLink.set(
            input_data=[{dev.host_name: [{'device': link, 'operstate': 'down'}]}],
        )
        assert out[0][dev.host_name]['rc'] == 0, f'Failed to down the link {link} {out}'
        time.sleep(2)
        out = await IpLink.set(
            input_data=[{dev.host_name: [{'device': link, 'operstate': 'up'}]}],
        )
        assert out[0][dev.host_name]['rc'] == 0, f'Failed to down the link {link}'


async def tb_device_check_services(dev, prev_state, check, healthy_services=None):
    # not working on cumulus
    if dev.os == 'cumulus':
        return {}
    default_healthy_services = [
        'dnsmasq.service',
        'frr.service',
        'inetd.service',
        'lldpd.service',
        'lm-sensors.service',
        'netplug.service',
        'networking.service',
        'onlp-snmpd.service',
        'onlpd.service',
        'resolvconf.service',
        'rsyslog.service',
        'ssh.service',
        'systemd-udev-trigger.service',
        'systemd-udevd.service',
    ]
    if healthy_services is None:
        healthy_services = default_healthy_services
    out = await Service.show(
        input_data=[{dev.host_name: [{}]}],
        parse_output=True,
    )
    assert out[0][dev.host_name]['rc'] == 0, f'Failed to get Service on {dev.host_name} {out}'
    services = out[0][dev.host_name]['parsed_output']
    serv_dict = {}
    for s in services:
        serv_dict[s['name']] = s

    if not check:
        return serv_dict

    check = 1
    for s in healthy_services:
        if s not in serv_dict:
            dev.applog.info(f'Service is {s} not found ')
            check = 0
            continue
        if serv_dict[s]['active'] != 'active':
            dev.applog.info('{} service is down {}'.format(s, serv_dict[s]))
            check = 0
    assert check, 'Service check failed {out}'
    return serv_dict


async def tb_device_check_memory(dev, prev_state, check):
    out = await MemoryUsage.show(
        input_data=[{dev.host_name: [{}]}],
        parse_output=True,
    )
    assert out[0][dev.host_name]['rc'] == 0, f'Failed to get MemoryUsage on {dev.host_name} {out}'
    mem_dict = out[0][dev.host_name]['parsed_output']
    if not check:
        return mem_dict
    mem_to_check = [
        'mem_total',
        'mem_free',
        'mem_available',
    ]
    for k, v in mem_dict.items():
        if k not in mem_to_check:
            dev.applog.info(f'skipping to check {k}')
            continue
        old_v = (prev_state['memory'][k] * 1.0) if prev_state['memory'][k] else 1.0
        diff_p = (abs(prev_state['memory'][k] - v) / old_v) * 100.0
        if diff_p > 15.0:
            dev.applog.info(
                '{} Value not in range {} {} {}'.format(k, diff_p, v, prev_state['memory'][k])
            )
            assert 0, f'Value out of range {k} {v} by {diff_p} {out}'
    return mem_dict


async def tb_device_check_cpu(dev, prev_state, check):
    # not working on cumulus
    if dev.os == 'cumulus':
        return {}
    out = await CpuUsage.show(
        input_data=[{dev.host_name: [{'dut_discovery': True}]}],
        parse_output=True,
    )
    assert out[0][dev.host_name]['rc'] == 0, f'Failed to get CpuUsage on {dev.host_name} {out}'
    cpu_dict = out[0][dev.host_name]['parsed_output']
    if not check:
        return cpu_dict
    cpu_to_check = [
        'usr',
        'nice',
        'sys',
        'irq',
        'soft',
        'steal',
        'guest',
        'gnice',
    ]
    for cpu, ocpu in zip(cpu_dict, prev_state['cpu']):
        for k, v in cpu.items():
            if k not in cpu_to_check:
                continue
            diff_p = abs(ocpu[k] - v) * 100.0
            if diff_p > 15.0:
                dev.applog.info('{} Value not in range {} {} {}'.format(k, diff_p, v, ocpu[k]))
                # assert 0, f"Value out of range {k} {v} by {diff_p}"

    return cpu_dict


async def tb_device_check_disk(dev, prev_state, check):
    out = await DiskFree.show(
        input_data=[{dev.host_name: [{}]}],
        parse_output=True,
    )
    assert out[0][dev.host_name]['rc'] == 0, f'Failed to get DiskFree on {dev.host_name} {out}'
    dkt = out[0][dev.host_name]['parsed_output']
    disk_dict = {}
    for d in dkt:
        disk_dict[d['mounted_on']] = d

    if not check:
        return disk_dict

    for k, v in disk_dict.items():
        diff = abs(v['use_percentage'] - prev_state['disk'][k]['use_percentage'])
        if diff > 15.0:
            dev.applog.info(
                '{} Value not in range {} {} {}'.format(
                    k, diff, v['use_percentage'], prev_state['disk'][k]['use_percentage']
                )
            )
            assert 0, f'Value out of range {k} {v} by {diff} {out}'

    return disk_dict


async def tb_device_check_health(dev, prev_state, check):
    # check for memory usage
    # check for average load
    # check for critical services
    # check the cpu usage.
    # check traffic if possible

    cur_state = {}
    cur_state['services'] = await tb_device_check_services(dev, prev_state, check)
    cur_state['memory'] = await tb_device_check_memory(dev, prev_state, check)
    cur_state['cpu'] = await tb_device_check_cpu(dev, prev_state, False)
    cur_state['disk'] = await tb_device_check_disk(dev, prev_state, False)
    return cur_state


async def tb_check_and_install_pkg(device, package):
    rc, out = await device.run_cmd(f'{package} --version')
    if rc != 0:
        rc, out = await device.run_cmd(f'apt install {package} -y')
        if rc != 0:
            device.applog.info('Failed to install {package}')
            return False

    return True


async def tb_get_device_object_from_dut(testbed, dev, skip_tg=True, skip_disconnected=True):
    if dev.device_id not in testbed.devices_dict:
        testbed.applog.info('Skipping device {}'.format(dev.device_id))
        return None
    device = testbed.devices_dict[dev.device_id]
    if skip_tg and device.type == DeviceType.TRAFFIC_GENERATOR:
        return None
    if skip_disconnected and not await device.is_connected():
        device.applog.info('Device not connected skipping')
        return None
    return device


async def tb_reset_ssh_connections(devices):
    # disconnect all the connections
    for device in devices:
        if device.ssh_conn_params.pssh:
            await device.conn_mgr.get_ssh_connection().disconnect()


async def tb_get_all_devices(
    testbed,
    exclude_devices=[DeviceType.TRAFFIC_GENERATOR, DeviceType.BLACKFOOT_ROUTER],
    include_devices=None,
    skip_disconnected=True,
):
    tb_devices = testbed.devices
    devices = []
    if testbed.discovery_report:
        for dev in testbed.discovery_report.duts:
            dev = await tb_get_device_object_from_dut(
                testbed, dev, skip_tg=False, skip_disconnected=False
            )
            if not dev or dev.type in exclude_devices:
                continue
            # only look for requested devices
            if include_devices is not None and dev.type not in include_devices:
                continue
            if skip_disconnected and not await dev.is_connected():
                continue
            devices.append(dev)
    else:
        for dev in tb_devices:
            if dev.type in exclude_devices:
                continue
            # only look for requested devices
            if include_devices is not None and dev.type not in include_devices:
                continue
            if skip_disconnected and not await dev.is_connected():
                continue
            devices.append(dev)
    return devices


async def tb_reload_nw_and_flush_firewall(devices):
    async def tb_device_flush_firewall(device):
        for cmd in [
            'ifreload -a',
            'systemctl restart frr.service',
            'iptables -F',
            'tc filter delete block 1 ingress',
            'tc chain delete chain 0 block 1',
            'tc chain delete chain 1 block 1',
        ]:
            await device.run_cmd(cmd, sudo=True)

    cos = list()
    for d in devices:
        if not await d.is_connected():
            continue
        cos.append(tb_device_flush_firewall(d))
    results = await asyncio.gather(*cos, return_exceptions=True)
    check_asyncio_results(results, 'tb_reload_nw_and_flush_firewall')


async def tb_reload_firewall(devices):
    async def tb_device_reload_firewall(device):
        for cmd in [
            'ifreload -a',
            'systemctl restart frr.service',
            'iptables -F',
            'tc filter delete block 1 ingress',
        ]:
            await device.run_cmd(cmd, sudo=True)

    cos = list()
    for d in devices:
        if not await d.is_connected():
            continue
        cos.append(tb_device_reload_firewall(d))
    results = await asyncio.gather(*cos, return_exceptions=True)
    check_asyncio_results(results, 'tb_reload_firewall')


async def tb_ping_device(device, target, pkt_loss_treshold=50, dump=False):
    pkt_stats = ''
    cmd = f'ping -c 10 {target}'
    rc, out = await device.run_cmd(cmd, sudo=True)
    if dump:
        device.applog.info(f'Ran {cmd} on {device.host_name} with rc {rc} and out {out}')
    for line in out.splitlines():
        line = line.rstrip()
        if 'transmitted' in line:
            pkt_stats = line
    pkt_loss = next(
        (pkt_stat for pkt_stat in pkt_stats.split(',') if 'packet loss' in pkt_stat), None
    )
    if pkt_loss:
        pkt_loss_percent = pkt_loss.strip().split(' ')[0].split('.')[0]
        pkt_loss_percent = int(pkt_loss_percent[: pkt_loss_percent.find('%')])
    else:
        pkt_loss_percent = -1
    # 0 for success
    # 1 for failure
    return 0 if pkt_loss_percent <= pkt_loss_treshold else 1


async def tb_device_onie_install(dev):
    await Onie.select(input_data=[{dev.host_name: [{'options': 'install'}]}])
    await System.shutdown(input_data=[{dev.host_name: [{'options': '-r +1'}]}])


async def tb_reset_qdisc(dev, port, direction):
    await TcQdisc.delete(input_data=[{dev.host_name: [{'dev': port, 'direction': direction}]}])
    out = await TcQdisc.add(input_data=[{dev.host_name: [{'dev': port, 'direction': direction}]}])
    assert out[0][dev.host_name]['rc'] == 0, f'Tc qdisc add failed: {out}'


async def tb_restore_qdisc(dev, port, direction):
    await TcQdisc.delete(input_data=[{dev.host_name: [{'dev': port, 'direction': direction}]}])
    await TcQdisc.add(
        input_data=[
            {
                dev.host_name: [
                    {
                        'dev': port,
                        'handle': 'ffff',
                        'ingress_block': 1,
                        'direction': direction,
                    }
                ]
            }
        ]
    )


async def tb_check_all_devices_are_connected(devices):
    # check if all the devices can be reached??
    for dev in devices:
        if dev.type in [DeviceType.TRAFFIC_GENERATOR, DeviceType.BLACKFOOT_ROUTER]:
            continue
        if not await dev.is_connected():
            return False
    return True


def console_log_analyzer(dev, file):
    # check for back trace
    pattern = re.compile('------------[ cut here ]------------')
    for line in open(file):
        for match in re.finditer(pattern, line):
            print(line)
            return -1
    return 0


async def tb_collect_logs_from_device(device):
    files = [
        '/etc/network/interfaces',
        '/etc/frr/frr.conf',
        '/var/log/messages',
        '/var/log/syslog',
        '/var/log/autoprovision',
        '/var/log/frr/frr.log',
        '/var/tmp/dmesg',
        '/var/tmp/boot-0.log',
    ]
    file_analyzers = {
        '/var/tmp/boot-0.log': console_log_analyzer,
    }

    await device.run_cmd('dmesg > /var/tmp/dmesg', sudo=True)
    await device.run_cmd('journalctl -b 0 > /var/tmp/boot-0.log', sudo=True)
    # copy to temp so that everyone can read
    for f in files + device.files_to_collect:
        fname = f.split('/')[-1]
        rc, out = await device.run_cmd(f'ls {f}', sudo=True)
        if rc != 0:
            continue
        await device.run_cmd(f'cp {f} /tmp/{fname}', sudo=True)
        await device.run_cmd(f'chmod 755 /tmp/{fname}', sudo=True)

    for f in files + device.files_to_collect:
        l_f = f.split('/')[-1]
        r_f = os.path.join('/tmp', l_f)
        l_f = os.path.join(device.serial_logs_base_dir, l_f)
        rc, out = await device.run_cmd(f'ls {r_f}', sudo=True)
        if rc != 0:
            continue
        device.applog.info('Getting the remote file ' + r_f)
        device.applog.info(f'Copying file {r_f} to {l_f}')
        try:
            await device.scp(l_f, r_f, remote_to_local=True)
            if f in file_analyzers:
                ret = file_analyzers[f](device, l_f)
                assert ret == 0, f'Found Errors in {f} on {device.host_name}'
        except Exception as e:
            device.applog.error(str(e))


async def tb_collect_logs_from_devices(devices,
                                       exclude_devices=[DeviceType.TRAFFIC_GENERATOR],
                                       ):
    """
    collect the logs from the given devices, skip if not connected.
    """
    cos = list()
    for device in devices:
        if device.type in exclude_devices:
            continue
        if not await device.is_connected():
            continue
        cos.append(tb_collect_logs_from_device(device))
    results = await asyncio.gather(*cos, return_exceptions=True)
    check_asyncio_results(results, 'tb_collect_logs_from_devices')


def tb_generate_network_diagram(testbed, links_dict):
    net = Network(height='750px', width='100%', bgcolor='#222222', font_color='white', layout=True)
    net.barnes_hut()
    for src, links in links_dict.items():
        for slink, links in links.items():
            link, oper, ver = links
            dst, dlink = link.split(':')
            net.add_node(src, src, title=src, shape='square', group=testbed.devices_dict[src].type.value, level=testbed.devices_dict[src].type.value)
            group = testbed.devices_dict[dst].type.value if dst in testbed.devices_dict else 0
            net.add_node(dst, dst, title=dst, shape='square', group=group, level=group)
            color = 'grey'
            if oper == 'UP':
                color = 'green'
            if oper == 'DOWN':
                color = 'red'
            edge = f'{src}:{slink}<-->{dst}:{dlink}'
            # update the title
            found = False
            for e in net.edges:
                if (e['to'] == dst and e['from'] == src) or (e['from'] == dst and e['to'] == src):
                    e['title'] += '<br>' + edge + f' {oper}'
                    found = True
                    break
            if not found:
                net.add_edge(src, dst, id=edge, color=color, title=edge + f' {oper}')

    neighbor_map = net.get_adj_list()
    # add neighbor data to node hover data
    for node in net.nodes:
        node['title'] += ' Neighbors:<br>' + '<br>'.join(neighbor_map[node['id']])
        node['value'] = len(neighbor_map[node['id']])

    net.show('network.html')


async def tb_device_tcpdump(device, interface, options, count_only=False, timeout=60, dump=False):
    """
    Run tcpdump on a device and return number of captured packets or complete output
    """
    cmd = f'timeout --preserve-status {timeout} tcpdump -i {interface} {options}'
    device.applog.info(f'Starting {cmd} on {device.host_name}...')

    rc, out = await device.run_cmd(cmd, sudo=True)

    if dump:
        device.applog.info(f'Ran {cmd} on {device.host_name} with rc {rc} and out {out}')

    if count_only:
        rr = re.findall('\n(\d+) packet[s]* captured\n', out, re.MULTILINE)
        if rr:
            return int(rr[0])
        else:
            return 0

    else:
        return out


async def tb_get_qualified_ports(device, ports, speed, duplex, required_ports=2):
    """
    Get dict of dut ports with matching speed and duplex
    Args:
        device (DeviceType): Dut device
        ports (list): List of dut ports
        speed (int): Required port speed
        duplex (str): Required port duplex
        required_ports (int): Required number of ports

    Returns: Dictionary of qualified ports
    """

    # Check dut media mode name. If it supports the speed parameter
    if device.media_mode == 'mixed':
        raise ValueError('Mixed mode is not supported')
    if device.media_mode == 'copper' and speed == 10000:
        raise ValueError(f'Can not run test in device {device.host_name} with the speed: {speed}')

    # Check that there are at least minimum 2 ports with the provided speed parameter
    speed_ports = {}
    for port in ports:
        out = await Ethtool.show(input_data=[{device.host_name: [{'devname': port}]}], parse_output=True)
        assert out[0][device.host_name]['rc'] == 0, f'Ethtool show failed: {out}'
        supported_speeds = '{}baseT/{}' if 'TP' in out[0][device.host_name]['parsed_output'][
            'supported_ports'] else '{}baseSR/{}'
        if supported_speeds.format(speed, duplex.capitalize()) in out[0][device.host_name]['result']:
            speed_ports[port] = {'speed': speed,
                                 'duplex': duplex}
    err_msg = f'Need {required_ports} ports with the same speed of {speed} and duplex {duplex}'
    assert len(speed_ports) >= required_ports, err_msg
    return speed_ports
