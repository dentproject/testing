import pytest
import pytest_asyncio


from dent_os_testbed.utils.test_utils.tgen_utils import tgen_utils_get_dent_devices_with_tgen
from dent_os_testbed.utils.test_utils.cleanup_utils import cleanup_sysctl
from dent_os_testbed.lib.os.recoverable_sysctl import RecoverableSysctl


@pytest_asyncio.fixture()
async def enable_ignore_linkdown_routes(testbed):
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent = dent_devices[0].host_name
    ignore_routes = 'net.ipv4.conf.default.ignore_routes_with_linkdown'

    out = await RecoverableSysctl.set(input_data=[{dent: [
        {'variable': ignore_routes, 'value': 1}
    ]}])
    assert not out[0][dent]['rc'], f'Failed to set net.ipv4.conf.default.ignore_routes_with_linkdown=1 \n{out}'

    yield

    # Restore original value
    await cleanup_sysctl()


@pytest_asyncio.fixture()
async def enable_multipath_hash_policy(testbed):
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent = dent_devices[0].host_name
    multipath_hash_policy = 'net.ipv4.fib_multipath_hash_policy'

    out = await RecoverableSysctl.set(input_data=[{dent: [
        {'variable': multipath_hash_policy, 'value': 1}
    ]}])
    assert not out[0][dent]['rc'], f'Failed to set net.ipv4.fib_multipath_hash_policy=1 \n{out}'

    yield

    # Restore original value
    await cleanup_sysctl()
