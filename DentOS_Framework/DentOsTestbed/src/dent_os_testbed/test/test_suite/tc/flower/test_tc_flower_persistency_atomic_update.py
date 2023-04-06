import time

import pytest

from dent_os_testbed.lib.iptables.ip_tables import IpTables
from dent_os_testbed.utils.test_utils.tb_utils import tb_reload_nw_and_flush_firewall
from dent_os_testbed.utils.test_utils.tc_flower_utils import (
    tcutil_cleanup_tc_rules,
    tcutil_get_tc_rule_stats,
    tcutil_iptable_to_tc,
)
from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_connect_to_tgen,
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_get_swp_info,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_protocols,
    tgen_utils_stop_traffic,
)

pytestmark = pytest.mark.suite_tc_flower


@pytest.mark.asyncio
async def test_tc_flower_persistency_atomic_update_w_traffic(testbed):
    """
    Test Name: test_tc_flower_persistency_atomic_update_w_traffic
    Test Suite: suite_tc_flower
    Test Overview: Test the tc flower tool with atomic flag while traffic is flowing
    Test Procedure:
    1. setup dent switch
      - get a dent switch
      - configure the switch for h/w forwarding
    2. setup tgen
      - setup traffic stream with a known SIP1,DIP1 and SIP2,DIP2
    3. install two iptables rules in filter table at FORWARD stage
      to drop and accept the packet matching SIP1 and DIP1
      - 1. iptables -t filter -A FORWARD -i swp1 -s SIP1 -d DIP1 -j DROP
      - 2. iptables -t filter -A FORWARD -i swp1 -s SIP1 -d DIP1 -j PASS
    4. run the tc persistency  tools
    5. start the traffic
    6. install two more iptables rules in filter table at FORWARD stage
      to drop the packet matching SIP2 and DIP2
      - 1. iptables -t filter -A FORWARD -i swp1 -s SIP1 -d DIP1 -j DROP
      - 2. iptables -t filter -A FORWARD -i swp1 -s SIP1 -d DIP1 -j PASS
      - 3. iptables -t filter -A FORWARD -i swp1 -s SIP2 -d DIP2 -j DROP
      - 4. iptables -t filter -A FORWARD -i swp1 -s SIP2 -d DIP2 -j PASS
    7. run the tc persistency  tools
    8. check the traffic stats
      - the traffic to SIP1 should not be accepted
    """
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        print('The testbed does not have enough dent with tgen connections')
        return
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    swp_tgen_ports = tgen_dev.links_dict[dent][1]

    await tb_reload_nw_and_flush_firewall([dent_dev])

    await tgen_utils_connect_to_tgen(tgen_dev, dent_dev)
    streams = {
        'bgp': {
            'protocol': 'ip',
            'ipproto': 'tcp',
            'dstPort': '179',
        },
    }
    await tgen_utils_setup_streams(
        tgen_dev,
        pytest._args.config_dir + f'/{dent}/tgen_tc_atomic_config.ixncfg',
        streams,
    )

    # - install iptables rules in filter table at FORWARD stage
    #  to drop the packet matching SIP and DIP
    #  - iptables -t filter -A FORWARD -i swp1 -s SIP -d DIP -j DROP
    iptable_rules = {}
    sip = {}
    sip2 = {}
    for swp in swp_tgen_ports:
        swp_info = {}
        await tgen_utils_get_swp_info(dent_dev, swp, swp_info)
        sip[swp] = '.'.join(swp_info['ip'][:-1] + [str(int(swp[3:]) * 2)])
        sip2[swp] = '.'.join(swp_info['ip'][:-1] + [str(int(swp[3:]) * 2 + 1)])
        iptable_rules[swp] = [
            {
                'table': 'filter',
                'chain': 'FORWARD',
                'in-interface': swp,
                'source': sip[swp],  # FIXME
                'protocol': 'tcp',
                'dport': '179',
                'target': 'DROP',
            },
            {
                'table': 'filter',
                'chain': 'FORWARD',
                'in-interface': swp,
                'source': sip[swp],  # FIXME
                'protocol': 'tcp',
                'dport': '179',
                'target': 'ACCEPT',
            },
            {
                'table': 'filter',
                'chain': 'FORWARD',
                'in-interface': swp,
                'target': 'ACCEPT',
            },
        ]
        dent_dev.applog.info(f'Adding iptable rule for {swp}')
        out = await IpTables.append(input_data=[{dent: iptable_rules[swp]}])
        dent_dev.applog.info(out)
    # out = await IpTables.list(input_data=[{dent: [{"table": "filter", "chain": "FORWARD",}]}])
    # dent_dev.applog.info(out)

    # perform the rule translation
    await tcutil_iptable_to_tc(dent_dev, swp_tgen_ports, iptable_rules)
    await tgen_utils_start_traffic(tgen_dev)
    # - check the traffic stats
    #  -- all the packets matching the SIP and DIP should be dropped.
    dent_dev.applog.info('zzzZZZ!! (20s)')
    time.sleep(20)
    swp_tc_rules = {}
    await tcutil_get_tc_rule_stats(dent_dev, swp_tgen_ports, swp_tc_rules)
    # install the rule set
    iptable_rules = {}
    for swp in swp_tgen_ports:
        iptable_rules[swp] = [
            {
                'table': 'filter',
                'chain': 'FORWARD',
                'in-interface': swp,
                'source': sip[swp],
                'protocol': 'tcp',
                'dport': '179',
                'target': 'DROP',
            },
            {
                'table': 'filter',
                'chain': 'FORWARD',
                'in-interface': swp,
                'source': sip[swp],
                'protocol': 'tcp',
                'dport': '179',
                'target': 'ACCEPT',
            },
            {
                'table': 'filter',
                'chain': 'FORWARD',
                'in-interface': swp,
                'source': sip2[swp],
                'protocol': 'tcp',
                'dport': '179',
                'target': 'DROP',
            },
            {
                'table': 'filter',
                'chain': 'FORWARD',
                'in-interface': swp,
                'source': sip2[swp],
                'protocol': 'tcp',
                'dport': '179',
                'target': 'ACCEPT',
            },
            {
                'table': 'filter',
                'chain': 'FORWARD',
                'in-interface': swp,
                'target': 'ACCEPT',
            },
        ]
        dent_dev.applog.info(f'Updating iptable rule for {swp}')
        out = await IpTables.append(input_data=[{dent: iptable_rules[swp]}])
        dent_dev.applog.info(out)
    # out = await IpTables.list(input_data=[{dent: [{"table": "filter", "chain": "FORWARD",}]}])
    # dent_dev.applog.info(out)
    # perform the rule translation
    await tcutil_iptable_to_tc(dent_dev, swp_tgen_ports, iptable_rules)
    dent_dev.applog.info('zzzZZZ!! (20s)')
    time.sleep(20)
    swp_tc_rules = {}
    await tcutil_get_tc_rule_stats(dent_dev, swp_tgen_ports, swp_tc_rules)

    # install the new rule set
    iptable_rules = {}
    for swp in swp_tgen_ports:
        iptable_rules[swp] = [
            {
                'table': 'filter',
                'chain': 'FORWARD',
                'in-interface': swp,
                'source': sip2[swp],
                'protocol': 'tcp',
                'dport': '179',
                'target': 'DROP',
            },
            {
                'table': 'filter',
                'chain': 'FORWARD',
                'in-interface': swp,
                'source': sip2[swp],
                'protocol': 'tcp',
                'dport': '179',
                'target': 'ACCEPT',
            },
            {
                'table': 'filter',
                'chain': 'FORWARD',
                'in-interface': swp,
                'target': 'ACCEPT',
            },
        ]
        dent_dev.applog.info(f'Updating iptable rule for {swp}')
        out = await IpTables.append(input_data=[{dent: iptable_rules[swp]}])
        dent_dev.applog.info(out)
    # out = await IpTables.list(input_data=[{dent: [{"table": "filter", "chain": "FORWARD",}]}])
    # dent_dev.applog.info(out)
    # perform the rule translation
    await tcutil_iptable_to_tc(dent_dev, swp_tgen_ports, iptable_rules)
    dent_dev.applog.info('zzzZZZ!! (20s)')
    time.sleep(20)

    await tgen_utils_stop_traffic(tgen_dev)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    swp_tc_rules = {}
    await tcutil_get_tc_rule_stats(dent_dev, swp_tgen_ports, swp_tc_rules)
    # verify the rules stats

    # end of Test
    await tgen_utils_stop_protocols(tgen_dev)
    # cleanup
    tcutil_cleanup_tc_rules(dent_dev, swp_tgen_ports, swp_tc_rules)
