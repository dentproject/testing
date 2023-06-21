from math import isclose as is_close
import asyncio
import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.mstpctl.mstpctl import Mstpctl

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
)

from dent_os_testbed.utils.test_utils.data.tgen_constants import (
    TRAFFIC_ITEM_NAME,
    RX_PORT,
    RX_RATE,
)

from dent_os_testbed.test.test_suite.functional.stp.stp_utils import (
    get_rand_mac,
    PortRole,
)


pytestmark = [
    pytest.mark.suite_functional_stp,
    pytest.mark.usefixtures('cleanup_bridges', 'cleanup_tgen', 'enable_mstpd'),
    pytest.mark.asyncio,
]


@pytest.mark.parametrize('version', ['stp', 'rstp'])
async def test_stp_bpdu_filter(testbed, version):
    """
    Test Name: test_stp_bpdu_filter
    Test Suite: suite_functional_stp
    Test Overview: Verify BDPU filter basic functionality works as expected
    Test Procedure:
    1. Add bridge
    2. Enslave ports
    3. Enable STP/RSTP
    4. Setup streams:
       - BPDU stream with higher prio than bridge from port#0
       - BPDU stream with higher prio than bridge from port#1
       - data traffic from port#2 to ports #0 and #1
    5. Send traffic
    6. Disable/Enable BPDU filter
    7. Verify port#1 is ALTERNATE/DESIGNATED
    8. Verify traffic is discarded/forwarded through port#1
    """
    num_ports = 3
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], num_ports)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_device = dent_devices[0]
    dent = dent_device.host_name
    tg_ports = tgen_dev.links_dict[dent][0][:num_ports]
    ports = tgen_dev.links_dict[dent][1][:num_ports]
    bridge = 'br0'
    bridge_mac = get_rand_mac('02:55:XX:XX:XX:XX')
    root_mac = get_rand_mac('02:10:XX:XX:XX:XX')
    rand_mac = get_rand_mac('02:AA:XX:XX:XX:XX')
    convergence_time_s = 40 if version == 'stp' else 20
    rate_bps = 300_000_000  # 300Mbps
    traffic = 'data traffic'
    tolerance = 0.05

    # 1. Add bridge
    out = await IpLink.add(input_data=[{dent: [
        {'device': bridge, 'type': 'bridge', 'stp_state': 1}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bridge'

    # 2. Enslave ports
    out = await IpLink.set(input_data=[{dent: [
        {'device': port, 'operstate': 'up', 'master': bridge}
        for port in ports
    ] + [
        {'device': bridge, 'operstate': 'up', 'address': bridge_mac}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # 3. Enable STP/RSTP
    out = await Mstpctl.add(input_data=[{dent: [{'bridge': bridge}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bridge'

    out = await Mstpctl.set(input_data=[{dent: [
        {'parameter': 'forcevers', 'bridge': bridge, 'version': version}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to enable stp/rstp'

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': f'1.1.1.{idx}', 'gw': '1.1.1.5', 'plen': 24}
        for idx, port in enumerate(tg_ports, start=1)
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    # 4. Setup streams
    stp = {
        'rootIdentifier': f'8000{root_mac.replace(":", "")}',
        'bridgeIdentifier': f'8000{root_mac.replace(":", "")}',
        'portIdentifier': '8002',
        'messageAge': 1 << 8,
        'frameSize': 100,
    }
    rstp = {
        'agreement': 1,
        'forwarding': 1,
        'learning': 1,
        'portRole': PortRole.DESIGNATED.value,
        'proposal': 1,
        'protocol': '0027',
    } if version == 'rstp' else {}
    streams = {
        # BPDU stream with higher prio than bridge from port#0
        f'{ports[0]} {version}': {
            'type': 'bpdu',
            'version': version,
            'ep_source': ports[0],
            'ep_destination': ports[0],
            'rate': 1,  # pps
            'allowSelfDestined': True,
            'srcMac': root_mac,
            **stp,
            **rstp,
        },
        # BPDU stream with higher prio than bridge from port#1
        f'{ports[1]} {version}': {
            'type': 'bpdu',
            'version': version,
            'ep_source': ports[1],
            'ep_destination': ports[1],
            'rate': 1,  # pps
            'allowSelfDestined': True,
            'srcMac': rand_mac,
            **stp,
            **rstp,
            'bridgeIdentifier': f'8000{rand_mac.replace(":", "")}',
        },
        # data traffic from port#2 to ports #0 and #1
        traffic: {
            'type': 'ethernet',
            'ep_source': ports[2],
            'frame_rate_type': 'bps_rate',
            'rate': rate_bps,
        },
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # 5. Send traffic
    await tgen_utils_start_traffic(tgen_dev)
    # don't stop

    config = [
        (False,
         [rate_bps, 0],
         {ports[0]: {'role': PortRole.ROOT, 'state': 'forwarding'},
          ports[1]: {'role': PortRole.ALTERNATE, 'state': 'discarding'},
          ports[2]: {'role': PortRole.DESIGNATED, 'state': 'forwarding'}}),
        (True,
         [rate_bps, rate_bps],
         {ports[0]: {'role': PortRole.ROOT, 'state': 'forwarding'},
          ports[1]: {'role': PortRole.DESIGNATED, 'state': 'forwarding'},
          ports[2]: {'role': PortRole.DESIGNATED, 'state': 'forwarding'}}),
    ]
    for enable_filter, exp_rate, stp_state in [config[0], config[1], config[0]]:
        # 6. Disable/Enable BPDU filter
        out = await Mstpctl.set(input_data=[{dent: [
            {'parameter': 'portbpdufilter',
             'bridge': bridge,
             'port': ports[1],
             'enable': enable_filter}
        ]}])
        assert out[0][dent]['rc'] == 0, 'Failed to enable bpdu filter'

        dent_device.applog.info(f'Waiting {convergence_time_s}s for topo convergence')
        await asyncio.sleep(convergence_time_s)

        # 7. Verify port#1 is ALTERNATE/DESIGNATED
        out = await Mstpctl.show(input_data=[{dent: [
            {'parameter': 'portdetail', 'bridge': bridge, 'options': '-f json'}
        ]}], parse_output=True)
        assert out[0][dent]['rc'] == 0, 'Failed to get port detail'

        for info in out[0][dent]['parsed_output']:
            dev = info['port']
            role = stp_state[dev]['role'].name
            state = stp_state[dev]['state']
            assert info['role'].upper() == role, f'Expected port {dev} role to be \'{role}\''
            assert info['state'] == state, f'Expected port {dev} state to be \'{state}\''

        # 8. Verify traffic is discarded/forwarded through port#1
        stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
        for row in stats.Rows:
            if row[TRAFFIC_ITEM_NAME] != traffic:
                continue
            expected = exp_rate[row[RX_PORT] == tg_ports[1]]
            actual = float(row[RX_RATE])
            dent_device.applog.info(f'Expected rate {expected // 10**6}Mbps, actual {actual // 10**6}Mbps, '
                                    f'rx port {row[RX_PORT]}')
            assert is_close(expected, actual, rel_tol=tolerance), \
                f'Expected rate {expected}, but actual is {row[RX_RATE]} ({row[TRAFFIC_ITEM_NAME]} => {row[RX_PORT]})'
