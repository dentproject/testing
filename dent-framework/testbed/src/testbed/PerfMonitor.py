"""Wrapper module for PerfUtil
"""

from testbed.utils.perf_util import PerfUtil


class PerfMonitor:
    """Class that abstracts PerfUtil"""

    def __init__(self, logger, devices):
        """Initializer for PerfMonitor
        Args:
            logger (Logger.Apploger): Logger
            devices (list): List of Device instances whose performance needs to be monitored
        """
        self.perf_util = PerfUtil(devices=devices)
        self.monitoring = False
        self.applog = logger

    def start(self):
        """Start performance monitoring"""
        try:
            self.perf_util.start_monitoring()
            self.monitoring = True
        except Exception as e:
            self.applog.exception(
                f"Exception occured --> {PerfMonitor.start.__qualname__}", exec_info=e
            )
            raise

    def stop(self):
        """Stop performance monitoring monitoring"""
        try:
            if self.monitoring:
                self.perf_util.stop_monitoring()
        except Exception as e:
            self.applog.exception(
                f"Exception occured --> {PerfMonitor.stop.__qualname__}", exec_info=e
            )
            raise
