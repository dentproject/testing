"""
Steps:
   1: Telnet to Dent ONIE prompt.
         - Enter onie-syseeprom to get Base MAC Address
         - Create Mac address folder in /srv/tftp
         - Copy new build to mac-address folder with filename:
                  onie-installer-arm64-accton_as4224_52p-r0

   2: Install the build in the ONIE prompt
         - scp dent@10.36.118.11:/srv/tftp/<image> /onie-installer
           Note:
              - This is just a workaround for ONIE to automatically boot a Linux image
                because for some reason ONIE cannot find the tftp://<image>

   2: Go on Linux shell to verify the build installation version: cat /etc/issue
            DENT OS DENTOS-HEAD, 2023-07-27.09:26-fa55378

telnet 10.36.118.200 7007
     - each device has its own ip port found in the confluence table
     - login: root / onl
     - reboot
     - Expect: Hit any key to stop autoboot -> Press a key to go into Marvell>> prompt
     - enter: run onie_bootcmd
     - After ~60sec seconds when onie is booting
          - enter: onie-discovery-stop (To stop spamming me messages. when the screen is showing info messages)
     - Expect: "ONIE:" prompt

     - Now in the onie prompt:
     - To install the build, enter:
           Use curl/wget to download build to localhost 10.36.118.11:
               https://repos.refinery.dev/service/rest/repository/browse/dent/snapshots/org/dent/dentos/dentos-verify-main/

           # Put the downloaded build into tftp folder path with this filename:
               tftp://10.36.118.11/98-19-2C-45-4D-00/onie-installer-arm64-accton_as4224_52p-r0

           # MUST DOCUMENT THIS IN GITHUB USER GUIDE
               apt-get install tftpd-hpa
               # Each switch its own mac-address!  Get them appropriately.
               put in /srv/tftp/98-19-2C-45-4D-00
               Add user to tftp group

           onie-nos-install http://10.36.118.12/downloads/DENTOS-HEAD_ONL-OS9_2023-05-09.0522-988026a_ARM64_INSTALLED_INSTALLER
           (When mircea-dan fixes 10.36.118.11 with http server, then use 10.36.118.11 insteaad)
"""
from re import search
import os
import traceback
import pexpect
import time
from multiprocessing import Process

import Utilities
import globalSettings


class DeployDent():
    """
    This class installs a build on a Dent switch

    1> Verify/create Dent mac address folder in /srv/tftp
    2> Copy dent cpuArchitecture build to mac address folder
    3> Boot to Onie shell
    4> Install via tftp
    5> Verify:
         - Log into Linux shell
         - Verify build: grep -rn /etc -e "DENT"
    """
    def __init__(self, ciVars: object, dentDeviceLogObj: object = None, testbedObj: dict = {}) -> None:
        self.installMethod = ciVars.installMethod
        # Each dent switch update has its own update log file
        self.log = dentDeviceLogObj

        # Create a result file to store the build update result because
        # this class is run as multiprocess. Need to get the results at the end.
        self.installBuildResultFolder = ciVars.installBuildResultFolder
        self.resultFile = f'{self.installBuildResultFolder}/{testbedObj["friendlyName"].replace(" ", "_")}_result.json'

        self.name = testbedObj['friendlyName']
        self.macAddress = testbedObj['macAddress']
        self.cpuArchitecture = testbedObj['cpuArchitecture']
        self.serialConsoleIp = testbedObj['serialConsole']['ip']
        self.serialConsolePort = testbedObj['serialConsole']['port']
        self.linuxShellLogin = testbedObj['login']['userName']
        self.linuxShellPassword = testbedObj['login']['password']
        self.pduIp = testbedObj['pdu']['ip']
        self.pduLogin = testbedObj['pdu']['login']
        self.pduPassword = testbedObj['pdu']['password']
        self.pduNumber = str(testbedObj['pdu']['number'])
        # tftp://<ip address>
        self.tftpServerPath = globalSettings.tftpServerPath
        # /srv/tftp
        self.tftpServerFolder = globalSettings.tftpServerFolder

        # http://10.36.118.11/DentBuildReleases/09-27-2023-00-15-49-343919_jenkinsCI_devTest
        self.serverPrefixPath = ciVars.serverPrefixPath
        # http path to download new build
        if ciVars.builds:
            self.srcBuildList = ciVars.builds
        if ciVars.localBuilds:
            self.srcBuildList = ciVars.localBuilds
        self.spawnId = None
        # This variable will get set by self.parseForArmOrAmdImageToInstall()
        self.installBuild = None
        self.result = None
        self.checkIfItIsRebooting = False

        self.parseForArmOrAmdImageToInstall()

        if self.installMethod == 'tftp':
            self.createMacAddressFolderInTftp()
            if self.createOnieDefaultImageInTftp() is False:
                self.createOnieDefaultTftpImage = 'failed'
            else:
                self.createOnieDefaultTftpImage = 'passed'

            self.log.info(f'Mac Address: {self.macAddress}')

        resultContent = {'result': 'None'}
        Utilities.writeToJson(self.resultFile, data=resultContent, mode='w')

        self.log.info(f'Serial Console: {self.serialConsoleIp} {self.serialConsolePort}')
        self.log.info(f'CPU architecture: {self.cpuArchitecture}')

    def updateDentResult(self, result):
        self.result = result
        resultContent = {'result': result}
        Utilities.writeToJson(self.resultFile, data=resultContent, mode='w')

    def parseForArmOrAmdImageToInstall(self):
        for buildUrl in self.srcBuildList:
            build = buildUrl.split('/')[-1]
            if self.cpuArchitecture.upper() in build:
                self.installBuild = build
                self.log.info(f'parseForArmOrAmdImageToInstall: DentOS {self.name} has CPU architecture: {self.cpuArchitecture}. Set image to: {build}')

    def createMacAddressFolderInTftp(self):
        """
        For tftp installation only.
        Onie looks for a Dent mac address folder in the tftp server path.

        Verify/create a dent switch mac address folder in the tftp folder.
        Onie has automatic discovery to boot image from the mac address folder.
        """
        if self.installMethod == 'tftp' and self.macAddress:
            macAddress = self.macAddress.replace(':', '-')
            self.dentSwitchMacAddressTftpFolder = f'{self.tftpServerFolder}/{macAddress}'
            if os.path.exists(self.dentSwitchMacAddressTftpFolder) is False:
                Utilities.runLinuxCmd(f'mkdir -p {self.dentSwitchMacAddressTftpFolder}', logObj=self.log)
            else:
                self.log.info(f'createMacAddressFolderInTftp: A Mac Address folder already exists: {self.dentSwitchMacAddressTftpFolder}')

    def createOnieDefaultImageInTftp(self):
        """
        If the Dent switch is in the ONIE shell, it does an auto-discovery for an image
        in its mac address folder in the tftp folder.
        This function wll copy the dent switch cpu architecture build to its mac address folder

        DENTOS-HEAD_ONL-OS10_2023-08-11.1533-be121f3_AMD64_INSTALLED_INSTALLER
        DENTOS-HEAD_ONL-OS10_2023-08-11.1533-be121f3_ARM64_INSTALLED_INSTALLER
        """
        # Note:
        #   self.dentSwitchMacAddressTftpFolder is created by createMacAddressFolderInTftp()
        #   f'{self.tftpServerFolder}/{macAddress}'
        try:
            if os.path.exists(f'{self.tftpServerFolder}/{self.installBuild}'):
                if 'AMD' in self.installBuild:
                    defaultDentFilename = f'{self.dentSwitchMacAddressTftpFolder}/onie-installer-amd64-accton_as4224_52p-r0'
                    Utilities.runLinuxCmd(f'cp {self.tftpServerFolder}/{self.installBuild} {defaultDentFilename}', logObj=self.log)
                else:
                    defaultDentFilename = f'{self.dentSwitchMacAddressTftpFolder}/onie-installer-arm64-accton_as4224_52p-r0'
                    Utilities.runLinuxCmd(f'cp {self.tftpServerFolder}/{self.installBuild} {defaultDentFilename}', logObj=self.log)
            else:
                self.log.error(f'createOnieDefaultImageInTftp: Build not found in tftp server for Dent {self.name}: {self.tftpServerFolder}/{self.installBuild}')
                return False
        except Exception as errMsg:
            self.log.error(f'createOnieDefaultImageInTftp: Error on Dent {self.name}: {traceback.format.exc(None, errMsg)}')
            return False

    def updateDent(self, spawnTelnet=True, timeout=10) -> bool:
        """
        Parameters:
           spawnTelent: <bool>: If 'Type the hot key to suspend the connection' is snagged, it will call itself with spawnTelnet=False.

           timeout: <int>: If spawn encountered a default 5 second timeout, the dent switch could be in the middle of rebooting.
                           Call itself and set timeout to 60 seconds. If it is still timeing out to connect, then something is
                           wrong with the switch.
        """
        try:
            if spawnTelnet:
                self.log.info(f'updateDent: {self.name}: Telnet to serial console: {self.serialConsoleIp} {self.serialConsolePort}')
                self.spawnId = pexpect.spawn(f'telnet {self.serialConsoleIp} {self.serialConsolePort}')
                # 1 = turn on buffering
                self.spawnId.maxsize = 1
                self.spawnId.timeout = timeout

            # '.*localhost login.*'
            # 'root@localhost:~# *'
            while True:
                expectIndex = self.send('\n', expect=['Type the hot key to suspend the connection',
                                                      '.*ONIE:/.*',
                                                      '.*login:.*',
                                                      'Marvell>>',
                                                      'root@.*',
                                                      '.*This connection is in use.*'
                                                      ], timeout=timeout)
                if expectIndex in [0, 1, 2, 3, 4, 5, 6]:
                    break
                else:
                    time.sleep(1)

            if expectIndex == 0:
                self.updateDent(spawnTelnet=False)

            if expectIndex == 1:
                self.log.info(f'UpdteDent: {self.name}: got ONIE prompt')
                if self.install() is False:
                    self.updateDentResult('failed')
                else:
                    self.updateDentResult('passed')
                self.log.info(f'UpdateDent: {self.name}: End of update from ONIE. Final result: {self.result}')

            if expectIndex == 2:
                self.log.info(f'UpdateDent: {self.name}: Got Linux shell login prompt')
                if self.login():
                    if self.goToOnieFromLinuxShell() is False:
                        self.updateDentResult('failed')
                    else:
                        self.log.info(f'UpdateDent: {self.name}: Back to updateDent(). Calling install() ...')
                        if self.install() is False:
                            self.updateDentResult('failed')
                        else:
                            self.updateDentResult('passed')

                        self.log.info(f'UpdateDent: {self.name}: End of update from Linux shell login prompt. Final result: {self.result}')
                else:
                    self.updateDentResult('failed')

            if expectIndex == 3:
                self.log.info(f'UpdateDent: {self.name}: Got Marvell prompt')
                if self.goToOniePromptFromMarvellPrompt() is False:
                    self.updateDentResult('failed')
                else:
                    if self.install() is False:
                        self.updateDentResult('failed')
                    else:
                        self.updateDentResult('passed')

                    self.log.info(f'UpdateDent: {self.name}: End of update from Marvell. Final result: {self.result}')

            if expectIndex == 4:
                self.log.info(f'UpdateDent: {self.name}: Linux shell prompt')
                if self.goToOnieFromLinuxShell() is False:
                    self.updateDentResult('failed')
                else:
                    if self.install() is False:
                        self.updateDentResult('failed')
                    else:
                        self.updateDentResult('passed')

                    self.log.info(f'UpdateDent: {self.name}: End of update from Linux shell prompt. Final result: {self.result}')

            if expectIndex == 5:
                self.log.failed(f'UpdateDent: {self.name}: Somebody is using this serial console: {self.serialConsoleIp} {self.serialConsolePort}')
                self.updateDentResult('failed')

            # pexpect.TIMEOUT
            if expectIndex == 6:
                self.log.failed(f'UpdateDent timed out: {self.name}: Telnet serial console: {self.serialConsoleIp} {self.serialConsolePort}.  Somebody could be using the serial console!')
                # Dent could be in the middle of rebooting
                if self.checkIfItIsRebooting is False:
                    self.checkIfItIsRebooting = True
                    self.updateDent(spawnTelnet=False, timeout=90)

                self.updateDentResult('failed')

        except pexpect.ExceptionPexpect:
            self.log.failed(f'updateDent error 1: {self.name}: Telnet {self.serialConsoleIp} {self.serialConsolePort} timed out.')
            self.updateDentResult('failed')

        except Exception as errMsg:
            self.log.failed(f'updateDent error 2: {self.name}:  {traceback.format_exc(None, errMsg)}')
            self.updateDentResult('failed')

    def send(self, cmd: str, expect: list = [], timeout: int = 10) -> None:
        self.spawnId.timeout = timeout

        if self.spawnId.before:
            self.spawnId.expect(r'.+')

        if cmd == '\n':
            self.spawnId.sendline()
        else:
            self.log.info(f'send: {cmd} ...')
            self.spawnId.send(cmd)
            self.spawnId.expect(cmd)
            self.spawnId.send('\r\n')

        expectList = expect + [pexpect.TIMEOUT]
        index = self.spawnId.expect(expectList, timeout=timeout)

        if expectList[index] != pexpect.TIMEOUT:
            if self.spawnId.before:
                for line in self.spawnId.before.decode('utf-8').split('\r\n'):
                    if line:
                        self.log.info(line, noTimestamp=True)

            if self.spawnId.after:
                for line in self.spawnId.after.decode('utf-8').split('\r\n'):
                    if line:
                        self.log.info(line, noTimestamp=True)

        return index

    def getCurrentShell(self, timeout=5):
        # '.*localhost login.*',
        # '.*root@localhost:.*',
        while True:
            expectIndex = self.send('\n', expect=['ONIE:.*',
                                                  '.*Marvell>>.*',
                                                  '.*login:.*',
                                                  '.*root@.*',
                                                  '.*This connection is in use.*'
                                                  ], timeout=timeout)
            if expectIndex in [0, 1, 2, 3, 4, 5, 6]:
                break
            else:
                time.sleep(1)

        if expectIndex == 0:
            return 'onie'
        elif expectIndex == 1:
            return 'marvell'
        elif expectIndex == 2:
            return 'linuxLogin'
        elif expectIndex == 3:
            return 'linuxShell'
        elif expectIndex == 4:
            return 'inUse'
        else:
            return None

    def login(self) -> bool:
        expectIndex = self.send(cmd=self.linuxShellLogin, expect=['Password.*'])
        if expectIndex != 0:
            self.log.failed(f'login: Dent device: {self.name}: Failed to log into Linux shell with username: {self.linuxShellLogin}')
            return False
        else:
            self.log.info('Got password prompt')
            # password = onl
            self.log.info('Sending password ..')
            self.spawnId.sendline(self.linuxShellPassword)

            # 'root@localhost:~# *'
            expectList = ['.*root@.*', pexpect.TIMEOUT]
            expectIndex = self.spawnId.expect(expectList, timeout=3)

            if expectIndex == 0:
                self.log.info(F'Successfully logged into Linux shell for Dent device: {self.name}')
                return True

            if expectIndex == 1:
                self.log.failed(f'login: log into the Linux shell failed for Dent: {self.name}')
                return False

    def goToOniePrompt(self):
        """
        run onie_bootcmd
        onie-discovery-stop
        """
        # 'root@localhost:~# *'
        while True:
            expectResult = self.send(cmd='\n', expect=['ONIE:.*', 'Marvell>>', 'root@.*'], timeout=3)
            if expectResult in [0, 1, 2, 3]:
                break
            else:
                time.sleep(1)

        if expectResult == 0:
            self.log.info(f'goToOniePrompt: {self.name}: Got ONIE prompt. Done')
            return True

        # Got Marvell>> prompt
        if expectResult == 1:
            self.log.info('goToOniePrompt: {self.name}: Got Marvell prompt')
            self.log.info('goToOniePrompt: {self.name}: Sending: run onie_bootcmd. Waiting up to 80 seconds  ...')
            return self.goToOniePromptFromMarvellPrompt()

        # Got into the Linux shell
        if expectResult == 2:
            expectIndex = self.send(cmd='reboot', expect=['Hit any key to stop autoboot'], timeout=60)
            if expectIndex == 0:
                while True:
                    expectIndex = self.send(cmd='\n', expect=['Marvell>>'], timeout=120)
                    if expectIndex in [0, 1]:
                        break
                    else:
                        time.sleep(1)

                if expectIndex == 0:
                    return self.goToOniePromptFromMarvellPrompt()

        if expectResult == 3:
            self.log.failed(f'goToOniePrompt: {self.name}: timedout expecting prompts: ONIE:, Marvell>>, root@localhst')

        return False

    def goToOniePromptFromMarvellPrompt(self):
        if self.spawnId.before:
            self.spawnId.expect(r'.+')

        timeout = 120
        while True:
            expectIndex = self.send('\n', expect=['Marvell>>'], timeout=5)
            if expectIndex in [0, 1]:
                break
            else:
                time.sleep(1)

        if expectIndex == 2:
            self.log.failed('goToOniePromptFromMarvellPrompt: Dent:{self.name}: Failed to get the Marvell>> prompt. Cannot continue.')
            return False

        self.log.info(f'goToOniePromptFromMarvellPrompt: Sending: run onie_bootcmd on Dent:{self.name}. Waiting up to {timeout} seconds  ...')
        expectIndex0 = self.send(cmd='run onie_bootcmd', expect=['.*ONIE:.*'], timeout=timeout)
        if expectIndex0 == 0:
            self.log.info(f'goToOniePromptFromMarvellPrompt: Got ONIE prompt on Dent device: {self.name}')
            self.log.info(f'goToOniePromptFromMarvellPrompt: Dent:{self.name} -> Sending onie-discovery-stop ...')
            expectIndex1 = self.send(cmd='onie-discovery-stop', expect=['.*ONIE:.*'], timeout=20)
            if expectIndex1 == 0:
                self.log.info('goToOniePromptFromMarvellPrompt: {self.name}: Got ONIE prompt.  Auto-discovery stopped.')
                return True
            if expectIndex1 == 1:
                self.log.failed('goToOniePromptFromMarvellPrompt: {self.name}: Did not get ONIE prompt after sending onei-discovery-stop')
                return False

        return False

    def goToOnieFromLinuxShell(self):
        """
        Note:
           Some Dent switches such as infra2 ask to enter "123" to stop autoboot.
           If "123" was entered, it goes into the Marvell>> mode immediately.
           Otherwise, it goes into mode.
        """
        while True:
            expectIndex = self.send(cmd='\n', expect=['Hit any key to stop autoboot',
                                                      '.*Type 123<ENTER> to STOP autoboot.*'], timeout=80)
            if expectIndex in [0, 1, 2]:
                break
            else:
                time.sleep(1)

        if expectIndex == 0:
            return self.goToOniePromptFromMarvellPrompt()

        if expectIndex == 1:
            self.log.info(f'goToOnieFromLinuxShell: Dent device: {self.name}: Got Type 123 <Enter> on serial console. Sening 123 to go into Marvell>> ...')
            if self.spawnId.before:
                self.spawnId.expect(r'.+')

            self.spawnId.sendline('123\r\n')
            expectIndex1 = self.spawnId.expect(['.*Marvell>>.*', pexpect.TIMEOUT], timeout=5)

            self.log.debug(f'goToOnieFromLinuxShell: {self.name}: spawnId.after: {self.spawnId.after}')
            # self.spawnId.after => got back after: b'Marvell>> \r\nMarvell>> \r\nMarvell>> '

            if expectIndex1 == 0 or 'Marvell' in self.spawnId.after.decode('utf'):
                self.log.info(f'goToOnieFromLinuxShell: {self.name}: Got Marvell>> prompt.')
                result = self.goToOniePromptFromMarvellPrompt()
                return result

            # pexpect.TIMEOUT
            if expectIndex1 == 1:
                self.log.failed(f'goToOnieFromLinuxShell: Waiting for Marvell prompt timedout on Dent: {self.name}')
                currentShell = self.getCurrentShell()
                self.log.debug(f'goToOnieFromLinuxShell: {self.name}: Current mode is {currentShell}')
                if currentShell == 'marvell':
                    result = self.goToOniePromptFromMarvellPrompt()
                    return result

                if currentShell == 'onie':
                    return True

                return False

    def install(self, retry=False) -> bool:
        """
        build == tftp://{macAddress}/build

        Install new build in ONIE shell
        If success:
            it will automatically reboot. Press <enter> key
            on 'Hit any key to stop autoboot' to Linux shell.
            This will go into the Marvell shell. From there, boot to ONIE.

        If failed: Return False
        """
        if self.spawnId.before:
            self.spawnId.expect(r'.+')

        # http://<ip>/dentInstallation/<testid> | tftp://<ip>/src/tftp/<testId>
        installServerPath = f'{self.serverPrefixPath}/{self.installBuild}'

        """
        onie-nos-install http://10.36.118.11/dentBuildReleases/DENTOS-HEAD_ONL-OS10_2023-12-13.1632-67e7fe4_ARM64_INSTALLED_INSTALLER
        discover: installer mode detected.
        Stopping: discover... done.
        Info: Attempting http://10.36.118.11/dentInstallations/DENTOS-HEAD_ONL-OS10_2023-08-11.1533-be121f3_ARM64_INSTALLED_INSTALLER ...
        Connecting to 10.36.118.11 (10.36.118.11:80)
        installer            100% |*******************************|   333M  0:00:00 ETA
        ONIE: Executing installer: http://10.36.118.11/dentInstallations/DENTOS-HEAD_ONL-OS10_2023-08-11.1533-be121f3_ARM64_INSTALLED_INSTALLER
        installer: computing checksum of original archive
        installer: checksum is OK
        """
        timeout = 300
        self.spawnId.timeout = timeout

        cmd = f'onie-nos-install {installServerPath}'
        self.log.info(f'install: sending cmd on Dent: {self.name}: {cmd} ...')

        # Must use sendline() instead of send()
        self.log.info(f'install: Dent: {self.name}: Waiting for installation to complete and reboot to Linux mode ...')
        self.spawnId.sendline(cmd)
        self.spawnId.expect(['.*'], timeout=3)

        # '.*localhost login.*'
        while True:
            expectIndex = self.send(cmd='\n', expect=['.*404 Not Found',
                                                      '.*login:.*'], timeout=80)

            if expectIndex in [0, 1, 2]:
                break
            else:
                time.sleep(1)

        if expectIndex == 0:
            self.log.failed(f'install: {self.name}: wget: server returned error: HTTP/1.1 404 Not Found')
            return False

        if expectIndex == 1:
            self.log.info(f'install: Installation is complete for Dent device: {self.name}')
            self.log.info(f'install: Logging into Dent Linux shell: {self.name} ...')

            if self.login():
                result = self.verifyCurrentBuild()
                return result
            else:
                return False

        # pexpect.TIMEOUT
        if expectIndex == 1:
            self.log.failed(f'install: Timed out waiting for Linux login after onie installation for Dent device: {self.name}')
            self.log.debug(f'install: Verifying which shell mode the Dent switch is in: {self.name}')
            currentShell = self.getCurrentShell()
            self.log.debug(f'install: The current shell for Dent device: {self.name} == {currentShell}')

            if currentShell == 'onie':
                if retry is False:
                    self.log.warning(f'install: Dent device: {self.name}: Failed to install build. Still in ONIE mode. Attempt to install one more time ...')
                    self.install(retry=True)
                if retry:
                    self.log.failed('install: Retried to install build failed again. Still in ONIE mode. Expecting the installation to complete in Linux mode')
                    return False

            if currentShell == 'linuxLogin':
                self.log.debug('install: Since it is in the Linux login prompt, the installation is complete')
                if self.login():
                    result = self.verifyCurrentBuild()
                    return result
                else:
                    return False

            return False

    def verifyCurrentBuild(self):
        self.log.info(f'verifyCurrentBuild: Dent device: {self.name} ...')
        if self.spawnId.before:
            self.spawnId.expect(r'.+')

        self.spawnId.sendline(r'grep -rn /etc -e "DENT" \| grep versions.json \| grep VERSION_STRING')
        expectIndex = self.spawnId.expect(['.*root@.*'], timeout=10)

        if expectIndex == 0:
            for line in self.spawnId.after.decode('utf-8').split('\r\n'):
                self.log.info(line)
                """
                line: | grep versions.json | grep VERSION_STRING
                line: /etc/onl/loader/versions.json:3:  "VERSION_STRING": "DENT OS DENTOS-HEAD, 2023-08-11.15:33-be121f3",
                line: root@localhost:~#
                """
                if 'DENT OS' not in line:
                    continue

                # ['/etc/onl/loader/versions.json:3:  "VERSION_STRING": "DENT OS DENTOS-HEAD', ' 2023-08-11.15:33-be121f3"', '']
                # ' 2023-08-11.15:33-be121f3'
                hashTag = line.split(',')[1].replace('"', '').split('-')[-1]
                if "'" in hashTag:
                    hashTag = hashTag.replace("'", '')

                if bool(search(f'.*{hashTag}.*', self.installBuild)):
                    self.log.info(f'verifyCurrentBuild: Passed: Dent device: {self.name}: {hashTag}')
                    return True
                else:
                    self.log.failed(f'verifyCurrentBuild: Failed: Dent device {self.name}. The installed build is {self.installBuild}. Expecting build with hash tag: {hashTag}')
                    return False

                # Search for: /etc/onl/loader/versions.json:3:  "VERSION_STRING": "DENT OS DENTOS-HEAD, 2023-08-11.15:33-be121f3",
                # Real image: DENTOS-HEAD_ONL-OS10_2023-08-11.1533-be121f3_ARM64_INSTALLED_INSTALLER
            else:
                self.log.failed(f'verifyCurrentBuild: grep had no output for Dent device: {self.name}')

        if expectIndex == 1:
            self.log.failed(f'verifyCurrentBuild Attempted to verify the installed image on Dent {self.name}, but failed to get grep output')
            return False

    def getCPUArchitecture(self) -> str:
        """
        root@localhost:~# lscpu
           Architecture:        aarch64
           Vendor ID:           ARM

        cat /etc/onl/platform
           ARM = arm64-accton-as4224-52p-r0
           AMD = ?
        """
        # arm64-accton-as4224-52p-r0
        index = self.send(cmd='cat /etc/onl/platform', expect=[], timeout=2)

        if index == 1:
            for line in self.spawnId.before.decode('utf-8').split('\r\n'):
                matchRegexp = search('.*(arm64|amd.*)', line)
                if matchRegexp:
                    # arm64 | amd
                    self.cpuArchitecture = matchRegexp.group(1)
                    self.log.info(f'CPU = {self.cpuArchitecture}')
                    return self.cpuArchitecture

        return self.cpuArchitecture

    def getDentMacAddress(self) -> str:
        """
        At the ONIE prompt, enter: onie-syseeprom to get Base Mac Address

        Note: Do not get the dent switch mac address from the linux shell.
              It is different and ONIE auto-discovery looks for tftp folder with
              the onie mac address.
        """
        expectIndex1 = self.send(cmd='onie-discovery-stop', expect=['ONIE:.*'], timeout=5)
        if expectIndex1 == 0:
            self.log.info('Got ONIE prompt.  Spamming messages stopped')
            return True

        index = self.send(cmd='onie-syseeprom', expect=['ONIE:.*'], timeout=5)

        if index == 0:
            for line in self.spawnId.before.decode('utf-8').split('\r\n'):
                self.log.info(line)
                # Base MAC Address     0x24   6 98:19:2C:45:4D:00
                matchRegexp = search('.*Base MAC Address +[^ ]+ +[0-9]+ +([^ ]+)', line)
                if matchRegexp:
                    # arm64 | amd
                    macAddress = matchRegexp.group(1)
                    self.macAddress = macAddress.replace(':', '-')
                    self.log.info(f'MAC Address = {self.macAddress}')
                    return self.macAddress

        return self.macAddress

    def closeSpawnId(self):
        if self.spawnId:
            self.spawnId.close()


class PowerCycle:
    """
    Usage:
        self.powerCycleObj = PowerCycle(logObj=logObj, deviceIp=pduIp, deviceIpPort=None,
                                        user=pduLogin, password=pduPassword, powerCycleNumber=pduNumber)
        if self.powerCycleObj.telnetToDevice() is False:
            return False
    """
    def __init__(self, logObj: object, deviceIp: str, deviceIpPort: int = None,
                 user: str = None, password: str = None, powerCycleNumber: str = None) -> None:
        self.log = logObj
        self.deviceIp = deviceIp
        self.deviceIpPort = deviceIpPort
        self.user = user
        self.password = password
        self.powerCycleNumber = powerCycleNumber

    def telnetToDevice(self, spawnTelnet=True):
        try:
            self.log.info(f'PowerCycle.TelnetToDevice: {self.deviceIp} {self.deviceIpPort}')
            self.spawnId = pexpect.spawn(f'telnet {self.deviceIp}')
            self.spawnId.maxsize = 0
            self.spawnId.timeout = 10
            self.spawnId.maxread = 100000

            expectIndex = self.send('\n', expect=['.+ser.*ame.', '.+assword.*', '.+Console.*'], timeout=2)

            if expectIndex == 0:
                self.log.info('PowerCycle: Sending user: {self.user} ...')
                expectIndex1 = self.send(self.user, expect=['Password'], timeout=2)
                if expectIndex1 != 0:
                    self.log.failed(f'PowerCycle: Login user name failed: {self.user}')
                    return False

                if expectIndex1 == 0:
                    self.spawnId.send(f'{self.password}\r\n')
                    expectIndex2 = self.spawnId.expect(['American', 'Event'], timeout=2)
                    if expectIndex2 != 0:
                        self.log.failed(f'PowerCycle: Failed to log into the power cycle device with password: {self.password}')
                        return False

                    if expectIndex2 in [0, 1]:
                        self.log.info('PowerCycle: Successfully logged into the power cycle device 1')
                        return

            if expectIndex == 1:
                self.spawnId.send(f'{self.password}\r\n')
                expectIndex2 = self.spawnId.expect(['American', 'Event'], timeout=2)
                if expectIndex3 != 0:
                    self.log.failed(f'PowerCycle: Failed to log into the power cycle device with password: {self.password}')
                    return False

                if expectIndex3 in [0, 1]:
                    self.log.info('PowerCycle: Successfully logged into the power cycle device 2')
                    return

            if expectIndex == 2:
                self.log.info('PowerCycle: Successfully logged into the power cycle device 3')
                return

        except pexpect.ExceptionPexpect as errMsg:
            self.log.failed(f'Error. PowerCycle: telnetToDevice: {self.deviceIp}: {traceback.format_exc(None, errMsg)}.')
            return False

        except Exception as errMsg:
            self.log.failed(f'PowerCycle: Telnet error: {traceback.format_exc(None, errMsg)}')
            return False

    def rebootToMarvellShell(self):
        pass

    def reboot(self):
        """
        In the Dent switch Linux shell, there is no reboot command
        Using a PDU to power cycle the switch

        Reboot the dent switch to go into the Linux shell
        Mainly to get the cpu architecture

        Power cycling:
            - If there is no installation, it will boot into ONIE
                  - Install an AMD build (Just a guest)
                  - Verify for error
                  - If there is an error, install ARM build

            - If there is an installation:
                 - It will boot into the Linux shell
                 - Get the CPU architecture
                 - Enter "reboot" and "Hit any key to stop autoboot" will enter the Marvell shell
        """
        # 1 = Device Manager
        expectIndex0 = self.send('\n', expect=['.*Control.*Event.*'], timeout=10)
        if expectIndex0 != 0:
            self.log.info('PowerCycle: Failed to see power cycle PDU')
            return
        else:
            self.log.info('PowerCycle: Got PDU!')

        time.sleep(1)
        expectIndex = self.send('1', expect=['.*Device Manager.*Event.*'], timeout=10)
        if expectIndex == 0:
            self.log.info('PowerCycle: Device Manager')

            time.sleep(3)
            # 2 = Outlet Management
            expectIndex = self.send('2', expect=['.*Outlet Management.*Event.*'], timeout=10)
            if expectIndex == 0:
                self.log.info('PowerCycle: Outlet Management')

                time.sleep(3)
                # 1 = Outlet Control/Configuration
                expectIndex = self.send('1', expect=['.*Outlet.*Control/Configuration.*Event.*'], timeout=10)
                if expectIndex == 0:
                    self.log.info('PowerCycle: Outlet Control/Configuration')

                    time.sleep(3)
                    expectIndex = self.send(str(self.powerCycleNumber), expect=[f'.*Outlet.*{self.powerCycleNumber}.*Event.*'], timeout=10)
                    if expectIndex == 0:

                        time.sleep(3)
                        # 1 = Control Outlet
                        expectIndex = self.send('1', expect=['.*Control.*Outlet.*Event.*'], timeout=10)
                        if expectIndex == 0:
                            self.log.info('PowerCycle: Control Outlet')

                            time.sleep(3)
                            # 1- Immediate On
                            # 2- Immediate Off
                            # 3- Immediate Reboot
                            self.log.info('PowerCycle: Entering 3 to reboot immediately ...')
                            expectIndex = self.send('3', expect=['.*YES.*'], timeout=10)

                            time.sleep(3)
                            if expectIndex == 0:
                                self.log.info('PowerCycle: Entering "YES" to continue')

                                time.sleep(3)
                                expectIndex = self.send('YES', expect=['.*<ENTER> to continue.*'], timeout=10)
                                if expectIndex == 0:

                                    time.sleep(3)
                                    self.log.info('PowerCycle: Pressing the enter key to continue')
                                    expectIndex = self.send('\n', expect=['.*Control.*Event.*'], timeout=10)
                                    if expectIndex == 0:
                                        self.log.info(f'PowerCycle: Successfully power cycled: {self.powerCycleNumber}')

    def send(self, cmd: str, expect: list = [], timeout: int = 10) -> int:
        self.spawnId.timeout = timeout

        if self.spawnId.before:
            self.spawnId.expect(r'.+')

        if cmd == '\n':
            # self.spawnId.sendline()
            self.spawnId.send('')
            self.spawnId.expect('')
            self.spawnId.send('\r\n')
        else:
            self.log.info(f'PowerCycle: send: {cmd} ...')
            self.spawnId.send(cmd)
            self.spawnId.expect(cmd)
            self.spawnId.send('\r\n')

        expectList = expect + [pexpect.EOF, pexpect.TIMEOUT]
        index = self.spawnId.expect(expectList, timeout=timeout)

        if expectList[index] != pexpect.TIMEOUT:
            if self.spawnId.before:
                for line in self.spawnId.before.decode('utf-8').split('\r\n'):
                    if line:
                        self.log.info(line, noTimestamp=True)

            if self.spawnId.after:
                for line in self.spawnId.after.decode('utf-8').split('\r\n'):
                    if line:
                        self.log.info(line, noTimestamp=True)

        self.log.info(f'PowerCycle: : Got expect: {expectList[index]}')
        return index

    def closeSpawnId(self):
        if self.spawnId:
            self.spawnId.close()


def updateDent(ciVars: object) -> bool:
    """
    [{'model': 'arm64-accton-as4224-52p-r0',
      'os': 'dentos',
      'baudrate': 115200,
      'friendlyName': 'Dev Dent',
      'hostName': 'dev-hw',
      'ip': '10.36.118.42',
      'links': [['swp49', 'agg1:swp47'],
                ['swp50', 'agg2:swp47'],
                ['swp51', 'infra2:swp51'],
                ['swp52', 'infra2:swp52']],
      'login': {'password': 'onl', 'userName': 'root'},
      'cpuArchitecture': 'arm',
      'macAddress': '98:19:2C:45:4D:00',
      'pduIp': '10.36.118.201',
      'pduLogin': 'dent',
      'pduNumber': 7,
      'pduPassword': 'dent123!',
      'serialConsoleIp': '10.36.118.200',
      'serialConsolePort': 7007,
      'serialDev': '/dev/ttyUSB0',
      'type': 'INFRA_SWITCH'}]
    """
    threadList = []
    objectList = []

    Utilities.updateStage(ciVars.overallSummaryFile, stage='installDentOS', status='running', threadLock=ciVars.lock)

    if len(ciVars.testbeds) == 0:
        ciVars.sessionLog.error('updateDent: ciVars.testbeds has no testbeds!')
        finalResult = False
        Utilities.updateStage(ciVars.overallSummaryFile, stage='installDentOS', status='stopped',
                              result='failed', threadLock=ciVars.lock)
        return finalResult

    for testbed in ciVars.testbeds:
        if testbed['os'] != 'dentos':
            continue

        deviceName = testbed['friendlyName'].replace(' ', '_')
        deviceUpdateLogFile = f'{ciVars.testSessionLogsFolder}/{deviceName}_updateLogs'
        currentDeviceUpdateLogObj = Utilities.CreateLogObj(deviceUpdateLogFile)
        connectToDentObj = DeployDent(ciVars=ciVars, dentDeviceLogObj=currentDeviceUpdateLogObj,
                                      testbedObj=testbed)

        objectList.append(connectToDentObj)
        threadObj = Process(target=connectToDentObj.updateDent, name=f'{deviceName}')
        threadList.append(threadObj)

    Utilities.runThreads(ciVars, threadList)

    finalResult = True

    for eachDentObj in objectList:
        deviceName = eachDentObj.name
        updateResultJsonFile = eachDentObj.resultFile
        dentInstallation = Utilities.readJson(updateResultJsonFile)

        if dentInstallation['result'] == 'failed':
            ciVars.sessionLog.failed(f'Update Dent and verified: {deviceName} result: {dentInstallation["result"]}')
            finalResult = False

        if dentInstallation['result'] == 'passed':
            ciVars.sessionLog.info(f'Update Dent and verified: {deviceName} result: {dentInstallation["result"]}')

        try:
            os.remove(updateResultJsonFile)
        except Exception:
            pass

    ciVars.sessionLog.info(f'Final result for build installation on all Dent switches: {finalResult}')
    if finalResult is False:
        Utilities.updateStage(ciVars.overallSummaryFile, stage='installDentOS', status='stopped',
                              result='failed', threadLock=ciVars.lock)
    else:
        Utilities.updateStage(ciVars.overallSummaryFile, stage='installDentOS', status='completed',
                              result='passed', threadLock=ciVars.lock)

    return finalResult
