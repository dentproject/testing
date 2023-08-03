import pytest_asyncio
import asyncio
import pytest

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
)


async def _configure_mstpd(testbed, enable):
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 0)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')

    conf = '/etc/bridge-stp.conf'
    backup = '/etc/bridge-stp.conf.bak'

    out = await asyncio.gather(*[dent.run_cmd(f'cp {conf} {backup}') for dent in dent_devices])
    assert all(rc == 0 for rc, _ in out), 'Failed to create config backup'

    run_daemon = 'mstpd' if enable else '(pidof mstpd && kill `pidof mstpd`) || echo'
    enable = 'y' if enable else 'n'

    out = await asyncio.gather(*[
        dent.run_cmd(f'sed -i "/^[#]*MANAGE_MSTPD=/ cMANAGE_MSTPD=\'{enable}\'" {conf} && {run_daemon}')
        for dent in dent_devices
    ])
    assert all(rc == 0 for rc, _ in out), 'Failed to enable mstpd'

    yield  # Run the test

    await asyncio.gather(*[dent.run_cmd(f'cp {backup} {conf}') for dent in dent_devices])


@pytest_asyncio.fixture()
async def enable_mstpd(testbed):
    async for _ in _configure_mstpd(testbed, True):
        yield


@pytest_asyncio.fixture()
async def disable_mstpd(testbed):
    async for _ in _configure_mstpd(testbed, False):
        yield
