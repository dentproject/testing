import time

import pytest
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.utils.perf_util import PerfUtil

from .utils import TestDevice

pytest.devices = [TestDevice()]
pytestmark = pytest.mark.skip('Perf tests still WIP')


class TestBedSetup(object):
    perf_util = None

    def __init__(self, *a, **kw):
        self.conf_args = a
        self.conf_kw = kw
        if not TestBedSetup.perf_util:
            TestBedSetup.perf_util = PerfUtil(devices=pytest.devices, frequency=1)
            # TestBedSetup.perf_util.start_monitoring()
        if 'perf_thresholds' in kw:
            TestBedSetup.perf_util.set_thresholds(thresholds=kw.get('perf_thresholds'))

    def __call__(self, func, *args, **kwargs):
        def wrapper(*args, **kwargs):
            if 'perf_thresholds' in self.conf_kw:
                print('Enabling Per for ' + func.__name__)
                TestBedSetup.perf_util.resume()
            val = func(*args, **kwargs)
            if 'perf_thresholds' in self.conf_kw:
                TestBedSetup.perf_util.pause()
            return val

        return wrapper


@TestBedSetup(
    discovery=True,
    perf_thresholds={
        'CPU': {'idle': (50.0, 100.0)},
        'Memory': {'MemTotal': (0, 81308160)},
        'Process': {'all': {'VmPeak': (0, 114680)}, 'sshd': {'VmPeak': (0, 114680)}},
    },
)
def test_that_iproute2_address(*args):

    # dummy test device
    dv1 = TestDevice()

    out = IpAddress.show(
        input_data=[{'test_dev': [{}]}],
        device_obj={'test_dev': dv1},
    )
    # check if the command was formed
    assert 'command' in out[0]['test_dev'].keys()
    assert 'result' in out[0]['test_dev'].keys()
    time.sleep(3)


@TestBedSetup(
    discovery=True,
    perf_thresholds={
        'CPU': {'idle': (60.0, 100.0)},
        'Memory': {'MemTotal': (0, 81308160)},
        'Process': {'all': {'VmPeak': (0, 114680)}, 'sshd': {'VmPeak': (0, 114680)}},
    },
)
def test_that_iproute2_link(*args):

    # dummy test device
    dv1 = TestDevice()

    out = IpLink.show(
        input_data=[{'test_dev': [{}]}],
        device_obj={'test_dev': dv1},
    )

    # check if the command was formed
    assert 'command' in out[0]['test_dev'].keys()
    assert 'result' in out[0]['test_dev'].keys()
    time.sleep(3)
