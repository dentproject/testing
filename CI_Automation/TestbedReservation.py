import os
from re import search
from glob import glob
from time import sleep
from datetime import datetime

import Utilities
import globalSettings


class ManageTestbed:
    def __init__(self, ciVars: object):
        self.ciVars = ciVars
        self.log = ciVars.sessionLog
        self.testbedMgmtFolder = globalSettings.testbedMgmtFolder
        self.testbedWaitingFolder = globalSettings.testbedMgmtWaitingFolder
        self.testIdTestbeds = ciVars.testIdTestbeds

    def isTestPidRunning(self, pid: str):
        isPidExists = Utilities.getDentCiRunningProcessIds(processName='testSuite')

        if str(pid) in isPidExists:
            return True
        else:
            return False

    def lockTestbed(self, testbed: str) -> None:
        """
        testbed: Just the name of the testbed without the testId (sit-testbed.json)

        This function will touch a file and append the testId to the testbed name
        to show who is using the testbed
        """
        self.log.info(f'lockTestbed: {self.testbedMgmtFolder}/{testbed}')
        Utilities.runLinuxCmd(f'touch {testbed}', cwd=self.testbedMgmtFolder, logObj=self.log)

    def unlockTestbeds(self) -> None:
        # ['sit-testbed_09-08-2023-21-49-17-278760_<testSessionName>]
        for testbed in self.testIdTestbeds:
            testbedPath = f'{self.testbedMgmtFolder}/{testbed}'

            try:
                if os.path.exists(testbedPath):
                    self.log.info(f'UnlockTestbed: {testbed}')
                    os.remove(testbedPath)

            except Exception:
                self.log.error(f'UnlockTested: Failed: {testbed}')

    def removeFromWaitingQueue(self, testbed):
        testbedTestId = f'{self.testbedWaitingFolder}/{testbed}'
        if os.path.exists(testbedTestId):
            self.log.info(f'removeTestbedFromWaitingQueue: {testbedTestId}')
            os.remove(testbedTestId)

    def getNextTestIdInTestbedQueue(self, requiredTestbed: str):
        """
        Check date/timestamp to see who is next to use the testbed

        requiredTestbed:
        """
        testbeds = glob(f'{self.testbedWaitingFolder}/*')
        if len(testbeds) == 0:
            return True

        waitingListDateTime = []

        for testbed in testbeds:
            # sit-testbed_09-08-2023-17-54-47-780586_<testName>
            # sit-testbed_09-14-2023-15-50-31-007677
            testbedTestIdFilename = testbed.split('/')[-1]

            matchRegex = search('(.*)_([0-9]+-[0-9]+-[0-9]+-[0-9]+-[0-9]+-[0-9]+-[0-9]+)(_.*)?', testbedTestIdFilename)
            if matchRegex:
                format = '%m-%d-%Y-%H-%M-%S-%f'
                testbedName = matchRegex.group(1)

                # 09-08-2023-17-48-18-217537_<testName>
                timestamp = matchRegex.group(2)
                datetimeObj = datetime.strptime(timestamp, format)

                # There could be many different testbeds in the waiting queue.
                # User specified the required testbed
                # Get a list of all the testIds waiting for the same testbed.
                if bool(search(f'.*{testbedName}.*', requiredTestbed)):
                    if len(waitingListDateTime) == 0:
                        waitingListDateTime.append((timestamp, testbedTestIdFilename))
                    else:
                        currentlyLowestDatetimeObj = datetime.strptime(waitingListDateTime[0][0], format)
                        if datetimeObj < currentlyLowestDatetimeObj:
                            waitingListDateTime[0] = (timestamp, testbedTestIdFilename)

        if waitingListDateTime:
            # Return the full testbed + testId filename
            # sit-testbed_09-07-2023-20-38-41_testName
            testIdWaiting = waitingListDateTime[0][1]
        else:
            testIdWaiting = None

        self.log.info(f'getNextTestIdInTestbedQueue: Next in line waiting: {testIdWaiting}')
        return testIdWaiting

    def goToTestbedQueue(self, testbed):
        """
        Put testId into waiting queue for a testbed
        """
        if os.path.exists(self.testbedWaitingFolder) is False:
            Utilities.runLinuxCmd(f'mkdir -p {self.testbedWaitingFolder}', logObj=self.log)

        # Append the testId to the testbed filename to show who is waiting.
        # Ex: sit-testbed_09-07-2023-20-38-41_testName
        self.log.info(f'goToTestbedQueue: {testbed}')
        Utilities.runLinuxCmd(f'touch {testbed}', cwd=self.testbedWaitingFolder, logObj=self.log)

    def isTestbedLocked(self, testbed: str) -> bool:
        """
        testbed: Just the name of the testbed without the testId (sit-testbed.json)

        Check the TestbedMgmt folder for the testbed.
        If the testbed name matches, it's being used.
        """
        self.log.info(f'I need this testbed {testbed}')
        # Search for just the testbed name. If exists, it's being used.
        # Ex: sit-testbed_09-07-2023-20-38-41_testName
        regexMatch = search('(^.+)_[0-9]+-[0-9]+-[0-9]+-[0-9]+-[0-9]+-[0-9]+.+', testbed)
        testbedName = regexMatch.group(1)

        self.log.info(f'Looking into TestbeMgmt folder for testbed:{testbedName} -> {self.testbedMgmtFolder}/{testbedName}')

        currentTestbedsInUse = glob(f'{self.testbedMgmtFolder}/{testbedName}*')
        selfCleanUp = False

        if len(currentTestbedsInUse) == 0:
            self.log.info(f'isTestbedLocked: The testbed {testbedName} is not in use. Returning false')
            return False
        else:
            self.log.info(f'The testbed is currently locked by testId: {currentTestbedsInUse}')

        # Check for the specified testbed name
        # If any exist, check if it's running by the PID.
        for testbedInUse in currentTestbedsInUse:
            # testbed: /home/dent/DentCiMgmt/TestbedMgmt/sit-testbed_09-26-2023-15-45-28-689235_myDev
            matchRegex = search('.*_([0-9]+-[0-9]+-[0-9]+-[0-9]+-[0-9]+-[0-9]+-[0-9]+.+)', testbedInUse)
            testId = matchRegex.group(1)

            # /home/dent/DentCiMgmt/TestResults/09-26-2023-17-42-03-894011_myDev
            testIdUsingTestbed = f'{globalSettings.dentTestResultsFolder}/{testId}'
            testbedTestId = testbed.split('/')[-1]

            # Check the currently reserved testId if it's really actively running by
            # looking at pgrep $pid
            testIdOverallSummaryFile = f'{testIdUsingTestbed}/ciOverallSummary.json'

            if os.path.exists(testIdOverallSummaryFile) is False:
                self.log.info(f'isTestbedLocked: {testbedInUse}. No ciOverallSummary file found. Unlocking tested')
                os.remove(testbedInUse)
            else:
                testIdData = Utilities.readJson(testIdOverallSummaryFile)
                pid = testIdData['pid']

                if self.isTestPidRunning(pid):
                    # The testbed is indeed active and being used
                    self.log.info(f'\nisTestbedlocked: {testbedName} is currently running and is Locked by {testbedTestId}')
                    return True
                else:
                    self.log.info(f'\nisTestbedlocked: {testbedName} is currently not in used and is Locked. Unlocking testbed from testId: {testbed}')
                    try:
                        os.remove(testbedInUse)
                        selfCleanUp = True
                    except Exception:
                        self.log.error(f'Failed to unlock testbed: {testbedInUse}')
                        selfCleanUp = False

        if selfCleanUp:
            # Freed up the unused tested
            self.log.info(f'The testbed is freed for usage: {testbedName}')
            return False

    def waitForTestbeds(self):
        """
        Wait for all the required testbeds before starting the test
        """
        if os.path.exists(self.testbedMgmtFolder) is False:
            Utilities.runLinuxCmd(f'mkdir -p {self.testbedMgmtFolder}')

        iAmWaitingForTestbeds = []

        # self.testIdTestbeds: These are testIds I need to use.
        #    Ex: ['sit-testbed_09-08-2023-21-49-17-278760_<testSessionName>]
        for eachTestbed in self.testIdTestbeds:
            isLocked = self.isTestbedLocked(eachTestbed)
            self.log.info(f'waitForTestbed: Required testbed: {eachTestbed} -> isLocked: {isLocked}')
            if isLocked:
                self.goToTestbedQueue(eachTestbed)
                iAmWaitingForTestbeds.append(eachTestbed)
            else:
                self.lockTestbed(eachTestbed)

        if len(iAmWaitingForTestbeds) == 0:
            # None of the testbeds I want to use are in the waiting queue.
            # Testbeds are freed for usage
            return True

        showOnce = True
        showOnce2 = True
        # Wait for all testbeds availability before starting test
        while True:
            # These are testbeds the test is waiting for
            for iAmWaitingForThisTestbed in iAmWaitingForTestbeds:
                isLocked = self.isTestbedLocked(iAmWaitingForThisTestbed)
                if showOnce2:
                    self.log.info(f'waitForTestbeds: {iAmWaitingForThisTestbed} is locked: {isLocked}')
                else:
                    print(f'print waitForTestbeds: {iAmWaitingForThisTestbed} is locked: {isLocked}')

                if isLocked is False:
                    print('print waitForTestbeds:  isLocked is False.  Calling getNextTestInLine')
                    # nextInLineForTheTestbed: sit-testbed_09-27-2023-15-37-20-331756_myDev
                    nextInLineForTheTestbed = self.getNextTestIdInTestbedQueue(iAmWaitingForThisTestbed)

                    # nextInLineForTheTestbed: sit-testbed_09-14-2023-16-22-01-266139  Iam: sit-testbed_09-14-2023-16-22-01-266139
                    if nextInLineForTheTestbed == iAmWaitingForThisTestbed:
                        self.lockTestbed(nextInLineForTheTestbed)
                        self.removeFromWaitingQueue(nextInLineForTheTestbed)

                        # Update the current waiting list
                        index = iAmWaitingForTestbeds.index(nextInLineForTheTestbed)
                        iAmWaitingForTestbeds.pop(index)
                    else:
                        # Testbed is not lock and I am not next. Check if other waiting test IDs are still
                        # actively running.
                        self.log.info('waitForTestbeds: Testbed is not locked and I am not next. Checking if next in line is actively running')
                        regexMatch = search('.*_([0-9]+-[0-9]+-[0-9]+-[0-9]+-[0-9]+-[0-9]+-[0-9]+[^ ]+)', nextInLineForTheTestbed)
                        if regexMatch:
                            testId = regexMatch.group(1)
                            nextInLineTestIdDirectory = f'{globalSettings.dentTestResultsFolder}/{testId}'

                            self.log.info(f'Verifying TestId: {testId}')
                            if os.path.exists(nextInLineTestIdDirectory) is False:
                                # The testId doesn't exists.  Safe to remove testId from testbedMgmt waitlist
                                self.log.info('waitForTestbeds: nextInLine testId does not exists anymore. Removing from the waitlist')
                                self.removeFromWaitingQueue(nextInLineForTheTestbed)
                            else:
                                isPidExists = Utilities.getDentCiRunningProcessIds(processName='testSuite')

                                if isPidExists:
                                    # Next-in-line is still active.
                                    pass
                                else:
                                    self.log.info('Next-in-line testId is not actively running. Removing it from the waitlist')
                                    self.removeFromWaitingQueue(nextInLineForTheTestbed)

            if showOnce is False:
                showOnce2 = False

            if len(iAmWaitingForTestbeds) > 0:
                if showOnce:
                    self.log.info(f'waitForTestbeds: My testId is waiting for testbeds: {iAmWaitingForTestbeds}')
                    showOnce = False

                sleep(3)
            else:
                break

        self.log.info('waitForTestbeds: All testbeds are locked and ready')
