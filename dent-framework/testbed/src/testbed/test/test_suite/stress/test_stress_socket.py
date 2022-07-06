import json
import os
import time

import pytest

from testbed.Device import DeviceType
from testbed.utils.test_utils.tb_utils import (
    tb_check_and_install_pkg,
    tb_device_check_health,
    tb_get_device_object_from_dut,
)

pytestmark = pytest.mark.suite_stress


@pytest.mark.asyncio
async def test_stress_sock_usage(testbed):
    """
    Test Name: test_stress_sock_usage
    Test Suite: suite_stress
    Test Overview: to exhause the SOCK and check if the critical process are still up and running.
    Test Procedure:
    1. create
      - exhaust sock
      - wait for some soak time so that processes react the system change
    2. check for critical process if  they are up and running
      - sshd, poectl, frr services, dhcpd,
    3. perform some basic operation like link up down
    4. dns lookup etc.
    5. cleanup
     - cleanup the files created.
    """
    if not testbed.discovery_report:
        testbed.applog.info(
            f"Discovery report not present, +"
            "skipping run_test in {test_stress_exhause_disk_space.__func__}"
        )
        return
    for dev in testbed.discovery_report.duts:
        device = await tb_get_device_object_from_dut(testbed, dev)
        if not device:
            continue
        if not await tb_check_and_install_pkg(device, "stress-ng"):
            continue
        cpu = len(dev.system.os.cpu)
        prev_state = await tb_device_check_health(device, None, False)
        cmds = [
            # "dccp",  # --dccp N             start N workers exercising network DCCP I/O
            "dnotify",  # --dnotify N          start N workers exercising dnotify events
            "epoll",  # --epoll N            start N workers doing epoll handled socket activity
            "fifo",  # --fifo N             start N workers exercising fifo I/O
            "inotify",  # --inotify N          start N workers exercising inotify events
            "mq",  # --mq N               start N workers passing messages using POSIX messages
            # "netlink-proc",  # --netlink-proc N     start N workers exercising netlink process events
            "pipe",  # --pipe N             start N workers exercising pipe I/O
            "sock",  # --sock N             start N workers exercising socket I/O
            "sockfd",  # --sockfd N           start N workers sending file descriptors over sockets
            "udp",  # --udp N              start N workers performing UDP send/receives
            "udp-flood",  # --udp-flood N        start N workers that performs a UDP flood attack
        ]
        for cmd in cmds:
            cmd = f"stress-ng --{cmd} {cpu} --metrics-brief --perf --timeout 10s"
            rc, out = await device.run_cmd(cmd)
            assert rc == 0, f"Failed to run {cmd} {out}"
            device.applog.info(f"{cmd}: {rc} {out}")
        # check the system state
        await tb_device_check_health(device, prev_state, True)
