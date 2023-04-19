import pytest
import asyncio

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ethtool.ethtool import Ethtool

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_dev_groups_from_config,
    tgen_utils_traffic_generator_connect,
    tgen_utils_get_loss,
    tgen_utils_update_l1_config,
    tgen_utils_clear_traffic_items
)

from dent_os_testbed.utils.test_utils.tb_utils import tb_get_qualified_ports

pytestmark = [pytest.mark.suite_functional_l1,
              pytest.mark.asyncio,
              pytest.mark.usefixtures('cleanup_bridges', 'cleanup_tgen')]


@pytest.mark.parametrize('speed , duplex',
                         [
                            pytest.param(10, 'full'),
                            pytest.param(10, 'half'),
                            pytest.param(100, 'full'),
                            pytest.param(100, 'half'),
                            pytest.param(1000, 'full'),
                            pytest.param(10000, 'full'),
                         ])
async def test_l1_forced_speed_(testbed, speed, duplex):
    """
    Test Name: L1: forced speed
    Test Suite: suite_functional_l1
    Test Overview: Verify forced speed, duplex configuration
    Test Procedure:
    1. Create bridge entity
    2. Enslave ports to the created bridge entity
    3. Configure dut ports:
        speed -> speed
        autoneg -> off
        advertise -> off
       Configure ixia ports:
        speed -> speed
        autoneg -> off
    4. Verify port duplex and speed per was configured
    5. Set up traffic rate according to duplex mode
    6. Send traffic
    7. Verify no traffic loss
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        print('The testbed does not have enough dent with tgen connections')
        return
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1][:2]

    speed_ports = await tb_get_qualified_ports(dent_dev, ports, speed, duplex)

    # 1. Create bridge entity
    out = await IpLink.add(input_data=[{device_host_name: [{'device': 'br0', 'type': 'bridge'}]}])
    assert out[0][device_host_name]['rc'] == 0, 'Failed creating bridge.'

    out = await IpLink.set(input_data=[{device_host_name: [{'device': 'br0', 'operstate': 'up'}]}])
    assert out[0][device_host_name]['rc'] == 0, "Verify that bridge set to 'UP' state."

    # 2. Enslave ports to the created bridge entity
    out = await IpLink.set(input_data=[{device_host_name: [{
        'device': port,
        'operstate': 'up',
        'master': 'br0'
    } for port in ports]}])
    assert out[0][device_host_name]['rc'] == 0, 'Failed setting link to state UP.'

    # 3. Configure dut ports
    out = await Ethtool.set(input_data=[{device_host_name: [{
        'devname': port,
        'speed': speed,
        'autoneg': 'off',
        'duplex': duplex} for port in ports]}])
    assert out[0][device_host_name]['rc'] == 0, 'Failed setting port duplex, speed.'

    dev_groups = tgen_utils_dev_groups_from_config(
        [{'ixp': tg_ports[0], 'ip': '100.1.1.2', 'gw': '100.1.1.6', 'plen': 24, },
         {'ixp': tg_ports[1], 'ip': '100.1.1.3', 'gw': '100.1.1.6', 'plen': 24}])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    #   Configure ixia ports
    await tgen_utils_update_l1_config(tgen_dev, tg_ports, speed=speed, autoneg=False, duplex=duplex)
    await asyncio.sleep(20)  # wait needed in case port was down before

    # 4. Verify port duplex and speed was configured
    for port in ports:
        out = await Ethtool.show(input_data=[{device_host_name: [{'devname': port}]}],  parse_output=True)
        assert speed == int(out[0][device_host_name]['parsed_output']['speed'][:-4]), 'Failed speed test'
        assert duplex.capitalize() == out[0][device_host_name]['parsed_output']['duplex'], 'Failed duplex test'

    supported_speed_ports = [name for name in speed_ports.keys()]
    first_port_index = ports.index(supported_speed_ports[0])
    second_port_index = ports.index(supported_speed_ports[1])

    traffic_loss = {}
    streams = {
        f'{tg_ports[first_port_index]} --> {tg_ports[second_port_index]}': {
            'type': 'ethernet',
            'ep_source': ports[first_port_index],
            'ep_destination': ports[second_port_index],
            'frame_rate_type': 'line_rate',
            'rate': 100
        },
        f'{tg_ports[second_port_index]} --> {tg_ports[first_port_index]}': {
            'type': 'ethernet',
            'ep_source': ports[second_port_index],
            'ep_destination': ports[first_port_index],
            'frame_rate_type': 'line_rate',
            'rate': 100
        }
    }

    # 5. Set up traffic according to duplex mode
    if duplex.capitalize() == 'Half':
        for stream_name, stream in streams.items():

            await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams={stream_name: stream})
            # 6. Send traffic to rx_ports
            await tgen_utils_start_traffic(tgen_dev)
            await asyncio.sleep(1)
            await tgen_utils_stop_traffic(tgen_dev)

            stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
            for row in stats.Rows:
                traffic_loss[stream_name] = (tgen_utils_get_loss(row))
            await tgen_utils_clear_traffic_items(tgen_dev)
    else:
        await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

        # 6. Send traffic to rx_ports
        await tgen_utils_start_traffic(tgen_dev)
        await asyncio.sleep(1)
        await tgen_utils_stop_traffic(tgen_dev)

        stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
        for row in stats.Rows:
            traffic_loss[row['Traffic Item']] = tgen_utils_get_loss(row)

    # 7. Verify no traffic loss on rx ports
    for stream, loss in traffic_loss.items():
        assert loss == 0.000, f'No traffic for traffic item {stream}: expected 0.000 got : {loss}'
