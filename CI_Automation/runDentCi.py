#!/usr/bin/python3

"""
Dent CI Automation Framework

Automating the following stages:
   Stage 1: Clone test repo
   Stage 1: Download new builds
   Stage 2: Install Dent OS
   Stage 2: Deploy IxNetwork
   Stage 2: Deploy Dent test containers
   Stage 3: Run Test

Usage:
   For Jenkins CI, must include -testName that begins with jenkinsCI_<label>
   This will create result path in a file for Jenkin's CI operators to retrieve

   # Dev mode quick test
   runDentCi -testSuite hw/sit/cleanConfig -testName devMode -localBranch /home/dent/testing
   runDentCi -testSuite hw/sit/cleanConfig -testName devMode -localBranch /path/dent-testing2 -localBuilds <arms> <amd>
   runDentCi -testSuite hw/sit/l3tests -testName devMode -localBranch /home/dent/testing
   runDentCi -testSuite hw/sit/cleanConfig -repo https://github.com/dentproject/testing.git -testName devMode -localBranch /home/dent/testing

   # dev mode: disable all
   runDentCi -testSuite hw/sit/cleanConfig -testName devMode -disableCloneTestRepo -disableDownloadNewBuilds -disableInstallDentOS -disableDeployDentTestContainer -disableRunTest

   # Dent repo with a specific branch name
   runDentCi -testSuite hw/sit/fullRegression.yml -repo https://github.com/dentproject/testing.git -branchName pr_update_testbed_configs2 -keepTestBranch

   # Don't remove the test branch after the test using -keepTestBranch
   runDentCi -testSuite hw/sit/cleanConfig -keepTestBranch -repo https://github.com/dentproject/testing.git -builds
"""

import sys
import os
import traceback
from threading import Thread, Lock
from datetime import datetime
from re import search
from time import sleep
from glob import glob
from shutil import rmtree
from pydantic import Field, dataclasses

import Utilities
import globalSettings
from DentCiArgParse import DentCiArgParse
from CloneTestingRepo import GitCloneTestingRepo
from DownloadBuilds import downloadBuilds
from DeployIxNetwork import deployIxNetworkInit
from DeployDent import updateDent
from DeployTestContainers import DeployTestContainers
from TestMgmt import TestMgmt
from TestbedReservation import ManageTestbed

pid = os.getpid()
threadLock = Lock()


@dataclasses.dataclass
class CiVars:
    """
    This class declares and contains all variables and share across all modules
    """
    # Stages are set in DentCiArgParse.py

    # Stage 1
    cloneTestRepo:             bool = True
    downloadNewBuilds:         bool = True
    # Stage 2
    installDentOS:             bool = True  # requires cloneTestRepo for testbed configs
    # IxNetwork is always enabled. No need to deploy until new IxNetwork is released
    deployIxNetwork:           bool = False
    deployDentTestContainers:  bool = True
    # Stage 3
    runTest:                   bool = True  # requires cloneTestRepo for testbed configs

    # The test ID timestamp (without the appended testName)
    timestamp:                str = ''
    # The follows are set in DentCiArgParse.py
    testId:                   str = ''
    # A name to identify a test
    testName:                 str = ''
    # /home/dent/DentCiMgmt/TestResults/<testId>
    testSessionFolder:        str = ''
    # '{testSessionFolder}/CI_Logs'
    testSessionLogsFolder:    str = ''
    # '{testSessionLogsFolder}/sessionLogs'
    testSessionLogsFile:      str = ''
    # '{testSessionLogsFolder}/deployIxNetworkLogs'
    ixNetworkLogsFile:        str = ''
    # '{testSessionLogsFolder}/deployTestContainersLogs'
    testContainersLogFile:    str = ''
    # '{testSessionFolder}/ciOverallSummary.json'
    overallSummaryFile:       str = ''
    # '{testSessionFolder}/ciTestReport'
    reportFile:               str = ''

    # The CI test object
    ciObj:                    object = None

    # File to store all test result paths for Jenkins CI/CT/CD
    ciResultPathFolderName:   str = 'CiResultPaths'
    ciResultPathsFile:        str = f'{globalSettings.dentCiMgmtPath}/{ciResultPathFolderName}/ciResultPaths.json'

    testSuiteFolder:          str = f'{globalSettings.dentCiFrameworkPath}/TestSuites'
    installBuildResultFolder: str = f'{globalSettings.dentCiMgmtPath}/installBuildResultsTempFolder'

    # Where to store IxNetwork VM downloads
    ixNetworkVMFolder:        str = f'{globalSettings.dentCiMgmtPath}/IxNetworkVMs'
    # If user did not specify a repo to pull for testing, default to Dent's main branch
    gitCloneDefaultRepo:      str = globalSettings.gitCloneDefaultRepo
    repo:                     str = None
    branchName:               str = ''
    # dockerImageTag = Each testId creates a docker image name for identification
    #                  Set in CloneTestingRepo.py::clone
    dockerImageTag:           str = None

    testBranchFolder:         str = f'{globalSettings.dentCiMgmtPath}/TestBranches'
    deleteTestBranchAfterTest: bool = True

    # This is set in DentCiArgParse.py
    # This framework will change the cloned test branch name to the testId as the
    # name of the test branch and delete it when test is done
    testIdTestingBranch:      str = ''

    # A repo test branch already pulled on local server. User wants to use this branch for testing
    localTestBranch:          str = None

    # Either http|tftp set below this class: http://<ip>/dentInstallation
    serverPrefixPath:         str = ''
    # /DentBuildReleases/<testId> or /tftpMainPath/<testId>. Set below this class.
    downloadToServerFolder:   str = ''

    # Set in DentCiArgParse.py. Default to http
    installMethod:            str = 'http'
    testBranch:               str = ''
    # testbeds includes the entire testbed config json data for Dent updates
    testbeds:                 list = Field(default_factory=lambda: [])
    # testIdTestbeds are just the testbed names for reservation
    testIdTestbeds:           list = Field(default_factory=lambda: [])
    ixNetworkIpAddresses:     list = Field(default_factory=lambda: [])
    pid:                      int = pid
    user:                     str = os.environ['USER']
    sessionLog:               object = None
    builds:                   list = Field(default_factory=lambda: [])
    localBuilds:              list = Field(default_factory=lambda: [])
    localTestBranch:          str = None
    testSuites:               list = Field(default_factory=lambda: [])
    abortTestOnError:         bool = False
    lock:                     object = threadLock
    exitCode:                 str = None


class DentCI:
    def __init__(self, ciVars):
        self.ciVars = ciVars

        self.ciVars.testIdTestingBranch = f'{self.ciVars.testBranchFolder}/{self.ciVars.testId}'

        if self.ciVars.installMethod == 'http':
            # /dentInstallations/<testId>
            self.ciVars.downloadToServerFolder = f'{globalSettings.httpServerFolder}/{self.ciVars.testId}'
            # http://<ip>/dentInstallations/<testId>
            # http://ipAddress/DentBuildReleases/06-11-2024-19-07-00-659703_devMode
            self.ciVars.serverPrefixPath = f'{globalSettings.httpServerPath}/{self.ciVars.testId}'
        if self.ciVars.installMethod == 'tftp':
            # /srv/tftp/<testId>
            self.ciVars.downloadToServerFolder = f'{globalSettings.tftpServerFolder}/{self.ciVars.testId}'
            # tftp://<ip>/srv/tftp/<testId>
            self.ciVars.serverPrefixPath = f'{globalSettings.tftpServerPath}/{self.ciVars.testId}'

        self.removePastResults()
        self.removeStaleTestBranches()
        self.removePastBuildDownloads()
        self.removeDockerStaleImages()

        self.testMgmtData = {'pid': self.ciVars.pid,
                             'testId': self.ciVars.testId,
                             'testName': self.ciVars.testName,
                             'startTime': datetime.now().strftime('%m-%d-%Y %H:%M:%S:%f'),
                             'stopTime': None,
                             'testDuration': None,
                             'error': None,
                             'result': None,
                             'abortTestOnError': self.ciVars.abortTestOnError,
                             'testSuites': self.ciVars.testSuites,
                             'testbeds': self.ciVars.testIdTestbeds,
                             'builds': self.ciVars.builds,
                             'localBuilds': self.ciVars.localBuilds,
                             'localTestBranch': ciVars.localTestBranch,
                             'buildDate': None,
                             'buildNumber': None,
                             'repo': self.ciVars.repo,
                             'branchName': self.ciVars.branchName,
                             'tempTestBranchPath': self.ciVars.testIdTestingBranch,
                             'dockerImageTag': self.ciVars.dockerImageTag,
                             'deleteTestBranchAfterTest': self.ciVars.deleteTestBranchAfterTest,
                             'user': self.ciVars.user,
                             'logDir': self.ciVars.testSessionFolder,
                             'status': 'running',
                             'stageOrder': [('stage 1', 'cloneTestRepo'), ('stage 1', 'downloadNewBuilds'),
                                            ('stage 2', 'installDentOS'), ('stage 2', 'deployIxNetwork'),
                                            ('stage 2', 'deployDentTestContainers'), ('stage 3', 'runTest')],
                             'stages': {'cloneTestRepo':   {'status': None, 'result': None, 'error': []},
                                        'downloadNewBuilds':  {'status': None, 'result': None, 'error': []},
                                        'installDentOS':   {'status': None, 'result': None, 'error': []},
                                        'deployIxNetwork': {'status': None, 'result': None, 'error': []},
                                        'deployDentTestContainers': {'status': None, 'result': None, 'error': []},
                                        'runTest': {'status': None, 'result': None, 'error': []},
                                        },
                             'testcases': {}
                             }

        # Create a unique test session timestamp folder
        Utilities.runLinuxCmd(f'mkdir -p {self.ciVars.testSessionFolder}', logObj=None)
        Utilities.runLinuxCmd(f'mkdir -p {self.ciVars.testSessionLogsFolder}', logObj=None)
        Utilities.writeToJson(jsonFile=self.ciVars.overallSummaryFile, data=self.testMgmtData, mode='w')

        self.ciVars.sessionLog = Utilities.CreateLogObj(self.ciVars.testSessionLogsFile)
        if os.path.exists(self.ciVars.installBuildResultFolder) is False:
            Utilities.runLinuxCmd(f'mkdir -p {self.ciVars.installBuildResultFolder}', logObj=self.ciVars.sessionLog)

        self.ciVars.sessionLog.info(f'PID: {self.ciVars.pid}')
        self.ciVars.sessionLog.info(f'Test ID: {self.ciVars.testId}')
        self.ciVars.sessionLog.info(f'Builds: {self.ciVars.builds}')
        self.ciVars.sessionLog.info(f'Test session folder: {self.ciVars.testSessionFolder}')
        self.ciVars.sessionLog.info(f'Install Method: {self.ciVars.installMethod}')
        self.ciVars.sessionLog.info(f'Testing repo: {self.ciVars.repo}')
        self.ciVars.sessionLog.info(f'Install branchName: {self.ciVars.branchName}')

        # Wait at this point until the CI system is enabled
        self.isCiSystemEnabled()

        # If user wants to install IxNetwork, must disable
        # the CI system so no new incoming test could run
        if self.ciVars.deployIxNetwork:
            self.ciVars.sessionLog.info('The CI framework is going to install a new version of IxNetwork as soon as all the current tests are done. Please wait.')
            Utilities.runLinuxCmd(f'touch {globalSettings.disableSystemFilename}', cwd=globalSettings.dentCiMgmtPath)
            # Wait until all current tests are done before running *this* test that installs IxNetwork VM
            while True:
                currentlyRunningPids = Utilities.getDentCiRunningProcessIds(processName='testSuite')
                if str(self.ciVars.pid) in currentlyRunningPids:
                    index = currentlyRunningPids.index(str(self.ciVars.pid))
                    currentlyRunningPids.pop(index)

                if len(currentlyRunningPids) > 0:
                    self.ciVars.sessionLog.info(f'There are still {len(currentlyRunningPids)} dent tests running')
                    sleep(10)
                else:
                    self.ciVars.sessionLog.info('No Dent test running')
                    break

        Utilities.createCiResultPathFolder(dentCiMgmtPath=globalSettings.dentCiMgmtPath,
                                           ciResultPathFolderName=self.ciVars.ciResultPathFolderName)

        Utilities.removeJenkinsCiOldResults(jenkinsCiResultFile=self.ciVars.ciResultPathsFile,
                                            removeAfterDays=globalSettings.removeTestResultsAfterNumberOfDays,
                                            threadLock=self.ciVars.lock)

        Utilities.updateTestMgmtData(self.ciVars.overallSummaryFile, updateProperties={'status': 'running'}, threadLock=self.ciVars.lock)

        for eachStage in ['cloneTestRepo', 'downloadNewBuilds', 'installDentOS',
                          'deployIxNetwork', 'deployDentTestContainers', 'runTest']:
            if getattr(self.ciVars, eachStage):
                Utilities.updateStage(self.ciVars.overallSummaryFile, stage=eachStage, status='not-started', threadLock=self.ciVars.lock)
            else:
                Utilities.updateStage(self.ciVars.overallSummaryFile, stage=eachStage, status='disabled', threadLock=self.ciVars.lock)

        self.createDockerImageTag()
        self.lockTestbeds()

    def createDockerImageTag(self):
        """
        Create a docker image tag for each test
        Docker will overwrite existing tags except for the latest.
        This CI framework will remove the created tag image at the end
        of the test.
        """
        if self.ciVars.localTestBranch:
            # Show the last x-paths
            repoName = self.ciVars.localTestBranch.replace('/', '-')
            repoName = f'localBranch{repoName}'
        else:
            regexMatch = search(r'.*.com/(.*)\.git', self.ciVars.repo)
            repoName = regexMatch.group(1).replace('/', '-')

        # randomLetters = Utilities.generatorRandom(6, 'abcdef')
        randomNumbers = self.ciVars.timestamp.split('-')[-1]

        # Defined the docker image tag here for DeployTestContainers to use
        if self.ciVars.branchName:
            self.ciVars.dockerImageTag = f'CI-{repoName}-{branchName}-{randomNumbers}'
        else:
            self.ciVars.dockerImageTag = f'CI-{repoName}-main-{randomNumbers}'

        self.testMgmtData.update({'dockerImageTag': self.ciVars.dockerImageTag})
        Utilities.writeToJson(jsonFile=self.ciVars.overallSummaryFile, data=self.testMgmtData, mode='w')

    def isDockerImageTagExists(self):
        """
        REPOSITORY                 TAG                                     IMAGE ID       CREATED          SIZE
        dent/test-framework        CI-dentproject-testing-main             9eb2da646f95   24 minutes ago   897MB
        dent/test-framework        CI-localBranch-home-dent-testing-main   3ef4db5d132e   24 hours ago     897MB
        dent/test-framework-base   latest                                  1a91767e8243   44 hours ago     539MB
        """
        output = Utilities.runLinuxCmd('docker images', logObj=self.ciVars.sessionLog)
        for lineOutput in output:
            if bool(search(f'[^ ]+ +{self.ciVars.dockerImageTag} .+', lineOutput)):
                return True

    def lockTestbeds(self):
        # getTestbeds will populate self.ciVars.testIdTestbeds
        Utilities.getTestbeds(self.ciVars)

        self.testbedMgmtObj = ManageTestbed(ciVars=self.ciVars)
        self.testbedMgmtObj.waitForTestbeds()

        self.testMgmtData.update({'testbeds': self.ciVars.testIdTestbeds})
        Utilities.writeToJson(jsonFile=self.ciVars.overallSummaryFile, data=self.testMgmtData, mode='w')

    def isGitCloneSafeToRun(self):
        """
        git clone is not thread safe. Must verify if git is cloning.
        If yes, wait until the it is done
        """
        while True:
            if Utilities.processExists(processName='git clone'):
                self.ciVars.sessionLog.info('git clone is running. Waiting 3 seconds ...')
                sleep(3)
            else:
                self.ciVars.sessionLog.info('git clone is not running. Safe to do git clone.')
                break

        sleep(3)

    def isCiSystemEnabled(self):
        """
        Pause the test if Dent CI framework is disabled.
        Dent CI looks for the "disabledCiSystem" file in the /home/dent/DentCiMgmt folder

        When the CI automation framework is avaialble for testing, each test
        will reserve the testbed or go to testbed waiting list -> self governing
        """
        showOnce = True
        while True:
            if os.path.exists(f'{globalSettings.dentCiMgmtPath}/{globalSettings.disableSystemFilename}'):
                if showOnce:
                    self.ciVars.sessionLog.info('The Dent CI Framework is currently disabled for maintenace. The test will run when it is enabled.')
                    Utilities.updateTestMgmtData(self.ciVars.overallSummaryFile,
                                                 updateProperties={'status': 'system-is-disabled | waiting-for-system'},
                                                 threadLock=self.ciVars.lock)
                    showOnce = False
                sleep(3)
            else:
                break

    def isTestIdTestBranchExists(self, stage=None):
        """
        Verify if the testing branch successfully got cloned
        """
        if os.path.exists(self.ciVars.testIdTestingBranch) is False:
            errorMsg = f'Stage={stage}: Is cloneTestBranch == True?  The testID test branch does not exists: {self.ciVars.testIdTestingBranch}.'
            self.ciVars.sessionLog.error(errorMsg)

            if stage:
                Utilities.updateStage(self.ciVars.overallSummaryFile, stage=stage,
                                      status='aborted', result=None, error=errorMsg, threadLock=self.ciVars.lock)

            self.testbedMgmtObj.unlockTestbeds()
            Utilities.closeTestMgmtStatus(overallSummaryFile=self.ciVars.overallSummaryFile,
                                          status='aborted', result='None', threadLock=self.ciVars.lock)
            Utilities.runDentCiTearDown(self.ciVars, errorMsg)

    def removeDockerStaleImages(self):
        # REPOSITORY                 TAG                                  IMAGE ID       CREATED         SIZE
        # dent/test-framework        CI-dentproject-testing-main-eaafaf   0a19af8a32ea   4 minutes ago   897MB
        # dent/test-framework-base   latest                               1a91767e8243   47 hours ago    539MB
        dockerImages = Utilities.runLinuxCmd('docker images')

        # docker container ps -a
        # bbdac6c0735d   dent/test-framework:CI-dentproject-testing-main-eaafaf   "dentos_testbed_runt…"   37 seconds ago
        # Up 37 seconds             suite_group_clean_config_10-05-2023-20-47-10-738249_myDev

        dockerContainers = Utilities.runLinuxCmd('docker container  ps -a', logObj=self.ciVars.sessionLog)

        if len(dockerContainers) == 0:
            for dockerImage in dockerImages:
                regexMatch = search('[^ ]+ +(CI-[^ ]+) +([^ ]+) .+', dockerImage)
                if regexMatch:
                    tag = regexMatch.group(1)
                    imageId = regexMatch.group(2)

                    if tag != 'latest':
                        Utilities.runLinuxCmd(f'docker rmi -f {imageId}', logObj=self.ciVars.sessionLog)
        else:
            for dockerImage in dockerImages:
                regexMatch = search('[^ ]+ +(CI-[^ ]+) +([^ ]+) .+', dockerImage)
                if regexMatch:
                    tag = regexMatch.group(1)
                    imageId = regexMatch.group(2)
                    removeDockerImage = True

                    for openedContainer in dockerContainers:
                        # Don't remove the docker image if a container is using it
                        if bool(search(f'[^ ]+ +:{tag} .+', openedContainer)):
                            removeDockerImage = False
                            break

                    if removeDockerImage:
                        Utilities.runLinuxCmd(f'docker rmi -f {imageId}', logObj=self.ciVars.sessionLog)

    def parseForTestbeds(self, configFullPath):
        """
        Get all testbeds from test suites "config" parameter
        """
        if os.path.exists(configFullPath) is False:
            print(f'Test Suite config does not exists: {configFullPath}')
            Utilities.runDentCiTearDown(ciVars, f'Test Suite file has an incorrect "config" path: {configFullPath}')

        testbedContents = Utilities.readJson(configFullPath)

        for eachTestbedInSit in testbedContents['devices']:
            hostName = eachTestbedInSit['hostName']
            if hostName == 'ixia':
                ixNetworkIp = eachTestbedInSit['ip']

                if ixNetworkIp not in ciVars.ixNetworkIpAddresses:
                    ciVars.ixNetworkIpAddresses.append(ixNetworkIp)

            if eachTestbedInSit['os'] == 'dentos':
                deviceAlreadyInTheTestbedList = False

                # Check the current testbed list for the Dent device
                for existingTestbed in self.ciVars.testbeds:
                    if existingTestbed['hostName'] == hostName:
                        deviceAlreadyInTheTestbedList = True

                if deviceAlreadyInTheTestbedList is False:
                    self.ciVars.testbeds.append(eachTestbedInSit)

    def verifyIxNetworkVMFunctionality(self):
        for ixNetworkIp in ciVars.ixNetworkIpAddresses:
            self.ciVars.sessionLog.info(f'verifyIxNetworkVMFunctionality: {ixNetworkIp}')

            if Utilities.isReachable(ipOrName=ixNetworkIp, port=443) is False:
                self.ciVars.sessionLog.warning(f'ixNetwork VM is unreachable: {ixNetworkIp}')
                if self.ciVars.deployIxNetwork is False:
                    self.deployIxNetwork(forceBringUp=True)
            else:
                self.ciVars.sessionLog.info(f'IxNetwork VM is reachable: {ixNetworkIp}')

    def removePastResults(self):
        """
        Self clean up all past test results to free up storage space
        """
        Utilities.removePastResults(folder=globalSettings.dentTestResultsFolder,
                                    removeDaysOlderThan=globalSettings.removeTestResultsAfterNumberOfDays)

        testIdList = glob(f'{globalSettings.dentTestResultsFolder}/*')

        # Remove stale running process IDs that doesn't have a ciOverallSummary.json file
        for testIdFullPath in testIdList:
            testIdName = testIdFullPath.split('/')[-1]
            ciSummaryFile = f'{testIdFullPath}/ciOverallSummary.json'

            if os.path.exists(ciSummaryFile) is False:
                # The testId has no ciOverallSummary file. Just remove it.
                self.ciVars.sessionLog.info(f'Removing stale testId result folder that does not have a ciOverallSummary.json file: {testIdName}')
                try:
                    rmtree(testIdFullPath)
                except Exception as errMsg:
                    self.ciVars.sessionLog.failed(f'Failed to remove testId: {testIdName}. Error: {errMsg}')

    def removePastBuildDownloads(self):
        # Exampe: /DentBuildReleases/09-28-2023-16-25-52-377875_myDev3
        Utilities.removeBuildReleases(folder=globalSettings.httpServerFolder, removeDaysOlderThan=1)

    def removeStaleTestBranches(self):
        """
        Remove left-over past test branches if:
            - They were not deleted
            - The testId is removed in TestResults folder
        """
        if os.path.exists(f'{globalSettings.dentTestResultsFolder}'):
            existingTestIds = glob(f'{globalSettings.dentTestResultsFolder}/*')

            # /home/dent/DentCiMgmt/TestBranches/09-01-2023-23-07-28
            for clonedTestRepoPath in glob(f'{self.ciVars.testBranchFolder}/*'):
                if self.ciVars.testIdTestingBranch == clonedTestRepoPath:
                    # Don't delete the current testing branch
                    continue

                clonedTestRepo = clonedTestRepoPath.split('/')[-1]

                if clonedTestRepo not in existingTestIds:
                    Utilities.runLinuxCmd(f'rm -rf {clonedTestRepoPath}', logObj=self.ciVars.sessionLog)
                else:
                    testIdOverallSummary = f'{globalSettings.dentTestResultsFolder}/{clonedTestRepo}/dtfOverallSummary.json'
                    if os.path.exists(testIdOverallSummary):
                        data = readJson(testIdOverallSummary)
                        pid = data['pid']

                        if Utilities.isPidRunning(pid, stdout=True) is False:
                            Utilities.runLinuxCmd(f'rm -rf {clonedTestRepoPath}', logObj=self.ciVars.sessionLog)
                    else:
                        # Something went wrong with the test session if there is no dtfOverallSummary.json file
                        # Remove the repo branch
                        Utilities.runLinuxCmd(f'rm -rf {clonedTestRepoPath}', logObj=self.ciVars.sessionLog)

    def cloneTestRepo(self):
        """
        STAGE 1: Git clone test repo to the /TestBranches folder
        and name it the testId
        """
        if self.ciVars.cloneTestRepo is False:
            return

        self.isGitCloneSafeToRun()
        # Avoid: No Such File or Directory (tmp_pack_XXXXXX)
        Utilities.runLinuxCmd('git config --global core.fscache false', logObj=self.ciVars.sessionLog)

        try:
            result = False
            cloneObj = GitCloneTestingRepo(self.ciVars)
            result = cloneObj.clone()

        except Exception as errMsg:
            self.ciVars.sessionLog.error(traceback.format_exc(None, errMsg))
            self.testbedMgmtObj.unlockTestbeds()
            Utilities.closeTestMgmtStatus(overallSummaryFile=self.ciVars.overallSummaryFile,
                                          status='aborted', result='failed', threadLock=self.ciVars.lock)
            Utilities.runDentCiTearDown(self.ciVars, 'Clone Dent test repo failed')

        if result:
            # Parse out all testbeds from test suite files and from the cloned repo
            for testSuite in self.ciVars.testSuites:
                contents = Utilities.readYaml(testSuite)
                # {'suiteGroups': {'runInSeries': [{'name': 'suite_group_clean_config',
                #   'config': './DentOsTestbed/configuration/testbed_config/sit_vm/testbed.json', 'suiteGroups': ['suite_group_clean_config']}]}}
                for suiteGroup in contents['suiteGroups'].get('runInSeries', []) + contents['suiteGroups'].get('runInParallel', []):
                    # config: ./DentOsTestbed/configuration/testbed_config/sit/testbed.json
                    config = suiteGroup['config']
                    matchRegex = search('.*/(DentOsTestbed/configuration/testbed_config/.+)', config)
                    if matchRegex:
                        # Ex: DentOsTestbed/configuration/testbed_config/sit/testbed.json
                        userDefinedSitPath = matchRegex.group(1)
                        # /home/dent/testing
                        configFullPath = f'{self.ciVars.testIdTestingBranch}/DentOS_Framework/{userDefinedSitPath}'
                        self.parseForTestbeds(configFullPath)

            sleep(3)
        else:
            # Cloning repo failed
            Utilities.closeTestMgmtStatus(overallSummaryFile=self.ciVars.overallSummaryFile,
                                          status='aborted', result='failed', threadLock=self.ciVars.lock)
            # This will unlocktestbed, remove testId test branch, create jenkinsCI result path
            Utilities.runDentCiTearDown(self.ciVars, 'Clone Dent test repo failed on clone verification')

        self.verifyIxNetworkVMFunctionality()

    def downloadBuilds(self):
        """
        STAGE 1: Download Dent build image to tftp server /srv/tftp
        """
        if self.ciVars.downloadNewBuilds is False:
            return

        downloadBuildsResults = downloadBuilds(self.ciVars)
        if downloadBuildsResults is False:
            self.testbedMgmtObj.unlockTestbeds()
            Utilities.runDentCiTearDown(self.ciVars, 'Download builds failed')

    def installDentOS(self):
        """
        STAGE 2: Install build on Dent
        """
        if self.ciVars.installDentOS is False:
            return

        stage = 'installDentOS'

        # Requires pulling the branch for testbed configs
        self.isTestIdTestBranchExists(stage=stage)
        updateDentResult = updateDent(self.ciVars)

        # Remove the downloaded build to clean up
        # Example: /DentBuildReleases/09-28-2023-16-25-52-377875_myDev3
        Utilities.runLinuxCmd(f'rm -rf {self.ciVars.downloadToServerFolder}')

        if updateDentResult is False:
            Utilities.closeTestMgmtStatus(overallSummaryFile=self.ciVars.overallSummaryFile,
                                          status='aborted', result='failed', threadLock=self.ciVars.lock)
            Utilities.runDentCiTearDown(self.ciVars, 'failed')

        self.ciVars.sessionLog.info(f'{stage}: passed')

    def deployIxNetwork(self, forceBringUp=False):
        """
        STAGE 2: Deploy IxNetwork
        """
        if self.ciVars.deployIxNetwork is False and forceBringUp is False:
            return

        deployIxNetworkResult = deployIxNetworkInit(ciVars=self.ciVars)
        if deployIxNetworkResult is False:
            Utilities.closeTestMgmtStatus(overallSummaryFile=self.ciVars.overallSummaryFile,
                                          status='aborted', result='failed', threadLock=self.ciVars.lock)
            Utilities.runDentCiTearDown(self.ciVars, 'failed')

        # Enable back the CI system for other test to run
        if os.path.exists(f'{globalSettings.dentCiMgmtPath}/{globalSettings.disableSystemFilename}'):
            Utilities.runLinuxCmd(f'rm {globalSettings.disableSystemFilename}',
                                  cwd=globalSettings.dentCiMgmtPath,
                                  logObj=self.ciVars.sessionLog)

    def deployDentTestContainers(self):
        """
        STAGE 2: Deploy test containers
        """
        if self.ciVars.deployDentTestContainers is False:
            return

        dentContainerObj = DeployTestContainers(self.ciVars.testContainersLogFile, self.ciVars)
        result = dentContainerObj.removeAndBuild()

        if result is False:
            Utilities.closeTestMgmtStatus(overallSummaryFile=self.ciVars.overallSummaryFile,
                                          status='aborted', result='failed', threadLock=self.ciVars.lock)
            Utilities.runDentCiTearDown(self.ciVars, 'failed')

    def runTest(self):
        """
        STAGE 3: Run test
        """
        if self.ciVars.runTest is False:
            return

        stage = 'runTest'

        # Verify if test branch exists
        self.isTestIdTestBranchExists(stage=stage)

        # Verify if Dent docker images are indeed running
        dentContainerObj = DeployTestContainers(self.ciVars.testContainersLogFile, self.ciVars)

        if dentContainerObj.isDockerImagesExists() is False:
            Utilities.updateStage(self.ciVars.overallSummaryFile, stage=stage, result='failed',
                                  status='aborted', error='Dent docker images are not running',
                                  threadLock=self.ciVars.lock)
            Utilities.closeTestMgmtStatus(overallSummaryFile=self.ciVars.overallSummaryFile,
                                          status='aborted', result='failed', threadLock=self.ciVars.lock)
            Utilities.runDentCiTearDown(self.ciVars, 'failed')

        runTestObj = TestMgmt(self.ciVars)
        testResult = runTestObj.overallTestResult

        self.ciVars.sessionLog.info(f'Test is done. Test result: {testResult}')
        Utilities.closeTestMgmtStatus(overallSummaryFile=self.ciVars.overallSummaryFile,
                                      status='completed', result=testResult, threadLock=self.ciVars.lock)

        if testResult == 'Passed':
            Utilities.runDentCiTearDown(self.ciVars)
        else:
            Utilities.runDentCiTearDown(self.ciVars, 'failed')


ciVars = CiVars()

try:
    DentCiArgParse(ciVars).parse()
    ci = DentCI(ciVars)
    ciVars.ciObj = ci

    # Stage 1
    threads = []
    if ciVars.cloneTestRepo:
        threads.append(Thread(target=ci.cloneTestRepo, name='cloneTestRepo'))

    if ciVars.downloadNewBuilds:
        threads.append(Thread(target=ci.downloadBuilds, name='downloadNewBuilds'))

    if threads:
        Utilities.runThreads(ciVars, threads)

    # Stage 2
    threads = []
    if ciVars.installDentOS:
        ci.installDentOS()
        # threads.append(Thread(target=ci.installDentOS, name='installDentOS'))

    if ciVars.deployIxNetwork:
        threads.append(Thread(target=ci.deployIxNetwork, name='deployIxNetwork'))

    if ciVars.deployDentTestContainers:
        threads.append(Thread(target=ci.deployDentTestContainers, name='deployDentTestContainers'))

    if threads:
        Utilities.runThreads(ciVars, threads)

    # Stage 3
    if ciVars.runTest:
        ci.runTest()

    # If in dev mode, it might not call runDentCiTearDown.
    # So call it to unlocktestbed
    if ciVars.exitCode is None:
        Utilities.runDentCiTearDown(ciVars)

except KeyboardInterrupt:
    Utilities.closeTestMgmtStatus(overallSummaryFile=ciVars.overallSummaryFile,
                                  status='ctrl-c aborted', result=None, threadLock=ciVars.lock)
    Utilities.runDentCiTearDown(ciVars, errorMsg='ctrl-c aborted')
    Utilities.runLinuxCmd(f'kill -9 {ciVars.pid}')

except Exception as errMsg:
    errorMsg = traceback.format_exc(None, errMsg)
    print(f'\nException error:\n\n{errorMsg}')
    if 'ci' in locals():
        ciVars.sessionLog.error(f'runDentCi exception: {errorMsg}')
        Utilities.closeTestMgmtStatus(overallSummaryFile=ciVars.overallSummaryFile,
                                      status='Aborted', result=None,
                                      updateProperties={'error': errorMsg},
                                      threadLock=ciVars.lock)
    Utilities.runDentCiTearDown(ciVars, errorMsg=errorMsg)

finally:
    print(f'\nrunDentCi sysexit({ciVars.exitCode})')
    sys.exit(ciVars.exitCode)
