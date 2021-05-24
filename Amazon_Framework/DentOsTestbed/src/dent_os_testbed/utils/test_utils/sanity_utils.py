# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
import json
import time

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_route import IpRoute
from dent_os_testbed.lib.poe.poectl import Poectl
from dent_os_testbed.utils.test_utils.tb_utils import (
    tb_device_check_services,
    tb_ping_device,
    tb_reset_ssh_connections,
)


async def check_certificates(dev, devices_dict):
    # certificates - should be refreshed every 10mins at /var/shared_resources/credentials/*.sts
    cmd = "find /var/shared_resources/credentials/ -name '*.sts' -mmin -10 -type f -exec ls  {} \;"
    rc, out = await dev.run_cmd(cmd, sudo=True)
    dev.applog.info(f"Ran {cmd} rc {rc} out {out}")
    # there should be atleast two files
    if rc or not out:
        rc, out = await dev.run_cmd("date && ls -l /var/shared_resources/credentials/*.sts")
        return False
    dev.applog.info(f"Found {out} files")
    return True


async def check_routes(dev, devices_dict):
    # Check routing and access to internet - Traffic test - check for offload

    out = await IpRoute.show(
        input_data=[{dev.host_name: [{"cmd_options": "-j -d "}]}], parse_output=True
    )
    assert out[0][dev.host_name]["rc"] == 0, f"Failed to get routes on {dev.host_name}"
    routes = out[0][dev.host_name]["parsed_output"]
    for route in routes:
        dst = route["dst"]
        if "offload" in route["flags"]:
            dev.applog.info(f"route {dst} offloaded")
            continue
        if "linkdown" in route["flags"]:
            dev.applog.info(f"route {dst} linkdown")
            continue
        # add exceptions
        dev.applog.info(f"checking route {dst} exceptions")
        # no device
        port = route.get("dev", "eth0")
        # mgmt interfces
        if port in ["eth0"]:
            continue
        if port.startswith("vlan") and port.endswith("-v0"):
            continue
        if dst in ["10.1.253.0/24", "10.2.0.222"]:
            continue
        dev.applog.info(f"route {route} not offloaded")
        return False
    return True


async def check_internet_connectivity(dev, devices_dict):
    rc = await tb_ping_device(dev, "www.amazon.com")
    if rc:
        dev.applog.info(f"Failed to reach internet")
        return False
    return True


async def check_wan_failover(dev, devices_dict):
    # WAN failover - do it per dist - turn off wan port and see reachability via other DIST - SWP10
    if dev.type == DeviceType.DISTRIBUTION_ROUTER:
        # TODO should we do this on dist also??
        return True

    if len(devices_dict[DeviceType.DISTRIBUTION_ROUTER]) < 2:
        dev.applog.info(f"Not sufficient dist router to perform this test")
        return True

    # down swp10 the link on one of the DIST
    dist = devices_dict[DeviceType.DISTRIBUTION_ROUTER][0]
    out = await IpLink.set(
        input_data=[{dist.host_name: [{"device": "swp10", "operstate": "up"}]}],
    )
    time.sleep(2)
    out = await IpLink.show(
        input_data=[{dist.host_name: [{"device": "swp10", "cmd_options": "-j"}]}],
        parse_output=True,
    )

    assert out[0][dist.host_name]["rc"] == 0, f"Failed to get swp10 link info on {dist.host_name}"
    links = out[0][dist.host_name]["parsed_output"]

    if links[0]["operstate"] == "DOWN":
        dev.applog.info("Link to the WAN is already down!!!")
        return False

    # bring down the link in background since the connection might be on this link
    cmd = "(sleep 1; sudo ip link set swp10 down) &"
    rc, out = await dist.run_cmd(cmd, sudo=True)
    if rc:
        dev.applog.info(f"Could do a link down on swp10 on {dist.host_name}")
        return False
    # disconnect and try now
    devices = []
    for d in devices_dict.values():
        devices.extend(d)
    await tb_reset_ssh_connections(devices)
    time.sleep(10)
    # check if we can reach the internet
    ret = await check_internet_connectivity(dev, devices_dict)

    out = await IpLink.set(
        input_data=[{dist.host_name: [{"device": "swp10", "operstate": "up"}]}],
    )
    if out[0][dist.host_name]["rc"]:
        dev.applog.info(f"Could not do a link up on swp10 on {dist.host_name}")
        return False
    time.sleep(10)
    return ret


async def check_wan_to_lte_failver(dev, devices_dict):
    # WAN failover - do it per dist - turn off wan port and see reachability via other DIST - SWP10
    if dev.type == DeviceType.DISTRIBUTION_ROUTER:
        # TODO should we do this on dist also??
        return True

    if len(devices_dict[DeviceType.DISTRIBUTION_ROUTER]) < 2:
        dev.applog.info(f"Not sufficient dist router to perform this test")
        return True

    devices = []
    for d in devices_dict.values():
        devices.extend(d)

    # down swp10 the link on one of the DIST
    for dist in devices_dict[DeviceType.DISTRIBUTION_ROUTER]:
        out = await IpLink.set(
            input_data=[{dist.host_name: [{"device": "swp10", "operstate": "up"}]}],
        )
        time.sleep(2)
        out = await IpLink.show(
            input_data=[{dist.host_name: [{"device": "swp10", "cmd_options": "-j"}]}],
            parse_output=True,
        )
        assert (
            out[0][dist.host_name]["rc"] == 0
        ), f"Failed to get swp10 link info on {dist.host_name}"
        links = out[0][dist.host_name]["parsed_output"]

        if links[0]["operstate"] == "DOWN":
            dev.applog.info("Link to the WAN is already down!!!")
            return False

        # bring down the link in background since the connection might be on this link
        cmd = "(sleep 1; sudo ip link set swp10 down) &"
        rc, out = await dist.run_cmd(cmd)
        if rc:
            dev.applog.info(f"Could not do a link down on swp10 on {dist.host_name}")
            return False
        # disconnect and try now
        await tb_reset_ssh_connections(devices)

    time.sleep(30)
    await tb_reset_ssh_connections(devices)

    # check if we can reach the internet
    ret = await check_internet_connectivity(dev, devices_dict)

    # bring em back up again.
    for dist in devices_dict[DeviceType.DISTRIBUTION_ROUTER]:
        # bring down the link in background since the connection might be on this link
        cmd = "(sleep 1; sudo ip link set swp10 up) &"
        rc, out = await dist.run_cmd(cmd)
        if rc:
            dev.applog.info(f"Could not do a link up on swp10 on {dist.host_name}")
            return False
    time.sleep(5)
    return ret


async def check_bgp_sessions(dev, devices_dict):
    # BGP sessions - exceptions due to missing aggs/dists/oobs.
    # Otherwise all should be UP. Check for "state":"Established" - show ip bgp summary json

    cmd = "vtysh -c 'show ip bgp summary json'"
    rc, out = await dev.run_cmd(cmd, sudo=True)
    dev.applog.info(f"Ran {cmd} rc {rc} out {out}")
    assert rc == 0, f"Failed get bgp summary {rc} {out}"
    bgp_summary = json.loads(out)
    for prefix, peer in bgp_summary["ipv4Unicast"]["peers"].items():
        if peer["state"] == "Established":
            dev.applog.info(f"{prefix} peer is in Established state")
            continue
        # handle exceptions
        dev.applog.info(f"{prefix} peer is in not Established state. Checking for excptions")
        if prefix in [
            "10.2.96.130",
            "10.2.96.134",
            "10.2.97.173",
            "10.2.96.173",
            "10.2.96.41",
            "10.2.96.45",
        ]:
            continue
        dev.applog.info(f"BGP peer {prefix} is supposed to be established {peer}")
        return False
    return True


async def check_services(dev, devices_dict):
    """
    Processes list check:
     1. keepaliveD (infra only)
     2. NTPD (all devices)
     3. DHCPD (on OOBs its onie-dhcp, one infra its isc-dhcp-server)
    """
    services = []
    services.append("auditd.service")
    services.append("awslogs.service")
    # services.append("bridge-interface.service")
    services.append("frr.service")
    services.append("IhmDentTcFlower.service")
    # if provisioned then need more services
    if dev.ssh_conn_params.pssh:
        services.append("bridge-agent.service")
        services.append("identity-agent.service")
        services.append("IhmInfraSystemsDeviceProvisioning.service")
        services.append("IhmNetworkDeviceHostMetricMonitoring.service")
        services.append("IhmNetworkDeviceMetricAgent.service")
        services.append("tennant.service")
    services.append("inetd.service")
    services.append("lldpd.service")
    services.append("lm-sensors.service")
    services.append("networking.service")
    services.append("ntp.service")
    services.append("onlpd.service")
    services.append("resolvconf.service")
    services.append("ssh.service")
    if dev.type == DeviceType.INFRA_SWITCH:
        services.append("keepalived.service")
        services.append("isc-dhcp-server.service")
        rc, out = await dev.run_cmd("ls /sputnik/env/IhmDentPoe/bin/poectl")
        if rc == 0:
            dev.applog.info("Adding poe service to check")
            services.append("IhmDentPoe.service")
    if dev.type == DeviceType.OUT_OF_BOUND_SWITCH:
        services.append("onie-dhcp.service")
    try:
        await tb_device_check_services(dev, None, True, services)
    except Exception:
        return False
    return True


async def check_ntp_sync(dev, devices_dict):
    """
    - NTP is in sync - ntpq -np (borrow code from ZTP)
    - look for synced peer
    ihm-infra@netprod-dentlab-sea55-mendel-oob-sw2:~$ ntpq -p
     remote           refid      st t when poll reach   delay   offset  jitter
    ==============================================================================
    -12.167.151.1    66.85.78.80      3 u   48  256  377   88.876   -3.292   0.331
    -68.233.45.146   130.207.244.240  2 u  107  256  375   61.408   -6.170   0.165
    +162.159.200.123 10.28.8.178      3 u   86  256  377    0.985    1.477   0.292
    -50.205.244.24   50.205.244.27    2 u  218  256  377   63.265   -2.898   0.302
    +10.2.190.100    10.2.191.100     3 u  246  256  377    0.151   -0.580   0.630
    *10.2.191.100    163.237.218.19   2 u   40  256  377    0.162   -2.040   0.137 <--- looking for this
    """
    cmd = "ntpq -np | grep '^\*'"
    rc, out = await dev.run_cmd(cmd, sudo=True)
    dev.applog.info(f"Ran {cmd} rc {rc} out {out}")
    if rc != 0:
        dev.applog.info(f"NTP not synced {rc} {out}")
        return False
    return True


async def check_infra_to_infra_ping(dev, devices_dict):
    """
    - Check infra to infra pings over vlan100 - 10.1.4.3 on infra1 and 10.1.4.2 on infra2.
    """
    if dev.type is not DeviceType.INFRA_SWITCH:
        return True

    for infra in devices_dict[DeviceType.INFRA_SWITCH]:
        # no need to ping self
        if infra.host_name == dev.host_name:
            continue

        # do a poing to this device
        # get the ip
        out = await IpAddress.show(
            input_data=[{infra.host_name: [{"dev": "vlan100", "cmd_options": "-j"}]}],
            parse_output=True,
        )
        assert (
            out[0][infra.host_name]["rc"] == 0
        ), f"Failed to get ip address for vlan100 on {infra.host_name}"

        addresses = out[0][infra.host_name]["parsed_output"]
        infra_ip = None
        for addr in addresses[0]["addr_info"]:
            if addr["family"] == "inet" and addr["scope"] == "global":
                infra_ip = addr["local"]

        if infra_ip is None:
            dev.applog.info(f"Could not get IP address for vlan100 to {infra.host_name}")

        rc = await tb_ping_device(dev, f"{infra_ip}", dump=True)
        if rc != 0:
            dev.applog.info(f"Failed to reach {infra.host_name} {rc}")
            return False

    return True


async def check_poe_devices(dev, devices_dict):
    """
    - check if the poectl works.
    """
    if dev.type is not DeviceType.INFRA_SWITCH:
        return True
    rc, out = await dev.run_cmd("ls /sputnik/env/IhmDentPoe/bin/poectl")
    if rc != 0:
        return True
    dev.applog.info("Checking for poectl Health")
    out = await Poectl.show(
        input_data=[{dev.host_name: [{"cmd_options": "-j -a"}]}],
        parse_output=True,
    )
    if out[0][dev.host_name]["rc"] != 0:
        dev.applog.info(f"{dev.host_name} poectl command returned failure {rc} {out}")
        return False
    ports = out[0][dev.host_name]["parsed_output"]
    if len(ports) < 48:
        n = len(ports)
        dev.applog.info(f"{dev.host_name} has fewer ports --> {n}")
        return False
    for data in ports:
        port = data["swp"]
        if not port.startswith("swp"):
            return False
    return True
