"""
Steps:
   1: Telnet to Dent ONIE prompt.
         - Enter onie-syseeprom to get Base MAC Address
         - Create Mac address folder in /srv/tftp

   2: Reboot to Linux prompt to get the CPU architecture
         - Verify each Dent CPU architecture: arm64 or amd
         - At Linux prompt, enter: cat /etc/onl/platform
         - set the cpu architecture in self.cpuArchitecture
         - Main script:
             - Downloads both ARM and AMD file in /srv/tftp
             - Copy the amd or arm build to the mac address folder and rename to
               onie-installer-arm64-accton_as4224_52p-r0

telnet 10.36.118.200 7007
     - In the ONIE prompt, enter: syseeprom to get the Dent switch mac address
     - With the mac address, create a mac address folder in /srv/tftp
     - Copy new build in this folder and rename it to onie-installer-arm64-accton_as4224_52p-r0 

      ONIE:/ # onie-syseeprom
TlvInfo Header:
   Id String:    TlvInfo
   Version:      1
   Total Length: 176
TLV Name             Code Len Value
-------------------- ---- --- -----
Product Name         0x21  20 AS4224-52P-O-AC-F-EC
Part Number          0x22  13 F0LEC4224004Z
Serial Number        0x23  14 422452P2141017
Base MAC Address     0x24   6 98:19:2C:45:4D:00
Manufacture Date     0x25  19 10/08/2021 17:32:03
Label Revision       0x27   4 R0CA
Platform Name        0x28  26 arm64-accton_as4224_52t-r0
ONIE Version         0x29  13 2020.02.00.09
MAC Addresses        0x2A   2 69
Manufacturer         0x2B   6 Accton
Country Code         0x2C   2 TW
Vendor Name          0x2D   8 Edgecore
Diag Version         0x2E  11 00.0c.01.00
CRC-32               0xFE   4 0x697F9F3C


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
import sys, traceback, pexpect, time, threading

import utilities

class DeployDent:
    """
    This class installs a build on a Dent switch

    """
    def __init__(self, logObj: object, serialConsoleIp: str, serialConsolePort: str,
                 linuxShellLogin: str, linuxShellPassword: str, pduIp: str, pduLogin: str,
                 pduPassword: str, pduNumber: str, tftpServerPath: str, tftpServerFolder: str,
                 srcBuildList: list) -> None:

        self.log = logObj
        self.serialConsoleIp = serialConsoleIp
        self.serialConsolePort = serialConsolePort
        self.linuxShellLogin = linuxShellLogin
        self.linuxShellPassword = linuxShellPassword
        self.pduIp = pduIp
        self.pduLogin = pduLogin
        self.pduPassword = pduPassword
        self.pduNumber = str(pduNumber)
        # tftp://<ip address>
        self.tftpServerPath = tftpServerPath
        # /srv/tftp
        self.tftpServerFolder = tftpServerFolder
        # http path to download new build
        self.srcBuildList = srcBuildList
        self.spawnId = None
        self.cpuArchitecture = None
        self.macAddress = None

    def getMacAddressAndCpuArchitecture(self):
        """
        Must be at the ONIE prompt
        """
        if self.getDentMacAddress() is None:
            return False

        # Power cycle dent to go into Linux shell to get cput prompt
        if self.powerCycleDentHelper() == False:
            return False

        # Wait for dent switch to reboot and go into Linux login prompt
        if self.waitForRebootEnterLinuxLogin() == False:
            return False

        if self.linuxPromptLogin():
            # arm | amd
            if self.getCPUArchitecture() is None:
                return False
            
            if self.goToOnieFromLinuxShell():
                return False

            self.log.info(f'---- macAddress:{self.macAddress}  cpu:{self.cpuArchitecture} ----')
            if self.macAddress:
                macAddress = self.macAddress.replace(":", "-")
                dentSwitchMacAddressTftpFolder = f'{self.tftpServerFolder}/{macAddress}'
                if os.path.exists(dentSwitchMacAddressTftpFolder) == False:
                    utilities.runLinuxCmd(dentSwitchMacAddressTftpFolder, logObj=self.log)
                    
            return True
        else:
            return False

    def updateDent(self, spawnTelnet=True):
        try:
            if spawnTelnet:
                self.log.info(f'updateDent: Telnet to serial console: {self.serialConsoleIp} {self.serialConsolePort}')
                self.spawnId = pexpect.spawn(f'telnet {self.serialConsoleIp} {self.serialConsolePort}')
                # 1 = turn on buffering
                self.spawnId.maxsize = 1
                self.spawnId.timeout = 5
            
            expectIndex = self.send('\n', expect=['Type the hot key to suspend the connection',
                                                  'ONIE',
                                                  'localhost login',
                                                  'Marvell>>',
                                                  'root@localhost:~# *',
                                                  'This connection is in use.*'
                                                  ], timeout=3)

            self.log.debug(f'updateDent: expectIndex: {expectIndex}')
                
            if expectIndex == 0:
                self.updateDent(spawnTelnet=False)
                
            if expectIndex == 1:
                self.log.info('Got ONIE prompt')
                if self.getMacAddressAndCpuArchitecture() == False:
                    return False
                
                #if self.installBuildHelperTftp() == False:
                #    return False
                #else:
                #    return True
                
            if expectIndex == 2:
                self.log.info('Got Linux shell login prompt')
            
                if self.linuxPromptLogin():
                    self.getCPUArchitecture()
                    
                    if self.goToOnieFromLinuxShell() == False:
                        return False
                        
                    self.getDentMacAddress()
                    self.log.info(f'---- From Linux shell login:  macAddress:{self.macAddress}  cpu:{self.cpuArchitecture} ----')
                    return
                
                    #if self.installBuildHelperTftp() == False:
                    #    return False
                    #else:
                    #    return True
                else:
                    self.log.failed('Login failed')
                    return False
                    
            if expectIndex == 3:
                self.log.info(f'Got Marvell prompt')
                if self.goToOniePromptFromMarvellPrompt() == False:
                    return False

                if self.getMacAddressAndCpuArchitecture() == False:
                    return False
                
                #if self.installBuildHelperTftp() == False:
                #    return False
                #else:
                #    return True
                
            if expectIndex == 4:
                self.log.info(f'Linux shell prompt')
                
                self.getCPUArchitecture()
                
                if self.goToOnieFromLinuxShell() == False:
                    return False

                self.getDentMacAddress()
                self.log.info(f'---- From Linux shell prompt:  macAddress:{self.macAddress}  cpu:{self.cpuArchitecture} ----')
                return
            
                #if self.installBuildHelperTftp() == False:
                #    return False
                #else:
                #    return True
                
            if expectIndex == 5:
                self.log.failed(f'Somebody is using this serial console: {self.serialConsoleIp} {self.serialConsolePort}')
                return False

            # pexpect.TIMEOUT
            if expectIndex == 7:
                self.log.failed(f'Failed to telnet into device: {self.serialConsoleIp} {self.serialConsolePort}.  Somebody could be using the serial console!')
                return False
          
        except pexpect.ExceptionPexpect:
            self.log.failed(f'telnetToDevice: {self.serialConsoleIp} {self.serialConsolePort} Expect timeout exceeded.')
            return False
        except Exception as errMsg:
            self.log.failed(f'Telnet error: {traceback.format_exc(None, errMsg)}')
            return False

    def send(self, cmd: str, expect: list=[], timeout: int=10) -> None:
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
        
        return index
        
    def getCurrentShell(self, timeout=3):
        expectIndex = self.send('\n', expect=['ONIE',
                                              'Marvell>>',
                                              'localhost login',
                                              'root@localhost:~# *',
                                              'This connection is in use.*'
                                              ], timeout=timeout)
        self.log.debug(f'getCurrentShell: expectIndex: {expectIndex}')
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

    def waitForRebootEnterLinuxLogin(self):
        self.log.info(f'waitForRebootEnterLinuxLogin: Takes approximately 2 minutes at this point ...')
        
        expectIndex = self.send(cmd='\n\r', expect=['localhost login'], timeout=180)
        if expectIndex == 0:
            self.log.info('waitForRebootEnterLinuxLogin: Successfully reboot to Linux login prompt') 
            return True

        if expectIndex == 2:
            self.log.failed(f'Failed to reboot into Linux loging prompt')
            return False
        
    def linuxPromptLogin(self) -> bool:
        expectIndex = self.send(cmd=self.linuxShellLogin, expect=['Password'])
        if expectIndex != 0:
            self.log.failed('Failed to log into Linux shell with username: {self.linuxShellLogin}')
            return False
        else:
            self.log.info('Got password prompt')
            # password = onl
            #expectIndex = self.send(cmd=self.linuxShellPassword, expect=['root@localhost'])
            self.spawnId.send(f'{self.linuxShellPassword}\r\n')
            expectIndex = self.spawnId.expect(['root@localhost'], timeout=5)
            if expectIndex == 0:
                self.log.info('Successfully logged into Linux shell')
                return True
            else:
                self.log.failed(f'Failed to log into Linux Shell with password')
                return False

    def goToOniePrompt(self):
        """
        run onie_bootcmd
        onie-discovery-stop
        """
        expectResult = self.send(cmd='\n', expect=['ONIE', 'Marvell>>', 'root@localhost'], timeout=3)
        if expectResult == 0:
            self.log.info(f'Got ONIE prompt. Done')
            return

        # Got Marvell>> prompt
        if expectResult == 1:
            self.log.info(f'Got Marvell prompt')
            self.log.info(f'Sending: run onie_bootcmd. Waiting up to 80 seconds  ...')
            self.goToOniePromptFromMarvellPrompt()
            return
        
        # Got into the Linux shell
        if expectResult == 2:
            expectIndex = self.send(cmd='reboot', expect=['Hit any key to stop autoboot'], timeout=60)
            if expectIndex == 0:
                expectIndex = self.send(cmd='\n', expect=['Marvell>>'], timeout=120)
                if expectIndex == 0:
                    self.goToOniePromptFromMarvellPrompt()
                    return

        return False

    def goToOniePromptFromMarvellPrompt(self):
        expectIndex = self.send('\n', expect=['Marvell>>'], timeout=5)
        if expectIndex == 2:
            self.log.failed('goToOniePromptFromMarvellPrompt: Failed to get the Marvell>> prompt. Cannot continue.')
            return False
        
        self.log.info(f'goToOniePromptFromMarvellPrompt: Sending: run onie_bootcmd. Waiting up to 80 seconds  ...')
        expectIndex1 =  self.send(cmd='run onie_bootcmd', expect=['ONIE'], timeout=80)
        if expectIndex1 == 0:
            self.log.info(f'Got ONIE prompt.  Sending onie-discovery-stop to stop spamming messages ...')
            expectIndex2 =  self.send(cmd='onie-discovery-stop', expect=['ONIE'], timeout=80)
            if expectIndex2 == 0:
                self.log.info(f'Got ONIE prompt.  Spamming messages stopped')
                return
            
        return False
    
    def goToOnieFromLinuxShell(self):
        expectIndex1 =  self.send(cmd='reboot', expect=['Hit any key to stop autoboot',
                                                        'Type 123<ENTER> to STOP autoboot'], timeout=80)
        if expectIndex1 == 0:
            return self.goToOniePromptFromMarvellPrompt()

        if expectIndex1 == 1:
            expectIndex1 =  self.send(cmd='123', expect=['Marvell>>'], timeout=120)
            if expectIndex1 == 0:
                return self.goToOniePromptFromMarvellPrompt()

            # pexpect.TIMEOUT
            if expectIndex1 ==2:
                return False

    def downloadBuild(self) -> None:
        """
        srcBuildList: A list of ARM and AMD files to download
             buildSrcPath: https://repos.refinery.dev/repository/dent/snapshots/org/dent/dentos/dentos-verify-main
             armBuild:     DENTOS-HEAD_ONL-OS10_2023-05-17.2235-63c7032_ARM64_INSTALLED_INSTALLER
             amdBuild:     DENTOS-HEAD_ONL-OS10_2023-05-24.1342-38a20b1_AMD64_INSTALLED_INSTALLER

        targetFolder: /srv/tftp
        """
        self.log.info(f'Downloading build image ...')
        for srcBuild in self.srcBuildList:
            buildName = srcBuild.split('/')[-1]
            utilities.runLinuxCmd(f'curl -KLX -o {self.destBuildPath}/{buildName} {srcBuild}', logObj=self.log)
            
    def installBuildHelperTftp(self) -> bool:
        """
        Helper function to install one of two builds.
        Try both ARM and AMD builds. If ARM failed, try AMD.
        """
        for build in self.srcBuildList:
            buildName = build.split('/')[-1]
            if self.installBuildTftp(build=buildName) == 'Build Failed':
                self.log.warning('installBuild failed. Trying different cput arch build')
                continue
            else:
                return True

        return False
                
    def installBuildTftp(self, build: str) -> None:
        """
        build == tftp://x.x.x.x/build
        
        Install new build in ONIE shell
        If success:
            it will automatically reboot. Press <enter> key 
            on 'Hit any key to stop autoboot' to Linux shell.
            This will go into the Marvell shell. From there, boot to ONIE.

        If failed: Return False
        """
        timeout = 180
        self.spawnId.timeout = timeout
        time.sleep(2)

        if self.spawnId.before:
            self.spawnId.expect(r'.+')
            
        tftpPath = f'{self.tftpServerPath}/{build}'
        cmd = f'onie-nos-install {tftpPath}'
        self.log.info(f'sending cmd: {cmd} ...')
        # Must use sendline() instead of send()
        self.spawnId.sendline(f'{cmd}\n')
        self.spawnId.expect('.*')
        self.log.info('Wait 60 seconds ...')
        time.sleep(60)
        self.log.info('Checking the installation ...')
        self.spawnId.sendline()

        expectList = [f'.*{tftpPath}.*', '.*Failure: Unable to install image.*'] + [pexpect.EOF, pexpect.TIMEOUT]
        expectIndex = self.spawnId.expect(expectList, timeout=timeout)

        if expectIndex == 1:
            self.log.warning('Installing build failed')
            return 'Build Failed'

        if expectIndex == 0:
            if self.spawnId.before:
                self.spawnId.expect(r'.+')

            self.log.info('Installation is working.  Got Attempting message. Waiting for installation to complete and reboot ...')
            expectIndex = self.send(cmd=f'\n',expect=['.*Hit any key to stop autoboot.*'], timeout=300)
            if expectIndex == 0:
                self.log.info(f'Installation is done. Rebooted and got "Hit any key stop autoboot"')
                expectIndex = self.send(cmd='\n', expect=['Marvell>>'], timeout=300)
                if expectIndex == 0:
                    # return False if failed
                    self.log.info('Got into Marvell>> shell. Booting to ONIE ...')
                    return self.goToOniePromptFromMarvellPrompt()

                # pexpect.TIMEOUT
                if expectIndex == 2:
                    self.log.info('Timed out waiting for Marvell>> prompt')
                    return False
                
            # pexpect.TIMEOUT
            if expectIndex == 2:
                self.log.info('Timed out waiting for "Hit any key to stop autoboot')
                return False
                
        # pexpect.TIMEOUT
        if expectIndex == 3:
            return False

    def installBuild_backup(self) -> None:
        """
        build == tftp://x.x.x.x/build
        
        Install new build in ONIE shell
        If success:
            it will automatically reboot. Press <enter> key 
            on 'Hit any key to stop autoboot' to Linux shell.
            This will go into the Marvell shell. From there, boot to ONIE.

        If failed: Return False
        """
        expectIndex = self.send(cmd=f'onie-nos-install {build}',
                                expect=['Failure: Unable to install image',
                                        'Hit any key to stop autoboot',
                                        'Marvell>>',
                                        'localhost login',
                                        ],
                                timeout=180)
        if expectIndex == 0:
            return False
        
        if expectIndex == 1:
            expectIndex = self.send(cmd='\n', expect=['Marvell>>'], timeout=60)
            if expectIndex == 0:
                # return False if failed
                return self.goToOniePromptFromMarvellPrompt()

        if expectIndex == 2:
            return self.goToOniePromptFromMarvellPrompt()
        
        if expectIndex == 3:
            if self.linuxPromptLogin():
                return self.goToOniePrompt()
            else:
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
        # Sending Linux commands expects pexpect.EOF, which is the returned index=1
        # Then it timesout.  I don't know why.
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
        """
        index = self.send(cmd='onie-syseeprom', expect=[], timeout=2)

        if index == 1:
            for line in self.spawnId.before.decode('utf-8').split('\r\n'):
                # Base MAC Address     0x24   6 98:19:2C:45:4D:00
                matchRegexp = search('.*Base MAC Address +[^ ]+ +[0-9]+ +([^ ]+)', line)
                if matchRegexp:
                    # arm64 | amd
                    self.macAddress = matchRegexp.group(1)
                    self.log.info(f'MAC Address = {self.macAddress}')
                    return self.macAddress

        return self.macAddress
    
    def powerCycleDentHelper(self):
        self.powerCycleObj = PowerCycle(logObj=self.log, deviceIp=self.pduIp, deviceIpPort=None,
                                        user=self.pduLogin, password=self.pduPassword, powerCycleNumber=self.pduNumber)
        if self.powerCycleObj.telnetToDevice() == False:
            return False

        if self.powerCycleObj.reboot() == False:
            return False

        return True

    def closeSpawnId(self):
        if self.spawnId:
            self.spawnId.close()


class PowerCycle:
    """
    Usage:
        self.powerCycleObj = PowerCycle(logObj=logObj, deviceIp=pduIp, deviceIpPort=None,
                                        user=pduLogin, password=pduPassword, powerCycleNumber=pduNumber)
        if self.powerCycleObj.telnetToDevice() == False:
            return False

        if self.powerCycleObj.reboot() == False:
            return False
    """
    def __init__(self, logObj: object, deviceIp: str, deviceIpPort: int=None,
                 user: str=None, password: str=None, powerCycleNumber: str=None) -> None:
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
                self.log.info(f'PowerCycle: Sending user: {self.user} ...')
                expectIndex1 = self.send(self.user, expect=['Password'], timeout=2)
                if expectIndex1 != 0:
                    self.log.failed(f'PowerCycle: Login user name failed: {self.user}')
                    return False

                if expectIndex1 == 0:
                    #expectIndex2 = self.send(self.password, expect=['American', 'Event'], timeout=2)
                    self.spawnId.send(f'{self.password}\r\n')
                    expectIndex2 = self.spawnId.expect(['American', 'Event'], timeout=2)
                    if expectIndex2 != 0:
                        self.log.failed(f'PowerCycle: Failed to log into the power cycle device with password: {self.password}')
                        return False

                    if expectIndex2 in [0, 1]:
                        self.log.info('PowerCycle: Successfully logged into the power cycle device 1')
                        #self.reboot()
                        return

            if expectIndex == 1:
                #expectIndex3 = self.send(self.password, expect=['American', 'Event'], timeout=2)
                self.spawnId.send(f'{self.password}\r\n')
                expectIndex2 = self.spawnId.expect(['American', 'Event'], timeout=2)
                if expectIndex3 != 0:
                    self.log.failed(f'PowerCycle: Failed to log into the power cycle device with password: {self.password}')
                    return False

                if expectIndex3 in [0, 1]:
                    self.log.info('PowerCycle: Successfully logged into the power cycle device 2')
                    #self.reboot()
                    return

            if expectIndex == 2:
                self.log.info('PowerCycle: Successfully logged into the power cycle device 3')
                #self.reboot()
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
        expectIndex0 = self.send("\n", expect=['.*Control.*Event.*'], timeout=10)
        if expectIndex0 != 0:
            self.log.info('PowerCycle: Failed to see power cycle PDU')
            return
        else:
            self.log.info('PowerCycle: Got PDU!')

        time.sleep(1)
        expectIndex = self.send("1", expect=['.*Device Manager.*Event.*'], timeout=10)
        if expectIndex == 0:
            self.log.info(f'PowerCycle: Device Manager')

            time.sleep(3)
            # 2 = Outlet Management
            expectIndex = self.send("2", expect=['.*Outlet Management.*Event.*'], timeout=10)
            if expectIndex == 0:
                self.log.info(f'PowerCycle: Outlet Management')

                time.sleep(3)
                # 1 = Outlet Control/Configuration
                expectIndex = self.send("1", expect=['.*Outlet.*Control/Configuration.*Event.*'], timeout=10)
                if expectIndex == 0:
                    self.log.info(f'PowerCycle: Outlet Control/Configuration')

                    time.sleep(3)
                    expectIndex = self.send(str(self.powerCycleNumber), expect=[f'.*Outlet.*{self.powerCycleNumber}.*Event.*'], timeout=10)
                    if expectIndex == 0:

                        time.sleep(3)
                        # 1 = Control Outlet
                        expectIndex = self.send("1", expect=['.*Control.*Outlet.*Event.*'], timeout=10)
                        if expectIndex == 0:
                            self.log.info(f'PowerCycle: Control Outlet')

                            time.sleep(3)
                            # 1- Immediate On
                            # 2- Immediate Off
                            # 3- Immediate Reboot
                            self.log.info('PowerCycle: Entering 3 to reboot immediately ...')
                            expectIndex = self.send("3", expect=['.*YES.*'], timeout=10)

                            time.sleep(3)
                            if expectIndex == 0:
                                self.log.info('PowerCycle: Entering "YES" to continue')

                                time.sleep(3)
                                expectIndex = self.send("YES", expect=['.*<ENTER> to continue.*'], timeout=10)
                                if expectIndex == 0:

                                    time.sleep(3)
                                    self.log.info('PowerCycle: Pressing the enter key to continue')
                                    expectIndex = self.send("\n", expect=['.*Control.*Event.*'], timeout=10)
                                    if expectIndex == 0:
                                        self.log.info(f'PowerCycle: Successfully power cycled: {self.powerCycleNumber}')
                                        return True
        return False
    
    def send(self, cmd: str, expect: list=[], timeout: int=10) -> int:
        self.spawnId.timeout = timeout

        if self.spawnId.before:
            self.spawnId.expect(r'.+')
        
        if cmd == '\n':
            #self.spawnId.sendline()
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

            #if self.spawnId.match:
            #    print('\n---- match:', self.spawnId.match)
                
        self.log.info(f'PowerCycle: : Got expect: {expectList[index]}')            
        return index
    
    def closeSpawnId(self):
        if self.spawnId:
            self.spawnId.close()


def deployDentInit(testSessionFolder: str, tftpServerPath: str, tftpServerFolder: str,
                   srcBuildList: str, setupDict: dict, sessionLog: object) -> bool:
    """
    Install build image on Dent switches
    """
    threadList = []
    dentObjList = []

    for dentSetup in setupDict['setups']:
        for dentProperty,value in dentSetup.items():
            serialConsoleIp    = dentSetup['serialConsoleIp']
            serialConsolePort  = dentSetup['serialConsolePort']
            linuxShellLogin    = dentSetup['linuxShellLogin']
            linuxShellPassword = dentSetup['linuxShellPassword']
            pduIp              = dentSetup['pduIp']
            pduLogin           = dentSetup['pduLogin']
            pduPassword        = dentSetup['pduPassword']
            pduNumber          = dentSetup['pduNumber']

        dentBuildInstallLogFile = f'{testSessionFolder}/dentInstall-{serialConsoleIp}-{serialConsolePort}_logs'
        dentLogObj = utilities.LogTestSession(dentBuildInstallLogFile)

        dentObj = DeployDent(logObj=dentLogObj, serialConsoleIp=serialConsoleIp, serialConsolePort=serialConsolePort,
                             linuxShellLogin=linuxShellLogin, linuxShellPassword=linuxShellPassword,
                             pduIp=pduIp, pduLogin=pduLogin, pduPassword=pduPassword, pduNumber=pduNumber,
                             tftpServerPath=tftpServerPath, tftpServerFolder=tftpServerFolder, srcBuildList=srcBuildList)

        threadObj = threading.Thread(target=dentObj.updateDent, name=f'{serialConsoleIp}-{serialConsolePort}')
        threadList.append(threadObj)
        dentObjList.append(dentObj)

        #result = dentObj.updateDent()
        #print('\n---- result:', result)
        #if result:
        #    log.info('Successfully installed on Dent')
        #else:
        #    log.failed('Installing build on Dent failed')        
        #dentObj.closeSpawnId()

    # Start all the threads
    for eachThread in threadList:
        sessionLog.info(f'Starting thread name: {eachThread.name}')
        eachThread.start()

    # Wait for all threads to complete
    while True:
        breakoutCounter = 0

        for eachJoinThread in threadList:
            sessionLog.info(f'Verifying thread join completed: {eachJoinThread.name}')
            eachJoinThread.join()

            if eachJoinThread.is_alive():
                sessionLog.info(f'{eachJoinThread.name} is still alive')
            else:
                # Thread is done
                sessionLog.info(f'{eachJoinThread.name} alive == {eachJoinThread.is_alive}')
                breakoutCounter += 1

        if breakoutCounter == len(threadList):
            sessionLog.info('All threads are done')
            break
        else:
            time.sleep(1)
            continue

    for eachDentObj in dentObjList:
        eachDentObj.closeSpawnId()
            
