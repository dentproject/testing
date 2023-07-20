import pytest

from dent_os_testbed.lib.tc.tc_filter import TcFilter
from dent_os_testbed.lib.tc.tc_qdisc import TcQdisc
from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.utils.test_utils.tgen_utils import tgen_utils_get_dent_devices_with_tgen

pytestmark = [
    pytest.mark.suite_functional_lacp,
    pytest.mark.usefixtures('cleanup_qdiscs', 'cleanup_tgen', 'cleanup_bonds'),
    pytest.mark.asyncio,
]


async def test_lacp_acl_negative(testbed):
    """
    Test Name: LAG with ACL
    Test Suite: suite_functional_lacp
    Test Overview: Verify rule is not offloaded when created on bond entity
    Test Procedure:
    1. Create a bond entity
    3. Create an ingress qdisc on the LAG
    4. Add a rule to bond entity
    5. Verify the rule is not offloaded
    """

    # 1. Create a bond entity
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 0)
    if not tgen_dev or not dent_devices:
        pytest.skip(
            'The testbed does not have enough dent with tgen connections')
    device = dent_devices[0]
    dent = device.host_name
    bond = 'bond_33'

    out = await IpLink.add(input_data=[{dent: [{
        'name': bond,
        'type': 'bond',
        'mode': '802.3ad'
        }]
    }])
    assert out[0][dent]['rc'] == 0, 'Failed creating bond entity.'

    await IpLink.set(input_data=[{dent: [{'device': bond, 'operstate': 'up'}]}])
    assert out[0][dent]['rc'] == 0, 'Failed setting bond to state UP.'

    # 3. Create an ingress qdisc on the LAG

    out = await TcQdisc.add(input_data=[{dent: [{
        'dev': bond,
        'direction': 'ingress'}]}])
    assert out[0][dent]['rc'] == 0, 'Failed adding qdisc'
    tc_rule = {
        'dev': bond,
        'direction': 'ingress',
        'filtertype': {},
        'action': 'drop'
        }

    # 4. Add a rule to bond entity
    out = await TcFilter.add(input_data=[{dent: [tc_rule]}])
    assert out[0][dent]['rc'] == 0, 'Fail in adding tc rule to bond'

    # 5. Verify the rule is not offloaded
    out = await TcFilter.show(input_data=[{dent: [
        {'dev': bond, 'direction': 'ingress', 'options': '-j'}]}], parse_output=True)
    assert out[0][dent]['rc'] == 0, 'Fail retrieving rules'
    not_offloaded = out[0][dent]['parsed_output'][1]['options'].get('not_in_hw')
    assert not_offloaded, 'Verify the rule is not offloaded'
