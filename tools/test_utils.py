#!/usr/bin/env python3

from operator import attrgetter
from xml.etree import ElementTree as ET
from treelib import Tree
import argparse
import glob

# Configurables
# How many characters of failure message
MESSAGE_LENGTH = 100
# Command used to run dent tests, minus suite groups
RUN_CMD = (
    'dentos_testbed_runtests -d --stdout'
    ' --config configuration/testbed_config/basic_infra1_vm/testbed.json'
    ' --config-dir configuration/testbed_config/basic_infra1_vm/'
    ' --discovery-reports-dir ./reports'
    ' --discovery-path ../DentOsTestbedLib/src/dent_os_testbed/discovery/modules/ ')


class TestCase:
    '''Individual Test Case Class to find name, status, message'''

    def __init__(self, node: ET.Element):
        self.classname = node.get('classname')
        self.name = node.get('name')
        # Get Status, Empty Node is Pass
        if len(list(node)) == 0:
            self.status = 'pass'
        else:
            self.status = list(node)[0].tag
        # Get Failure Message and Crop
        if self.status == 'failure':
            self.message = list(node)[0].get('message')
            if (len(self.message) > MESSAGE_LENGTH):
                self.message = self.message.replace('\n', '')[:MESSAGE_LENGTH] + '...'
        else:
            self.message = ''

    def table_entry(self):
        return f'<tr><td>{self.name}</td><td>{self.status}</td><td>{self.message}</td></tr>'

    def to_csv(self):
        return f'{self.name},{self.classname.split(".")[0]},{self.classname.split(".")[1]},{self.status},"{self.message}"'

    def __repr__(self):
        return f'<tr><td>{self.name}</td><td>{self.status}</td><td>{self.message}</td></tr>'

    @staticmethod
    def table_header():
        return '<tr><td colspan="6"><details><summary>&emsp;Results</summary>'\
            '<table><tr><th>Test Name</th><th>Status</th><th>Message</th></tr>'

    @staticmethod
    def table_footer():
        return '</table></details></td></tr>'


class TestSuite:
    '''Test Suite Generalized Class for Printing/Adding'''

    def __init__(self, name: str):
        self.name = name
        self.fails = 0
        self.skips = 0
        self.time = 0
        self.errors = 0
        self.tests = 0
        self.passes = 0
        return

    def __add__(self, other):
        ts = TestSuite(self.name)
        ts.fails = self.fails + other.fails
        ts.skips = self.skips + other.skips
        ts.time = self.time + other.time
        ts.errors = self.errors + other.errors
        ts.tests = self.tests + other.tests
        ts.passes = self.passes + other.passes
        return ts

    def __repr__(self) -> str:
        return (f'{self.name :<20}'
                f'{self.tests :>4} ran, {self.passes :>4} passed, {self.fails :>4} failed, '
                f'{self.errors :>4} errors, {self.skips :>4} skipped in {self.time :10.3f} s')

    def table_entry(self):
        return (f'<tr><td>{self.name}</td>'
                f'<td>{self.tests}</td><td>{self.passes}</td> <td>{self.fails}</td>'
                f'<td>{self.errors}</td><td>{self.skips}</td><td>{self.time :.3f}</td></tr>')

    @staticmethod
    def table_header():
        return ('<table style="width:100%"><tr><th>Test Suite Name</th>'
                '<th>Ran</th><th>Passed</th> <th>Failed</th>'
                '<th>Errors</th><th>Skipped</th><th>Time</th></tr>')


class TestSuiteXML(TestSuite):
    '''Test Suite Child Class for Parsing XMLs into Test Suites'''

    def __init__(self, filename: str) -> None:
        # Get name of suite from filepath
        name: str = filename.split('/')[-1].removeprefix('junit_suite_group_').removesuffix('.xml')
        super().__init__(name)
        self.filename: str = filename
        # Parse XML
        root: ET.ElementTree = ET.parse(filename)
        diag: ET.Element = root.find('testsuite')
        # Get data from found testsuite node
        self.fails: int = int(diag.get('failures'))
        self.skips: int = int(diag.get('skipped'))
        self.time: float = float(diag.get('time'))
        self.errors: int = int(diag.get('errors'))
        self.tests: int = int(diag.get('tests')) - self.skips
        # Calculate number of passes from total
        self.passes: int = self.tests - self.fails - self.errors

        # Create list of Test Cases
        self.case_list = [TestCase(node) for node in diag.findall('testcase')]
        self.case_list.sort(key=attrgetter('status'))


def main():
    # Define Possible Operating Modes
    modes = ['tree', 'list', 'html', 'csv', 'run_fails']
    # Define Sort Options
    sort_dict = {'n': 'filename', 'p': 'passes', 'f': 'fails', 's': 'skips', 'r': 'tests', 't': 'time'}

    # Process Args with argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', default='list', choices=modes, help='Operating Mode')
    # Directory of log location
    parser.add_argument('-d', '--dir', default='../DentOS_Framework/DentOsTestbed/logs', help='Specify folder location of log XMLs')
    # Option to sort for list mode
    parser.add_argument('-s', '--sort', choices=sort_dict.keys(), help='Sort By: ' + repr(sort_dict))
    args = parser.parse_args()

    # Get Suites from XML files in src directory
    suites: list[TestSuiteXML] = [TestSuiteXML(filename) for filename in sorted(glob.glob(args.dir + '/*.xml'))]
    # Aggregate data into Total suite
    total_suite: TestSuite = sum(suites, TestSuite('TOTAL'))

    if args.sort is not None:
        sort_key: str = sort_dict[args.sort]
        suites.sort(key=attrgetter(sort_key), reverse=True)

    # Take Appropriate Action
    match args.mode:
        # List out stats of all suites
        case 'list':
            for suite in suites:
                print(suite)
            print(97*'-')
            print(total_suite)
        # Format suite and case data into html table for html/markdown
        case 'html':
            # Print Outer Suite Table
            print(TestSuite.table_header())
            for suite in suites:
                print(suite.table_entry())
                # Print Inner Case Table
                print(TestCase.table_header())
                for case in suite.case_list:
                    print(case.table_entry())
                print(TestCase.table_footer())
            print(total_suite.table_entry)
            print('</table>')

        case 'csv':
            # Add CSV Header
            print('Name,Group,Subgroup,Status,Message')
            for suite in suites:
                for case in suite.case_list:
                    print(case.to_csv())

        # Organize cases by subgroup and print as tree
        case 'tree':
            tree = Tree()
            tree.create_node('Test Groups', 'root')
            for suite in suites:
                tree.create_node(suite.name, suite.name, parent='root')
                subtype_dict = {}
                # Count [Passes, Fails] by subtype
                for case in suite.case_list:
                    subtype = (case.classname or 'None.None').split('.')[1]
                    if subtype not in subtype_dict:
                        subtype_dict[subtype] = [0, 0]
                    subtype_dict[subtype][0] += 1 if case.status == 'pass' else 0
                    subtype_dict[subtype][1] += 1 if case.status == 'failure' else 0
                # Construct tree by suite and subtype, calculate pass %
                for (subtype, subtype_list) in subtype_dict.items():
                    percent = 100 if sum(subtype_list) == 0 else 100*subtype_list[0]/sum(subtype_list)
                    tree.create_node(f'{subtype + ":" : <25} {subtype_list[0] : >3} Pass '
                                     f'{subtype_list[1] : >3} Fail {int(percent) : >3}%',
                                     str(suite)+subtype, parent=suite.name)
            tree.show()

        # Generate command to run all failed tests
        case 'run_fails':
            for suite in suites:
                if suite.fails == 0:
                    continue
                failures = [case.name for case in suite.case_list if case.status == 'failure']
                print(RUN_CMD + f' --suite-groups suite_group_{suite.name}'
                      + f" -k '{' or '.join(failures)}'\n")


if __name__ == '__main__':
    main()
