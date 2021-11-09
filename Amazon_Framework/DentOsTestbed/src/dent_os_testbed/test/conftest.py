import os
import tempfile

import pytest

from dent_os_testbed.constants import DEFAULT_LOGGER, LOGDIR, PYTEST_SUITES
from dent_os_testbed.logger.Logger import AppLogger
from dent_os_testbed.utils.FileHandlers.FileHandlerFactory import (
    FileHandlerFactory,
    FileHandlerTypes,
)

# Add python files for defining per folder fixtures here
# And depending on the scope of fixtures, they can be used
# in other modules if scope is session
pytest_plugins = ["dent_os_testbed.test.connection.fixtures"]


# pytest_sessionstart and pytest_sessionfinish
# functions can be used as global setup and cleanup functions


@pytest.hookimpl(trylast=True)
def pytest_configure(config):

    # dynamically add custom markers defined in dent_os_testbed.__init__
    for suite_name, suite_desc in PYTEST_SUITES.items():
        config.addinivalue_line("markers", "%s: %s" % (suite_name, suite_desc))

    tr = config.pluginmanager.getplugin("terminalreporter")
    if tr:
        config._pytestsessionfile = tempfile.TemporaryFile("w+")
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
    if hasattr(config, "_pytestsessionfile"):
        # get terminal contents and delete file
        config._pytestsessionfile.seek(0)
        sessionlog = config._pytestsessionfile.read()
        config._pytestsessionfile.close()
        # write summary
        test_summary_file = os.path.join(LOGDIR, "test_summary.log")
        lfh = FileHandlerFactory.get_file_handler(FileHandlerTypes.LOCAL, logger)
        lfh.write(test_summary_file, sessionlog)

    # Save and parameters for each suite run


def pytest_runtest_setup(item):
    logger = AppLogger(DEFAULT_LOGGER)
    if logger:
        logger = logger.getChild("conftest")
        logger.info("=================================================================")
        logger.info(
            '<a href="#%s">Starting testcase:%s from file:%s </a>'
            % (item.name, item.name, item.fspath)
        )
        logger.info("=================================================================")


def pytest_runtest_teardown(item, nextitem):
    logger = AppLogger(DEFAULT_LOGGER)
    if logger:
        logger = logger.getChild("conftest")
        logger.info("Finished testcase:%s from file:%s" % (item.name, item.fspath))


def pytest_sessionstart(session):
    if hasattr(pytest, "testbed"):
        pytest.stdout_logger = AppLogger("test_stdout")
    else:
        pytest.stdout_logger = None


def pytest_sessionfinish(session):
    pass


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    pass


def pytest_runtest_logreport(report):
    report_str = "Test: %s stdout:%s\n\n" % (report.nodeid, report.capstdout)
    if hasattr(pytest, "stdout_logger") and pytest.stdout_logger:
        pytest.stdout_logger.info(report_str)


def pytest_collection_modifyitems(session, config, items):
    logger = AppLogger(DEFAULT_LOGGER)
    if logger:
        logger = logger.getChild("conftest")
    for item in items:
        for mark in item.own_markers:
            if mark and mark.name.startswith("feature"):
                if logger:
                    logger.info("pytest %s has feature markers:%s" % (item.name, item.own_markers))
    return False


@pytest.fixture(scope="session")
def testbed():
    return pytest.testbed


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    test_fn = item.obj
    docstring = getattr(test_fn, "__doc__")
    if docstring:
        print (docstring)
