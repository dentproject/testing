import pytest

from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.utils.test_utils.tb_utils import tb_get_all_devices

pytestmark = [pytest.mark.suite_functional_vlan,
              pytest.mark.asyncio,
              pytest.mark.usefixtures('cleanup_bridges', 'cleanup_tgen')]


async def test_vlan_can_set_max_vlans(testbed):
    """
    Test Name: Maximum vlans for the interface
    Test Suite: suite_functional_vlan
    Test Overview: Test maximum number of vlans that can be set on interface
    Test Procedure:
    1. Initiate test params
    2. Create bridge entity and set state to "up" state.
    3. Enslave interface to the created bridge entity.
    4. Insert interface to all VLANs possible (4094)
    5. Verify interface is in all possible (4094) VLANs
    """

    # 1. Initiate test params
    dent_devices = await tb_get_all_devices(testbed)
    device = dent_devices[0].host_name
    test_port = dent_devices[0].links_dict[device][1][0]  # get first port from config
    max_vlans = 4094
    bridge = 'br0'

    # 2. Create bridge entity and set state to "up" state
    out = await IpLink.add(input_data=[{device: [{'device': bridge, 'type': 'bridge', 'vlan_filtering': 1}]}])
    assert out[0][device]['rc'] == 0, 'Failed to create bridge'

    out = await IpLink.set(input_data=[{device: [{'device': bridge, 'operstate': 'up'}]}])
    assert out[0][device]['rc'] == 0, 'Failed to set bridge status to UP'

    # 3. Enslave interface to the created bridge entity
    out = await IpLink.set(input_data=[{device: [{'device': test_port, 'master': bridge, 'operstate': 'up'}]}])
    assert out[0][device]['rc'] == 0, 'Failed to enslave links to bridge'

    # 4. Insert interface to all VLANs possible
    cmd = f'time for i in {{1..{max_vlans}}}; do bridge vlan add vid $i dev {test_port}; done'
    rc, _ = await dent_devices[0].run_cmd(cmd)
    assert rc == 0, f'Failed adding the interface to VLANs 1..{max_vlans}'

    # 5. Verify interface is in all possible (4094) VLANs
    out = await BridgeVlan.show(input_data=[{device: [{'device': test_port, 'cmd_options': '-j'}]}],
                                parse_output=True)
    assert len(out[0][device]['parsed_output'][0]['vlans']) == max_vlans, \
        f'Not all VLANS has been added to {test_port} on {device} device'


async def test_vlan_can_not_add_interface_to_vlan_wo_bridge(testbed):
    """
    Test Name: Add  interface to vlan without enslaving to bridge entity (negative scenario)
    Test Suite: suite_functional_vlan
    Test Overview: Test that interface can not be added to VLAN without bridge entity
    Test Procedure:
    1. Initiate test params
    2. Insert interface to any VLAN
       Verify adding interface to VLAN fails
    3. Create bridge entity.
    4. Insert interface to any VLAN
       Verify adding interface to VLAN fails
    """

    # 1. Initiate test params
    dent_devices = await tb_get_all_devices(testbed)
    device = dent_devices[0].host_name
    test_port = dent_devices[0].links_dict[device][1][0]  # get first port from config
    vid = 2
    bridge = 'br0'

    # 2. Insert interface to any VLAN. Verify adding interface to VLAN fails
    out = await BridgeVlan.add(input_data=[{device: [{'device': test_port, 'vid': vid}]}])
    assert out[0][device]['rc'] != 0, 'No error on adding interface to VLAN without creating bridge beforehand'

    # 3. Create bridge entity.
    out = await IpLink.add(input_data=[{device: [{'device': bridge, 'type': 'bridge'}]}])
    assert out[0][device]['rc'] == 0, 'Failed to create bridge'

    out = await IpLink.set(input_data=[{device: [{'device': bridge, 'operstate': 'up'}]}])
    assert out[0][device]['rc'] == 0, 'Failed setting bridge to state UP'

    # 4. Insert interface to any VLAN. Verify adding interface to VLAN fails
    out = await BridgeVlan.add(input_data=[{device: [{'device': test_port, 'vid': vid}]}])
    assert out[0][device]['rc'] != 0, 'No error on inserting port to a VLAN without bridge'
