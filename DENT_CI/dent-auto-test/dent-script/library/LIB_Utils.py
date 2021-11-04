import pexpect
import sys, time, re, json
import json

class UI():
  '''
    Class Name: UI
    Purpose:
        Methods relate to the DUT user interface or utility
  '''
  def __init__(self, prompt, server, port, username, password, ip, netmask):
    self.device = None
    self.prompt = prompt
    self.server = server
    self.port = port
    self.username = username
    self.password = password
    self.ip = ip
    self.netmask = netmask
    self.gateway = '192.168.0.254'

  def initConsole(self):
    '''
      Method Name: getDivider
      Purpose:
        Initialize the spawn session
    '''
    try:
      self.device = pexpect.spawn('telnet %s %s' % (self.server, self.port), encoding='utf-8', codec_errors='replace')
      # print to the sys.stdout
      self.device.logfile = sys.stdout

    except Exception as e:
      self.showStep('FAIL', 'Error: Fail to initialize the Telnet spawn session. Exception: %s' % str(e), '*')
      sys.exit(1)

    self.device.send('\r')
    retry = 0
    while retry < 6:
      i = self.device.expect(['Last login:', self.prompt, 'login:','Password:'], timeout=10)
      if i == 1:
        self.showStep('PASS', 'Login to DUT successfully.', '*')
        break
      elif i == 2:
        self.device.send('%s\r' % self.username)
      elif i == 3:
        self.device.send('%s\r' % self.password)
      
      retry += 1
      
      if retry == 6:
        self.showStep('FAIL', 'Error: Fail to login to the DUT.', '*')
        sys.exit(1)
      
      time.sleep(3)

  def closeConsole(self):
    '''
      Method Name: closeConsole
      Purpose:
        Close the spawn session
    '''
    self.device.close()

  def getDivider(self, title: str, divider_symbol: str) -> str:
    '''
      Method Name: getDivider
      Purpose:
        Create the divider to show the formatted steps or result
      Input:
        title - String to include in the divider
        divider_symbol - Symbol as a style of the divider
    '''
    if title == '':
      centered_title = '{:{divider}^{width}}'.format('', divider=divider_symbol, width=140)
    else:
      centered_title = '{:{divider}^{width}}'.format(' %s ' %title, divider=divider_symbol, width=140)

    wirte_lines = ''

    # Add title and wrap.
    wirte_lines += centered_title + '\n\n'

    return wirte_lines

  def showStep(self, step, action, devider_symbol):
    '''
      Method Name: showStep
      Purpose:
        Show the step and its action or the result
      Input:
        step - Step number or result
        action - The explanation of the step
        divider_symbol - Symbol as a style of the divider
    '''
    print('\r')
    lines = self.getDivider(step, devider_symbol) + '\r' + action
    print(lines)
  
  # convert netmask ip to cidr number
  def netmask2cidr(self, netmask):
    '''
      Method Name: netmask2cidr
      Purpose:
        Convert netmask ip to CIDR number
      Input:
        netmask - netmask ip
    '''
    return sum([bin(int(x)).count('1') for x in netmask.split('.')])