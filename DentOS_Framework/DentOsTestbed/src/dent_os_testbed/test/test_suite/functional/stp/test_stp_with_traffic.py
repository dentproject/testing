import asyncio
import pytest
from math import isclose

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.mstpctl.mstpctl import Mstpctl

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_get_traffic_stats,
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
async def test_stp_traffic_during_mode_change(testbed, version):
    """
    Test Name: test_stp_traffic_during_mode_change
    Test Suite: suite_functional_stp
    Test Overview: Verify Topology rebuild during mode changes – STP/RSTP
    Test Procedure:
    1. Create bridge entity with STP enabled
    2. Enslave port to the bridge
    3. Change the MAC addresses the bridge
    4. Set link up on all participant ports, bridge
    5. Create streams. Send traffic
    6. Verify port 2 state is blocking
    7. Verify traffic is forwarded to port 1 and that port 2 doesn't receive any traffic
    8. Randomly select between STP/RSTP modes
    """
    num_ports = 4
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], num_ports)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_device = dent_devices[0]
    dent = dent_device.host_name
    tg_ports = tgen_dev.links_dict[dent][0][:num_ports]
    ports = tgen_dev.links_dict[dent][1][:num_ports]
    bridge = 'br0'
    root_mac = get_rand_mac('00:44:XX:XX:XX:XX')
    rand_mac = get_rand_mac('22:4X:XX:XX:XX:XX')
    convergence_time_s = 40 if version == 'stp' else 20
    rate_bps = 300_000_000  # 300Mbps
    traffic = f'data traffic {ports[2]}'
    traffic_1 = f'data traffic {ports[3]}'
    tolerance = 0.05

    # 1. Create bridge entity with STP enabled
    out = await IpLink.add(input_data=[{dent: [
        {'device': bridge, 'type': 'bridge', 'stp_state': 1}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bridge'

    # 2. Enslave port to the bridge
    out = await IpLink.set(input_data=[{dent: [
        {'device': port,
         'master': bridge} for port in ports]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    # 3. Change the MAC addresses the bridge
    out = await IpLink.set(input_data=[{dent: [
        {'device': bridge,
         'address': '22:BB:4D:85:E7:098'}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to change MAC address'

    out = await Mstpctl.add(input_data=[{dent: [{'bridge': bridge}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bridge'

    out = await Mstpctl.set(input_data=[{dent: [
        {'parameter': 'forcevers', 'bridge': bridge, 'version': version}
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to enable stp/rstp'

    # 4. Set link up on all participant ports, bridge
    out = await IpLink.set(input_data=[{dent: [
        {'device': port,
         'operstate': 'up'} for port in ports]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set port state UP'

    out = await IpLink.set(input_data=[{dent: [
        {'device': bridge,
         'operstate': 'up'}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set bridge to state UP'

    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': f'1.1.1.{idx}', 'gw': '1.1.1.5', 'plen': 24}
        for idx, port in enumerate(tg_ports, start=1)
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    # 5. Setup streams
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
        traffic: {
            'type': 'ethernet',
            'ep_source': ports[2],
            'frame_rate_type': 'bps_rate',
            'srcMac': get_rand_mac('00:11:XX:XX:XX:XX'),
            'rate': rate_bps,
        },
        traffic_1: {
            'type': 'ethernet',
            'ep_source': ports[3],
            'frame_rate_type': 'bps_rate',
            'srcMac': get_rand_mac('00:22:XX:XX:XX:XX'),
            'rate': rate_bps,
        },
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)
    await tgen_utils_start_traffic(tgen_dev)
    # don't stop
    await asyncio.sleep(convergence_time_s)

    versions = ['rstp', 'stp'] if version == 'stp' else ['stp', 'rstp']
    for new_version in versions:
        # 6. Verify port 2 state is blocking
        out = await Mstpctl.show(input_data=[{dent: [
            {'parameter': 'portdetail',
             'bridge': bridge,
             'options': '-f json'}]}], parse_output=True)
        assert out[0][dent]['rc'] == 0, 'Failed to get port detail of '
        ports_state = [bond['state'] for bond in out[0][dent]['parsed_output']]
        assert 'discarding' == ports_state[1], 'Bridge  does not have a blocking port'
        await asyncio.sleep(convergence_time_s)

        # 7. Verify traffic is forwarded  and port 2 doesn't receive any traffic
        stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
        for row in stats.Rows:
            if row['Traffic Item'] not in [traffic, traffic_1] and row['Rx Port'] == tg_ports[1]:
                err_msg = f'Expected 0.0 got : {float(row["Rx Rate (Mbps)"])}'
                assert isclose(float(row['Rx Rate (Mbps)']), 0.0, abs_tol=tolerance), err_msg
            if row['Traffic Item'] in [traffic, traffic_1] and row['Rx Port'] != tg_ports[1]:
                err_msg = f'Expected 300 got : {float(row["Rx Rate (Mbps)"])}'
                assert isclose(float(row['Rx Rate (Mbps)']), 300, rel_tol=tolerance), err_msg

        # 8. Randomly select between STP/RSTP modes
        out = await Mstpctl.set(input_data=[{dent: [
            {'parameter': 'forcevers', 'bridge': bridge, 'version': new_version}
        ]}])
        assert out[0][dent]['rc'] == 0, 'Failed to enable stp/rstp'
        await asyncio.sleep(convergence_time_s)
