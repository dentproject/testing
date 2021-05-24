"""Utility module for device control
"""

import os
import time
from enum import Enum, unique

from net_utils.PingUtil import PingUtil

from dent_os_testbed.logger.Logger import DeviceLogger
from dent_os_testbed.utils.ConnectionHandlers import ConnectionParams
from dent_os_testbed.utils.ConnectionHandlers.ConnectionManager import ConnectionManager


@unique
class DeviceType(Enum):
    UNKNOWN = 0
    DISTRIBUTION_ROUTER = 1
    AGGREGATION_ROUTER = 2
    BLACKFOOT_ROUTER = 3
    OUT_OF_BOUND_SWITCH = 4
    INFRA_SWITCH = 5
    ROUTER_SWITCH = 6
    LTE_MODEM = 7
    TRAFFIC_HELPER = 8
    TRAFFIC_GENERATOR = 9
    CONSOLE_SERVER = 10


class Device(object):
    """
    Class representing a Device. Contains attributes of the device and methods
    to control the device. The APIs of the class are async and the calling application
    needs to have a running event loop before calling the APIs fo the class.
    """

    PING_PKT_LOSS_TRESHOLD_PERCENT = 20
    SERIAL_LOG_FILE_NAME = "serial_logs.txt"
    SSH_LOG_FILE_NAME = "ssh_logs.txt"
    LOGS_BASE_DIR = "./logs/"
    GET_OS_INFO_CMD = "cat /etc/onl/SWI | cut -d: -f 2"

    def __init__(self, logger, loop, params):
        """
        Initializliation for device - Device attributes, connections and
        device specifc logging

        Args:
            logger (Logger.Apploger): Logger
            loop: Event loop to use for scheduling the async methods for this class
            params (dict): Key value pairs representing the device attributes

        Raises:
            ValueError: If event loop is not passed
            Exception: For generic failure in device initialization
        """
        if not loop:
            raise ValueError("Device class needs a running event loop to manage its async APIs")
        try:
            self.loop = loop
            self.friendly_name = params["friendlyName"]
            self.applog = logger.tag_logs(self.friendly_name)
            self.applog.debug(f"Initializing device")
            self.os = params["os"]
            self.host_name = params["hostName"]
            self.ip = params["ip"]
            self.force_update = params.get("forceUpdate", True)
            self.login = params["login"]
            self.serial_dev = params["serialDev"]
            self.baudrate = params["baudrate"]
            self.links = params.get("links", [])
            self.type = DeviceType.__members__[params.get("type", "UNKNOWN")]
            self.files_to_collect = []
            # dictionary of links with device name as key
            self.links_dict = {}
            for link in self.links:
                fr, to = link[0], link[1]
                dut, port = to.split(":")
                if dut not in self.links_dict:
                    self.links_dict[dut] = [[], []]  # from and port seperate array
                self.links_dict[dut][0].append(fr)
                self.links_dict[dut][1].append(port)
            self.username = self.login["userName"]
            self.password = self.login["password"]
            self.ssh_log = DeviceLogger(
                device_name=self.host_name, log_file_name=Device.SSH_LOG_FILE_NAME
            )
            self.ssh_conn_params = (
                ConnectionParams.Builder()
                .username(self.login["userName"])
                .ip(self.ip)
                .password(self.login["password"])
                .hostname(self.host_name)
                .logger(self.ssh_log)
                .build()
            )
            if "pssh" in params:
                self.ssh_conn_params.pssh = params["pssh"]
                self.ssh_conn_params.aws_region = params["aws_region"]
                self.ssh_conn_params.store_domain = params["store_domain"]
                self.ssh_conn_params.store_type = params["store_type"]
                self.ssh_conn_params.store_id = params["store_id"]

            self.serial_logs_base_dir = Device.LOGS_BASE_DIR + self.host_name
            if not os.path.exists(self.serial_logs_base_dir):
                os.makedirs(self.serial_logs_base_dir)
            self.serial_conn_params = (
                ConnectionParams.Builder()
                .username(self.login["userName"])
                .password(self.login["password"])
                .serial_dev(self.serial_dev)
                .baudrate(self.baudrate)
                .hostname(self.host_name)
                .log_file_path(self.serial_logs_base_dir + "/" + Device.SERIAL_LOG_FILE_NAME)
                .build()
            )
            self.conn_mgr = ConnectionManager(
                logger, loop, self.ssh_conn_params, self.serial_conn_params
            )
            self.applog.debug(f"Device successfully initialized")

        except Exception as e:
            self._handle_exception(e, "Error in device initialization")

    def __repr__(self):
        return f"[{self.friendly_name}: {self.ip}]"

    async def verify_ping(self, timeout):
        """
        Verify ping to the device

        Args:
            timeout(int): Max timeout in seconds to retry for pings

        Raises:
            TimeoutError: If no response from ping for the given 'timeout' seconds
            Exception: For generic failures
        """
        try:
            self.applog.debug(f"Testing reachability through ping..")
            exec_time = 0
            while exec_time <= timeout:
                ping_chk_stime = time.time()
                reachable = await PingUtil.verify_ping(
                    self.ip, Device.PING_PKT_LOSS_TRESHOLD_PERCENT
                )
                ping_chk_etime = time.time()
                if reachable:
                    self.applog.debug(f"Device is reachable through ping")
                    return
                exec_time += int(ping_chk_etime - ping_chk_stime)
                self.applog.debug(
                    f"Not reachable after {exec_time} secs, retrying ping to {self.host_name}"
                )
            raise TimeoutError(f"No ping response from {self.host_name} after timeout secs")
        except Exception as e:
            self._handle_exception(e, "Error in ping")

    async def scp(self, local_path, remote_path, remote_to_local=False):
        """
        Secure copy from/to the device

        Args:
            local_path(string): Local path of the file
            remote_path(string): Remote path of the file
            remote_to_local(boolean): Flag to enable remote to local copy.
            (Default: local to remote)
        Raises:
            Exception: For generic failures
        """
        try:
            self.applog.debug(f"Copying from {local_path} to {remote_path}")
            if not remote_to_local:
                await self.conn_mgr.get_ssh_connection().copy_local_to_remote(
                    local_path, remote_path
                )
                self.applog.debug(f"Successfully copied from {local_path} to {remote_path}")
            else:
                await self.conn_mgr.get_ssh_connection().copy_remote_to_local(
                    remote_path, local_path
                )
                self.applog.debug(f"Successfully copied from {remote_path} to {local_path}")
        except Exception as e:
            self._handle_exception(e, "Error in scp")

    async def run_cmd(self, cmd, console="ssh", sudo=False):
        """
        Run the command on the devices console SSH/Serial

        Args:
            cmd(string): Command to execute on the device
            console(string): Console on which the command needs to be run ("ssh"/"serial")
            sudo(boolean): If set to true, the command will be executed as the sudo user

        Raises:
            Exception: For generic failures
        """
        try:
            if sudo:
                cmd = self._get_sudo_cmd(cmd)
            self.applog.debug(f"Executing command {cmd}")
            if console == "ssh":
                exit_status, stdout = await self.conn_mgr.get_ssh_connection().run_cmd(cmd)
            elif console == "serial":
                exit_status, stdout = await self.conn_mgr.get_serial_connection().run_cmd(cmd)
            self.applog.debug(f"{cmd} executed, ret_code = {exit_status}")
            return exit_status, stdout
        except Exception as e:
            self._handle_exception(e, f"Error executing {cmd}")

    async def get_os_info(self):
        """
        Get OS information of the device

        Raises:
            Exception: For generic failures
        """
        try:
            _, stdout = await self.conn_mgr.get_serial_connection().run_cmd(Device.GET_OS_INFO_CMD)
            return stdout
        except Exception as e:
            self._handle_exception(e, "Error in get_os_info")
            raise

    async def reboot(self):
        """
        Reboot the device

        Raises:
            Exception: For generic failures
        """
        try:
            await self.conn_mgr.close_connections()
        except Exception as e:
            self.applog.exception("Exception while closing connections", exc_info=e)
        try:
            self.applog.debug(f"Triggering reboot")
            reboot_cmd = self._get_sudo_cmd("reboot")
            await self.conn_mgr.get_ssh_connection().run_cmd(reboot_cmd)
            self.applog.debug("Successfully triggered reboot")
        except Exception as e:
            self._handle_exception(e, "Error in reboot")

    async def is_connected(self):
        """
        Verify connectivity (SSH) to the device.

        Raises:
            Exception: For generic failures
        """
        result = False
        try:
            exit_status, _ = await self.conn_mgr.get_ssh_connection().run_cmd("date")
            if exit_status == 0:
                result = True
        except Exception as e:
            self.applog.exception(f"Exception --> {Device.is_connected.__qualname__}", exc_info=e)
        return result

    async def cleanup(self):
        """
        Clean up the device - Close open connections(SSH/Serial) of the device

        Raises:
            Exception: For generic failures
        """
        try:
            self.conn_mgr.cleanup()
        except Exception as e:
            self.applog.exception(f"Exception --> {Device.cleanup.__qualname__}", exc_info=e)
            raise

    def _get_sudo_cmd(self, cmd):
        return f'echo {self.login["password"]} | sudo -S {cmd}'

    def _handle_exception(self, e, except_str):
        self.applog.exception(f"{except_str}", exc_info=e)
        e.extra_info = self.friendly_name
        raise e
