import os
import Utilities

currentDir = os.path.abspath(os.path.dirname(__file__))


class GitCloneTestingRepo:
    def __init__(self, ciVars: object) -> None:
        self.repo = ciVars.repo
        self.branchName = ciVars.branchName
        self.testBranchFolder = ciVars.testBranchFolder
        # Where all the cloned repos are stored. The renamed cloned repo
        self.testIdTestingBranch = ciVars.testIdTestingBranch
        self.log = ciVars.sessionLog
        self.ciVars = ciVars
        self.lock = ciVars.lock

    def clone(self):
        Utilities.updateStage(self.ciVars.overallSummaryFile, stage='cloneTestRepo',
                              status='running', result='None', threadLock=self.lock)

        self.log.info(f'clone: testIdTestingBranch: {self.testIdTestingBranch}')

        # Create the TestBranch folder to hold all testId testing repos
        if os.path.exists(self.testBranchFolder) is False:
            Utilities.runLinuxCmd(f'mkdir -p {self.testBranchFolder}')
            Utilities.runLinuxCmd(f'chown -R dent:dent {self.testBranchFolder}', logObj=self.log)
            Utilities.runLinuxCmd(f'chmod -R 777 {self.testBranchFolder}', logObj=self.log)

            # Avoiding:
            #    error: could not lock config file /home/dent/TestBranches/09-15-2023-21-53-50-403070/.git/config:
            #    No such file or directory
            # fatal: could not set 'core.repositoryformatversion' to '0'
            Utilities.runLinuxCmd('git config --file=.git/config core.repositoryformatversion 1',
                                  cwd=self.testBranchFolder, logObj=self.log)

            # The reason of this issue may be the corruption of the file system cache.
            # In this case, we could try to execute following command:
            Utilities.runLinuxCmd('git config --global core.fscache false',
                                  cwd=self.testBranchFolder, logObj=self.log)

        Utilities.runLinuxCmd(f'mkdir -p {self.testIdTestingBranch}')
        Utilities.runLinuxCmd(f'chmod 770 {self.testIdTestingBranch}')

        if self.ciVars.localTestBranch:
            Utilities.runLinuxCmd(f'cp -r {self.ciVars.localTestBranch}/* {self.testIdTestingBranch}', logObj=self.log)
        else:
            if self.branchName:
                cmd = f'git clone --branch {self.branchName} {self.repo} {self.testIdTestingBranch}'
            else:
                cmd = f'git clone {self.repo} {self.ciVars.testId}'

            try:
                self.log.info(f'Cloning {self.repo} -> {self.testBranchFolder}/{self.ciVars.testId}')
                output = Utilities.runLinuxCmd(cmd, cwd=self.testBranchFolder, logObj=self.log)
            except Exception as errMsg:
                verified = False
                Utilities.updateStage(self.ciVars.overallSummaryFile, stage='cloneTestRepo',
                                      status='error', result='failed', error=errMsg, threadLock=self.lock)

                raise Exception(errMsg)

        if os.path.exists(self.testIdTestingBranch):
            self.log.info('Verify if cloned repo test branch has files in it')
            output = Utilities.runLinuxCmd('ls', cwd=self.testIdTestingBranch, logObj=self.log)
            if len(output) > 0:
                self.log.info('Verified cloned files')
                verified = True
                Utilities.updateStage(self.ciVars.overallSummaryFile, stage='cloneTestRepo',
                                      status='completed', result='passed', threadLock=self.lock)
            else:
                errorMsg = 'Cloned testing repo branch has no files in it!'
                self.log.failed(errorMsg)
                Utilities.updateStage(self.ciVars.overallSummaryFile, stage='cloneTestRepo',
                                      status='error', result='failed', error=errMsg, threadLock=self.lock)
                verified = False
        else:
            verified = False
            Utilities.updateStage(self.ciVars.overallSummaryFile, stage='cloneTestRepo',
                                  status='completed', result='failed', error=output, threadLock=self.lock)

        return verified
