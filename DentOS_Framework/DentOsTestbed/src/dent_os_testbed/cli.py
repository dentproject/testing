""" Implements the Command Line Interface(CLI) for the testbed
"""

import argparse
import asyncio
import os
import traceback

import pytest

from dent_os_testbed.constants import (
    LOGDIR,
    OS_IMAGE_DOWNLOAD_URL,
    PYTEST_SUITE_GROUPS,
    TEST_OUTPUT_FOLDER,
    TESTBED_CONFIG_FILE_NAME,
)
from dent_os_testbed.Device import DeviceType
from dent_os_testbed.discovery.constants import REPORTS_DIR
from dent_os_testbed.logger.Logger import AppLogger
from dent_os_testbed.TestBed import TestBed
from dent_os_testbed.utils.test_utils.tb_utils import tb_collect_logs_from_devices
from dent_os_testbed.utils.Utils import check_asyncio_results


def get_args():
    """
    Parse command line arguments

    Raises:
        SystemExit: If argument parsing failed
    """
    parser = argparse.ArgumentParser(
        description="Trigger for initiating test framework " "for DENT networking switches"
    )
    parser.add_argument(
        "-c",
        "--config",
        help="json file containing list of DUTs",
        default=TESTBED_CONFIG_FILE_NAME,
    )
    parser.add_argument(
        "--suite-groups",
        help=(
            "List of suite groups to run in given order. Available options: %s"
            % list(PYTEST_SUITE_GROUPS.keys())
        ),
        metavar="suite group",
        nargs="*",
    )
    parser.add_argument(
        "-d",
        "--discovery-force",
        help="Boolean to trigger discovery package",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--discovery-path",
        help="Set the discovery modules path",
        type=str,
    )
    parser.add_argument(
        "--discovery-reports-dir",
        help="Directory path to obtain locate and save discovery results",
        type=str,
        default=REPORTS_DIR,
    )
    parser.add_argument(
        "--discovery-operator",
        help="Set the discovery operator",
        type=str,
    )
    parser.add_argument(
        "--discovery-topology",
        help="Set the discovery topology",
        type=str,
    )
    parser.add_argument(
        "-l",
        "--log-level",
        help="Log level is numerical and as follows. "
        "Default being INFO (1:Critical, 2:Error, 3:Warn, 4:Info, 5:Debug)",
        type=int,
        default=4,
        choices=range(1, 6),
    )
    parser.add_argument(
        "--stdout",
        help="Enable print statements to be output to stdout while " "test framework execution",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--test-output-dest",
        help=(
            'Desination to copy test output folder. Default is folder called "%s" in current'
            "directory" % (TEST_OUTPUT_FOLDER)
        ),
        default=TEST_OUTPUT_FOLDER,
    )
    parser.add_argument(
        "--upgrade-os-image",
        dest="os_image_download_url",
        help=(
            "If provided, Testbed init will also upgrade the OS image of switch based on the "
            "image provided in --config file"
        ),
        default=None,
    )
    parser.add_argument(
        "--use-pssh",
        help=("use_pssh"),
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--aws-region",
        help="AWS Region",
        type=str,
    )
    parser.add_argument(
        "--store-domain",
        help="Store Domain",
        type=str,
    )
    parser.add_argument(
        "--store-type",
        help="Store type",
        type=str,
    )
    parser.add_argument(
        "--store-id",
        help="Store ID",
        type=str,
    )
    parser.add_argument(
        "--config-dir",
        help="Directory path to config file for the testbed",
        type=str,
    )
    parser.add_argument(
        "-k",
        "--suite-tests",
        help="Test case name pattern to run",
        type=str,
    )
    parser.add_argument(
        "--notify-testbed",
        help="Update the DUT login banner about the test that is running",
        type=str,
    )
    parser.add_argument(
        "--discover-links",
        help="Update links information in devices using discovery results",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--is-provisioned",
        help="flag to indicate the setup is provisioned",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--collect-logs",
        help="collect the logs at the end of the test",
        action="store_true",
        default=False,
    )
    args = parser.parse_args()
    return args


def validate_args(args):
    """
    Validate command line arguments

    Args:
        args: Command line arguments

    Raises:
        ArgumentTypeError: If argument is invalid
    """
    if args.discovery_reports_dir:
        if not os.path.isdir(args.discovery_reports_dir):
            msg = (
                "--discovery-reports-dir: Given path %s does not exist" % args.discovery_reports_dir
            )
            raise argparse.ArgumentTypeError(msg)
    if args.discover_links:
        # TODO: Add an option to pass in discovery report and update links
        if not args.discovery_force:
            msg = "--discover-links: Discovery is not enabled"
            raise argparse.ArgumentTypeError(msg)
    if args.config_dir:
        if not os.path.isdir(args.config_dir):
            msg = "--config-dir: Given path %s does not exist" % args.config_dir
            raise argparse.ArgumentTypeError(msg)
    if args.config and not os.path.exists(args.config):
        raise argparse.ArgumentTypeError("--config: Given path does not exist")
    if args.suite_groups:
        for sc in args.suite_groups:
            if sc not in PYTEST_SUITE_GROUPS:
                raise argparse.ArgumentTypeError(
                    "suite group %s is not valid. "
                    "Valid suite groups:%s" % (sc, list(PYTEST_SUITE_GROUPS.keys()))
                )
    if args.use_pssh:
        if (
            args.aws_region is None
            or args.store_domain is None
            or args.store_type is None
            or args.store_id is None
        ):
            msg = f"Need to specify --aws-region --store-domain --store-type --store-id"
            raise argparse.ArgumentTypeError(msg)
    pytest._args = args


def main():
    """
    Main method for testbed. sets up testbed and runs tests

    Raises:
        ArgumentTypeError: If argument is invalid
        Exception: Generic errors
    """
    try:
        args = get_args()
        validate_args(args)
        applog = AppLogger(name="DENT")
        loop = asyncio.get_event_loop()
        pytest.testbed = TestBed(applog, loop, args)
        loop.run_until_complete(setup(args, applog))
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            testbed_update_login_banner(pytest.testbed.devices, args, applog, add=True)
        )
        run_tests(args, applog)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            testbed_update_login_banner(pytest.testbed.devices, args, applog, add=False)
        )
        if args.collect_logs:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(
                tb_collect_logs_from_devices(pytest.testbed.devices)
            )

    except argparse.ArgumentTypeError as e:
        print("Invalid arguments. Err: %s" % str(e))
    except Exception as e:
        print("Error occured in testbed. Err: %s" % str(e))
        traceback.print_exc()
    finally:
        if pytest and hasattr(pytest, "testbed") and pytest.testbed:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(pytest.testbed.cleanup())


async def setup(args, applog):
    """
    Set up testbed, installs OS on testbed devices and performs discovery

    Args:
        args: Command line arguments
        applog (logger.AppLogger): Logger instance

    Raises:
        Exception: Generic errors
    """
    try:
        if args.os_image_download_url is not None:
            await pytest.testbed.install_os()
        if args.discovery_force:
            await pytest.testbed.discover()
            if args.discover_links:
                await pytest.testbed.update_links()
    except Exception as e:
        applog.exception("Error in testbed setup", exc_info=e)
        raise


async def testbed_update_login_banner(devices, args, applog, add):
    """
    Updates the login banner to indicate the test under progress

    Args:
        args: Command line arguments
        applog (logger.AppLogger): Logger instance

    Raises:
        Exception: Generic errors
    """
    if args.notify_testbed is None:
        # setup the login prompt to reflect the current test under progress
        return

    async def _update_device_login_banner(device, string, applog, add):
        wall_message = "*" * 40 + f"\n{string}\n" + "*" * 40 + "\n"
        message = 'echo "' + "*" * 40 + f'"\necho "{string}"\necho "' + "*" * 40 + '"\n'
        file = "/etc/update-motd.d/20-testing"
        commands = {
            True: [
                f"echo '#!/bin/sh\n {message} \n' | sudo tee {file}",
                f"chmod 755 {file}",
                f"wall '{wall_message}' START",
            ],
            False: [
                f"rm {file}",
                f"wall '{wall_message}' END",
            ],
        }
        for cmd in commands[add]:
            rc, out = await device.run_cmd(cmd, sudo=True)

    cos = []
    for d in devices:
        if d.type == DeviceType.TRAFFIC_GENERATOR:
            continue
        if not await d.is_connected():
            continue
        cos.append(_update_device_login_banner(d, args.notify_testbed, applog, add))
    results = await asyncio.gather(*cos, return_exceptions=False)
    try:
        check_asyncio_results(results, "_update_device_login_banner")
    except Exception as e:
        applog.info("Done updating banner")


def run_tests(args, applog):
    """
    Executes the test suite

    Args:
        args: Command line arguments
        applog (logger.AppLogger): Logger instance

    Raises:
        Exception: Generic errors
    """
    try:
        additional_args = []
        additional_args.extend(["--pyargs", "dent_os_testbed.test.test_suite", "--strict-markers"])
        additional_args.append("--durations=0")
        if args.stdout:
            additional_args.append("--capture=tee-sys")

        suite_groups = args.suite_groups if args.suite_groups else PYTEST_SUITE_GROUPS.keys()
        for sg_name in suite_groups:
            sg = PYTEST_SUITE_GROUPS[sg_name]
            pytest_args = []
            if not sg:
                continue
            pytest._current_suite = sg_name
            pytest_args.append("-m")
            markers_string = sg[0] + "".join([(" or %s" % suite) for suite in sg[1:]])
            pytest_args.append(markers_string)
            pytest_args.append("--html=%s/report_%s.html" % (LOGDIR, sg_name))
            pytest_args.append("--junitxml=%s/junit_%s.xml" % (LOGDIR, sg_name))
            pytest_args.append("--self-contained-html")
            if args.suite_tests:
                pytest_args.append("-k")
                pytest_args.append(args.suite_tests)
            input_args = additional_args + pytest_args
            applog.info("Triggering pytest with args : %s" % input_args)
            pytest.main(input_args)
    except Exception as e:
        applog.exception("Error running tests", exc_info=e)
        raise


if __name__ == "__main__":
    main()
