"""Module for to manage SerialConnection: connect, execute commands, disconnect.
"""

import asyncio
import collections
from threading import Lock, Thread

import pexpect.fdpexpect
import serial


class DeviceType:
    DEVICE_DENT = 1


class SerialAsyncLoop:
    """
    It is a singleton factory that has one loop for all clients
    We want to invoke a separate thread and assign the loop to run in the thread
    so that, all tasks related to serial connection are run in background.
    """

    _loop = None
    _thread = None
    THREAD_JOIN_TIMEOUT_SECS = 30
    count = 0
    mutex = Lock()

    def __init__(self, logger):
        """
        Initializliation for SerialAsyncLoop

        Args:
            logger (Logger.Apploger): Logger
        """
        if logger:
            logger.info('Initializing SerialAsyncLoop')
        SerialAsyncLoop._loop = asyncio.new_event_loop()
        SerialAsyncLoop._thread = Thread(
            name='SerialAsyncLoop',
            target=SerialAsyncLoop.start_loop,
            args=[SerialAsyncLoop, SerialAsyncLoop._loop],
        )
        SerialAsyncLoop._thread.start()

    def start_loop(self, loop):
        """
        Start the event loop for this thread

        Args:
            loop: Event loop to use for scheduling the async methods
        """
        asyncio.set_event_loop(loop)
        loop.run_forever()

    @staticmethod
    def stop_loop(logger):
        """
        Stop the event loop

        Args:
            logger (Logger.Apploger): Logger
        """
        try:
            SerialAsyncLoop.mutex.acquire()
            SerialAsyncLoop.count -= 1
            if logger:
                logger.info(f'SerialAsyncLoop instance count: {SerialAsyncLoop.count}')
            if SerialAsyncLoop.count == 0:
                loop = SerialAsyncLoop._loop
                loop.call_soon_threadsafe(loop.stop)
                SerialAsyncLoop._thread.join(SerialAsyncLoop.THREAD_JOIN_TIMEOUT_SECS)
        except Exception as e:
            raise
        finally:
            SerialAsyncLoop.mutex.release()

    @staticmethod
    def get_loop(logger):
        """
        Static factory method to iniitalize this classs

        Args:
            logger (Logger.Apploger): Logger
        """
        try:
            SerialAsyncLoop.mutex.acquire()
            if SerialAsyncLoop.count == 0:
                SerialAsyncLoop(logger)
            SerialAsyncLoop.count += 1
            if logger:
                logger.info(f'SerialAsyncLoop instance count: {SerialAsyncLoop.count}')
            return SerialAsyncLoop._loop
        except Exception as e:
            raise
        finally:
            SerialAsyncLoop.mutex.release()


class SerialConsole:
    """
    SerialConsole class implementing the APIs required to manage a serial connection
    """

    MAX_CONSOLE_BUFFER = 1024 * 100
    PRINT_PREFIX = '<console>:'
    COMMAND_PROMPT = ''
    LOGIN_RETRIES = 20
    ONIE_WAIT = 30

    class LoginPexpectHelper:
        """
        Class to store constants used for serial console login
        """

        ONIE = 0
        LOGIN = 1
        PASSWORD = 2
        EOF = 3
        TIMEOUT = 4
        CMD_PROMPT = 5
        PEXPECT_MAP = collections.OrderedDict(
            [
                (ONIE, 'ONIE'),
                (LOGIN, '(?i)login'),
                (PASSWORD, '(?i)password'),
                (EOF, pexpect.EOF),
                (TIMEOUT, pexpect.TIMEOUT),
            ]
        )

    def __init__(self, logger, loop, conn_params):
        """
        Initializliation for SerialConsole

        Args:
            logger (Logger.Apploger): Logger
            loop: Event loop to use for scheduling the async methods for this class
            conn_params (ConnectionParams): Serial connection parameters.

        Raises:
            ValueError: If event loop is not passed/parameters are invalid
            Exception: For generic failure in SerialConsole initialization
        """
        try:
            self._validate_and_update_params(logger, loop, conn_params)
            self.device_type = DeviceType.DEVICE_DENT
            self.loop = SerialAsyncLoop.get_loop(logger)
            self.login_done = False
            self.login_successful = False
            self.console = None
            self.pexpect_child = None
            self.console_buffer = ''
            if self.username == 'root':
                self.cmd_prompt = f'{self.username}@localhost:~#'
            else:
                self.cmd_prompt = f'{self.username}@{self.hostname}:~$'
            SerialConsole.LoginPexpectHelper.PEXPECT_MAP[
                SerialConsole.LoginPexpectHelper.CMD_PROMPT
            ] = self.cmd_prompt
            if not self.username and not self.password:
                self.applog.info('Not trying to login since username/password ' 'not available')
                return
        except Exception as e:
            self.applog.exception('Exception --> Error initializing serial connection', exc_info=e)
            raise

    def _validate_and_update_params(self, logger, loop, conn_params):
        if not loop:
            raise ValueError(
                'SerialConsole class needs a running event loop to manage its async APIs'
            )
        if not conn_params.dev:
            raise ValueError('No serial device provided')
        self.dev = conn_params.dev
        self.logger = logger
        self.applog = logger.tag_logs(self.dev)
        # self.devlog = conn_params.logger.tag_logs(self.dev)
        self.log_file = open(conn_params.log_file_path, 'w')
        if not conn_params.username:
            raise ValueError('No username provided')
        self.username = conn_params.username
        if not conn_params.hostname:
            raise ValueError('No hostname provided')
        self.hostname = conn_params.hostname
        if not conn_params.baudrate:
            raise ValueError('Baud rate not provided')
        self.baudrate = conn_params.baudrate
        self.password = conn_params.password  # Not validating - What if password is empty?

    def login_cb(self, result):
        """
        Handles login completion from the '_login_routine'

        Raises:
            Exception: For generic failures
        """
        try:
            self.applog.info('Login done. %s' % ('Succeeded' if result.result() else 'Failed'))
            self.login_successful = result.result()
        except:
            self.applog.exception('Login to console %s failed' % self.dev)
            self.login_successful = False
        self.login_done = True
        return

    def login_info(self):
        """
        Get login information

        Returns:
            (login_done, login_successful) -> Indicates if login attempt is done and is successful
        """
        return (self.login_done, self.login_successful)

    async def logged_in(self):
        """
        Verify if logged in to console

        Returns:
            True if logged in False otherwise

        Raises:
            Exception: For generic failures
        """
        if not self.pexpect_child or not self.console:
            return False
        try:
            self._flush_buffer()
            exit_status, result = await self._run_cmd('who')
            if exit_status != 0:
                return False
            if result:
                fields = [line for line in result.splitlines()][0].split()
            self.applog.info(f'user/ttyinfo:{fields}')
            return fields and fields[0] == self.username and 'tty' in fields[1]
        except Exception as e:
            self.applog.exception('Exception --> logged_in()', exc_info=e)
            return False

    async def handle_username_prompt(self):
        """
        Handle username prompt in login sequence

        Raises:
            Exception: For generic failures
        """
        self.applog.info('sending username %s' % self.username)
        self._flush_buffer()
        self.pexpect_child.sendline(self.username)
        ret = self.pexpect_child.expect(['(?i)password', pexpect.TIMEOUT, pexpect.EOF], timeout=10)
        self.applog.info('handle_username %s ret:%s' % (self.username, ret))
        if ret == 0:
            return await self.handle_password_prompt()
        elif ret == 2:
            self.applog.info('Login username prompt failed with %s' % ret)
        return False

    async def handle_password_prompt(self):
        """
        Handle password prompt in login sequence

        Raises:
            Exception: For generic failures
        """
        self.applog.info('sending password %s' % self.password)
        self._flush_buffer()
        self.pexpect_child.sendline(self.password)
        ret = self.pexpect_child.expect_exact(
            [self.cmd_prompt, pexpect.TIMEOUT, pexpect.EOF], timeout=10
        )
        if ret == 0:
            return True
        self.applog.info('handle_password_prompt failed with %s' % ret)
        return False

    async def _login_routine(self):
        """
        Login routine to handle the login state

        Raises:
            Exception: For generic failures
        """
        self.applog.info('----Starting login----')
        for i in range(self.LOGIN_RETRIES):
            self._flush_buffer()
            self.pexpect_child.sendline('')
            self.applog.info('retrying login: %s' % i)
            ret = self.pexpect_child.expect(
                list(SerialConsole.LoginPexpectHelper.PEXPECT_MAP.values()), timeout=10
            )
            self.applog.info(
                'Login expect: got %s' % SerialConsole.LoginPexpectHelper.PEXPECT_MAP[ret]
            )
            if ret == SerialConsole.LoginPexpectHelper.PASSWORD:
                if await self.handle_password_prompt() and await self.logged_in():
                    return True
            elif ret == SerialConsole.LoginPexpectHelper.LOGIN:
                if await self.handle_username_prompt() and await self.logged_in():
                    return True
            elif ret == SerialConsole.LoginPexpectHelper.CMD_PROMPT:
                self.applog.info('Received command prompt, verify if already logged in')
                if await self.logged_in():
                    return True
            elif ret == SerialConsole.LoginPexpectHelper.EOF:
                self.applog.info('Login failed with EOF')
                return False
            elif (
                ret == SerialConsole.LoginPexpectHelper.ONIE
                or ret == SerialConsole.LoginPexpectHelper.TIMEOUT
            ):
                await asyncio.sleep(30)
            else:
                self.applog.info('Login attempt failed with expect ret:%s. Trying again..' % ret)
            self.applog.info('Login expect ret: %s' % ret)

        self.applog.warning('console login unsuccessful')
        raise TimeoutError('Serial console login to %s timed out' % self.dev)

    async def _login(self):
        """
        Trigger login by starting '_login_routine' in a thread

        Raises:
            Exception: For generic failures
        """
        try:
            self.login_done = False
            self.login_successful = False
            if not self.console:
                self.console = serial.Serial(
                    self.dev,
                    baudrate=int(self.baudrate),
                    parity='N',
                    stopbits=1,
                    bytesize=8,
                    timeout=8,
                )
            if not self.pexpect_child:
                self.pexpect_child = pexpect.fdpexpect.fdspawn(
                    self.console.fileno(), encoding='utf-8'
                )
                self.pexpect_child.logfile = self.log_file
            self.connect_future = asyncio.run_coroutine_threadsafe(self._login_routine(), self.loop)
            self.connect_future.add_done_callback(self.login_cb)
            while not self.login_done:
                await asyncio.sleep(2)
            if not self.login_successful:
                raise RuntimeError(f'Unable to login to {self.dev}')
        except Exception as e:
            self.applog.exception('Exception occured --> __login', exc_info=e)
            raise

    def _flush_buffer(self):
        """
        Flush serial console buffer

        Raises:
            Exception: For generic failures
        """
        self.pexpect_child.logfile = None
        flushedStuff = ''
        while self.pexpect_child.expect([pexpect.TIMEOUT, r'.+'], timeout=1):
            flushedStuff += self.pexpect_child.match.group(0)
        self.pexpect_child.logfile = self.log_file

    def parse_cmd_output(self, cmd_out):
        """
        Parse output of command from stdout of serial console

        Return:
            Command output
        """
        output_lines = cmd_out.splitlines()
        res = output_lines[1].strip() if output_lines else ''
        return res

    async def _run_cmd(self, cmd, timeout=5):
        """
        Run command (internal method)

        Raises:
            Exception: For generic failures

        Return:
            exit_status, stdout of command execution
        """
        try:
            self._flush_buffer()
            self.pexpect_child.sendline(cmd)
            ret = self.pexpect_child.expect_exact(
                [self.cmd_prompt, pexpect.TIMEOUT], timeout=timeout
            )
            stdout = self.parse_cmd_output(self.pexpect_child.before) if ret == 0 else ''
            self.pexpect_child.sendline('echo $?')
            ret = self.pexpect_child.expect_exact(
                [self.cmd_prompt, pexpect.TIMEOUT], timeout=timeout
            )
            exit_status = self.parse_cmd_output(self.pexpect_child.before) if ret == 0 else -1
            try:
                exit_status = int(exit_status)
            except ValueError:
                exit_status = -1
            return exit_status, stdout
        except Exception as e:
            self.applog.exception('Exception occured --> _run_command', exc_info=e)
            raise

    async def run_cmd(self, cmd, timeout=5):
        """
        Run command API - Login (if needed) and run_cmd

        Raises:
            Exception: For generic failures

        Return:
            exit_status, stdout of command execution
        """
        try:
            if not await self.logged_in():
                self.applog.info(f'Logging in to console')
                await self._login()
            self.applog.info(f'Executing command {cmd}')
            return await self._run_cmd(cmd, timeout)
        except Exception as e:
            self.applog.exception('Exception occured --> run_command', exc_info=e)
            raise

    def cleanup(self):
        """
        Cleanup - Cleanup routine, disconnect and terminate login threads

        Raises:
            Exception: For generic failures
        """
        try:
            self.disconnect()
            self.log_file.close()
            SerialAsyncLoop.stop_loop(self.logger)
        except Exception as e:
            self.applog.exception(f'Exception --> {SerialConsole.cleanup.__qualname__}', exc_info=e)
            raise

    def disconnect(self):
        """
        Disconnect serial connection

        Raises:
            Exception: For generic failures
        """
        try:
            if self.console:
                self.applog.debug('Disconnecting serial connection')
                self.console.close()
                self.console = self.pexpect_child.logfile = self.pexpect_child = None
                self.applog.debug('Serial connection disconnected')
            else:
                self.applog.debug('No active connection to disconnect')
        except Exception as e:
            self.applog.exception('Exception --> serial disconnect:', exc_info=e)
            raise
