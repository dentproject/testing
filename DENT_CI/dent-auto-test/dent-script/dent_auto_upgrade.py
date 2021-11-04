'''
This script upgrade the DUT with image from input link (image on HTTP server)

Python module that is required:
    - pexpect

Parameters:
    --device, -dev: The DUT that is going to be upgraded. Define as 'friendlyName' in configuration.json..
    --image_url, -img: The url link to the image file.
    --config, -c: The path to the configuration file.
    --network_file, -nf: The path to the network interface file.
'''

from library.LIB_DENT import DENT
import argparse, json, time, os

def process_command():
  '''
    Method Name: process_command
    Purpose:
      Script input argument
  '''
  parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
  parser.add_argument('--device', '-dev', type=str, required=True, help="\nThe DUT that is going to be upgraded. Define as 'friendlyName' in configuration.json.")
  parser.add_argument('--image_url', '-img', type=str, required=True, help="\nThe url link to the image file.")
  parser.add_argument('--config', '-c', type=str, required=True, help="\nThe path to the configuration file.")
  parser.add_argument("--network_file", "-nf", type=str, required=True, help="The path where the network interface file is located. This file is along with the DENT testing code.")
  return parser.parse_args()

if __name__ == '__main__':
  args = process_command()

  device = DENT()
  device.readConfigFile(file_path=args.config, friendly_name=args.device)

  device.showStep('STEP#01', 'Connect to %s port %s' % (device.server, device.port), '#')
  device.showStep('Terminal Output from Console Server', '', '=')
  device.initConsole()

  device.showStep('STEP#02', 'Reboot DUT and enter the uboot environment', '#')
  device.showStep('Terminal Output from Console Server', '', '=')
  device.enterUboot()

  device.showStep('STEP#03', 'Enter the ONIE', '#')
  device.showStep('Terminal Output from Console Server', '', '=')
  device.enterONIE()

  device.showStep('STEP#04', 'Upgrade image through ONIE', '#')
  device.showStep('Terminal Output from Console Server', '', '=')
  device.installImage(image_url=args.image_url)
  device.closeConsole()

  device.showStep('STEP#05', 'Login to DUT after image installation', '#')
  device.showStep('Terminal Output from Console Server', '', '=')
  device.initConsole()

  device.showStep('STEP#06', 'Check the image version', '#')
  device.showStep('Terminal Output from Console Server', '', '=')
  device.checkImageVersion(image_version=args.image_url)

  device.showStep('STEP#07-1', 'Set DUT interface ma1 with IP %s and mask %s' % (device.ip, device.netmask), '#')
  device.showStep('Terminal Output from Console Server', '', '=')
  current_dir = os.path.dirname(os.path.abspath(__file__))
  temp_file = os.path.join(current_dir, 'NETWORK_INTERFACES_temp')
  device.setDUTIP(template_path=temp_file, output_path=args.network_file, 
                  ip_address=device.ip, netmask=device.netmask,
                  username=device.username, password=device.password, gateway=device.gateway)
  device.showStep('STEP#07-2', 'Reboot DUT', '#')
  device.showStep('Terminal Output from Console Server', '', '=')
  device.rebootDUT()
  device.showStep('STEP#07-3', 'Check DUT IP is set', '#')
  device.showStep('Terminal Output from Console Server', '', '=')
  device.chkDUTIP(ip_address=device.ip)

  device.showStep('Close Console', '', '=')
  device.closeConsole()