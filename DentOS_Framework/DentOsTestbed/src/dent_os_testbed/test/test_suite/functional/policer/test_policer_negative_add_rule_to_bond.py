import pytest

from dent_os_testbed.lib.tc.tc_filter import TcFilter
from dent_os_testbed.lib.tc.tc_qdisc import TcQdisc
from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.utils.test_utils.tgen_utils import tgen_utils_get_dent_devices_with_tgen

from dent_os_testbed.utils.test_utils.tc_flower_utils import tcutil_generate_rule_with_random_selectors

pytestmark = [
    pytest.mark.suite_functional_policer,
    pytest.mark.usefixtures('cleanup_qdiscs', 'cleanup_tgen', 'cleanup_bonds'),
    pytest.mark.asyncio,
]


async def test_policer_bond_rule_not_offloaded(testbed):
    """
    Test Name: Policer with bond entity
    Test Suite: suite_functional_policer
    Test Overview: Verify rule is not offloaded when created on soft entity
    Test Procedure:
    1. Create a bond entity
    2. Set link up on bond; enslave port(s) to bond entity
    3. Create an ingress qdisc on the LAG
    4. Add a police pass rule to on bond entity
    5. Verify the rule is not offloaded
    """

    # 1. Create a bond entity
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip(
            'The testbed does not have enough dent with tgen connections')
    device = dent_devices[0]
    dent = device.host_name
    ports = tgen_dev.links_dict[dent][1][:2]

    dent = device.host_name
    bond = 'bond33'

    out = await IpLink.add(input_data=[{dent: [{
        'name': bond,
        'type': 'bond',
        'mode': '802.3ad'
        }]
    }])
    assert out[0][dent]['rc'] == 0, 'Failed creating bond entity.'

    await IpLink.set(input_data=[{dent: [{'device': bond, 'operstate': 'up'}]}])
    assert out[0][dent]['rc'] == 0, 'Failed setting bond to state UP.'

    # 2. Set link up on bond; enslave port(s) to bond entity

    # Device can not be enslaved while up.
    out = await IpLink.set(input_data=[{dent: [{
        'device': port,
        'operstate': 'down',
    } for port in ports]}])
    assert out[0][dent]['rc'] == 0, 'Failed setting port(s) to state down'
    out = await IpLink.set(input_data=[{dent: [{
        'device': port,
        'master': bond
    } for port in ports]}])
    assert out[0][dent]['rc'] == 0, 'Failed enslaving port(s) to bond'

    out = await IpLink.set(input_data=[{dent: [{
        'device': port,
        'operstate': 'up',
    } for port in ports]}])
    assert out[0][dent]['rc'] == 0, 'Failed setting link(s) to state up'

    # 3. Create an ingress qdisc on the LAG

    out = await TcQdisc.add(input_data=[{dent: [{
        'dev': bond,
        'direction': 'ingress'}]}])
    assert out[0][dent]['rc'] == 0, 'Failed adding qdisc'

    # 4. Add a police pass rule to on bond entity
    tc_rule = tcutil_generate_rule_with_random_selectors(bond)
    out = await TcFilter.add(input_data=[{dent: [tc_rule]}])
    assert out[0][dent]['rc'] == 0, 'Fail in adding tc rule to bond'

    # 5. Verify the rule is not offloaded
    out = await TcFilter.show(input_data=[{dent: [
        {'dev': bond, 'direction': 'ingress', 'options': '-j'}]}], parse_output=True)
    not_offloaded = out[0][dent]['parsed_output'][1]['options'].get('not_in_hw')
    assert not_offloaded, 'Verify the rule is not offloaded'
