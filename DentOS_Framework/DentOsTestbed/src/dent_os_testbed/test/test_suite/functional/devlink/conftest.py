import pytest
import pytest_asyncio


from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
)


BASH_UTILS = '''
# Sniff pkt for specified/any interface and return amount of sniffed packets
tcpdump_cpu_traps_rate()
{
    local IFACE="any"
    if [ $# -ge 1 ]; then IFACE=$1; fi
    timeout 1.06 tcpdump -i $IFACE &> xx; cat xx | grep -Eo "[0-9]+ packets received by filter" | cut -d " " -f 1; rm xx
}

# Get average CPU rate by tcpdump
tcpdump_cpu_traps_rate_avg()
{
    local start_index=0
    local end=25
    local counter=0
    for((num=start_index; num<=end; num++)); do
       local temp=$(tcpdump_cpu_traps_rate $1)
       sleep 1
       counter=$((counter+temp))
    done
    echo $((counter/6))
}

# Get CPU rate by reading traps debug counters
get_cpu_traps_rate_code()
{
    R1=`cat /sys/kernel/debug/prestera/$2_counters/traps/cpu_code_$1_stats | tr -d "\\0"`
    sleep 1
    R2=`cat /sys/kernel/debug/prestera/$2_counters/traps/cpu_code_$1_stats | tr -d "\\0"`
    RXPPS=`expr $R2 - $R1`
    echo $RXPPS
}

# Get average CPU rate by reading traps debug counters
get_cpu_traps_rate_code_avg()
{
    local start_index=0
    local end=9
    local counter=0
    for((num=start_index; num<=end; num++)); do
       local temp=$(get_cpu_traps_rate_code $1 $2)
       sleep 1
       counter=$((counter+temp))
    done
    echo $((counter/10))
}

# Get CPU rate by reading devlink trap counters
get_devlink_cpu_traps_rate()
{
    R1=`devlink -vs trap show pci/0000:01:00.0 trap $1 | grep -o "packets.*" | cut -d " " -f 2`
    sleep 1
    R2=`devlink -vs trap show pci/0000:01:00.0 trap $1 | grep -o "packets.*" | cut -d " " -f 2`
    RXPPS=`expr $R2 - $R1`
    echo $RXPPS
}

# Get average CPU rate by reading devlink trap counters
get_devlink_cpu_traps_rate_avg()
{
    local start_index=0
    local end=9
    local counter=0
    for((num=start_index; num<=end; num++)); do
       local temp=$(get_devlink_cpu_traps_rate $1)
       sleep 1
       counter=$((counter+temp))
    done
    echo $((counter/10))
}

# Get drop counters rate by reading hardware drop counters
get_drops_rate_code()
{
    R1=`cat /sys/kernel/debug/prestera/hw_counters/drops/cpu_code_$1_stats | tr -d "\\0"`
    sleep 1
    R2=`cat /sys/kernel/debug/prestera/hw_counters/drops/cpu_code_$1_stats | tr -d "\\0"`
    RXPPS=`expr $R2 - $R1`
    echo $RXPPS
}

# Get average drop rate by reading hardware drop counters
get_drops_rate_code_avg()
{
    local start_index=0
    local end=9
    local counter=0
    for((num=start_index; num<=end; num++)); do
        local temp=$(get_drops_rate_code $1)
        sleep 1
        counter=$((counter+temp))
    done
    echo $((counter/10))
}
'''


@pytest_asyncio.fixture()
async def define_bash_utils(testbed):
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    func_list = ['tcpdump_cpu_traps_rate', 'tcpdump_cpu_traps_rate_avg', 'get_cpu_traps_rate_code',
                 'get_cpu_traps_rate_code_avg', 'get_devlink_cpu_traps_rate', 'get_devlink_cpu_traps_rate_avg',
                 'get_drops_rate_code', 'get_drops_rate_code_avg']
    listed_funcs = ' '.join(func_list)
    bashrc = '/root/.bashrc'
    backup = '/root/.bashrc.bak'

    res, _ = await dent_dev.run_cmd(f'type {listed_funcs} > /dev/null 2>&1')
    if res:
        dent_dev.applog.info(f'Bash func isnt defined: \n{listed_funcs} \nDefining func in .bashrc')
        rc, out = await dent_dev.run_cmd(f'cp {bashrc} {backup}', sudo=True)
        rc, out = await dent_dev.run_cmd(f"echo '{BASH_UTILS}' >> {bashrc}", sudo=True)
        try:
            assert not rc
        except AssertionError:
            _, _ = await dent_dev.run_cmd(f'mv {backup} {bashrc}', sudo=True)
            pytest.skip('Skiping test due defining func failed with rc {}'.format(rc))

    yield

    _, _ = await dent_dev.run_cmd(f'mv {backup} {bashrc}', sudo=True)


@pytest_asyncio.fixture()
async def disable_sct(testbed):
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    sct_path = '/sys/kernel/debug/prestera/sct'

    """
    all_unspecified_cpu_opcodes: 100 (pps)\n\0
    sct_acl_trap_queue_0: 4000 (pps)\n\0
    sct_acl_trap_queue_1: 4000 (pps)\n\0
    """
    rc, static_traps = await dent_dev.run_cmd(f'cat {sct_path}/*')
    assert not rc, 'Failed to get default SCT values'

    restore_cmd = []
    for trap in static_traps.split('\n\0'):
        try:
            key, val = trap.split(': ')
        except ValueError:
            continue
        restore_cmd.append(f'echo {val.split(" ")[0]} > {sct_path}/{key}')

    # disable SCT
    rc, _ = await dent_dev.run_cmd(f'for sct in `find {sct_path}/*`; do echo 0 > $sct; done')
    if rc != 0:
        # restore old values in case some of them were changed
        await dent_dev.run_cmd(' && '.join(restore_cmd))
        raise AssertionError('Failed to disable SCT')

    yield  # Run the test

    # restore old values
    await dent_dev.run_cmd(' && '.join(restore_cmd))
