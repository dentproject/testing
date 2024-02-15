"""Module implementing SSH connection layer - Used for executing commands over SSH and SCP
"""
import io

import asyncssh


class SSHClient(asyncssh.SSHClient):
    """
    Class used to receive connnection updates for asyncssh.create_connection
    """

    def __init__(self):
        self.auth_made = False
        self.conn_made = False

    def connection_made(self, conn):
        self.conn_made = True
        print(f"Connection made to {conn.get_extra_info('peername')[0]}")

    def auth_completed(self):
        self.auth_made = True
        print('Authentication complete')

    def connection_lost(self, exc):
        self.conn_made = False
        self.auth_made = False

    # This is to accept public host key without a prompt
    def validate_host_public_key(self, host, addr, port, key):
        return True


class SSHConnection:
    """
    SSHConnection class - Used for executing commands over SSH and SCP
    """

    _DEFAULT_PORT = 22
    _SUCCESS = 0

    def __init__(self, logger, loop, connection_params):
        """
        Initializliation for SSHConnection

        Args:
            logger (Logger.Apploger): Logger
            loop: Event loop to use for scheduling the async methods for this class
            connection_params (dict): Connection parameters

        Raises:
            ValueError: If arguments are invalid
            Exception: For generic failures
        """
        try:
            self._validate_and_update_params(logger, loop, connection_params)
            self.conn = None
        except Exception as e:
            self.applog.exception('Error initializing SSH connection', exc_info=e)
            raise

    async def run_cmd(self, cmd, bufsize=io.DEFAULT_BUFFER_SIZE, input=None):
        """
        Run command through SSH connection

        Args:
            cmd (str): Command to execute
            bufsize:  Buffer size to use when feeding data from to stdin
            input: Input data to feed to standard input of the remote process

        Raises:
            Exception: For generic failures
        """
        try:
            if not cmd:
                raise ValueError('Empty command is not allowed')
            self.applog.debug(f'Running {cmd}')
            if not self.conn:
                await self._connect()
            self.sshlog.debug(cmd)
            try:
                result = await self.conn.run(cmd, bufsize=bufsize, input=input)
            except Exception as e:
                await self._connect()
                self.sshlog.debug(f'Caught SSH {e} Error, Re-Running {cmd}')
                result = await self.conn.run(cmd, bufsize=bufsize, input=input)
            self.applog.debug(f'Executed {cmd}; exit_status {result.exit_status}')
            self.sshlog.debug(result.stdout + result.stderr)
            return result.exit_status, result.stdout + result.stderr
        except Exception as e:
            self.applog.exception(f'Error running command: {cmd}', exc_info=e)
            raise

    async def copy_local_to_remote(self, src, dst):
        """
        SCP from local to remote

        Args:
            src (str): Source path in local host
            dst(str): Destination path in remote host

        Raises:
            Exception: For generic failures
        """
        try:
            self.applog.debug(f'Copying from local {src} to remote {dst}')
            await self._connect()
            await asyncssh.scp(src, (self.conn, dst))
            self.applog.debug(f'Successfully copied from local {src} to remote {dst}')
        except Exception as e:
            self.applog.exception(f'copy_local_to_remote {src} {dst}', exc_info=e)
            raise

    async def copy_remote_to_local(self, src, dst):
        """
        SCP from remote to local

        Args:
            src (str): Source path in remote host
            dst(str): Destination path in local host

        Raises:
            Exception: For generic failures
        """
        try:
            self.applog.debug(f'Copying from remote {src} to local {dst}')
            await self._connect()
            await asyncssh.scp((self.conn, src), dst)
            self.applog.debug(f'Successfully copied from remote {src} to local {dst}')
        except Exception as e:
            self.applog.exception(f'copy_remote_to_local {src} {dst}', exc_info=e)
            raise

    async def is_connected(self):
        """
        Check if in connected state - State ready for command execution

        Raises:
            Exception: For generic failures
        """
        try:
            return await self._connected()
        except Exception as e:
            self.applog.exception('Exception occured --> is_connected', exc_info=e)
            raise

    async def disconnect(self):
        """
        Disconnect this connection

        Raises:
            Exception: For generic failures
        """
        try:
            if await self._connected():
                self.applog.debug('Disconnecting')
                self.conn.close()
                self.conn = None
                self.applog.debug('Disconnect complete')
            else:
                self.applog.debug('No active connection to disconnect')
        except Exception as e:
            self.applog.exception('Exception --> SSH disconnect', exc_info=e)
            raise

    def _validate_and_update_params(self, logger, loop, connection_params):
        if not loop:
            raise ValueError(
                'SSHConnection class needs a running event loop to manage its async APIs'
            )
        if not connection_params.ip:
            raise ValueError('No IP provided to create SSHConnection')
        self.ip = connection_params.ip
        self.applog = logger.tag_logs(self.ip)
        self.sshlog = connection_params.logger
        if not connection_params.username:
            raise ValueError('No username provided to create SSHConnection')
        self.user_name = connection_params.username
        if connection_params.password:
            self.password = connection_params.password
        elif connection_params.public_key and connection_params.passphrase:
            self.public_key = connection_params.public_key
            self.passphrase = connection_params.passphrase
        else:
            raise ValueError('Neither password nor public key provided to create SSHConnection')

    async def _connected(self):
        try:
            if self.conn:
                result = await self.conn.run('date')
                if result.exit_status == SSHConnection._SUCCESS:
                    stdout = result.stdout.rstrip('\n')
                    self.applog.debug(f'Connection to device is healthy at {stdout}')
                    result = True
                else:
                    result = False
            else:
                result = False
            return result
        except Exception as e:
            print(e)
            self.applog.debug('Currently no connection exists to device')
            return False

    async def _connect(self):
        try:
            if not await self._connected():
                if self.password:
                    self.conn, _ = await asyncssh.create_connection(
                        SSHClient,
                        self.ip,
                        username=self.user_name,
                        password=self.password,
                        known_hosts=None,
                    )
                elif self.public_key:
                    self.conn, _ = await asyncssh.create_connection(
                        SSHClient,
                        self.ip,
                        username=self.user_name,
                        client_keys=self.public_key,
                        passphrase=self.passphrase,
                        known_hosts=None,
                    )
                else:
                    invalid_credentials = 'Invalid SSH credentials for device %s' % self.ip
                    raise RuntimeError(invalid_credentials)
        except Exception as e:
            self.applog.exception('Error establishing connection', exc_info=e)
            raise
