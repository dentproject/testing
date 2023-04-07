"""Module for installing OS through onie-select
"""
import os
import time


class OsInstallerOnieSelect:
    """
    Implements APIs for installing OS through onie-select
    """

    DEVICE_UP_WAIT_TIME_SECS = 60 * 3

    def __init__(self, logger, loop):
        """
        Initializliation for OsInstallerOnieSelect

        Args:
            logger (Logger.Apploger): Logger
            loop: Event loop to use for scheduling the async methods for this class

        Raises:
            ValueError: If event loop is not passed
            Exception: For generic failure in device initialization
        """
        try:
            if not loop:
                raise ValueError(
                    'OsInstallerOnie is an async utility and requires a running event loop'
                )
            self.loop = loop
            self.applog = logger
        except Exception as e:
            if self.applog:
                self.applog.exception('Error initializing OsInstallerOnieSelect', exc_info=e)
            raise

    async def install_os(self, device, os_image_download_url, staging_device, staging_path):
        """
        Install OS

        Args:
            device (Device): Device on which the OS needs to be installed
            os_image_download_url (str): HTTP URL to download the OS image from
            staging_device (Device): Device to stage the OS image,from which onie-select picks it up
            staging_path(str): Path on the staging device to which the OS image is copied to.

        Raises:
            ValueError: If event loop is not passed
            Exception: For generic failure in device initialization
        """
        try:
            self.applog.debug('Starting installation..')
            await self._stage_os_image(os_image_download_url, staging_device, staging_path)
            await self._run_onie_select(device)
            await self._reboot(device)
            self.applog.debug('Successfully installed image')
        except Exception as e:
            self.applog.exception('OsInstallerOnie.install_os', exc_info=e)
            raise

    async def verify_os(self, device, os_image_download_url, staging_device, staging_path):
        """
        Validate the installed OS

        Args:
            device (Device): Device on which the OS needs to be installed
            os_image_download_url (str): HTTP URL to download the OS image from
            staging_device (Device): Device to stage the OS image,from which onie-select picks it up
            staging_path(str): Path on the staging device to which the OS image is copied to.

        Raises:
            ValueError: If event loop is not passed
            Exception: For generic failure in device initialization
        """
        try:
            self.applog.debug('Starting installation..')
            os_image_name = os_image_download_url.split('/')[-1].replace(
                '_INSTALLED_INSTALLER', '.swi'
            )
            await self._validate_installation(device, os_image_name)
            self.applog.debug('Successfully validated image')
        except Exception as e:
            self.applog.exception('OsInstallerOnie.validate_os', exc_info=e)
            raise

    async def _run_onie_select(self, device):
        try:
            await device.run_cmd('onie-select install', sudo=True)
        except Exception as e:
            self.applog.exception(
                f'{OsInstallerOnieSelect._run_onie_select.__qualname__}', exc_info=e
            )
            raise

    async def _reboot(self, device):
        try:
            self.applog.debug('Rebooting device')
            await device.reboot()
            self.applog.debug('Device rebooted successfully')
        except Exception as e:
            self.applog.exception(f'{OsInstallerOnieSelect._reboot.__qualname__}', exc_info=e)
            raise

    async def _validate_installation(self, device, expected_version):
        try:
            total_time = 0
            while total_time <= OsInstallerOnieSelect.DEVICE_UP_WAIT_TIME_SECS:
                start_time = time.time()
                self.applog.debug('Retrieving OS info to validate installation')
                os_info = await device.get_os_info()
                if os_info == expected_version:
                    return
                else:
                    err_str = f'Installation failed. expected:{expected_version} actual:{os_info}'
                    self.applog.error(err_str)
                    raise Exception(err_str)
                total_time += time.time() - start_time
            raise TimeoutError('Installation timeout')
        except Exception as e:
            self.applog.exception('Exception occured in retrieving OS information', exc_info=e)
            raise

    async def _stage_os_image(self, os_image_download_url, staging_device, staging_path):
        """OS image will be staged in the path 'onie_select_src_path; of 'onie_select_src_host'"""
        try:
            self.applog.debug(f'Staging OS image on {staging_device} at {staging_path}')
            await staging_device.run_cmd(
                f'wget {os_image_download_url} -O {staging_path}', sudo=True
            )
            self.applog.debug('Staging complete')
        except Exception as e:
            self.applog.exception('Exception occured --> stage_os_image', exc_info=e)
            raise
        finally:
            if os.path.exists(staging_path):
                self.applog.debug(f'Removing {staging_path}')
                os.remove(staging_path)
