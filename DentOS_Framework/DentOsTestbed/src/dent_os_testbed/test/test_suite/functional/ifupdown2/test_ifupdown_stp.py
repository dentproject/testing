import asyncio
import pytest
from math import isclose

from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_setup_streams,
    tgen_utils_get_traffic_stats,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic
)

from dent_os_testbed.test.test_suite.functional.stp.stp_utils import (
    get_rand_mac,
    PortRole,
)

from dent_os_testbed.test.test_suite.functional.ifupdown2.ifupdown2_utils import (
    INTERFACES_FILE,
    reboot_and_wait,
    write_reload_check_ifupdown_config,
    config_bridge_temp, check_member_devices,
    verify_ifupdown_config,
)

pytestmark = [
    pytest.mark.suite_functional_ifupdown2,
    pytest.mark.asyncio,
]


@pytest.mark.parametrize('version', ['stp', 'rstp'])
async def test_ifupdown2_stp(testbed, modify_ifupdown_conf, version):
    """
    Test Name: test_ifupdown2_stp
    Test Suite: suite_functional_ifupdown2
    Test Overview: Test ifupdown2 with Bridge device and tagged/untagged traffic
    Test Procedure:
    1. Prepare ifupdown2 environment config
    2. Prepare ifupdown2 config: Add Bridge device, enable stp, add  bridge mac
    3. Verify no errors in ifupdown2 config, apply config, compare running ifupdown2 config vs default config
    4. Verify that bridge device added with 4 member ports and expected bridge mac address
    5. Verify MAC address of the bridge is as set by ifupdown2 configuration
    6. Verify STP is running on the correct space
    7. Init interfaces and connect devices
    8. Setup streams
    9. Transmit streams
    10. Verify expected blocking port is in blocking state
    11. Verify traffic is forwarded  and port 2 doesn't receive any traffic
    12. Reboot DUT
    13. Compare running ifupdown2 config vs default config
    14. Transmit streams
    15. Verify traffic is forwarded  and port 2 doesn't receive any traffic
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dev_name = dent_devices[0].host_name
    dent_dev = dent_devices[0]
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]
    traffic_duration = 40
    bridge = 'br0'
    full_config = ''
    root_mac = get_rand_mac('00:00:XX:XX:XX:XX')
    rand_mac = get_rand_mac('00:02:XX:XX:XX:XX')
    rate_bps = 300_000_000  # 300Mbps
    traffic = 'L2 traffic'
    # Forcebly select kernal userspace beforehand
    rc, out = await dent_dev.run_cmd("sed -i \"/^[#]*MANAGE_MSTPD=/ cMANAGE_MSTPD='n'\" /etc/bridge-stp.conf")
    assert rc == 0, 'Failed to edit bridge-stp.conf'

    # 1.Prepare ifupdown2 environment config
    config = {'template_lookuppath': '/etc/network/ifupdown2/templates',
              'addon_syntax_check': 1,
              'default_interfaces_configfile': INTERFACES_FILE
              }
    rc = await modify_ifupdown_conf(dent_dev, config)
    assert not rc, 'Failed to prepare ifupdown2 enviroment config'

    # Set the space (user/kernel) according to the STP mode (kernel for STP, userspace for RSTP)
    if version == 'stp':
        rc, _ = await dent_dev.run_cmd('if [ ! -z "$(pidof mstpd)" ]; then killall mstpd; fi')
        assert rc == 0, 'Failed to execute cmd'

    else:
        rc, _ = await dent_dev.run_cmd('mstpd')
        rc, out = await dent_dev.run_cmd("sed -i \"/^[#]*MANAGE_MSTPD=/ cMANAGE_MSTPD='y'\" /etc/bridge-stp.conf")

        assert rc == 0, 'Failed to execute cmd'

    # 2.Prepare ifupdown2 config: Add Bridge device, enable stp, add  bridge mac
    bridge_addr = get_rand_mac('22:XX:XX:XX:XX:XX')
    full_config += config_bridge_temp(bridge, dut_ports, stp=True, hwaddress=bridge_addr)

    # 3.Verify no errors in ifupdown2 config, apply config, compare running ifupdown2 config vs default config
    await write_reload_check_ifupdown_config(dent_dev, full_config, config['default_interfaces_configfile'])

    # 4.Verify that bridge device added with 4 member ports and expected bridge mac address
    # 5.Verify MAC address of the bridge is as set by ifupdown2 configuration
    out = await IpLink.show(input_data=[{dev_name: [
        {'device': bridge,
         'cmd_options': '-j -d'}]}], parse_output=True)
    assert out[0][dev_name]['rc'] == 0, 'Failed to get port detail'
    err_msg = f'Address of bridge is not as expected {bridge_addr}'
    assert out[0][dev_name]['parsed_output'][0]['address'] == bridge_addr, err_msg

    await asyncio.sleep(40)  # Sleep some time for ports to get UP
    await check_member_devices(dev_name, {bridge: dut_ports})

    # 6. Verify STP is running on the correct space
    # 6. Verify STP is running on the correct space
    out = await IpLink.show(input_data=[{dev_name: [
        {'device': bridge,
         'cmd_options': '-j -d'}]}], parse_output=True)
    assert out[0][dev_name]['rc'] == 0, 'Failed to get bridge detail'
    space_id = out[0][dev_name]['parsed_output'][0]['linkinfo']['info_data']['stp_state']
    err_msg = f'Version: {version} should run on {"Kernal" if version == "stp" else "USER"} space'
    if version == 'rstp':
        assert space_id == 2, err_msg
    else:
        assert space_id == 1, err_msg
    # 7.Init interfaces and connect devices
    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': f'1.1.1.{idx}', 'gw': '1.1.1.5', 'plen': 24}
        for idx, port in enumerate(tg_ports, start=1)
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    # 8.Setup streams
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
        f'{tg_ports[0]} {version}': {
            'type': 'bpdu',
            'version': version,
            'ep_source': dut_ports[0],
            'ep_destination': dut_ports[0],
            'rate': 1,  # pps
            'allowSelfDestined': True,
            'srcMac': root_mac,
            **stp,
            **rstp,
        },
        f'{tg_ports[1]} {version}': {
            'type': 'bpdu',
            'version': version,
            'ep_source': dut_ports[1],
            'ep_destination': dut_ports[1],
            'rate': 1,  # pps
            'allowSelfDestined': True,
            'srcMac': rand_mac,
            **stp,
            **rstp,
            'bridgeIdentifier': f'8000{rand_mac.replace(":", "")}',
        },
        traffic: {
            'type': 'ethernet',
            'ep_source': dut_ports[2],
            'frame_rate_type': 'bps_rate',
            'srcMac': get_rand_mac('44:XX:XX:XX:XX:XX'),
            'rate': rate_bps,
        }
    }
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    # 9.Transmit streams
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)

    # 10. Verify expected blocking port is in blocking state
    out = await IpLink.show(input_data=[{dev_name: [
        {'device': dut_ports[1],
         'cmd_options': '-j -d'}]}], parse_output=True)
    assert out[0][dev_name]['rc'] == 0, 'Failed to get port detail'
    err_msg = f'Port : {dut_ports[1]} has to be in forwarding state'
    assert out[0][dev_name]['parsed_output'][0]['linkinfo']['info_slave_data']['state'] == 'blocking', err_msg

    await asyncio.sleep(20)

    # 11. Verify traffic is forwarded  and port 2 doesn't receive any traffic
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        if row['Traffic Item'] == traffic and row['Rx Port'] == tg_ports[1]:
            err_msg = f'Expected 0.0 got : {float(row["Rx Rate (Mbps)"])}'
            assert isclose(float(row['Rx Rate (Mbps)']), 0.0, abs_tol=0.1), err_msg
        if row['Traffic Item'] == traffic and row['Rx Port'] in [tg_ports[0], tg_ports[3]]:
            err_msg = f'Expected 300 got : {float(row["Rx Rate (Mbps)"])}'
            assert isclose(float(row['Rx Rate (Mbps)']), 300, rel_tol=0.1), err_msg

    await tgen_utils_stop_traffic(tgen_dev)
    # 12.Reboot DUT
    await reboot_and_wait(dent_dev)

    # 13.Compare running ifupdown2 config vs default config
    await verify_ifupdown_config(dent_dev, config['default_interfaces_configfile'])

    # 14.Transmit streams
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)

    # 15.Verify traffic is forwarded  and port 2 doesn't receive any traffic
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        if row['Traffic Item'] == traffic and row['Rx Port'] == tg_ports[1]:
            err_msg = f'Expected 0.0 got : {float(row["Rx Rate (Mbps)"])}'
            assert isclose(float(row['Rx Rate (Mbps)']), 0.0, abs_tol=0.1), err_msg
        if row['Traffic Item'] == traffic and row['Rx Port'] in [tg_ports[0], tg_ports[3]]:
            err_msg = f'Expected 300 got : {float(row["Rx Rate (Mbps)"])}'
            assert isclose(float(row['Rx Rate (Mbps)']), 300, rel_tol=0.1), err_msg
