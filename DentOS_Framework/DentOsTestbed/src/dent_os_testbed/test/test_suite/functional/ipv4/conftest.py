import pytest_asyncio

from dent_os_testbed.lib.os.sysctl import Sysctl

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
)


@pytest_asyncio.fixture()
async def enable_ipv4_forwarding(testbed):
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgen connections")
        return
    dent = dent_devices[0].host_name
    ip_forward = "net.ipv4.ip_forward"

    # Get ip_forward to restore it later
    out = await Sysctl.get(input_data=[{dent: [
        {"variable": ip_forward, "options": "-n"}
    ]}])
    assert out[0][dent]["rc"] == 0
    default_value = int(out[0][dent]["result"])

    # Enable ipv4 forwarding
    out = await Sysctl.set(input_data=[{dent: [
        {"variable": ip_forward, "value": 1}
    ]}])
    assert out[0][dent]["rc"] == 0

    yield  # Run the test

    # Restore original value
    out = await Sysctl.set(input_data=[{dent: [
        {"variable": ip_forward, "value": default_value}
    ]}])
