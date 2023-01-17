# Configuration for running the tests

## Test Bed configuration file format

```json
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
                ["ma1", "oob_sw2:swp40"],     # ["local port", "remote port:remote port"]
                ...
            ]

       } ...
     ]
    "operator" : "dent",                       # Operator name
    "topology" : "gordion-knot",               # topology name
    "force_discovery" : false                  # if we want to retrigger discovery
}
```

## Configurations

Below is the directory structure expected for testbed configuration

* configurations/
  * testbed_config
    * [testbed_name1]
      * [dut1]
        * NTP
        * QUAGGA_CONFIG
        * DHCP
        * QUAGGA_DAEMONS
        * HOSTNAME
        * QUAGGA_VTYSH
        * HOSTS
        * RESOLV
        * NETWORK_INTERFACES
        * SSHD_CONF
        * KEEPALIVED_CONF
      * [dut2]
        * NTP
        * QUAGGA_CONFIG
        * ...
    * [testbed_name2]
      * [dut1]
    * ...
