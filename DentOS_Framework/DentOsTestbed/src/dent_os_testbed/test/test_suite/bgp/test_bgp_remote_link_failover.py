import snappi_convergence
from dent_os_testbed.test.test_suite.bgp.files.helper import run_bgp_remote_link_failover_test
import pytest
from netmiko import ConnectHandler

tgen_ports = [
        {
        'ip': '21.1.1.2',
        'ipv6': '3001::2',
        'ipv6_prefix': u'64',
        'location': '10.36.78.42;3;9',
        'peer_ip': u'21.1.1.1',
        'peer_ipv6': u'3001::1',
        'prefix': u'24',
        },
        {
        'ip': '22.1.1.2',
        'ipv6': '3002::2',
        'ipv6_prefix': u'64',
        'location': '10.36.78.42;3;10',
        'peer_ip': u'22.1.1.1',
        'peer_ipv6': u'3002::1',
        'prefix': u'24',
        },
        {
        'ip': '23.1.1.2',
        'ipv6': '3003::2',
        'ipv6_prefix': u'64',
        'location': '10.36.78.42;3;11',
        'peer_ip': u'23.1.1.1',
        'peer_ipv6': u'3003::1',
        'prefix': u'24',
        },
        {
        'ip': '24.1.1.2',
        'ipv6': '3004::2',
        'ipv6_prefix': u'64',
        'location': '10.36.78.42;3;12',
        'peer_ip': u'24.1.1.1',
        'peer_ipv6': u'3004::1',
        'prefix': u'24',
        }
    ]

dent1 = { 
    "device_type": "linux",
    "ip": "10.36.78.149",
    "username": "root",
    "password": "onl" ,
}

# Show command that we execute.
cfg_file = "config_bgp_1.txt"
with ConnectHandler(**dent1) as net_connect:
    output = net_connect.send_config_from_file(cfg_file)

print(output)
	
@pytest.mark.parametrize('multipath', [3])
@pytest.mark.parametrize('convergence_test_iterations', [1])
@pytest.mark.parametrize('number_of_routes', [1000])
@pytest.mark.parametrize('route_type', ['IPv4'])
@pytest.mark.parametrize('port_speed',['speed_10_gbps'])
@pytest.mark.parametrize('port_media',['fiber'])
@pytest.mark.parametrize('tgen_ports',[tgen_ports])


@pytest.mark.suite_bgp_routes
def test_bgp_convergence_for_remote_link_failover(multipath,
																		 convergence_test_iterations,
																		 number_of_routes,
																		 route_type,
																		 port_speed,
																		 port_media,
																		 tgen_ports,):
    """
    Topo:
    TGEN1 --- DUT --- TGEN(2..N)

    Steps:
    1) Create BGP config on DUT and TGEN respectively
    2) Create a flow from TGEN1 to (N-1) TGEN ports
    3) Send Traffic from TGEN1 to (N-1) TGEN ports having the same route range
    4) Simulate link failure by bringing down one of the (N-1) TGEN Ports
    5) Calculate the packet loss duration for convergence time
    6) Clean up the BGP config on the dut

    Verification:
    1) Send traffic without flapping any link
       Result: Should not observe traffic loss
    2) Flap one of the N TGEN link
       Result: The traffic must be routed via rest of the ECMP paths

Args:
    cvg_api (pytest fixture): Snappi Convergence API
    duthost (pytest fixture): duthost fixture
    tgen_ports (pytest fixture): Ports mapping info of testbed
    conn_graph_facts (pytest fixture): connection graph
    fanout_graph_facts (pytest fixture): fanout graph
    multipath: ECMP value
    convergence_test_iterations: number of iterations the link failure test has to be run for a port
    number_of_routes:  Number of IPv4/IPv6 Routes
    route_type: IPv4 or IPv6 routes
    port_speed: speed of the port used for test
    """
    #convergence_test_iterations, multipath, number_of_routes and route_type parameters can be modified as per user preference
    cvg_api = snappi_convergence.api(location='10.36.79.222' + ':' + str(443),ext='ixnetwork')
    run_bgp_remote_link_failover_test(cvg_api,
														convergence_test_iterations,
														multipath,
														number_of_routes,
														route_type,
														port_speed,
														port_media,
														tgen_ports,)