import asyncio
import os
import tempfile

import pytest
import pytest_asyncio

from dent_os_testbed.constants import DEFAULT_LOGGER, LOGDIR, PYTEST_SUITES
from dent_os_testbed.logger.Logger import AppLogger
from dent_os_testbed.utils.FileHandlers.FileHandlerFactory import (
    FileHandlerFactory,
    FileHandlerTypes,
)
from dent_os_testbed.utils.test_utils.tb_utils import tb_get_all_devices
from dent_os_testbed.utils.test_utils.cleanup_utils import (
    cleanup_ip_addrs as _cleanup_ip_addrs,
    cleanup_bridges as _cleanup_bridges,
    cleanup_qdiscs as _cleanup_qdiscs,
    cleanup_routes as _cleanup_routes,
    cleanup_bonds as _cleanup_bonds,
    cleanup_vrfs as _cleanup_vrfs,
    cleanup_sysctl as _cleanup_sysctl,
    get_initial_routes,
)
from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_stop_traffic,
)

# Add python files for defining per folder fixtures here
# And depending on the scope of fixtures, they can be used
# in other modules if scope is session
pytest_plugins = ['dent_os_testbed.test.connection.fixtures']


# pytest_sessionstart and pytest_sessionfinish
# functions can be used as global setup and cleanup functions


@pytest.hookimpl(trylast=True)
def pytest_configure(config):

    # dynamically add custom markers defined in dent_os_testbed.__init__
    for suite_name, suite_desc in PYTEST_SUITES.items():
        config.addinivalue_line('markers', '%s: %s' % (suite_name, suite_desc))

    tr = config.pluginmanager.getplugin('terminalreporter')
    if tr:
        config._pytestsessionfile = tempfile.TemporaryFile('w+')
        oldwrite = tr._tw.write

        def tee_write(s, **kwargs):
            oldwrite(s, **kwargs)
            config._pytestsessionfile.write(s)

        tr._tw.write = tee_write


# def pytest_html_report_title(report):
#    report.title = "Suite: %s" % pytest._current_suite


def pytest_unconfigure(config):
    # Log all the output from pytest to test_summary.log
    logger = AppLogger(DEFAULT_LOGGER)
    if hasattr(config, '_pytestsessionfile'):
        # get terminal contents and delete file
        config._pytestsessionfile.seek(0)
        sessionlog = config._pytestsessionfile.read()
        config._pytestsessionfile.close()
        # write summary
        test_summary_file = os.path.join(LOGDIR, 'test_summary.log')
        lfh = FileHandlerFactory.get_file_handler(FileHandlerTypes.LOCAL, logger)
        lfh.write(test_summary_file, sessionlog)

    # Save and parameters for each suite run


def pytest_runtest_setup(item):
    logger = AppLogger(DEFAULT_LOGGER)
    if logger:
        logger = logger.getChild('conftest')
        logger.info('=================================================================')
        logger.info(
            '<a href="#%s">Starting testcase:%s from file:%s </a>'
            % (item.name, item.name, item.fspath)
        )
        logger.info('=================================================================')


def pytest_runtest_teardown(item, nextitem):
    logger = AppLogger(DEFAULT_LOGGER)
    if logger:
        logger = logger.getChild('conftest')
        logger.info('Finished testcase:%s from file:%s' % (item.name, item.fspath))


def pytest_sessionstart(session):
    if hasattr(pytest, 'testbed'):
        pytest.stdout_logger = AppLogger('test_stdout')
    else:
        pytest.stdout_logger = None


def pytest_sessionfinish(session):
    pass


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    pass


def pytest_runtest_logreport(report):
    report_str = 'Test: %s stdout:%s\n\n' % (report.nodeid, report.capstdout)
    if hasattr(pytest, 'stdout_logger') and pytest.stdout_logger:
        pytest.stdout_logger.info(report_str)


def pytest_collection_modifyitems(session, config, items):
    logger = AppLogger(DEFAULT_LOGGER)
    if logger:
        logger = logger.getChild('conftest')
    for item in items:
        for mark in item.own_markers:
            if mark and mark.name.startswith('feature'):
                if logger:
                    logger.info('pytest %s has feature markers:%s' % (item.name, item.own_markers))
    return False


@pytest.fixture(scope='session')
def testbed():
    return pytest.testbed


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    outcome.get_result()
    test_fn = item.obj
    docstring = getattr(test_fn, '__doc__')
    if docstring:
        print(docstring)


async def _get_dent_devs_from_testbed(testbed):
    devs = await tb_get_all_devices(testbed)
    return devs


@pytest_asyncio.fixture()
async def cleanup_qdiscs(testbed):
    yield
    devices = await _get_dent_devs_from_testbed(testbed)
    qdisc_cleanups = [_cleanup_qdiscs(dev) for dev in devices]
    await asyncio.gather(*qdisc_cleanups)


@pytest_asyncio.fixture
async def cleanup_bridges(testbed):
    yield
    devices = await _get_dent_devs_from_testbed(testbed)
    bridge_cleanups = [_cleanup_bridges(dev) for dev in devices]
    await asyncio.gather(*bridge_cleanups)


@pytest_asyncio.fixture
async def cleanup_vrfs(testbed):
    yield
    devices = await _get_dent_devs_from_testbed(testbed)
    vrf_cleanups = [_cleanup_vrfs(dev) for dev in devices]
    await asyncio.gather(*vrf_cleanups)


@pytest_asyncio.fixture
async def cleanup_ip_addrs(testbed):
    yield
    # get all dent devices regardless of number of tg links
    tgen_dev, devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 0)
    ip_addrs_cleanups = [_cleanup_ip_addrs(dev, tgen_dev) for dev in devices]
    await asyncio.gather(*ip_addrs_cleanups)


@pytest_asyncio.fixture
async def cleanup_tgen(testbed):
    yield
    tgen_dev, _ = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    await tgen_utils_stop_traffic(tgen_dev)


@pytest_asyncio.fixture
async def cleanup_routes(testbed):
    devices = await _get_dent_devs_from_testbed(testbed)
    initial_routes = dict()
    for dev in devices:
        initial_routes[dev.host_name] = await get_initial_routes(dev)
    yield
    routes_cleanups = [_cleanup_routes(dev, initial_routes[dev.host_name]) for dev in devices]
    await asyncio.gather(*routes_cleanups)


@pytest_asyncio.fixture
async def cleanup_sysctl():
    yield
    await _cleanup_sysctl()


@pytest_asyncio.fixture
async def cleanup_bonds(testbed):
    yield
    # get all dent devices regardless of number of tg links
    _, devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 0)
    bonds_cleanup = [_cleanup_bonds(dev) for dev in devices]
    await asyncio.gather(*bonds_cleanup)
