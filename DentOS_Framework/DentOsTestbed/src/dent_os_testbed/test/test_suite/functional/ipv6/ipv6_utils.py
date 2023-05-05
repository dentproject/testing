from dent_os_testbed.lib.ip.ip_route import IpRoute
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.ip.ip_neighbor import IpNeighbor


async def verify_dut_routes(dent, expected_routes):
    out = await IpRoute.show(input_data=[{dent: [
        {'cmd_options': '-j -4'},
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get IPv4 routes'
    routes = out[0][dent]['parsed_output']

    out = await IpRoute.show(input_data=[{dent: [
        {'cmd_options': '-j -6'},
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get IPv6 routes'
    routes += out[0][dent]['parsed_output']

    for expected_route in expected_routes:
        for route in routes:
            if not all(expected_route[key] == route.get(key)
                       for key in expected_route
                       if key not in ['flags', 'should_exist']):
                # if some keys do not match go to the next route
                continue
            # route found
            assert expected_route['should_exist'], f'Route {route} found, but not expected'
            assert all(flag in route['flags'] for flag in expected_route['flags']), \
                f'Route {route} should have {expected_route["flags"]} flags'
            break
        else:  # route not found
            if expected_route['should_exist']:
                raise LookupError(f'Route {expected_route} expected, but not found')


async def verify_dut_neighbors(dent, expected_neis):
    out = await IpNeighbor.show(input_data=[{dent: [
        {'cmd_options': '-j -4'},
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get IPv4 neighbors'
    neighbors = out[0][dent]['parsed_output']

    out = await IpNeighbor.show(input_data=[{dent: [
        {'cmd_options': '-j -6'},
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get IPv6 neighbors'
    neighbors += out[0][dent]['parsed_output']

    for expected_nei in expected_neis:
        for nei in neighbors:
            for key in expected_nei:  # find matching neighbor
                if key == 'states':
                    continue
                if expected_nei[key] != nei[key]:
                    break
            else:  # neighbor found
                assert 'offload' in nei, f'Neighbor {nei} should be offloaded'
                assert nei['state'][0] in expected_nei['states'], \
                    f'Neighbor {nei} should have one of {expected_nei["states"]} states'
                break
        else:  # neighbor not found
            raise LookupError(f'Neighbor {expected_nei} expected, but not found')

    learned_macs = {}
    for nei in neighbors:
        if nei['dev'] not in learned_macs:
            learned_macs[nei['dev']] = []
        learned_macs[nei['dev']].append(nei['lladdr'])
    return learned_macs


async def verify_dut_addrs(dent, expected_addrs, expect_family=('inet', 'inet6')):
    out = await IpAddress.show(input_data=[{dent: [
        {'cmd_options': '-j -4'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get IPv4 addr'
    links = out[0][dent]['parsed_output']

    out = await IpAddress.show(input_data=[{dent: [
        {'cmd_options': '-j -6'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get IPv6 addr'
    links += out[0][dent]['parsed_output']

    for swp, ip, plen in expected_addrs:
        for link in links:
            if swp != link['ifname']:
                continue
            # link found
            for addr in link['addr_info']:
                if ip != addr['local']:
                    continue
                # IP addr found
                assert addr['family'] in expect_family, f'Expected {addr} to be {expect_family}'
                assert addr['prefixlen'] == plen, f'Expected {addr} prefix length to be {plen}'
                break
            else:  # IP addr not found
                # `links` list might have duplicate entries (for ipv4 and ipv6),
                # thus we need to look through all of the entries.
                continue
            break
        else:  # `swp` with `ip` addr not found
            raise LookupError(f'IP addr {swp, addr} expected, but not found')
