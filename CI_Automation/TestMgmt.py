import sys
import traceback
import threading
from datetime import datetime

import Utilities
import globalSettings

"""
# Note: Added --mount /etc/* to run docker container as dent user
#       sudo -H -u dent

        cmd = f"docker run --rm --network host \
        --name suite_group_clean_config_$RUN_DATE \
        --mount src=$LOG_DIR,target=/DENT/reports,type=bind \
        --mount src=$LOG_DIR,target=/DENT/logs,type=bind \
        --mount src=/etc/passwd,target=/etc/passwd,type=bind,readonly \
        --mount src=/etc/group,target=/etc/group,type=bind,readonly \
        --mount src=/etc/shadow,target=/etc/shadow,type=bind,readonly \
        --mount src=/etc/gshadow,target=/etc/gshadow,type=bind,readonly \
        --mount src=/etc/localtime,target=/etc/localtime,type=bind,readonly \
        --user $(id -u ${USER}):$(id -g ${USER}) \
        -d dent/test-framework:$DENT_CONTAINER_TAG dentos_testbed_runtests \
        -d --stdout \
        --config ./DentOsTestbed/configuration/testbed_config/sit/testbed.json \
        --config-dir ./DentOsTestbed/configuration/testbed_config/sit/ \
        --suite-groups suite_group_clean_config \
        --discovery-reports-dir ./reports"

        cmd = f"docker run --rm --network host \
        --name suite_group_clean_config_$RUN_DATE \
        --mount src=$LOG_DIR,target=/DENT/reports,type=bind \
        --mount src=$LOG_DIR,target=/DENT/logs,type=bind \
        --mount src=/etc/passwd,target=/etc/passwd,type=bind,readonly \
        --mount src=/etc/group,target=/etc/group,type=bind,readonly \
        --mount src=/etc/shadow,target=/etc/shadow,type=bind,readonly \
        --mount src=/etc/gshadow,target=/etc/gshadow,type=bind,readonly \
        --mount src=/etc/localtime,target=/etc/localtime,type=bind,readonly \
        --user $(id -u ${USER}):$(id -g ${USER}) \
        -d dent/test-framework:CI \
        -d --stdout \
        --config ./DentOsTestbed/configuration/testbed_config/sit/testbed.json \
        --config-dir ./DentOsTestbed/configuration/testbed_config/sit/ \
        --suite-groups suite_group_clean_config \
        --discovery-reports-dir ./reports"

"""


class TestMgmt():
    def __init__(self, ciVars: object = None):
        self.lock = ciVars.lock
        self.dentCiFrameworkPath = globalSettings.dentCiFrameworkPath
        # Full path to test suite yml file
        self.testSuites = ciVars.testSuites
        self.testSuiteFolder = ciVars.testSuiteFolder
        # Testbed reservation
        self.testbedMgmtFolder = globalSettings.testbedMgmtFolder
        self.testbedWaitingFolder = globalSettings.testbedMgmtWaitingFolder
        # Test session folder: /home/dent/DentCiMgmt/TestResults/06-14-2024-16-18-45-420609
        self.testSessionFolder = ciVars.testSessionFolder
        # testIdTestingBranch: /path/DentCiMgmt/TestBranches/06-14-2024-16-18-45-420609_devMode
        self.testIdTestingBranch = ciVars.testIdTestingBranch
        # The Linux host logged in user running the test
        self.user = ciVars.user
        # Just the date-timestamp
        self.testId = ciVars.testId
        # dockerImageName is used for labeling the docker image: CI-<repoName>-<branchName>
        self.dockerImageTag = ciVars.dockerImageTag

        self.log = ciVars.sessionLog
        self.overallSummaryFile = ciVars.overallSummaryFile
        self.reportFile = ciVars.reportFile
        self.abortTestOnError = ciVars.abortTestOnError
        self.overallTestResult = 'None'
        self.testIdTestbeds = []
        self.setTestcases()
        self.isThereAnyResultInReport = None

        self.log.info(f'RunTest: testSuites={self.testSuites}')
        self.log.info(f'RunTest: logDir={self.testSessionFolder}')
        self.log.info(f'RunTest: testId={self.testId}')

        self.dockerRun = f'docker run --rm --network host \
        --name [dockerContainerName]_{self.testId} \
        --mount src={self.testSessionFolder},target=/DENT/reports,type=bind \
        --mount src={self.testSessionFolder},target=/DENT/logs,type=bind \
        --mount src=/etc/passwd,target=/etc/passwd,type=bind,readonly \
        --mount src=/etc/group,target=/etc/group,type=bind,readonly \
        --mount src=/etc/shadow,target=/etc/shadow,type=bind,readonly \
        --mount src=/etc/gshadow,target=/etc/gshadow,type=bind,readonly \
        --mount src=/etc/localtime,target=/etc/localtime,type=bind,readonly \
        --user $(id -u {self.user}):$(id -g {self.user}) \
        -d dent/test-framework:{self.dockerImageTag}  dentos_testbed_runtests \
        -d --stdout \
        --config [testbedJsonFile] \
        --config-dir [testbedPath] \
        --suite-groups [suiteGroups] \
        --discovery-reports-dir DISCOVERY_REPORTS_DIR \
        --discovery-reports-dir ./reports \
        --discovery-path ./DentOsTestbedLib/src/dent_os_testbed/discovery/modules/'

        self.runTestSuite()

    def setTestcases(self):
        """
        Metadata for all test cases

        self.testStartTime = datetime.now()
        self.testMgmt = {'startTime': self.testStartTime.strftime('%m-%d-%Y %H:%M:%S:%f'),
                         'stopTime': None,
                         'testDuration': None,
                         'result': None,
                         'user': self.user,
                         'logDir': self.testSessionFolder,
                         'status': 'Running',
                         'testcases': {}
                         }
        """
        testMgmtData = Utilities.readJson(self.overallSummaryFile, threadLock=self.lock)

        for testsuite in self.testSuites:
            testSuiteDetails = Utilities.readYaml(testsuite)

            for testConduct in ['runInParallel', 'runInSeries']:
                for test in testSuiteDetails['suiteGroups'].get(testConduct, []):
                    suiteGroup = test['name']
                    config = test['config'].split('configuration')[-1]
                    suiteGroups = test['suiteGroups']

                    # Get a list of all the testId testbeds so the framework knows which testbed to unlock
                    testbedName = config.split('testbed_config/')[-1].replace('/', '-')
                    testbedNameWithTestId = f'{testbedName.split(".json")[0]}_{self.testId}'
                    if testbedNameWithTestId not in self.testIdTestbeds:
                        self.testIdTestbeds.append(testbedNameWithTestId)

                    testMgmtData['testcases'][suiteGroup] = {}
                    testMgmtData['testcases'][suiteGroup].update({'testbed': None,
                                                                  'testConduct': testConduct,
                                                                  'config': config,
                                                                  'suiteGroups': suiteGroups,
                                                                  'additionalParams': test.get('additionalParams', None),
                                                                  'startTime': None,
                                                                  'stopTime': None,
                                                                  'testDuration': None,
                                                                  'aborted': False,
                                                                  'error': None,
                                                                  'status': 'Not-Started',
                                                                  'result': 'Not-Ready'
                                                                  })
        self.writeToOverallSummaryFile(testMgmtData)

    def writeToOverallSummaryFile(self, testMgmtData):
        """
        Update the overallSummary metadata file
        """
        Utilities.writeToJson(jsonFile=self.overallSummaryFile, data=testMgmtData, mode='w', threadLock=self.lock)

    def killTest(self, status):
        Utilities.closeTestMgmtStatus(overallSummaryFile=self.overallSummaryFile,
                                      status=status, result='None', threadLock=self.lock)
        Utilities.removeTestingRepo(self.testIdTestingBranch)
        Utilities.runLinuxCmd(f'kill -9 {self.testMgmtData["pid"]}', logObj=self.log)

    def report(self) -> str:
        """
        This report shows overall suite group result.
        But within each suite group has many testcases with results.
        """
        testResult = None

        # /path/DentCiMgmt/tools/test_utils.py
        result = Utilities.runLinuxCmd(f'{sys.executable} {globalSettings.dentToolsPath}/test_utils.py csv -d {self.testSessionFolder}',
                                       logObj=self.log)

        if result:
            report = ''
            # ['Name,Group,Subgroup,Status,Message', 'test_clean_config,basic_triggers,test_clean_config,pass,""']
            for index, line in enumerate(result):
                if not line:
                    continue

                line = line.split(',')

                if index == 0:
                    report += f'{"Name":25} {"Group":20} {"SubGroup":20} {"Report":20} {"Message":30}\n'
                    report += f'{"-"*96}\n'
                else:
                    if len(line) != 5:
                        continue

                    self.isThereAnyResultInReport = True
                    status = line[3]
                    # pass | failure
                    if status != 'pass':
                        testResult = 'failed'
                        self.overallTestResult = 'Failed'

                    report += f'{line[0]:25} {line[1]:20} {line[2]:20} {line[3]:20} {line[4]:30}\n'

            if self.isThereAnyResultInReport and testResult is None:
                testResult = 'passed'
            if self.isThereAnyResultInReport and testResult == 'failed':
                testResult = 'failed'
            if self.isThereAnyResultInReport is None and testResult is None:
                testResult = 'none'

            self.log.info(f'{report}', noTimestamp=True)
            Utilities.writeToFile(report, filename=self.reportFile, mode='w', printToStdout=False)

        return testResult

    def runTestSuite(self) -> None:
        """
        Create a list for runInParallel and runInSeries
        Runs both parallels and series in parallel
        """
        Utilities.updateStage(self.overallSummaryFile, stage='runTest', status='running',
                              result='not-ready', threadLock=self.lock)
        startTime = datetime.now()
        errorMsg = None
        aborted = False

        try:
            # Gather up a list of suite groups to test first
            for testsuite in self.testSuites:
                testSuiteDetails = Utilities.readYaml(testsuite)
                self.runInParallelList = testSuiteDetails['suiteGroups'].get('runInParallel', [])
                self.runInSeriesList = testSuiteDetails['suiteGroups'].get('runInSeries', [])

            threadList = []
            if self.runInParallelList:
                threadObj = threading.Thread(target=self.runInParallel, name='RunTestInParallel')
                threadList.append(threadObj)

            if self.runInSeriesList:
                threadObj = threading.Thread(target=self.runInSeries, name='RunTestInSeries')
                threadList.append(threadObj)

            for eachThread in threadList:
                self.log.info(f'Starting suite test: {eachThread.name} ...')
                eachThread.start()

            while True:
                # Reset and check all threads for complete again
                breakoutCounter = 0

                for eachJoinThread in threadList:
                    self.log.info(f'runTestSuites: Waiting for thread to complete: {eachJoinThread.name}')
                    eachJoinThread.join()

                    if eachJoinThread.is_alive():
                        self.log.info(f'runTestSuites: {eachJoinThread.name} is still alive')
                    else:
                        self.log.info(f'runTestSuites: {eachJoinThread.name} alive == {eachJoinThread.is_alive}')
                        breakoutCounter += 1

                if breakoutCounter == len(threadList):
                    self.log.info('runTestSuites: All threads are done')
                    break
                else:
                    continue

        except KeyboardInterrupt:
            aborted = True
            errorMsg = 'TestMgmt:runSuites: aborted by pressing CTRL-C'
            Utilities.updateStage(self.overallSummaryFile, stage='runTest', status='ctrl-c aborted',
                                  result='None', error=errorMsg, threadLock=self.lock)
            self.log.abort(errorMsg)

        except Exception as errMsg:
            aborted = True
            errorMsg = f'TestMgmt:runSuites: {traceback.format_exc(None, errMsg)}'
            Utilities.updateStage(self.overallSummaryFile, stage='runTest', status='running-error',
                                  result='None', error=errorMsg, threadLock=self.lock)
            self.log.error(errorMsg)
            print(f'runTestSuite error: {errorMsg}')

        finally:
            stopTime = datetime.now()
            testDeltaTime = str((stopTime - startTime))
            if aborted:
                status = 'aborted'
                self.overallTestResult = 'Aborted'
            else:
                status = 'completed'

            if status == 'completed':
                if self.isThereAnyResultInReport and self.overallTestResult not in ['Aborted', 'Failed']:
                    self.overallTestResult = 'Passed'

                if self.isThereAnyResultInReport and self.overallTestResult in ['Aborted', 'Failed']:
                    self.overallTestResult = 'Failed'

                if self.isThereAnyResultInReport is None:
                    self.overallTestResult = 'Failed'
                    errorMsg = 'There were no test case results hmtl files found in the test branch folder. No result.'

            self.report()
            Utilities.updateTestMgmtData(self.overallSummaryFile,
                                         {'status': status,
                                          'stopTime': stopTime.strftime('%m-%d-%Y %H:%M:%S:%f'),
                                          'testDuration': testDeltaTime,
                                          'error': errorMsg,
                                          'aborted': aborted,
                                          'result': self.overallTestResult
                                          },
                                         threadLock=self.lock)

            Utilities.updateStage(self.overallSummaryFile, stage='runTest', status=status,
                                  result=self.overallTestResult, error=None, threadLock=self.lock)

            if aborted and self.abortTestOnError:
                self.killTest(status='AbortTestOnError')

    def runInParallel(self) -> None:
        """
        Run test suites in parallel
        """
        threadList = []

        for suiteGroup in self.runInParallelList:
            threadObj = threading.Thread(target=self.runSuiteGroup, args=(suiteGroup,), name=suiteGroup['name'])
            threadList.append(threadObj)

        for eachThread in threadList:
            self.log.info(f'Starting suite group in parallel: {eachThread.name} ...')
            eachThread.start()

        while True:
            # Reset and check all threads for complete again
            breakoutCounter = 0

            for eachJoinThread in threadList:
                self.log.info(f'runInParallel: Waiting for thread to complete: {eachJoinThread.name}')
                eachJoinThread.join()

                if eachJoinThread.is_alive():
                    self.log.info(f'runInParallel: {eachJoinThread.name} is still alive')
                else:
                    self.log.info(f'runInParallel: {eachJoinThread.name} alive == {eachJoinThread.is_alive}')
                    breakoutCounter += 1

            if breakoutCounter == len(threadList):
                self.log.info('runInParallel: All threads are done')
                break
            else:
                continue

    def runInSeries(self) -> None:
        """
        Run test suites in series
        """
        for suiteGroup in self.runInSeriesList:
            self.runSuiteGroup(suiteGroup)

    def runSuiteGroup(self, suiteGroup: dict) -> None:
        try:
            currentDockerRunTemplate = self.dockerRun
            suiteName = suiteGroup['name']
            config = suiteGroup['config']
            errorMsg = None
            aborted = False

            if config:
                testbedName = config.split('testbed_config/')[-1].replace('/', '-')
            else:
                testbedName = None

            if 'configDir' in suiteGroup:
                configDir = suiteGroup['configDir']
            else:
                # Yank out the tailend /testbed.json
                if config:
                    configDir = '/'.join(config.split('/')[:-1])
                else:
                    configDir = 'None'

            if 'additionalParams' in suiteGroup:
                # Users could pass in PyTest parameters that flows through docker run command such as PyTest -k
                additionalDockerParametersForPyTest = suiteGroup['additionalParams']
                currentDockerRunTemplate += f' {additionalDockerParametersForPyTest}'

            suiteGroups = suiteGroup['suiteGroups']
            startTime = datetime.now()
            Utilities.updateTestcaseSuiteTest(self.overallSummaryFile, suiteName,
                                              {'status': 'running',
                                               'testbed': testbedName,
                                               'startTime': startTime.strftime('%m-%d-%Y %H:%M:%S:%f')},
                                              threadLock=self.lock)

            for wordReplacement in [('[dockerContainerName]', suiteName),
                                    ('[testbedJsonFile]', str(config)),
                                    ('[testbedPath]', str(configDir))]:
                currentDockerRunTemplate = currentDockerRunTemplate.replace(wordReplacement[0], wordReplacement[1])

            suiteGroupReplacements = ''
            for eachSuiteGroup in suiteGroups:
                suiteGroupReplacements += f'{eachSuiteGroup}'

            currentDockerRunTemplate = currentDockerRunTemplate.replace('[suiteGroups]', suiteGroupReplacements)
            self.log.info(currentDockerRunTemplate)

            self.log.info(f'Running test: {suiteName} ...')
            Utilities.runLinuxCmd(currentDockerRunTemplate, logObj=self.log)
            self.log.info(f'Wait for docker {suiteName}_{self.testId} to complete ...')
            Utilities.runLinuxCmd(f'docker wait {suiteName}_{self.testId}', logObj=self.log)

        except Exception as errMsg:
            aborted = True
            errorMsg = f'TestMgmt:runSuiteGroup: "{suiteName}": {traceback.format_exc(None, errMsg)}'
            Utilities.updateStage(self.overallSummaryFile, stage='runTest', status='error',
                                  result='None', error=errorMsg, threadLock=self.lock)
            self.log.error(errorMsg)
            self.overallTestResult = 'Aborted'
            print(f'runSuiteGroup error: {errorMsg}')

        finally:
            stopTime = datetime.now()
            testDeltaTime = str((stopTime - startTime))
            if aborted is False:
                status = 'completed'
            else:
                status = 'aborted'

            Utilities.updateTestcaseSuiteTest(self.overallSummaryFile, suiteName,
                                              {'status': status,
                                               'stopTime': stopTime.strftime('%m-%d-%Y %H:%M:%S:%f'),
                                               'testDuration': testDeltaTime,
                                               'aborted': aborted,
                                               'result': 'None'},
                                              threadLock=self.lock)
