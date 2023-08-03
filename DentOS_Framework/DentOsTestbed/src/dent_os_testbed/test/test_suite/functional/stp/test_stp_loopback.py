import asyncio
import pytest
from math import isclose

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.mstpctl.mstpctl import Mstpctl

from dent_os_testbed.utils.test_utils.tgen_utils import (tgen_utils_get_dent_devices_with_tgen,
                                                         tgen_utils_setup_streams, tgen_utils_start_traffic,
                                                         tgen_utils_get_traffic_stats,
                                                         tgen_utils_dev_groups_from_config,
                                                         tgen_utils_traffic_generator_connect, )
pytestmark = [pytest.mark.suite_functional_stp,
              pytest.mark.asyncio,
              pytest.mark.usefixtures('cleanup_tgen', 'cleanup_bridges', 'enable_mstpd')]


@pytest.mark.parametrize('version', ['stp', 'rstp'])
async def test_stp_loopback_detection(testbed, version):
    """
    Test Name: STP/RSTP loopback detection
    Test Suite: suite_functional_stp
    Test Overview: Test stp/rstp loopback detection
    Test Procedure:
    1. Create bridge and set link up on them
    2. Enslave ports ot bridge
    4. Set link up on all participant ports, bridges
    5. Wait until topology converges
    6. Send broadcast traffic
    7. Verify device remain stable afterwards (during storming). Verify there is a storming
    8. Set bridge stp_state to 1
    9. Verify that afterwards all ports with the lowest number within a loopback connection are blocked.
    10. Verify that the rate on tgen ports is 0 (storming has stopped)
    """
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip(
            'The testbed does not have enough dent with tgen connections')
    device = dent_devices[0]
    dent = device.host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    dut_ixia_ports = tgen_dev.links_dict[dent][1]
    bridge = 'bridge_1'
    wait_time = 40 if version == 'stp' else 20
    loopback_ports = {}
    for idx, port in enumerate(device.links_dict[dent][0] + device.links_dict[dent][1]):
        loopback_ports[f'loopback_{idx+1}'] = port

    # 1. Create bridge entity
    out = await IpLink.add(input_data=[{dent: [{
        'device': bridge,
        'type': 'bridge',
        'stp_state': 0}]}])  # stp not enabled
    assert out[0][dent]['rc'] == 0, 'Failed to add bridge'

    # 2. Enslave ports according to the test's setup topology
    out = await IpLink.set(input_data=[
        {dent: [{'device': port, 'operstate': 'down'} for port in dut_ixia_ports] +
               [{'device': port, 'operstate': 'down'} for port in loopback_ports.values()] +
               [{'device': bridge, 'operstate': 'down'}]
         }])
    assert out[0][dent]['rc'] == 0, 'Failed changing state of the interfaces to down'

    out = await IpLink.set(input_data=[
        {dent:
            [{'device': port, 'master': bridge} for port in dut_ixia_ports] +
            [{'device': port, 'master': bridge} for port in loopback_ports.values()]

         }])
    assert out[0][dent]['rc'] == 0, 'Failed to enslave ports'

    # 4. Set link up on all participant ports, bridges
    out = await IpLink.set(input_data=[
        {dent: [{'device': port, 'operstate': 'up'} for port in dut_ixia_ports] +
               [{'device': port, 'operstate': 'up'} for port in loopback_ports.values()] +
               [{'device': bridge, 'operstate': 'up'}]
         }])
    assert out[0][dent]['rc'] == 0, 'Failed changing state of the interfaces'

    # 5. Wait until topology converges
    await asyncio.sleep(wait_time)

    # 6. Send broadcast traffic
    dev_groups = tgen_utils_dev_groups_from_config((
        {'ixp': tg_ports[0], 'ip': '1.1.1.2', 'gw': '1.1.1.1', 'plen': 24},
        {'ixp': tg_ports[1], 'ip': '1.1.1.3', 'gw': '1.1.1.1', 'plen': 24},
        {'ixp': tg_ports[2], 'ip': '1.1.1.4', 'gw': '1.1.1.1', 'plen': 24},
        {'ixp': tg_ports[3], 'ip': '1.1.1.5', 'gw': '1.1.1.1', 'plen': 24},

    ))
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ixia_ports, dev_groups)
    tx_ports = dev_groups[tg_ports[0]][0]['name']
    rx_ports = [dev_groups[tg_ports[1]][0]['name'],
                dev_groups[tg_ports[2]][0]['name'],
                dev_groups[tg_ports[3]][0]['name']]
    streams = {
        f'{rx_ports} -> Broadcast': {
            'type': 'raw',
            'ip_source': tx_ports,
            'ip_destination': rx_ports,
            'srcMac': 'aa:bb:cc:dd:ee:ff',
            'dstMac': 'ff:ff:ff:ff:ff:ff',
            'frame_rate_type': 'line_rate',
            'rate': 5
        }
    }

    await tgen_utils_setup_streams(tgen_dev, None, streams)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(wait_time)

    # 7. Verify device remain stable afterwards (during storming).
    rc, out = await device.run_cmd("echo 'Hello World'")
    assert rc == 0, 'FAIL: DUT crashed due to storming'
    assert out.strip() == 'Hello World', f'Expected <Hello World> got {out}'

    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Port Statistics')
    # Verify there is storming
    for row in stats.Rows:
        if row['Port Name'] == tg_ports[0]:
            err_msg = f'Expected 1400 got : {float(row["Rx. Rate (Mbps)"])}'
            assert float(row['Rx. Rate (Mbps)']) > 1400, err_msg

    # 8. Set bridge stp_state to 1.
    out = await IpLink.set(input_data=[{dent: [{
        'device': bridge,
        'type': 'bridge',
        'stp_state': 1}]}])  # stp enabled
    assert out[0][dent]['rc'] == 0, 'Failed to enable stp on bridge'
    out = await Mstpctl.add(input_data=[{dent: [{'bridge': bridge}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bridge with mstpd'
    out = await Mstpctl.set(input_data=[{dent: [{
        'bridge': bridge,
        'parameter': 'forcevers',
        'version': version}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set stp/rstp version'
    await asyncio.sleep(wait_time)

    out = await Mstpctl.add(input_data=[{dent: [{'bridge': bridge}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to add bridge with mstpd'
    out = await Mstpctl.set(input_data=[{dent: [{
        'bridge': bridge,
        'parameter': 'forcevers',
        'version': version}]}])
    assert out[0][dent]['rc'] == 0, 'Failed to set stp/rstp version'
    out = await Mstpctl.show(input_data=[{dent: [
        {'parameter': 'portdetail',
         'bridge': bridge,
         'options': '-f json'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, f'Failed to get port detail of {bridge}'

    # 9. Verify that afterwards all ports with the lowest number within a loopback connection are blocked.
    for dev in out[0][dent]['parsed_output']:
        if dev['port'] in list(loopback_ports.values())[3:]:
            assert dev['state'] == 'discarding'
    await asyncio.sleep(wait_time)

    # 10. Verify that the rate on Ixia ports is 0 (storming has stopped)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Port Statistics')
    for row in stats.Rows:
        if row['Port Name'] == tg_ports[0]:
            err_msg = f'Expected 0 got : {float(row["Rx. Rate (Mbps)"])}'
            assert isclose(float(row['Rx. Rate (Mbps)']), 0.00, abs_tol=0.1), err_msg
