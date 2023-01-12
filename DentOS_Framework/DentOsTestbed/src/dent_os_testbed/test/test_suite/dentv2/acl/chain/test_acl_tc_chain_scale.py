import json
import time

import pytest

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.lib.iptables.ip_tables import IpTables
from dent_os_testbed.utils.test_utils.tb_utils import (
    tb_get_all_devices,
    tb_reload_nw_and_flush_firewall,
)
from dent_os_testbed.utils.test_utils.tc_flower_utils import (
    tcutil_get_tc_rule_stats,
    tcutil_iptable_to_tc,
)

pytestmark = pytest.mark.suite_acl_scale


@pytest.mark.asyncio
async def test_iptables_tc_scale(testbed):
    """
    Test Name: test_iptables_tc_scale
    Test Suite: suite_acl_scale
    Test Overview: To test the tc chain support with 2000 tcp rules and 10 icmp rules.
    Test Procedure:
    1. To test the ACL scale with chain's
    2. select infra devices and install iptables FORWARD rules.
    3. should have installed all the rules in the hardware in different chains
    """
    devices = await tb_get_all_devices(testbed, include_devices=[DeviceType.INFRA_SWITCH])
    if not devices:
        testbed.applog.info(f"No Infra devices reachable... Skipping test!!!")
        assert 0
        return
    dent_dev = devices[0]
    dent = dent_dev.host_name

    # cleanup the firewall
    await tb_reload_nw_and_flush_firewall([dent_dev])
    iptable_rules = {}
    swp = "swp1"

    rules = []
    # install 2000 rules with different sport.
    for i in range(1000, 3000):
        rule = {
            "table": "filter",
            "chain": "FORWARD",
            "in-interface": swp,
            "source": "10.0.0.0/24",
            "destination": "20.0.0.0/24",
            "protocol": "tcp",
            "dport": "443",
            "sport": f"{i}",
            "target": 'ACCEPT -m comment --comment "TC:--vlan-tag TC:100"',
        }
        rules.append(rule)
        if len(rules) > 10:
            out = await IpTables.append(input_data=[{dent: rules}])
            dent_dev.applog.info(out)
            rules = []

    # install 10 icmp rules
    for type in range(1, 10):
        rule = {
            "table": "filter",
            "chain": "FORWARD",
            "in-interface": swp,
            "source": "30.0.0.0/24",
            "destination": "40.0.0.0/24",
            "protocol": "icmp",
            "icmp-type": type,
            # "icmp-code": code,
            "target": 'ACCEPT -m comment --comment "TC:--vlan-tag TC:100"',
        }
        rules.append(rule)
    out = await IpTables.append(input_data=[{dent: rules}])
    dent_dev.applog.info(out)

    # convert it to tc
    # perform the rule translation
    await tcutil_iptable_to_tc(
        dent_dev, [swp], iptable_rules, extra_args=" --prestera-chain-mode --no-batch --non-atomic "
    )
    swp_tc_rules = {}
    await tcutil_get_tc_rule_stats(dent_dev, [swp], swp_tc_rules)

    # check how many rules got to tc.
    assert len(swp_tc_rules[swp]) == 2011, "Failed to install 2011 rules in chain"
