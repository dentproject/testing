import pytest_asyncio

from dent_os_testbed.lib.ip.ip_route import IpRoute
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.os.sysctl import Sysctl

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
)


@pytest_asyncio.fixture()
async def enable_ipv4_forwarding(testbed):
    _, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 0)
    dent_host_name = [dent.host_name for dent in dent_devices]
    ip_forward = 'net.ipv4.ip_forward'

    # Get ip_forward to restore it later
    out = await Sysctl.get(input_data=[{dent: [
        {'variable': ip_forward, 'options': '-n'}
    ]} for dent in dent_host_name])
    assert all(res[host_name]['rc'] == 0 for res in out for host_name in res)
    default_value = {
        host_name: int(res[host_name]['result'])
        for res in out for host_name in res
    }

    # Enable ipv4 forwarding
    out = await Sysctl.set(input_data=[{dent: [
        {'variable': ip_forward, 'value': 1}
    ]} for dent in dent_host_name])
    assert all(res[host_name]['rc'] == 0 for res in out for host_name in res)

    yield  # Run the test

    # Restore original value
    out = await Sysctl.set(input_data=[{dent: [
        {'variable': ip_forward, 'value': value}
    ]} for dent, value in default_value.items()])


@pytest_asyncio.fixture()
async def remove_default_gateway(testbed):
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print('The testbed does not have enough dent with tgen connections')
        return
    dent = dent_devices[0].host_name

    out = await IpRoute.show(input_data=[{dent: [
        {'cmd_options': '-j -4'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get list of IPv4 route entries'
    # save default route to restore it later
    def_routes = [route for route in out[0][dent]['parsed_output'] if route['dst'] == 'default']

    out = await IpRoute.show(input_data=[{dent: [
        {'cmd_options': '-j -6'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get list of IPv6 route entries'
    # save default route to restore it later
    def_routes += [route for route in out[0][dent]['parsed_output'] if route['dst'] == 'default']

    out = await IpRoute.delete(input_data=[{dent: [
        {'dev': route['dev'], 'type': 'default', 'via': route['gateway']}
        for route in def_routes
    ]}])
    assert out[0][dent]['rc'] == 0, 'Failed to remove default route'

    yield  # Run the test

    out = await IpRoute.show(input_data=[{dent: [
        {'cmd_options': '-j -4'}
    ]}], parse_output=True)
    default_routes = [route for route in out[0][dent]['parsed_output'] if route['dst'] == 'default']

    out = await IpRoute.show(input_data=[{dent: [
        {'cmd_options': '-j -6'}
    ]}], parse_output=True)
    default_routes += [route for route in out[0][dent]['parsed_output'] if route['dst'] == 'default']

    if default_routes:
        # Remove non-default gateways
        out = await IpRoute.delete(input_data=[{dent: [
            {'dev': route['dev'], 'type': 'default', 'via': route['gateway']}
            for route in default_routes
        ]}])

    # Restore default gateway
    out = await IpRoute.replace(input_data=[{dent: [
        {'dev': route['dev'], 'type': 'default', 'via': route['gateway']}
        for route in def_routes
    ]}])


@pytest_asyncio.fixture()
async def cleanup_mtu(testbed):
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print('The testbed does not have enough dent with tgen connections')
        return
    dent = dent_devices[0].host_name
    ports = tgen_dev.links_dict[dent][1]

    # Get current mtu to restore it later
    out = await IpLink.show(input_data=[{dent: [
        {'cmd_options': '-j'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get ports'

    def_mtu_map = [link for link in out[0][dent]['parsed_output'] if link['ifname'] in ports]

    yield  # Run the test

    # Restore old mtu
    out = await IpLink.set(input_data=[{dent: [
        {'device': link['ifname'], 'mtu': link['mtu']} for link in def_mtu_map
    ]}])
