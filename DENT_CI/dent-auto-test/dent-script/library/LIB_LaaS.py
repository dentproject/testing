import requests
import os, sys
from http import HTTPStatus
import urllib3

# To disable the ssl warning message on console
# InsecureRequestWarning: Unverified HTTPS request is being made. 
# Adding certificate verification is strongly advised. 
# See: https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
class LaaSApi():
  '''
    Class Name: LaaSApi
    Purpose:
        Methods relate to the LaaS Api
  '''
  def __init__(self):
    self.SERVER_URL = "https://172.31.12.250:443/api/1.0"
    self.MAX_RETRY_TIME = 20
    self.is_debug_mode = False
    self.using_ssl = False
    self.headers = dict()

  def get_token(self, username, password):
    '''
      Method Name: get_token
      Purpose:
        Get the token by username and password
      Input:
        username - username of LaaS account
        password - password of LaaS account
    '''
    account = {"username": username, "password": password}
    auth_response = requests.post(self.SERVER_URL + "/auth/tokens/", json=account, verify=self.using_ssl)
    if auth_response.status_code != HTTPStatus.CREATED:
        print("Get token:", auth_response.json())
        exit(1)
    return auth_response.json()["token"]

  def delete_token(self):
    '''
      Method Name: delete_token
      Purpose:
        delete the token
    '''
    delete_response = requests.delete(self.SERVER_URL + "/auth/tokens/by-token", headers=self.headers, verify=self.using_ssl)

  def login(self, username):
    '''
      Method Name: login
      Purpose:
        Login to LaaS with token
      Input:
        username - username of LaaS account
        password - required by user input
    '''
    global password
    os.system("stty -echo")
    password = input()
    os.system("stty echo")
    token = self.get_token(username, password)
    self.headers["Authorization"] = 'Bearer ' + token
    if self.is_debug_mode:
      print("Login successfully.")

  def relogin(self):
    '''
      Method Name: relogin
      Purpose:
        Retry to login to LaaS
    '''
    global username, password, retry_time
    if retry_time == self.MAX_RETRY_TIME:
      print("Retry limit reached")
      exit(1)
    token = self.get_token(username, password)
    self.headers["Authorization"] = 'Bearer ' + token
    retry_time += 1
    if self.is_debug_mode:
      print("Re-login successfully.")
      print("Retry time:", retry_time)

  def logout(self):
    '''
      Method Name: logout
      Purpose:
        Logout from LaaS
    '''
    self.delete_token()
    if self.is_debug_mode:
        print("Logout successfully.")

  def get_reservation_information(self, reservation_id):
    '''
      Method Name: get_reservation_information
      Purpose:
        Get the reservation information by calling the api with reservation id
      Input:
        reservation_id - the id of reservation
    '''
    api_url = self.SERVER_URL + '/reservations/' + reservation_id
    reservation_response = requests.get(api_url, headers=self.headers, verify=self.using_ssl)
    while reservation_response.status_code == HTTPStatus.UNAUTHORIZED:
      self.relogin()
      reservation_response = requests.get(api_url, headers=self.headers, verify=self.using_ssl)
    if reservation_response.status_code == HTTPStatus.OK:
      return reservation_response
    else:
      print("Error: the API- %s returns error response- %s" % (api_url, devices_response.status_code), file=sys.stderr)
      sys.exit(1)
  
  def get_device_information(self, device_name):
    '''
      Method Name: get_device_information
      Purpose:
        Get the device information by calling the api with device name
      Input:
        device_name - the full device name
    '''
    api_url = self.SERVER_URL + '/devices/' + requests.utils.quote(device_name, safe='')
    device_info_response = requests.get(api_url, headers=self.headers, verify=self.using_ssl)
    while device_info_response.status_code == HTTPStatus.UNAUTHORIZED:
      self.relogin()
      device_info_response = requests.get(api_url, headers=self.headers, verify=self.using_ssl)
    if device_info_response.status_code == HTTPStatus.OK:
      return device_info_response
    else:
      print("Error: the API- %s returns error response- %s" % (api_url, device_info_response.status_code), file=sys.stderr)
      sys.exit(1)