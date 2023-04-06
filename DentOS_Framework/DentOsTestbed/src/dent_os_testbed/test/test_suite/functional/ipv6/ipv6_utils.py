from dent_os_testbed.lib.ip.ip_route import IpRoute
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.ip.ip_neighbor import IpNeighbor


async def verify_dut_routes(dent, expected_routes):
    out = await IpRoute.show(input_data=[{dent: [
        {'cmd_options': '-j -6'},
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get IPv6 routes'

    for route in out[0][dent]['parsed_output']:
        dev = route['dev']
        if dev not in expected_routes:
            continue
        if route['dst'].startswith('f'):  # broadcast
            continue
        assert 'rt_trap' in route['flags'], 'Route should be offloaded'
        assert route['dst'] in expected_routes[dev], \
            f"Expected route to be one of {expected_routes[dev]}, not {route['dst']}"


async def verify_dut_neighbors(dent, expected_neis):
    out = await IpNeighbor.show(input_data=[{dent: [
        {'cmd_options': '-j -6'},
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get IPv6 neighbors'

    learned_macs = {}
    for nei in out[0][dent]['parsed_output']:
        dev = nei['dev']
        if dev not in expected_neis:
            continue
        if nei['dst'].startswith('f'):  # broadcast
            continue
        assert nei['dst'] in expected_neis[dev], \
            f"Expected neighbor to be one of {expected_neis[dev]}, not {nei['dst']}"
        assert 'offload' in nei, 'Neighbor should be offloaded'
        assert nei['state'] != 'FAILED', 'Unexpected neighbor state'
        if dev not in learned_macs:
            learned_macs[dev] = []
        learned_macs[dev].append(nei['lladdr'])
    return learned_macs


async def verify_dut_addrs(dent, expected_addrs, plen=64):
    out = await IpAddress.show(input_data=[{dent: [
        {'cmd_options': '-j'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to add IP addr to port'

    for link in out[0][dent]['parsed_output']:
        dev = link['ifname']
        if dev not in expected_addrs:
            continue
        for addr in link['addr_info']:
            ip = addr['local']
            assert addr['family'] == 'inet6', 'Expected only IPv6 addresses'
            if ip.startswith('f'):  # broadcast
                continue
            assert int(addr['prefixlen']) == plen, f'Expected prefix to be {plen}'
            assert ip in expected_addrs[dev], \
                f'Expected IP addr to be one of {expected_addrs[dev]}, not {ip}'
