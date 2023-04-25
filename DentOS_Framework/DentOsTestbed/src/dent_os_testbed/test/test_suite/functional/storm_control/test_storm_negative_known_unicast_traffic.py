import pytest
import asyncio

from dent_os_testbed.test.test_suite.functional.storm_control.storm_control_utils import devlink_rate_value
from dent_os_testbed.utils.test_utils.cleanup_utils import cleanup_kbyte_per_sec_rate_value
from dent_os_testbed.lib.bridge.bridge_fdb import BridgeFdb
from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_clear_traffic_stats,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_get_loss
)

pytestmark = [
    pytest.mark.suite_functional_storm_control,
    pytest.mark.asyncio,
    pytest.mark.usefixtures('cleanup_bridges', 'cleanup_tgen')
]


async def test_storm_negative_known_unicast_traffic(testbed):
    """
    Test Name: test_storm_negative_known_unicast_traffic
    Test Suite: suite_functional_storm_control
    Test Overview: Verify Known Unicast traffic is not limited by Storm Control.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1, swp2 master br0.
    3.  Set entities swp1, swp2 UP state.
    4.  Set bridge br0 admin state UP.
    5.  Add static mac entry (on the first TG port) to the bridge.
    6.  Set up the following stream:
        - unicast stream from the second TG port to the first TG port.
    7.  Set storm control rate limit rule for unicast traffic on TX port (first TG port)
    8.  Transmit traffic by TG.
    9.  Verify the RX rate on the RX port is as expected - the rate is not limited by storm control.
    10. Flush FDB.
    11. Verify the RX rate on the RX port is as expected - the rate is limited by storm control.
    """

    bridge = 'br0'
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 15
    pps_value = 1000

    out = await IpLink.add(
        input_data=[{device_host_name: [
            {'device': bridge, 'vlan_filtering': 1, 'type': 'bridge'}]}])
    err_msg = f"Verify that bridge created and vlan filtering set to 'ON'.\n{out}"
    assert out[0][device_host_name]['rc'] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': bridge, 'operstate': 'up'}]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that bridge set to 'UP' state.\n{out}"

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': port, 'master': bridge, 'operstate': 'up'} for port in ports]}])
    err_msg = f"Verify that bridge entities set to 'UP' state and links enslaved to bridge.\n{out}"
    assert out[0][device_host_name]['rc'] == 0, err_msg

    out = await BridgeFdb.add(
        input_data=[{device_host_name: [
            {'device': ports[0], 'lladdr': '68:16:3d:2e:b4:c8', 'master': True, 'static': True}]}])
    assert out[0][device_host_name]['rc'] == 0, f'Verify that FDB static entry added.\n{out}'

    await devlink_rate_value(dev=f'pci/0000:01:00.0/{ports[0].replace("swp","")}',
                             name='unk_uc_kbyte_per_sec_rate', value=0,
                             device_host_name=device_host_name, verify=True)
    await devlink_rate_value(dev=f'pci/0000:01:00.0/{ports[0].replace("swp","")}',
                             name='unk_uc_kbyte_per_sec_rate', value=93420,
                             cmode='runtime', device_host_name=device_host_name, set=True, verify=True)

    try:
        address_map = (
            # swp port, tg port,    tg ip,     gw,        plen
            (ports[0], tg_ports[0], '1.1.1.2', '1.1.1.1', 24),
            (ports[1], tg_ports[1], '1.1.1.3', '1.1.1.1', 24)
        )

        dev_groups = tgen_utils_dev_groups_from_config(
            {'ixp': port, 'ip': ip, 'gw': gw, 'plen': plen}
            for _, port, ip, gw, plen in address_map
        )

        await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

        """
        Set up the following stream:
        — stream_A —
        swp2 -> swp1
        """

        streams = {
            'stream_A': {
                'ip_source': dev_groups[tg_ports[1]][0]['name'],
                'ip_destination': dev_groups[tg_ports[0]][0]['name'],
                'srcIp': '4.218.149.95',
                'dstIp': '155.99.214.26',
                'srcMac': '6c:d5:aa:6f:2c:b7',
                'dstMac': '68:16:3d:2e:b4:c8',
                'frameSize': 458,
                'rate': pps_value,
                'protocol': '0x0800',
                'type': 'raw'
            }
        }

        await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)
        await tgen_utils_start_traffic(tgen_dev)

        for x in range(2):
            await asyncio.sleep(traffic_duration)

            # check the traffic stats
            stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
            for row in stats.Rows:
                loss = tgen_utils_get_loss(row)
                assert loss == 0, f'Expected loss: 0%, actual: {loss}%'
            if x == 0:
                out = await BridgeFdb.delete(
                    input_data=[{device_host_name: [
                        {'device': ports[0], 'lladdr': '68:16:3d:2e:b4:c8', 'master': True, 'static': True}]}])
                assert out[0][device_host_name]['rc'] == 0, f'Verify that FDB static entry deleted.\n{out}'
                await tgen_utils_clear_traffic_stats(tgen_dev)
    finally:
        await cleanup_kbyte_per_sec_rate_value(dent_dev, unk_uc=True)