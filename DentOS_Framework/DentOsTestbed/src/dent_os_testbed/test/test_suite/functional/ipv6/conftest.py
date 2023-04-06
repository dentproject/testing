import pytest_asyncio

from dent_os_testbed.lib.os.recoverable_sysctl import RecoverableSysctl

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
)

from dent_os_testbed.utils.test_utils.cleanup_utils import (
    cleanup_sysctl,
)


@pytest_asyncio.fixture()
async def enable_ipv6_forwarding(testbed):
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgen connections")
        return
    dent = dent_devices[0].host_name
    ip_forward = "net.ipv6.conf.all.forwarding"

    # Enable ipv6 forwarding
    out = await RecoverableSysctl.set(input_data=[{dent: [
        {"variable": ip_forward, "value": 1}
    ]}])
    assert out[0][dent]["rc"] == 0

    yield  # Run the test

    # Restore original value
    await cleanup_sysctl()
