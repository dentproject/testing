from random import randrange


def get_streams(srcMac, self_mac, prefix, dev_groups, tg_ports):
    return {
     'Bridged_UnknownL2UC': {
        'ip_source': dev_groups[tg_ports[0]][0]['name'],
        'ip_destination': dev_groups[tg_ports[1]][0]['name'],
        'srcMac': srcMac,
        'dstMac': '00:00:BB:11:22:33',
        'frameSize': 96,
        'protocol': '0x6666',
        'type': 'raw'
     },
     'BridgedLLDP': {
        'ip_source': dev_groups[tg_ports[0]][0]['name'],
        'ip_destination': dev_groups[tg_ports[1]][0]['name'],
        'srcMac': srcMac,
        'dstMac': '01:80:c2:00:00:0e',
        'frameSize': 96,
        'protocol': '0x88cc',
        'type': 'raw'
     },
     'LACPDU': {
        'ip_source': dev_groups[tg_ports[0]][0]['name'],
        'ip_destination': dev_groups[tg_ports[1]][0]['name'],
        'srcMac': srcMac,
        'dstMac': '01:80:c2:00:00:02',
        'frameSize': 130,
        'protocol': '0x8809',
        'type': 'raw'
     },
     'IPv4ToMe': {
        'ip_source': dev_groups[tg_ports[0]][0]['name'],
        'ip_destination': dev_groups[tg_ports[1]][0]['name'],
        'srcIp': '1.1.1.2',
        'dstIp': prefix,
        'srcMac': srcMac,
        'dstMac': self_mac,
        'frameSize': 96,
        'protocol': '0x0800',
        'type': 'raw'
     },
     'ARP_Request_BC': {
        'ip_source': dev_groups[tg_ports[0]][0]['name'],
        'ip_destination': dev_groups[tg_ports[1]][0]['name'],
        'srcMac': srcMac,
        'dstMac': 'FF:FF:FF:FF:FF:FF',
        'frameSize': 96,
        'protocol': '0x0806',
        'type': 'raw'
     },
     'ARP_Reply': {
        'ip_source': dev_groups[tg_ports[0]][0]['name'],
        'ip_destination': dev_groups[tg_ports[1]][0]['name'],
        'srcMac': srcMac,
        'dstMac': self_mac,
        'frameSize': 96,
        'protocol': '0x0806',
        'type': 'raw'
     },
     'IPv4_Broadcast': {
        'ip_source': dev_groups[tg_ports[0]][0]['name'],
        'ip_destination': dev_groups[tg_ports[1]][0]['name'],
        'srcIp': '1.1.1.2',
        'dstIp': '100.1.1.255',
        'srcMac': srcMac,
        'dstMac': 'FF:FF:FF:FF:FF:FF',
        'frameSize': 96,
        'protocol': '0x0800',
        'type': 'raw'
     },
     'IPV4_SSH': {
        'ip_source': dev_groups[tg_ports[0]][0]['name'],
        'ip_destination': dev_groups[tg_ports[1]][0]['name'],
        'srcIp': '1.1.1.2',
        'dstIp': prefix,
        'srcMac': srcMac,
        'dstMac': self_mac,
        'ipproto': 'tcp',
        'srcPort': str(randrange(0xffff + 1)),
        'dstPort': '22',
        'frameSize': 96,
        'protocol': '0x0800',
        'type': 'raw'
     },
     'IPV4_Telnet': {
        'ip_source': dev_groups[tg_ports[0]][0]['name'],
        'ip_destination': dev_groups[tg_ports[1]][0]['name'],
        'srcIp': '1.1.1.2',
        'dstIp': prefix,
        'srcMac': srcMac,
        'dstMac': self_mac,
        'ipproto': 'tcp',
        'srcPort': str(randrange(0xffff + 1)),
        'dstPort': '23',
        'frameSize': 96,
        'protocol': '0x0800',
        'type': 'raw'
     },
     'Host_to_Host_IPv4': {
        'ip_source': dev_groups[tg_ports[0]][0]['name'],
        'ip_destination': dev_groups[tg_ports[1]][0]['name'],
        'srcIp': '192.168.1.1',
        'dstIp': '192.168.1.253',
        'srcMac': srcMac,
        'dstMac': self_mac,
        'ipproto': 'tcp',
        'srcPort': str(randrange(0xffff + 1)),
        'dstPort': '23',
        'frameSize': 96,
        'protocol': '0x0800',
        'type': 'raw'
     },
     'IPv4_ICMP_Request': {
        'ip_source': dev_groups[tg_ports[0]][0]['name'],
        'ip_destination': dev_groups[tg_ports[1]][0]['name'],
        'srcIp': '1.1.1.2',
        'dstIp': prefix,
        'srcMac': srcMac,
        'dstMac': self_mac,
        'ipproto': 'icmpv1',
        'frameSize': 96,
        'protocol': '0x0800',
        'type': 'raw'
     },
     'IPv4_DCHP_BC': {
        'ip_source': dev_groups[tg_ports[0]][0]['name'],
        'ip_destination': dev_groups[tg_ports[1]][0]['name'],
        'srcIp': '0.0.0.0',
        'dstIp': '255.255.255.255',
        'srcMac': srcMac,
        'dstMac': 'FF:FF:FF:FF:FF:FF',
        'frameSize': 346,
        'ipproto': 'udp',
        'srcPort': '67',
        'dstPort': '68',
        'frameSize': 346,
        'protocol': '0x0800',
        'type': 'raw'
     },
     'IPv4_Reserved_MC': {
        'ip_source': dev_groups[tg_ports[0]][0]['name'],
        'ip_destination': dev_groups[tg_ports[1]][0]['name'],
        'srcIp': '1.1.1.2',
        'dstIp': '224.0.0.69',
        'srcMac': srcMac,
        'dstMac': '01:00:5E:00:00:45',
        'frameSize': 96,
        'protocol': '0x0800',
        'type': 'raw'
     },
     'IPv4_All_Systems_on_this_Subnet': {
        'ip_source': dev_groups[tg_ports[0]][0]['name'],
        'ip_destination': dev_groups[tg_ports[1]][0]['name'],
        'srcIp': '1.1.1.2',
        'dstIp': '224.0.0.1',
        'srcMac': srcMac,
        'dstMac': '01:00:5E:00:00:01',
        'frameSize': 96,
        'protocol': '0x0800',
        'type': 'raw'
     },
     'IPv4_All_Routers_on_this_Subnet': {
        'ip_source': dev_groups[tg_ports[0]][0]['name'],
        'ip_destination': dev_groups[tg_ports[1]][0]['name'],
        'srcIp': '1.1.1.2',
        'dstIp': '224.0.0.2',
        'srcMac': srcMac,
        'dstMac': '01:00:5E:00:00:02',
        'frameSize': 96,
        'protocol': '0x0800',
        'type': 'raw'
     },
     'IPv4_OSPFIGP': {
        'ip_source': dev_groups[tg_ports[0]][0]['name'],
        'ip_destination': dev_groups[tg_ports[1]][0]['name'],
        'srcIp': '1.1.1.2',
        'dstIp': '224.0.0.5',
        'srcMac': srcMac,
        'dstMac': '01:00:5E:00:00:05',
        'frameSize': 96,
        'protocol': '0x0800',
        'type': 'raw'
     },
     'IPv4_RIP2_Routers': {
        'ip_source': dev_groups[tg_ports[0]][0]['name'],
        'ip_destination': dev_groups[tg_ports[1]][0]['name'],
        'srcIp': '1.1.1.2',
        'dstIp': '224.0.0.9',
        'srcMac': srcMac,
        'dstMac': '01:00:5E:00:00:09',
        'frameSize': 96,
        'protocol': '0x0800',
        'type': 'raw'
     },
     'IPv4_EIGRP_Routers': {
        'ip_source': dev_groups[tg_ports[0]][0]['name'],
        'ip_destination': dev_groups[tg_ports[1]][0]['name'],
        'srcIp': '1.1.1.2',
        'dstIp': '224.0.0.10',
        'srcMac': srcMac,
        'dstMac': '01:00:5E:00:00:0A',
        'frameSize': 96,
        'protocol': '0x0800',
        'type': 'raw'
     },
     'IPv4_DHCP_Server/Relay_Agent': {
        'ip_source': dev_groups[tg_ports[0]][0]['name'],
        'ip_destination': dev_groups[tg_ports[1]][0]['name'],
        'srcIp': '1.1.1.2',
        'dstIp': '224.0.0.12',
        'srcMac': srcMac,
        'dstMac': '01:00:5E:00:00:0C',
        'ipproto': 'udp',
        'srcPort': '68',
        'dstPort': '67',
        'frameSize': 96,
        'protocol': '0x0800',
        'type': 'raw'
     },
     'IPv4_VRRP': {
        'ip_source': dev_groups[tg_ports[0]][0]['name'],
        'ip_destination': dev_groups[tg_ports[1]][0]['name'],
        'srcIp': '1.1.1.2',
        'dstIp': '224.0.0.18',
        'srcMac': srcMac,
        'dstMac': '01:00:5E:00:00:12',
        'frameSize': 96,
        'protocol': '0x0800',
        'type': 'raw'
     },
     'IPv4_IGMP': {
        'ip_source': dev_groups[tg_ports[0]][0]['name'],
        'ip_destination': dev_groups[tg_ports[1]][0]['name'],
        'srcIp': '1.1.1.2',
        'dstIp': '224.0.0.22',
        'srcMac': srcMac,
        'dstMac': '01:00:5E:00:00:16',
        'frameSize': 96,
        'protocol': '0x0800',
        'type': 'raw'
     },
     'IPV4_BGP': {
        'ip_source': dev_groups[tg_ports[0]][0]['name'],
        'ip_destination': dev_groups[tg_ports[1]][0]['name'],
        'srcIp': '1.1.1.2',
        'dstIp': prefix,
        'ipproto': 'tcp',
        'srcPort': '179',
        'dstPort': '179',
        'srcMac': srcMac,
        'dstMac': self_mac,
        'frameSize': 96,
        'protocol': '0x0800',
        'type': 'raw'
     }
    }
