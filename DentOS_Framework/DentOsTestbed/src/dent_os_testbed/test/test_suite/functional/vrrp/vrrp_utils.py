import asyncio
import pytest

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_address import IpAddress

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
)

from dent_os_testbed.utils.test_utils.tb_utils import (
    tb_device_tcpdump,
    tb_ping_device,
)


async def setup_topo_for_vrrp(testbed, use_bridge=False):
    """
    Setup:
            agg
         ___| |___
      L0 |       | L1
         |       |
    infra[0]    infra[1]

    Configure:
        agg:
            L0 and L1: master bridge
            bridge: ip address 192.168.1.5/24
        infra[0]:
            L0 (port/bridge): ip address 192.168.1.3/24
        infra[1]:
            L1 (port/bridge): ip address 192.168.1.4/24
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

    bridge = 'br0'
    ep_ip = '192.168.1.5/24'
    links = [
        # L0
        {infra[0]: infra[0].links_dict[agg.host_name][0][0],
         agg: infra[0].links_dict[agg.host_name][1][0]},
        # L1
        {infra[1]: infra[1].links_dict[agg.host_name][0][0],
         agg: infra[1].links_dict[agg.host_name][1][0]},
    ]

    # 1. Configure aggregation router
    out = await IpLink.add(input_data=[{agg.host_name: [
        {'name': bridge, 'type': 'bridge'}
    ]}])
    assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
        'Failed to create bridge'

    out = await IpLink.set(input_data=[{
        agg.host_name: [
            {'device': port, 'master': bridge, 'operstate': 'up'}
            for port in [links[0][agg], links[1][agg]]
        ] + [
            {'device': bridge, 'operstate': 'up'}
        ]
    }])
    assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
        'Failed to enslave ports'

    # 2. Configure infra devices
    if use_bridge:
        out = await IpLink.add(input_data=[{
            dent.host_name: [{'name': bridge, 'type': 'bridge'}]
            for dent in infra
        }])
        assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
            'Failed to create bridge'

        out = await IpLink.set(input_data=[{
            infra[0].host_name: [
                {'device': links[0][infra[0]], 'operstate': 'up', 'master': bridge},
                {'device': bridge, 'operstate': 'up'},
            ],
            infra[1].host_name: [
                {'device': links[1][infra[1]], 'operstate': 'up', 'master': bridge},
                {'device': bridge, 'operstate': 'up'},
            ],
        }])
        assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
            'Failed to enslave ports'

        out = await IpAddress.add(input_data=[{
            infra[0].host_name: [{'dev': bridge, 'prefix': '192.168.1.3/24'}],
            infra[1].host_name: [{'dev': bridge, 'prefix': '192.168.1.4/24'}],
            agg.host_name: [{'dev': bridge, 'prefix': ep_ip}],
        }])
        assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
            'Failed to add IP addr'
    else:  # port
        out = await IpLink.set(input_data=[{
            infra[0].host_name: [{'device': links[0][infra[0]], 'operstate': 'up'}],
            infra[1].host_name: [{'device': links[1][infra[1]], 'operstate': 'up'}],
        }])
        assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
            'Failed to set operstate to UP'

        out = await IpAddress.add(input_data=[{
            infra[0].host_name: [{'dev': links[0][infra[0]], 'prefix': '192.168.1.3/24'}],
            infra[1].host_name: [{'dev': links[1][infra[1]], 'prefix': '192.168.1.4/24'}],
            agg.host_name: [{'dev': bridge, 'prefix': ep_ip}],
        }])
        assert all(res[host_name]['rc'] == 0 for res in out for host_name in res), \
            'Failed to add IP addr'

    return {
        'tgen_dev': tgen_dev,
        'infra': infra,
        'agg': agg,
        'bridge': bridge,
        'ep_ip': ep_ip,
        'links': links,
    }


async def verify_vrrp_ping(agg, infra, ports, expected, dst, count=10):
    interval = 0.1
    tcpdump = [
        # capture 2x number of sent icmp packets (request + reply)
        asyncio.create_task(tb_device_tcpdump(dent, port, f'-n -c {count*2} icmp',
                                              count_only=True, timeout=interval*5 * count))
        for dent, port in zip(infra, ports)
    ]
    await asyncio.sleep(1)  # give tcpdump some time to start capturing packets

    rc = await tb_ping_device(agg, dst, dump=True, count=count, interval=interval)
    if all(exp_pkt == 0 for exp_pkt in expected):
        assert rc != 0, 'Did not expect pings to have a reply'
    else:
        assert rc == 0, 'Some pings did not reach their destination'

    captured = await asyncio.gather(*tcpdump)
    for dent, exp_pkt, actual_pkt in zip(infra, expected, captured):
        assert exp_pkt == actual_pkt, f'Expected {dent} to handle {exp_pkt} icmp packets'
