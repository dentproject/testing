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
async def test_stress_cpu_usage(testbed):
    """
    - Abstract
      - to exhause the CPU and check if the critical process are still up and running.
    - create
      - exhaust cpu
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
            "affinity",  # --affinity N         start N workers that rapidly change CPU affinity
            "bsearch",  # --bsearch N          start N workers that exercise a binary search
            "clock",  # --clock N            start N workers thrashing clocks and POSIX timers
            "context",  # --context N          start N workers exercising user context
            "cpu",  # --cpu N              start N workers spinning on sqrt(rand())
            "crypt",  # --crypt N            start N workers performing password encryption
            "daemon",  # --daemon N           start N workers creating multiple daemons
            # "exec",  # --exec N             start N workers spinning on fork() and exec()
            "fork",  # --fork N             start N workers spinning on fork() and exit()
            "fp-error",  # --fp-error N         start N workers exercising floating point errors
            "futex",  # --futex N            start N workers exercising a fast mutex
            "getrandom",  # --getrandom N        start N workers fetching random data via getrandom()
            "heapsort",  # --heapsort N         start N workers heap sorting 32 bit random integers
            "hsearch",  # --hsearch N          start N workers that exercise a hash table search
            "icache",  # --icache N           start N CPU instruction cache thrashing workers
            "itimer",  # --itimer N           start N workers exercising interval timers
            "kcmp",  # --kcmp N             start N workers exercising kcmp
            "longjmp",  # --longjmp N          start N workers exercising setjmp/longjmp
            "lsearch",  # --lsearch N          start N workers that exercise a linear search
            "matrix",  # --matrix N           start N workers exercising matrix operations
            "mergesort",  # --mergesort N        start N workers merge sorting 32 bit random integers
            "pthread",  # --pthread N          start N workers that create multiple threads
            "ptrace",  # --ptrace N           start N workers that trace a child using ptrace
            "qsort",  # --qsort N            start N workers qsorting 32 bit random integers
            "sem",  # --sem N              start N workers doing semaphore operations
            "str",  # --str N              start N workers exercising lib C string functions
            "timer",  # --timer N            start N workers producing timer events
            "tsearch",  # --tsearch N          start N workers that exercise a tree search
            "vfork",  # --vfork N            start N workers spinning on vfork() and exit()
        ]
        for cmd in cmds:
            cmd = f"stress-ng --{cmd} {cpu} --metrics-brief --perf --timeout 10s"
            rc, out = await device.run_cmd(cmd)
            assert rc == 0, f"Failed to run {cmd} {out}"
            device.applog.info(f"{cmd}: {rc} {out}")

        # check the system state
        await tb_device_check_health(device, prev_state, True)
