import json
import os
import time

import pytest

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.utils.test_suite.tb_utils import (
    tb_check_and_install_pkg,
    tb_device_check_health,
    tb_get_device_object_from_dut,
)

pytestmark = pytest.mark.suite_stress


@pytest.mark.asyncio
async def test_stress_mem_usage(testbed):
    """
    - Abstract
      - to exhause the MEM and check if the critical process are still up and running.
    - create
      - exhaust mem
      - wait for some soak time so that processes react the system change
    - check for critical process if  they are up and running
      - sshd, poectl, frr services, dhcpd,
    - perform some basic operation like link up down
    - dns lookup etc.
    - cleanup
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
            "bigheap",  # --bigheap N          start N workers that grow the heap using calloc()
            "cache",  # --cache N            start N CPU cache thrashing workers
            "fault",  # --fault N            start N workers producing page faults
            "malloc",  # --malloc N           start N workers exercising malloc/realloc/free
            "membarrier",  # --membarrier N       start N workers performing membarrier system calls
            "memcpy",  # --memcpy N           start N workers performing memory copies
            "memfd",  # --memfd N            start N workers allocating memory with memfd_create
            "mmap",  # --mmap N             start N workers stressing mmap and munmap
            "mremap",  # --mremap N           start N workers stressing mremap
            "stack",  # --stack N            start N workers generating stack overflows
            "stream",  # --stream N           start N workers exercising memory bandwidth
            "vm",  # --vm N               start N workers spinning on anonymous mmap
        ]
        for cmd in cmds:
            cmd = f"stress-ng --{cmd} {cpu} --metrics-brief --perf --timeout 10s"
            rc, out = await device.run_cmd(cmd)
            assert rc == 0, f"Failed to run {cmd} {out}"
            device.applog.info(f"{cmd}: {rc} {out}")
        # check the system state
        await tb_device_check_health(device, prev_state, True)
