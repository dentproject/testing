from dent_os_testbed.Device import DeviceType
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.utils.test_utils.tb_utils import tb_reload_nw_and_flush_firewall


async def bonding_get_interconnected_infra_devices(testbed, infra_devices):
    devices = []
    for dd1 in infra_devices:
        if dd1.type != DeviceType.INFRA_SWITCH:
            continue
        for dd2, links in dd1.links_dict.items():
            if (
                dd2 not in testbed.devices_dict
                or testbed.devices_dict[dd2].type != DeviceType.INFRA_SWITCH
                or not await testbed.devices_dict[dd2].is_connected()
            ):
                continue
            if testbed.devices_dict[dd2].type == DeviceType.INFRA_SWITCH:
                devices.append(dd1)
                break
    return devices


async def bonding_setup(infra_devices, state='down'):
    # break down all the links and pass the traffic thru the infra links
    await tb_reload_nw_and_flush_firewall(infra_devices)
    """
    # TODO cannot do this now since this will break the pssh
    for dd in infra_devices:
        # bring down the links that are 10g links
        for swp in range(49, 53):
            link = f"swp{swp}"
            # check if this link is to agg then only drop it.
            out = await IpLink.set(
                input_data=[{dd.host_name: [{"device": link, "operstate": state}]}],
            )
            assert out[0][dd.host_name]["rc"] == 0, f"Failed to {state} the link {link} {out}"
    """
