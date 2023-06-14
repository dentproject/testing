from functools import reduce
import pytest_asyncio
import asyncio

from dent_os_testbed.lib.ethtool.ethtool import Ethtool
from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
)


adv_modes = {
    '10baseT/Half': 0x001,
    '10baseT/Full': 0x002,
    '100baseT/Half': 0x004,
    '100baseT/Full': 0x008,
    '1000baseT/Full': 0x020,
    '10000baseT/Full': 0x1000,
}


@pytest_asyncio.fixture()
async def restore_port_speed(testbed):
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        print('The testbed does not have enough dent with tgen connections')
        return
    dent = dent_devices[0].host_name
    ports = tgen_dev.links_dict[dent][1]

    out = await IpLink.show(input_data=[{dent: [{'cmd_options': '-j'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Failed to get port state'

    if not all(link['operstate'] == 'UP'
               for link in out[0][dent]['parsed_output']
               if link['ifname'] in ports):
        # not all ports are up
        # port hast to be UP to see current advertisement modes and/or speed
        out = await IpLink.set(input_data=[{dent: [
            {'device': port, 'operstate': 'up'}
            for port in ports
        ]}])
        assert out[0][dent]['rc'] == 0, 'Failed to set operstate up'

        await asyncio.sleep(10)

    ethtool = await asyncio.gather(*[
        Ethtool.show(input_data=[{dent: [{'devname': port}]}], parse_output=True)
        for port in ports
    ])
    assert all(out[0][dent]['rc'] == 0 for out in ethtool), 'Failed to get ports\' speed'

    yield  # Run the test

    cmd = []
    for out, port in zip(ethtool, ports):
        mode = out[0][dent]['parsed_output']
        if 'Unknown!' in mode['speed']:
            continue
        if mode['auto-negotiation'] == 'on':
            adv = reduce(lambda x, y: x | y,
                         [adv_modes[m]
                          for m in mode['advertised_link_modes'].split(' ')
                          if m in adv_modes])
            cmd.append({
                'devname': port,
                'autoneg': mode['auto-negotiation'],
                'advertise': f'{adv:X}',
            })
        else:  # not autoneg
            cmd.append({
                'devname': port,
                'autoneg': 'off',
                'speed': int(mode['speed'][:-4]),
                'duplex': mode['duplex'].lower(),
            })

    if cmd:
        await Ethtool.set(input_data=[{dent: cmd}])
