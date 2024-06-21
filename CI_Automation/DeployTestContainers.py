import os
import re
import Utilities


class DeployTestContainers:
    def __init__(self, testContainersLogFile: str, ciVars: object):
        self.ciVars = ciVars
        self.overallSummaryFile = ciVars.overallSummaryFile
        self.lock = ciVars.lock
        self.dentContainerTag = None
        self.log = Utilities.CreateLogObj(testContainersLogFile)
        self.sessionLog = ciVars.sessionLog
        self.dockerImageName = 'dent/test-framework'
        self.dockerImageNameBase = 'dent/test-framework-base'
        # Each test gets a new clone to: /<baseDir>/TestBranches/<testId>
        self.testIdTestingBranch = ciVars.testIdTestingBranch

    def removeAndBuild(self) -> str:
        """
        Returns container tag | None (as failed)
        """
        stage = 'deployDentTestContainers'

        Utilities.updateStage(self.overallSummaryFile, stage=stage,
                              status='running', result=None, threadLock=self.lock)

        self.buildContainerImages()

        if self.dentContainerTag is False:
            errorMsg = 'failed: Getting dent test docker image container ID'
            Utilities.updateStage(self.overallSummaryFile, stage=stage,
                                  status='aborted', result='failed', threadLock=self.lock, error=errorMsg)
            return False

        # Verify
        # docker images
        # REPOSITORY                 TAG                                     IMAGE ID       CREATED          SIZE
        # dent/test-framework        CI-dentproject-testing-main             de9c1f2bd920   29 seconds ago   897MB
        # dent/test-framework        CI-localBranch-home-dent-testing-main   3ef4db5d132e   16 minutes ago   897MB
        # dent/test-framework-base   latest                                  1a91767e8243   21 hours ago     539MB

        if self.isDockerImagesExists():
            Utilities.updateStage(self.overallSummaryFile, stage=stage,
                                  status='completed', result='passed', threadLock=self.lock)
            self.sessionLog.info(f'dentContainerTag: {self.ciVars.dockerImageTag}')
            return True
        else:
            errorMsg = 'Dent test docker images not found'
            Utilities.updateStage(self.overallSummaryFile, stage=stage,
                                  status='aborted', result='failed',
                                  threadLock=self.lock, error="Dent docker images don't exist")
            return False

    def isDockerImagesExists(self):
        output = Utilities.runLinuxCmd('docker images')
        image1Exists = False
        image2Exists = False

        for line in output:
            # REPOSITORY                 TAG                                     IMAGE ID       CREATED          SIZE
            # dent/test-framework        CI-dentproject-testing-main             de9c1f2bd920   29 seconds ago   897MB
            # dent/test-framework        CI-localBranch-home-dent-testing-main   3ef4db5d132e   16 minutes ago   897MB
            # dent/test-framework-base   latest                                  1a91767e8243   21 hours ago     539MB

            if bool(re.search(f'^{self.dockerImageName} +{self.ciVars.dockerImageTag} +([^ ]+)', line)):
                image1Exists = True

            if bool(re.search(f'^{self.dockerImageNameBase} +latest +([^ ]+)', line)):
                image2Exists = True

        if image1Exists and image2Exists:
            return True
        else:
            return False

    def buildContainerImages(self):
        if os.path.exists(self.testIdTestingBranch):
            self.log.info(f'Located testId testing branch: {self.testIdTestingBranch}')
        else:
            self.log.error(f"TestId test branch doesn't exists: {self.testIdTestingBranch}")
            return False

        self.log.info('build the dent framework container if there is a need for it')
        self.log.info('optional step just a perf optimization so we dont build the container every time, build only if there is a change')

        # REPOSITORY                 TAG                                     IMAGE ID       CREATED          SIZE
        # dent/test-framework        CI-dentproject-testing-main             de9c1f2bd920   29 seconds ago   897MB
        # dent/test-framework        CI-localBranch-home-dent-testing-main   3ef4db5d132e   16 minutes ago   897MB
        # dent/test-framework-base   latest                                  1a91767e8243   21 hours ago     539MB

        # dent/test-framework-base
        # docker build -f /home/dent/DentCiMgmt/TestBranches/10-03-2023-22-08-54-156086_myDev/DentOS_Framework/Dockerfile.base
        # -t dent/test-framework-base:latest /home/dent/DentCiMgmt/TestBranches/10-03-2023-22-08-54-156086_myDev/DentOS_Framework
        self.log.info(f'Building docker image from {self.testIdTestingBranch}/DentOS_Framework/Dockerfile.base')
        cmd = f'docker build -f {self.testIdTestingBranch}/DentOS_Framework/Dockerfile.base '
        cmd += f'-t {self.dockerImageNameBase}:latest {self.testIdTestingBranch}/DentOS_Framework'
        Utilities.runLinuxCmd(cmd, logObj=self.log)

        # dent/test-framework
        # docker build --no-cache -f /home/dent/DentCiMgmt/TestBranches/10-03-2023-22-08-54-156086_myDev/DentOS_Framework/Dockerfile.auto
        # -t dent/test-framework-CI-dentproject-testing-main-abcdef /home/dent/DentCiMgmt/TestBranches/10-03-2023-22-08-54-156086_myDev/DentOS_Framework
        self.log.info('Building auto image')
        # ciVars.dockerImageTag=CI-<repoName>-<branchName>-<6randomLetters>
        cmd = f'docker build --no-cache -f {self.testIdTestingBranch}/DentOS_Framework/Dockerfile.auto '
        cmd += f'-t {self.dockerImageName}:{self.ciVars.dockerImageTag} {self.testIdTestingBranch}/DentOS_Framework'
        Utilities.runLinuxCmd(cmd, logObj=self.log)

        # Remove all <none> images
        # Especially if user is creating docker images with same tag name.
        # The old image becomes <none>
        # However, docker images with tag=latest will not get overwitten because latest is default
        Utilities.runLinuxCmd('docker rmi $(docker images --filter "dangling=true" -q --no-trunc)')

        self.log.info('Build dent docker test images are done')
