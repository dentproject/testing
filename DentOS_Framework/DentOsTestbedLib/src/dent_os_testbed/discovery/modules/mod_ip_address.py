# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# generated using file ./gen/model/dent/network/ip/address.yaml
#
# DONOT EDIT - generated by diligent bots

from dent_os_testbed.discovery.Module import Module
from dent_os_testbed.lib.ip.ip_address import IpAddress


class IpAddressMod(Module):
    """
    """

    def set_ip_address_info(self, src, dst):

        for i, ip_address_info in enumerate(src):
            if 'family' in ip_address_info: dst[i].family = ip_address_info.get('family')
            if 'local' in ip_address_info: dst[i].local = ip_address_info.get('local')
            if 'prefixlen' in ip_address_info: dst[i].prefixlen = ip_address_info.get('prefixlen')
            if 'scope' in ip_address_info: dst[i].scope = ip_address_info.get('scope')
            if 'label' in ip_address_info: dst[i].label = ip_address_info.get('label')
            if 'valid_life_time' in ip_address_info: dst[i].valid_life_time = ip_address_info.get('valid_life_time')
            if 'preferred_life_time' in ip_address_info: dst[i].preferred_life_time = ip_address_info.get('preferred_life_time')

    def set_ip_address(self, src, dst):

        for i, ip_address in enumerate(src):
            if 'ifindex' in ip_address: dst[i].ifindex = ip_address.get('ifindex')
            if 'ifname' in ip_address: dst[i].ifname = ip_address.get('ifname')
            if 'mtu' in ip_address: dst[i].mtu = ip_address.get('mtu')
            if 'qdisc' in ip_address: dst[i].qdisc = ip_address.get('qdisc')
            if 'operstate' in ip_address: dst[i].operstate = ip_address.get('operstate')
            if 'group' in ip_address: dst[i].group = ip_address.get('group')
            if 'txqlen' in ip_address: dst[i].txqlen = ip_address.get('txqlen')
            if 'link_type' in ip_address: dst[i].link_type = ip_address.get('link_type')
            if 'address' in ip_address: dst[i].address = ip_address.get('address')
            if 'broadcast' in ip_address: dst[i].broadcast = ip_address.get('broadcast')
            if 'promiscuity' in ip_address: dst[i].promiscuity = ip_address.get('promiscuity')
            if 'min_mtu' in ip_address: dst[i].min_mtu = ip_address.get('min_mtu')
            if 'max_mtu' in ip_address: dst[i].max_mtu = ip_address.get('max_mtu')
            if 'num_tx_queues' in ip_address: dst[i].num_tx_queues = ip_address.get('num_tx_queues')
            if 'num_rx_queues' in ip_address: dst[i].num_rx_queues = ip_address.get('num_rx_queues')
            if 'gso_max_size' in ip_address: dst[i].gso_max_size = ip_address.get('gso_max_size')
            if 'gso_max_segs' in ip_address: dst[i].gso_max_segs = ip_address.get('gso_max_segs')
            self.set_ip_address_info(ip_address.get('addr_info', []), dst[i].addr_info)
            if 'prefix' in ip_address: dst[i].prefix = ip_address.get('prefix')
            if 'peer' in ip_address: dst[i].peer = ip_address.get('peer')
            if 'anycast' in ip_address: dst[i].anycast = ip_address.get('anycast')
            if 'label' in ip_address: dst[i].label = ip_address.get('label')
            if 'scope' in ip_address: dst[i].scope = ip_address.get('scope')
            if 'dev' in ip_address: dst[i].dev = ip_address.get('dev')
            if 'options' in ip_address: dst[i].options = ip_address.get('options')

    async def discover(self):
        # need to get device instance to get the data from
        #
        for i, dut in enumerate(self.report.duts):
            if not dut.device_id: continue
            dev = self.ctx.devices_dict[dut.device_id]
            if dev.os == 'ixnetwork' or not await dev.is_connected():
                print('Device not connected skipping ip_address discovery')
                continue
            print('Running ip_address Discovery on ' + dev.host_name)
            out = await IpAddress.show(
                input_data=[{dev.host_name: [{'dut_discovery': True}]}],
                device_obj={dev.host_name: dev},
                parse_output=True
            )
            if out[0][dev.host_name]['rc'] != 0:
                print(out)
                print('Failed to get ip_address')
                continue
            if 'parsed_output' not in out[0][dev.host_name]:
                print('Failed to get parsed_output ip_address')
                print(out)
                continue
            self.set_ip_address(out[0][dev.host_name]['parsed_output'], self.report.duts[i].network.layer3.addresses)
            print('Finished ip_address Discovery on {} with {} entries'.format(dev.host_name, len(self.report.duts[i].network.layer3.addresses)))
