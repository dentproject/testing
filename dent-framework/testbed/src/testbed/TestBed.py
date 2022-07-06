""" Testbed module - Representing the tesbed to run tests on.
    Testbed contains devices and configurations.
    Orchestrates - installation, discovery and test execution.
"""
import json
import time

from testbed.Device import Device
from testbed.DeviceGroup import DeviceGroup
from testbed.DiscoveryManager import DiscoveryManager
# from testbed.PerfMonitor import PerfMonitor
from testbed.utils.FileHandlers.FileHandlerFactory import (
    FileHandlerFactory,
    FileHandlerTypes,
)


class TestBed:
    """
    TestBed class - contains devices, config, discovery info
    Implements APIs to install OS, perform discovery
    """

    def __init__(self, logger, loop, args):
        """
        Initializliation for TestBed

        Args:
            logger(Logger.Apploger): Logger
            loop: Event loop to use for scheduling the async methods for this class
            args: Command line arguments for testbed

        Raises:
            Exception: For generic failures.
        """
        try:
            self.args = args
            self.applog = logger
            self.applog.debug("Initializing TestBed")
            self.applog.debug(f"Loading configuration file from {args.config}")
            file_handler = FileHandlerFactory.get_file_handler(FileHandlerTypes.LOCAL, self.applog)
            self.config = json.loads(file_handler.read(args.config))
            self.loop = loop
            self.device_group = DeviceGroup(self.applog, self.loop)
            if args.use_pssh:
                for cfg in self.config["devices"]:
                    cfg["pssh"] = True
                    cfg["aws_region"] = args.aws_region
                    cfg["store_domain"] = args.store_domain
                    cfg["store_type"] = args.store_type
                    cfg["store_id"] = args.store_id
            self.devices = [
                Device(self.applog, self.loop, device) for device in self.config["devices"]
            ]
            self.device_group.add_devices(self.devices)
            self.devices_dict = {d.host_name: d for d in self.devices}
            self.discovery_report = None
            # self.perf_monitor = PerfMonitor(self.devices)
            # self.perf_monitor.start()
            self.applog.debug("TestBed initialized")
        except Exception as e:
            self.applog.exception("Error initializing testbed:", exc_info=e)
            raise

    async def cleanup(self):
        """
        Cleanup for TestBed

        Raises:
            Exception: For generic failures.
        """
        try:
            # self.perf_monitor.stop()
            await self.device_group.cleanup()
        except:
            self.applog.exception("Error occurred in stopping asyncio loop")

    async def install_os(self):
        """
        Install OS on the devices in the testbed

        Raises:
            Exception: For generic failures.
        """
        try:
            self.applog.debug("TestBed::_install_image++")
            await self.device_group.install_os(self.args.os_image_download_url)
            self.applog.debug("TestBed::_install_image--")
            time.sleep(7 * 60)
            # self.applog.debug("TestBed::_verify_image++")
            # await self.device_group.verify_os(self.args.os_image_download_url)
            # self.applog.debug("TestBed::_install_image--")
        except Exception as e:
            self.applog.exception("Error installing image on one or more devices:", exc_info=e)
            if "extra_info" in dir(e):
                self.applog.error(f"Failed devices: {e.extra_info}")
                self.device_group.remove_devices(e.extra_info)
            raise

    async def discover(self):
        """
        Perform discovery on the testbed - Determine running configurations

        Raises:
            Exception: For generic failures.
        """
        try:
            discovery = DiscoveryManager(
                self.applog, self.args, self.config, self.devices, self.devices_dict
            )
            self.discovery_report = await discovery.run()
        except Exception as e:
            self.applog.exception("Error running discovery", exc_info=e)
            raise

    async def update_links(self):
        """
        Update links information on devices in the testbed using discovery results

        Raises:
            Exception: For generic failures.
        """
        try:
            self.applog.debug("TestBed::update_links++")
            await self.device_group.update_links(self.discovery_report)
            self.applog.debug("TestBed::update_links--")
        except Exception as e:
            self.applog.exception("Error running update_links", exc_info=e)
            raise
