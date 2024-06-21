import os
import sys
import subprocess
import yaml
import json
import traceback
import random
import string
from datetime import datetime
from time import sleep
from shutil import rmtree
from glob import glob
from re import search, findall
import socket


def getTimestamp(includeMillisecond: bool = True) -> str:
    now = datetime.now()

    if includeMillisecond:
        timestamp = now.strftime('%m-%d-%Y-%H:%M:%S:%f')
    else:
        timestamp = now.strftime('%m-%d-%Y-%H:%M:%S')

    return timestamp


def runLinuxCmd(command: str = None, cwd: str = None, logObj: object = None,
                showStdout: bool = True) -> list:
    from os import fdopen

    if logObj:
        logObj.info(f'\nrunLinuxCmd: {command}\n')

    capturedOutput = []
    with subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1,
                          cwd=cwd, text=True) as output:

        # Flush stdout
        # with fdopen(sys.stdout.fileno(), 'wb', closefd=False) as stdout:
        with fdopen(sys.stdout.fileno(), 'wb', closefd=False):
            for line in output.stdout:
                if showStdout:
                    print(line.strip())

                capturedOutput.append(line.strip())

    return capturedOutput


def readJson(jsonFile: str = None, threadLock: object = None) -> object:
    """
    Read JSON data

    :returns: JSON data
    """
    if threadLock:
        threadLock.acquire()

    counter = 1
    retry = 5
    while True:
        try:
            with open(jsonFile, mode='r', encoding='utf8') as jsonData:
                jsonData = json.load(jsonData)

            break
        except Exception as errMsg:
            if counter == retry:
                print(f'\nutilities: readJson failed on file: {jsonFile}:\nError: {errMsg}')
                raise Exception(errMsg)
                break
            else:
                counter += 1
                sleep(1)

    if threadLock:
        threadLock.release()

    return jsonData


def writeToJson(jsonFile: str = None, data: object = None, mode: str = 'w+',
                sortKeys: bool = False, indent: int = 4, threadLock: object = None) -> None:
    """
    Write data to JSON file. Use file lock to prevent collisions
    multithreaded.

    :param jsonFile: <str>: The .json file to write to.
    :param data: <dict>: The json data.
    :param mode: <str>: w|w+ append to the file
    :param retry: <int>: Number of times to retry.  Sometimes if multiple instances tries to access
                         the same file might clash.
    """
    if threadLock:
        threadLock.acquire()

    counter = 1
    retry = 5
    while True:
        try:
            with open(jsonFile, mode=mode, encoding='utf-8') as fileObj:
                json.dump(data, fileObj, indent=indent, sort_keys=sortKeys)

            break

        except Exception as errMsg:
            if counter == retry:
                print(f'\nwriteToJson failed: {jsonFile}: {errMsg}')
                raise (errMsg)
            else:
                print(f'\nwriteToJson failed/clashed: {errMsg}: {jsonFile}: retry {counter}/{retry}')
                counter += 1
                sleep(1)

    if threadLock:
        threadLock.release()


def readYaml(yamlFile: str = None, threadLock: object = None) -> object:
    """
    Read Yaml file. Use threadLock to prevent collision.
    """
    if threadLock:
        threadLock.acquire()

    counter = 1
    retry = 5
    while True:
        try:
            with open(yamlFile, mode='r', encoding='utf8') as yamlData:
                try:
                    # For yaml version >5.1
                    yamlData = yaml.load(yamlData, Loader=yaml.FullLoader)
                except yaml.YAMLError as exception:
                    # Show the Yaml syntax error
                    raise exception
                except Exception:
                    yamlData = yaml.safe_load(yamlData)

            break
        except Exception as errMsg:
            if counter == retry:
                print(f'readYaml failed: {errMsg}')
                raise (errMsg)
            else:
                counter += 1
                sleep(1)

    if threadLock:
        threadLock.release()

    return yamlData


def writeToYaml(data: object = None, yamlFile: str = None, mode: str = 'w', threadLock: object = None):
    """
    mode: w | w+
    """
    if threadLock:
        threadLock.acquire()

    counter = 1
    retry = 5
    while True:
        try:
            with open(yamlFile, mode) as fileObj:
                yaml.dump(data, fileObj, default_flow_style=False)

            break
        except Exception as errMsg:
            if counter == retry:
                print(f'utilities:writetoYamlFile failed: {errMsg}')
                raise Exception(errMsg)
            else:
                counter += 1
                sleep(1)

    if threadLock:
        threadLock.release()


def writeToFile(msg: str = None, filename: str = None, mode: str = 'a+',
                threadLock: object = None, printToStdout: bool = True) -> None:
    """
    Log message to file.

    :param mode: <str>: w = new, a+ = append to file.
    """
    if threadLock:
        threadLock.acquire()

    if printToStdout:
        print(f'{msg}\n')

    counter = 1
    retry = 5
    while True:
        try:
            with open(filename, mode=mode, encoding='utf-8') as msgFile:
                msgFile.write(f'{msg}\n')

            break
        except Exception as errMsg:
            if counter == retry:
                print(f'utilities:writeToFile failed: {errMsg}')
                raise Exception(errMsg)
            else:
                counter += 1
                sleep(1)

    if threadLock:
        threadLock.release()


def generatorRandom(size=6, chars=string.ascii_uppercase + string.digits):
    """
    generatorRandom() -> 'G5G74W'
    generatorRandom(3, "6793YUIO") -> 'Y3U'
    generatorRandom(6, 'ABCDEF')   -> 'DBBFFE'
    generatorRandom(6, 'abcdef')   -> 'eeadea'
    """
    return ''.join(random.choice(chars) for _ in range(size))


def runDentCiTearDown(ciVars: object, errorMsg: str = ''):
    # In case the testID test branch did not get removed
    if ciVars.deleteTestBranchAfterTest and os.path.exists(ciVars.testIdTestingBranch):
        try:
            ciVars.sessionLog.info(f'runDentCiTearDown: Removing testId test branch: {ciVars.testIdTestingBranch}')
            rmtree(ciVars.testIdTestingBranch)
        except Exeption:
            pass

    ciVars.sessionLog.info(f'runDentCiTearDown: removeDockerImage: {ciVars.dockerImageTag}')
    removeDockerImage(ciVars.dockerImageTag, ciVars.sessionLog)

    if ciVars.ciObj:
        ciVars.ciObj.testbedMgmtObj.unlockTestbeds()

    if ciVars.testName and ciVars.testName.startswith('jenkinsCI_'):
        ciVars.sessionLog.info(f'Recording result path: {ciVars.testSessionFolder}')
        recordCiTestResultPath(testName=ciVars.testName,
                               timestamp=ciVars.timestamp,
                               resultPathFile=ciVars.ciResultPathsFile,
                               resultPath=ciVars.testSessionFolder,
                               threadLock=ciVars.lock)

    # This informs the main script runDentCi how to exit
    if errorMsg:
        ciVars.exitCode = 1
    else:
        ciVars.exitCode = 0


def closeTestMgmtStatus(overallSummaryFile: str = None,
                        status: str = None, result: str = None, updateProperties: dict = None,
                        threadLock: object = None):
    """
    Update to close the test status

    status: completed|stopped
    result: completed|aborted
    """
    testMgmtData = readJson(overallSummaryFile, threadLock=threadLock)
    removeTestBranch = testMgmtData['deleteTestBranchAfterTest']
    if removeTestBranch:
        removeTestingRepo(testMgmtData['tempTestBranchPath'])

    startTime = testMgmtData['startTime']
    format = '%m-%d-%Y %H:%M:%S:%f'
    startTimeObj = datetime.strptime(startTime, format)

    testStopTime = datetime.now()
    testDuration = str(testStopTime - startTimeObj)
    testMgmtData.update({'stopTime': testStopTime.strftime('%m-%d-%Y %H:%M:%S:%f'),
                         'testDuration': testDuration,
                         'status': str(status).lower(),
                         'result': str(result).lower()})

    if updateProperties:
        testMgmtData.update(updateProperties)

    writeToJson(overallSummaryFile, testMgmtData, mode='w', threadLock=threadLock)


def updateStage(overallSummaryFile: str, stage: str,
                status: str = 'None', result: str = 'None',
                error: str = None, threadLock: object = None) -> None:
    """
    A helper function to update a CI stage
    """
    testMgmtData = readJson(overallSummaryFile, threadLock=threadLock)

    testMgmtData['stages'][stage].update({'status': str(status).lower(), 'result': str(result).lower()})
    if error is not None:
        testMgmtData['stages'][stage]['error'].append(error)

    writeToJson(overallSummaryFile, testMgmtData, mode='w', threadLock=threadLock)


def updateTestcaseSuiteTest(overallSummaryFile: str = None, suiteGroup: str = None,
                            updateProperties: dict = None, threadLock: object = None):
    """
    updateProperties: testMgmtData property/value to update
    """
    testMgmtData = readJson(overallSummaryFile, threadLock=threadLock)
    testMgmtData['testcases'][suiteGroup].update(updateProperties)
    writeToJson(overallSummaryFile, testMgmtData, mode='w', threadLock=threadLock)


def updateTestMgmtData(overallSummaryFile: str = None, updateProperties: dict = None, threadLock: object = None):
    """
    Updating the ciOverallSummary top-level data only
    updateProperties: testMgmtData property/value to update
    """
    testMgmtData = readJson(overallSummaryFile, threadLock=threadLock)
    testMgmtData.update(updateProperties)
    writeToJson(overallSummaryFile, testMgmtData, mode='w', threadLock=threadLock)


def removePastResults(folder, removeDaysOlderThan=3):
    """
    Remove past results/logs/artifacts. Self clean up the storage spacew.

    Examples:
       0 = Deleting starting with today
       1 = Keep today's. Delete yesterday and beyond
    """
    today = datetime.now()

    for root in glob(f'{folder}/*'):
        # /home/dent/DentTests/08-31-2023-17-37-41
        timestampFolder = root.split('/')[-1]

        # 10-06-2023-01-09-19-082399_myDev_l3tests
        matchRegex = search('([0-9]+-[0-9]+-[0-9]+)-[0-9]+-[0-9]+-[0-9]+.*', timestampFolder)
        if matchRegex:
            timestampFolderDate = matchRegex.group(1)
            format = '%m-%d-%Y'
            datetimeObj = datetime.strptime(timestampFolderDate, format)
            daysDelta = today.date() - datetimeObj.date()
            daysRecorded = daysDelta.days

            if int(daysRecorded) >= int(removeDaysOlderThan):
                try:
                    if os.path.exists(f'{root}/ciOverallSummary.json'):
                        overallSummary = readJson(f'{root}/ciOverallSummary.json')
                        pid = overallSummary['pid']
                        isPidExists = runLinuxCmd(f'pgrep {pid}', showStdout=False)

                        if len(isPidExists) == 0:
                            if os.path.isfile(root):
                                os.remove(root)

                            if os.path.isdir(root):
                                rmtree(root)

                except Exception as errMsg:
                    print(f'removePastResults error: {root}\n{errMsg}')


def removeBuildReleases(folder, removeDaysOlderThan=3):
    """
    Remove past Dent build releases

    Examples:
       0 = Deleting starting with today
       1 = Keep today's. Delete yesterday and beyond
    """
    today = datetime.now()

    for root in glob(f'{folder}/*'):
        # /home/dent/DentTests/08-31-2023-17-37-41
        timestampFolder = root.split('/')[-1]
        # 10-06-2023-01-09-19-082399_myDev_l3tests
        matchRegex = search('([0-9]+-[0-9]+-[0-9]+)-[0-9]+-[0-9]+-[0-9]+.*', timestampFolder)
        if matchRegex:
            timestampFolderDate = matchRegex.group(1)
            format = '%m-%d-%Y'
            datetimeObj = datetime.strptime(timestampFolderDate, format)
            daysDelta = today.date() - datetimeObj.date()
            daysRecorded = daysDelta.days

            if int(daysRecorded) >= int(removeDaysOlderThan):
                try:
                    print(f'Removing past Dent build release: {root}')
                    rmtree(root)

                except Exception as errMsg:
                    print(f'removeBuildReleases error: {root}\n{errMsg}')


def removeJenkinsCiOldResults(jenkinsCiResultFile: str, removeAfterDays: int, threadLock: object) -> None:
    """
    Remove the past <days> recorded result paths in ciJenkinsResultFile
    """
    if os.path.exists(jenkinsCiResultFile):
        today = datetime.now()
        data = readJson(jenkinsCiResultFile, threadLock=threadLock)
        indexListToRemove = []

        for index, resultPath in enumerate(data['results']):
            format = '%m-%d-%Y-%H-%M-%S-%f'
            # 09-26-2023-21-46-10-216597_jenkinsCI_devTest
            currentResultTimestamp = datetime.strptime(resultPath['timestamp'], format)
            daysDeltaObj = today.date() - currentResultTimestamp.date()
            daysDelta = daysDeltaObj.days

            if int(daysDelta) >= int(removeAfterDays):
                indexListToRemove.append(resultPath['timestamp'])

        if indexListToRemove:
            for oldResult in indexListToRemove:
                index = getDictIndexFromList(listOfDicts=data['results'], key='timestamp', value=oldResult)
                if index:
                    data['results'].pop(index)

            writeToJson(jenkinsCiResultFile, data, mode='w', threadLock=threadLock)


def removeTestingRepo(path):
    """
    Remove the testing branch
    """
    if os.path.exists(path):
        print(f'\nremoveTestingRepo: {path}')
        rmtree(path)


def getDictIndexFromList(listOfDicts, key, value):
    """
    Get the index of the dict object in a list that has key=value
    """
    for index, element in enumerate(listOfDicts):
        timestamp = element[key]
        if value == timestamp:
            return index


def getDictIndexList(listOfDicts, key, deepSearch=False):
    listOfIndexes = []
    for index, element in enumerate(listOfDicts):
        for item, values in element.items():
            if deepSearch is False:
                if item == key:
                    listOfIndexes.append({index: values})

            if deepSearch:
                for property, value in values.items():
                    if property == key:
                        listOfIndexes.append({item: value})

    return listOfIndexes


def runThreads(ciVars: object, threadList: list):
    """
    Start the Python threadlist and wait until all threads are done.
    """
    for eachThread in threadList:
        ciVars.sessionLog.info(f'runThread: Starting {eachThread.name}')
        eachThread.start()

    while True:
        # Reset and check all threads for complete again
        breakoutCounter = 0

        for eachJoinThread in threadList:
            ciVars.sessionLog.info(f'runThreads: Waiting for thread to complete: {eachJoinThread.name}')
            eachJoinThread.join()

            if eachJoinThread.is_alive():
                ciVars.sessionLog.info(f'runThreads: {eachJoinThread.name} is still alive')
            else:
                ciVars.sessionLog.info(f'runThreads: {eachJoinThread.name} alive == {eachJoinThread.is_alive}')
                breakoutCounter += 1

        if breakoutCounter == len(threadList):
            ciVars.sessionLog.info('runThreads: All threads are done')
            break
        else:
            continue


def sendEmail(emailTo, fromSender, subject, bodyMessage, emailAttachmentList=None):
    """
    postfix must be installed and the service must be running for emailing.

    Utilities.sendEmail('hubert.gee@keysight.com', 'dent@dentServer.com', 'Test Result', 'This is a test')
    """
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase  # zip file attachment
    from email import encoders  # zip file attachment
    from email.mime.multipart import MIMEMultipart
    from email.mime.application import MIMEApplication

    # plain | html
    body = MIMEText(bodyMessage, 'plain')
    msg = MIMEMultipart('alternative')
    msg['From'] = fromSender
    msg['To'] = emailTo
    msg['Subject'] = subject
    msg.attach(body)

    # fileAttachment is passed in as a list
    if emailAttachmentList:
        print(f'\nsendEmail() {emailAttachmentList}')
        for eachAttachment in emailAttachmentList:
            if eachAttachment is None:
                continue

            if '/' in eachAttachment:
                filename = eachAttachment.split('/')[-1]
            else:
                filename = eachAttachment

            if 'zip' in filename:
                # Note: Destination email server may not accept large zip file size such as 1MB
                attachment = MIMEBase('application', 'zip')
                attachment.set_payload(open(eachAttachment, 'rb').read())

                encoders.encode_base64(attachment)
                attachment.add_header('Content-Disposition', 'attachment', filename=f'{filename}.zip')
            else:
                attachment = MIMEApplication(open(eachAttachment, 'rb').read())
                attachment.add_header('Content-Disposition', 'attachment', filename=filename)

            msg.attach(attachment)

    try:
        print(f'\nSending email To:{emailTo} From:{fromSender} Subject:{subject}')
        # Linux machine must have postgres installed and started
        p = subprocess.Popen(['sendmail', '-t'], stdin=subprocess.PIPE, universal_newlines=True)
        p.communicate(msg.as_string())
    except Exception as errMsg:
        print(f'\nsendEmail() error: {errMsg}')


def getTestbeds(ciVars):
    """
    Get a list of all the testbeds by reading the test suite file(s)
    -> ['sit-testbed_09-13-2023-23-32-15-912060']
    """
    for testsuite in ciVars.testSuites:
        testSuiteDetails = readYaml(testsuite)

        for testConduct in ['runInParallel', 'runInSeries']:
            for test in testSuiteDetails['suiteGroups'].get(testConduct, []):
                # config: ./DentOsTestbed/configuration/testbed_config/basic_infra1/testbed.json
                #          /testbed_config/basic_infra1/testbed.json
                config = test['config'].split('configuration')[-1]

                regexMatch = search('testbed_config/(.+)', config)
                if regexMatch is False:
                    ciVars.sessionLog.error(f'getTestbeds: Expecting config pattern /testbed_config/<testbed_name>/testbed.json, but got pattern: {config}')
                    runDentCiTearDown(ciVars, errorMsg=True)

                # lockTestbed touches a testbed file that begins with sit/<testbed> (slash), but touch
                # errors out because it see's slashes as paths. Need to replace slashes with dashes
                testbedName = regexMatch.group(1).replace('/', '-')
                # Get a list of all the testId testbeds so the framework knows which testbed to unlock

                testbedNameWithTestId = f'{testbedName.split(".json")[0]}_{ciVars.testId}'
                if testbedNameWithTestId not in ciVars.testIdTestbeds:
                    ciVars.testIdTestbeds.append(testbedNameWithTestId)

    ciVars.sessionLog.info(f'Using testbeds: {ciVars.testIdTestbeds}')


def createCiResultPathFolder(dentCiMgmtPath: str, ciResultPathFolderName: str) -> None:
    if os.path.exists(f'{dentCiMgmtPath}/{ciResultPathFolderName}') is False:
        runLinuxCmd(f'mkdir {ciResultPathFolderName}', cwd=dentCiMgmtPath)


def recordCiTestResultPath(testName: str, timestamp: str, resultPath: str,
                           resultPathFile: str, threadLock: object) -> None:
    """
    Append new test result path to the json file
    """
    newResultPath = {'testName': testName, 'timestamp': timestamp, 'resultPath': resultPath}

    if os.path.exists(resultPathFile):
        data = readJson(resultPathFile)
        data['results'].append(newResultPath)
        writeToJson(jsonFile=resultPathFile, data=data, mode='w+', threadLock=threadLock)
    else:
        data = {'results': [newResultPath]}
        writeToJson(jsonFile=resultPathFile, data=data, mode='w', threadLock=threadLock)


def getDentCiRunningProcessIds(processName: str) -> list:
    """
    Get a list of all the process IDs based on the process name
    """
    pidList = []
    ps = subprocess.Popen('ps ax -o pid= -o args= ', shell=True, stdout=subprocess.PIPE)
    psPid = ps.pid
    output = ps.stdout.read()
    ps.stdout.close()
    ps.wait()

    for line in output.decode('utf-8').split('\n'):
        res = findall(r'(\d+) (.*)', line)
        if res:
            pid = int(res[0][0])
            if processName in res[0][1] and pid != os.getpid() and pid != psPid:
                pidList.append(str(pid))

    return pidList


def processExists(processName):
    """
    Check if a process name exists or active
    """
    ps = subprocess.Popen('ps ax -o pid= -o args= ', shell=True, stdout=subprocess.PIPE)
    psPid = ps.pid
    output = ps.stdout.read()
    ps.stdout.close()
    ps.wait()

    for line in output.decode('utf-8').split('\n'):
        res = findall(r'(\d+) (.*)', line)
        if res:
            pid = int(res[0][0])
            if processName in res[0][1] and pid != os.getpid() and pid != psPid:
                return True

    return False


def removeDockerImage(dockerTag: str, logObj: object):
    """
    Search for docker image tag. If a tag matches the keystack version,
    remove the docker image.

    REPOSITORY                 TAG                                     IMAGE ID       CREATED          SIZE
    dent/test-framework        CI-dentproject-testing-main             9eb2da646f95   24 minutes ago   897MB
    dent/test-framework        CI-localBranch-home-dent-testing-main   3ef4db5d132e   24 hours ago     897MB
    dent/test-framework-base   latest                                  1a91767e8243   44 hours ago     539MB
    """
    try:
        output = runLinuxCmd('docker images', logObj=logObj)

        for line in output:
            # REPOSITORY                 TAG       IMAGE ID       CREATED          SIZE
            # dent/test-framework-base   latest    160171bcc120   28 minutes ago   874MB
            match = search(f'[^ ]+ +{dockerTag} +([^ ]+) +', line)
            if match:
                dockerImageId = match.group(1)
                logObj.info(f'Removing Docker imageId for Tag={dockerTag}: {dockerImageId}')
                runLinuxCmd(f'docker rmi -f {dockerImageId}', logObj=logObj)
                return True

    except Exception as errMsg:
        logObj.error(f'removeDockerImage error: {traceback.format_exc(None, errMsg)}')
        return False


def isReachable(ipOrName, port, timeout=3):
    """
    If your server does not support ICMP (firewall might block it),
    it most probably still offers a service on a TCP port.
    In this case, you can perform a TCP ping (platform independently and
    without installing additional python modules) like this.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)

    try:
        s.connect((ipOrName, int(port)))
        s.shutdown(socket.SHUT_RDWR)
        return True
    except Exception:
        return False
    finally:
        s.close()


class CreateLogObj:
    """
    An object class to log various types of logs:
       info | warning | failed | error | debug
    """
    def __init__(self, logFile: str) -> None:
        self.logFile = logFile
        open(logFile, 'w').close()

    def info(self, msg: str, threadLock: object = None, noTimestamp: bool = False) -> None:
        if noTimestamp:
            writeToFile(msg, self.logFile, threadLock=threadLock)
        else:
            msg = f'{getTimestamp()}: [Info]: {msg}'
            writeToFile(msg, self.logFile, threadLock=threadLock)

    def warning(self, msg: str, threadLock: object = None) -> None:
        writeToFile(f'{getTimestamp()}: [Warning]: {msg}', self.logFile, threadLock=threadLock)

    def failed(self, msg: str, threadLock: object = None) -> None:
        writeToFile(f'{getTimestamp()}: [Failed]: {msg}', self.logFile, threadLock=threadLock)

    def error(self, msg: str, threadLock: object = None) -> None:
        writeToFile(f'{getTimestamp()}: [Error]: {msg}', self.logFile, threadLock=threadLock)

    def debug(self, msg: str, threadLock: object = None) -> None:
        writeToFile(f'{getTimestamp()}: [Debug]: {msg}', self.logFile, threadLock=threadLock)

    def abort(self, msg: str, threadLock: object = None) -> None:
        writeToFile(f'{getTimestamp()}: [Abort]: {msg}', self.logFile, threadLock=threadLock)
