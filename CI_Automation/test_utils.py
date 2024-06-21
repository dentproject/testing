#!/usr/bin/env python3
import glob
from operator import attrgetter
from xml.etree import ElementTree as ET
from treelib import Tree
import argparse

message_length = 100


def test_result_str(name, ran, passed, failed, errors, skipped, time):
    return (f'{name :<20}' \
            f'{ran :>4} ran, {passed :>4} passed, {failed :>4} failed, '\
            f'{errors :>4} errors, {skipped :>4} skipped in {time :10.3f} s')

def test_result_table_header():
    return (f'<table style="width:100%"><tr><th>Test Suite Name</th>' \
            f'<th>Ran</th><th>Passed</th> <th>Failed</th>'\
            f'<th>Errors</th><th>Skipped</th><th>Time</th></tr>')
def test_result_table(name, ran, passed, failed, errors, skipped, time):
    return (f'<tr><td>{name}</td>' \
            f'<td>{ran}</td><td>{passed}</td> <td>{failed}</td>'\
            f'<td>{errors}</td><td>{skipped}</td><td>{time :.3f}</td></tr>')

class TestCase:
    def __init__(self, node:ET.Element):
        self.node = node
        self.classname = node.get('classname')
        self.name = node.get('name')
        if len(list(self.node)) == 0:
            self.status = 'pass'
        else:
            self.status = list(self.node)[0].tag
        if self.status == 'failure':
            self.message = list(self.node)[0].get('message')
            if (len(self.message) > message_length):
                self.message = self.message.replace('\n','')[:message_length] + '...'
        else:
            self.message = ''
    def to_html(self):
        return f'<tr><td>{self.name}</td><td>{self.status}</td><td>{self.message}</td></tr>'
    def to_csv(self):
        return f'{self.name},{self.classname.split(".")[0]},{self.classname.split(".")[1]},{self.status},"{self.message}"'
    def __repr__(self):
        return f'<tr><td>{self.name}</td><td>{self.status}</td><td>{self.message}</td></tr>'
        # return f"\t{self.status : <7}: {self.name}: {self.message}"

class TestSuiteXML:
    def __init__(self, filename:str) -> None:
        self.filename:str = filename
        root:ET.ElementTree = ET.parse(filename)  # alternatively use ET.fromstring()
        # Find diagnosis by "name" (ICD-10 code)
        diag:ET.Element = root.find('testsuite')
        # Print out some information ("name" and "desc" tags)
        self.fails:int   = int(diag.get('failures'))
        self.skips:int   = int(diag.get('skipped'))
        self.time:float  = float(diag.get('time'))
        self.errors:int  = int(diag.get('errors'))
        self.tests:int   = int(diag.get('tests')) - self.skips
        self.passes:int = self.tests - self.fails - self.errors

        # Update name

        self.filename = self.filename.split('/')[-1]\
                        .removeprefix('junit_suite_group_').removesuffix('.xml')
        #Test Cases
        self.case_list = [TestCase(node) for node in diag.findall('testcase')]
        self.case_list.sort(key=attrgetter('status'))

    def __repr__(self) -> str:
        return test_result_str(self.filename,\
                               self.tests, self.passes, self.fails, self.errors, self.skips, self.time)
    def print_entry(self):
        print(test_result_table(self.filename,\
                               self.tests, self.passes, self.fails, self.errors, self.skips, self.time))
sort_dict = {'n': 'filename', 'p' : 'passes', 'f': 'fails', 's' : 'skips', 'r' : 'tests', 't' : 'time'}

def combine_logs():
    # Process Args
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', default='list', choices=['tree','list','html', 'run_fails','csv'], help='Operating Mode')
    parser.add_argument('-src', default='logs', help='Specify folder location of log XMLs')
    parser.add_argument('-sort', choices=sort_dict.keys(), help = 'Sort By: ' + repr(sort_dict))
    args = parser.parse_args()

    suites:list[TestSuiteXML] = [TestSuiteXML(filename) for filename in sorted(glob.glob(args.src + '/*.xml'))]

    total_tests:int = sum(s.tests for s in suites)
    total_fail:int  = sum(s.fails for s in suites)
    total_skip:int  = sum(s.skips for s in suites)
    total_time:float = sum(s.time for s in suites)
    total_passes: int = sum(s.passes for s in suites)
    total_errors: int = sum(s.errors for s in suites)

    if args.sort != None:
            sort_key:str = sort_dict[args.sort]
            suites.sort(key=attrgetter(sort_key), reverse=True)

    match args.mode:
        case 'list':
            for suite in suites:
                print(suite)
            print( 97*'-')
            print(test_result_str('TOTAL', total_tests, total_passes, total_fail, total_errors, total_skip, total_time ))
        case 'html':
            print(test_result_table_header())
            for suite in suites:
                suite.print_entry()
                print('<tr><td colspan="6"><details><summary>&emsp;Results')
                print('</summary>')
                print('<table>')
                print('<tr><th>Test Name</th><th>Status</th><th>Message</th></tr>')
                for case in suite.case_list:
                    print(case.to_html())
                print('</table>')
                print('</details></td></tr>')
            print(test_result_table('TOTAL', total_tests, total_passes, total_fail, total_errors, total_skip, total_time ))
            print('</table>')
        case 'csv':
            print('Name,Group,Subgroup,Status,Message')
            for suite in suites:
                subtype_dict = {}
                for case in suite.case_list:
                    print(case.to_csv())
        case 'tree':
            tree = Tree()
            tree.create_node('Test Groups', 'tests')
            for suite in suites:
                tree.create_node(suite.filename, suite.filename, parent='tests')
                subtype_dict = {}
                for case in suite.case_list:
                    passed = 1 if case.status == 'pass' else 0
                    failed = 1 if case.status == 'failure' else 0
                    subtype = case.classname.split('.')[1]
                    if subtype in subtype_dict:
                        subtype_dict[subtype][0] += passed
                        subtype_dict[subtype][1] += failed
                    else:
                        subtype_dict[subtype] = [passed,failed]
                for (subtype, subtype_list) in subtype_dict.items():
                    percent = 100
                    if (subtype_list[0] + subtype_list[1]) != 0:
                        percent = 100*subtype_list[0] / (subtype_list[0] + subtype_list[1])
                    tree.create_node(f"{subtype+':' : <25} {subtype_list[0] : >3} Pass {subtype_list[1] : >3} Fail {int(percent) : >3}%"\
                                    ,str(suite)+subtype,parent=suite.filename)
            tree.show()
        case 'run_fails':
            suite_failures = {}
            case_failures = []
            for suite in suites:
                if suite.fails == 0:
                    continue
                suite_failures[suite.filename] = []
                for case in suite.case_list:
                    if case.status == 'failure':
                        case_failures.append(case.name)
                        suite_failures[suite.filename].append(case.name)
            for suite_name in suite_failures.keys():
                print(f"    dentos_testbed_runtests -d --stdout \
        --config configuration/testbed_config/basic_infra1_vm/testbed.json \
        --config-dir configuration/testbed_config/basic_infra1_vm/ \
        --suite-groups suite_group_{suite_name} \
        --discovery-reports-dir ./reports \
        --discovery-path ../DentOsTestbedLib/src/dent_os_testbed/discovery/modules/ \
        -k '{' or '.join(suite_failures[suite_name])}'")
                print()


if __name__ == '__main__':

    combine_logs()
