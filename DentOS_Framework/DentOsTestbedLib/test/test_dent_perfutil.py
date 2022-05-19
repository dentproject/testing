import time

from dent_os_testbed.utils.perf_util import PerfUtil

from .utils import TestDevice


def test_that_perf_util(capfd):
    dv = TestDevice()
    util = PerfUtil(devices=[dv], frequency=1)
    util.start_monitoring()
    time.sleep(5)
    util.stop_monitoring()
    try:
        util.analyze(thresholds={"CPU": {"idle": (0.0, 50.0)}})
    except Exception as e:
        print(e)

    try:
        util.analyze(thresholds={"Memory": {"mem_total": (0, 1024)}})
    except Exception as e:
        print(e)

    try:
        util.analyze(thresholds={"Process": {"all": {"VmPeak": (0, 1024)}}})
    except Exception as e:
        print(e)

    try:
        util.analyze(thresholds={"Process": {"sshd": {"VmPeak": (0, 1024)}}})
    except Exception as e:
        print(e)


def test_that_perf_during_test(capfd):
    dv = TestDevice()
    util = PerfUtil(
        devices=[dv],
        frequency=1,
        thresholds={
            "CPU": {"idle": (0.0, 100.0)},
            "Memory": {"mem_total": (0, 102400000)},
            "Process": {"all": {"VmPeak": (0, 102400000)}, "sshd": {"VmPeak": (0, 102400000)}},
        },
    )
    util.start_monitoring()
    time.sleep(2)
    util.set_thresholds(
        device=dv,
        thresholds={
            "CPU": {"idle": (0.0, 10.0)},
            "Memory": {"mem_total": (0, 102400000)},
            "Process": {"all": {"VmPeak": (0, 102400000)}, "sshd": {"VmPeak": (0, 102400000)}},
        },
    )
    time.sleep(2)
    util.set_thresholds(
        device=dv,
        thresholds={
            "CPU": {"idle": (0.0, 100.0)},
            "Memory": {"mem_total": (0, 10)},
            "Process": {"all": {"VmPeak": (0, 102400000)}, "sshd": {"VmPeak": (0, 102400000)}},
        },
    )
    time.sleep(2)
    util.set_thresholds(
        device=dv,
        thresholds={
            "CPU": {"idle": (0.0, 100.0)},
            "Memory": {"mem_total": (0, 102400000)},
            "Process": {"all": {"VmPeak": (0, 1024)}, "sshd": {"VmPeak": (0, 1024)}},
        },
    )
    time.sleep(2)
    util.stop_monitoring()
