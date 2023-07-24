import pytest_asyncio
import pytest

from dent_os_testbed.lib.interfaces.interface import Interface

from dent_os_testbed.utils.test_utils.tgen_utils import tgen_utils_get_dent_devices_with_tgen

from dent_os_testbed.test.test_suite.functional.ifupdown2.ifupdown2_utils import (
    IFUPDOWN_CONF, IFUPDOWN_BACKUP,
    INTERFACES_FILE,
)


async def _apply_config(dent_dev, fields, config_file=IFUPDOWN_CONF):
    # Prep env and change it
    opts = [f's~^{k}=.*~{k}={v}~' for k, v in fields.items()]
    rc, _ = await dent_dev.run_cmd(f'sed -i -E "{"; ".join(opts)}" {config_file}')
    return rc


async def _copy(dent_dev, src, dst, do_assert=True):
    rc, out = await dent_dev.run_cmd(f'cp {src} {dst}', sudo=True)
    if do_assert:
        assert not rc, f'Failed to copy.\n{out}'


@pytest_asyncio.fixture()
async def modify_ifupdown_conf(testbed):
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 0)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    defaults = {}
    for dent_dev in dent_devices:
        # Get Default values
        settings = ['template_lookuppath', 'addon_syntax_check', 'default_interfaces_configfile']
        rc, out = await dent_dev.run_cmd(f'cat {IFUPDOWN_CONF}')
        defaults[dent_dev] = {
            setting: line.strip().split('=')[-1]
            for setting in settings
            for line in out.splitlines() if setting in line
        }

        # Make backup's
        await _copy(dent_dev, IFUPDOWN_CONF, IFUPDOWN_BACKUP)
        await _copy(dent_dev, defaults[dent_dev]['default_interfaces_configfile'], INTERFACES_FILE)

    yield _apply_config

    for dent_dev in dent_devices:
        # Restore from backup
        rc = await _apply_config(dent_dev, defaults[dent_dev])
        if rc != 0:
            dent_dev.applog.error(f'Error during apply of ifupdown2 config {rc}')
            await _copy(dent_dev, IFUPDOWN_BACKUP, IFUPDOWN_CONF, do_assert=False)

        out = await Interface.reload(input_data=[{dent_dev.host_name: [{'options': '-a -v'}]}])
        assert out[0][dent_dev.host_name]['rc'] == 0, 'Failed to reload config'
