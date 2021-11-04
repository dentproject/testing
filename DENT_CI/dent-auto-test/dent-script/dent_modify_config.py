'''
This script will output a configuration file for running the DENT testing by retrieving device information from LaaS server.

Python module that is required:
    - requests

Parameters:
    --reservation_id, -rid: The id of reservation on LaaS.
    --user_account, -u: The laas user account.
    --output_path, -op: The output json file path.
'''
import argparse, json, os
from library.LIB_LaaS import LaaSApi

def process_command():
  '''
    Method Name: process_command
    Purpose:
      Script input argument
  '''
  global current_dir
  current_dir = os.path.dirname(os.path.abspath(__file__))
  parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
  parser.add_argument("--reservation_id", "-rid", required=True, help="The id of reservation on LaaS.")
  parser.add_argument("--user_account", "-u", required=True, help="The laas user account.")
  parser.add_argument("--output_path", "-op", nargs='?', type=str, default=os.path.join(current_dir, 'configuration_test.json'), required=False, help="The output json file path.")
  return parser.parse_args()

if __name__ == '__main__':
  args = process_command()

  laasApi = LaaSApi()
  
  # 0) Login to LaaS and get a token with authorization
  laasApi.login(args.user_account)

  # 1) Get the device by reservation id
  print("Get the device by reservation id: %s" % args.reservation_id)
  device = laasApi.get_reservation_information(args.reservation_id).json()['devices'][0]

  # 2) Get the device information
  print("Get the device infomation: device = %s" % device)
  device_info = laasApi.get_device_information(device).json()

  # 3) modify configuration file
  with open(os.path.join(current_dir, 'config_temp.json'), 'r') as f:
    data = json.load(f)
    data['devices'][0]['friendlyName'] = device_info['name']
    data['devices'][0]['ip'] = device_info['mgmt_ips'][0]['ip']
    data['devices'][0]['login']['userName'] = device_info['accounts'][0]['username']
    data['devices'][0]['login']['password'] = device_info['accounts'][0]['password']
    data['devices'][0]['consoleServer']['ip'] = device_info['console_ports_ips'][0]['ip']
    data['devices'][0]['consoleServer']['port'] = device_info['console_ports_ips'][0]['port']
  
  with open(args.output_path, 'w') as f:
    json.dump(data, f, indent=4)

  laasApi.logout()