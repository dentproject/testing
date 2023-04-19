from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan
from dent_os_testbed.lib.ip.ip_link import IpLink


async def configure_bridge_setup(device, dut_ports, default_pvid=0):
    """
    Configures bridge on "device"; enslaves "dut_ports" to bridge. Set bridge, ports to UP.

    Args:
        device (str): Dent device host_name
        dut_ports (list): List of ports of the dent device
        default_pvid (int): Bridge default pvid. Defaults to 0
    """

    out = await IpLink.add(input_data=[{device: [{
        'device': 'br0',
        'type': 'bridge',
        'vlan_filtering': 1,
        'vlan_default_pvid': default_pvid}]
    }])
    assert out[0][device]['rc'] == 0, 'Failed creating bridge.'

    await IpLink.set(input_data=[{device: [{'device': 'br0', 'operstate': 'up'}]}])
    assert out[0][device]['rc'] == 0, 'Failed setting bridge to state UP.'

    out = await IpLink.set(input_data=[{device: [{
        'device': port,
        'operstate': 'up',
        'master': 'br0'
    } for port in dut_ports]}])
    assert out[0][device]['rc'] == 0, 'Failed setting link to state UP.'


async def configure_vlan_setup(device, port_vlan_map, dut_ports):
    """
    Configures vlan on device ports

    Args:
        device (str): Dent device host_name
        dut_ports (list): List of ports of the dent device.
        port_vlan_map (tuple): Tuple of dicts. Ex:
            port_vlan_map = (
                {"port": 0, "settings": [{"vlan": 2, "untagged": False, "pvid": False},)
    """

    for config in port_vlan_map:
        port = dut_ports[config['port']]
        out = await BridgeVlan.add(input_data=[{device: [{
            'device': port,
            'vid': setting['vlan'],
            'pvid': setting['pvid'],
            'untagged': setting['untagged']
        } for setting in config['settings']]}])

        assert out[0][device]['rc'] == 0, f'Vlan: {config["settings"]["vlan"]}  is not added to link: {port}.'


def get_traffic_port_vlan_mapping(streams, port_vlan_map, tg_ports, tx_port=0, default_pvid=0):
    """
    Generate stream to rx interface map

    Args:
       streams (dict): Traffic streams passed to tgen
       tg_ports (list): List of tgen ports
       port_vlan_map (tuple): Tuple of dicts. Ex:
            port_vlan_map = (
                {"port": 0, "settings": [{"vlan": 2, "untagged": False, "pvid": False},)
       tx_port (int): Transmitting port
       default_pvid (int): Default PVID on bridge

    Returns:
        Dictionary. Relation of streams and rx ports
            ti_to_rx_port_map = {"stream": [port1, port2..]}
    """

    ti_to_rx_port_map = {k: [] for k in list(streams.keys())}
    for stream_name, stream in streams.items():
        vid = stream.get('vlanID', None)
        #  If no vlanID in stream apply pvid of transmitting port
        if not vid:
            for item in port_vlan_map[tx_port]['settings']:
                if item['pvid'] is True:
                    vid = item['vlan']
                    continue
        for port in port_vlan_map:
            for setting in port['settings']:
                if vid == setting['vlan'] or vid == default_pvid:
                    ti_to_rx_port_map[stream_name].append(tg_ports[port['port']])
    return ti_to_rx_port_map
