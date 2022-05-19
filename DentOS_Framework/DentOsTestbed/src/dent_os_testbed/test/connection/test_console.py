import time

import pytest

pytestmark = pytest.mark.suite_connection


def test_serial_run_command(serial_setup):
    testbed = pytest.testbed
    assert len(testbed.devices)
    device = testbed.devices[0]
    serial_console = device.conn_mgr.get_serial_connection()
    login_done, login_successful = serial_console.login_info()
    assert login_done and login_successful
    output = serial_console.run_command("uname -a", timeout=2)
    assert output.lower().find("linux") != -1


def test_serial_get_console_log(serial_setup):
    testbed = pytest.testbed
    assert len(testbed.devices)
    device = testbed.devices[0]
    serial_console = device.conn_mgr.get_serial_connection()
    console_log = serial_console.get_console_buffer(clear=False)
    assert len(console_log)


@pytest.fixture
def serial_setup():
    testbed = pytest.testbed
    assert len(testbed.devices)
    device = testbed.devices[0]
    serial_console = device.conn_mgr.get_serial_connection()
    retry = 0
    login_done, login_successful = False, False
    while not login_done:
        login_done, login_successful = serial_console.login_info()
        print(
            "WAIT for LOGIN: %s login_done: %s login_successful:%s"
            % (retry, login_done, login_successful)
        )
        retry += 1
        if retry > 40:
            break
        time.sleep(5)
    assert login_done and login_successful
