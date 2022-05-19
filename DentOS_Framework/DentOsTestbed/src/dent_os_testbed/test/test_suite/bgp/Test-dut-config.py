import pytest
from netmiko import ConnectHandler

dent1 = { 
    "device_type": "linux",
    "ip": "10.36.78.149",
    "username": "root",
    "password": "onl" ,
}

# Show command that we execute
	
	
cfg_file = "config_bgp_1.txt"
with ConnectHandler(**dent1) as net_connect:
    output = net_connect.send_config_from_file(cfg_file)

print(output)