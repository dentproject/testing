from tabulate import tabulate
from statistics import mean
import time

TGEN_AS_NUM = 65200
DUT_AS_NUM = 65100
TIMEOUT = 30
BGP_TYPE = 'ebgp'
NG_LIST = []
aspaths = [65002, 65003]

def run_rib_in_convergence_test(cvg_api,
												tgen_ports,
												iteration,
												multipath,
												number_of_routes,
												route_type,
												port_media,
												port_speed,):
	"""
	Run RIB-IN Convergence test

	Args:
		cvg_api (pytest fixture): snappi API
		duthost (pytest fixture): duthost fixture
		tgen_ports (pytest fixture): Ports mapping info of T0 testbed
		iteration: number of iterations for running convergence test on a port
		multipath: ecmp value for BGP config
		number_of_routes:  Number of IPv4/IPv6 Routes
		route_type: IPv4 or IPv6 routes
		port_speed: speed of the port used for test
	"""
	port_count = multipath+1

	"""  Create bgp config on TGEN """
	tgen_bgp_config = __tgen_bgp_config(cvg_api,
															port_count,
															number_of_routes,
															route_type,
															port_speed,
															port_media,
															tgen_ports,) 
	"""
		Run the convergence test by withdrawing all routes at once and
		calculate the convergence values
	"""
	get_rib_in_convergence(cvg_api,
										tgen_bgp_config,
										iteration,
										multipath,
										number_of_routes,
										route_type,)
										
def run_bgp_remote_link_failover_test(cvg_api,
														iteration,
														multipath,
														number_of_routes,
														route_type,
														port_speed,
														port_media,
														tgen_ports,):
	"""
	Run Local link failover test

	Args:
	cvg_api (pytest fixture): snappi API
	duthost (pytest fixture): duthost fixture
	tgen_ports (pytest fixture): Ports mapping info of T0 testbed
	iteration: number of iterations for running convergence test on a port
	multipath: ecmp value for BGP config
	number_of_routes:  Number of IPv4/IPv6 Routes
	route_type: IPv4 or IPv6 routes
	port_speed: speed of the port used for test
	"""
	port_count = multipath+1

	""" Create bgp config on TGEN """
	tgen_bgp_config = __tgen_bgp_config(cvg_api,
															port_count,
															number_of_routes,
															route_type,
															port_speed,
															port_media,
															tgen_ports,)
	"""
	Run the convergence test by flapping all the rx
	links one by one and calculate the convergence values
	"""
	get_convergence_for_remote_link_failover(cvg_api,
																tgen_bgp_config,
																iteration,
																multipath,
																number_of_routes,
																route_type,)
																
def run_bgp_local_link_failover_test(cvg_api,
													iteration,
													multipath,
													number_of_routes,
													route_type,
													port_speed,
													port_media,
													tgen_ports,):
	"""
	Run Local link failover test

	Args:
	cvg_api (pytest fixture): snappi API
	duthost (pytest fixture): duthost fixture
	tgen_ports (pytest fixture): Ports mapping info of T0 testbed
	iteration: number of iterations for running convergence test on a port
	multipath: ecmp value for BGP config
	number_of_routes:  Number of IPv4/IPv6 Routes
	route_type: IPv4 or IPv6 routes
	port_speed: speed of the port used for test
	"""
	port_count = multipath+1

	""" Create bgp config on TGEN """
	tgen_bgp_config = __tgen_bgp_config(cvg_api,
													port_count,
													number_of_routes,
													route_type,
													port_speed,
													port_media,
													tgen_ports,)
	"""
	Run the convergence test by flapping all the rx
	links one by one and calculate the convergence values
	"""
	get_convergence_for_local_link_failover(cvg_api,
														tgen_bgp_config,
														iteration,
														multipath,
														number_of_routes,
														route_type,)
														
def __tgen_bgp_config(cvg_api,
									port_count,
									number_of_routes,
									route_type,
									port_speed,
									port_media,
									tgen_ports,):
	"""
	Creating  BGP config on TGEN

	Args:
		cvg_api (pytest fixture): snappi API
		port_count: multipath + 1
		number_of_routes:  Number of IPv4/IPv6 Routes
		route_type: IPv4 or IPv6 routes
		port_speed: speed of the port used for test
	"""
	global NG_LIST
	conv_config = cvg_api.convergence_config()
	config = conv_config.config
	for i in range(1, port_count+1):
		config.ports.port(name='Test_Port_%d' % i, location=tgen_ports[i-1]['location'])
		config.devices.device(name='Topology %d' % i)
	config.options.port_options.location_preemption = True
	layer1 = config.layer1.layer1()[-1]
	layer1.name = 'port settings'
	layer1.port_names = [port.name for port in config.ports]
	layer1.ieee_media_defaults = True
	layer1.auto_negotiation.rs_fec = True
	layer1.auto_negotiation.link_training = False
	layer1.speed = port_speed
	layer1.auto_negotiate = False
	layer1.media = 'fiber'

	def create_v4_topo():
		eth = config.devices[0].ethernets.add()
		eth.port_name = config.ports[0].name
		eth.name = 'Ethernet 1'
		eth.mac = "00:00:00:00:00:01"
		ipv4 = eth.ipv4_addresses.add()
		ipv4.name = 'IPv4 1'
		ipv4.address = tgen_ports[0]['ip']
		ipv4.gateway = tgen_ports[0]['peer_ip']
		ipv4.prefix = int(tgen_ports[0]['prefix'])
		rx_flow_name = []
		for i in range(2, port_count+1):
			NG_LIST.append('Network_Group%s'%i)
			if len(str(hex(i).split('0x')[1])) == 1:
				m = '0'+hex(i).split('0x')[1]
			else:
				m = hex(i).split('0x')[1]

			ethernet_stack = config.devices[i-1].ethernets.add()
			ethernet_stack.port_name = config.ports[i-1].name
			ethernet_stack.name = 'Ethernet %d' % i
			ethernet_stack.mac = "00:00:00:00:00:%s" % m
			ipv4_stack = ethernet_stack.ipv4_addresses.add()
			ipv4_stack.name = 'IPv4 %d' % i
			ipv4_stack.address = tgen_ports[i-1]['ip']
			ipv4_stack.gateway = tgen_ports[i-1]['peer_ip']
			ipv4_stack.prefix = int(tgen_ports[i-1]['prefix'])
			bgpv4 = config.devices[i-1].bgp
			bgpv4.router_id = tgen_ports[i-1]['peer_ip']
			bgpv4_int = bgpv4.ipv4_interfaces.add()
			bgpv4_int.ipv4_name = ipv4_stack.name
			bgpv4_peer = bgpv4_int.peers.add()
			bgpv4_peer.name = 'BGP %d' % i
			bgpv4_peer.as_type = BGP_TYPE
			bgpv4_peer.peer_address = tgen_ports[i-1]['peer_ip']
			bgpv4_peer.as_number = int(TGEN_AS_NUM)
			route_range = bgpv4_peer.v4_routes.add(name=NG_LIST[-1]) #snappi object named Network Group 2 not found in internal db
			route_range.addresses.add(address='200.1.0.1', prefix=32, count=number_of_routes)
			as_path = route_range.as_path
			as_path_segment = as_path.segments.add()
			as_path_segment.type = as_path_segment.AS_SEQ
			as_path_segment.as_numbers = aspaths
			rx_flow_name.append(route_range.name)
		return rx_flow_name

	def create_v6_topo():
		eth = config.devices[0].ethernets.add()
		eth.port_name = config.ports[0].name
		eth.name = 'Ethernet 1'
		eth.mac = "00:00:00:00:00:01"
		ipv6 = eth.ipv6_addresses.add()
		ipv6.name = 'IPv6 1'
		ipv6.address = tgen_ports[0]['ipv6']
		ipv6.gateway = tgen_ports[0]['peer_ipv6']
		ipv6.prefix = int(tgen_ports[0]['ipv6_prefix'])
		rx_flow_name = []
		for i in range(2, port_count+1):
			NG_LIST.append('Network_Group%s'%i)
			if len(str(hex(i).split('0x')[1])) == 1:
				m = '0'+hex(i).split('0x')[1]
			else:
				m = hex(i).split('0x')[1]
			ethernet_stack = config.devices[i-1].ethernets.add()
			ethernet_stack.port_name = config.ports[i-1].name
			ethernet_stack.name = 'Ethernet %d' % i
			ethernet_stack.mac = "00:00:00:00:00:%s" % m
			ipv6_stack = ethernet_stack.ipv6_addresses.add()
			ipv6_stack.name = 'IPv6 %d' % i
			ipv6_stack.address = tgen_ports[i-1]['ipv6']
			ipv6_stack.gateway = tgen_ports[i-1]['peer_ipv6']
			ipv6_stack.prefix = int(tgen_ports[i-1]['ipv6_prefix'])
			
			bgpv6 = config.devices[i-1].bgp
			bgpv6.router_id = tgen_ports[i-1]['peer_ip']
			bgpv6_int = bgpv6.ipv6_interfaces.add()
			bgpv6_int.ipv6_name = ipv6_stack.name
			bgpv6_peer = bgpv6_int.peers.add()
			bgpv6_peer.name  = 'BGP+_%d' % i
			bgpv6_peer.as_type = BGP_TYPE
			bgpv6_peer.peer_address = tgen_ports[i-1]['peer_ipv6']
			bgpv6_peer.as_number = int(TGEN_AS_NUM)
			route_range = bgpv6_peer.v6_routes.add(name=NG_LIST[-1])
			route_range.addresses.add(address='3000::1', prefix=64, count=number_of_routes)
			as_path = route_range.as_path
			as_path_segment = as_path.segments.add()
			as_path_segment.type = as_path_segment.AS_SEQ
			as_path_segment.as_numbers = aspaths
			rx_flow_name.append(route_range.name)
		return rx_flow_name

	if route_type == 'IPv4':
		rx_flows = create_v4_topo()
		flow = config.flows.flow(name='IPv4 Traffic')[-1]
	elif route_type == 'IPv6':
		rx_flows = create_v6_topo()
		flow = config.flows.flow(name='IPv6 Traffic')[-1]
	else:
		raise Exception('Invalid route type given')
	flow.tx_rx.device.tx_names = [config.devices[0].name]
	flow.tx_rx.device.rx_names = rx_flows
	flow.size.fixed = 1024
	flow.rate.percentage = 100
	flow.metrics.enable = True
	return conv_config

def get_flow_stats(cvg_api):
    """
    Args:
        cvg_api (pytest fixture): Snappi API
    """
    request = cvg_api.convergence_request()
    request.metrics.flow_names = []
    return cvg_api.get_results(request).flow_metric

def get_convergence_for_local_link_failover(cvg_api,
                                            bgp_config,
                                            iteration,
                                            multipath,
                                            number_of_routes,
                                            route_type,):
	"""
	Args:
		cvg_api (pytest fixture): snappi API
		bgp_config: __tgen_bgp_config
		config: TGEN config
		iteration: number of iterations for running convergence test on a port
		number_of_routes:  Number of IPv4/IPv6 Routes
		route_type: IPv4 or IPv6 routes
	"""
	rx_port_names = []
	for i in range(1, len(bgp_config.config.ports)):
		rx_port_names.append(bgp_config.config.ports[i].name)
	bgp_config.rx_rate_threshold = 90/(multipath-1)
	cvg_api.set_config(bgp_config)

	""" Starting Protocols """
	print("Starting all protocols ...")
	cs = cvg_api.convergence_state()
	cs.protocol.state = cs.protocol.START
	cvg_api.set_state(cs)
	time.sleep(40)

	def get_avg_dpdp_convergence_time(port_name):
		"""
		Args:
			   port_name: Name of the port
		"""
		table, avg, tx_frate, rx_frate, avg_delta = [], [], [], [], []
		for i in range(0, iteration):
			print('|---- {} Link Flap Iteration : {} ----|'.format(port_name, i+1))

			""" Starting Traffic """
			print('Starting Traffic')
			cs = cvg_api.convergence_state()
			cs.transmit.state = cs.transmit.START
			cvg_api.set_state(cs)
			time.sleep(40)
			flow_stats = get_flow_stats(cvg_api)
			tx_frame_rate = flow_stats[0].frames_tx_rate
			assert tx_frame_rate != 0, "Traffic has not started"
			""" Flapping Link """
			print('Simulating Link Failure on {} link'.format(port_name))
			cs = cvg_api.convergence_state()
			cs.link.port_names = [port_name]
			cs.link.state = cs.link.DOWN
			cvg_api.set_state(cs)
			time.sleep(40)
			flows = get_flow_stats(cvg_api)
			for flow in flows:
				tx_frate.append(flow.frames_tx_rate)
				rx_frate.append(flow.frames_rx_rate)
			assert sum(tx_frate) - sum(rx_frate) < 500, "Traffic has not converged after link flap: TxFrameRate:{},RxFrameRate:{}".format(sum(tx_frate), sum(rx_frate))
			print("Traffic has converged after link flap")
			""" Get control plane to data plane convergence value """
			request = cvg_api.convergence_request()
			request.convergence.flow_names = []
			convergence_metrics = cvg_api.get_results(request).flow_convergence
			for metrics in convergence_metrics:
			   print('CP/DP Convergence Time (ms): {}'.format(metrics.control_plane_data_plane_convergence_us/1000))
			avg.append(int(metrics.control_plane_data_plane_convergence_us/1000))
			avg_delta.append(int(flows[0].frames_tx)-int(flows[0].frames_rx))
			""" Performing link up at the end of iteration """
			print('Simulating Link Up on {} at the end of iteration {}'.format(port_name, i+1))
			cs = cvg_api.convergence_state()
			cs.link.port_names = [port_name]
			cs.link.state = cs.link.UP
			cvg_api.set_state(cs)
			cs = cvg_api.convergence_state()
			cs.transmit.state = cs.transmit.STOP
			cvg_api.set_state(cs)
			time.sleep(40)
		table.append('%s Link Failure' % port_name)
		table.append(route_type)
		table.append(number_of_routes)
		table.append(iteration)
		table.append(mean(avg_delta))
		table.append(mean(avg))
		return table
	table = []
	""" Iterating link flap test on all the rx ports """
	for i, port_name in enumerate(rx_port_names):
		  table.append(get_avg_dpdp_convergence_time(port_name))
	columns = ['Event Name', 'Route Type', 'No. of Routes', 'Iterations', 'Delta Frames', 'Avg Calculated Data Convergence Time (ms)']
	print("\n%s" % tabulate(table, headers=columns, tablefmt="psql"))

def get_convergence_for_remote_link_failover(cvg_api,
                                             bgp_config,
                                             iteration,
                                             multipath,
                                             number_of_routes,
                                             route_type,):
    """
    Args:
        cvg_api (pytest fixture): snappi API
        bgp_config: __tgen_bgp_config
        config: TGEN config
        iteration: number of iterations for running convergence test on a port
        number_of_routes:  Number of IPv4/IPv6 Routes
        route_type: IPv4 or IPv6 routes
    """
    route_names = NG_LIST
    bgp_config.rx_rate_threshold = 90/(multipath-1)
    cvg_api.set_config(bgp_config)
	
    def get_avg_cpdp_convergence_time(route_name):
        """
        Args:
            route_name: name of the route

        """
        table, avg, tx_frate, rx_frate, avg_delta = [], [], [], [], []
        """ Starting Protocols """
        print("Starting all protocols ...")
        cs = cvg_api.convergence_state()
        cs.protocol.state = cs.protocol.START
        cvg_api.set_state(cs)
        time.sleep(40)
        for i in range(0, iteration):
            print('|---- {} Route Withdraw Iteration : {} ----|'.format(route_name, i+1))
            """ Starting Traffic """
            print('Starting Traffic')
            cs = cvg_api.convergence_state()
            cs.transmit.state = cs.transmit.START
            cvg_api.set_state(cs)
            time.sleep(40)
            flow_stats = get_flow_stats(cvg_api)
            tx_frame_rate = flow_stats[0].frames_tx_rate
            assert tx_frame_rate != 0, "Traffic has not started"

            """ Withdrawing routes from a BGP peer """
            print('Withdrawing Routes from {}'.format(route_name))
            cs = cvg_api.convergence_state()
            cs.route.names = [route_name]
            cs.route.state = cs.route.WITHDRAW
            cvg_api.set_state(cs)
            time.sleep(40)
            flows = get_flow_stats(cvg_api)
            for flow in flows:
                tx_frate.append(flow.frames_tx_rate)
                rx_frate.append(flow.frames_rx_rate)
            assert sum(tx_frate) - sum(rx_frate) < 500, "Traffic has not converged after lroute withdraw TxFrameRate:{},RxFrameRate:{}".format(sum(tx_frate), sum(rx_frate))
            print("Traffic has converged after route withdraw")

            """ Get control plane to data plane convergence value """
            request = cvg_api.convergence_request()
            request.convergence.flow_names = []
            convergence_metrics = cvg_api.get_results(request).flow_convergence
            for metrics in convergence_metrics:
                print('CP/DP Convergence Time (ms): {}'.format(metrics.control_plane_data_plane_convergence_us/1000))
            avg.append(int(metrics.control_plane_data_plane_convergence_us/1000))
            avg_delta.append(int(flows[0].frames_tx)-int(flows[0].frames_rx))
            """ Advertise the routes back at the end of iteration """
            cs = cvg_api.convergence_state()
            cs.route.names = [route_name]
            cs.route.state = cs.route.ADVERTISE
            cvg_api.set_state(cs)
            print('Readvertise {} routes back at the end of iteration {}'.format(route_name, i+1))
            cs = cvg_api.convergence_state()
            cs.transmit.state = cs.transmit.STOP
            cvg_api.set_state(cs)
            time.sleep(40)

        table.append('%s route withdraw' % route_name)
        table.append(route_type)
        table.append(number_of_routes)
        table.append(iteration)
        table.append(mean(avg_delta))
        table.append(mean(avg))
        return table
    table = []
    """ Iterating route withdrawal on all BGP peers """
    for route in route_names:
        table.append(get_avg_cpdp_convergence_time(route))

    columns = ['Event Name', 'Route Type', 'No. of Routes', 'Iterations', 'Frames Delta', 'Avg Control to Data Plane Convergence Time (ms)']
    print("\n%s" % tabulate(table, headers=columns, tablefmt="psql"))
	
def get_rib_in_convergence(cvg_api,
										bgp_config,
										iteration,
										multipath,
										number_of_routes,
										route_type,):
    """
    Args:
        cvg_api (pytest fixture): snappi API
        bgp_config: __tgen_bgp_config
        config: TGEN config
        iteration: number of iterations for running convergence test on a port
        number_of_routes:  Number of IPv4/IPv6 Routes
        route_type: IPv4 or IPv6 routes
    """
    route_names = NG_LIST
    bgp_config.rx_rate_threshold = 90/(multipath)
    cvg_api.set_config(bgp_config)
    table, avg, tx_frate, rx_frate, avg_delta = [], [], [], [], []
    for i in range(0, iteration):
        print('|---- RIB-IN Convergence test, Iteration : {} ----|'.format(i+1))
        """ withdraw all routes before starting traffic """
        print('Withdraw All Routes before starting traffic')
        cs = cvg_api.convergence_state()
        cs.route.names = route_names
        cs.route.state = cs.route.WITHDRAW
        cvg_api.set_state(cs)
        time.sleep(25)
        """ Starting Protocols """
        print("Starting all protocols ...")
        cs = cvg_api.convergence_state()
        cs.protocol.state = cs.protocol.START
        cvg_api.set_state(cs)
        time.sleep(40)
        """ Start Traffic """
        print('Starting Traffic')
        cs = cvg_api.convergence_state()
        cs.transmit.state = cs.transmit.START
        cvg_api.set_state(cs)
        time.sleep(30)
        flow_stats = get_flow_stats(cvg_api)
        tx_frame_rate = flow_stats[0].frames_tx_rate
        rx_frame_rate = flow_stats[0].frames_rx_rate
        assert tx_frame_rate != 0, "Traffic has not started"
        assert rx_frame_rate == 0

        """ Advertise All Routes """
        print('Advertising all Routes from {}'.format(route_names))
        cs = cvg_api.convergence_state()
        cs.route.names = route_names
        cs.route.state = cs.route.ADVERTISE
        cvg_api.set_state(cs)
        time.sleep(30)
        flows = get_flow_stats(cvg_api)
        for flow in flows:
            tx_frate.append(flow.frames_tx_rate)
            rx_frate.append(flow.frames_rx_rate)
        assert sum(tx_frate) - sum(rx_frate) < 500, "Traffic has not convergedv, TxFrameRate:{},RxFrameRate:{}".format(sum(tx_frate), sum(rx_frate))
        print("Traffic has converged after route advertisement")

        """ Get RIB-IN convergence """
        request = cvg_api.convergence_request()
        request.convergence.flow_names = []
        convergence_metrics = cvg_api.get_results(request).flow_convergence
        for metrics in convergence_metrics:
            print('RIB-IN Convergence time (ms): {}'.format(metrics.control_plane_data_plane_convergence_us/1000))
        avg.append(int(metrics.control_plane_data_plane_convergence_us/1000))
        avg_delta.append(int(flows[0].frames_tx)-int(flows[0].frames_rx))
        """ Stop traffic at the end of iteration """
        print('Stopping Traffic at the end of iteration{}'.format(i+1))
        cs = cvg_api.convergence_state()
        cs.transmit.state = cs.transmit.STOP
        cvg_api.set_state(cs)
        time.sleep(30)
        """ Stopping Protocols """
        print("Stopping all protocols ...")
        cs = cvg_api.convergence_state()
        cs.protocol.state = cs.protocol.STOP
        cvg_api.set_state(cs)
        time.sleep(30)
    table.append('Advertise All BGP Routes')
    table.append(route_type)
    table.append(number_of_routes)
    table.append(iteration)
    table.append(mean(avg_delta))
    table.append(mean(avg))
    columns = ['Event Name', 'Route Type', 'No. of Routes','Iterations', 'Frames Delta', 'Avg RIB-IN Convergence Time(ms)']
    print("\n%s" % tabulate([table], headers=columns, tablefmt="psql"))