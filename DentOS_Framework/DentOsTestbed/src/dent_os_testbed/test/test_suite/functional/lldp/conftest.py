import pytest
import pytest_asyncio

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
)
from dent_os_testbed.utils.test_utils.tb_utils import tb_device_check_services

from dent_os_testbed.lib.lldp.lldp import Lldp
from dent_os_testbed.lib.os.service import Service


@pytest_asyncio.fixture()
async def check_and_restore_lldp_service(testbed):
    """
    Check if lldp.service is running, start if it isnt running and restore default lldp settings
    """
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 0)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    dev_name = dent_devices[0].host_name
    dut_ports = tgen_dev.links_dict[dev_name][1]
    service = 'lldpd.service'

    try:
        result = await tb_device_check_services(dent_dev, None, True, healthy_services=[service])
        assert result.get(service).get('status') == 'running', \
            f'Unexpected {service} status expected running actual {result.get(service).get("status")}'
    except AssertionError:
        out = await Service.restart(input_data=[{dev_name: [{'name': service}]}])
        assert not out[0][dev_name]['rc'], f'Failed to restart service {service}.\n{out}'

    # Collect running LLDP configuration
    out = await Lldp.show_lldpcli(
        input_data=[{dev_name: [
            {'running-configuration': '', 'cmd_options': '-f json'}]}], parse_output=True)
    assert not out[0][dev_name]['rc'], f'Failed to show LLDP neighbors.\n{out}'
    default_lldp_setup = out[0][dev_name]['parsed_output']['configuration']['config']
    default_state = 'rx-and-tx'

    yield

    # Restore default LLDP settings
    out = await Lldp.configure(
        input_data=[{dev_name: [
            {'interface': port, 'ports': '', 'lldp': '', 'status': default_state} for port in dut_ports]}])
    assert not out[0][dev_name]['rc'], f'Failed to configure lldp status on port {dut_ports}.\n{out}'

    out = await Lldp.show_lldpcli(
        input_data=[{dev_name: [
            {'running-configuration': '', 'cmd_options': '-f json'}]}], parse_output=True)
    assert not out[0][dev_name]['rc'], f'Failed to show LLDP neighbors.\n{out}'
    actual_lldp_setup = out[0][dev_name]['parsed_output']['configuration']['config']

    if actual_lldp_setup['tx-delay'] != default_lldp_setup['tx-delay']:
        out = await Lldp.configure(
            input_data=[{dev_name: [
                {'lldp': '', 'tx-interval': default_lldp_setup['tx-delay']}]}])
        assert not out[0][dev_name]['rc'], f'Failed to configure LLDP tx-interval.\n{out}'

    if actual_lldp_setup['tx-hold'] != default_lldp_setup['tx-hold']:
        out = await Lldp.configure(
            input_data=[{dev_name: [
                {'lldp': '', 'tx-hold': default_lldp_setup['tx-hold']}]}])
        assert not out[0][dev_name]['rc'], f'Failed to configure LLDP tx-hold.\n{out}'

    if actual_lldp_setup['bond-slave-src-mac-type'] != default_lldp_setup['bond-slave-src-mac-type']:
        out = await Lldp.configure(
            input_data=[{dev_name: [
                {'system': f'bond-slave-src-mac-type {default_lldp_setup["bond-slave-src-mac-type"]}'}]}])
        assert not out[0][dev_name]['rc'], f'Failed to configure LLDP tx-hold.\n{out}'
