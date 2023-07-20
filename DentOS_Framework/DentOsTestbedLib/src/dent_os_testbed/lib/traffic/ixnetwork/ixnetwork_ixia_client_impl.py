import os
import sys
import time

from dent_os_testbed.lib.traffic.ixnetwork.ixnetwork_ixia_client import IxnetworkIxiaClient
from ixnetwork_restpy.assistants.statistics.statviewassistant import StatViewAssistant as SVA
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
    bad_crc = {True: '', False: ''}

    def format_connect(self, command, *argv, **kwarg):
        return command

    def run_connect(self, device, command, *argv, **kwarg):
        """
        - IxiaClient
          connect - client_addr, ports- ['chassis_ip:card:port',...]
          disconnect -
        """
        # TODO: Implement me
        if command == 'disconnect':
            if IxnetworkIxiaClientImpl.session is not None:
                device.applog.info('Removing Session ID: %d' % IxnetworkIxiaClientImpl.session.Id)
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
            return 0, ''
        params = kwarg['params']
        if not params or not params[0] or 'test' in device.host_name:
            return 0, ''
        param = params[0]
        try:
            caddr = param['client_addr']
            cport = param.get('client_port', 443)
            if not caddr:
                return 0, 'No Address to connect!'

            gw = SessionAssistant(
                IpAddress=caddr,
                RestPort=cport,
                UserName=device.username,
                Password=device.password,
                SessionName='DENT',
                ClearConfig=True
            )  # ,LogLevel='info'
            session = gw.Session

            device.applog.info('Connected to Linux Gateway Session ID: %d' % session.Id)
            device.applog.info('Reserving test ports, and may take a minute...')
            IxnetworkIxiaClientImpl.session = session
            IxnetworkIxiaClientImpl.ixnet = session.Ixnetwork
            IxnetworkIxiaClientImpl.ixnet.NewConfig()
            IxnetworkIxiaClientImpl.rr_eps = []
            IxnetworkIxiaClientImpl.bgp_eps = []
            IxnetworkIxiaClientImpl.ip_eps = []
            IxnetworkIxiaClientImpl.eth_eps = []
            IxnetworkIxiaClientImpl.raw_eps = []
            IxnetworkIxiaClientImpl.tis = []
            crc = IxnetworkIxiaClientImpl.ixnet.Traffic.TrafficItem.ConfigElement._SDM_ENUM_MAP['crc']
            IxnetworkIxiaClientImpl.bad_crc = {True: crc[0], False: crc[1]}
            IxnetworkIxiaClientImpl.stack_template = {
                stack_type: IxnetworkIxiaClientImpl.ixnet.Traffic.ProtocolTemplate.find(StackTypeId=f'^{stack_type}$')
                for stack_type in ('ipv4', 'ipv6', 'vlan', 'ethernet', 'tcp', 'udp', 'icmpv1', 'icmpv2', 'icmpv6',
                                   'igmpv2', 'igmpv3MembershipQuery', 'igmpv3MembershipReport', 'llc',
                                   'stpCfgBPDU', 'stpTCNBPDU', 'rstpBPDU', 'lldp', 'custom_v2')
            }

            device.applog.info('Connection to Ixia REST API Server Established')
            ixia_ports = param['tgen_ports']
            swp_ports = param['swp_ports']
            dev_groups = param['dev_groups']

            vports = {}
            for port, sport in zip(ixia_ports, swp_ports):
                # Specify Location on Port Add to simplify assignment
                vports[port] = (IxnetworkIxiaClientImpl.ixnet.Vport.add(Name=port, Location=port.replace(':', ';')), sport)

            device.applog.info('Assigning ports')
            IxnetworkIxiaClientImpl.ixnet.AssignPorts(True)
            portType = vports[port][0].Type

            lags = {}
            lag_ports = []
            if (portType != 'ethernetvm'):
                # init virtual lags
                for name, group in dev_groups.items():
                    if group[0]['type'] != 'lag':
                        continue
                    lag_vports = [vports[port][0].href for port in group[0]['lag_members']]
                    lags[name] = {
                        'vports': lag_vports,
                        'instance': IxnetworkIxiaClientImpl.ixnet.Lag.add(Name=name, Vports=lag_vports),
                    }
                lag_ports = [port for lag in lags.values() for port in lag['vports']]

            if (portType != 'ethernetvm'):
                self.__update_ports_mode(vports, device)
            # Add ports
            for port, vport in vports.items():
                if vport[0].href in lag_ports or port not in dev_groups.keys():
                    continue
                device.applog.info('Adding interface on ixia port {} swp {}'.format(port, vport[1]))
                topo = IxnetworkIxiaClientImpl.ixnet.Topology.add(Vports=vport[0])
                self.__add_endpoint(dev_groups, device, topo, port, vport)

            # Add lags
            for name, lag in lags.items():
                device.applog.info('Adding lag {} with ports {}'.format(name, lag['vports']))
                topo = IxnetworkIxiaClientImpl.ixnet.Topology.add(Ports=[lag['instance']])
                lag['instance'].Vports = lag['vports']
                lag['instance'].ProtocolStack.add().Ethernet.add().Lagportlacp.add()
                self.__add_endpoint(dev_groups, device, topo, name, lag['instance'], is_lag=True)

        except Exception as e:
            # Log Exception with Line Number and Return Error
            device.applog.info(f'Exception Caught: {repr(e)}')

            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            device.applog.info(f'{exc_type}, {fname}:{exc_tb.tb_lineno}')
            return -1, 'Error!'
        return 0, 'Connected!'

    @staticmethod
    def __add_endpoint(dev_groups, device, topo, name, instance, is_lag=False):
        """
        Creates and stores L2/L3 endpoints. Works both with regular ports and lags.
        """
        for dev in dev_groups[name]:
            device.applog.info('Adding device {}'.format(dev))
            l2_name = name if is_lag else instance[1]
            is_ipv6 = dev.get('version', 'ipv4') == 'ipv6'
            dev_group = topo.DeviceGroup.add(Multiplier=dev.get('count', 2))
            # L2
            if dev.get('vlan'):
                eth = dev_group.Ethernet.add(Name=l2_name, UseVlans=True, VlanCount=1)
                eth.Vlan.find()[0].VlanId.Single(dev['vlan'])
            else:
                eth = dev_group.Ethernet.add(Name=l2_name)
            # L3
            if is_ipv6:
                ep = eth.Ipv6.add(Name=dev['name'])
                ep.Address.Increment(dev['ip'], '::1')
            else:
                ep = eth.Ipv4.add(Name=dev['name'])
                ep.Address.Increment(dev['ip'], '0.0.0.1')
            ep.GatewayIp.Single(dev['gw'])
            ep.Prefix.Single(dev['plen'])

            if dev.get('bgp_peer', {}):
                bp = dev['bgp_peer']
                if is_ipv6:
                    bgp_ep = ep.BgpIpv6Peer.add(Name=dev['name'])
                else:
                    bgp_ep = ep.BgpIpv4Peer.add(Name=dev['name'])
                bgp_ep.DutIp.Single(dev['gw'])
                bgp_ep.Type.Single('external')
                bgp_ep.LocalAs2Bytes.Single(bp['local_as'])
                bgp_ep.HoldTimer.Single(bp['hold_timer'])
                bgp_ep.UpdateInterval.Single(bp['update_interval'])
                ng = dev_group.NetworkGroup.add(
                    Multiplier=len(bp['route_ranges']), Name=dev['name']
                )
                ng.Enabled.Single(True)
                for rr in bp['route_ranges']:
                    if is_ipv6:
                        pool = ng.Ipv6PrefixPools.add(
                            Name=dev['name'], NumberOfAddresses=rr['number_of_routes']
                        )
                    else:
                        pool = ng.Ipv4PrefixPools.add(
                            Name=dev['name'], NumberOfAddresses=rr['number_of_routes']
                        )
                    pool.NetworkAddress.Single(rr['first_route'])
                    IxnetworkIxiaClientImpl.rr_eps.append(pool)

                IxnetworkIxiaClientImpl.bgp_eps.append(bgp_ep)
            else:
                IxnetworkIxiaClientImpl.bgp_eps.append(ep)
                IxnetworkIxiaClientImpl.rr_eps.append(ep)
            IxnetworkIxiaClientImpl.ip_eps.append(ep)
            IxnetworkIxiaClientImpl.eth_eps.append(eth)
            if is_lag:
                IxnetworkIxiaClientImpl.raw_eps.append(instance)
            else:
                IxnetworkIxiaClientImpl.raw_eps.append(instance[0].Protocols.find())

    @staticmethod
    def __update_ports_mode(vports, device):
        """
        Changes media modes for Ixia ports
        """
        for port, vport in vports.items():
            card = vport[0].L1Config.NovusTenGigLan or vport[0].L1Config.Ethernet
            if device.media_mode == 'mixed':
                # Get required media mode. Default - copper
                required_media = next((link[2] for link in device.links if link[0] == port), 'copper')
                device.applog.info(f'Changing port: {port} media mode {required_media}')
                card.Media = required_media
                card.AutoInstrumentation = 'floating'
            elif device.media_mode == 'fiber':
                device.applog.info('Changing all vports media mode to fiber')
                card.Media = 'fiber'
                card.AutoInstrumentation = 'floating'
            else:
                device.applog.info('Changing all vports media mode to copper')
                card.Media = 'copper'
                card.AutoInstrumentation = 'floating'

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
        # TODO: Implement me
        if not IxnetworkIxiaClientImpl.ixnet:
            return 0, 'Ixia not connected'
        params = kwarg['params']
        if not params or not params[0]:
            return 0, 'Need to specify config file name'
        param = params[0]
        fname = param['config_file_name']
        name = os.path.basename(fname)
        if command == 'load_config':
            files = IxnetworkIxiaClientImpl.session.GetFileList()
            found = False
            for f in files['files']:
                if f['name'] == name:
                    found = True
                    break
            if not found:
                out = IxnetworkIxiaClientImpl.session.UploadFile(fname, name)
            out = IxnetworkIxiaClientImpl.ixnet.LoadConfig(Files(name))
            # get the traffic items back
            IxnetworkIxiaClientImpl.tis = IxnetworkIxiaClientImpl.ixnet.Traffic.TrafficItem.find()
        elif command == 'save_config':
            out = IxnetworkIxiaClientImpl.ixnet.SaveConfig(Files(name))
            out += IxnetworkIxiaClientImpl.session.DownloadFile(name, fname)
        return 0, out

    def parse_config(self, command, output, *argv, **kwarg):
        return command

    def format_traffic_item(self, command, *argv, **kwarg):
        return command

    @staticmethod
    def __configure_egress_tracking(ti, pkt_data):
        if 'egress_track_by' not in pkt_data:
            return
        ti.EgressEnabled = True
        track_by = pkt_data['egress_track_by']
        if type(track_by) is list:
            track_by = ''.join(track_by)
        if 'vlan' in track_by:
            tracker = ti.EgressTracking.add()
            if 'vlan_4k' in track_by:
                tracker.Offset = 'Outer VLAN ID (12 bits)'  # vid 0..4095
            else:
                tracker.Offset = 'Outer VLAN ID (4 bits)'  # vid 0..15
        if 'pcp' in track_by:
            tracker = ti.EgressTracking.add()
            tracker.Offset = 'Outer VLAN Priority (3 bits)'  # pcp 0..7
        if 'dscp' in track_by:
            tracker = ti.EgressTracking.add()
            tracker.Offset = 'IPv4 DSCP (6 bits)'  # dscp 0..63

    @staticmethod
    def __parse_multivalue(value):
        if 'type' not in value:
            raise KeyError(f'Value type is mandatory {value}')

        if value['type'] == 'single':
            return {
                'ValueType': 'singleValue',
                'SingleValue': str(value['value']),
            }
        elif value['type'] in ('increment', 'decrement'):
            return {
                'ValueType': value['type'],
                'StartValue': str(value['start']),
                'StepValue': str(value['step']),
                # choosing a large number will increase wait time from Ixia
                'CountValue': str(value.get('count', 255)),
            }
        elif value['type'] == 'list':
            if not value.get('list', []):
                raise ValueError('Value list cannot be empty')
            return {
                'ValueType': 'valueList',
                'ValueList': value['list'],
            }
        elif value['type'] == 'random':
            return {
                'ValueType': 'nonRepeatableRandom',
                'RandomMask': value.get('mask'),  # ignored when applied to MAC
            }

        valid_types = ('single', 'increment', 'decrement', 'list', 'random')
        raise ValueError(f'Valid multivalue types are: {valid_types}')

    def __update_field(self, field, value):
        if field.FieldTypeId == 'ipv4.header.priority.raw':  # exception for dscp
            field.ActiveFieldChoice = True
        if type(value) == str or type(value) == int or type(value) == float:
            param = self.__parse_multivalue({'type': 'single', 'value': value})
        elif type(value) == dict:
            param = self.__parse_multivalue(value)
        else:
            raise ValueError(f'Unable to set {value} for field {field.Name}')
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
            'line_rate': 'percentLineRate',
            'bps_rate': 'bitsPerSecond',
            'ipg_rate': 'interPacketGap',
            'pps_rate': 'framesPerSecond'}
        config_element.FrameRate.update(
            Type=frame_rate_types[pkt_data.get('frame_rate_type', 'pps_rate')],
            Rate=pkt_data.get('rate', '100'),
        )

    def __update_transmission_control(self, config_element, pkt_data):
        """
        Update transmission_control type from pkt_data
        Args:
            config_element (ConfigElement): grouping of endpoints under the Traffic Item per unique packet structure
            pkt_data (dict): Packet stream config
        """
        transmission_control_types = {
            'continuous': 'continuous',
            'fixedPktCount': 'fixedFrameCount',
            'fixedDuration': 'fixedDuration'}
        config_element.TransmissionControl.update(
            Type=transmission_control_types[pkt_data.get('transmissionControlType', 'continuous')],
            StartDelay=pkt_data.get('startDelay', 0),
            MinGapBytes=pkt_data.get('minGapBytes', 12),
            FrameCount=pkt_data.get('frameCount', 1),
            Duration=pkt_data.get('duration', 1))

    @classmethod
    def __create_traffic_items(cls, device, pkt_data, name):
        traffic_type = pkt_data.get('type', 'ipv4')
        if traffic_type == 'ethernet':
            ixia_traffic_type = 'ethernetVlan'
        elif traffic_type == 'bgp':
            ixia_traffic_type = 'ipv4'
        elif traffic_type == 'bpdu':
            ixia_traffic_type = 'raw'
        elif traffic_type == 'custom':
            ixia_traffic_type = 'raw'
        else:
            ixia_traffic_type = traffic_type

        for ip1, ep1, rep1, rr1 in zip(cls.ip_eps, cls.eth_eps, cls.raw_eps, cls.rr_eps):
            if any(src in pkt_data and endpoint.Name not in pkt_data[src]
                   for src, endpoint in (('ip_source', ip1), ('ep_source', ep1), ('bgp_source', rr1))):
                continue
            device.applog.info(f'Creating {traffic_type} traffic stream')
            ti = cls.ixnet.Traffic.TrafficItem.add(
                Name=name, TrafficType=ixia_traffic_type
            )
            ep_count = 0
            for ip2, ep2, rep2, rr2 in zip(cls.ip_eps, cls.eth_eps, cls.raw_eps, cls.rr_eps):
                if ep1 == ep2 and not pkt_data.get('allowSelfDestined', False):
                    continue
                if any(dst in pkt_data and endpoint.Name not in pkt_data[dst]
                       for dst, endpoint in (('ip_destination', ip2),
                                             ('ep_destination', ep2),
                                             ('bgp_destination', rr2))):
                    continue

                src_name, dst_name = None, None
                if traffic_type in ('ipv4', 'ipv6'):
                    src, dst = ip1, ip2
                elif traffic_type == 'bgp':
                    src, dst = rr1, rr2
                elif traffic_type in ('raw', 'bpdu', 'custom'):
                    src, dst = rep1, rep2
                    src_name, dst_name = ep1.Name, ep2.Name
                else:
                    src, dst = ep1, ep2

                if src_name is None and dst_name is None:
                    src_name, dst_name = src.Name, dst.Name
                device.applog.info(f'Adding endpoint {src_name} to {dst_name}')

                ti.EndpointSet.add(Sources=src, Destinations=dst)
                ep_count += 1
            cls.tis.append(ti)
            ti.Enabled = True

            yield ti, ep_count

    def __configure_l2_stack(self, config_element, pkt_data, track_by):
        eth_stack = config_element.Stack.find(StackTypeId='^ethernet$')

        if 'dstMac' in pkt_data:
            self.__update_field(eth_stack.Field.find(FieldTypeId='ethernet.header.destinationAddress'),
                                pkt_data['dstMac'])
        if 'srcMac' in pkt_data:
            self.__update_field(eth_stack.Field.find(FieldTypeId='ethernet.header.sourceAddress'),
                                pkt_data['srcMac'])
        if 'protocol' in pkt_data and pkt_data['protocol'] not in ['ipv6', 'ipv4', 'ip', '802.1Q', 'lldp']:
            self.__update_field(eth_stack.Field.find(FieldTypeId='ethernet.header.etherType'),
                                pkt_data['protocol'])
        if 'vlanID' in pkt_data:
            vlan_stack = config_element.Stack.read(
                eth_stack.AppendProtocol(self.stack_template['vlan'])
            )
            self.__update_field(vlan_stack.Field.find(FieldTypeId='vlan.header.vlanTag.vlanID'),
                                pkt_data['vlanID'])
            if 'vlanPriority' in pkt_data:
                self.__update_field(vlan_stack.Field.find(FieldTypeId='vlan.header.vlanTag.vlanUserPriority'),
                                    pkt_data['vlanPriority'])
            track_by.update(['vlanVlanId0', 'vlanVlanUserPriority0'])
            return vlan_stack
        return eth_stack

    def __configure_l3_stack(self, config_element, pkt_data, track_by, eth_stack):
        if pkt_data.get('protocol') == 'lldp':
            return
        elif pkt_data.get('type') == 'ipv6' or pkt_data.get('protocol') == 'ipv6':
            proto = 'ipv6'
            fields = {
                'dstIp': 'ipv6.header.dstIP',
                'srcIp': 'ipv6.header.srcIP',
                'hopLimit': 'ipv6.header.hopLimit',
                'traffic_class': 'ipv6.header.versionTrafficClassFlowLabel.trafficClass',
            }
        else:
            proto = 'ipv4'
            fields = {
                'dstIp': 'ipv4.header.dstIp',
                'srcIp': 'ipv4.header.srcIp',
                'dscp_ecn': 'ipv4.header.priority.raw',
                'ttl': 'ipv4.header.ttl',
                'totalLength': 'ipv4.header.totalLength',
                'l3Proto': 'ipv4.header.protocol',
                'ipv4Checksum': 'ipv4.header.checksum',
                'ipv4HeaderLength': 'ipv4.header.headerLength',
            }

        ip_stack = config_element.Stack.find(StackTypeId=f'^{proto}$')
        if not len(ip_stack):
            ip_stack = config_element.Stack.read(
                eth_stack.AppendProtocol(self.stack_template[proto])
            )
        for key, field_type in fields.items():
            if key not in pkt_data:
                continue
            if key == 'dscp_ecn':
                track_by.add('ipv4Raw0')
            if key == 'traffic_class':
                track_by.add('ipv6Trafficclass0')
            self.__update_field(ip_stack.Field.find(FieldTypeId=field_type),
                                pkt_data[key])
        return ip_stack

    def __configure_l4_stack(self, config_element, pkt_data, track_by, ip_stack):
        l4_proto_types = ['tcp', 'udp', 'icmpv1', 'icmpv2', 'icmpv6',
                          'igmpv2', 'igmpv3MembershipQuery',
                          'igmpv3MembershipReport']
        if 'ipproto' not in pkt_data:
            return
        proto = pkt_data['ipproto']
        if proto not in l4_proto_types:
            return

        l4_stack = config_element.Stack.read(
            ip_stack.AppendProtocol(self.stack_template[proto])
        )
        if proto == 'igmpv3MembershipReport':
            grp_addr_id = 'header.groupRecords.groupRecord.multicastAddress'
            num_srcs_id = 'header.groupRecords.groupRecord.numberOfSources'
        else:
            grp_addr_id = 'header.groupAddress'
            num_srcs_id = 'header.numberOfSources'

        if proto == 'icmpv6':
            fields = {
                'icmpType': 'icmpv6.icmpv6Message.icmpv6MessegeType.destinationUnreachableMessage.mesageType',
                'icmpCode': 'icmpv6.icmpv6Message.icmpv6MessegeType.destinationUnreachableMessage.code',
            }
        else:
            fields = {
                'dstPort': f'{proto}.header.dstPort',
                'srcPort': f'{proto}.header.srcPort',
                'icmpType': f'{proto}.message.messageType',
                'icmpCode': f'{proto}.message.codeValue',
                'igmpType': f'{proto}.header.type',
                'igmpChecksum': f'{proto}.header.checksum',
                'igmpGroupAddr': f'{proto}.{grp_addr_id}',
                'igmpRecordType': f'{proto}.header.groupRecords.groupRecord.recordType',
                'igmpSourceAddr': f'{proto}.header.groupRecords.groupRecord.multicastSources.multicastSource',
                'numberOfSources': f'{proto}.{num_srcs_id}',
                'maxResponseCode': f'{proto}.header.maximumResponseCodeunits110Second',
            }

        for key, field_type in fields.items():
            if key not in pkt_data:
                continue
            self.__update_field(l4_stack.Field.find(FieldTypeId=field_type),
                                pkt_data[key])
        return l4_stack

    def __configure_bpdu(self, config_element, pkt_data, track_by):
        version = 'rstpBPDU' if pkt_data['version'] == 'rstp' else 'stpCfgBPDU'

        eth_stack = self.__configure_l2_stack(config_element, {**pkt_data, 'dstMac': '01:80:C2:00:00:00'}, track_by)
        llc_stack = config_element.Stack.read(
            eth_stack.AppendProtocol(self.stack_template['llc'])
        )
        bpdu_stack = config_element.Stack.read(
            llc_stack.AppendProtocol(self.stack_template[version])
        )

        fields = {
            'protocolIdentifier': f'{version}.header.protocolIdentifier',
            'protocolVersionIdentifier': f'{version}.header.protocolVersionIdentifier',
            'topologyChangeAcknowledgement': f'{version}.header.flags.topologyChangeAcknowledgement',
            'agreement': 'rstpBPDU.header.flags.agreement',
            'forwarding': 'rstpBPDU.header.flags.forwarding',
            'learning': 'rstpBPDU.header.flags.learning',
            'portRole': 'rstpBPDU.header.flags.portRole',
            'proposal': 'rstpBPDU.header.flags.proposal',
            'topologyChange': f'{version}.header.flags.topologyChange',
            'rootIdentifier': f'{version}.header.rootIdentifier',
            'rootPathCost': 'rstpBPDU.header.externalRootPathCost' if version == 'rstpBPDU' else
                            'stpCfgBPDU.header.rootPathCost',
            'bridgeIdentifier': 'rstpBPDU.header.regionalRootIdentifier' if version == 'rstpBPDU' else
                                'stpCfgBPDU.header.bridgeIdentifier',
            'portIdentifier': f'{version}.header.portIdentifier',
            'messageAge': f'{version}.header.messageAge',
            'maxAge': f'{version}.header.maxAge',
            'helloTime': f'{version}.header.helloTime',
            'forwardDelay': f'{version}.header.forwardDelay',
            'version1Length': 'rstpBPDU.header.version1Length',
        }

        for key, field_type in fields.items():
            if key not in pkt_data:
                continue
            self.__update_field(bpdu_stack.Field.find(FieldTypeId=field_type), pkt_data[key])

    def __configure_lldp_stack(self, config_element, pkt_data, eth_stack):
        if pkt_data.get('protocol') != 'lldp':
            return
        else:
            proto = 'lldp'
            fields = {
                # Mandatory TLVs
                'chassisLen': 'lldp.header.mandatoryTlv.chassisIdTlv.length',
                'chassisSubtype': 'lldp.header.mandatoryTlv.chassisIdTlv.subtype',
                'chassisVarLen': 'lldp.header.mandatoryTlv.chassisIdTlv.variableChassisIDLength',
                'chassisId': 'lldp.header.mandatoryTlv.chassisIdTlv.chassisId',
                'portLen': 'lldp.header.mandatoryTlv.portIdTlv.length',
                'portSubtype': 'lldp.header.mandatoryTlv.portIdTlv.subtype',
                'portVarLen': 'lldp.header.mandatoryTlv.portIdTlv.variablePortIDLength',
                'portId': 'lldp.header.mandatoryTlv.portIdTlv.portId',
                'ttlLen': 'lldp.header.mandatoryTlv.ttlTlv.length',
                'ttlVal': 'lldp.header.mandatoryTlv.ttlTlv.ttl'
            }

            lldp_stack = config_element.Stack.read(
                eth_stack.AppendProtocol(self.stack_template[proto])
            )
            for key, field_type in fields.items():
                if key not in pkt_data:
                    continue
                self.__update_field(lldp_stack.Field.find(FieldTypeId=field_type), pkt_data[key])
            return lldp_stack

    def __configure_custom_stack(self, config_element, pkt_data, track_by):
        proto = 'custom_v2'
        fields = {
            'customLength': 'custom_v2.header.length',
            'customData': 'custom_v2.header.data'
        }

        eth_stack = self.__configure_l2_stack(config_element, {**pkt_data}, track_by)
        custom_stack = config_element.Stack.read(
            eth_stack.AppendProtocol(self.stack_template[proto])
        )

        for key, field_type in fields.items():
            if key not in pkt_data:
                continue
            self.__update_field(custom_stack.Field.find(FieldTypeId=field_type), pkt_data[key])
        return custom_stack

    def set_traffic(self, device, name, pkt_data):
        for ti, ep_count in self.__create_traffic_items(device, pkt_data, name):
            track_by = {'trackingenabled0', 'sourceDestValuePair0'}
            for ep in range(ep_count):
                config_element = ti.ConfigElement.find(EndpointSetId=ep + 1)
                self.__update_frame_rate(config_element, pkt_data)
                config_element.FrameSize.update(
                    Type='fixed', FixedSize=pkt_data.get('frameSize', '512')
                )
                config_element.Crc = self.bad_crc[pkt_data.get('bad_crc', False)]
                self.__update_transmission_control(config_element, pkt_data)

                if pkt_data.get('type') == 'bpdu':
                    self.__configure_bpdu(config_element, pkt_data, track_by)
                    continue
                elif pkt_data.get('type') == 'custom':
                    self.__configure_custom_stack(config_element, pkt_data, track_by)
                    continue

                eth_stack = self.__configure_l2_stack(config_element, pkt_data, track_by)
                self.__configure_lldp_stack(config_element, pkt_data, eth_stack)
                ip_stack = self.__configure_l3_stack(config_element, pkt_data, track_by, eth_stack)
                self.__configure_l4_stack(config_element, pkt_data, track_by, ip_stack)

            ti.Tracking.find()[0].TrackBy = list(track_by)
            ti.BiDirectional = pkt_data.get('bi_directional', False)
            ti.AllowSelfDestined = pkt_data.get('allowSelfDestined', False)
            self.__configure_egress_tracking(ti, pkt_data)

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
            return 0, 'Ixia not connected'
        # TODO: Implement me
        if command == 'set_traffic':
            params = kwarg['params']
            if not params or not params[0]:
                return 0, 'Need to specify the packet data'
            param = params[0]
            self.set_traffic(device, name=param['name'], pkt_data=param['pkt_data'])
        elif command == 'start_traffic':
            device.applog.info('Starting Traffic')
            IxnetworkIxiaClientImpl.ixnet.Traffic.StartStatelessTrafficBlocking()
        elif command == 'stop_traffic':
            device.applog.info('Stopping Traffic')
            IxnetworkIxiaClientImpl.ixnet.Traffic.StopStatelessTrafficBlocking()
            attempts = 0
            while IxnetworkIxiaClientImpl.ixnet.Traffic.IsTrafficRunning and attempts < 3:
                device.applog.info(
                    '\tIs Traffic running: ' + str(IxnetworkIxiaClientImpl.ixnet.Traffic.IsTrafficRunning))
                time_to_sleep = 5
                time.sleep(time_to_sleep)
                attempts += 1
            if attempts > 3:
                device.applog.info(f'INFO: Traffic not stopped after {attempts * time_to_sleep} Seconds')
        elif command == 'get_stats':
            device.applog.info('Getting Stats')
            stats_type = 'Port Statistics'
            params = kwarg['params']
            if params or params[0]:
                stats_type = params[0].get('stats_type', stats_type)
            stats = SVA(IxnetworkIxiaClientImpl.ixnet, stats_type)
            # device.applog.info(stats)
            return 0, stats
        elif command == 'get_drilldown_stats':
            UDS = 'User Defined Statistics'
            param = kwarg['params'][0]
            row = param['row']
            view = IxnetworkIxiaClientImpl.ixnet.Statistics.View.find(Caption=row._view_name)
            view.DoDrillDownByOption(row._index + 1 if row._index != -1 else 1, param['group_by'])
            uds_view = IxnetworkIxiaClientImpl.ixnet.Statistics.View.find(Caption=UDS)
            if param.get('num_of_rows'):
                uds_view.Page.EgressPageSize = int(param['num_of_rows'])
            uds_view.Enabled = True  # have to enable uds view every time it is changed
            return self.run_traffic_item(device, 'get_stats', params=[{'stats_type': UDS}])
        elif command == 'clear_stats':
            device.applog.info('Clear Stats')
            IxnetworkIxiaClientImpl.ixnet.ClearStats()
        elif command == 'clear_traffic':
            traffic_names = kwarg['params'][0]['traffic_names']
            tis_to_remove = IxnetworkIxiaClientImpl.tis[:]
            if traffic_names:
                tis_to_remove = filter(lambda ti: ti.Name in traffic_names, tis_to_remove)
            for traffic_item in tis_to_remove:
                device.applog.info(f'TI to be removed: {traffic_item.Name}')
                traffic_item.remove()
                IxnetworkIxiaClientImpl.tis.remove(traffic_item)
        return 0, ''

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
            return 0, 'Ixia not connected'
        # TODO: Implement me
        if command == 'start_protocols':
            device.applog.info('Starting All Protocols')
            IxnetworkIxiaClientImpl.ixnet.StartAllProtocols(Arg1='sync')
            time.sleep(15)
            for ep in IxnetworkIxiaClientImpl.ip_eps:
                device.applog.info('Sending ARP on ' + ep.Name)
                ep.Start()
                if 'SendArp' in dir(ep):
                    ep.SendArp()  # ipv4
                else:
                    ep.SendNs()  # ipv6
            time.sleep(5)
            device.applog.info('Generating Traffic')
            for ti in IxnetworkIxiaClientImpl.tis:
                ti.Generate()
            device.applog.info('Applying Traffic')
            IxnetworkIxiaClientImpl.ixnet.Traffic.Apply()
        elif command == 'stop_protocols':
            device.applog.info('Stopping All Protocols')
            IxnetworkIxiaClientImpl.ixnet.StopAllProtocols(Arg1='sync')
        elif command == 'set_protocol':
            params = kwarg['params']
            param = params[0]
            for ep in IxnetworkIxiaClientImpl.bgp_eps:
                if 'bgp_peer' in param and param['bgp_peer'] != ep.Name:
                    continue
                enable = param['enable']
                IxnetworkIxiaClientImpl.bgp_eps
                ep.Active.Single(enable)
            IxnetworkIxiaClientImpl.ixnet.Globals.Topology.ApplyOnTheFly()
        return 0, ''

    def parse_protocol(self, command, output, *argv, **kwarg):
        return command

    def format_send_ping(self, command, *argv, **kwarg):
        return command

    def format_resolve_neighbor(self, command, *argv, **kwarg):
        return command

    def format_update_l1_config(self, command, *argv, **kwarg):
        return command

    @classmethod
    def __get_ip_iface(cls, port, port_ip=None):
        vport = cls.ixnet.Vport.find(Name=port)
        for ip_ep in cls.ip_eps:
            # ip -> eth -> dev group -> topo
            topo = ip_ep.parent.parent.parent
            if vport.href not in topo.Ports:
                continue
            if not port_ip:
                return ip_ep

            if '::' in port_ip:  # aa:bb::cc:dd -> aa:bb:0:0:0:0:cc:dd
                ip = port_ip
                if ip.startswith('::'):
                    ip = '0' + ip
                if ip.endswith('::'):
                    ip = ip + '0'
                begin, end = ip.split('::')
                num_of_zero_groups = 8 - port_ip.count(':')
                ip = ':'.join([begin] + ['0']*num_of_zero_groups + [end])
            else:
                ip = port_ip

            if ip in ip_ep.Address.Pattern:
                return ip_ep
        return None

    def run_send_ping(self, device, command, *argv, **kwarg):
        """
        - IxiaClient
           send_ping - [port, dst_ip, src_ip]
        """
        params = kwarg['params']
        res = []
        err = 0
        for param in params:
            port = param['port']
            dst = param['dst_ip']
            src = param.get('src_ip', None)
            out = {
                'port': port,
                'src_ip': src,
                'dst_ip': dst,
            }

            ip_ep = self.__get_ip_iface(port, src)
            if not ip_ep:
                err_msg = f'Did not find IP endpoint {port} with ip {src}'
                out['arg2'] = False
                out['arg3'] = err_msg
                device.applog.info(err_msg)
            else:
                device.applog.info(f'Sending Ping from {ip_ep.Name} to {dst}')
                out.update(ip_ep.SendPing(DestIp=dst)[0])

            res.append(out)
            if not out['arg2']:
                err = 1

        return err, [{'success': msg['arg2'],
                      'info': msg['arg3'],
                      'port': msg['port'],
                      'src_ip': msg['src_ip'],
                      'dst_ip': msg['dst_ip']} for msg in res]

    def run_resolve_neighbor(self, device, command, *argv, **kwarg):
        """
        - IxiaClient
           send_arp - [port, src_ip]
           send_ns - [port, src_ip]
        """
        params = kwarg['params']
        res = []
        err = 0
        for param in params:
            port = param['port']
            src = param.get('src_ip', None)
            out = {
                'port': port,
                'src_ip': src,
            }

            ip_ep = self.__get_ip_iface(port, src)
            if not ip_ep:
                out['arg2'] = False
                device.applog.info(f'Did not find IP endpoint {port} with ip {src}')
            else:
                if command == 'send_arp':
                    device.applog.info(f'Sending ARP from {ip_ep.Name}')
                    out.update(ip_ep.SendArp()[0])
                elif command == 'send_ns':
                    device.applog.info(f'Sending NS from {ip_ep.Name}')
                    out.update(ip_ep.SendNs()[0])

            res.append(out)
            if not out['arg2']:
                err = 1

        return err, [{'success': msg['arg2'],
                      'port': msg['port'],
                      'src_ip': msg['src_ip']} for msg in res]

    def run_update_l1_config(self, device, command, *argv, **kwarg):
        if not IxnetworkIxiaClientImpl.ixnet:
            return 1, 'Ixia not connected'
        if command == 'update_l1_config':
            vports = IxnetworkIxiaClientImpl.ixnet.Vport.find()
            ports = kwarg['params'][0].get('tgen_ports', [])
            if len(ports) < 1:
                return 1, 'IXIA ports not provided'
            # fd -> full duplex ; hd -> half duplex
            duplex = 'fd' if kwarg['params'][0].get('duplex', 'Full').capitalize() == 'Full' else 'hd'
            speed = kwarg['params'][0].get('speed', None)
            if speed:
                ixia_speed = self.__convert_to_ixia_speed(speed, duplex)
            else:
                ixia_speed = None
            autoneg = kwarg['params'][0].get('autoneg', True)
            names = [vport.Name for vport in vports]
            for port in ports:
                if port not in names:
                    continue
                required_ixia_port = vports[names.index(port)]
                card = required_ixia_port.L1Config.NovusTenGigLan or required_ixia_port.L1Config.Ethernet
                device.applog.info(f'Changing speed from {required_ixia_port.ActualSpeed} to {speed} \
                                     on tgen_port {required_ixia_port.Name}')
                device.applog.info(f'Changing autoneg to {autoneg} on tgen_port {required_ixia_port.Name}')
                card.update(AutoNegotiate=autoneg, Speed=ixia_speed)
            return 0, ''

    def run_switch_min_frame_size(self, device, command, *argv, **kwarg):
        if not IxnetworkIxiaClientImpl.ixnet:
            return 1, 'Ixia not connected'
        if command == 'switch_min_frame_size':
            IxnetworkIxiaClientImpl.ixnet.Traffic.EnableMinFrameSize = kwarg['params'][0].get('enable_min_size', True)
        return 0, ''

    def format_switch_min_frame_size(self, command, *argv, **kwarg):
        return command

    def parse_switch_min_frame_size(self, command, *argv, **kwarg):
        return command

    @classmethod
    def __convert_to_ixia_speed(self, speed, duplex):
        if speed == 100 or speed == 10:
            speed = f'speed{speed}{duplex}'
        elif speed == 1000:
            speed = f'speed{speed}'
        elif speed == 10000:
            speed = 'speed10g'
        else:
            raise ValueError(' Can not convert provided speed to IXIA speed value ')
        return speed
