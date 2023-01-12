# Testbed package for testing dent devices.

The package is intended to do the following

- Initialize the testbed
- Install Dent OS on the devices in the testbed
- Trigger tests
- Aggregates the results from the tests

### Install
Test framework install using the pip tool
```
pip3 install -r Requirements.txt
pip3 install .

pip install netmiko
pip install paramiko
```

### Usage
```
usage: dentos_testbed_runtests [-h] [-c CONFIG]
                               [--suite-groups [suite group [suite group ...]]]
                               [-d] [--discovery-path DISCOVERY_PATH]
                               [-l {1,2,3,4,5}] [--stdout]
                               [--test-output-dest TEST_OUTPUT_DEST]

Trigger for initiating test framework for DENT networking switches

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        json file containing list of DUTs
  --suite-groups [suite group [suite group ...]]
                        List of suite groups to run in given order
  -d, --discovery       Boolean to trigger discovery package
  --discovery-path DISCOVERY_PATH
                        File path to obtain already existing discovery
                        results. This argument cannot be used with -d
  -l {1,2,3,4,5}, --log-level {1,2,3,4,5}
                        Log level is numerical and as follows. Default being
                        INFO (1:Critical, 2:Error, 3:Warn, 4:Info, 5:Debug)
  --stdout              Enable print statements to be output to stdout while
                        test framework execution
  --test-output-dest TEST_OUTPUT_DEST
                        Desination to copy test output folder. Default is
                        folder called "test_output" in currentdirectory
```

Sample run on DENT lab

```
dentos_testbed_runtests -d --stdout --config configuration/testbed_config/basic/testbed.json --config-dir configuration/testbed_config/basic/ --suite-groups suite_group_cleanup --discovery-reports-dir ./reports --discovery-path ../DentOsTestbedLib/src/dent_os_testbed/discovery/modules/
```

### Organizing test cases
- Tests can be organized into scopes of functions, classes, modules and packages.
- Inside the test folder, its recommended to organize the test code in following file hierarchy.
```
src/dent_os_testbed/test/test_suite
	conftest.py

	connection/
  	connection_fixtures.py
  	test_ssh.py
  	test_console.py
	platform/
  	platform_fixtures.py
  	test_plat1.py
  	test_plat2.py
	l3_tests/
		l3_fixtures.py
		test_ip_route.py
		test_iptables.py
	l2_tests/
```
 - Note  that every test case written needs to be either prefixed or suffixed with `test` since PyTest collects test cases based on the naming.
 - Fixtures are a good way to write setup, cleanup, data injections, parameterizing, db provider etc.
 - Global fixtures can be provided in conftest.py
 - Package or module level fixtures can be defined in respective folders as shown above. But need to be registered in conftest.py as shown below.
   `pytest_plugins = ["dent_os_testbed.test.connection.fixtures"]`
 - Fixtures can also be written per test case level where fixture functions have to be decorated with `@pytest.fixture`
 - Usage of any pytest hooks of fixtures need to be placed in `conftest.py`
   Refer for pytest in-built plugins, fixtures and hooks: https://docs.pytest.org/en/stable/reference.html

### Test suite and suite groups
- For this framework, we are organizing test cases into `suite` and `suite group`
- Test cases are mapped to test suites. Test suites are mapped to test suite groups.
- Mapping test cases to suite is done through using custom PyTest markers.
- test suite names need to be prefixed with `suite_` and suite group names need `suite_group_` prefix.
- We can define custom markers at different scopes. ie function, class and module.

```
func level
----------
@pytest.mark.suite_test
def test_func():

class level
-----------
class TestClass:
    pytestmark = pytest.mark.suite_test

module level (test_sample.py)
------------
import pytest
pytestmark = [pytest.mark.suite_test]
```

- test case can belong to multiple suites.
- test suite and mapping from test suite to test suite group needs to be defined in `src/dent_os_testbed/constants.py`

```
PYTEST_SUITES = {
    "suite_test": "Test marker",
    "suite_unittest": "Example suite for writing unit test cases which are run during bb",
    "suite_feature_f1": "Test marker for feature f1",
    "suite_feature_f2": "Test marker for feature f1",
    "suite_connection": "Marker for suite related to connection APIs like ssh, serial",
}

PYTEST_SUITE_GROUPS = {
    "suite_group_test": ["suite_test", "suite_feature_f1", "suite_feature_f2"],
    "suite_group_connection": ["suite_connection"],
}
```


### Location for writing tests
- For tests that we want to run with "bb test" needs to be in "unit_tests" folder.
- For tests that are part of test framework needs to be packaged with the build. So they should be part of "src/dent_os_testbed/test" folder.

## Reporting
- Logs, test framework summary, html reports will be output to folder `test_output/dent_test_result_MM_DD_YYYY_THH_mm_SS` and will have following sample file hierarchy
```
device_files/
	oob1/
		ssh.log
		console.log
		..
		..
	oob2/
	infra1/
	..
	..
discovery-report.json
report_suite_group_connection.html
report_suite_group_l3_tests.html
report_suite_group_test.html
test_stdout.log
test_summary.log
testbed.log
testbed_args
testbed_config.json
```
