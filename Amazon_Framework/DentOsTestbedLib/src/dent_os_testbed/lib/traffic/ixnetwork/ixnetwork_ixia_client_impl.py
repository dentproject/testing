import os
import time

from dent_os_testbed.lib.traffic.ixnetwork.ixnetwork_ixia_client import IxnetworkIxiaClient
from ixnetwork_restpy.assistants.statistics.statviewassistant import StatViewAssistant as SVA
from ixnetwork_restpy.files import Files
from ixnetwork_restpy.testplatform.testplatform import TestPlatform


class IxnetworkIxiaClientImpl(IxnetworkIxiaClient):
    """
    - IxiaClient
        connect - client_addr, ports
        load_config - [config_file_name]
        start_traffic - [traffic_names]
        stop_traffic  - [traffic_names]
        get_stats - [traffic_names]
        clear_stats - [traffic_names]
        start_protocols - [protocols]
        stop_protocols - [protocols]
        get_protocol_stats - [protocols]
        clear_protocol_stats - [protocols]

    """

    ixnet = None
    session = None
    rr_eps = []  # route range end points
    bgp_eps = []  # bgp device end point
    ip_eps = []  # ip interface end point
    eth_eps = []  # ethernet interface end point
    raw_eps = []  # raw vort end point
    tis = []

    def format_connect(self, command, *argv, **kwarg):
        return command

    def run_connect(self, device, command, *argv, **kwarg):
        """
        - IxiaClient
          connect - client_addr, ports- ['chassis_ip:card:port',...]
          disconnect -
        """
        ############# Implement me ################
        if command == "disconnect":
            if IxnetworkIxiaClientImpl.session is not None:
                device.applog.info("Removing Session ID: %d" % IxnetworkIxiaClientImpl.session.Id)
                IxnetworkIxiaClientImpl.session.remove()
                IxnetworkIxiaClientImpl.session = None
                IxnetworkIxiaClientImpl.ixnet = None
                IxnetworkIxiaClientImpl.session = None
                IxnetworkIxiaClientImpl.rr_eps = []
                IxnetworkIxiaClientImpl.bgp_eps = []
                IxnetworkIxiaClientImpl.ip_eps = []
                IxnetworkIxiaClientImpl.eth_eps = []
                IxnetworkIxiaClientImpl.raw_eps = []
                IxnetworkIxiaClientImpl.tis = []
            return 0, ""
        params = kwarg["params"]
        if not params or not params[0] or "test" in device.host_name:
            return 0, ""
        param = params[0]
        try:
            caddr = param["client_addr"]
            if not caddr:
                return 0, "No Address to connect!"
            gw = TestPlatform(ip_address=caddr, rest_port=443)
            gw.Authenticate("admin", "admin")
            # session = gw.Sessions.find()[0]
            # device.applog.info(session)
            # if session.Id == -1:
            session = gw.Sessions.add()
            device.applog.info("Connected to Linux Gateway Session ID: %d" % session.Id)
            device.applog.info("Reserving test ports, and may take a minute...")
            IxnetworkIxiaClientImpl.session = session
            IxnetworkIxiaClientImpl.ixnet = session.Ixnetwork
            IxnetworkIxiaClientImpl.ixnet.NewConfig()
            IxnetworkIxiaClientImpl.rr_eps = []
            IxnetworkIxiaClientImpl.bgp_eps = []
            IxnetworkIxiaClientImpl.ip_eps = []
            IxnetworkIxiaClientImpl.eth_eps = []
            IxnetworkIxiaClientImpl.raw_eps = []
            IxnetworkIxiaClientImpl.tis = []

            device.applog.info("Connection to Ixia REST API Server Established")
            ixia_ports = param["tgen_ports"]
            swp_ports = param["swp_ports"]
            dev_groups = param["dev_groups"]
            pports = []
            vports = {}
            for port, sport in zip(ixia_ports, swp_ports):
                vports[port] = (IxnetworkIxiaClientImpl.ixnet.Vport.add(Name=port), sport)
                pport = port.split(":")
                pports.append({"Arg1": pport[0], "Arg2": int(pport[1]), "Arg3": int(pport[2])})
            vport_hrefs = [vport.href for vport in IxnetworkIxiaClientImpl.ixnet.Vport.find()]
            device.applog.info("Assigning ports")
            IxnetworkIxiaClientImpl.ixnet.AssignPorts(pports, [], vport_hrefs, True)
            for port, vport in vports.items():
                vport[0].L1Config.NovusTenGigLan.Media = "fiber"
                device.applog.info("Adding Ipv4 on ixia port {} swp {}".format(port, vport[1]))
                topo = IxnetworkIxiaClientImpl.ixnet.Topology.add(Vports=vport[0])
                for dev in dev_groups[port]:
                    device.applog.info("Adding device {}".format(dev))
                    dev_group = topo.DeviceGroup.add(Multiplier=dev.get("count", 2))
                    if "vlan" in dev and dev["vlan"] is not None:
                        eth = dev_group.Ethernet.add(Name=vport[1], UseVlans=True, VlanCount=1)
                        eth.Vlan.find()[0].VlanId.Single(dev["vlan"])
                    else:
                        eth = dev_group.Ethernet.add(Name=vport[1])
                    ep = eth.Ipv4.add(Name=dev["name"])
                    ep.Address.Increment(dev["ip"], "0.0.0.1")
                    ep.GatewayIp.Single(dev["gw"])
                    ep.Prefix.Single(dev["plen"])
                    if dev.get("bgp_peer", {}):
                        bp = dev["bgp_peer"]
                        bgp_ep = ep.BgpIpv4Peer.add(Name=dev["name"])
                        bgp_ep.DutIp.Single(dev["gw"])
                        bgp_ep.Type.Single("external")
                        bgp_ep.LocalAs2Bytes.Single(bp["local_as"])
                        bgp_ep.HoldTimer.Single(bp["hold_timer"])
                        bgp_ep.UpdateInterval.Single(bp["update_interval"])
                        # "route_ranges": [{"number_of_routes": 100, "first_route": f"{br_ip}.0.0.1",},],
                        ng = dev_group.NetworkGroup.add(
                            Multiplier=len(bp["route_ranges"]), Name=dev["name"]
                        )
                        ng.Enabled.Single(True)
                        for rr in bp["route_ranges"]:
                            pool = ng.Ipv4PrefixPools.add(
                                Name=dev["name"], NumberOfAddresses=rr["number_of_routes"]
                            )
                            pool.NetworkAddress.Single(rr["first_route"])
                            IxnetworkIxiaClientImpl.rr_eps.append(pool)

                        IxnetworkIxiaClientImpl.bgp_eps.append(bgp_ep)
                    else:
                        IxnetworkIxiaClientImpl.bgp_eps.append(ep)
                        IxnetworkIxiaClientImpl.rr_eps.append(ep)
                    IxnetworkIxiaClientImpl.ip_eps.append(ep)
                    IxnetworkIxiaClientImpl.eth_eps.append(eth)
                    IxnetworkIxiaClientImpl.raw_eps.append(vport[0].Protocols.find())
        except Exception as e:
            device.applog.info(e)
        return 0, "Connected!"

    def parse_connect(self, command, output, *argv, **kwarg):
        return command

    def format_config(self, command, *argv, **kwarg):
        return command

    def run_config(self, device, command, *argv, **kwarg):
        """
        - IxiaClient
           load_config - config_file_name
           save_config - config_file_name
        """
        ############# Implement me ################
        if not IxnetworkIxiaClientImpl.ixnet:
            return 0, "Ixia not connected"
        params = kwarg["params"]
        if not params or not params[0]:
            return 0, "Need to specify config file name"
        param = params[0]
        fname = param["config_file_name"]
        name = os.path.basename(fname)
        if command == "load_config":
            files = IxnetworkIxiaClientImpl.session.GetFileList()
            found = False
            for f in files["files"]:
                if f["name"] == name:
                    found = True
                    break
            if not found:
                out = IxnetworkIxiaClientImpl.session.UploadFile(fname, name)
            out = IxnetworkIxiaClientImpl.ixnet.LoadConfig(Files(name))
            # get the traffic items back
            IxnetworkIxiaClientImpl.tis = IxnetworkIxiaClientImpl.ixnet.Traffic.TrafficItem.find()
        elif command == "save_config":
            out = IxnetworkIxiaClientImpl.ixnet.SaveConfig(Files(name))
            out += IxnetworkIxiaClientImpl.session.DownloadFile(name, fname)
        return 0, out

    def parse_config(self, command, output, *argv, **kwarg):
        return command

    def format_traffic_item(self, command, *argv, **kwarg):
        return command

    def set_l4_traffic(self, config_element, ipv4_stack, pkt_data):
        if "ipproto" not in pkt_data:
            return
        if pkt_data["ipproto"] not in ["tcp", "udp", "icmpv1"]:
            return
        ipproto_template = IxnetworkIxiaClientImpl.ixnet.Traffic.ProtocolTemplate.find(
            StackTypeId="^{}$".format(pkt_data["ipproto"])
        )
        l4_stack = config_element.Stack.read(ipv4_stack.AppendProtocol(ipproto_template))
        if "dstPort" in pkt_data:
            dst_port = l4_stack.Field.find(
                FieldTypeId="{}.header.dstPort".format(pkt_data["ipproto"])
            )
            dst_port.Auto = False
            dst_port.update(ValueType="singleValue", SingleValue="{}".format(pkt_data["dstPort"]))
        if "srcPort" in pkt_data:
            src_port = l4_stack.Field.find(
                FieldTypeId="{}.header.srcPort".format(pkt_data["ipproto"])
            )
            src_port.Auto = False
            src_port.update(ValueType="singleValue", SingleValue="{}".format(pkt_data["srcPort"]))

    def set_ethernet_traffic(self, device, name, pkt_data, traffic_type):
        # create an ipv4 traffic item
        ipv4_template = IxnetworkIxiaClientImpl.ixnet.Traffic.ProtocolTemplate.find(
            StackTypeId="^ipv4$"
        )
        vlan_template = IxnetworkIxiaClientImpl.ixnet.Traffic.ProtocolTemplate.find(
            StackTypeId="^vlan$"
        )
        for ip1, ep1, rep1 in zip(
            IxnetworkIxiaClientImpl.ip_eps,
            IxnetworkIxiaClientImpl.eth_eps,
            IxnetworkIxiaClientImpl.raw_eps,
        ):
            if "ip_source" in pkt_data and ip1.Name not in pkt_data["ip_source"]:
                continue
            if "ep_source" in pkt_data and ep1.Name not in pkt_data["ep_source"]:
                continue
            device.applog.info("Creating the Ethernet traffic stream on {}".format(ep1.Name))
            ti = IxnetworkIxiaClientImpl.ixnet.Traffic.TrafficItem.add(
                Name=name, TrafficType=traffic_type
            )
            ep_count = 0
            for ip2, ep2, rep2 in zip(
                IxnetworkIxiaClientImpl.ip_eps,
                IxnetworkIxiaClientImpl.eth_eps,
                IxnetworkIxiaClientImpl.raw_eps,
            ):
                if ep1 == ep2:
                    continue
                if "ip_destination" in pkt_data and ip2.Name not in pkt_data["ip_destination"]:
                    continue
                if "ep_destination" in pkt_data and ep2.Name not in pkt_data["ep_destination"]:
                    continue
                # create an endpoint set using the ipv4 objects
                device.applog.info(
                    "Adding the endpoint ep1 {} to ep2 {}".format(ep1.Name, ep2.Name)
                )
                if traffic_type == "raw":
                    endpoint_set = ti.EndpointSet.add(Sources=rep1, Destinations=rep2)
                else:
                    endpoint_set = ti.EndpointSet.add(Sources=ep1, Destinations=ep2)
                ep_count += 1
            IxnetworkIxiaClientImpl.tis.append(ti)
            ti.Tracking.find()[0].TrackBy = ["trackingenabled0", "sourceDestValuePair0"]
            ti.Enabled = True
            for ep in range(ep_count):
                config_element = ti.ConfigElement.find(EndpointSetId=ep + 1)
                # set the rate
                config_element.FrameRate.update(
                    Type="framesPerSecond", Rate=pkt_data.get("rate", "100")
                )
                config_element.FrameSize.update(
                    Type="fixed", FixedSize=pkt_data.get("frameSize", "512")
                )
                config_element.TransmissionControl.update(Type="continuous")
                ethernet_stack = config_element.Stack.find(StackTypeId="^ethernet$")
                if "vlanID" in pkt_data:
                    vlan_stack = config_element.Stack.read(
                        ethernet_stack.AppendProtocol(vlan_template)
                    )
                    ipv4_stack = config_element.Stack.read(vlan_stack.AppendProtocol(ipv4_template))
                else:
                    ipv4_stack = config_element.Stack.read(
                        ethernet_stack.AppendProtocol(ipv4_template)
                    )
                # update the Mac address
                if "dstMac" in pkt_data:
                    dst_mac = ethernet_stack.Field.find(
                        FieldTypeId="ethernet.header.destinationAddress"
                    )
                    dst_mac.Auto = False
                    dst_mac.update(
                        ValueType="singleValue", SingleValue="{}".format(pkt_data["dstMac"])
                    )
                if "srcMac" in pkt_data:
                    src_mac = ethernet_stack.Field.find(FieldTypeId="ethernet.header.sourceAddress")
                    src_mac.Auto = False
                    src_mac.update(
                        ValueType="singleValue", SingleValue="{}".format(pkt_data["srcMac"])
                    )
                if "vlanID" in pkt_data:
                    vlan_id = vlan_stack.Field.find(FieldTypeId="vlan.header.vlanTag.vlanID")
                    vlan_id.Auto = False
                    vlan_id.update(
                        ValueType="singleValue", SingleValue="{}".format(pkt_data["vlanID"])
                    )
                # update the Ip address
                if "dstIp" in pkt_data:
                    dst_ip = ipv4_stack.Field.find(FieldTypeId="ipv4.header.dstIp")
                    dst_ip.Auto = False
                    dst_ip.update(
                        ValueType="singleValue", SingleValue="{}".format(pkt_data["dstIp"])
                    )
                if "srcIp" in pkt_data:
                    src_ip = ipv4_stack.Field.find(FieldTypeId="ipv4.header.srcIp")
                    src_ip.Auto = False
                    src_ip.update(
                        ValueType="singleValue", SingleValue="{}".format(pkt_data["srcIp"])
                    )
                self.set_l4_traffic(config_element, ipv4_stack, pkt_data)

    def set_ipv4_traffic(self, device, name, pkt_data, traffic_type):
        # create an ipv4 traffic item
        for ep1, rr_ep1 in zip(IxnetworkIxiaClientImpl.ip_eps, IxnetworkIxiaClientImpl.rr_eps):
            if "bgp_source" in pkt_data and rr_ep1.Name not in pkt_data["bgp_source"]:
                continue
            if "ip_source" in pkt_data and ep1.Name not in pkt_data["ip_source"]:
                continue
            device.applog.info("Creating the IPV4 traffic stream on {}".format(ep1.Name))
            ti = IxnetworkIxiaClientImpl.ixnet.Traffic.TrafficItem.add(
                Name=name, TrafficType="ipv4"
            )
            ep_count = 0
            for ep2, rr_ep2 in zip(IxnetworkIxiaClientImpl.ip_eps, IxnetworkIxiaClientImpl.rr_eps):
                if ep1 == ep2:
                    continue
                if "bgp_destination" in pkt_data and rr_ep2.Name not in pkt_data["bgp_destination"]:
                    continue
                if "ip_destination" in pkt_data and ep2.Name not in pkt_data["ip_destination"]:
                    continue
                # create an endpoint set using the ipv4 objects
                device.applog.info(
                    "Adding the endpoint ep1 {} to ep2 {}".format(ep1.Name, ep2.Name)
                )
                if traffic_type == "ipv4":
                    endpoint_set = ti.EndpointSet.add(Sources=ep1, Destinations=ep2)
                else:
                    endpoint_set = ti.EndpointSet.add(Sources=rr_ep1, Destinations=rr_ep2)
                ep_count += 1
            IxnetworkIxiaClientImpl.tis.append(ti)
            ti.Tracking.find()[0].TrackBy = ["trackingenabled0", "sourceDestValuePair0"]
            ti.Enabled = True
            for ep in range(ep_count):
                config_element = ti.ConfigElement.find(EndpointSetId=ep + 1)
                # set the rate
                config_element.FrameRate.update(
                    Type="framesPerSecond", Rate=pkt_data.get("rate", "100")
                )
                config_element.FrameSize.update(
                    Type="fixed", FixedSize=pkt_data.get("frameSize", "512")
                )
                config_element.TransmissionControl.update(Type="continuous")
                ipv4_stack = config_element.Stack.find(StackTypeId="^ipv4$")
                self.set_l4_traffic(config_element, ipv4_stack, pkt_data)

    def run_traffic_item(self, device, command, *argv, **kwarg):
        """
        - IxiaClient
           set_traffic - [traffic_names], [ports]
           start_traffic - [traffic_names]
           stop_traffic  - [traffic_names]
           get_stats - [traffic_names]
           clear_stats - [traffic_names]

        """
        if not IxnetworkIxiaClientImpl.ixnet:
            return 0, "Ixia not connected"
        ############# Implement me ################
        if command == "set_traffic":
            params = kwarg["params"]
            if not params or not params[0]:
                return 0, "Need to specify the packet data"
            param = params[0]
            type = param["pkt_data"].get("type", "ipv4")
            if type == "ipv4":
                self.set_ipv4_traffic(device, param["name"], param["pkt_data"], traffic_type="ipv4")
            elif type == "bgp":
                self.set_ipv4_traffic(device, param["name"], param["pkt_data"], traffic_type="bgp")
            elif type == "ethernet":
                self.set_ethernet_traffic(
                    device, param["name"], param["pkt_data"], traffic_type="ethernetVlan"
                )
            elif type == "ethernetVlan":
                self.set_ethernet_traffic(
                    device, param["name"], param["pkt_data"], traffic_type="ethernetVlan"
                )
            elif type == "raw":
                self.set_ethernet_traffic(
                    device, param["name"], param["pkt_data"], traffic_type="raw"
                )
        elif command == "start_traffic":
            device.applog.info("Starting Traffic")
            IxnetworkIxiaClientImpl.ixnet.Traffic.Start()
        elif command == "stop_traffic":
            device.applog.info("Stopping Traffic")
            IxnetworkIxiaClientImpl.ixnet.Traffic.Stop()
        elif command == "get_stats":
            device.applog.info("Getting Stats")
            stats_type = "Port Statistics"
            params = kwarg["params"]
            if params or params[0]:
                stats_type = params[0].get("stats_type", stats_type)
            stats = SVA(IxnetworkIxiaClientImpl.ixnet, stats_type)
            # device.applog.info(stats)
            return 0, stats
        elif command == "clear_stats":
            device.applog.info("Clear Stats")
            IxnetworkIxiaClientImpl.ixnet.ClearStats()
        return 0, ""

    def parse_traffic_item(self, command, output, *argv, **kwarg):
        return command

    def format_protocol(self, command, *argv, **kwarg):
        return command

    def run_protocol(self, device, command, *argv, **kwarg):
        """
        - IxiaClient
           start_protocols - [protocols]
           stop_protocols - [protocols]
           set_protocol - [protocol]
           get_protocol_stats - [protocols]
           clear_protocol_stats - [protocols]

        """
        if not IxnetworkIxiaClientImpl.ixnet:
            return 0, "Ixia not connected"
        ############# Implement me ################
        if command == "start_protocols":
            device.applog.info("Starting All Protocols")
            IxnetworkIxiaClientImpl.ixnet.StartAllProtocols(Arg1="sync")
            time.sleep(15)
            for ep in IxnetworkIxiaClientImpl.ip_eps:
                device.applog.info("Sending ARP on " + ep.Name)
                ep.Start()
                ep.SendArp()
            time.sleep(5)
            device.applog.info("Generating Traffic")
            for ti in IxnetworkIxiaClientImpl.tis:
                ti.Generate()
            device.applog.info("Applying Traffic")
            IxnetworkIxiaClientImpl.ixnet.Traffic.Apply()
        elif command == "stop_protocols":
            device.applog.info("Stopping All Protocols")
            IxnetworkIxiaClientImpl.ixnet.StopAllProtocols(Arg1="sync")
        elif command == "set_protocol":
            params = kwarg["params"]
            param = params[0]
            for ep in IxnetworkIxiaClientImpl.bgp_eps:
                if "bgp_peer" in param and param["bgp_peer"] != ep.Name:
                    continue
                enable = param["enable"]
                IxnetworkIxiaClientImpl.bgp_eps
                ep.Active.Single(enable)
            IxnetworkIxiaClientImpl.ixnet.Globals.Topology.ApplyOnTheFly()
        return 0, ""

    def parse_protocol(self, command, output, *argv, **kwarg):
        return command
