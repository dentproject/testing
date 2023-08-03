import pytest
import re
import asyncio

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.utils.test_utils.tgen_utils import tb_get_all_devices

pytestmark = [pytest.mark.suite_functional_lacp,
              pytest.mark.asyncio,
              pytest.mark.usefixtures('cleanup_tgen', 'cleanup_bonds')]


async def get_all_device_ports(device, port):
    name_template = re.search(r'(.+?)\d{1,2}$', port).group(1)
    out = await IpLink.show(input_data=[{device: [{'cmd_options': '-j'}]}], parse_output=True)
    res = out[0][device]['parsed_output']
    ports = [el['ifname'] for el in res if name_template in el['ifname']]
    return ports


async def test_lacp_unsupported_modes(testbed):
    """
    Test Name: LACP unsupported modes
    Test Suite: suite_functional_lacp
    Test Overview: Test lacp unsupported modes state
    Test Procedure:
    1. Create bond devices with unsupported modes : 'balance-rr', 'broadcast', 'balance-tlb', 'balance-alb'
    2. Try to set created bond devices to `up` state
    3. Verify bond(s) with unsupported modes are in `down` state
    """
    dent_devices = await tb_get_all_devices(testbed)
    device = dent_devices[0].host_name
    unsupported_modes = ['balance-rr',
                         'broadcast', 'balance-tlb', 'balance-alb']
    # 1. Create bond devices with unsupported modes : 'balance-rr', 'broadcast', 'balance-tlb', 'balance-alb'
    out = await IpLink.add(input_data=[{device: [
        {'device': f'bond_{unsupported_modes.index(mode)}',
         'type': 'bond',
         'mode': mode} for mode in unsupported_modes]}])
    assert out[0][device]['rc'] == 0, 'Fail to create bond(s)'
    # 2. Try to set created bond devices to `up` state

    out = await IpLink.set(input_data=[{device: [
        {'device': f'bond_{unsupported_modes.index(mode)}',
         'operstate': 'up'} for mode in unsupported_modes]}])
    assert out[0][device]['rc'] == 0, 'Fail to set bond(s) to up state'

    await asyncio.sleep(15)
    # 3. Verify bond(s) with unsupported modes are in `down` state
    for mode in unsupported_modes:
        out = await IpLink.show(input_data=[{device: [{'device': f'bond_{unsupported_modes.index(mode)}',
                                                       'cmd_options': '-j'}]}], parse_output=True)
        err_msg = f'Bond bond_{unsupported_modes.index(mode)} with unsupported mode {mode} is in `UP` state'
        assert out[0][device]['parsed_output'][0]['operstate'] == 'DOWN', err_msg


async def test_lacp_max_lags(testbed):
    """
    Test Name: LACP maximum lags
    Test Suite: suite_functional_lacp
    Test Overview: Test lacp maximum lags creation
    Test Procedure:
    1. Create max 'number of  bond devices
    2. Verify it is possible to create max 'number of bond devices
    2. Enslave all ports to different bonds
    3. Verify it is possible to enslave all ports to bond(s)
    """
    dent_devices = await tb_get_all_devices(testbed)
    device = dent_devices[0].host_name
    ports = dent_devices[0].links_dict[device][1]
    device_ports = await get_all_device_ports(device, ports[0])
    max_bonds = 64
    # 1. Create max 'number of  bond devices
    cmd = [{'device': f'bond_{idx}',
            'type': 'bond',
            'mode': '802.3ad'} for idx in range(max_bonds)]
    out = await IpLink.add(input_data=[{device: cmd}])
    # 2. Verify it is possible to create bond devices
    assert out[0][device]['rc'] == 0, 'Fail to create bond(s)'

    port_name = re.search(r'(.+?)\d{1,2}$', ports[0]).group(1)
    rc, num_of_ports = await dent_devices[0].run_cmd(f'ifconfig  -a | grep -Eo "{port_name}[0-9]+" | wc -l')
    assert rc == 0, 'Failed to calculate number of ports'
    assert int(num_of_ports) >= 1, 'Fail getting port on devices'

    out = await IpLink.set(input_data=[{device: [
        {'device': port,
         'operstate': 'down'} for port in device_ports]}])
    assert out[0][device]['rc'] == 0, 'Fail to set port(s) to down state'
    # 2. Enslave all ports to different bonds
    out = await IpLink.set(input_data=[{device: [
        {'device': port,
         'master': f'bond_{idx}'} for idx, port in enumerate(device_ports)]}])

    # 3. Verify it is possible to enslave all ports to bond(s)
    assert out[0][device]['rc'] == 0, 'Fail to enslave port(s) to bond'

    out = await IpLink.set(input_data=[{device: [
        {'device': port,
         'operstate': 'up'} for port in device_ports]}])
    assert out[0][device]['rc'] == 0, 'Fail to set ports to up state'


async def test_lacp_max_ports_in_lags(testbed):
    """
    Test Name: LACP ports in lag
    Test Suite: suite_functional_lacp
    Test Overview: Test can enslave max number of ports to lag
    Test Procedure:
    1. Create bond device
    5. Add 9 ports to bond
    6. Verify only 8 ports can be enslaved to bond
    """
    dent_devices = await tb_get_all_devices(testbed)
    device = dent_devices[0].host_name
    bond = 'bond_1'
    max_ports_in_lag = 8
    ports = dent_devices[0].links_dict[device][1]
    device_ports = await get_all_device_ports(device, ports[0])

    # 1. Create bond device
    out = await IpLink.add(input_data=[{device: [{'device': bond,
                                                  'type': 'bond',
                                                  'mode': '802.3ad'}]}])
    assert out[0][device]['rc'] == 0, 'Fail to create bond'

    # 5. Add 9 ports to bond
    out = await IpLink.set(input_data=[{device: [
        {'device': port,
         'operstate': 'down'} for port in device_ports[:max_ports_in_lag + 1]]}])
    assert out[0][device]['rc'] == 0, 'Fail to set port to down state'

    out = await IpLink.set(input_data=[{device: [
        {'device': port,
         'master': bond} for port in device_ports[:max_ports_in_lag + 1]]}])
    assert 'RTNETLINK answers: No space left on device' in out[0][device]['result'],\
        f'Number of enslaved ports is about the limit of {max_ports_in_lag}'

    out = await IpLink.set(input_data=[{device: [
        {'device': port,
         'operstate': 'up'} for port in device_ports[:max_ports_in_lag + 1]]}])
    assert out[0][device]['rc'] == 0, 'Fail setting port(s) to up state'
