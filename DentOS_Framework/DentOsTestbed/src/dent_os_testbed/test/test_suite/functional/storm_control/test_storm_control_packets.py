import pytest
import asyncio

from dent_os_testbed.test.test_suite.functional.devlink.devlink_utils import get_sct_streams
from dent_os_testbed.utils.test_utils.cleanup_utils import cleanup_kbyte_per_sec_rate_value
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.test.test_suite.functional.storm_control.storm_control_utils import (
    devlink_rate_value,
    get_streams,
    verify_cpu_rate
)

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic
)

pytestmark = [
    pytest.mark.suite_functional_storm_control,
    pytest.mark.asyncio,
    pytest.mark.usefixtures('cleanup_tgen', 'cleanup_ip_addrs', 'define_bash_utils')
]


async def set_rates(kbyte_value_stream, ports, device_host_name):
    params = [
        {'port': ports[0], 'name': 'bc_kbyte_per_sec_rate', 'value': kbyte_value_stream},
        {'port': ports[0], 'name': 'unreg_mc_kbyte_per_sec_rate', 'value': kbyte_value_stream},
        {'port': ports[0], 'name': 'unk_uc_kbyte_per_sec_rate', 'value': kbyte_value_stream}
    ]
    for value in params:
        await devlink_rate_value(dev=f'pci/0000:01:00.0/{value["port"].replace("swp","")}',
                                 name=value['name'], value=value['value'],
                                 cmode='runtime', device_host_name=device_host_name, set=True, verify=True)


async def test_storm_control_packets(testbed):
    """
    Test Name: test_storm_control_packets
    Test Suite: suite_functional_storm_control
    Test Overview: Verify there is no effect of Storm Control on the CPU trap average rate.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Set entities swp1, swp2 UP state.
    2.  Configure ip address on ports.
    3.  Set up the streams.
    4.  Set the Storm Control rate limit lower than the default values of SCT profiles on tx port.
    5.  Transmit continues traffic by TG.
    6.  Verify for each stream that the rate is according to hardware specs
        and not according to Storm Control's rate configured.
    7.  Set the Storm Control rate limit higher than the default values of SCT profiles on tx port.
    8.  Transmit continues traffic by TG.
    9.  Verify for each stream that the rate is according to hardware specs
        and not according to Storm Control's rate configured.
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 15
    deviation = 0.10
    pkt_size = 150
    high_rate = 500
    low_rate = 90

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': port, 'operstate': 'up'} for port in ports]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that entities set to 'UP' state.\n{out}"

    out = await IpAddress.add(
        input_data=[{device_host_name: [
            {'dev': ports[0], 'prefix': '192.168.1.5/24', 'broadcast': '192.168.1.255'},
            {'dev': ports[1], 'prefix': '192.168.1.4/24', 'broadcast': '192.168.1.255'}]}])
    assert out[0][device_host_name]['rc'] == 0, f'Failed to add IP address to ports.\n{out}'

    # set a storm control rate limits
    kbyte_value_stream = [low_rate*pkt_size, high_rate*pkt_size]
    await set_rates(kbyte_value_stream[0], ports, device_host_name)

    try:
        address_map = (
            # swp port, tg port,    tg ip,          gw,           plen
            (ports[0], tg_ports[0], '192.168.1.6', '192.168.1.5', 24),
            (ports[1], tg_ports[1], '192.168.1.7', '192.168.1.4', 24)
        )

        dev_groups = tgen_utils_dev_groups_from_config(
            {'ixp': port, 'ip': ip, 'gw': gw, 'plen': plen}
            for _, port, ip, gw, plen in address_map
        )

        await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

        list_streams = await get_sct_streams(dent_dev, dev_groups, tg_ports[:2], ports[0])
        streams = get_streams(list_streams, ['stp', 'lacp', 'lldp', 'dhcp',
                                             'arp_bc', 'router_mc', 'ip_bc_mac', 'vrrp'])

        await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)
        await tgen_utils_start_traffic(tgen_dev)
        await asyncio.sleep(traffic_duration)
        await verify_cpu_rate(dent_dev, deviation)

        await tgen_utils_stop_traffic(tgen_dev)

        # change a storm control rate limits
        await set_rates(kbyte_value_stream[1], ports, device_host_name)

        await tgen_utils_start_traffic(tgen_dev)
        await asyncio.sleep(traffic_duration)
        await verify_cpu_rate(dent_dev, deviation)
    finally:
        await tgen_utils_stop_traffic(tgen_dev)
        await cleanup_kbyte_per_sec_rate_value(dent_dev, tgen_dev, all_values=True)
