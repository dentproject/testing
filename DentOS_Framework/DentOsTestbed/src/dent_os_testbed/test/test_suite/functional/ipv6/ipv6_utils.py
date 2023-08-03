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
            if not all(expected_nei[key] == nei.get(key)
                       for key in expected_nei
                       if key not in ['states', 'offload', 'should_exist']):
                # if some keys do not match go to the next neighbor
                continue
            # neighbor found
            assert expected_nei['should_exist'], f'Neighbor {nei} found, but not expected'
            assert nei['state'][0] in expected_nei['states'], \
                f'Neighbor {nei} should have one of {expected_nei["states"]} states'
            if 'offload' in expected_nei:
                # neighbor is offloaded when the entry has the 'offload' key (the value does not matter)
                assert ('offload' in nei) == expected_nei['offload'], \
                    f'Expected offload state {expected_nei["offload"]}, but neighbor has {nei}'
            break
        else:  # neighbor not found
            if expected_nei['should_exist']:
                raise LookupError(f'Neighbor {expected_nei} expected, but not found')


async def get_dut_neighbors(dent):
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

    learned_macs = {}
    for nei in neighbors:
        if nei['dev'] not in learned_macs:
            learned_macs[nei['dev']] = []
        if 'lladdr' in nei and not nei.get('dst', '').startswith('fe80'):  # ignore mcast
            learned_macs[nei['dev']].append(nei['lladdr'])
    return learned_macs


async def verify_dut_addrs(dent, expected_addrs):
    out = await IpAddress.show(input_data=[{dent: [
        {'cmd_options': '-j'}
    ]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get IPv4 addr'

    for expected_addr in expected_addrs:
        for link in out[0][dent]['parsed_output']:
            if not all(expected_addr[key] == link.get(key)
                       for key in expected_addr
                       if key not in ['addr_info', 'should_exist']):
                # if some keys do not match go to the next link
                continue
            # link found
            if any(all(expected_addr['addr_info'][key] == addr.get(key)
                       for key in expected_addr['addr_info'])
                   for addr in link['addr_info']):
                # addr in link found
                assert expected_addr['should_exist'], f'Link {link} found, but not expected'
                break
        else:  # link with addr not found
            if expected_addr['should_exist']:
                raise LookupError(f'IP addr {expected_addr} expected, but not found')
