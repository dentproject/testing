"""ConnectionManager module to manage SSH and serial connections
"""

from dent_os_testbed.utils.ConnectionHandlers.SerialHandler import SerialConsole
from dent_os_testbed.utils.ConnectionHandlers.SSHHandler import SSHConnection


class ConnectionManager:
    """
    ConnectionManager class that implements APIs to get and release SSH/Serial connections.
    """

    NUMBER_OF_SSH_CONNS = 1

    def __init__(self, logger, loop, ssh_conn_params=None, serial_conn_params=None):
        """
        Initializliation for ConnectionManager

        Args:
            logger (Logger.Apploger): Logger
            loop: Event loop to use for scheduling the async methods for this class
            ssh_conn_params (ConnectionParams): SSH connection parameters
            serial_conn_params (ConnectionParams): Serial connection parameters

        Raises:
            ValueError: If event loop is not passed
            Exception: For generic failure
        """
        if not loop:
            raise ValueError(
                "ConnectionManager class needs a running event loop"
                + " to manage its connection objects"
            )
        self.applog = logger
        self.ssh_connection = None
        self.serial_connection = None
        self.loop = loop
        if ssh_conn_params:
            self.ssh_connection = SSHConnection(logger, self.loop, ssh_conn_params)
        if serial_conn_params:
            self.serial_connection = SerialConsole(logger, self.loop, serial_conn_params)

    # TODO: Currently, we only have 1 connection. We need to extend this to
    # a pool of connections per host
    def get_ssh_connection(self):
        """
        Get a SSHConnection instance

        Returns:
            SSHConnection
        """
        return self.ssh_connection

    def get_serial_connection(self):
        """
        Get a SerialConsole instance

        Returns:
            SerialConsole
        """
        return self.serial_connection

    async def close_connections(self):
        """
        Close all the connections managed by this ConnectionManager

        Raises:
            Exception: For generic failure
        """
        try:
            if self.ssh_connection:
                await self._close_ssh_connection()
            if self.serial_connection:
                self._close_serial_connection()
        except Exception as e:
            self.applog.exception(
                f"Exception --> {ConnectionManager.close_connections.__qualname__}", exc_info=e
            )
            raise

    def cleanup(self):
        """
        Perform clean up - Primarily call SerialConsole.cleanup

        Raises:
            Exception: For generic failure
        """
        try:
            if self.serial_connection:
                self.serial_connection.cleanup()
        except Exception as e:
            self.applog.exception(
                f"Exception --> {ConnectionManager.cleanup.__qualname__}", exc_info=e
            )
            raise

    async def _close_ssh_connection(self):
        try:
            await self.ssh_connection.disconnect()
        except Exception as e:
            self.applog.exception(
                f"Exception --> {ConnectionManager._close_ssh_connection.__qualname__}", exc_info=e
            )
            raise

    def _close_serial_connection(self):
        try:
            self.serial_connection.disconnect()
        except Exception as e:
            self.applog.exception(
                f"Exception --> {ConnectionManager._close_serial_connection.__qualname__}",
                exc_info=e,
            )
            raise
