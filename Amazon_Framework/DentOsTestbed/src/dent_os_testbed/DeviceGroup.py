""" Implements DeviceGroup class for controlling a group of devices
"""

import asyncio

from dent_os_testbed.installers.OsInstallerOnieSelect import OsInstallerOnieSelect


class DeviceGroup:
    """
    DeviceGroup class for controlling a group of devices
    """

    def __init__(self, logger, loop):
        """
        Initializliation for DeviceGroup

        Args:
            logger(Logger.Apploger): Logger
            loop: Event loop to use for scheduling the async methods for this class

        Raises:
            Exception: For generic failures.
        """
        self.devices = []
        self.applog = logger
        self.loop = loop
        self.installer = OsInstallerOnieSelect(self.applog, self.loop)

    def add_device(self, device):
        """
        Add a device to this group.

        Args:
            device(Device): Device instance to be added to this group
        """
        self.devices.append(device)

    def add_devices(self, devices):
        """
        Add a list of devices to this group.

        Args:
            devices(List): List of device instances to be added
        """
        self.devices.extend(devices)

    def remove_devices(self, devices_to_remove):
        """
        Remove a list of devices from this group

        Args:
            devices(List): List of device instances to be removed
        """
        self.devices = list(filter(lambda device: (device not in devices_to_remove), self.devices))

    def run_cmd(self, cmd):
        """
        Exceute command on this DeviceGroup (all the devices in the group)

        Args:
            cmd(List): Command to execute
        """
        pass

    async def install_os(self, os_image_download_url):
        """
        Install OS for this DeviceGroup (all the devices in the group)

        Args:
            os_image_download_url(str): HTTP url of the OS image
        """
        coroutines = []
        self.applog.debug("DeviceGroup::install_image++")
        for device in self.devices:
            if device.force_update == "true" and device.os == "dentos":
                staging_device = device
                staging_path = "/onie-installer"
                coroutines.append(
                    self.installer.install_os(
                        device, os_image_download_url, staging_device, staging_path
                    )
                )
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        self._handle_device_failures_if_exists(results, "image installation")
        self.applog.debug("DeviceGroup::install_image--")

    async def verify_os(self, os_image_download_url):
        """
        Verify OS for this DeviceGroup (all the devices in the group)

        Args:
            os_image_download_url(str): HTTP url of the OS image
        """
        coroutines = []
        self.applog.debug("DeviceGroup::verify_image++")
        for device in self.devices:
            if device.force_update == "true" and device.os == "dentos":
                staging_device = device
                staging_path = "/onie-installer"
                coroutines.append(
                    self.installer.verify_os(
                        device, os_image_download_url, staging_device, staging_path
                    )
                )
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        self._handle_device_failures_if_exists(results, "image verification")
        self.applog.debug("DeviceGroup::verify_image--")

    def _handle_device_failures_if_exists(self, results, op):
        exception_occured = False
        failed_devices = []
        print(results)
        for r in results:
            if isinstance(r, Exception):
                exception_occured = True
                if "extra_info" in dir(r):
                    failed_devices.append(r.extra_info)
        if exception_occured:
            e = Exception(f"Failure in {op} for one more devices")
            e.extra_info = failed_devices
            raise e

    async def cleanup(self):
        """
        Clean up the DeviceGroup. Calls device.cleanup for all devices of the group.

        Args:
            os_image_download_url(str): HTTP url of the OS image

        Raises:
            Exception: For generic failures.
        """
        for device in self.devices:
            try:
                await device.cleanup()
            except Exception as e:
                self.applog.error(
                    f"Error closing connections for {device.host_name}."
                    + "Program termination will have issues. Kill the process before next run"
                )
                raise e
