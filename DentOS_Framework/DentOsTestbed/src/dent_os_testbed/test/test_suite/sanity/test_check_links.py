# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import time

import pytest

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.utils.test_utils.tb_utils import tb_get_all_devices, tb_generate_network_diagram

pytestmark = pytest.mark.suite_system_health


async def get_link_operstate(host_name, link):
    if host_name == 'tgen':
        return 'UP'
    out = await IpLink.show(
        input_data=[{host_name: [{'device': link, 'cmd_options': '-j'}]}],
        parse_output=True,
    )
    assert out[0][host_name]['rc'] == 0
    # bond interface parent will take care of the UP/DOWN
    if (
        out[0][host_name]['parsed_output'][0]['operstate'] == 'DOWN'
        and 'SLAVE' in out[0][host_name]['parsed_output'][0]['flags']
    ):
        return 'UP'
    return out[0][host_name]['parsed_output'][0]['operstate']


async def check_and_validate_switch_links(testbed):
    """
    - check the links if they are up
    - down on one and see of the other end goes down for validity
    """
    CGREEN = '\33[32m'
    CRED = '\33[91m'
    CEND = '\33[0m'

    devices = {}
    links_dict = {}
    for dev in await tb_get_all_devices(testbed):
        devices[dev.host_name] = dev
        links_dict[dev.host_name] = {}

    for _, dev in devices.items():
        if dev.type not in [
            DeviceType.DISTRIBUTION_ROUTER,
            DeviceType.AGGREGATION_ROUTER,
            DeviceType.OUT_OF_BOUND_SWITCH,
            DeviceType.INFRA_SWITCH,
        ]:
            continue
        for links in dev.links:
            # check now
            link = links[0]
            other_end = links[1].split(':')
            operstate = await get_link_operstate(dev.host_name, link)
            verified = 'N/A'
            # if the other is not in the topo then mark as not available
            if operstate != 'UP' and other_end[0] not in devices:
                operstate = 'N/A'

            # this can be done on system which is not provisiond since there might be links that
            # cannot be brought down.
            if not testbed.args.is_provisioned and operstate == 'UP' and other_end[0] in devices:
                out = await IpLink.set(
                    input_data=[{dev.host_name: [{'device': link, 'operstate': 'down'}]}],
                )
                assert out[0][dev.host_name]['rc'] == 0
                time.sleep(5)
                other_operstate = await get_link_operstate(other_end[0], other_end[1])
                verified = 'YES' if other_operstate != 'UP' else 'NO'
                out = await IpLink.set(
                    input_data=[{dev.host_name: [{'device': link, 'operstate': 'up'}]}],
                )
            links_dict[dev.host_name][link] = [links[1], operstate, verified]

    # try to generate a visual version of the network
    try:
        tb_generate_network_diagram(testbed, links_dict)
    except Exception as e:
        pass
    all_links_up = True
    for dev, links in links_dict.items():
        for link, links in links.items():
            other = links[0]
            operstate = links[1]
            verified = links[2]
            if operstate in ['UP', 'N/A']:
                print(
                    f'{dev:>10}:{link:<10}<-->{other:>20} {CGREEN}[{operstate} - {verified}]{CEND}'
                )
            else:
                print(f'{dev:>10}:{link:<10}<-->{other:>20} {CRED}[DOWN!!]{CEND}')
                all_links_up = False

    assert all_links_up is True, 'One or more links down'


@pytest.mark.asyncio
async def test_check_and_validate_switch_links(testbed):
    """
    Test Name: test_check_and_validate_switch_links
    Test Suite: suite_system_health
    Test Overview: Check the links between infra, agg, oob, dist devices if they are UP
    Test Procedure:
      1. get all the reachable devices
      2. check the operstate of the link enumerated in device.links
      3. fail the test if any of the link operstate is DOWN
    """
    # check the links
    await check_and_validate_switch_links(testbed)
