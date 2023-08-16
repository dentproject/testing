# Utility Usage

This folder holds tools for use with dentOS testing.

## Test Utils

`test_utils.py` is a test utility that interacts with pytest XMLs to aggregate, sort, and export data across XMLs.

Available usage modes are:

- `list` : show basic results from all test suites
  - can use `-s` flag to sort listby passes, fails, etc.
- `tree` : show results as a tree grouped by subtype
- `html` : export test results as a markdown-compatible html table
- `csv` : export test results as a csv
- `run_fails` : generate commands to rerun all failed tests

### Usage

`./test_utils.py {MODE} -d {XML Directory}`

### Examples

Listing test suite results sorted by number passed

`./test_utils.py list -d ../DentOS_Framework/DentOsTestbed/logs -s p`

Exporting test data to a csv file

`./test_utils.py csv -d ../DentOS_Framework/DentOsTestbed/logs > test.csv`
