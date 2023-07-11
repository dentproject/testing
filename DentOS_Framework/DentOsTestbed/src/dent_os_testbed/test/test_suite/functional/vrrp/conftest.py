import pytest_asyncio

from dent_os_testbed.lib.os.service import Service


KEEPALIVE_CONF = '/etc/keepalived/keepalived.conf'
TEMPLATE = """
global_defs {{
    vrrp_garp_master_refresh 60
}}

vrrp_instance vrrp_{vr_id} {{
    state {state}
    interface {dev}
    virtual_router_id {vr_id}
    priority {prio}
    version 3
    use_vmac
    vmac_xmit_base
    virtual_ipaddress {{
        {vr_ip}
    }}
    {additional_opts}
}}
"""


@pytest_asyncio.fixture()
async def configure_vrrp():
    devs_to_clear = set()

    async def apply_config(dent_dev, state, dev, prio, vr_ip, vr_id=40,
                           additional_opts=None, apply=True, clear=True):
        devs_to_clear.add(dent_dev)
        dent = dent_dev.host_name
        opts = '\n'.join(additional_opts) if type(additional_opts) is list else ''
        append = '>' if clear else '>>'

        rc, _ = await dent_dev.run_cmd(f"""
            cat << EOF {append} {KEEPALIVE_CONF}
                {TEMPLATE.format(state=state, dev=dev, prio=prio, vr_ip=vr_ip,
                                 vr_id=vr_id, additional_opts=opts)}
            \nEOF""")
        assert rc == 0, f'Failed to add VRRP config on DUT {dent}'

        if apply:
            out = await Service.restart(input_data=[{
                dent: [{'name': 'keepalived'}]
            }])
            assert out[0][dent]['rc'] == 0, f'Failed to restart keepalive service on DUT {dent}'

    yield apply_config  # Run the test

    for dent_dev in devs_to_clear:
        rc, _ = await dent_dev.run_cmd(f'rm {KEEPALIVE_CONF}')
        if rc != 0:
            dent_dev.applog.error(f'Failed to remove {KEEPALIVE_CONF}')

        out = await Service.stop(input_data=[{
            dent_dev.host_name: [{'name': 'keepalived'}]
        }])
        if out[0][dent_dev.host_name]['rc'] != 0:
            dent_dev.applog.error('Failed to stop keepalive service')
