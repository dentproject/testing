# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
import json
import time

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.lib.frr.bgp import Bgp
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_route import IpRoute
from dent_os_testbed.lib.poe.poectl import Poectl
from dent_os_testbed.utils.test_utils.tb_utils import (
    tb_device_check_services,
    tb_ping_device,
    tb_reset_ssh_connections,
)


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
    services.append("frr.service")
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
    cmd = "ntpq -np | grep '^\\*'"
    rc, out = await dev.run_cmd(cmd, sudo=True)
    dev.applog.info(f"Ran {cmd} rc {rc} out {out}")
    if rc != 0:
        dev.applog.info(f"NTP not synced {rc} {out}")
        return False
    return True
