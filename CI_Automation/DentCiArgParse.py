import sys
import os
import argparse
import Utilities
import globalSettings

timestamp = Utilities.getTimestamp(includeMillisecond=True).replace(':', '-')


class DentCiArgParse:
    def __init__(self, ciVars: object) -> None:
        self.ciVars = ciVars

        # Create the DentCiMgmt folder
        if os.path.exists(globalSettings.dentCiMgmtPath) is False:
            Utilities.runLinuxCmd(f'mkdir -p {globalSettings.dentCiMgmtPath}')
            Utilities.runLinuxCmd(f'chmod -R 770 {globalSettings.dentCiMgmtPath}')

        if os.path.exists(f'{globalSettings.dentCiMgmtPath}/TestBranches') is False:
            Utilities.runLinuxCmd('mkdir TestBranches', cwd=globalSettings.dentCiMgmtPath)
            Utilities.runLinuxCmd('chmod -R 770 TestBranches', cwd=globalSettings.dentCiMgmtPath)

    def parse(self):
        parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
        parser.add_argument('-testName',          nargs='+', default=None, help='Give a test name to identify your test ID.')
        parser.add_argument('-builds',            nargs='+', default=None, help='Get from Dent website. Both ARM and AMD full path URLs for the builds')
        parser.add_argument('-localBuilds',       nargs='+', default=None, help='Local path to builds. Both ARM and AMD full path URLs for the builds')
        parser.add_argument('-testSuites',        nargs='+', default=None, help='The test suite to run')
        parser.add_argument('-repo',              nargs='+', default=None, help='The repo to clone for testing')
        parser.add_argument('-localBranch',       nargs='+', default=None, help='Test with a local branch that is already cloned. Provide the path.')
        parser.add_argument('-branchName',        nargs='+', default=None, help='The repo branch to use for testing')
        parser.add_argument('-keepTestBranch',    action='store_true', default=False, help='Do not delete the test branch after the test')
        parser.add_argument('-http',              action='store_true', default=False, help='Install build by http server')
        parser.add_argument('-tftp',              action='store_true', default=False, help='Install build by tftp server')
        parser.add_argument('-abortTestOnError',  action='store_true', default=False, help='Abort the test if test encounters an error')
        parser.add_argument('-disableCloneTestRepo',     action='store_true', default=False, help='Disable clone Dent test repo for testing')
        parser.add_argument('-disableDownloadNewBuilds', action='store_true', default=False, help='Disable download builds')
        parser.add_argument('-disableInstallDentOS',     action='store_true', default=False, help='Disable Install DentOS on Dent switches')
        parser.add_argument('-deployIxNetwork',          action='store_true', default=False, help='Enable deploy IxNetwork')
        parser.add_argument('-disableDeployDentTestContainer', action='store_true', default=False, help='Disable deploy Dent Test Docker Containers')
        parser.add_argument('-disableRunTest',           action='store_true', default=False, help='Disable run Dent regression testing')
        args: object = parser.parse_args()

        if args.testName:
            self.ciVars.testName = args.testName[0]
            self.ciVars.testId = f'{timestamp}_{args.testName[0]}'
        else:
            self.ciVars.testId = timestamp

        self.ciVars.timestamp:                str = timestamp
        self.ciVars.testSessionFolder:        str = f'{globalSettings.dentTestResultsFolder}/{self.ciVars.testId}'
        self.ciVars.testSessionLogsFolder:    str = f'{self.ciVars.testSessionFolder}/CI_Logs'
        self.ciVars.testSessionLogsFile:      str = f'{self.ciVars.testSessionLogsFolder}/ciSessionLogs'
        self.ciVars.testIdTestingBranch:      str = f'{globalSettings.dentCiMgmtPath}/TestBranches/{self.ciVars.testId}'
        self.ciVars.ixNetworkLogsFile:        str = f'{self.ciVars.testSessionLogsFolder}/deployIxNetworkLogs'
        self.ciVars.testContainersLogFile:    str = f'{self.ciVars.testSessionLogsFolder}/deployTestContainersLogs'
        self.ciVars.overallSummaryFile:       str = f'{self.ciVars.testSessionFolder}/ciOverallSummary.json'
        self.ciVars.reportFile:               str = f'{self.ciVars.testSessionFolder}/ciTestReport'

        if args.testSuites is None:
            sys.exit(1, '-testSuites parameter is required with test suites to use for testing')
        else:
            # Verify for user defined testSuites existence
            for eachTestSuite in args.testSuites:
                testSuite = eachTestSuite.replace('.yml', '')
                testSuiteFile = f'{self.ciVars.testSuiteFolder}/{testSuite}.yml'
                if os.path.exists(testSuiteFile) is False:
                    Utilities.sysExit(self.ciVars, f'No such test suite name found: {eachTestSuite}')

                self.ciVars.testSuites.append(testSuiteFile)

        if args.builds is None:
            self.ciVars.builds = []
        else:
            self.ciVars.builds = args.builds

        if args.localBuilds is None:
            self.ciVars.localBuilds = []
        else:
            self.ciVars.localBuilds = args.localBuilds

        if args.repo is None:
            # Default pulling the main branch
            self.ciVars.repo = self.ciVars.gitCloneDefaultRepo
        else:
            self.ciVars.repo = args.repo[0]

        if args.branchName:
            # ['/home/dent/testing']
            self.ciVars.branchName = args.branchName[0]

        if args.localBranch:
            if os.path.exists(args.localBranch[0]):
                # Get rid of the training slash
                if args.localBranch[0][-1] == '/':
                    localBranch = args.localBranch[0][:-1]
                else:
                    localBranch = args.localBranch[0]

                self.ciVars.localTestBranch = localBranch
                self.ciVars.repo = localBranch
            else:
                print(f'No such local test branch: {args.localBranch[0]}')
                sys.exit(f'No such local test branch: {args.localBranch[0]}')
        else:
            self.ciVars.localTestBranch = None

        if args.tftp is False and args.http is False:
            # Default to use http
            self.ciVars.installMethod == 'http'
        else:
            if args.tftp:
                self.ciVars.installMethod == 'tftp'

            if args.http:
                self.ciVars.installMethod == 'http'

        if args.keepTestBranch:
            self.ciVars.deleteTestBranchAfterTest = False

        if args.abortTestOnError:
            self.ciVars.abortTestOnError = True

        if args.disableCloneTestRepo:
            self.ciVars.cloneTestRepo = False

        if args.disableDownloadNewBuilds:
            self.ciVars.downloadNewBuilds = False
        else:
            if args.builds:
                self.ciVars.builds = args.builds
            else:
                # Getting here means to scrape for the latest builds
                self.ciVars.builds = []

        if args.disableInstallDentOS:
            self.ciVars.installDentOS = False

        if args.disableDeployDentTestContainer:
            self.ciVars.deployDentTestContainers = False

        if args.deployIxNetwork:
            self.ciVars.deployIxNetwork = True

        if args.disableRunTest:
            self.ciVars.runTest = False
