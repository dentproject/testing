import functools

import pytest


class TestCaseSetup(object):
    """
    Decorator for
    """

    def __init__(self, *a, **kw):
        self.conf_args = a
        self.conf_kw = kw
        if "perf_thresholds" in kw:
            pytest.testbed.perf_util.set_thresholds(thresholds=kw.get("perf_thresholds"))

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if "perf_thresholds" in self.conf_kw:
                pytest.testbed.logger.info("Resuming Perf for " + func.__name__)
                pytest.testbed.perf_util.resume()
            if "setup" in self.conf_kw:
                pytest.testbed.logger.info("Invoking test case setup for  " + func.__name__)
                self.conf_kw["setup"]()
            val = func(*args, **kwargs)
            if "perf_thresholds" in self.conf_kw:
                pytest.testbed.logger.info("Pausing Perf for " + func.__name__)
                pytest.testbed.perf_util.pause()
            if "teardown" in self.conf_kw:
                pytest.testbed.logger.info("Invoking test case teardown for " + func.__name__)
                self.conf_kw["teardown"]()
            return val

        return wrapper
