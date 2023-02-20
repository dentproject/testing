import pytest

from dent_os_testbed.lib.tc.tc_filter import TcFilter
from dent_os_testbed.lib.tc.tc_qdisc import TcQdisc


from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
)

pytestmark = [
    pytest.mark.suite_functional_acl,
    pytest.mark.usefixtures("cleanup_qdiscs"),
    pytest.mark.asyncio,
]


async def test_acl_rule_without_qdisc(testbed):
    """
    Test Name: test_acl_rule_without_qdisc
    Test Suite: suite_functional_acl
    Test Overview: Check that creating a rule without a qdisc will fail
    Test Procedure:
    1. Initiate test params
    2. Define a qsidc
    3. Try adding rules to a port - make sure does not fail
    4. Delete the qdisc
    5. Try adding rules to a port - make sure it fails
    """
    # 1. Initiate test params
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 1)
    if not tgen_dev or not dent_devices:
        pytest.skip("The testbed does not have enough dent with tgen connections")
    dent = dent_devices[0].host_name
    port = tgen_dev.links_dict[dent][1][0]
    handle = 10

    # 2. Define a qsidc
    out = await TcQdisc.add(input_data=[{dent: [
        {"dev": port, "direction": "clsact", "handle": handle}
    ]}])
    assert out[0][dent]["rc"] == 0, "Failed to create qdisc"

    # 3. Try adding rules to a port - make sure does not fail
    out = await TcFilter.add(input_data=[{dent: [
        {"dev": port,
         "direction": "ingress",
         "filtertype": {"skip_sw": ""},
         "action": "drop"}
    ]}])
    assert out[0][dent]["rc"] == 0, "Failed to create tc rules"

    # 4. Delete the qdisc
    out = await TcQdisc.delete(input_data=[{dent: [
        {"dev": port, "direction": "clsact", "handle": handle}
    ]}])
    assert out[0][dent]["rc"] == 0, "Failed to delete qdisc"

    # 5. Try adding rules to a port - make sure it fails
    out = await TcFilter.add(input_data=[{dent: [
        {"dev": port,
         "direction": "ingress",
         "filtertype": {"skip_sw": ""},
         "action": "drop"}
    ]}])
    assert out[0][dent]["rc"] != 0, "Adding rules without qdisc should fail"
