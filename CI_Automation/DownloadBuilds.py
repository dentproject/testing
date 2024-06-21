import os
import requests
import threading
from re import search
from bs4 import BeautifulSoup
from datetime import datetime

import Utilities
import globalSettings


class DownloadBuilds:
    """
    This class is executed by downloadBuids at the bottom of this file.
    User could include the parameter -builds stating the builds to download or
    exclude the -builds parameter to automatically scrape for the latest builds
    """
    def __init__(self, ciVars: object):
        # /DentBuildReleases/<testId>
        self.downloadToServerFolder = ciVars.downloadToServerFolder
        self.srcBuildList = ciVars.builds
        self.ciVars = ciVars
        self.log = ciVars.sessionLog

        # Every test has its down testId folder to store the builds download
        # /DentBuildReleases/06-11-2024-19-34-49-119160_devMode
        Utilities.runLinuxCmd(f'mkdir -p {self.downloadToServerFolder}', logObj=self.log)
    '''
    def getPullRequestList(self):
        """
        curl -KL -X GET https://api.github.com/repos/dentProject/dentOS/pulls
        """
        import pandas
        from pprint import pprint

        page = 1
        pullRequestList = []

        while True:
            # state = open|closed|all
            #response = requests.get(f'https://api.github.com/repos/dentProject/dentOS/pulls?state=open&page={page}')
            response = requests.get(f'https://api.github.com/repos/dentProject/dentOS/pulls/233')
            if response.json() == []:
                break

            #for x in response.json():
            #    pprint(x)
            pprint(response.text)
            #pullRequestDataFrames = pandas.read_json(response.json()[0])
            #if pullRequestDataFrames:
            #    break

            page += 1
            break

        #df = pandas.concat(pullRequestList, axis='rows', ignore_index=True)
        #print('\n---- df:', df.to_string())

        #for req in pullRequestList:
        #    print(f'- {req}\n')
    '''

    def scrapeForLatestBuild(self, buildSrcPath: str):
        self.latestBuild = {'date': None, 'buildNumber': None, 'builds': []}
        self.log.info(f'scrapeForLatestBuild: buildSrcPath = {buildSrcPath}')
        response = requests.get(buildSrcPath)
        # hmtlPage = response.text
        soup = BeautifulSoup(response.text, 'html.parser')

        # Step 1/3: Get a list of all the builds and parse for the latest build date
        for link in soup.find_all('a', href=True):
            # print(link['href'])
            # https://repos.refinery.dev/repository/dent/snapshots/org/dent/dentos/dentos-verify-main/DENTOS-HEAD_ONL-OS10_2023-05-17.2235-63c7032_ARM64_INSTALLED_INSTALLER
            dateMatch = search('.*DENTOS-HEAD_.*_([0-9]+-[0-9]+-[0-9]+).*', link['href'])
            if dateMatch:
                dateFormat = '%Y-%m-%d'
                buildDate = dateMatch.group(1)
                buildDateObj = datetime.strptime(buildDate, dateFormat)
                if self.latestBuild['date'] is None:
                    self.latestBuild.update({'date': buildDate})
                else:
                    latestDateObj = datetime.strptime(self.latestBuild['date'], dateFormat)
                    if buildDateObj.date() > latestDateObj.date():
                        self.latestBuild.update({'date': buildDate})

        # Step 2/3: Parse for latest build number from the latest build dates
        for link in soup.find_all('a', href=True):
            # print('\n--- link:', link["href"])
            # https://repos.refinery.dev/repository/dent/snapshots/org/dent/dentos/dentos-verify-main/DENTOS-HEAD_ONL-OS10_2023-05-17.2235-63c7032_ARM64_INSTALLED_INSTALLER
            latestBuildMatch = search(rf'.*{self.latestBuild["date"]}\.([0-9]+)-.*INSTALLED_INSTALLER$', link['href'])
            if latestBuildMatch:
                buildNumber = latestBuildMatch.group(1)
                if self.latestBuild['buildNumber'] is None:
                    self.latestBuild.update({'buildNumber': buildNumber})
                else:
                    if int(self.latestBuild['buildNumber']) < int(buildNumber):
                        self.latestBuild.update({'buildNumber': buildNumber})

        # Step 3/3: Get the latest build number after the latest date
        for link in soup.find_all('a', href=True):
            # print(f'--- link: {link}')
            # https://repos.refinery.dev/repository/dent/snapshots/org/dent/dentos/dentos-verify-main/DENTOS-HEAD_ONL-OS10_2023-09-18.0854-94317c6_ARM64_INSTALLED_INSTALLER"

            # https://repos.refinery.dev/repository/dent/snapshots/org/dent/dentos/dentos-verify-main/DENTOS-HEAD_ONL-OS10_2023-07-27.0926-fa55378_AMD64_INSTALLED_INSTALLER
            latestBuildMatch = search(rf'.*{self.latestBuild["date"]}\.{self.latestBuild["buildNumber"]}-.*INSTALLED_INSTALLER$', link['href'])
            if latestBuildMatch:
                self.latestBuild['builds'].append(link['href'])

        self.log.info(f'Build date: {self.latestBuild["date"]}')
        self.log.info(f'Build number: {self.latestBuild["buildNumber"]}')
        self.log.info(f'Build builds: {self.latestBuild["builds"]}')

        data = Utilities.readJson(self.ciVars.overallSummaryFile)
        data.update({'buildDate': self.latestBuild['date'], 'buildNumber': self.latestBuild['buildNumber']})
        Utilities.writeToJson(jsonFile=self.ciVars.overallSummaryFile, data=data, mode='w', threadLock=self.ciVars.lock)

        if self.latestBuild['date'] is not None and \
           self.latestBuild['buildNumber'] is not None and \
           self.latestBuild['builds'] != []:
            return self.latestBuild['builds']
        else:
            return False

    def wgetBuild(self, srcBuild: str):
        # -c continue from an interruption
        Utilities.runLinuxCmd(f'wget --no-check-certificate --show-progress -c -P {self.downloadToServerFolder} {srcBuild}', logObj=self.log)
        Utilities.runLinuxCmd(f'sudo chmod -R 775 {self.downloadToServerFolder}')

    def downloadBuilds(self, scrapedBuildList: bool = False):
        """
        Download the builds to /srv/tftp
        """
        if scrapedBuildList:
            if len(self.ciVars.builds) > 0:
                self.srcBuildList = self.ciVars.builds
            else:
                self.srcBuildList = []

        buildList = []

        if len(self.srcBuildList) > 0:
            buildList = self.srcBuildList
        else:
            if len(self.latestBuild['builds']) > 0:
                buildList = self.latestBuild['builds']

        if len(buildList) == 0:
            self.log.error('No builds provided')
            return False

        threadList = []
        doOnce = True

        for srcBuild in buildList:
            buildName = srcBuild.split('/')[-1]
            downloadToDestPath = f'{self.downloadToServerFolder}/{buildName}'
            if 'ARM' in buildName:
                buildCpu = 'ARM'
            else:
                buildCpu = 'AMD'

            if doOnce:
                # buildName: DENTOS-HEAD_ONL-OS10_2023-09-20.1438-a00d7f6_ARM64_INSTALLED_INSTALLER
                matchReg = search(r'DENTOS.*_([0-9]+-[0-9]+-[0-9]+)\.([0-9]+)-.*', buildName)
                if matchReg:
                    data = Utilities.readJson(self.ciVars.overallSummaryFile)
                    data.update({'buildDate': matchReg.group(1), 'buildNumber': matchReg.group(2)})
                    Utilities.writeToJson(jsonFile=self.ciVars.overallSummaryFile, data=data, mode='w', threadLock=self.ciVars.lock)
                    doOnce = False

            self.log.info(f'Downloading build image: {srcBuild} ...')

            if os.path.exists(downloadToDestPath):
                self.log.info(f'There is an existing build with same filename. Removing {srcBuild} ...')
                os.remove(downloadToDestPath)

            # -c continue from an interruption
            # Utilities.runLinuxCmd(f'wget --show-progress -c -P {self.downloadToServerFolder} {srcBuild}', logObj=self.log)

            threadObj = threading.Thread(target=self.wgetBuild, args=(srcBuild,), name=buildCpu)
            threadList.append(threadObj)

        for eachThread in threadList:
            eachThread.start()

        while True:
            # Reset and check all threads for completeness again
            breakoutCounter = 0

            for eachJoinThread in threadList:
                self.log.info(f'DownloadBuilds: Waiting for thread to complete: {eachJoinThread.name}')
                eachJoinThread.join()

                if eachJoinThread.is_alive():
                    self.log.info(f'DownloadBuilds: {eachJoinThread.name} is still alive\n')
                else:
                    self.log.info(f'DownloadBuilds: {eachJoinThread.name} alive == {eachJoinThread.is_alive}\n')
                    breakoutCounter += 1

            if breakoutCounter == len(threadList):
                self.log.info('DownloadBuilds: All threads are done')
                break
            else:
                time.sleep(10)
                continue

        verifyOk = True
        for srcBuild in buildList:
            # Verify the download
            if os.path.exists(downloadToDestPath) is False:
                self.log.error(f'DownloadBuilds: Build was not downloaded successfully: {srcBuild}')
                verifyOk = False

        if verifyOk:
            self.log.info('All downloaded build existences were verified')
            return True
        else:
            return False

    def copyLocalBuildsToHttpServerTestIdFolder(self):
        print('\ncopyLocalBuildsToHttpServerTestIdFolder')
        for srcBuild in self.ciVars.localBuilds:
            buildName = srcBuild.split('/')[-1]
            downloadToDestPath = f'{self.downloadToServerFolder}/{buildName}'

            doOnce = True
            if doOnce:
                # buildName: DENTOS-HEAD_ONL-OS10_2023-09-20.1438-a00d7f6_ARM64_INSTALLED_INSTALLER
                matchReg = search(r'DENTOS.*_([0-9]+-[0-9]+-[0-9]+)\.([0-9]+)-.*', buildName)
                if matchReg:
                    data = Utilities.readJson(self.ciVars.overallSummaryFile)
                    data.update({'buildDate': matchReg.group(1), 'buildNumber': matchReg.group(2)})
                    Utilities.writeToJson(jsonFile=self.ciVars.overallSummaryFile, data=data, mode='w', threadLock=self.ciVars.lock)
                    doOnce = False

            Utilities.runLinuxCmd(f'cp {srcBuild} {downloadToDestPath}', logObj=self.log)


def downloadBuilds(ciVars: object) -> bool:
    """
    downloadToServerFolder: For http = /dentInstallations
                            For tftp = /srv/tftp
    """
    Utilities.updateStage(ciVars.overallSummaryFile, stage='downloadNewBuilds',
                          status='running', result=None, threadLock=ciVars.lock)
    downloadBuildsObj = DownloadBuilds(ciVars)
    srcBuildList = ciVars.builds

    if ciVars.localBuilds:
        downloadBuildsObj.copyLocalBuildsToHttpServerTestIdFolder()
        Utilities.updateStage(ciVars.overallSummaryFile, stage='downloadNewBuilds',
                              status='completed', result='passed', threadLock=ciVars.lock)
        return True

    if ciVars.builds == []:
        # User did not provide builds. Scrape for the latest builds from the main branch in github
        srcBuildList = downloadBuildsObj.scrapeForLatestBuild(globalSettings.downloadBuildUrlPrefixPath)
        ciVars.builds = srcBuildList
        ciVars.sessionLog.info(f'scrapeForLatestBuilds: {srcBuildList}')
        data = Utilities.readJson(ciVars.overallSummaryFile)
        data.update({'builds': srcBuildList})
        Utilities.writeToJson(ciVars.overallSummaryFile, data, mode='w', threadLock=ciVars.lock)

    if ciVars.builds:
        # User provided builds. Download them and verify for existence.
        downloadBuildResult = downloadBuildsObj.downloadBuilds(scrapedBuildList=True)
        if downloadBuildResult is False:
            Utilities.updateStage(ciVars.overallSummaryFile, stage='downloadNewBuilds',
                                  status='stopped', result='failed', threadLock=ciVars.lock)

            Utilities.closeTestMgmtStatus(overallSummaryFile=ciVars.overallSummaryFile,
                                          status='stopped', result='failed', threadLock=ciVars.lock)
            return False
        else:
            Utilities.updateStage(ciVars.overallSummaryFile, stage='downloadNewBuilds',
                                  status='completed', result='passed', threadLock=ciVars.lock)
            return True
