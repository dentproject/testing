"""
Spin up an IxNetwork VM

Requirements:
   - The Linux host server must be configured as a DHCP server
   - The DHCP server will assign a specific IP address for the IxNetwork VM
     based on the Mac Address

     Edit: /etc/dhcp/dhcpd.conf
     host ixnetwork {
        hardware ethernet 00:1a:c5:00:00:12;
        fixed-address 10.36.118.111;
     }

Generate notes and steps:
   # Deploy IxNetwork client or dockers or windows (as long as it's automated)
   echo 'start ixnetwork container'
   echo 'stop the vm'
   virsh shutdown IxNetwork-930
   echo 'wait 10 sec'
   sleep 10
   echo 'remove the vm'
   virsh undefine IxNetwork-930
   cd /vms
   echo 'remove existing vm hdd'
   rm -f ./IxNetworkWeb_KVM_9.30.2212.22.qcow2
   echo 'untar the vm image'
   tar xf IxNetworkWeb_KVM_9.30.2212.22.qcow2.tar.bz2 --use-compress-program=lbzip2
   echo 'deploy the vm'
   virt-install --name IxNetwork-930 --memory 32000 --vcpus 16 --disk /vms/IxNetworkWeb_KVM_9.30.2212.22.qcow2,bus=sata \
   --import --os   -variant centos7.0 --network bridge=br1,model=virtio,mac=00:1a:c5:00:00:12 --noautoconsole
   echo 'start the vm'
   virsh autostart IxNetwork-930
   virsh start IxNetwork-930

Debug:
   virsh console IxNetwork-9.30
"""
import os
import time
import Utilities
from re import search
from shutil import rmtree

import globalSettings


class DeployIxNetwork:
    def __init__(self, ixNetworkVMFolder: str, logObj: object) -> None:
        # IxNetworkLobFile object
        self.log = logObj
        self.initPassed = True

        # https://downloads.ixiacom.com/support/downloads_and_updates/public/ixnetwork/9.30/IxNetworkWeb_KVM_9.30.2212.22.qcow2.tar.bz2'
        self.downloadRelease = globalSettings.ixNetworkVMImage

        # /home/dent/IxNetworkVMs
        self.ixNetworkVMFolder = ixNetworkVMFolder

        # Before downloading new IxNetwork installation file, mv the current IxNetworkVM
        # folder to IxNetworkVM_backup. In case if the download or installation fails,
        # mv the IxNetworkVM_backup back to IxNetworkVM
        self.ixNetworkVMFolderBackup = f'{ixNetworkVMFolder}_backup'

        # IxNetworkWeb_KVM_9.30.2212.22.qcow2.tar.bz2
        self.releaseFilename = self.downloadRelease.split('/')[-1]

        # qcow2: IxNetworkWeb_KVM_9.30.2212.22.qcow2
        self.qcow2 = self.releaseFilename.split('.tar.bz2')[0]

        self.localIxNetworkQcow2Path = f'{self.ixNetworkVMFolder}/{self.qcow2}'

        # /home/dent/DentCiMgmt/IxNetworkVMs/IxNetworkWeb_KVM_9.30.2212.22.qcow2.tar.bz2
        self.localIxNetworkVMTarPath = f'{self.ixNetworkVMFolder}/{self.releaseFilename}'

        # Parse for 9.30
        matchRegex = search(r'.*KVM_([0-9]+\.[0-9]+)\..*', self.releaseFilename)
        if matchRegex:
            self.vmName = f'IxNetwork-{matchRegex.group(1)}'
        else:
            self.log.error('DeployIxNetwork: Failed to parse release for release version: {self.releaseFilename}')
            self.initPassed = False

    def isIxNetworkVMExists(self) -> bool:
        vmExists = False

        # Attempt to verify up to 5 times. Sometimes this command
        # is either delayed or doesn't show anything
        for counter in range(0, 5):
            output = Utilities.runLinuxCmd('virsh list', logObj=self.log)
            self.log.info(f'isNetworkVMExists: Verifying {counter}/5x: {output}')

            if output:
                for line in output:
                    if bool(search(f'.*{self.vmName}.*', line)):
                        self.log.info(f'isIxNetworkVMExists: {self.vmName} exists')
                        return True

            time.sleep(.5)

        self.log.info(f'isIxNetworkVMExists: {self.vmName} does not exists')
        return vmExists

    def stopAndRemoveExistingVM(self) -> bool:
        """
        virsh shutdown IxNetwork-930
        echo 'wait 10 sec'
        sleep 10
        echo 'remove the vm'
        virsh undefine IxNetwork-930
        cd /vms
        echo 'remove existing vm hdd'
        rm -f ./IxNetworkWeb_KVM_9.30.2212.22.qcow2
        """
        output = Utilities.runLinuxCmd('virsh list')
        if output:
            for line in output:
                if bool(search(f'.*{self.vmName}.*', line)):
                    self.log.info(f'Destroy IxNetwork VM in virsh: {self.vmName}')
                    # Utilities.runLinuxCmd(f'virsh shutdown {self.vmName}', logObj=self.log)
                    Utilities.runLinuxCmd(f'virsh destroy {self.vmName}', logObj=self.log)

                    self.log.info('Wait 10 seconds ...')
                    time.sleep(3)

                    self.log.info(f'Remove the current IxNetwork VM in virsh: {self.vmName}')
                    Utilities.runLinuxCmd(f'virsh undefine {self.vmName}', logObj=self.log)
                    time.sleep(10)
                    break

        if self.isIxNetworkVMExists() is False:
            return True
        else:
            return False

    def backupCurrentIxNetworkVMFolder(self):
        Utilities.runLinuxCmd(f'mv {self.ixNetworkVMFolder} {self.ixNetworkVMFolderBackup}', logObj=self.log)

    def restoreBackupIxNetworkVMFolder(self):
        if os.path.exists(self.ixNetworkVMFolder):
            try:
                # Remove the failed download/installation folder and restore it
                # back with the IxNetworkVMs_backup folder
                rmtree(self.ixNetworkVMFolder)
            except Exception as errMsg:
                self.log.error(f'restoreBackupIxNetworkVMFolder error: {traceback.format_exc(None, errMsg)}')

        Utilities.runLinuxCmd(f'mv {self.ixNetworkVMFolderBackup} {self.ixNetworkVMFolder}', logObj=self.log)

    def removeBackupIxNetworkVMFolder(self):
        try:
            rmtree(self.ixNetworkVMFolderBackup)
        except Exception as errMsg:
            self.log.error(f'removeBackupIxNetworkVMFolder error: {traceback.format_exc(None, errMsg)}')

    def downloadVMRelease(self) -> bool:
        downloadIxNetworkFilePath = f'{self.ixNetworkVMFolder}/{self.releaseFilename}'
        self.log.info(f'Downloading build image: src={self.downloadRelease} target={self.ixNetworkVMFolder} ...')
        # Utilities.runLinuxCmd(f'curl -KLX -o {downloadIxNetworkFilePath}  {self.downloadRelease}', logObj=self.log)
        Utilities.runLinuxCmd(f'wget --show-progress -c -P {self.ixNetworkVMFolder} {self.downloadRelease}', logObj=self.log)

        if os.path.exists(downloadIxNetworkFilePath):
            return True
        else:
            return False

    def decompressNewRelease(self) -> bool:
        Utilities.runLinuxCmd(f'sudo tar xjf {self.releaseFilename}', cwd=self.ixNetworkVMFolder, logObj=self.log)

        if os.path.exists(f'{self.ixNetworkVMFolder}/{self.releaseFilename}'):
            self.log.info(f'decompressRelease: Verified file is decompressed: {self.ixNetworkVMFolder}/{self.releaseFilename}')
            return True
        else:
            self.log.info(f'decompressRelease: Verified for decompressed file failed. Not exists: {self.ixNetworkVMFolder}/{self.releaseFilename}')
            return False

    def install(self) -> bool:
        # virt-install --name IxNetwork-930 --memory 32000 --vcpus 16
        # --disk /vms/IxNetworkWeb_KVM_9.30.2212.22.qcow2,bus=sata --import --os-variant centos7.0
        # --network bridge=br1,model=virtio,mac=00:1a:c5:00:00:12 --noautoconsole

        cmd = f'virt-install --name {self.vmName} --memory 32000 --vcpus 16 '
        cmd += f'--disk {self.localIxNetworkQcow2Path},bus=sata --import '
        cmd += f'--os-variant centos7.0 --network bridge=br1,model=virtio,mac={globalSettings.ixNetworkVMDhcpMacAddress} '
        cmd += '--noautoconsole'

        self.log.info(f'Install IxNetwork VM: {cmd}')
        output = Utilities.runLinuxCmd(cmd, logObj=self.log)

        # ERROR    Disk /vms/IxNetworkWeb_KVM_9.30.2212.22.qcow2 is already in use by other guests ['IxNetwork-930']. (Use --check path_in_use=off or --check all=off to override)
        if output and 'ERROR' in output:
            pass

        Utilities.runLinuxCmd(f'virsh autostart {self.vmName}', logObj=self.log)
        Utilities.runLinuxCmd(f'virsh start {self.vmName}', logObj=self.log)

        self.log.info('Wait 30 seconds for IxNetwork VM to come up ...')
        time.sleep(30)

        if self.isIxNetworkVMExists():
            return True
        else:
            return False


def deployIxNetworkInit(ciVars: object = None):
    stage = 'deployIxNetwork'
    ixNetworkLogObj = Utilities.CreateLogObj(ciVars.ixNetworkLogsFile)
    ixNetworkObj = DeployIxNetwork(ciVars.ixNetworkVMFolder, logObj=ixNetworkLogObj)

    if ixNetworkObj.initPassed is False:
        return False

    Utilities.updateStage(ciVars.overallSummaryFile, stage=stage,
                          status='running', result='None', threadLock=ciVars.lock)

    ixNetworkObj.backupCurrentIxNetworkVMFolder()

    result1 = ixNetworkObj.stopAndRemoveExistingVM()
    if result1 is False:
        Utilities.updateStage(ciVars.overallSummaryFile, stage=stage,
                              status='aborted', result='failed: stop existing VM',
                              threadLock=ciVars.lock)
        return False

    result2 = ixNetworkObj.downloadVMRelease()
    if result2 is False:
        ixNetworkObj.restoreBackupIxNetworkVMFolder()
        Utilities.updateStage(ciVars.overallSummaryFile, stage=stage,
                              status='aborted', result='failed: download VM',
                              threadLock=ciVars.lock)
        return False

    result3 = ixNetworkObj.decompressNewRelease()
    if result3 is False:
        ixNetworkObj.restoreBackupIxNetworkVMFolder()
        Utilities.updateStage(ciVars.overallSummaryFile, stage=stage,
                              status='aborted', result='failed: decompress IxNetworkVM',
                              threadLock=ciVars.lock)
        return False

    result4 = ixNetworkObj.install()
    if result4 is False:
        ixNetworkObj.restoreBackupIxNetworkVMFolder()
        Utilities.updateStage(ciVars.overallSummaryFile, stage=stage,
                              status='aborted', result='failed: install IxNetworkVM',
                              threadLock=ciVars.lock)
    else:
        ixNetworkObj.removeBackupIxNetworkVMFolder()
        Utilities.updateStage(ciVars.overallSummaryFile, stage=stage,
                              status='completed', result='passed', threadLock=ciVars.lock)
    return result4
