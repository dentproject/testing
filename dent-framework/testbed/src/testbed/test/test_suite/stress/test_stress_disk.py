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
async def test_stress_exhause_disk_space(testbed):
    """
    Test Name: test_stress_exhause_disk_space
    Test Suite: suite_stress
    Test Overview: to exhause the diskspace and check if the critical process are still up and running.
    Test Procedure:
    1. create
      - mix of small size files
      - mix of large size files
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
            "aio",  # --aio N              start N workers that issue async I/O requests
            "chdir",  # --chdir N            start N workers thrashing chdir on many paths
            "chmod",  # --chmod N            start N workers thrashing chmod file mode bits
            "chown",  # --chown N            start N workers thrashing chown file ownership
            "copy-file",  # --copy-file N        start N workers that copy file data
            "dentry",  # --dentry N           start N dentry thrashing stressors
            "dir",  # --dir N              start N directory thrashing stressors
            "dirdeep",  # --dirdeep N          start N directory depth stressors
            "fallocate-bytes 1G --fallocate",  # --fallocate N        start N workers fallocating 16MB files
            "fallocate-bytes 512M --fallocate",  # --fallocate-bytes N  specify size of file to allocate
            "fcntl",  # --fcntl N            start N workers exercising fcntl commands
            "fiemap",  # --fiemap N           start N workers exercising the FIEMAP ioctl
            "filename",  # --filename N         start N workers exercising filenames
            "flock",  # --flock N            start N workers locking a single file
            "fstat",  # --fstat N            start N workers exercising fstat on files
            "full",  # --full N             start N workers exercising /dev/full
            "getdent",  # --getdent N          start N workers reading directories using getdents
            "hdd",  # --hdd N              start N workers spinning on write()/unlink()
            "io",  # --io N               start N workers spinning on sync()
            "link",  # --link N             start N workers creating hard links
            "mknod",  # --mknod N            start N workers that exercise mknod
            "open",  # --open N             start N workers exercising open/close
            "readahead",  # --readahead N        start N workers exercising file readahead
            "rename",  # --rename N           start N workers exercising file renames
            "seek",  # --seek N             start N workers performing random seek r/w IO
            "sendfile",  # --sendfile N         start N workers exercising sendfile
            "symlink",  # --symlink N          start N workers creating symbolic links
            "sync-file",  # --sync-file N        start N workers exercise sync_file_range
        ]
        for cmd in cmds:
            cmd = f"stress-ng --{cmd} {cpu} --metrics-brief --perf --timeout 10s"
            rc, out = await device.run_cmd(cmd)
            assert rc == 0, f"Failed to run {cmd} {out}"
            device.applog.info(f"{cmd}: {rc} {out}")

        # check the system state
        await tb_device_check_health(device, prev_state, True)
