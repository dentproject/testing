import asyncio
import os

import pytest

from dent_os_testbed.utils.ConnectionHandlers.SSHHandler import SSHConnectionGroup
from dent_os_testbed.utils.FileHandlers.FileHandlerFactory import (
    FileHandlerFactory,
    FileHandlerTypes,
)
from dent_os_testbed.utils.logging.LoggerUtil import LoggerUtil

pytestmark = pytest.mark.suite_connection


class SSHTester:

    __instance = None
    local_file = '/tmp/ssh_test'
    local_file_content = 'this is a test file'

    @staticmethod
    def get_instance():
        if not SSHTester.__instance:
            SSHTester()
        return SSHTester.__instance

    def __init__(self):
        self.testbed = pytest.testbed
        device_params = [
            (device, {'idx': idx, 'remote_file': 'test%s.txt' % idx})
            for idx, device in enumerate(self.testbed.devices)
        ]
        self.ssh_group = SSHConnectionGroup(device_params)
        self.ssh_group.connect()
        SSHTester.__instance = self
        self.logger = LoggerUtil.get_default_logger().getChild('test_ssh')

    def get_testbed(self):
        return self.testbed

    @staticmethod
    def get_logger():
        return SSHTester.get_instance().logger

    def is_connected(self):
        tester = SSHTester.__instance
        for conn in tester.ssh_group.conns:
            if not (conn.client and conn.is_connected):
                print('SSH connection to %s not successful' % conn.device.host_name)
                return False
        return True


def ssh_cleanup():
    logger = SSHTester.get_logger()
    try:
        os.unlink(SSHTester.local_file)
    except:
        logger.exception()
        assert False


@pytest.fixture
def ssh_setup(request):
    logger = SSHTester.get_logger()
    try:
        with open(SSHTester.local_file, 'w') as fh:
            fh.write(SSHTester.local_file_content)
    except:
        logger.exception()
        assert False
    request.addfinalizer(ssh_cleanup)


def test_ssh_connect(ssh_setup):
    logger = SSHTester.get_logger()
    tester = SSHTester.get_instance()
    testbed = tester.get_testbed()
    assert len(testbed.devices)
    ssh_conn = testbed.devices[0].conn_mgr.get_ssh_connection()
    ssh_conn.connect()

    assert ssh_conn.is_connected()
    logger.info('test_ssh_connect complete')


def test_ssh_run_command(ssh_setup):
    logger = SSHTester.get_logger()
    tester = SSHTester.get_instance()
    testbed = tester.get_testbed()
    assert len(testbed.devices)
    device = testbed.devices[0]
    ssh_conn = device.conn_mgr.get_ssh_connection()
    ssh_conn.connect()

    result = ssh_conn.run_command('whoami')
    assert (
        result
        and not result.exit_status
        and result.stdout.strip() == device.login.get('userName', '')
    )
    logger.info('tst_ssh_run_command complete')


def test_ssh_copy_local_to_remote(ssh_setup):
    logger = SSHTester.get_logger()
    tester = SSHTester.get_instance()
    testbed = tester.get_testbed()
    assert len(testbed.devices)
    device = testbed.devices[0]
    ssh_conn = device.conn_mgr.get_ssh_connection()
    ssh_conn.connect()

    remote_file_name = '/tmp/ssh_test.txt'
    ssh_conn.copy_local_to_remote(SSHTester.local_file, remote_file_name)
    result = ssh_conn.run_command('cat %s' % remote_file_name)
    assert (
        result and not result.exit_status and result.stdout.strip() == SSHTester.local_file_content
    )
    ssh_conn.run_command('rm %s' % remote_file_name)
    logger.info('test_ssh_copy_local_to_remote complete')


def test_ssh_copy_remote_to_local(ssh_setup):
    logger = SSHTester.get_logger()
    tester = SSHTester.get_instance()
    testbed = tester.get_testbed()
    assert len(testbed.devices)
    device = testbed.devices[0]
    ssh_conn = device.conn_mgr.get_ssh_connection()
    ssh_conn.connect()

    remote_file_name = '/tmp/ssh_test.txt'
    ssh_conn.copy_local_to_remote(SSHTester.local_file, remote_file_name)
    result = ssh_conn.run_command('cat %s' % remote_file_name)
    assert (
        result and not result.exit_status and result.stdout.strip() == SSHTester.local_file_content
    )

    local_file_name = '/tmp/scp_local.txt'
    ssh_conn.copy_remote_to_local(remote_file_name, local_file_name)
    local_file_handler = FileHandlerFactory.get_file_handler(FileHandlerTypes.LOCAL)
    local_file_str = local_file_handler.read(local_file_name)
    assert local_file_str.strip() == SSHTester.local_file_content
    os.system('rm %s' % local_file_name)

    ssh_conn.run_command('rm %s' % remote_file_name)
    logger.info('test_ssh_copy_remote_to_local complete')


@pytest.fixture
def ssh_disconnect():
    tester = SSHTester.get_instance()
    testbed = tester.get_testbed()
    assert len(testbed.devices)
    ssh_conn = testbed.devices[0].conn_mgr.get_ssh_connection()
    ssh_conn.disconnect()


@pytest.mark.parametrize(
    'auth',
    [
        {'userName': 'test', 'password': 'test'},
        {'userName': 'root', 'password': 'password'},
        {'userName': 'testroot', 'password': 'onl'},
        {'userName': 'root'},
        {'password': 'onl'},
        {},
    ],
)
def test_ssh_auth_fail(monkeypatch, ssh_disconnect, auth):
    tester = SSHTester.get_instance()
    testbed = tester.get_testbed()
    assert len(testbed.devices)
    device = testbed.devices[0]
    monkeypatch.setattr(device, 'login', auth, raising=True)
    ssh_conn = testbed.devices[0].conn_mgr.get_ssh_connection()
    with pytest.raises(Exception) as login_exc:
        ssh_conn.connect()
    # print("login_exc:%s" % str(login_exc.value))
    assert 'Invalid SSH credentials' in str(login_exc.value) or 'Permission denied' in str(
        login_exc.value
    )


@pytest.mark.parametrize('host_ip', ['1.2.3.4', '5.6.7.8'])
def test_unreachable_host(monkeypatch, ssh_disconnect, host_ip):
    tester = SSHTester.get_instance()
    testbed = tester.get_testbed()
    assert len(testbed.devices)
    device = testbed.devices[0]
    monkeypatch.setattr(device, 'ip', host_ip, raising=True)
    ssh_conn = testbed.devices[0].conn_mgr.get_ssh_connection()
    with pytest.raises(Exception) as login_exc:
        ssh_conn.connect()
    assert login_exc.type is asyncio.TimeoutError


def test_ssh_group_connect(ssh_setup):
    tester = SSHTester.get_instance()
    assert tester.is_connected()


def test_ssh_group_run_command(ssh_setup):
    tester = SSHTester.get_instance()
    assert tester.is_connected()
    result = tester.ssh_group.run_command('whoami')
    for i, r in enumerate(result):
        assert (
            r
            and not r.exit_status
            and r.stdout.strip() == tester.ssh_group.conns[i].device.login.get('userName', '')
        )


def test_ssh_group_copy_local_to_remote(ssh_setup):
    tester = SSHTester.get_instance()
    assert tester.is_connected()
    # copy the file to remote
    tester.ssh_group.copy_local_to_remote(
        SSHTester.local_file, '/tmp/%s', dst_params=['remote_file']
    )
    # verify remote file contents
    result = tester.ssh_group.run_command('cat /tmp/%s', cmd_params=['remote_file'])
    for r in result:
        assert r and not r.exit_status and r.stdout.strip() == SSHTester.local_file_content
    result = tester.ssh_group.run_command('rm /tmp/%s', cmd_params=['remote_file'])


def test_ssh_group_copy_remote_to_local(ssh_setup):
    tester = SSHTester.get_instance()
    assert tester.is_connected()
    # First copy the file to remote
    tester.ssh_group.copy_local_to_remote(
        SSHTester.local_file, '/tmp/%s', dst_params=['remote_file']
    )
    result = tester.ssh_group.run_command('cat /tmp/%s', cmd_params=['remote_file'])
    for r in result:
        assert r and not r.exit_status and r.stdout.strip() == SSHTester.local_file_content

    # Now copy the file back to local
    tester.ssh_group.copy_remote_to_local(
        '/tmp/%s', '/tmp/local_test%s', dst_params=['remote_file'], src_params=['idx']
    )
    local_file_handler = FileHandlerFactory.get_file_handler(FileHandlerTypes.LOCAL)
    for i in range(len(tester.testbed.devices)):
        local_file_str = local_file_handler.read('/tmp/local_test%s' % i)
        # print("local_file %s: %s" % (i, local_file_str))
        assert local_file_str.strip() == SSHTester.local_file_content
        os.system('rm /tmp/local_test%s' % i)

    # delete tmp file on remote
    result = tester.ssh_group.run_command('rm /tmp/%s', cmd_params=['remote_file'])
