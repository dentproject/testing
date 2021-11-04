import os
import sys
import yaml
import json
import time
import requests
import datetime
import urllib3
import argparse
import datetime
import re
from http import HTTPStatus
from library.LIB_LaaS import LaaSApi

laasApi = LaaSApi()

testbedReg = r"testbed(\d{2})"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
RESERVATION_LIST_HEADER = ["Id", "Username", "Domain Name", ["Requested/Reserved", "Device(s)"], ["Reservation", "Type"], "Duration", "Start/End Time", "Status"]
RESERVATION_STATUS = 'verifying,pending,active,finished,cancelled,terminated'
MAX_RETRY_TIME = 20
SERVER_URL = laasApi.SERVER_URL
NUMBER_OF_TESTBED = 6
NUMBER_OF_VM = 64
TESTBED_NAME_PATTERN = "/tainan/sonic/vm/testbed%02d/"
headers = {}
using_ssl = False
is_debug_mode = False
retry_time = 0
username = ''
password = ''

def get_devices_list(devices):
    devices_list = devices.split(",")
    if is_debug_mode:
        print("devices_list =", devices_list)
    return devices_list

def get_device_types_dict(device_types):
    device_types_list = device_types.split(",")
    device_types_dict = {}
    for device_type in device_types_list:
        type_num = device_type.split(":")
        device_types_dict[type_num[0]] = int(type_num[1])
    if is_debug_mode:
        print("device_types_dict =", device_types_dict)
    return device_types_dict

def get_token(username, password):
    account = {"username": username, "password": password}
    auth_response = requests.post(SERVER_URL + "/auth/tokens/", json=account, verify=using_ssl)
    if auth_response.status_code != HTTPStatus.CREATED:
        print("Get token:", auth_response.json())
        exit(1)
    return auth_response.json()["token"]

def delete_token():
    delete_response = requests.delete(SERVER_URL + "/auth/tokens/by-token", headers=headers, verify=using_ssl)

def create_reservation(request_content):
    create_response = requests.post(SERVER_URL + "/reservations/actions/creations/",
                                    json=request_content, headers=headers, verify=using_ssl)
    while create_response.status_code == HTTPStatus.UNAUTHORIZED:
        relogin()
        create_response = requests.post(SERVER_URL + "/reservations/actions/creations/",
                                        json=request_content, headers=headers, verify=using_ssl)
    if is_debug_mode:
        print("Create reservation:", create_response.json())
    return create_response

def delete_reservation(reservation_id):
    delete_response = requests.post(SERVER_URL + "/reservations/" + str(reservation_id) + "/actions/deletions/",
                                    headers=headers, verify=using_ssl)
    while delete_response.status_code == HTTPStatus.UNAUTHORIZED:
        relogin()
        delete_response = requests.post(SERVER_URL + "/reservations/" + str(reservation_id) + "/actions/deletions/",
                                        headers=headers, verify=using_ssl)
    if is_debug_mode:
        print("Delete reservation:", delete_response.json())

def get_device_information(device_name):
    device_response = requests.get(SERVER_URL + "/devices/" + requests.utils.quote(device_name, safe=''), headers=headers, verify=using_ssl)
    while device_response.status_code == HTTPStatus.UNAUTHORIZED:
        relogin()
        device_response = requests.get(SERVER_URL + "/devices/" + requests.utils.quote(device_name, safe=''), headers=headers, verify=using_ssl)
    if is_debug_mode:
        print("List device:", device_response.json())
    return device_response

def get_reservation_information(reservation_id):
    reservation_list_response = requests.get(SERVER_URL + "/reservations/" + str(reservation_id), headers=headers, verify=using_ssl)
    while reservation_list_response.status_code == HTTPStatus.UNAUTHORIZED:
        relogin()
        reservation_list_response = requests.get(SERVER_URL + "/reservations/" + str(reservation_id), headers=headers, verify=using_ssl)
    if is_debug_mode:
        print("List reservation:", reservation_list_response.json())
    return reservation_list_response

def get_all_reservation_information_of_user(username, status_list=RESERVATION_STATUS):
    check_url = f"{SERVER_URL}/reservations/?page=1&page_size=1&user={username}&status={','.join(status_list)}"
    reservation_check_response = requests.get(check_url, headers=headers, verify=using_ssl)
    while reservation_check_response.status_code == HTTPStatus.UNAUTHORIZED:
        relogin()
        reservation_check_response = requests.get(check_url, headers=headers, verify=using_ssl)
    item_count = reservation_check_response.json()['item_count']
    if is_debug_mode:
        print(f"Item count: {item_count}")
    if item_count == 0:
        item_count = 1
    list_url = f"{SERVER_URL}/reservations/?page=1&page_size={item_count}&user={username}&status={','.join(status_list)}"
    reservation_list_response = requests.get(list_url, headers=headers, verify=using_ssl)
    while reservation_list_response.status_code == HTTPStatus.UNAUTHORIZED:
        relogin()
        reservation_list_response = requests.get(list_url, headers=headers, verify=using_ssl)
    if is_debug_mode:
        print(f"List reservation: {reservation_list_response.json()}")
    return reservation_list_response

def login(username):
    global password
    print(SERVER_URL)
    os.system("stty -echo")
    password = input()
    os.system("stty echo")
    token = get_token(username, password)
    headers["Authorization"] = 'Bearer ' + token
    if is_debug_mode:
        print("Login successfully.")

def relogin():
    global username, password, retry_time
    if retry_time == MAX_RETRY_TIME:
            print("Retry limit reached")
            exit(1)
    token = get_token(username, password)
    headers["Authorization"] = 'Bearer ' + token
    retry_time += 1
    if is_debug_mode:
        print("Re-login successfully.")
        print("Retry time:", retry_time)

def logout():
    delete_token()
    if is_debug_mode:
        print("Logout successfully.")

def reserve_with_device_name(domain_name, devices: list, duration, type, trigger_url=""):
    reservation_request = {
        "type": type if not type == "" else "stand-by" ,
        "domain_name": domain_name,
        "definition": {
            "devices": devices,
            "device_types": {},
            "duration": duration
        },
        "trigger_url": trigger_url
    }
    create_response = create_reservation(reservation_request)
    if is_debug_mode:
        print("Reserve with name:", create_response.json())
    return create_response

def reserve_with_device_type(domain_name, device_types: dict, duration, type, trigger_url=""):
    reservation_request = {
        "type": type if not type == "" else "stand-by" ,
        "domain_name": domain_name,
        "definition": {
            "devices": [],
            "device_types": device_types,
            "duration": duration
        },
        "trigger_url": trigger_url
    }
    create_response = create_reservation(reservation_request)
    if is_debug_mode:
        print("Reserve with type:", create_response.json())
    return create_response

def reserve_with_device_name_and_type(domain_name, devices: list, device_types: dict, duration, type, trigger_url=""):
    reservation_request = {
        "type": type if not type == "" else "stand-by" ,
        "domain_name": domain_name,
        "definition": {
            "devices": devices,
            "device_types": device_types,
            "duration": duration
        },
        "trigger_url": trigger_url
    }
    create_response = create_reservation(reservation_request)
    if is_debug_mode:
        print("Reserve with name and type:", create_response.json())
    return create_response

def wait_for_reservation_verified(reservation_id):
    reservation_list_response = get_reservation_information(reservation_id)
    while reservation_list_response.json()["status"] == "verifying":
        reservation_list_response = get_reservation_information(reservation_id)
    if is_debug_mode:
        print("Verified reservation:", reservation_list_response.json())
    return reservation_list_response

def is_reservation_start_now(reservation_response):
    start_time = reservation_response.json()["start_time"]
    reservation_start_time = start_time[:len(start_time)-3] + start_time[len(start_time)-2:]
    if datetime.datetime.strptime(reservation_start_time, "%Y-%m-%dT%H:%M:%S%z") > datetime.datetime.now(tz=datetime.timezone.utc):
        if is_debug_mode:
            print("Reservation is not active!")
        delete_reservation(reservation_response.json()["id"])
        return False
    return True

def find_vm_start_id(vm_list):
    filter_vm_list = []
    testbed_id = ""
    for vm in vm_list:
        if re.search(testbedReg, vm):
            filter_vm_list.append(vm)
            current_testbed_id = re.search(testbedReg, vm).group(1)
            if testbed_id == "":
                testbed_id = current_testbed_id
            elif testbed_id != current_testbed_id:
                print("VM in different testbed!")
                exit(1)
    if filter_vm_list == []:
        return check_testbed_vm_usage()[0] + "00"
    sorted_vm_list = sorted(filter_vm_list, key=lambda vm: int(vm.rsplit("/", 1)[1]))
    if is_debug_mode:
        print("Sorted vm list:", sorted_vm_list)
    return testbed_id + "%02d" % (int(sorted_vm_list[0].rsplit("/", 1)[1]) - 1)

def check_testbed_vm_usage():
    testbed_candidate = {}
    for testbed_id in range(1,(1 + NUMBER_OF_TESTBED)):
        type_name = TESTBED_NAME_PATTERN % testbed_id
        available = 0
        total = 0
        for vm_id in range(1,(1 + NUMBER_OF_VM)):
            device_name = type_name + str(vm_id)
            device_response = get_device_information(device_name)
            if device_response.status_code == HTTPStatus.OK:
                device_status = get_device_information(device_name).json()["status"]
                if device_status != "disabled":
                    total += 1
                    if device_status == "available":
                        available += 1
        testbed_candidate["%02d" % testbed_id] = (available, total)
    sorted_testbed_candidate = {k: v for k, v in sorted(testbed_candidate.items(), key=lambda item: item[1], reverse=True)}
    if is_debug_mode:
        print("Sorted testbed candidate:", sorted_testbed_candidate)
    return list(sorted_testbed_candidate)

def sleep_until_the_device_available(msg, start_time):
    datetime_start_time = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
    time.sleep((datetime_start_time-datetime.datetime.utcnow()).total_seconds())
    print(msg)

def get_require_devices_info(request_definition):
    total_vm = 0
    total_vm = sum(abs(request_definition['device_types'][item]) for item in request_definition['device_types'])
    return_list = []
    return_list.extend(sorted(request_definition['devices']))
    return_list.append(f"Required number of VM: {total_vm}")
    return return_list

def get_reserved_devices_info(device_list):
    dut_list = []
    vm_list = []
    for device in device_list:
        if "/tainan/sonic/vm/" in device:
            vm_list.append(device)
        else:
            dut_list.append(device)
    return_list = []
    return_list.extend(sorted(dut_list))
    return_list.extend(sorted(vm_list, key=lambda vm: int(vm.rsplit("/", 1)[1])))
    return return_list

def convert_time_to_string(time):
    time = f"{time.rsplit(':', 1)[0]}{time.rsplit(':', 1)[1]}"
    date_time_obj = datetime.datetime.strptime(time, '%Y-%m-%dT%H:%M:%S%z')
    return date_time_obj.strftime("%Y-%m-%d@%H:%M")

def calculate_max_height(input_list):
    max_height = 0
    for index in range(len(input_list)):
        if isinstance(input_list[index], list):
            max_height = len(input_list[index]) if len(input_list[index]) > max_height else max_height
        else:
            max_height = 1 if 1 > max_height else max_height
    return max_height

def calculate_max_length(input_list, max_length, is_header=False):
    if max_length == []:
        max_length = [0] * len(input_list)
    for index in range(len(input_list)):
        if isinstance(input_list[index], list):
            for string in input_list[index]:
                length = len(string) + 2 if is_header or index == (len(input_list) - 1) else len(string) + 3
                max_length[index] = length if length > max_length[index] else max_length[index]
        else:
            length = len(input_list[index]) + 2
            max_length[index] = length if length > max_length[index] else max_length[index]
    return max_length

def get_require_info_of_reservation_list(dictionary_list):
    require_info_list = []
    for info in dictionary_list:
        duration_info = f"{str(int(info['definition']['duration']/60))} min"
        try:
            time_info = f"{convert_time_to_string(info['start_time'])}/{convert_time_to_string(info['end_time'])}"
        except Exception:
            time_info = "N/A"
        if info['devices'] == []:
            devices_info = get_require_devices_info(info['definition'])
        else:
            devices_info = get_reserved_devices_info(info['devices'])
        require_info = [str(info['id']), info['username'], info['domain_name'], devices_info, info['type'], duration_info, time_info, info['status']]
        require_info_list.append(require_info)
    return require_info_list

def print_table(header, content):
    max_length_list = []
    max_length_list = calculate_max_length(header, max_length_list, is_header=True)

    for record in content:
        max_length_list = calculate_max_length(record, max_length_list)

    devider = "+"
    for max_length in max_length_list:
        devider = f"{devider}{'-' * max_length}+"
    print(devider)

    for row_index in range(calculate_max_height(header)):
        row_content = "|"
        for col_index in range(len(max_length_list)):
            if isinstance(header[col_index], list):
                start_space = int((max_length_list[col_index] - len(header[col_index][row_index]))/2)
                end_space = max_length_list[col_index] - len(header[col_index][row_index]) - start_space
                row_content = f"{row_content}{' ' * start_space}{header[col_index][row_index]}{' ' * end_space}|"
            else:
                if row_index == 0:
                    start_space = int((max_length_list[col_index] - len(header[col_index]))/2)
                    end_space = max_length_list[col_index] - len(header[col_index]) - start_space
                    row_content = f"{row_content}{' ' * start_space}{header[col_index]}{' ' * end_space}|"
                else:
                    row_content = f"{row_content}{' ' * max_length_list[col_index]}|"
        print(row_content)
    print(devider)

    for record in content:
        for row_index in range(calculate_max_height(record)):
            row_content = "|"
            for col_index in range(len(max_length_list)):
                if isinstance(record[col_index], list):
                    start_space = 1
                    end_space = max_length_list[col_index] - len(record[col_index][row_index]) - start_space
                    row_content = f"{row_content}{' ' * start_space}{record[col_index][row_index]}{' ' * end_space}|" \
                              if row_index == (calculate_max_height(record) - 1) else \
                              f"{row_content}{' ' * start_space}{record[col_index][row_index]},{' ' * (end_space - 1)}|"
                else:
                    if row_index == 0:
                        start_space = 1
                        end_space = max_length_list[col_index] - len(record[col_index]) - start_space
                        row_content = f"{row_content}{' ' * start_space}{record[col_index]}{' ' * end_space}|"
                    else:
                        row_content = f"{row_content}{' ' * max_length_list[col_index]}|"
            print(row_content)
    print(devider)

def _build_parser():
    # Create global parser for global argument. Note 'add_help=False'.
    global_parser = argparse.ArgumentParser(add_help=False)
    global_parser.add_argument("--no-ssl", help="disable checking ssl", action="store_true",dest="disable_ssl")
    global_parser.add_argument("--debug", help="enable debug mode", action="store_true",dest="debug")
    global_parser.add_argument("-u", "--useraccount", help="laas user account", default="", dest="useraccount")

    parser = argparse.ArgumentParser()
    parser.add_argument("--no-ssl", help="disable checking ssl", action="store_true", dest="disable_ssl")
    parser.add_argument("--debug", help="enable debug mode", action="store_true",dest="debug")

    action = parser.add_subparsers(dest="action", metavar="ACTION")
    action.required = True

    # Request devices
    request_parser = action.add_parser("request", help="request the devices", parents=[global_parser])

    request_method = request_parser.add_subparsers(dest="request_method", metavar="METHOD")
    request_method.required = True

    # Reserve with device name
    name_parser = request_method.add_parser("name", help="reserve with device name", parents=[global_parser])
    name_parser.add_argument("-t", "--type", help="reservation type",
                             dest="reservation_type", default="stand-by")
    name_parser.add_argument("domain_name", help="name of the domain",
                             metavar="DOMAIN")
    name_parser.add_argument("devices",
                             help="name of the device, use ',' to separate multiple devices",
                             metavar="DEVICES")
    name_parser.add_argument("duration", help="duration of the reservation",
                             metavar="DURATION")
    name_parser.add_argument("-T", "--trigger-url", help="url for trigger remote task",
                             dest="trigger_url")

    # Reserve with device type
    type_parser = request_method.add_parser("type", help="reserve with device type", parents=[global_parser])
    type_parser.add_argument("-t", "--type", help="reservation type",
                             dest="reservation_type", default="stand-by")
    type_parser.add_argument("domain_name", help="name of the domain",
                             metavar="DOMAIN")
    type_parser.add_argument("device_types",
                             help="name of the device type and require number, use ':' to combine the type and number, and use ',' to separate multiple types",
                             metavar="DEVICE_TYPES")
    type_parser.add_argument("duration", help="duration of the reservation",
                             metavar="DURATION")
    type_parser.add_argument("-T", "--trigger-url", help="url for trigger remote task",
                             dest="trigger_url")

    # Reserve with device name and type
    both_parser = request_method.add_parser("both", help="reserve with device name and type", parents=[global_parser])
    both_parser.add_argument("-t", "--type", help="reservation type",
                             dest="reservation_type", default="stand-by")
    both_parser.add_argument("domain_name", help="name of the domain",
                             metavar="DOMAIN")
    both_parser.add_argument("devices",
                             help="name of the device, use ',' to separate multiple devices",
                             metavar="DEVICES")
    both_parser.add_argument("device_types",
                             help="name of the device type and require number, use ':' to combine the type and number, and use ',' to separate multiple types",
                             metavar="DEVICE_TYPES")
    both_parser.add_argument("duration", help="duration of the reservation",
                             metavar="DURATION")
    both_parser.add_argument("-T", "--trigger-url", help="url for trigger remote task",
                             dest="trigger_url")

    # Release devices
    release_parser = action.add_parser("release", help="release the devices", parents=[global_parser])
    release_parser.add_argument("reservation_id", help="id of the reservation",
                                metavar="RESERVATION_ID")

    # Get information
    get_parser = action.add_parser("get", help="get information", parents=[global_parser])

    get_item = get_parser.add_subparsers(dest="get_item", metavar="ITEM")
    get_item.required = True

    reservation_info_parser = get_item.add_parser("reservation", help="get reservation information", parents=[global_parser])
    reservation_category_parser = reservation_info_parser.add_subparsers(dest="reservation_category", metavar="CATEGORY")
    reservation_category_parser.required = True

    # Get the VM start id
    vm_start_id_parser = reservation_category_parser.add_parser("vm-start-id", help="get the start id of VMs", parents=[global_parser])
    vm_start_id_parser.add_argument("reservation_id", help="id of the reservation", metavar="RESERVATION_ID")

    # Get the reservation list with the specific user
    reservation_user_parser = reservation_category_parser.add_parser("user", help="get user's reservation information", parents=[global_parser])
    reservation_user_parser.add_argument("username", help="user who makes the reservaions", metavar="USERNAME")
    reservation_user_parser.add_argument("-s", "--status", help="reservation status",
                                          dest="reservation_status", default=RESERVATION_STATUS)

    # Get the device info (DENT project)
    device_info_parser = reservation_category_parser.add_parser("device-info", help="get the information of device", parents=[global_parser])
    device_info_parser.add_argument("reservation_id", help="id of the reservation", metavar="RESERVATION_ID")

    return parser

if __name__ == '__main__':
    parser = _build_parser()
    args = parser.parse_args()
    if args.disable_ssl:
        using_ssl = False
    if args.debug:
        is_debug_mode = True
    useraccount = args.useraccount
    login(useraccount)

    # request resources
    if args.action == "request":
        # Reserve with device name
        if args.request_method == "name":
            reserve_response = reserve_with_device_name(args.domain_name, get_devices_list(args.devices),
                                                        duration=int(args.duration), type=args.reservation_type,
                                                        trigger_url=args.trigger_url)
            verified_reservation_response = wait_for_reservation_verified(reserve_response.json()["result"]["id"])
            if not (verified_reservation_response.json()["status"] == "pending" or verified_reservation_response.json()["status"] == "active"):
                print("0")
            else:
                print(verified_reservation_response.json()["id"])
        # Reserve with device type
        elif args.request_method == "type":
            reserve_response = reserve_with_device_type(args.domain_name, get_device_types_dict(args.device_types),
                                                        duration=int(args.duration), type=args.reservation_type,
                                                        trigger_url=args.trigger_url)
            verified_reservation_response = wait_for_reservation_verified(reserve_response.json()["result"]["id"])
            if not (verified_reservation_response.json()["status"] == "pending" or verified_reservation_response.json()["status"] == "active"):
                print("0")
            else:
                print(verified_reservation_response.json()["id"])
        # Reserve with device name and type
        elif args.request_method == "both":
            reserve_response = reserve_with_device_name_and_type(args.domain_name, get_devices_list(args.devices),
                                                                 get_device_types_dict(args.device_types),
                                                                 duration=int(args.duration), type=args.reservation_type,
                                                                 trigger_url=args.trigger_url)
            verified_reservation_response = wait_for_reservation_verified(reserve_response.json()["result"]["id"])
            if not (verified_reservation_response.json()["status"] == "pending" or verified_reservation_response.json()["status"] == "active"):
                print("0")
            else:
                print(verified_reservation_response.json()["id"])
    elif args.action == "release":
        delete_reservation(args.reservation_id)
    elif args.action == "get":
        if args.get_item == "reservation":
            if args.reservation_category == "vm-start-id":
                reservation_list_response = get_reservation_information(args.reservation_id)
                print(find_vm_start_id(reservation_list_response.json()["devices"]))
            elif args.reservation_category == "user":
                reservation_status_list = args.reservation_status.split(",")
                reservation_list_response = get_all_reservation_information_of_user(status_list=reservation_status_list, username=args.username)
                print_content = get_require_info_of_reservation_list(reservation_list_response.json()['results'])
                print_table(RESERVATION_LIST_HEADER, print_content)
            # For DENT project
            elif args.reservation_category == "device-info":
                reservation_list_response = get_reservation_information(args.reservation_id)
                current_dir = os.path.dirname(os.path.abspath(__file__))
                domain_name = reservation_list_response.json()["domain_name"]
                device = reservation_list_response.json()["devices"][0]
                with open(os.path.join(current_dir, 'testbed_device_mapping.json'), 'r') as f:
                    data = json.load(f)
                    testbed = data[domain_name]["testbed"] if device in data[domain_name]["device"] else "master"
                print(domain_name + "," + device + "," + testbed)

    logout()