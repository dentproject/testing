import asyncio
import json
import os
import time

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
from dent_os_testbed.utils.Utils import check_asyncio_results


async def tb_clean_config_device(d):
    config_file_list = [
        ["_NTP", "/etc/ntp.conf"],
        ["_QUAGGA_CONFIG", "/etc/frr/frr.conf"],
        ["_DHCP", "/etc/dhcp/dhcpd.conf"],
        ["_QUAGGA_DAEMONS", "/etc/frr/daemons"],
        ["_HOSTNAME", "/etc/hostname"],
        ["_QUAGGA_VTYSH", "/etc/frr/vtysh.conf"],
        ["_HOSTS", "/etc/hosts"],
        ["_RESOLV", "/etc/resolv.conf"],
        ["_NETWORK_INTERFACES", "/etc/network/interfaces"],
        ["_SSHD_CONF", "/etc/ssh/sshd_config"],
        ["_KEEPALIVED_CONF", "/etc/keepalived/keepalived.conf"],
        ["_CUMULUS_FIREWALL_RULES", "~/"],
    ]
    for src, dst in config_file_list:
        file = f"{pytest._args.config_dir}/{d.host_name}/{d.host_name}{src}"
        if not os.path.exists(file):
            d.applog.info(f"Cannot find {file}")
            continue
        out = await d.scp(file, dst)
    out = await Interface.reload(input_data=[{d.host_name: [{"options": "-a"}]}])
    d.applog.info(out)
    # restart the service
    services = [
        #    "networking",
        "frr.service",
    ]
    for s in services:
        out = await Service.restart(
            input_data=[{d.host_name: [{"name": s}]}],
        )
        assert out[0][d.host_name]["rc"] == 0, f"Failed to restart the service {s} {out}"

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
    check_asyncio_results(results, "tb_clean_config")


async def tb_flap_links(dev, ports):
    """
    - flap links that match ports
    - get a list of ports on the device
    """
    out = await IpLink.show(
        input_data=[{dev.host_name: [{"cmd_options": "-j"}]}],
    )
    assert out[0][dev.host_name]["rc"] == 0, f"Failed to get Links on {dev.host_name} {out}"
    links = json.loads(out[0][dev.host_name]["result"])
    link = ""
    for l in links:
        link = l["ifname"]
        if not link or l["operstate"] == "UP":
            continue
        if ports and not l["ifname"].startswith(ports):
            continue
        if link == "":
            print("Not even single swp is UP")
            return
        out = await IpLink.set(
            input_data=[{dev.host_name: [{"device": link, "operstate": "down"}]}],
        )
        assert out[0][dev.host_name]["rc"] == 0, f"Failed to down the link {link} {out}"
        time.sleep(2)
        out = await IpLink.set(
            input_data=[{dev.host_name: [{"device": link, "operstate": "up"}]}],
        )
        assert out[0][dev.host_name]["rc"] == 0, f"Failed to down the link {link}"


async def tb_device_check_services(dev, prev_state, check, healthy_services=None):
    default_healthy_services = [
        "dnsmasq.service",
        "frr.service",
        "inetd.service",
        "lldpd.service",
        "lm-sensors.service",
        "netplug.service",
        "networking.service",
        "onlp-snmpd.service",
        "onlpd.service",
        "resolvconf.service",
        "rsyslog.service",
        "ssh.service",
        "systemd-udev-trigger.service",
        "systemd-udevd.service",
        "IhmDentTcFlower.service",
    ]
    if healthy_services is None:
        healthy_services = default_healthy_services
    out = await Service.show(
        input_data=[{dev.host_name: [{}]}],
        parse_output=True,
    )
    assert out[0][dev.host_name]["rc"] == 0, f"Failed to get Service on {dev.host_name} {out}"
    services = out[0][dev.host_name]["parsed_output"]
    serv_dict = {}
    for s in services:
        serv_dict[s["name"]] = s

    if not check:
        return serv_dict

    check = 1
    for s in healthy_services:
        if s not in serv_dict:
            dev.applog.info(f"Service is {s} not found ")
            check = 0
        if serv_dict[s]["active"] != "active":
            dev.applog.info("{} service is down {}".format(s, serv_dict[s]))
            check = 0
    assert check, "Service check failed {out}"
    return serv_dict


async def tb_device_check_memory(dev, prev_state, check):
    out = await MemoryUsage.show(
        input_data=[{dev.host_name: [{}]}],
        parse_output=True,
    )
    assert out[0][dev.host_name]["rc"] == 0, f"Failed to get MemoryUsage on {dev.host_name} {out}"
    mem_dict = out[0][dev.host_name]["parsed_output"]
    if not check:
        return mem_dict
    mem_to_check = [
        "mem_total",
        "mem_free",
        "mem_available",
    ]
    for k, v in mem_dict.items():
        if k not in mem_to_check:
            dev.applog.info(f"skipping to check {k}")
            continue
        old_v = (prev_state["memory"][k] * 1.0) if prev_state["memory"][k] else 1.0
        diff_p = (abs(prev_state["memory"][k] - v) / old_v) * 100.0
        if diff_p > 15.0:
            dev.applog.info(
                "{} Value not in range {} {} {}".format(k, diff_p, v, prev_state["memory"][k])
            )
            assert 0, f"Value out of range {k} {v} by {diff_p} {out}"
    return mem_dict


async def tb_device_check_cpu(dev, prev_state, check):
    out = await CpuUsage.show(
        input_data=[{dev.host_name: [{"dut_discovery": True}]}],
        parse_output=True,
    )
    assert out[0][dev.host_name]["rc"] == 0, f"Failed to get CpuUsage on {dev.host_name} {out}"
    cpu_dict = out[0][dev.host_name]["parsed_output"]
    if not check:
        return cpu_dict
    cpu_to_check = [
        "usr",
        "nice",
        "sys",
        "irq",
        "soft",
        "steal",
        "guest",
        "gnice",
    ]
    for cpu, ocpu in zip(cpu_dict, prev_state["cpu"]):
        for k, v in cpu.items():
            if k not in cpu_to_check:
                continue
            diff_p = abs(ocpu[k] - v) * 100.0
            if diff_p > 15.0:
                dev.applog.info("{} Value not in range {} {} {}".format(k, diff_p, v, ocpu[k]))
                # assert 0, f"Value out of range {k} {v} by {diff_p}"

    return cpu_dict


async def tb_device_check_disk(dev, prev_state, check):
    out = await DiskFree.show(
        input_data=[{dev.host_name: [{}]}],
        parse_output=True,
    )
    assert out[0][dev.host_name]["rc"] == 0, f"Failed to get DiskFree on {dev.host_name} {out}"
    dkt = out[0][dev.host_name]["parsed_output"]
    disk_dict = {}
    for d in dkt:
        disk_dict[d["mounted_on"]] = d

    if not check:
        return disk_dict

    for k, v in disk_dict.items():
        diff = abs(v["use_percentage"] - prev_state["disk"][k]["use_percentage"])
        if diff > 15.0:
            dev.applog.info(
                "{} Value not in range {} {} {}".format(
                    k, diff, v["use_percentage"], prev_state["disk"][k]["use_percentage"]
                )
            )
            assert 0, f"Value out of range {k} {v} by {diff} {out}"

    return disk_dict


async def tb_device_check_health(dev, prev_state, check):
    # check for memory usage
    # check for average load
    # check for critical services
    # check the cpu usage.
    # check traffic if possible

    cur_state = {}
    cur_state["services"] = await tb_device_check_services(dev, prev_state, check)
    cur_state["memory"] = await tb_device_check_memory(dev, prev_state, check)
    cur_state["cpu"] = await tb_device_check_cpu(dev, prev_state, False)
    cur_state["disk"] = await tb_device_check_disk(dev, prev_state, False)
    return cur_state


async def tb_check_and_install_pkg(device, package):
    rc, out = await device.run_cmd(f"{package} --version")
    if rc != 0:
        rc, out = await device.run_cmd(f"apt install {package} -y")
        if rc != 0:
            device.applog.info("Failed to install {package}")
            return False

    return True


async def tb_get_device_object_from_dut(testbed, dev, skip_tg=True, skip_disconnected=True):
    if dev.device_id not in testbed.devices_dict:
        testbed.applog.info("Skipping device {}".format(dev.device_id))
        return None
    device = testbed.devices_dict[dev.device_id]
    if skip_tg and device.type == DeviceType.TRAFFIC_GENERATOR:
        return None
    if skip_disconnected and not await device.is_connected():
        device.applog.info("Device not connected skipping")
        return None
    return device


async def tb_reset_ssh_connections(devices):
    # disconnect all the connections
    for device in devices:
        if device.ssh_conn_params.pssh:
            await device.conn_mgr.get_ssh_connection().disconnect()


async def tb_get_all_devices(
    testbed, exclude_devices=[DeviceType.TRAFFIC_GENERATOR], skip_disconnected=True
):
    tb_devices = testbed.devices
    devices = []
    if testbed.discovery_report:
        for dev in testbed.discovery_report.duts:
            dev = await tb_get_device_object_from_dut(
                testbed, dev, skip_tg=False, skip_disconnected=skip_disconnected
            )
            if not dev or dev.type in exclude_devices:
                continue
            devices.append(dev)
    else:
        for dev in tb_devices:
            if dev.type in exclude_devices:
                continue
            if skip_disconnected and not await dev.is_connected():
                continue
            devices.append(dev)
    return devices


async def tb_reload_nw_and_flush_firewall(devices):
    async def tb_device_flush_firewall(device):
        for cmd in [
            "ifreload -a",
            "systemctl restart frr.service",
            "iptables -F",
            "tc filter delete block 1 ingress",
        ]:
            await device.run_cmd(cmd, sudo=True)

    cos = list()
    for d in devices:
        if not await d.is_connected():
            continue
        cos.append(tb_device_flush_firewall(d))
    results = await asyncio.gather(*cos, return_exceptions=True)
    check_asyncio_results(results, "tb_reload_nw_and_flush_firewall")


async def tb_reload_firewall(devices):
    async def tb_device_reload_firewall(device):
        for cmd in [
            "ifreload -a",
            "systemctl restart frr.service",
            "iptables -F",
            "tc filter delete block 1 ingress",
            "systemctl restart IhmDentTcFlower.service",
        ]:
            await device.run_cmd(cmd, sudo=True)

    cos = list()
    for d in devices:
        if not await d.is_connected():
            continue
        cos.append(tb_device_reload_firewall(d))
    results = await asyncio.gather(*cos, return_exceptions=True)
    check_asyncio_results(results, "tb_reload_firewall")


async def tb_ping_device(device, target, pkt_loss_treshold=50, dump=False):
    pkt_stats = ""
    cmd = f"ping -c 10 {target}"
    rc, out = await device.run_cmd(cmd, sudo=True)
    if dump:
        device.applog.info(f"Ran {cmd} on {device.host_name} with rc {rc} and out {out}")
    for line in out.splitlines():
        line = line.rstrip()
        if "transmitted" in line:
            pkt_stats = line
    pkt_loss = next(
        (pkt_stat for pkt_stat in pkt_stats.split(",") if "packet loss" in pkt_stat), None
    )
    if pkt_loss:
        pkt_loss_percent = pkt_loss.strip().split(" ")[0].split(".")[0]
        pkt_loss_percent = int(pkt_loss_percent[: pkt_loss_percent.find("%")])
    else:
        pkt_loss_percent = -1
    # 0 for success
    # 1 for failure
    return 0 if pkt_loss_percent <= pkt_loss_treshold else 1



async def tb_device_onie_install(dev):
    await Onie.select(input_data=[{dev.host_name: [{"options": "install"}]}])
    await System.shutdown(input_data=[{dev.host_name: [{"options": "-r +1"}]}])
