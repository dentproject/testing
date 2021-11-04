import pexpect
import sys, time, re, json
from library.LIB_Utils import UI

class DENT(UI):
  '''
    Class Name: DENT
    Purpose:
        Methods relate to the function running on DENT DUT
  '''
  def __init__(self, server=None, port=None, username=None, password=None, ip=None, netmask=None ,prompt=':~#'):
    UI.__init__(self, server=server, port=port, username=username, password=password, ip=ip, netmask=netmask, prompt=prompt)

  def readConfigFile(self, file_path, friendly_name):
    with open(file_path, newline='') as jsonfile:
      data = json.load(jsonfile)
      for dev in data['devices']:
        if friendly_name == dev['friendlyName']:
          self.server = dev['consoleServer']['ip']
          self.port = dev['consoleServer']['port']
          self.username = dev['login']['userName']
          self.password = dev['login']['password']
          self.ip = dev['ip']
          self.netmask = dev['netmask']
          return
      
      self.showStep('FAIL', 'Error: Fail to find the friendlyName %s from config file %s.' % (friendly_name, file_path), '*')
      sys.exit(1)
      
  def enterUboot(self):
    '''
      Method Name: enterUboot
      Purpose:
        Enter the Uboot environment
    '''
    self.device.send('sudo reboot\r')
    retry = 0
    while retry < 6:
        i = self.device.expect(['Marvell>>','Type password to STOP autoboot'], timeout=20)

        if i == 0:
          self.showStep('PASS', '', '*')
          break
        elif i == 1:
          self.device.send('@wa23\r')
          retry += 1
        
        if retry == 6:
          self.showStep('FAIL', 'Error: Fail to enter the uboot environment.', '*')
          self.device.close()
          sys.exit(1)
  
  def enterONIE(self):
    '''
      Method Name: enterONIE
      Purpose:
        Enter Open Network Install Environment
    '''
    self.device.send('run onie_rescue\r')
    retry = 0
    while retry < 6:
        i = self.device.expect(['ONIE:/', 'Please press Enter to activate this console.','Starting kernel','Loading Open Network Install Environment'], timeout=30)

        if i == 0:
          self.showStep('PASS', '', '*')
          break
        elif i == 1:
          self.device.send('\r')
        else:
          retry += 1
          time.sleep(10)
        
        if retry == 6:
          self.showStep('FAIL', 'Error: Fail to enter ONIE.', '*')
          self.device.close()
          sys.exit(1)
  
  def installImage(self, image_url):
    '''
      Method Name: installImage
      Purpose:
        Install image via ONIE
    '''
    self.device.send('onie-nos-install %s\r' % image_url)
    retry = 0
    while retry < 10:
        i = self.device.expect(['login:',
                          'Starting systemd',
                          'Setting up base platform configuration',
                          'Switching rootfs',
                          'Press Control-C',
                          'Starting kernel',
                          'Rebooting in 3s',
                          'default profile'], timeout=60)

        if i == 0:
          self.showStep('PASS', '', '*')
          break
        else:
          retry += 1
          time.sleep(15)
        
        if retry == 10:
          self.showStep('FAIL', 'Error: Fail to upgrade the image via ONIE.', '*')
          self.device.close()
          sys.exit(1)

  def checkImageVersion(self, image_version):
    '''
      Method Name: checkImageVersion
      Purpose:
        Check the image version installed on DUT
    '''
    # DENTOS-HEAD_ONL-OS9_2021-09-02.1633-a99943d_ARM64_INSTALLED_INSTALLER
    get_image_version = re.search('(DENTOS-HEAD_ONL-.+)_INSTALLED_INSTALLER', image_version)
    if get_image_version:
      image_version = get_image_version.group(1)
    self.device.send('cat /etc/onl/SWI | cut -d: -f 2\r')
    self.device.expect(self.prompt)
    buffer = self.device.before + self.device.after
    search_image_version = re.search(image_version, buffer)
    if search_image_version:
      self.showStep('PASS', 'Image upgrade correctly to version: %s.' % search_image_version.group(0), '*')
    else:
      self.showStep('FAIL', 'Error: Fail to upgrade device.', '*')
      sys.exit(1)
  
  def rebootDUT(self):
    '''
      Method Name: rebootDUT
      Purpose:
        reboot the dut
    '''
    self.device.send('sudo reboot\r')
    retry = 0
    while retry < 15:
        i = self.device.expect(['Last login:', 
                                self.prompt, 
                                'login:', 
                                'Password:',
                                'completed successfully',
                                'Type password to STOP autoboot',
                                'Press Control-C',
                                'Mounting filesystems',
                                'Prestera Switch FW is ready',
                                'Setting up base platform configuration'], timeout=20)

        if i == 1:
          self.showStep('PASS', '', '*')
          break
        elif i == 2:
          time.sleep(10)
          self.device.send('%s\r' % self.username)
        elif i == 3:
          self.device.send('%s\r' % self.password)
        else:
          time.sleep(5)
        
        retry += 1
        
        if retry == 15:
          self.showStep('FAIL', 'Error: Fail to reboot DUT.', '*')
          self.device.close()
          sys.exit(1)

  def scpFile(self, action, local_path, remote_path, username, password, ip_address):
    '''
      Method Name: scpFile
      Purpose:
        SCP file to or from remote server
    '''
    if action.lower() == 'upload':
      scp_cmd = 'scp %s %s@%s:%s' % (local_path, username, ip_address, remote_path)
    elif action.lower() == 'download':
      scp_cmd = 'scp %s@%s:%s %s' % (username, ip_address, remote_path, local_path)

    scp_session = pexpect.spawn(scp_cmd, encoding='utf-8', codec_errors='replace')
    # print to the sys.stdout
    scp_session.logfile = sys.stdout

    scp_session.send('%s\r' % scp_cmd)
    retry = 0
    keygen_result = None
    while retry < 3 and keygen_result == None:
        i = scp_session.expect(['s password:',
                                'yes/no',
                                'ssh-keygen -f ".*" -R ".*"',
                                'No such file or directory',
                                'Permission denied',
                                'lost connection', 
                                pexpect.EOF], timeout=20)

        if i == 0:
          scp_session.send('%s\r' % password)
          retry += 1
        elif i == 1:
          scp_session.send('yes\r')
          retry += 1
        elif i == 2:
          buffer = scp_session.before + scp_session.after
          keygen_result = re.search('ssh-keygen -f ".*" -R "(.*)"', buffer, re.M)
        elif i == 6:
          self.showStep('PASS', 'Successfully scp file', '*')
          scp_session.close()
          return
        else:
          self.showStep('FAIL', 'Error: Fail to scp the file', '*')
          scp_session.close()
          sys.exit(1)
    
    if keygen_result != None:
      # Remove the known host key on server
      pexpect.run(keygen_result.group(0) + '\r')

      self.scpFile(action, local_path, remote_path, username, password, ip_address)


  def modifyNetworkInterfaceFile(self, template_path, output_path, ip_address, netmask, gateway=None):
    '''
      Method Name: modifyNetworkInterfaceFile
      Purpose:
        Modify the network interface file from a template 'NETWORK_INTERFACES_temp'
    '''
    # Modify the template file
    with open(template_path, "r") as temp_file, open(output_path, "w") as out_file:
      contents = temp_file.read()
      mgmt_interface_old = "auto eth0\niface eth0 inet dhcp\n"
      mgmt_interface = "auto ma1\
                        \niface ma1 inet static\
                        \naddress %s/%s" % (ip_address, self.netmask2cidr(netmask))
      
      if gateway != None:
        mgmt_interface += "\ngateway %s" % gateway
      mgmt_interface += "\n"

      contents = re.sub(mgmt_interface_old, mgmt_interface, contents)
      out_file.write(contents)
  
  def setDUTIP(self, template_path, output_path, ip_address, netmask, username, password, gateway=None):
    '''
      Method Name: setDUTIP
      Purpose:
        Set the IP on DUT interface ma1
      History:
        2021/10/26- 
          Change to set up the DUT IP by loading the network interface file on /etc/network/interfaces
    '''
    self.modifyNetworkInterfaceFile(template_path, output_path, ip_address, netmask, gateway)
    # scp network file
    self.device.send('\r')
    self.device.expect(self.prompt)
    self.device.send('ip addr add %s/%s dev ma1\r' % (ip_address, self.netmask2cidr(netmask)))
    self.device.expect(self.prompt)
    self.device.send('route add default gw %s\r' % gateway)
    self.device.expect(self.prompt)
    self.scpFile('upload', output_path, '/etc/network/interfaces', username, password, ip_address)
    # reload to apply the network interface
    self.device.send('\r')
    self.device.expect(self.prompt)
    self.device.send('ifreload -a\r')
    self.device.expect(self.prompt, timeout=20)
    
  def chkDUTIP(self, ip_address):
    self.device.send('ifconfig ma1\r')
    self.device.expect(self.prompt)
    buffer = self.device.before + self.device.after
    search_ip = re.search(ip_address, buffer)
    if search_ip:
      self.showStep('PASS', 'IP is set correctly.', '*')
    else:
      self.showStep('FAIL', 'Fail to set the IP.', '*')
      sys.exit(1)
