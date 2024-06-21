#!/usr/bin/python3

"""
ciUtils
   CI Utilities

Description:
   This is a command line app that shows test IDs, results and status

TODOs:
   - Support manual testbed locking

"""
from tabulate import tabulate
from typing import Union
import argparse
import os
import sys
from glob import glob
from re import search
from shutil import rmtree

import Utilities
import globalSettings

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('-showtests',          action='store_true', default=False, help='Show all test IDs')
parser.add_argument('-showtestresults',    nargs='+',           default=False, help='Show test ID results')
parser.add_argument('-showstatus',         nargs='+',           default=None,  help='Show one test ID status')
parser.add_argument('-showallstatus',      action='store_true', default=False, help='Show all test status')
parser.add_argument('-showtestbeds',       action='store_true', default=False, help='Show all testbeds')
parser.add_argument('-showlockedtestbeds', action='store_true', default=False, help='Show testbed currently in-used')
# parser.add_argument('-locktestbeds',        nargs="+",          default=None,  help='Lock one or more testbeds')
parser.add_argument('-unlocktestbeds',      nargs='+',          default=None,  help='Unlock a testbed')
parser.add_argument('-unlockalltestbeds',  action='store_true', default=False, help='Unlock all testbeds')
parser.add_argument('-enableci',           action='store_true', default=False, help='Enable the CI Automation framework for testing')
parser.add_argument('-disableci',          action='store_true', default=False, help='Disable the CI Automation framework for testing')
parser.add_argument('-iscienabled',        action='store_true', default=False, help='Check if the CI framework is enabled')
parser.add_argument('-remove',             nargs='+',           default=False, help='Remove one or more test result')
parser.add_argument('-kill',               nargs='?',           default=False, help='Terminate the testId by killing the PID')
args: object = parser.parse_args()


def createTestResultFolder():
    if os.path.exists(globalSettings.dentTestResultsFolder) is False:
        Utilities.makeFolder(globalSettings.dentTestResultsFolder)


def removeFolder(testIdFullPath, testIdName):
    try:
        rmtree(testIdFullPath)
    except Exception as errMsg:
        print(f'Failed to remove testId: {testIdName}. Error: {errMsg}')


class ShowTests:
    """
    Show all the test IDs
    """
    def show(self):
        createTestResultFolder()
        Utilities.runLinuxCmd(f'ls {globalSettings.dentTestResultsFolder}', showStdout=True)


class ShowTestResults:
    """
    show a testId results
    """
    def show(self, testId: str = None) -> None:
        output = Utilities.runLinuxCmd(f'{sys.executable} {globalSettings.dentToolsPath}/test_utils.py csv -d {globalSettings.dentTestResultsFolder}/{testId}', showStdout=False)

        print()
        print(f'{"Name":55}{"Group":20}{"SubGroup":25}{"Status":10}Message')
        print(f'{"-"*117}')

        for index, line in enumerate(output):
            # Name,Group,Subgroup,Status,Message
            if index == 0:
                continue
            else:
                # ['test_system_wide_restart_and_service_reloads', 'sanity', 'test_restart_networking', 'pass', '""']
                line = line.split(',')
                if len(line) == 5:
                    print(f'{line[0]:55}{line[1]:20}{line[2]:25}{line[3]:10}{line[4]:10}')


class ShowStatus:
    """
    Show a testId status
    """
    def show(self, testId: str = None) -> None:
        if testId:
            if os.path.exists(f'{globalSettings.dentTestResultsFolder}/{testId}') is False:
                sys.exit(f'No such test ID: {testId}\n')

            testIdList = [testId]
        else:
            testIdList = Utilities.runLinuxCmd(f'ls {globalSettings.dentTestResultsFolder}', showStdout=False)

        for testId in testIdList:
            print()
            overallSummaryFile = f'{globalSettings.dentTestResultsFolder}/{testId}/ciOverallSummary.json'
            if os.path.exists(overallSummaryFile):
                testIdDetails = Utilities.readJson(overallSummaryFile)
                buildDate = testIdDetails['buildDate']
                buildNumber = testIdDetails['buildNumber']
                testbeds = testIdDetails['testbeds']
                dockerImageTag = testIdDetails['dockerImageTag']
                startTime = testIdDetails['startTime']
                stopTime = testIdDetails['stopTime']
                testDuration = testIdDetails['testDuration']
                testSuites = []
                for testSuite in testIdDetails['testSuites']:
                    regexMatch = search('.*/TestSuites/(.+)', testSuite)
                    if regexMatch:
                        testSuites.append(regexMatch.group(1))

                # Show stages
                print(f'TestId: {testId}   Status: {testIdDetails["status"]}')
                print(f'\tBuild Release: {buildDate}-{buildNumber}')
                print(f'\tTestSuites: {", ".join(testSuites)}')
                print(f'\tDocker Image Tag: {dockerImageTag}')
                print(f'\tStartTime: {startTime}    StopTime: {stopTime}')
                print(f'\tTestDuration: {testDuration}')
                testbedlist = ''
                for index, testbed in enumerate(testbeds):
                    # basic_infra1_10-06-2023-17-50-02-010517_fullRegression
                    regexMatch = search('(.*)_[0-9]+-[0-9]+-[0-9]+-[0-9]+-[0-9]+-[0-9]+-[0-9]+.*', testbed)
                    testbedlist += f'{regexMatch.group(1)} '
                testbedlist = testbedlist.replace(' ', ', ')[:-2]
                print(f'\tTestbeds: {testbedlist}')

                stageRow = ['Stage', 'Stage Name', 'Status', 'Result', 'Errors']
                stageTable = [stageRow]

                print()
                stageData = []
                for stage in testIdDetails['stageOrder']:
                    # stage = ['stage 1', 'cloneTestRepo']
                    stageNumber = stage[0].split(' ')[1]
                    stageName = stage[1]
                    status = testIdDetails['stages'][stageName]['status']
                    result = testIdDetails['stages'][stageName]['result']
                    error = testIdDetails['stages'][stageName]['error']
                    if len(error) > 0:
                        allErrors = ''
                        for eachError in error:
                            allErrors += f'{eachError}\n'
                    else:
                        allErrors = []

                    stageData = [stageNumber, stageName, status, result, allErrors]
                    stageTable.append(stageData)

                print(tabulate(stageTable, headers='firstrow', tablefmt='fancy_grid', numalign='center'))
                print()

                testcases = testIdDetails['testcases']
                testRow = ['Suite Group', 'Testbed', 'Test Conduct', 'Status']
                testTable = [testRow]
                testData = []

                for index, testcase in enumerate(testcases):
                    testbed = str(testIdDetails['testcases'][testcase]['testbed'])
                    status = testIdDetails['testcases'][testcase]['status']
                    result = str(testIdDetails['testcases'][testcase]['result'])
                    testConduct = testIdDetails['testcases'][testcase]['testConduct']
                    testcase = testcase.replace('suite_group_', '')

                    if status == 'Aborted':
                        result = 'None'

                    testData = [testcase, testbed, testConduct, status]
                    testTable.append(testData)

                print(tabulate(testTable, headers='firstrow', tablefmt='fancy_grid'))


class ShowTestbeds:
    """
    Show testbed names
    """
    def show(self):
        # /home/dent/testing
        dentTestingPath = globalSettings.dentCiFrameworkPath.replace('/CI_Automation', '')
        testbedPath = f'{dentTestingPath}/DentOS_Framework/DentOsTestbed/configuration/testbed_config'

        # ['basic_agg1', 'basic_agg2', 'basic_dist1', 'basic_infra1', 'basic_infra2', 'sit', 'sit_vm']
        testbeds = Utilities.runLinuxCmd(f'ls {testbedPath}', showStdout=False)
        sitIndex = testbeds.index('sit')
        testbeds.pop(sitIndex)
        sitVMIndex = testbeds.index('sit_vm')
        testbeds.pop(sitVMIndex)

        print('\nTestbeds:')
        print(f'{"-"*8}')
        for index, testbed in enumerate(testbeds):
            print(f'   {index+1}: {testbed}')
        print()


class ShowLockedTestbeds:
    """
    Show all occupied and wait-list testbeds
    """
    def show(self):
        lockedTestbeds = []

        output = Utilities.runLinuxCmd(f'ls {globalSettings.testbedMgmtFolder}', showStdout=False)
        print('\nTestbeds currently in used')
        print(f'{"-"*26}')
        for index, testbed in enumerate(output):
            if testbed == 'Waiting':
                continue

            print(f'   {index+1}: {testbed}')
            lockedTestbeds.append(testbed)

        print()

        if len(glob(f'{globalSettings.testbedMgmtWaitingFolder}/*')) > 0:
            print('\nTest waiting for testbeds')
            print(f'{"-"*25}')
            output = Utilities.runLinuxCmd(f'ls {globalSettings.testbedMgmtWaitingFolder}', showStdout=False)
            for index, testbed in enumerate(output):
                print(f'   {index+1}: {testbed}')
            print()

        return lockedTestbeds


class LockTestbeds:
    """
    Lock a testbed
    """
    def lock(self, testbeds: Union[list, str]) -> None:
        """
        Manually lock one or more testbeds

        TODO:
           - Enhanced TestbedReservation.py to support manually-locked testbeds
        """
        lockedTestbeds = ShowLockedTestbeds().show()

        for testbed in testbeds:
            isCurrentlyLocked = False
            # For each required testbed, check if the testbed is currently being used
            for currentlyLockedTestbed in lockedTestbeds:
                # basic_agg1|basic_agg1_10-05-2023-15-21-38-988142_myDev
                regexMatch = search(f'^{testbed}$|{testbed}_[0-9]+-[0-9]+-[0-9]+-[0-9]+-[0-9]+-[0-9]+-[0-9]+.*', currentlyLockedTestbed)
                if regexMatch:
                    isCurrentlyLocked = True

            if isCurrentlyLocked is False:
                print(f'Locking testbed: {testbed}')
                Utilities.runLinuxCmd(f'touch {testbed}', cwd=globalSettings.testbedMgmtFolder)


class UnlockTestbeds:
    """
    Unlock a testbed
    """
    def unlock(self, testbed: Union[list, str]) -> None:
        """
        testbed: One testbed name or 'all'
        """
        if testbed == 'all':
            testbeds = Utilities.runLinuxCmd(f'ls {globalSettings.testbedMgmtFolder}', showStdout=False)
        else:
            testbeds = testbed

        for eachTestbed in testbeds:
            testbedFile = f'{globalSettings.testbedMgmtFolder}/{eachTestbed}'
            Utilities.runLinuxCmd(f'rm {testbedFile}', showStdout=False)
            if os.path.exists(testbedFile) is False:
                print(f'\nTestbed unlocked: {eachTestbed}\n')
            else:
                print(f'\nFailed: Unlocktestbed: {eachTestbed}\n')


class Remove:
    def removeTestId(self, testIds: list = []) -> None:
        """
        testIds: The is a regex search.  You could provide a list of
                 exact filenames and regex patterns

        For example:
              -remove .*myDev$  -> This will remove all test results that has pattern ending with myDev
        """
        if testIds[0] == 'all':
            testIdList = glob(f'{globalSettings.dentTestResultsFolder}/*')
        else:
            testIdList = []
            for testId in testIds:
                for testResult in glob(f'{globalSettings.dentTestResultsFolder}/*'):
                    try:
                        if search(f'{testId}', testResult):
                            testIdList.append(testResult)
                    except Exception:
                        sys.exit(f'Invalid search: {testIds}')

        # Don't remove test resuts that are still running
        currentlyRunningPids = Utilities.runLinuxCmd('pgrep -f runDentCi.py', showStdout=True)

        for testIdFullPath in testIdList:
            testIdName = testIdFullPath.split('/')[-1]
            ciSummaryFile = f'{testIdFullPath}/ciOverallSummary.json'

            if os.path.exists(ciSummaryFile):
                try:
                    testIdData = Utilities.readJson(ciSummaryFile)
                    testIdPid = str(testIdData['pid'])
                    if testIdPid not in currentlyRunningPids:
                        print(f'Removing: {testIdName}')
                        removeFolder(testIdFullPath)
                except Exception:
                    removeFolder(testIdFullPath, testIdName)
            else:
                # The testId has no ciOverallSummary file. Just remove it.
                print(f'Removing stale testId result that does not have a ciOverallSummary.json file: {testIdName}')
                try:
                    print(f'Removing: {testIdFullPath}')
                    rmtree(testIdFullPath, testIdName)
                except Exception as errMsg:
                    print(f'Failed to remove testId: {testIdName}. Error: {errMsg}')


if args.showtests:
    ShowTests().show()

elif args.showtestresults:
    ShowTestResults().show(testId=args.showtestresults[0])

elif args.showstatus:
    ShowStatus().show(testId=args.showstatus[0])

elif args.showallstatus:
    ShowStatus().show()

elif args.showtestbeds:
    ShowTestbeds().show()

elif args.showlockedtestbeds:
    ShowLockedTestbeds().show()

elif args.unlocktestbeds:
    UnlockTestbeds().unlock(testbed=args.unlocktestbeds)

elif args.unlockalltestbeds:
    UnlockTestbeds().unlock(testbed='all')

# elif args.locktestbeds:
#    LockTestbeds().lock(testbeds=args.locktestbeds)

elif args.disableci:
    Utilities.runLinuxCmd(f'touch {globalSettings.disableSystemFilename}', cwd=globalSettings.dentCiMgmtPath)

elif args.enableci:
    Utilities.runLinuxCmd(f'rm {globalSettings.disableSystemFilename}', cwd=globalSettings.dentCiMgmtPath)

elif args.iscienabled:
    if os.path.exists(f'{globalSettings.dentCiMgmtPath}/{globalSettings.disableSystemFilename}'):
        print('\nCI framework is enabled\n')
    else:
        print('\nCI framework is disabled\n')

elif args.kill:
    # Termininate only one test at a time
    overallSummaryFile = f'{globalSettings.dentTestResultsFolder}/{args.kill}/ciOverallSummary.json'
    if os.path.exists(overallSummaryFile):
        pid = Utilities.readJson(overallSummaryFile)['pid']
        Utilities.closeTestMgmtStatus(overallSummaryFile=overallSummaryFile, status='terminated', result='None')
        Utilities.runLinuxCmd(f'kill -9 {pid}', showStdout=True)

elif args.remove:
    Remove().removeTestId(testIds=args.remove)

sys.exit()
