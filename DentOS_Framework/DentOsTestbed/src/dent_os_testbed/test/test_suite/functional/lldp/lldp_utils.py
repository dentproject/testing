from random import randint
from ipaddress import IPv4Address
from dent_os_testbed.lib.lldp.lldp import Lldp
from dent_os_testbed.utils.test_utils.tb_utils import tb_device_tcpdump

ERR_MSG_RX = 'Expected value {} for {} actual value {}'
ERR_MSG_TX = 'Expected value {} for {} to be in {}'
PORT_TYPE_MAP = {
    1: 'ifalias',
    3: 'mac',
    5: 'ifname',
}


def random_mac():
    return ':'.join(['02'] + [f'{randint(0, 255):02x}' for _ in range(5)])


def get_lldp_stream(tx_port, rx_port, lldp, src_mac='aa:bb:cc:dd:ee:11', rate=2, size=512, count=6, name=1):
    """
    Generate Lldp stream
    Args:
        tx_port (str): Name of Tx port
        rx_port (str): Name of Rx port
        lldp (dict): Dict with lldp params to set
        src_mac (str): Source MAC addr
        rate (int): Rate of stream
        size (int): Pkt size
        count (int): Amount of pkts to send
        name (int): Index to add to stream name
    Returns:
        Dict with lldp stream
    """

    stream = {f'lldp_{name}': {
        'type': 'raw',
        'protocol': 'lldp',
        'ip_source': tx_port,
        'ip_destination': rx_port,
        'srcMac': src_mac,
        'dstMac': '01:80:c2:00:00:0e',
        'rate': rate,
        'frameSize': size,
        'transmissionControlType': 'fixedPktCount',
        'frameCount': count,
        **lldp,
    }}
    return stream


def parse_lldp_pkt(tlvs, sniffed_out):
    """
    Parse sniffed lldp packet into dict with TLVs
    Args:
        tlvs (list): List with TLVs names
        sniffed_out (str): Sniffed lldp packet
    Returns:
        Dict with TLVs names as key and parsed part of pkt as value
    """
    parsed = {}
    sniffed = [i.strip() for i in sniffed_out.splitlines()]

    for tlv in tlvs:
        for line in sniffed:
            if line.startswith(tlv):
                result = []
                index = sniffed.index(line) + 1
                result.append(line)
                while 'TLV' not in sniffed[index]:
                    result.append(sniffed[index])
                    index += 1
                parsed[tlv] = ' '.join(result)
                break
    return parsed


async def get_lldp_statistic(dev_name, port, stats='tx'):
    """
    Get lldp statistics from port
    Args:
        dev_name (str): Dut name
        port (str): Dut port name
        stats (str): Which stats to get tx/rx
    Returns:
        lldp statistic for port
    """
    out = await Lldp.show_lldpcli(
        input_data=[{dev_name: [
            {'interface': port, 'statistics': '', 'ports': '', 'cmd_options': '-f json'}]}], parse_output=True)
    assert not out[0][dev_name]['rc'], f'Failed to show LLDP statistics.\n{out}'
    return int(out[0][dev_name]['parsed_output']['lldp']['interface'][port][stats][stats])


async def get_neighbors_info(dev_name, port):
    """
    Get lldp neighbors information
    Args:
        dev_name (str): Dut name
        port (str): Dut port name
    Returns:
        Dict with lldp neighbor info
    """
    out = await Lldp.show_lldpcli(
        input_data=[{dev_name: [
            {'interface': port, 'neighbors': '', 'ports': '', 'cmd_options': '-f json'}]}], parse_output=True)
    assert not out[0][dev_name]['rc'], f'Failed to show LLDP neighbors.\n{out}'
    return out[0][dev_name]['parsed_output']['lldp']


async def verify_rx_lldp_fields(dev_name, dut_port, chassis, port, port_type, ttl,
                                sys_name=None, port_desc=None, sys_desc=None,
                                mgmt_ip=None, capabilities=None):
    """
    Verify lldp neighbor info is as expected
    Args:
        dev_name (str): Dut name
        dut_port (str): Dut port name
        chassis (str): Expected chassis value
        port (str): Expected port value
        port_type (int): Expected port_type
        ttl (int): Expected ttl value
        sys_name (str): Expected system name
        port_desc (str): Expected port description
        sys_desc (str): Expected system description
        mgmt_ip (str): Expected Managment ip address
        capability (dict): Expected Capabilities
    """
    out = await get_neighbors_info(dev_name, port=dut_port)
    chassis_info = out['interface'][dut_port]['chassis']
    if sys_name:
        chassis_info = out['interface'][dut_port]['chassis'][sys_name]
    port_info = out['interface'][dut_port]['port']

    assert chassis_info['id']['type'] == 'mac', ERR_MSG_RX.format('mac', 'chassis_type', chassis_info['id']['type'])
    assert chassis_info['id']['value'] == chassis, ERR_MSG_RX.format(chassis, 'chassis', chassis_info['id']['value'])
    assert port_info['id']['type'] == PORT_TYPE_MAP[port_type], ERR_MSG_RX.format(PORT_TYPE_MAP[port_type], 'port_type', port_info['id']['type'])
    assert port_info['id']['value'] == port, ERR_MSG_RX.format(port, 'port', port_info['id']['value'])
    assert int(port_info['ttl']) == ttl, ERR_MSG_RX.format(ttl, 'ttl', port_info['ttl'])

    if port_desc:
        assert port_info['descr'] == port_desc, ERR_MSG_RX.format(port_desc, 'port_desc', port_info['descr'])
    if sys_name:
        assert sys_name in list(out['interface'][dut_port]['chassis'].keys()), \
            ERR_MSG_RX.format(sys_name, 'sys_name', out['interface'][dut_port]['chassis'].keys())
    if sys_desc:
        assert chassis_info['descr'] == sys_desc, ERR_MSG_RX.format(sys_desc, 'sys_desc', chassis_info['descr'])
    if mgmt_ip:
        assert chassis_info['mgmt-ip'] == mgmt_ip, ERR_MSG_RX.format(mgmt_ip, 'mgmt-ip', chassis_info['mgmt-ip'])
    if capabilities:
        res_capabilities = {capab['type']: capab['enabled'] for capab in chassis_info['capability']}
        for cap, enabled in capabilities.items():
            assert res_capabilities[cap] == enabled, \
                ERR_MSG_RX.format(enabled, 'capabilities', res_capabilities[cap])


async def verify_tx_lldp_fields(dev_name, dent_dev, port, interval, optional_tlvs=False):
    """
    Verify lldp pkts were transmitted and TLVs are as configured on DUT
    Args:
        dev_name (str): Dut name
        dent_dev (object): Dut object
        port (str): Dut port name
        interval (int): Timeout to sniff lldp pkt
        optional_tlvs (bool): If True check both mandatory and optional TLVs
    """
    out = await Lldp.show_lldpcli(
        input_data=[{dev_name: [
            {'interfaces': '', 'interface': port, 'ports': '', 'cmd_options': '-f json'}]}], parse_output=True)
    assert not out[0][dev_name]['rc'], f'Failed to LLDP port info.\n{out}'
    lldp_info = out[0][dev_name]['parsed_output']['lldp']['interface'][port]

    _, out = await dent_dev.run_cmd('uname -n')
    sys_name = out.strip()

    chassis_info = lldp_info['chassis'][sys_name]['id']
    port_info = lldp_info['port']['id']
    ttl = lldp_info['ttl']['ttl']

    res = await tb_device_tcpdump(dent_dev, port, 'ether proto 0x88cc -vnne', timeout=interval + 1, dump=True)
    mandatory_tlvs = ['Chassis ID TLV', 'Port ID TLV', 'Time to Live TLV']
    optional_tlvs = ['System Name TLV', 'System Description TLV', 'System Capabilities TLV',
                     'Management Address TLV', 'Port Description TLV']
    tlvs = mandatory_tlvs if not optional_tlvs else mandatory_tlvs + optional_tlvs
    parsed_lldp = parse_lldp_pkt(tlvs, res)

    assert f'Subtype {chassis_info["type"].upper()}' in parsed_lldp[tlvs[0]], \
        ERR_MSG_TX.format(chassis_info['type'].upper(), 'Chassis TLV Subtype', parsed_lldp[tlvs[0]])
    assert chassis_info['value'] in parsed_lldp[tlvs[0]], \
        ERR_MSG_TX.format(chassis_info['value'], 'Chassis TLV Value', parsed_lldp[tlvs[0]])
    assert f'Subtype {port_info["type"].upper()}' in parsed_lldp[tlvs[1]], \
        ERR_MSG_TX.format(port_info['type'].upper(), 'Port TLV Subtype', parsed_lldp[tlvs[1]])
    assert port_info['value'] in parsed_lldp[tlvs[1]], \
        ERR_MSG_TX.format(port_info['value'], 'Port TLV Value', parsed_lldp[tlvs[1]])
    assert str(ttl) in parsed_lldp[tlvs[2]], \
        ERR_MSG_TX.format(str(ttl), tlvs[2], parsed_lldp[tlvs[2]])

    if optional_tlvs:
        system_name = list(lldp_info['chassis'].keys())
        sys_descr = lldp_info['chassis'][sys_name]['descr']
        port_descr = lldp_info['port']['descr']
        capability = lldp_info['chassis'][sys_name]['capability']
        mgmt = lldp_info['chassis'][sys_name]['mgmt-ip']

        assert system_name[0] in parsed_lldp[optional_tlvs[0]], ERR_MSG_TX.format(system_name[0], optional_tlvs[0], parsed_lldp[optional_tlvs[0]])
        assert sys_descr in parsed_lldp[optional_tlvs[1]], ERR_MSG_TX.format(sys_descr, optional_tlvs[1], parsed_lldp[optional_tlvs[1]])
        for cap in capability:
            cap_name = cap['type'].upper() if cap['type'] == 'Wlan' else cap['type']
            assert cap_name in parsed_lldp[optional_tlvs[2]], ERR_MSG_TX.format(cap_name, optional_tlvs[2], parsed_lldp[optional_tlvs[2]])

            if cap['enabled']:
                assert cap_name in parsed_lldp[optional_tlvs[2]].split('Enabled Capabilities')[-1], \
                    ERR_MSG_TX.format(cap_name, 'System Enabled Capabilities', parsed_lldp[optional_tlvs[2]].split('Enabled Capabilities')[-1])

        assert mgmt[0] in parsed_lldp[optional_tlvs[3]], \
            ERR_MSG_TX.format(mgmt[0], optional_tlvs[3], parsed_lldp[optional_tlvs[3]])
        assert port_descr in parsed_lldp[optional_tlvs[4]], \
            ERR_MSG_TX.format(port_descr, optional_tlvs[4], parsed_lldp[optional_tlvs[4]])


def build_lldp_optional_pkt(chassis, port, ttl, port_desc=None, sys_name=None,
                            sys_desc=None, capability=None, enabled_capability=None,
                            mgmt_ip=None):
    """
    Build an hex output of lldp packet with optional fields
    Args:
        chassis (str): Chassis Mac address
        port (str): Port Mac address
        ttl (int): Ttl value to set
        port_desc (str): Port description
        sys_name (str): System name
        sys_desc (str): System description
        capability (int): Capabilities value to set (will be converted to hex)
        enabled_capability (int): Enabled capabilities value to set (will be converted to hex)
        mgmt_ip (str): Managment ip address to advertise
    Returns:
        String which contains hex representation of lldp pkt
    """
    lldp_mandatory = '02{chassis_len}04{chassis}04{port_len}03{port}0602{ttl}'
    lldp_optional = ''

    # Mandatory Fields
    chassis_len = hex(len(chassis.replace(':', '')) // 2 + 1)[2:].zfill(2)
    chassis_var = chassis.replace(':', '')
    port_len = hex(len(port.replace(':', '')) // 2 + 1)[2:].zfill(2)
    port_var = port.replace(':', '')
    ttl = hex(ttl)[2:].zfill(4)

    # Optional Fields
    if port_desc:
        port_description = port_desc.encode().hex()
        port_desc_len = hex(len(port_description) // 2)[2:]
        port_desc = port_description
        lldp_optional += ''.join(['08', port_desc_len, port_desc])
    if sys_name:
        system_name = sys_name.encode().hex()
        sys_name_len = hex(len(system_name) // 2)[2:].zfill(2)
        sys_name = system_name
        lldp_optional += ''.join(['0A', sys_name_len, sys_name])
    if sys_desc:
        system_description = sys_desc.encode().hex()
        sys_desc_len = hex(len(system_description) // 2)[2:]
        sys_desc = system_description
        lldp_optional += ''.join(['0C', sys_desc_len, sys_desc])
    if capability and enabled_capability:
        capability = hex(capability)[2:].zfill(4)
        enabled_capability = hex(enabled_capability)[2:].zfill(4)
        lldp_optional += ''.join(['0E04', capability, enabled_capability])
    if mgmt_ip:
        mgmt_ip = IPv4Address(mgmt_ip).packed.hex()
        lldp_optional += ''.join(['100C0501', mgmt_ip, '02000186A000'])

    lldp_mandatory = lldp_mandatory.format(chassis_len=chassis_len,
                                           chassis=chassis_var,
                                           port_len=port_len,
                                           port=port_var,
                                           ttl=ttl)

    return lldp_mandatory + lldp_optional + '0000'
