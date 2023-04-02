import pytest
import asyncio

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ethtool.ethtool import Ethtool

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_dev_groups_from_config,
    tgen_utils_traffic_generator_connect,
    tgen_utils_update_l1_config
)

pytestmark = [pytest.mark.suite_functional_l1,
              pytest.mark.asyncio,
              pytest.mark.usefixtures("cleanup_bridges", "cleanup_tgen")]


@pytest.mark.parametrize("l1_settings", ["autodetect", "autoneg"])
async def test_l1_settings_(testbed, l1_settings):
    """
    Test Name: L1 settings verification
    Test Suite: suite_functional_l1
    Test Overview: Verify L1 settings on dut port
    Test Procedure:
    1. Create bridge entity
    2. Enslave ports to the created bridge entity
    3. Set up port duplex, speed
    4. Verify port mode and speed
    5. Verify "Link Partner Advertised Auto-negotiation" is set to `Yes`
    6. Verify "Advertised Auto-negotiation" is set to `Yes`
    7. Verify "Link Partner Advertised Link Modes" is set to configured speed/duplex
    8. Verify "Advertised Link Modes" is set to configured speed/duplex
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 1)
    if not tgen_dev or not dent_devices:
        pytest.skip("The testbed does not have enough dent with tgen connections")
    device_host_name = dent_devices[0].host_name
    tg_port = tgen_dev.links_dict[device_host_name][0][0]
    port = tgen_dev.links_dict[device_host_name][1][0]
    speed = 1000
    duplex = "full"
    advertise = "0x020"

    options = {
        "autodetect":
            {
                "devname": port,
                "speed": speed,
                "duplex": "full"},
        "autoneg":
            {
                "devname": port,
                "autoneg": "on",
                "advertise": advertise}
    }

    # 1. Create bridge entity
    out = await IpLink.add(input_data=[{device_host_name: [{"device": "br0", "type": "bridge"}]}])
    assert out[0][device_host_name]["rc"] == 0, f"Failed creating bridge."

    out = await IpLink.set(input_data=[{device_host_name: [{"device": "br0", "operstate": "up"}]}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify that bridge set to 'up' state."

    # 2. Enslave port(s) to the created bridge entity
    out = await IpLink.set(input_data=[{device_host_name: [{
        "device": port,
        "operstate": "up",
        "master": "br0"
        }]}])
    assert out[0][device_host_name]["rc"] == 0, f"Failed setting link to state up."

    # 3. Set up port(s) duplex, speed, advertise
    out = await Ethtool.set(input_data=[{device_host_name: [options[l1_settings]]}])

    assert out[0][device_host_name]["rc"] == 0, f"Failed setting port duplex, speed."

    dev_groups = tgen_utils_dev_groups_from_config(
        [{"ixp": tg_port, "ip": "100.1.1.2", "gw": "100.1.1.6", "plen": 24}])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_port, port, dev_groups)

    # update settings on IXIA port
    await tgen_utils_update_l1_config(tgen_dev, tg_port, speed=speed, autoneg=True, duplex=duplex)

    await asyncio.sleep(20)  # wait needed in case port was down before

    out = await Ethtool.show(input_data=[{device_host_name: [{"devname": port}]}],  parse_output=True)

    # 4. Verify port mode: speed 1000 duplex full
    actual_speed = int(out[0][device_host_name]["parsed_output"]["speed"][:-4])
    assert speed == actual_speed, f"Expected  speed: {speed}, actual speed: {actual_speed}"
    actual_duplex = out[0][device_host_name]["parsed_output"]["duplex"]
    assert duplex.capitalize() == actual_duplex,  f"Expected  duplex: {duplex}, actual duplex: {actual_duplex}"

    # 5. Verify "Link Partner Advertised Auto-negotiation" is set to `Yes`
    actual_partner_adv_autoneg = out[0][device_host_name]["parsed_output"]["link_partner_advertised_auto-negotiation"]
    assert "Yes" == actual_partner_adv_autoneg, f"Expected Link Partner Advertised Auto-negotiation: Yes," \
                                                f" actual: {actual_partner_adv_autoneg}"

    # 6. Verify "Advertised Auto-negotiation" field in ethtool is set to `Yes`
    actual_adv_autoneg = out[0][device_host_name]["parsed_output"]["advertised_auto-negotiation"]
    assert "Yes" == actual_adv_autoneg,  f"Expected Advertised Auto-negotiation: Yes, actual: {actual_adv_autoneg}"

    # 7. Verify "Link partner Advertised Link Modes" field in ethtool command is as expected
    lnk_prtn_ad_link_modes = out[0][device_host_name]["parsed_output"]["link_partner_advertised_link_modes"]
    assert f"{speed}baseT/{duplex.capitalize()}" in lnk_prtn_ad_link_modes, \
        f"Expected Link partner Advertised Link Modes: {speed}baseT/{duplex.capitalize()}" \
        f" actual: {lnk_prtn_ad_link_modes}"

    # 8. Verify "Advertised Link Modes" field in ethtool command is as expected
    adv_link_modes = out[0][device_host_name]["parsed_output"]["advertised_link_modes"]
    assert f"{speed}baseT/{duplex.capitalize()}" == adv_link_modes,\
        f"Expected Advertised Link Modes:{speed}baseT/{duplex.capitalize()}, actual: {adv_link_modes}"
