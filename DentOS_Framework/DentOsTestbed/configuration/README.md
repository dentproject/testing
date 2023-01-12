# Configuration for running the tests

Test Bed configuration file format
--------------------
```
{
    "devices" : [
       {
            "friendlyName":"Dent OOB switch1", # Display Name
            "os":"dentos",                     # OS type options [ 'dentos', 'cumulus', 'ixnetwork']
            "type" : "OUT_OF_BOUND_SWITCH",    # device type [DISTRIBUTION_ROUTER, AGGREGATION_ROUTER,
                                               #              BLACKFOOT_ROUTER, OUT_OF_BOUND_SWITCH,
                                               #              INFRA_SWITCH, ROUTER_SWITCH, LTE_MODEM,
                                               #              TRAFFIC_HELPER, TRAFFIC_GENERATOR,
                                               #              CONSOLE_SERVER]
            "hostName": "oob_sw1",             # host name
            "ip": "10.1.4.4",                  # mgmt ip address to reach the device
            "login":{                          # Login details
                "userName":"root",             # User name to login (should have sudo permissions)
                "password":"onl"               # Password
            },
            "serialDev":"/dev/ttyUSB6",        # Serial console access
            "baudrate": 115200,                # Baud rate
            "links" : [                        # Link details
                ["eth0", "oob_sw2:swp40"],     # ["local port", "remote port:remote port"]
                ...
            ]

       } ...
     ]
    "operator" : "dent",                       # Operator name
    "topology" : "gordion-knot",               # topology name
    "force_discovery" : false                  # if we want to retrigger discovery
}
```

Configurations
---------------------

Below is the directory structure expected for testbed configuration

- configurations/
  - testbed_config
    - [testbed_name1]
      - [dut1]
        - [dut1]_NTP
        - [dut1]_QUAGGA_CONFIG
        - [dut1]_DHCP
        - [dut1]_QUAGGA_DAEMONS
        - [dut1]_HOSTNAME
        - [dut1]_QUAGGA_VTYSH
        - [dut1]_HOSTS
        - [dut1]_RESOLV
        - [dut1]_NETWORK_INTERFACES
        - [dut1]_SSHD_CONF
        - [dut1]_KEEPALIVED_CONF
     - [dut2]
        - [dut1]_NTP
        - [dut1]_QUAGGA_CONFIG
        ...
    - [testbed_name2]
      - [dut1]
