import asyncio
import pytest

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_route import IpRoute
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.ethtool.ethtool import Ethtool
from dent_os_testbed.lib.ip.ip_neighbor import IpNeighbor
from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
)

from dent_os_testbed.utils.test_utils.tb_utils import (
    tb_device_tcpdump,
    tb_ping_device,
)


def vr_id_to_mac(vr):
    return f'00:00:5e:00:01:{vr:02x}'


async def setup_topo_for_vrrp(testbed, use_bridge=False, use_vid=None, use_tgen=False, vrrp_ip=None):
    """
    Setup:
                   TG L0     ______
            agg ------------ |    |
         ___| |___           |    |
      L0 |       | L1        | TG |
         |       |           |    |
    infra[0] -- infra[1] --- |____|
             L2         TG L1

    Configure:
        agg:
            L0, L1, TG L0: master bridge
            bridge: ip address 192.168.1.5/24
        infra[0]:
            L0 (port/bridge): ip address 192.168.1.3/24
            L2: ip address 192.168.3.10/24
                route 192.168.2.2 via 192.168.3.11
        infra[1]:
            L1 (port/bridge): ip address 192.168.1.4/24
            L2: ip address 192.168.3.11/24
            TG L1: ip address 192.168.2.1/24
        TG (if use_tgen=True):
            L0: ip address 192.168.1.5/24
            L1: ip address 192.168.2.2/24
    """
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [
        DeviceType.AGGREGATION_ROUTER,
        DeviceType.INFRA_SWITCH,
    ], 0)
    if not tgen_dev or not dent_devices or len(dent_devices) < 3:
        pytest.skip('The testbed does not have enough devices (1 agg + 2 infra)')

    infra = [dent for dent in dent_devices if dent.type == DeviceType.INFRA_SWITCH]
    if len(infra) < 2:
        pytest.skip('The testbed does not have enough infra devices')
    infra = infra[:2]

    agg = [dent for dent in dent_devices if dent.type == DeviceType.AGGREGATION_ROUTER]
    if len(agg) < 1:
        pytest.skip('The testbed does not have enough agg devices')
    agg = agg[0]

    dev_groups = {}
    vlan_dev = None
    bridge = 'br0'
    ep_ip = '192.168.1.5/24'
    links = [
        # L0
        {infra[0]: infra[0].links_dict[agg.host_name][0][0],
         agg: infra[0].links_dict[agg.host_name][1][0]},
        # L1
        {infra[1]: infra[1].links_dict[agg.host_name][0][0],
         agg: infra[1].links_dict[agg.host_name][1][0]},
        # L2
        {infra[0]: infra[0].links_dict[infra[1].host_name][0][0],
         infra[1]: infra[0].links_dict[infra[1].host_name][1][0]},
    ]
    tg_links = [
        # L0
        {tgen_dev: tgen_dev.links_dict[agg.host_name][0][0],
         agg: tgen_dev.links_dict[agg.host_name][1][0]},
        # L1
        {tgen_dev: tgen_dev.links_dict[infra[1].host_name][0][0],
         infra[1]: tgen_dev.links_dict[infra[1].host_name][1][0]},
    ]

    ip_link_config = {
        agg.host_name: [{'device': links[0][agg], 'master': bridge, 'operstate': 'up'},
                        {'device': links[1][agg], 'master': bridge, 'operstate': 'up'},
                        {'device': bridge, 'operstate': 'up'}],
        infra[0].host_name: [{'device': links[0][infra[0]], 'master': bridge, 'operstate': 'up'},
                             {'device': links[2][infra[0]], 'operstate': 'up'},
                             {'device': bridge, 'operstate': 'up'}],
        infra[1].host_name: [{'device': links[1][infra[1]], 'master': bridge, 'operstate': 'up'},
                             {'device': links[2][infra[1]], 'operstate': 'up'},
                             {'device': bridge, 'operstate': 'up'}],
    }
    if use_vid is not None:  # Q-bridge
        bridge_config = {
            dent.host_name: [{'name': bridge, 'type': 'bridge', 'vlan_filtering': 1, 'vlan_default_pvid': 0}]
            for dent in [agg, infra[0], infra[1]]
        }
    elif use_bridge:  # D-bridge
        bridge_config = {
            dent.host_name: [{'name': bridge, 'type': 'bridge'}]
            for dent in [agg, infra[0], infra[1]]
        }
    else:  # port
        bridge_config = {
            agg.host_name: [{'name': bridge, 'type': 'bridge'}]
        }
        # do not enslave ports
        del ip_link_config[infra[0].host_name][0]['master']
        del ip_link_config[infra[1].host_name][0]['master']
        # do not set bridge up
        del ip_link_config[infra[0].host_name][-1]
        del ip_link_config[infra[1].host_name][-1]

    if use_tgen:
        ip_link_config[agg.host_name].append({'device': tg_links[0][agg],
                                              'master': bridge, 'operstate': 'up'})
        ip_link_config[infra[1].host_name].append({'device': tg_links[1][infra[1]],
                                                   'operstate': 'up'})

    # Add bridges
    out = await IpLink.add(input_data=[bridge_config])
    assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
        'Failed to create bridges'

    # Enslave ports
    out = await IpLink.set(input_data=[ip_link_config])
    assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
        'Failed to enslave ports'

    # Add vlans and bridge vlan interfaces
    if use_vid is not None:
        agg_vlans = [
            {'device': links[0][agg], 'vid': use_vid},
            {'device': links[1][agg], 'vid': use_vid},
        ]
        if use_tgen:
            agg_vlans.append({'device': tg_links[0][agg], 'vid': use_vid,
                              'untagged': True, 'pvid': True})

        out = await BridgeVlan.add(input_data=[{
            agg.host_name: agg_vlans,
            infra[0].host_name: [{'device': links[0][infra[0]], 'vid': use_vid},
                                 {'device': bridge, 'vid': use_vid, 'self': True}],
            infra[1].host_name: [{'device': links[1][infra[1]], 'vid': use_vid},
                                 {'device': bridge, 'vid': use_vid, 'self': True}],
        }])
        assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
            'Failed to add vlans'

        vlan_dev = f'{bridge}.{use_vid}'
        out = await IpLink.add(input_data=[{
            dent.host_name: [{
                'name': vlan_dev,
                'link': bridge,
                'type': f'vlan id {use_vid}',
            }]
            for dent in infra
        }])
        assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
            'Failed to create bridge vlan devices'

        out = await IpLink.set(input_data=[{
            infra[0].host_name: [{'device': vlan_dev, 'operstate': 'up'}],
            infra[1].host_name: [{'device': vlan_dev, 'operstate': 'up'}],
        }])
        assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
            'Failed to set operstate'

        ip_addr_config = {
            infra[0].host_name: [{'dev': vlan_dev, 'prefix': '192.168.1.3/24'}],
            infra[1].host_name: [{'dev': vlan_dev, 'prefix': '192.168.1.4/24'}],
        }
    elif use_bridge:
        ip_addr_config = {
            infra[0].host_name: [{'dev': bridge, 'prefix': '192.168.1.3/24'}],
            infra[1].host_name: [{'dev': bridge, 'prefix': '192.168.1.4/24'}],
        }
    else:  # port
        ip_addr_config = {
            infra[0].host_name: [{'dev': links[0][infra[0]], 'prefix': '192.168.1.3/24'}],
            infra[1].host_name: [{'dev': links[1][infra[1]], 'prefix': '192.168.1.4/24'}],
        }

    # Add ip addrs
    if use_tgen:
        ip_addr_config[infra[1].host_name].append({'dev': tg_links[1][infra[1]], 'prefix': '192.168.2.1/24'})
    else:
        ip_addr_config[agg.host_name] = [{'dev': bridge, 'prefix': ep_ip}]

    ip_addr_config[infra[0].host_name].append({'dev': links[2][infra[0]], 'prefix': '192.168.3.10/24'})
    ip_addr_config[infra[1].host_name].append({'dev': links[2][infra[1]], 'prefix': '192.168.3.11/24'})

    out = await IpAddress.add(input_data=[ip_addr_config])
    assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
        'Failed to add IP addr'

    # Configure TGen
    if use_tgen:
        tgen_ports = [tg_links[0][tgen_dev], tg_links[1][tgen_dev]]
        dut_ports = [tg_links[0][agg], tg_links[1][infra[1]]]

        dev_groups = tgen_utils_dev_groups_from_config([
            {'ixp': tgen_ports[0], 'ip': ep_ip.split('/')[0], 'gw': vrrp_ip, 'plen': ep_ip.split('/')[1]},
            {'ixp': tgen_ports[1], 'ip': '192.168.2.2', 'gw': '192.168.2.1', 'plen': 24},
        ])
        await tgen_utils_traffic_generator_connect(tgen_dev, tgen_ports, dut_ports, dev_groups)

        # Add route to TG L1 from infra[0] via infra[1] L2
        out = await IpRoute.add(input_data=[{
            infra[0].host_name: [
                {'dst': dev_groups[tg_links[1][tgen_dev]][0]['ip'],
                 'nexthop': [{'via': '192.168.3.11'}]}
            ],
        }])
        assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
            'Failed to add route from infra[0] to TG L1 via infra[1]'

        # FIXME
        # Add static arp because for some reason the neighbor is aged and becomes
        # invalid which causes traffic loss
        out = await IpAddress.show(input_data=[{
            infra[1].host_name: [{'dev': links[2][infra[1]], 'cmd_options': '-j'}]
        }], parse_output=True)
        assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
            'Failed to get infra1 mac addr'

        mac = out[0][infra[1].host_name]['parsed_output'][0]['address']
        out = await IpNeighbor.replace(input_data=[{
            infra[0].host_name: [
                {'dev': links[2][infra[0]], 'address': '192.168.3.11', 'lladdr': mac}
            ],
        }])
        assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
            'Failed to add static neighbor'

    return {
        'tgen_dev': tgen_dev,
        'infra': infra,
        'agg': agg,
        'bridge': bridge,
        'ep_ip': ep_ip,
        'links': links,
        'tg_links': tg_links,
        'dev_groups': dev_groups,
        'vlan_dev': vlan_dev,
    }


async def verify_vrrp_ping(agg, infra, ports, expected, dst=None, count=10, interval=0.1, do_ping=True):
    spinup_time = 1
    tcpdump = [
        asyncio.create_task(tb_device_tcpdump(dent, port, f'-n -c {count} "icmp && icmp[0] == 0"',
                                              count_only=True, timeout=interval*3 * count + spinup_time))
        for dent, port in zip(infra, ports)
    ]
    await asyncio.sleep(spinup_time)  # give tcpdump some time to start capturing packets

    if do_ping:
        rc = await tb_ping_device(agg, dst, dump=True, count=count, interval=interval)
        if all(exp_pkt == 0 for exp_pkt in expected):
            assert rc != 0, 'Did not expect pings to have a reply'
        else:
            assert rc == 0, 'Some pings did not reach their destination'

    captured = await asyncio.gather(*tcpdump)
    for dent, exp_pkt, actual_pkt in zip(infra, expected, captured):
        assert exp_pkt == actual_pkt, f'Expected {dent} to handle {exp_pkt} icmp packets'


async def get_rx_bps(dent, port, sleep_for=5):
    out = await Ethtool.show(input_data=[{dent: [
        {'devname': port, 'options': '-S'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0

    old_stats = int(out[0][dent]['parsed_output']['good_octets_received'])

    await asyncio.sleep(sleep_for)

    out = await Ethtool.show(input_data=[{dent: [
        {'devname': port, 'options': '-S'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0

    new_stats = int(out[0][dent]['parsed_output']['good_octets_received'])

    return (new_stats - old_stats) // sleep_for
