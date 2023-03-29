import os
import time
import re

from dent_os_testbed.lib.traffic.ixnetwork.ixnetwork_ixia_client import IxnetworkIxiaClient
from ixnetwork_restpy.assistants.statistics.statviewassistant import StatViewAssistant as SVA
from ixnetwork_restpy.files import Files
from ixnetwork_restpy.testplatform.testplatform import TestPlatform
from ixnetwork_restpy import SessionAssistant, Files


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
        send_ping - [port, dst_ip, src_ip]
        send_arp - [port, src_ip]

    """

    ixnet = None
    session = None
    rr_eps = []  # route range end points
    bgp_eps = []  # bgp device end point
    ip_eps = []  # ip interface end point
    eth_eps = []  # ethernet interface end point
    raw_eps = []  # raw vort end point
    tis = []
    bad_crc = {True: "", False: ""}

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
            cport = param.get("client_port", 443)
            if not caddr:
                return 0, "No Address to connect!"

            gw = SessionAssistant(
                IpAddress=caddr,
                RestPort=cport,
                UserName=device.username,
                Password=device.password,
                SessionName="DENT",
                ClearConfig=True
            )  # ,LogLevel='info'
            session = gw.Session

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
            crc = IxnetworkIxiaClientImpl.ixnet.Traffic.TrafficItem.ConfigElement._SDM_ENUM_MAP["crc"]
            IxnetworkIxiaClientImpl.bad_crc = {True: crc[0], False: crc[1]}

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
                if device.media_mode == "mixed":
                    # Get required media mode. Default - copper
                    required_media = next((link[2] for link in device.links if link[0] == port), 'copper')
                    device.applog.info(f"Changing port: {port} media mode {required_media}")
                    vport[0].L1Config.NovusTenGigLan.Media = required_media
                elif device.media_mode == "fiber":
                    device.applog.info("Changing all vports media mode to fiber")
                    vport[0].L1Config.NovusTenGigLan.Media = "fiber"
                else:
                    device.applog.info("Changing all vports media mode to copper")
                    vport[0].L1Config.NovusTenGigLan.Media = "copper"

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

    @staticmethod
    def __configure_egress_tracking(ti, pkt_data):
        if "egress_track_by" not in pkt_data:
            return
        ti.EgressEnabled = True
        track_by = pkt_data["egress_track_by"]
        if type(track_by) is list:
            track_by = "".join(track_by)
        if "vlan" in track_by:
            tracker = ti.EgressTracking.add()
            if "vlan_4k" in track_by:
                tracker.Offset = "Outer VLAN ID (12 bits)"  # vid 0..4095
            else:
                tracker.Offset = "Outer VLAN ID (4 bits)"  # vid 0..15
        if "pcp" in track_by:
            tracker = ti.EgressTracking.add()
            tracker.Offset = "Outer VLAN Priority (3 bits)"  # pcp 0..7
        if "dscp" in track_by:
            tracker = ti.EgressTracking.add()
            tracker.Offset = "IPv4 DSCP (6 bits)"  # dscp 0..63

    @staticmethod
    def __parse_multivalue(value):
        if "type" not in value:
            raise KeyError(f"Value type is mandatory {value}")

        if value["type"] == "single":
            return {
                "ValueType": "singleValue",
                "SingleValue": str(value["value"]),
            }
        elif value["type"] in ("increment", "decrement"):
            return {
                "ValueType": value["type"],
                "StartValue": str(value["start"]),
                "StepValue": str(value["step"]),
                # choosing a large number will increase wait time from Ixia
                "CountValue": str(value.get("count", 255)),
            }
        elif value["type"] == "list":
            if not value.get("list", []):
                raise ValueError("Value list cannot be empty")
            return {
                "ValueType": "valueList",
                "ValueList": value["list"],
            }
        elif value["type"] == "random":
            return {
                "ValueType": "nonRepeatableRandom",
                "RandomMask": value.get("mask"),  # ignored when applied to MAC
            }

        valid_types = ("single", "increment", "decrement", "list", "random")
        raise ValueError(f"Valid multivalue types are: {valid_types}")

    def __update_field(self, field, value):
        if field.FieldTypeId == "ipv4.header.priority.raw":  # exception for dscp
            field.ActiveFieldChoice = True
        if type(value) == str or type(value) == int or type(value) == float:
            param = self.__parse_multivalue({"type": "single", "value": value})
        elif type(value) == dict:
            param = self.__parse_multivalue(value)
        else:
            raise ValueError(f"Unable to set {value} for field {field.Name}")
        field.Auto = False
        field.update(**param)

    def __update_frame_rate(self, config_element, pkt_data):
        """
        Update frame rate type and frame rate from pkt_data

        Args:
            config_element (ConfigElement): grouping of endpoints under the Traffic Item per unique packet structure
            pkt_data (dict): Packet stream config
        """
        frame_rate_types = {
            "line_rate": "percentLineRate",
            "bps_rate": "bitsPerSecond",
            "ipg_rate": "interPacketGap",
            "pps_rate": "framesPerSecond"}
        config_element.FrameRate.update(
            Type=frame_rate_types[pkt_data.get("frame_rate_type", "pps_rate")],
            Rate=pkt_data.get("rate", "100"),
        )

    def set_l4_traffic(self, config_element, ipv4_stack, pkt_data):
        if "ipproto" not in pkt_data:
            return
        if pkt_data["ipproto"] not in ["tcp", "udp", "icmpv1", "icmpv2"]:
            return
        ipproto_template = IxnetworkIxiaClientImpl.ixnet.Traffic.ProtocolTemplate.find(
            StackTypeId="^{}$".format(pkt_data["ipproto"])
        )
        l4_stack = config_element.Stack.read(ipv4_stack.AppendProtocol(ipproto_template))
        if "dstPort" in pkt_data:
            if ":" in pkt_data["dstPort"]:
                start, step, count = pkt_data["dstPort"].split(":")
                value = {"type": "increment", "start": start, "step": step, "count": count}
            else:
                value = pkt_data["dstPort"]
            self.__update_field(l4_stack.Field.find(FieldTypeId=f"{pkt_data['ipproto']}.header.dstPort"),
                                value)
        if "srcPort" in pkt_data:
            self.__update_field(l4_stack.Field.find(FieldTypeId=f"{pkt_data['ipproto']}.header.srcPort"),
                                pkt_data["srcPort"])

        if "icmpType" in pkt_data:
            self.__update_field(l4_stack.Field.find(FieldTypeId=f"{pkt_data['ipproto']}.message.messageType"),
                                pkt_data["icmpType"])
        if "icmpCode" in pkt_data:
            self.__update_field(l4_stack.Field.find(FieldTypeId=f"{pkt_data['ipproto']}.message.codeValue"),
                                pkt_data["icmpCode"])

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
            track_by = {"trackingenabled0", "sourceDestValuePair0"}
            ti.Enabled = True
            self.__configure_egress_tracking(ti, pkt_data)

            for ep in range(ep_count):
                config_element = ti.ConfigElement.find(EndpointSetId=ep + 1)
                self.__update_frame_rate(config_element, pkt_data)
                config_element.FrameSize.update(
                    Type="fixed", FixedSize=pkt_data.get("frameSize", "512")
                )
                config_element.Crc = IxnetworkIxiaClientImpl.bad_crc[pkt_data.get("bad_crc", False)]
                config_element.TransmissionControl.update(Type="continuous")
                eth_stack = config_element.Stack.find(StackTypeId="^ethernet$")
                if "vlanID" in pkt_data:
                    vlan_stack = config_element.Stack.read(
                        eth_stack.AppendProtocol(vlan_template)
                    )
                    ipv4_stack = config_element.Stack.read(vlan_stack.AppendProtocol(ipv4_template))
                else:
                    ipv4_stack = config_element.Stack.read(
                        eth_stack.AppendProtocol(ipv4_template)
                    )
                if "dstMac" in pkt_data:
                    self.__update_field(eth_stack.Field.find(FieldTypeId="ethernet.header.destinationAddress"),
                                        pkt_data["dstMac"])
                if "srcMac" in pkt_data:
                    self.__update_field(eth_stack.Field.find(FieldTypeId="ethernet.header.sourceAddress"),
                                        pkt_data["srcMac"])
                if "vlanID" in pkt_data:
                    self.__update_field(vlan_stack.Field.find(FieldTypeId="vlan.header.vlanTag.vlanID"),
                                        pkt_data["vlanID"])
                    if "vlanPriority" in pkt_data:
                        self.__update_field(vlan_stack.Field.find(FieldTypeId="vlan.header.vlanTag.vlanUserPriority"),
                                            pkt_data["vlanPriority"])
                    track_by.update(["vlanVlanId0", "vlanVlanUserPriority0"])
                if "dstIp" in pkt_data:
                    self.__update_field(ipv4_stack.Field.find(FieldTypeId="ipv4.header.dstIp"),
                                        pkt_data["dstIp"])
                if "srcIp" in pkt_data:
                    self.__update_field(ipv4_stack.Field.find(FieldTypeId="ipv4.header.srcIp"),
                                        pkt_data["srcIp"])
                if "dscp_ecn" in pkt_data:  # dscp and ecn
                    self.__update_field(ipv4_stack.Field.find(FieldTypeId="ipv4.header.priority.raw"),
                                        pkt_data["dscp_ecn"])
                    track_by.add("ipv4Raw0")
                if "ttl" in pkt_data:
                    self.__update_field(ipv4_stack.Field.find(FieldTypeId="ipv4.header.ttl"),
                                        pkt_data["ttl"])
                self.set_l4_traffic(config_element, ipv4_stack, pkt_data)
            ti.Tracking.find()[0].TrackBy = list(track_by)

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
            track_by = {"trackingenabled0", "sourceDestValuePair0"}
            ti.Enabled = True
            ti.BiDirectional = pkt_data.get("bi_directional", False)
            self.__configure_egress_tracking(ti, pkt_data)

            for ep in range(ep_count):
                config_element = ti.ConfigElement.find(EndpointSetId=ep + 1)
                self.__update_frame_rate(config_element, pkt_data)
                config_element.FrameSize.update(
                    Type="fixed", FixedSize=pkt_data.get("frameSize", "512")
                )
                config_element.Crc = IxnetworkIxiaClientImpl.bad_crc[pkt_data.get("bad_crc", False)]
                config_element.TransmissionControl.update(Type="continuous")
                ipv4_stack = config_element.Stack.find(StackTypeId="^ipv4$")
                if "dscp_ecn" in pkt_data:  # dscp and ecn
                    self.__update_field(ipv4_stack.Field.find(FieldTypeId="ipv4.header.priority.raw"),
                                        pkt_data["dscp_ecn"])
                    track_by.add("ipv4Raw0")
                if "ttl" in pkt_data:
                    self.__update_field(ipv4_stack.Field.find(FieldTypeId="ipv4.header.ttl"),
                                        pkt_data["ttl"])
                self.set_l4_traffic(config_element, ipv4_stack, pkt_data)
            ti.Tracking.find()[0].TrackBy = list(track_by)

    def run_traffic_item(self, device, command, *argv, **kwarg):
        """
        - IxiaClient
           set_traffic - [traffic_names], [ports]
           start_traffic - [traffic_names]
           stop_traffic  - [traffic_names]
           get_stats - [traffic_names]
           get_drilldown_stats - [traffic_names]
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
        elif command == "get_drilldown_stats":
            UDS = "User Defined Statistics"
            param = kwarg["params"][0]
            row = param["row"]
            view = IxnetworkIxiaClientImpl.ixnet.Statistics.View.find(Caption=row._view_name)
            view.DoDrillDownByOption(row._index + 1 if row._index != -1 else 1, param["group_by"])
            uds_view = IxnetworkIxiaClientImpl.ixnet.Statistics.View.find(Caption=UDS)
            if param.get("num_of_rows"):
                uds_view.Page.EgressPageSize = int(param["num_of_rows"])
            uds_view.Enabled = True  # have to enable uds view every time it is changed
            return self.run_traffic_item(device, "get_stats", params=[{"stats_type": UDS}])
        elif command == "clear_stats":
            device.applog.info("Clear Stats")
            IxnetworkIxiaClientImpl.ixnet.ClearStats()
        elif command == "clear_traffic":
            for traffic_item in IxnetworkIxiaClientImpl.tis:
                device.applog.info(f"TI to be removed: {traffic_item.Name}")
                traffic_item.remove()
            IxnetworkIxiaClientImpl.tis.clear()
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

    def format_send_ping(self, command, *argv, **kwarg):
        return command

    def format_send_arp(self, command, *argv, **kwarg):
        return command

    @classmethod
    def __get_ip_iface(cls, port, port_ip=None):
        vport = cls.ixnet.Vport.find(Name=port)
        for ip_ep in cls.ip_eps:
            # ip -> eth -> dev group -> topo
            topo = ip_ep.parent.parent.parent
            if vport.href not in topo.Ports:
                continue
            if port_ip and port_ip not in str(ip_ep.Address):
                continue
            return ip_ep
        return None

    def run_send_ping(self, device, command, *argv, **kwarg):
        """
        - IxiaClient
           send_ping - [port, dst_ip, src_ip]
        """
        params = kwarg["params"]
        res = []
        err = 0
        for param in params:
            port = param["port"]
            dst = param["dst_ip"]
            src = param.get("src_ip", None)
            out = {
                "port": port,
                "src_ip": src,
                "dst_ip": dst,
            }

            ip_ep = self.__get_ip_iface(port, src)
            if not ip_ep:
                err_msg = f"Did not find IP endpoint {port} with ip {src}"
                out["arg2"] = False
                out["arg3"] = err_msg
                device.applog.info(err_msg)
            else:
                device.applog.info(f"Sending Ping from {ip_ep.Name} to {dst}")
                out.update(ip_ep.SendPing(DestIp=dst)[0])

            res.append(out)
            if not out["arg2"]:
                err = 1

        return err, [{"success": msg["arg2"],
                      "info": msg["arg3"],
                      "port": msg["port"],
                      "src_ip": msg["src_ip"],
                      "dst_ip": msg["dst_ip"]} for msg in res]

    def run_send_arp(self, device, command, *argv, **kwarg):
        """
        - IxiaClient
           send_arp - [port, src_ip]
        """
        params = kwarg["params"]
        res = []
        err = 0
        for param in params:
            port = param["port"]
            src = param.get("src_ip", None)
            out = {
                "port": port,
                "src_ip": src,
            }

            ip_ep = self.__get_ip_iface(port, src)
            if not ip_ep:
                out["arg2"] = False
                device.applog.info(f"Did not find IP endpoint {port} with ip {src}")
            else:
                device.applog.info(f"Sending ARP from {ip_ep.Name}")
                out.update(ip_ep.SendArp()[0])

            res.append(out)
            if not out["arg2"]:
                err = 1

        return err, [{"success": msg["arg2"],
                      "port": msg["port"],
                      "src_ip": msg["src_ip"]} for msg in res]
