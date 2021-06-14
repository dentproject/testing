###################################################################################
#	Marvell GPL License
#	
#	If you received this File from Marvell, you may opt to use, redistribute and/or
#	modify this File in accordance with the terms and conditions of the General
#	Public License Version 2, June 1991 (the "GPL License"), a copy of which is
#	available along with the File in the license.txt file or by writing to the Free
#	Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 or
#	on the worldwide web at http://www.gnu.org/licenses/gpl.txt.
#	
#	THE FILE IS DISTRIBUTED AS-IS, WITHOUT WARRANTY OF ANY KIND, AND THE IMPLIED
#	WARRANTIES OF MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE ARE EXPRESSLY
#	DISCLAIMED.  The GPL License provides additional details about this warranty
#	disclaimer.
###################################################################################

import ctypes
import distutils.sysconfig
from UnifiedTG.Unified.Utils import Converter
import ipaddress

import gc


# We use ctypes moule  to access our unreachable objects by memory address.
class PyObject(ctypes.Structure):
    _fields_ = [("refcnt", ctypes.c_long)]


#gc.disable()  # Disable generational gc

lst = []
lst.append(lst)

# Store address of the list
lst_address = id(lst)

# Destroy the lst reference
del lst

object_1 = {}
object_2 = {}
object_1['obj2'] = object_2
object_2['obj1'] = object_1

obj_address = id(object_1)

# Destroy references
del object_1, object_2

# Uncomment if you want to manually run garbage collection process
# gc.collect()

# Check the reference count
print(PyObject.from_address(obj_address).refcnt)
print(PyObject.from_address(lst_address).refcnt)
# from geopy import GoogleV3
#
# place = "221b Baker Street, London"
# location = GoogleV3().geocode(place)
#
# print(location.address)
# print(location.location)

# from emoji import emojize
#
# print(emojize(":thumbs_up:"))
#
# PortConfigList = ['slan0','slan1','slan2','slan0']
#
# from collections import Counter
#
# x = Counter(PortConfigList)
# lbname = x.most_common(1)[0][0]
# lblist = [p for p in PortConfigList if p==lbname]
# print()
#ostPortInfo = [p for p in PortConfigList if p.name.lower() == 'slan0']


# tmp = '40'
# x = hex(int(tmp))
# strip = '1.1.1.1'
# xxx = strip#.encode('utf-8')
# xx =


# def foo(bar=[]):        # bar is optional and defaults to [] if not specified
#     bar.append("baz")    # but this line could be problematic, as we'll see...
#     return bar
#
# print(foo())
# print(foo())
# print(foo())

# s = (Converter.uc23(strip))
# x = Converter.intIp2string(Converter.uc23(strip))
# xx = ipaddress.IPv4Address(s)
print ('')
from UnifiedTG.Unified.Utils import Converter
import sys,os
#import asyncio
import time
# x = sys.float_info
# y = sys.long_info

# if False:
#     pass
#
# async def say_after(delay, what):
#     await asyncio.sleep(delay)
#     print(what)
#
# async def main():
#     task1 = asyncio.create_task(
#         say_after(10, 'hello'))
#
#     task2 = asyncio.create_task(
#         say_after(5, 'world'))
#
#     print(f"started at {time.strftime('%X')}")
#
#     # Wait until both tasks are completed (should take
#     # around 2 seconds.)
#     await task1
#     await task2
#
#     print(f"finished at {time.strftime('%X')}")

#asyncio.run(main())

# def is_venv():
#     return (hasattr(sys, 'real_prefix') or
#             (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))
#
#
# xxx= is_venv()
#
# python_location = distutils.sysconfig.get_python_lib()
# python_inc = sys.executable
# x = sys.base_prefix
from UnifiedTG.Unified.Packet import *

# x = PTP()
# string = x.to_string()
# length = 2
# print("")

# import ipaddress
# addr = ipaddress.ip_address(u'::abc:7:def')
# print(addr.exploded)
import os
import sys
import copy
from os.path import exists
#'keyword1': 'foo', 'keyword2': 'bar'
params = {}
params['keyword1'] = 'foo'


x = int('256')

# def test(**data):
#     print('')
#
# test(**params)

# nums = range(100) #or any list, i.e. [0, 1, 2, 3...]
# number_string = ''.join([str(x) for x in nums])
# pl_size = 10
# pl = 'aabb'
# pl = str('{:0<'+str(pl_size)+'}').format(pl)


from UnifiedTG.PacketBuilder.Payload import payload
from pypacker.checksum import crc32_cksum

# x = payload()
#
# """Convert a bytestring to a hex-represenation:
# b'1234' -> '\x31\x32\x33\x34'"""
# def byte2hex(buf):
# 	#buf = b'1234'
# 	return "\\x" + "\\x".join(["%02X" % x for x in buf])
#
#
# x = byte2hex(bytearray([1,2,3]))
#
# p = Packet()
# p.size = 260
# p.l2_proto = TGEnums.L2_PROTO.SNAP
# # mpls_1 =  p.add_mpls_label()
# # p.mpls_labels[mpls_1].label = 123
# # p.mpls_labels[mpls_1].ttl = 20
#
# p.l3_proto = TGEnums.L3_PROTO.IPV4
#p.ethertype = "6000"
# v1 = p.add_vlan()
# p.vlans[v1].vid.value = '5'
# p.l3_proto = TGEnums.L3_PROTO.IPV6
# p.ipv6.destination_ip.value = '3555:5555:6666:6666:7777:7777:8888:8888'
# p.ipv6.source_ip.value = 'FE80:0:0:0:200:FF:FE00:20'
# p.l4_proto = TGEnums.L4_PROTO.UDP
# p.udp.source_port.value = '63'
# p.udp.destination_port.value = '63'
# p.tcp.source_port.value = '80'
# p.tcp.destination_port.value = '23'
# p.data_pattern.type = TGEnums.DATA_PATTERN_TYPE.FIXED
# p.data_pattern.value = 'AABBCC'
# x = p.to_string()
# print("")



# p = Packet()
#
# p.mac.da = '00:00:00:00:00:11'
# p.l2_proto = TGEnums.L2_PROTO.ETHERNETII
# p.l3_proto = TGEnums.L3_PROTO.IPV4
# p.ipv4.source_ip = '2.2.2.2'
#
# x = p.to_string()





# x = DSA_To_CPU()
# #x.Trg_Tagged = 1
# print(x.to_string())
# print()
#
# x = extDSA_To_CPU()
# #x.eVLAN_11_0 = 55
# #x.Src_Trunk_ePort_6_5 = 2
# print(x.to_string())
# print()
#
#
# x = EDSA_To_CPU()
# #x.eVLAN_11_0 = 55
# #x.Src_Trunk_ePort_6_5 = 2
# print(x.to_string())
# print()


# etag1 = E_Tag()
# etag1.E_PCP = 2
# etag1.E_DEI = 1
# etag1.Ingress_E_CID_base = 0x30
# etag1.GRP = 2
# etag1.E_CID_base = 0x15
# etag1.Ingress_E_CID_ext = 0xAA
# etag1.E_CID_ext = 0x66
# x = etag1.to_string()
# print()

# class bitter(object):
#     def __init__(self,size,offset):
#         self.size = size
#         self.offset = offset
#         self.mask = hex(((1 << size)-1) << offset)


#x = bitter(7,13)


# size  = 7
# num = (1<<size)-1
# x = hex(num <<13)
# print(hex(x))
# for i in range(1,14):
#     x = (x << 1)
#     print(hex(x))
# x = x^0x10000
# print(hex(x))
# def shark_path():
#     app_name = 'wireshark.exe'
#     """
#     Check if wireshark available on the system and return path/None
#     """
#     # known_path_list = ['C:\\Program Files\\Wireshark\\']
#     # for p in known_path_list:
#     #     if exists(p):
#     #         return p
#     sys_path_list = os.environ["PATH"].split(';')
#     for p in sys_path_list:
#         if exists(p + app_name):
#             return p
#     return None
#
# shark_path()






# retries = 5
# for i in range(1, retries):
#     pass
#
# from UnifiedTG.Unified.Utils import Converter
#
# z = int('0xFFFF', 16)
#
# y = Converter.convertstring2int('0xFFFF')
# x = Converter.convertstring2int('00:00:00:00:00:01')

# from string import Template
#
# indexOneParam = Template(' [$ix] $param1')
# indexTwoParams = Template(' [$ix] $param1 $param2')
#
# for ix,val in enumerate(['a','b']):
#     x = indexOneParam.substitute(ix=ix, param1=val)
#     y = indexTwoParams.substitute(ix=ix, param1=val,param2 = val+val)
#     cmd = 'PM'
#     print(cmd+x)
#     print(cmd+y)

# def split_by_delimiter(input,step,delimiter):
#     return  zip(input, input[1:])[::2]
#
#
# x1 = "8100"
#
# x3 = '{80 00}'
#
# res1 = Converter.remove_non_hexa_sumbols(x1)
# res2 = Converter.remove_non_hexa_sumbols(x3)
#
# res1int = Converter.hexaString2int(res1)
# res2int = Converter.hexaString2int(res2)
#
#
#
# res = '{{{0} {1}}}'.format(res1[:2],res1[2:])



def config_modifier(offset ,field):
    count = 10000 #field.count
    mode = 'INC'#XenaEnums.unified_to_xena(field)
    startValue = Converter.remove_non_hexa_sumbols(field)
    x = len(startValue)-4
    startValue = startValue[x:]
    startValue = Converter.stringMac2int(startValue)
    sMask = "FFFF0000"
    step = 1
    rep = 1
    smMaxVal = 0xFFFF
    smMaxCount = smMaxVal -startValue
    if count < smMaxCount:
        pass
        #use simple modifier
    else:
        pass
        #use extended modifier

PY3K = sys.version_info >= (3, 0)

if PY3K:
    from UnifiedTG.Tests.debug_run import *
else:
    from debug_run import *



txPort = tgPorts[0]
rxPort = tgPorts[0] if loopBackMode else tgPorts[1]

streamName = txPort.add_stream()

txPort.streams[streamName].instrumentation.automatic_enabled= True

txPort.receive_mode.data_inetgrity = True
txPort.data_integrity.enable = True
txPort.data_integrity.signature_offset = 54
txPort.data_integrity.enable_time_stamp = False

txPort.apply_streams()
txPort.apply_receive_mode()
txPort.apply_data_integrity()
txPort.apply_port_config()
print('')




# rxPort.reset_sequence_index()

def test_preemption():
    rxPort.properties.enable_basic_frame_preemption = True
    stream1 = rxPort.add_stream()
    rxPort.streams[stream1].packet.preemption.enabled = True
    rxPort.streams[stream1].packet.preemption.packetType = TGEnums.FP_PACKET_TYPE.SMD_C0
    rxPort.streams[stream1].packet.preemption.fragCount = TGEnums.FP_FRAG_COUNT.FragCount3
    rxPort.apply()
    rxPort.get_stats()
    rxPort.get_fp_stats()
    rxPort.statistics.rx_fp

    rxPort.streams[stream1].packet.preemption.fragCount = TGEnums.FP_FRAG_COUNT.FragCountAuto
    rxPort.apply()
    rxPort.streams[stream1].packet.preemption.enabled = False
    rxPort.apply()
    rxPort.streams[stream1].packet.preemption.enabled = True
    rxPort.streams[stream1].packet.preemption.packetType = TGEnums.FP_PACKET_TYPE.SMD_S1
    rxPort.streams[stream1].packet.preemption.endFragmet = False
    rxPort.apply()
    rxPort.streams[stream1].packet.preemption.endFragmet = True
    rxPort.apply()

test_preemption()


txPort.properties.transmit_mode = TGEnums.PORT_PROPERTIES_TRANSMIT_MODES.PORT_BASED
txPort.apply()

def test_arp_novus():
    txPort.properties.media_type = TGEnums.PORT_PROPERTIES_MEDIA_TYPE.COPPER
    txPort.apply()
    rxPort.properties.media_type = TGEnums.PORT_PROPERTIES_MEDIA_TYPE.COPPER
    rxPort.apply()

    txPort.enable_protocol_managment = True
    txPort.protocol_managment.enable_ARP = True
    p1_if_1 = txPort.protocol_managment.protocol_interfaces.add_interface()
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].enable = True
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].description = 'TX'
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].mac_addr = 'AA:AA:AA:AA:AA:00'
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].mask = '24'
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.address = '1.1.1.1'
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.gateway = '1.1.1.2'
    txPort.protocol_managment.protocol_interfaces.auto_arp = False
    txPort.protocol_managment.apply()
    #txPort.protocol_managment.arp_table.apply()

    rxPort.enable_protocol_managment = True
    rxPort.protocol_managment.enable_ARP = True
    p2_if_1 = rxPort.protocol_managment.protocol_interfaces.add_interface()
    rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].enable = True
    rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].description = 'RX'
    rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].mac_addr = '00:BB:BB:BB:BB:00'
    rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].mask = '24'
    rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].ipv4.address = '1.1.1.2'
    rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].ipv4.gateway = '1.1.1.1'
    rxPort.protocol_managment.protocol_interfaces.auto_arp = False
    rxPort.protocol_managment.apply()

    txPort.protocol_managment.arp_table.clear()
    rxPort.protocol_managment.arp_table.clear()
    txPort.protocol_managment.arp_table.transmit()
    rxPort.protocol_managment.arp_table.transmit()
    txPort.protocol_managment.arp_table.refresh()
    rxPort.protocol_managment.arp_table.refresh()
    if len(txPort.protocol_managment.arp_table.learned_table) != 1:
        print('FAILED MAC EMPTY')
    elif txPort.protocol_managment.arp_table.learned_table[0].mac != '00 BB BB BB BB 00':
        print('FAILED WRONG MAC')
    else:
        print('MAC LEARNED OK')


    stream1 = txPort.add_stream()
    txPort.streams[stream1].packet.l3_proto = TGEnums.L3_PROTO.IPV4
    txPort.streams[stream1].source_interface.enabled = True
    txPort.streams[stream1].source_interface.description_key = p1_if_1
    time.sleep(5)
    txPort.apply_streams()
    #txPort._port_driver_obj.write()
    txPort.apply()

    print("")




    # rxPort.enable_protocol_managment = True
    # rxPort.protocol_managment.enable_ARP = True
    # rxPort.protocol_managment.enable_PING = True
    # p2_if_1 = rxPort.protocol_managment.protocol_interfaces.add_interface()
    # rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].enable = True
    # rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].description = 'RX22'
    # rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].mac_addr = '00:00:00:00:11:22'
    # rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].ipv4.address = '1.1.1.2'
    # rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].ipv4.gateway = '1.1.1.1'
    # rxPort.apply()
    #
    # txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].send_ping('1.1.1.2')
    # all_stats = tg.get_all_ports_stats()
    # rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].send_ping('1.1.1.1')
    #
    # all_stats = tg.get_all_ports_stats()

#test_arp_novus()

def test_stas():
    rxPort.reset_factory_defaults()
    txPort.properties.loopback_mode = TGEnums.PORT_PROPERTIES_LOOPBACK_MODE.INTERNAL_LOOPBACK
    #txPort.properties.transmit_mode = TGEnums.PORT_PROPERTIES_TRANSMIT_MODES.PORT_BASED
    #rxPort.properties.transmit_mode = TGEnums.PORT_PROPERTIES_TRANSMIT_MODES.PORT_BASED
    #tx
    stream1 = txPort.add_stream()
    x = txPort.split_mode
    txPort.streams[stream1].instrumentation.automatic_enabled = True
    txPort.streams[stream1].instrumentation.time_stamp_enabled = True
    txPort.streams[stream1].instrumentation.packet_grouops_enabled = True
    txPort.streams[stream1].instrumentation.sequence_checking_enabled = True
    txPort.streams[stream1].packet.data_integrity.enable = True
    txPort.streams[stream1].instrumentation.packet_group.enable_group_id = True
    txPort.streams[stream1].instrumentation.packet_group.group_id = 0
    txPort.apply_streams()

    #rx
    rxPort.receive_mode.automatic_signature.enabled = True
    # rxPort.receive_mode.wide_packet_group = True
    # rxPort.receive_mode.data_inetgrity = True
    rxPort.apply_receive_mode()
    rxPort.apply_port_config()

    txPort.start_packet_groups()
    txPort.start_traffic()
    res = tg.get_advanced_stats()
    #res = tg.get_advanced_stats(['frameRate', 'bitRate'])
    print()

#test_stas()

def test_adv_stats():
    p1_name = p1 #'Port1'
    p2_name = p2 #'Port2'
    p3_name = 'Port3'
    port1_stream1 = "p1_s1"
    port1_stream2 = "p1_s2"
    port2_stream1 = "p2_s1"
    port2_stream2 = "p2_s2"
    port3_stream1 = "p3_s1"
    port3_stream2 = "p3_s2"
    #tg.ports[p1_name].add_stream(port1_stream1)
    tg.ports[p2_name].add_stream(port2_stream1)
    tg.ports[p2_name].add_stream(port2_stream2)
    # tg.ports[p3_name].add_stream(port3_stream1)
    # tg.ports[p3_name].add_stream(port3_stream2)
    # tg.ports[p1_name].streams[port1_stream1].packet.mac.fcs = TGEnums.FCS_ERRORS_MODE.NO_ERROR
    # tg.ports[p1_name].streams[port1_stream1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
    # tg.ports[p1_name].streams[port1_stream1].control.packets_per_burst = "200"
    # tg.ports[p1_name].streams[port1_stream1].frame_size.value = 68
    # tg.ports[p1_name].add_stream(port1_stream2)
    # tg.ports[p1_name].streams[port1_stream2].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
    # tg.ports[p1_name].streams[port1_stream2].control.packets_per_burst = "3657"
    # tg.ports[p1_name].streams[port1_stream2].frame_size.value = 68
    # tg.ports[p2_name].add_stream(port2_stream1)
    # tg.ports[p2_name].streams[port2_stream1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
    # tg.ports[p2_name].streams[port2_stream1].control.packets_per_burst = "634"
    # tg.ports[p2_name].streams[port2_stream1].frame_size.value = 68
    # tg.ports[p2_name].add_stream(port2_stream2)
    # tg.ports[p2_name].streams[port2_stream2].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
    # tg.ports[p2_name].streams[port2_stream2].control.packets_per_burst = "7567"
    # tg.ports[p2_name].streams[port2_stream2].frame_size.value = 68
    # tg.ports[p1_name].streams[port1_stream1].rate.mode = TGEnums.STREAM_RATE_MODE.UTILIZATION
    # tg.ports[p2_name].streams[port2_stream1].rate.mode = TGEnums.STREAM_RATE_MODE.UTILIZATION
    #
    # tg.ports[p1_name].streams[port1_stream1].packet.mac.da.mode = TGEnums.MODIFIER_MAC_MODE.RANDOM
    # tg.ports[p1_name].streams[port1_stream1].packet.mac.da.mask = '00:00:00:00:00:FF'

    # #TX
    # tg.ports[p1_name].streams[port1_stream1].instrumentation.automatic_enabled= True
    # #tg.ports[p1_name].streams[port1_stream1].instrumentation.time_stamp_enabled = True
    # #tg.ports[p1_name].streams[port1_stream1].instrumentation.packet_grouops_enabled =True
    # #tg.ports[p1_name].streams[port1_stream1].instrumentation.sequence_checking_enabled = True
    # tg.ports[p1_name].streams[port1_stream1].packet.data_integrity.enable = True
    # #RX
    #tg.ports[p2_name].receive_mode.automatic_signature.enabled = True
    #tg.ports[p2_name].receive_mode.data_inetgrity
    #tg.ports[p2_name].receive_mode.wide_packet_group = True
    #tg.ports[p2_name].receive_mode.data_inetgrity = True


    tg.ports[p1_name].apply()
    tg.ports[p2_name].apply()
    #tg.ports[p3_name].apply()
    #tg.ports[p1_name].start_traffic()
    # tg.ports[p2_name].apply()
    # tg.start_traffic()
    # sleep(2)
    # tg.stop_traffic()
    # tg.ports[p1_name].clear_all_statistics()

    tg.clear_all_stats(port_list=[p1_name, p2_name])
    #rx_port_list=None, tx_streams_list=None
    tg.configure_advanced_stats(rx_port_list=[p1_name], tx_streams_list={p2_name:[port2_stream1,port2_stream2]}) #, p3_name:[port3_stream1,port3_stream2]
    #tg.configure_advanced_stats(automatic=True)
    #tg.configure_advanced_stats(prbs=True)
    #tg.configure_advanced_stats([p1_name,p2_name],prbs=True)
    # config_dict = {
    #     p1_name: r"C:\temp\port1.prt",
    #     p2_name: r"C:\temp\port2.prt",
    # }
    # tg.save_config_file(config_dict)
    #tg.wait_for_link_up(timeout=10)
    tg.ports[p1_name].start_packet_groups()
    txPort.start_traffic()
    #txPort2.start_traffic()

    # tg.ports[p1_name].clear_port_statistics()
    tg.get_all_ports_stats()
    # error_dict1 = tg.ports[p1_name].count_error_stats(["bits_sent"])
    # error_dict2 = tg.ports[p2_name].count_error_stats()
    # tg.ports[p1_name].get_stats()
    # tg.ports[p1_name].streams[port1_stream1].get_stats()
    tg.get_advanced_stats()
    pass

#test_adv_stats()

def test_start_group():
    txPort.add_stream()
    rxPort.add_stream()
    txPort.properties.media_type = TGEnums.PORT_PROPERTIES_MEDIA_TYPE.COPPER
    txPort.apply()
    rxPort.properties.media_type = TGEnums.PORT_PROPERTIES_MEDIA_TYPE.COPPER
    rxPort.apply()

    def test_group(ports_list):
        tg.start_traffic(ports_list)
        time.sleep(1)
        txPort.get_stats()
        assert 0 < int(txPort.statistics.frames_sent)
        if type(ports_list) is list and len(ports_list) > 1:
            rxPort.get_stats()
            assert 0 < int(rxPort.statistics.frames_sent)
        tg.stop_traffic(ports_list)
        tg.clear_all_stats(ports_list)
        txPort.get_stats()
        assert 0 == int(txPort.statistics.frames_sent)
        rxPort.get_stats()
        assert 0 == int(rxPort.statistics.frames_sent)

    test_group([txPort._port_name, rxPort._port_name])
    test_group([txPort._port_name, rxPort._port_name])

test_start_group()

print("")



#txPort.properties.transmit_mode = TGEnums.PORT_PROPERTIES_TRANSMIT_MODES.PORT_BASED
#txPort.apply_port_config()



def test_v6():

    stream1 = txPort.add_stream("TX")
    txPort.streams[stream1].packet.l2_proto = TGEnums.L2_PROTO.ETHERNETII
    txPort.streams[stream1].packet.mac.sa.value = "00:00:00:00:11:11"
    txPort.streams[stream1].packet.ethertype = "0x86DD"
    txPort.streams[stream1].packet.l3_proto = TGEnums.L3_PROTO.IPV6
    txPort.streams[stream1].packet.ipv6.traffic_class = '40'
    txPort.streams[stream1].packet.ipv6.source_ip.value = "2001::2"
    txPort.streams[stream1].packet.ipv6.source_ip.mask = "64"
    txPort.streams[stream1].packet.ipv6.destination_ip.value = "3001::2"
    txPort.streams[stream1].packet.ipv6.destination_ip.mask = "64"
    txPort.streams[stream1].packet.ipv6.hop_limit = '254'

    # stream2 = txPort.add_stream()
    # txPort.streams[stream2].packet.l2_proto = TGEnums.L2_PROTO.ETHERNETII
    # txPort.streams[stream2].packet.mac.sa.value = "00:00:00:00:11:11"
    # txPort.streams[stream2].packet.ethertype = "0x86DD"
    # txPort.streams[stream2].packet.l3_proto = TGEnums.L3_PROTO.IPV6
    # txPort.streams[stream2].packet.ipv6.source_ip.value = "5001::2"
    # txPort.streams[stream2].packet.ipv6.source_ip.mask = "64"
    # txPort.streams[stream2].packet.ipv6.destination_ip.value = "6001::2"
    # txPort.streams[stream2].packet.ipv6.destination_ip.mask = "64"
    # txPort.streams[stream2].packet.ipv6.hop_limit = '22'

    #txPort.apply()

    #return
    #Fragment
    #frag1 = txPort.streams["TX"].packet.ipv6.extention_headers.add(TGEnums.Ipv6ExtensionType.Fragment)
    # txPort.streams["TX"].packet.ipv6.extention_headers.fragment[frag1].id = 123
    # txPort.streams["TX"].packet.ipv6.extention_headers.fragment[frag1].fragment_offset = 50
    # txPort.streams["TX"].packet.ipv6.extention_headers.fragment[frag1].mflag = True
    # txPort.streams["TX"].packet.ipv6.extention_headers.fragment[frag1].reserved = 60
    # txPort.streams["TX"].packet.ipv6.extention_headers.fragment[frag1].res= 0
    #
    # #Auth
    # auth1 = txPort.streams["TX"].packet.ipv6.extention_headers.add(TGEnums.Ipv6ExtensionType.Authentication)
    # txPort.streams["TX"].packet.ipv6.extention_headers.authentication[auth1].payload_length = 11
    # txPort.streams["TX"].packet.ipv6.extention_headers.authentication[auth1].security_param_index = 555
    # txPort.streams["TX"].packet.ipv6.extention_headers.authentication[auth1].sequence_number_filed = 2323
    #
    # #hop
    # hop1 = txPort.streams["TX"].packet.ipv6.extention_headers.add(TGEnums.Ipv6ExtensionType.HopByHop)
    # hop1_mid = txPort.streams["TX"].packet.ipv6.extention_headers.hopbyhop[hop1].add_option(TGEnums.Ipv6OptionType.MIpV6UniqueIdSub)
    # txPort.streams["TX"].packet.ipv6.extention_headers.hopbyhop[hop1].unique_id_sub[hop1_mid].SubUniqueId = 14
    #
    # hop1_acs = txPort.streams["TX"].packet.ipv6.extention_headers.hopbyhop[hop1].add_option(TGEnums.Ipv6OptionType.MlpV6AlternativeCoaSub)
    # txPort.streams["TX"].packet.ipv6.extention_headers.hopbyhop[hop1].alternative_coa_sub[hop1_acs].address = '2001:0:0:0:0:0:0:1'
    #
    # hop1_ba1 = txPort.streams["TX"].packet.ipv6.extention_headers.hopbyhop[hop1].add_option(TGEnums.Ipv6OptionType.BindingAcknowledgment)
    # txPort.streams["TX"].packet.ipv6.extention_headers.hopbyhop[hop1].binding_ack[hop1_ba1].life_time = 120
    # txPort.streams["TX"].packet.ipv6.extention_headers.hopbyhop[hop1].binding_ack[hop1_ba1].length = 14
    # txPort.streams["TX"].packet.ipv6.extention_headers.hopbyhop[hop1].binding_ack[hop1_ba1].status = 99
    # txPort.streams["TX"].packet.ipv6.extention_headers.hopbyhop[hop1].binding_ack[hop1_ba1].sequence_number = 123
    # txPort.streams["TX"].packet.ipv6.extention_headers.hopbyhop[hop1].binding_ack[hop1_ba1].refresh = 222
    # hop1_jum1 = txPort.streams["TX"].packet.ipv6.extention_headers.hopbyhop[hop1].add_option(TGEnums.Ipv6OptionType.Jumbo)
    # txPort.streams["TX"].packet.ipv6.extention_headers.hopbyhop[hop1].jumbo[hop1_jum1].payload = 55665544
    # txPort.streams["TX"].packet.ipv6.extention_headers.hopbyhop[hop1].add_option(TGEnums.Ipv6OptionType.PAD1)
    # hop1_ra1 = txPort.streams["TX"].packet.ipv6.extention_headers.hopbyhop[hop1].add_option(TGEnums.Ipv6OptionType.RouterAlert)
    # txPort.streams["TX"].packet.ipv6.extention_headers.hopbyhop[hop1].router_alert[hop1_ra1].alert_type = TGEnums.RouterAlertType.ActiveNetworks
    # hop1_padN = txPort.streams["TX"].packet.ipv6.extention_headers.hopbyhop[hop1].add_option(TGEnums.Ipv6OptionType.PADN)
    # txPort.streams["TX"].packet.ipv6.extention_headers.hopbyhop[hop1].PADN[hop1_padN].value = 'aa bb cc dd ee'
    # hop1_ba1 = txPort.streams["TX"].packet.ipv6.extention_headers.hopbyhop[hop1].add_option(TGEnums.Ipv6OptionType.BindingUpdate)
    # txPort.streams["TX"].packet.ipv6.extention_headers.hopbyhop[hop1].binding_update[hop1_ba1].length = 12
    # txPort.streams["TX"].packet.ipv6.extention_headers.hopbyhop[hop1].binding_update[hop1_ba1].router = True
    # txPort.streams["TX"].packet.ipv6.extention_headers.hopbyhop[hop1].binding_update[hop1_ba1].home = True
    # txPort.streams["TX"].packet.ipv6.extention_headers.hopbyhop[hop1].binding_update[hop1_ba1].bicasting = True
    # txPort.streams["TX"].packet.ipv6.extention_headers.hopbyhop[hop1].binding_update[hop1_ba1].prefix_length = 6
    # txPort.streams["TX"].packet.ipv6.extention_headers.hopbyhop[hop1].binding_update[hop1_ba1].sequence_number = 333
    # txPort.streams["TX"].packet.ipv6.extention_headers.hopbyhop[hop1].binding_update[hop1_ba1].life_time = 127
    #
    # #IXIA CRASHED
    # hop1_req1 = txPort.streams["TX"].packet.ipv6.extention_headers.hopbyhop[hop1].add_option(TGEnums.Ipv6OptionType.BindingRequest)
    # txPort.streams["TX"].packet.ipv6.extention_headers.hopbyhop[hop1].binding_request[hop1_req1].length = 120
    #
    # #Routing
    # rex1 = txPort.streams["TX"].packet.ipv6.extention_headers.add(TGEnums.Ipv6ExtensionType.Routing)
    # txPort.streams["TX"].packet.ipv6.extention_headers.routing[rex1].reserved = '{00 00 00 11}'
    # txPort.streams["TX"].packet.ipv6.extention_headers.routing[rex1].add_node('3000:0:0:0:0:0:0:1')
    # txPort.streams["TX"].packet.ipv6.extention_headers.routing[rex1].add_node('5000:0:0:0:0:0:0:2')
    # txPort.streams["TX"].packet.ipv6.extention_headers.routing[rex1].add_node('7000:0:0:0:0:0:0:3')
    #
    # #Destination
    # dest1 = txPort.streams["TX"].packet.ipv6.extention_headers.add(TGEnums.Ipv6ExtensionType.Destination)
    # dest_padN = txPort.streams["TX"].packet.ipv6.extention_headers.destination[dest1].add_option(TGEnums.Ipv6OptionType.PADN)
    # txPort.streams["TX"].packet.ipv6.extention_headers.destination[dest1].PADN[dest_padN].value = '33'
    # dest1_hm1 = txPort.streams["TX"].packet.ipv6.extention_headers.destination[dest1].add_option(TGEnums.Ipv6OptionType.HomeAddress)
    # txPort.streams["TX"].packet.ipv6.extention_headers.destination[dest1].home_address[dest1_hm1].address = '16:0:0:0:0:0:0:0'
    # txPort.streams["TX"].packet.ipv6.extention_headers.destination[dest1].add_option(TGEnums.Ipv6OptionType.PAD1)

    txPort.streams["TX"].packet.l4_proto = TGEnums.L4_PROTO.UDP
    txPort.streams[stream1].packet.udp.source_port.value = '555'
    txPort.streams[stream1].packet.tcp.destination_port.value = '777'
    txPort.apply()


    ch_tx1 = txPort.streams[stream1].packet.macSec.Tx.add_channel()
    txPort.streams[stream1].packet.macSec.Tx.channels[ch_tx1].macAddress = 'aa aa aa aa aa aa'


test_v6()

# txPort.properties.auto_neg_enable = False
# txPort.properties.auto_neg_speed = TGEnums.SPEED.SPEED100
# txPort.properties.auto_neg_duplex = TGEnums.DUPLEX.HALF
# txPort.apply()
# txPort.properties.auto_neg_speed = TGEnums.SPEED.SPEED100
# txPort.properties.auto_neg_duplex = TGEnums.DUPLEX.FULL
# txPort.apply()
# txPort.properties.auto_neg_speed = TGEnums.SPEED.SPEED10
# txPort.properties.auto_neg_duplex = TGEnums.DUPLEX.HALF
# txPort.apply()
# txPort.properties.auto_neg_speed = TGEnums.SPEED.SPEED10
# txPort.properties.auto_neg_duplex = TGEnums.DUPLEX.FULL
# txPort.apply()


def test_v4():
    stream1 = txPort.add_stream()
    txPort.streams[stream1].packet.l3_proto = TGEnums.L3_PROTO.IPV4
    txPort.streams[stream1].packet.ipv4.source_ip.value = '1.1.1.1'
    txPort.streams[stream1].packet.ipv4.source_ip.mode = TGEnums.MODIFIER_IPV4_ADDRESS_MODE.INCREMENT_NET
    txPort.streams[stream1].packet.ipv4.source_ip.mask = '255.255.255.0'
    txPort.streams[stream1].packet.ipv4.source_ip.count = 20
    txPort.streams[stream1].packet.ipv4.destination_ip.value = '2.2.2.2'
    txPort.streams[stream1].packet.ipv4.destination_ip.mode = TGEnums.MODIFIER_IPV4_ADDRESS_MODE.INCREMENT_NET
    txPort.streams[stream1].packet.ipv4.destination_ip.mask = '255.255.0.0'
    txPort.streams[stream1].packet.ipv4.dscp_decimal_value = '11'
    txPort.streams[stream1].packet.ipv4.identifier = 5
    txPort.apply()

#test_v4()
#print()







stream1 = txPort.add_stream()
txPort.properties.transmit_mode = TGEnums.PORT_PROPERTIES_TRANSMIT_MODES.PORT_BASED
txPort.streams[stream1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.CONTINUOUS_PACKET
txPort.apply()








txPort._parent._connector.session.ports['10.5.224.94/6/10'].streams.values()
stream2 = txPort.add_stream()
txPort._parent._connector.session.ports['10.5.224.94/6/10'].streams.values()


txPort.apply()



def test_gre():
    stream1 = txPort.add_stream()
    ################### GRE ############################################
    #txPort.streams[stream1].frame_size.value = 110
    txPort.streams[stream1].packet.l3_proto = TGEnums.L3_PROTO.IPV4
    txPort.streams[stream1].packet.l4_proto = TGEnums.L4_PROTO.GRE
   # txPort.streams[stream1].packet.gre.version = 1
    txPort.streams[stream1].packet.gre.key_field = "DD:AA:AA:AA"
    txPort.streams[stream1].packet.gre.sequence_number = "0xCCCCCCCC"
    txPort.streams[stream1].packet.gre.use_checksum = True
    txPort.streams[stream1].packet.gre.l3_proto = "81 aF"
    #txPort.streams[stream1].packet.gre.l3_proto = TGEnums.L3_PROTO.IPV4
    txPort.streams[stream1].packet.gre.l4_proto = TGEnums.L4_PROTO.TCP
    txPort.streams[stream1].packet.gre.ipv4.source_ip.value = '7.7.7.7'
    txPort.streams[stream1].packet.gre.tcp.destination_port.value = '777'
    txPort.apply()
    print()

# test_gre()



def test_PTP():
    stream1 = txPort.add_stream()
    txPort.streams[stream1].packet.protocol_pad.enabled = True
    txPort.streams[stream1].packet.protocol_pad.type = TGEnums.PROTOCOL_PAD_TYPE.PTP
    txPort.streams[stream1].packet.ptp.messageType = 12
    txPort.streams[stream1].packet.ptp.messageLength = 0x45
    txPort.apply()


test_PTP()
print ("")

def test_pgid():
    # TX
    stream1 = txPort.add_stream()
    txPort.streams[stream1].instrumentation.automatic_enabled= True
    # #tg.ports[p1_name].streams[port1_stream1].instrumentation.time_stamp_enabled = True
    txPort.streams[stream1].instrumentation.packet_grouops_enabled =True
    # #tg.ports[p1_name].streams[port1_stream1].instrumentation.sequence_checking_enabled = True
    # txPort.streams[stream1].packet.data_integrity.enable = True
    txPort.streams[stream1].instrumentation.packet_group.enable_group_id = True
    txPort.streams[stream1].instrumentation.packet_group.group_id = 6
    # txPort.properties.transmit_mode = TGEnums.PORT_PROPERTIES_TRANSMIT_MODES.PORT_BASED
    txPort.apply_streams()
    txPort.start_traffic()

    rxPort.receive_mode.automatic_signature.enabled = True
    rxPort.apply()
    rxPort.start_packet_groups()

    tg.get_advanced_stats()

#test_pgid()

def test_integrity():
    TgPort = txPort
    stream1 = TgPort.add_stream()
    TgPort.streams[stream1].packet.data_integrity.enable = True
    TgPort.streams[stream1].packet.data_integrity.signature_offset = 44

    TgPort.receive_mode.data_inetgrity = False
    TgPort.data_integrity.enable = True
    TgPort.data_integrity.signature_offset = 22
    TgPort.data_integrity.enable_time_stamp = False

    TgPort.apply_streams()
    TgPort.apply_receive_mode()
    TgPort.apply_data_integrity()
    TgPort.apply_port_config()




# test_integrity()
# print("")

def test_udfList():
    stream1 = txPort.add_stream()
    udf1Name = txPort.streams[stream1].packet.add_modifier()
    txPort.streams[stream1].packet.modifiers[udf1Name].enabled = True
    #txPort.streams[stream1].packet.modifiers[udf1Name].byte_offset = testOffset
    txPort.streams[stream1].packet.modifiers[udf1Name].bit_type = TGEnums.MODIFIER_UDF_BITS_MODE.BITS_16
    txPort.streams[stream1].packet.modifiers[udf1Name].mode = TGEnums.MODIFIER_UDF_MODE.VALUE_LIST
    txPort.streams[stream1].packet.modifiers[udf1Name].value_list = '{{AD AD} {00 00} {BB BB}}'
    txPort.apply()

#test_udfList()
#print('')

def test_mpls():
    stream1 = txPort.add_stream()
    mpls_3 = txPort.streams[stream1].packet.add_mpls_label()
    txPort.streams[stream1].packet.mpls_labels[mpls_3].label = 789
    txPort.streams[stream1].packet.mpls_labels[mpls_3].ttl = 60
    txPort.streams[stream1].packet.mpls_labels[mpls_3].experimental = 7
    mpls_1 = txPort.streams[stream1].packet.add_mpls_label()
    txPort.streams[stream1].packet.mpls_labels[mpls_1].label = 123
    txPort.streams[stream1].packet.mpls_labels[mpls_1].ttl = 20
    txPort.streams[stream1].packet.mpls_labels[mpls_1].experimental = 5
    mpls_2 = txPort.streams[stream1].packet.add_mpls_label()
    txPort.streams[stream1].packet.mpls_labels[mpls_2].label = 456
    txPort.streams[stream1].packet.mpls_labels[mpls_2].ttl = 40
    txPort.streams[stream1].packet.mpls_labels[mpls_2].experimental = 6




    txPort.streams[stream1].packet.mac.fcs = TGEnums.FCS_ERRORS_MODE.BAD_CRC
    txPort.apply()

#test_mpls()

def test_imcp():
    s1 = txPort.add_stream()
    txPort.streams[s1].packet.l2_proto = TGEnums.L2_PROTO.ETHERNETII
    txPort.streams[s1].packet.l3_proto = TGEnums.L3_PROTO.IPV4
    txPort.streams[s1].packet.l4_proto = TGEnums.L4_PROTO.ICMP
    txPort.streams[s1].packet.icmp.icmp_type = TGEnums.ICMP_HEADER_TYPE.ECHO_REQUEST
    txPort.streams[s1].packet.icmp.code = 123
    txPort.streams[s1].packet.icmp.id = 999
    txPort.streams[s1].packet.icmp.sequence = 784
    txPort.apply_streams()
    pass

#test_imcp()


def test_arp_v4():
    txPort.enable_protocol_managment = True
    txPort.protocol_managment.enable_ARP = True
    txPort.protocol_managment.enable_PING = True
    p1_if_1 = txPort.protocol_managment.protocol_interfaces.add_interface()
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].enable = True
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].description = 'TX11'
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].mac_addr = '00:00:00:00:11:11'
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.address = '1.1.1.1'
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.gateway = '1.1.1.2'
    txPort.apply()

    rxPort.enable_protocol_managment = True
    rxPort.protocol_managment.enable_ARP = True
    rxPort.protocol_managment.enable_PING = True
    p2_if_1 = rxPort.protocol_managment.protocol_interfaces.add_interface()
    rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].enable = True
    rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].description = 'RX22'
    rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].mac_addr = '00:00:00:00:11:22'
    rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].ipv4.address = '1.1.1.2'
    rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].ipv4.gateway = '1.1.1.1'
    rxPort.apply()

    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].send_ping('1.1.1.2')
    all_stats = tg.get_all_ports_stats()
    rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].send_ping('1.1.1.1')

    all_stats = tg.get_all_ports_stats()







    print('')

    # txPort.protocol_managment.arp_table.clear()
    # txPort.protocol_managment.arp_table.transmit()
    # txPort.protocol_managment.arp_table.refresh()
    # assert len(txPort.protocol_managment.arp_table.learned_table) == 1
    # assert txPort.protocol_managment.arp_table.learned_table[0].ip == '1.1.1.2'
    # assert txPort.protocol_managment.arp_table.learned_table[0].mac == '00 00 00 00 11 22'
    # rxPort.protocol_managment.arp_table.refresh()
    # assert len(rxPort.protocol_managment.arp_table.learned_table) == 1
    # assert rxPort.protocol_managment.arp_table.learned_table[0].ip == '1.1.1.1'
    # assert rxPort.protocol_managment.arp_table.learned_table[0].mac == '00 00 00 00 11 11'


def testv6_2streams():


    tgPort = txPort

    tgPort.enable_protocol_managment = True
    portIntKey = tgPort.protocol_managment.protocol_interfaces.add_interface()
    tgPort.protocol_managment.protocol_interfaces.interfaces[portIntKey].enable = True
    tgPort.protocol_managment.protocol_interfaces.interfaces[portIntKey].description = 'TX'
    tgPort.protocol_managment.protocol_interfaces.interfaces[portIntKey].ipv6.address = '3000::1'
    tgPort.protocol_managment.protocol_interfaces.interfaces[portIntKey].ipv6.mask = 96
    tgPort.protocol_managment.protocol_interfaces.interfaces[portIntKey].ipv6.gateway = '3000::2'

    tgPort.add_stream('test#{}'.format(len(list(tgPort.streams.keys())) + 1))
    stream = tgPort.streams['test#{}'.format(len(list(tgPort.streams.keys())))]
    stream.packet.l2_proto = TGEnums.L2_PROTO.ETHERNETII
    stream.packet.l3_proto = TGEnums.L3_PROTO.IPV6
    stream.source_interface.enabled = True
    stream.source_interface.description_key = portIntKey
    stream.packet.ipv6.destination_ip.value = '1001:db8:85a3::370:7334'
    tgPort.add_stream('test#{}'.format(len(list(tgPort.streams.keys())) + 1))
    stream = tgPort.streams['test#{}'.format(len(list(tgPort.streams.keys())))]
    stream.packet.l2_proto = TGEnums.L2_PROTO.ETHERNETII
    stream.packet.l3_proto = TGEnums.L3_PROTO.IPV6
    stream.source_interface.enabled = True
    stream.source_interface.description_key = portIntKey
    stream.packet.ipv6.destination_ip.value = 'aaaa:bbb:cccc::ddd:eeee'

    tgPort.apply()
    tgPort.apply_streams()




# txPort.properties.auto_neg_enable = True
# txPort.apply_auto_neg()
# txPort.properties.auto_neg_enable = False
# txPort.apply_auto_neg()
# txPort.properties.auto_neg_enable = True
# txPort.apply_auto_neg()
# txPort.properties.auto_neg_enable = False
# txPort.apply_auto_neg()


test_v6()
print ("")


def test2fromsource():
    txPort.enable_protocol_managment = True
    txPort.protocol_managment.enable_ARP = True
    # protocol interfaces:
    # add interface
    p1_if_1 = txPort.protocol_managment.protocol_interfaces.add_interface()
    # add v4
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].enable = True
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].description = 'TX11'
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].mac_addr = '00:00:00:00:11:11'
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.address = '1.1.1.2'
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.gateway = '1.1.1.1'

    #txPort.apply()

    p1_if_2 = txPort.protocol_managment.protocol_interfaces.add_interface()
    # add v4
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_2].enable = True
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_2].description = 'TX22'
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_2].mac_addr = '00:00:00:00:11:22'
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_2].ipv4.address = '1.1.1.253'
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_2].ipv4.gateway = '1.1.1.1'

    # FromProtocolInterface:
    stream1 = txPort.add_stream()
    txPort.streams[stream1].packet.l3_proto = TGEnums.L3_PROTO.IPV4
    txPort.streams[stream1].source_interface.enabled = True
    txPort.streams[stream1].source_interface.description_key = p1_if_1

    # FromProtocolInterface:
    stream1 = txPort.add_stream()
    txPort.streams[stream1].packet.l3_proto = TGEnums.L3_PROTO.IPV4
    txPort.streams[stream1].source_interface.enabled = True
    txPort.streams[stream1].source_interface.description_key = p1_if_2

    txPort.apply()

#test2fromsource()


test_v6()

def test_arp():
    # protocol management
    # enable feature:
    txPort.enable_protocol_managment = True
    txPort.protocol_managment.enable_ARP = True
    # protocol interfaces:
    # add interface
    p1_if_1 = txPort.protocol_managment.protocol_interfaces.add_interface()
    # add v4
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].enable = True
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].description = 'TX11'
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].mac_addr = '00:00:00:00:11:11'
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.address = '1.1.1.1'
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.gateway = '1.1.1.2'
    # add v6
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv6.address = '3000::1'
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv6.mask = 96
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv6.gateway = '3000::2'
    # add vlan
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].vlans.enable = True
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].vlans.vid = '22,33'
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].vlans.priority = '2,3'
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].vlans.tpid = '0x8100,0x9100'
    # params
    txPort.protocol_managment.protocol_interfaces.auto_neighbor_discovery = True
    txPort.protocol_managment.protocol_interfaces.auto_arp = True

    # apply config
    txPort.apply()
    #or txPort.protocol_managment.apply()

    # neighbor table:
    # actions
    txPort.protocol_managment.protocol_interfaces.clear_neigbors_table()
    txPort.protocol_managment.protocol_interfaces.send_neighbor_solicitation()
    txPort.protocol_managment.protocol_interfaces.send_router_solicitation()
    txPort.protocol_managment.protocol_interfaces.read_neigbors_table()
    # results
    if len(txPort.protocol_managment.protocol_interfaces.discovered_neighbors) > 1:
        txPort.protocol_managment.protocol_interfaces.discovered_neighbors[p1_if_1][0].ip == '3000:0:0:0:0:0:0:2'
        txPort.protocol_managment.protocol_interfaces.discovered_neighbors[p1_if_1][0].mac = '00 00 00 00 00 01'

    # arp table:
    # params
    txPort.protocol_managment.protocol_interfaces.auto_neighbor_discovery = True
    txPort.protocol_managment.protocol_interfaces.auto_arp = True
    txPort.protocol_managment.arp_table.arp_for = TGEnums.ARP_For.RESOLVE
    txPort.protocol_managment.arp_table.count = 2
    txPort.protocol_managment.arp_table.retries = 1
    # actions
    txPort.protocol_managment.arp_table.clear()
    txPort.protocol_managment.arp_table.transmit()
    txPort.protocol_managment.arp_table.refresh()
    # results
    if len(txPort.protocol_managment.arp_table.learned_table) > 1:
        txPort.protocol_managment.arp_table.learned_table[0].ip == '1.1.1.2'
        txPort.protocol_managment.arp_table.learned_table[0].mac == '00 00 00 00 11 22'

    # FromProtocolInterface:
    stream1 = txPort.add_stream()
    txPort.streams[stream1].packet.l3_proto = TGEnums.L3_PROTO.IPV4
    txPort.streams[stream1].source_interface.enabled = True
    txPort.streams[stream1].source_interface.description_key = p1_if_1

test_arp()

p1 = txPort
fc = p1.properties.flow_control
fc.enable = True
fc.type = TGEnums.Flow_Control_Type.IEEE802_1Qbb
fc.enable_response_delay = True
fc.delay_quanta = 24
p1.apply()

txPort.clear_port_statistics()
stream1 = txPort.add_stream()
txPort.properties.loopback_mode = TGEnums.PORT_PROPERTIES_LOOPBACK_MODE.INTERNAL_LOOPBACK
txPort.apply()
tg.start_traffic()
#tg.stop_traffic()
all_stats = tg.get_all_ports_stats()







termVID = txPort.filter_properties.create_size_match_term(from_size= 128,to_size=256)
txPort.filter_properties.capture_filter.add_condition(termVID)
txPort.properties.loopback_mode = TGEnums.PORT_PROPERTIES_LOOPBACK_MODE.INTERNAL_LOOPBACK
txPort.apply()
burst = 10
for i in range(1, 20):
    txPort.add_stream()
    txPort.apply_streams()
    if i == 1:
        txPort.start_traffic()



for i in range(1, 10):
    for j in range(0, i-1):
        stream1 = 'stream_'+str(i)
        txPort.streams[stream1].enabled = False
    txPort.apply_streams()
    for j in range(0, 3):
        stream1 = 'stream_'+str(i+j)
        txPort.streams[stream1].enabled = True

txPort.apply()
X = str(txPort.streams[stream1])

stream2 = rxPort.add_stream()
txPort.streams[stream1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
txPort.streams[stream1].control.packets_per_burst = burst
rxPort.streams[stream2].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
rxPort.streams[stream2].control.packets_per_burst = burst
txPort.apply()
rxPort.apply()
tg.start_traffic()
tg.start_capture()
tg.stop_capture()
tg.stop_traffic()
all_stats = tg.get_all_ports_stats()
pass
x = 2

# rxPort = tgPorts[0]
# txPort = tgPorts[1]
# txPort2 = tgPorts[2]


def init__setup_ports():
    txPort.reset_factory_defaults()
    txPort.clear_all_statistics()
    if loopBackMode:
        txPort.properties.loopback_mode = TGEnums.PORT_PROPERTIES_LOOPBACK_MODE.INTERNAL_LOOPBACK
    else:
        rxPort.reset_factory_defaults()
        rxPort.clear_all_statistics()







def test_trigger_2patterns_1filter():
    # if txPort.properties.speed is TGEnums.PORT_PROPERTIES_SPEED.GIGA_400:
    #     assert False

    def run(udfList):
        txPort.streams[stream1].packet.modifiers[udf1Name].enabled = False
        txPort.streams[stream1].packet.modifiers[udf2Name].enabled = False
        for udfName in udfList:
            txPort.streams[stream1].packet.modifiers[udfName].enabled = True
        if len(udfList) > 1:
            expectedtriger1 = burst / txPort.streams[stream1].packet.modifiers[udf1Name].repeat_count
        else:
            expectedtriger1 = 0

        txPort.apply()
        if txPort is not rxPort:
            rxPort.apply()
        rxPort.clear_all_statistics()
        txPort.start_traffic()

        time.sleep(rxSleep)
        stats = rxPort.statistics
        rxPort.get_stats()

        if int(stats.user_defined_stat_1) != expectedtriger1:
            print ("Not good!!!")
        assert expectedtriger1 == int(stats.user_defined_stat_1)

    testPattern = 'CC DD'
    testOffset = 24
    burst = 10

    pattern2 = '44 55'
    patternOffset2 = 14

    init__setup_ports()

    stream1 = txPort.add_stream()
    txPort.streams[stream1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
    txPort.streams[stream1].control.packets_per_burst = burst
    txPort.streams[stream1].rate.mode = TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND
    txPort.streams[stream1].rate.pps_value = 100

    udf1Name = txPort.streams[stream1].packet.add_modifier()
    txPort.streams[stream1].packet.modifiers[udf1Name].enabled = True
    txPort.streams[stream1].packet.modifiers[udf1Name].byte_offset = testOffset
    txPort.streams[stream1].packet.modifiers[udf1Name].bit_type = TGEnums.MODIFIER_UDF_BITS_MODE.BITS_16
    txPort.streams[stream1].packet.modifiers[udf1Name].mode = TGEnums.MODIFIER_UDF_MODE.NESTED_COUNTER
    txPort.streams[stream1].packet.modifiers[udf1Name].continuously_counting = False
    txPort.streams[stream1].packet.modifiers[udf1Name].repeat_count = burst / 5
    txPort.streams[stream1].packet.modifiers[udf1Name].repeat_init = testPattern
    txPort.streams[stream1].packet.modifiers[udf1Name].repeat_mode = TGEnums.MODIFIER_UDF_REPEAT_MODE.DOWN
    txPort.streams[stream1].packet.modifiers[udf1Name].repeat_step = 1
    txPort.streams[stream1].packet.modifiers[udf1Name].inner_repeat_step = 8
    txPort.streams[stream1].packet.modifiers[udf1Name].inner_repeat_count = 6
    txPort.streams[stream1].packet.modifiers[udf1Name].inner_repeat_loop = 12

    udf2Name = txPort.streams[stream1].packet.add_modifier()
    udf2 = txPort.streams[stream1].packet.modifiers[udf2Name]
    udf2.enabled = True
    udf2.byte_offset = patternOffset2
    udf2.bit_type = TGEnums.MODIFIER_UDF_BITS_MODE.BITS_32
    udf2.mode = TGEnums.MODIFIER_UDF_MODE.COUNTER
    udf2.continuously_counting = False
    udf2.repeat_count = burst / 5
    udf2.repeat_init = pattern2
    udf2.repeat_mode = TGEnums.MODIFIER_UDF_REPEAT_MODE.UP
    udf2.repeat_step = 1
    # udf2.from_chain = TGEnums.MODIFIER_UDF_FROM_CHAIN_MODE.UDF1

    term1 = rxPort.filter_properties.create_match_term(testPattern, testOffset)
    term2 = rxPort.filter_properties.create_match_term(pattern2, patternOffset2 + offset_adapter)

    myFilter_1 = rxPort.filter_properties.filters[1]
    myFilter_1.enabled = True
    myFilter_1.add_condition(term1)
    myFilter_1.add_condition(term2)

    # if txPort.properties.speed is not TGEnums.PORT_PROPERTIES_SPEED.GIGA_400:
    # run([udf1Name])
    # run([udf2Name])
    run([udf1Name, udf2Name])

def test_trig_overide():
    testPattern = 'CC DD'
    testOffset = 24
    term1 = rxPort.filter_properties.create_match_term(testPattern, testOffset)

    rxPort.filter_properties.match_terms[term1].offset = 33
    myFilter_1 = rxPort.filter_properties.filters[1]
    myFilter_1.enabled = True
    myFilter_1.add_condition(term1)
    rxPort.apply()
    myFilter_1.conditions=[]
    rxPort.apply()
    myFilter_1.add_condition(term1)

    rxPort.apply()
    pass

#test_trig_overide()


def test_rate_polling():
    init__setup_ports()
    txPort.properties.loopback_mode = TGEnums.PORT_PROPERTIES_LOOPBACK_MODE.INTERNAL_LOOPBACK
    burst = 300
    stream1 = txPort.add_stream()
    txPort.streams[stream1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
    txPort.streams[stream1].control.packets_per_burst = burst
    txPort.streams[stream1].rate.mode = TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND
    txPort.streams[stream1].rate.pps_value = 10

    txPort.streams[stream1].packet.l3_proto = TGEnums.L3_PROTO.IPV4
    txPort.streams[stream1].packet.ipv4.qos_type = TGEnums.QOS_MODE.TOS
    txPort.streams[stream1].packet.ipv4.tos_precedence = 7
    txPort.streams[stream1].packet.ipv4.tos_throughput = 1
    txPort.streams[stream1].packet.ipv4.tos_delay = 1
    txPort.streams[stream1].packet.l4_proto = TGEnums.L4_PROTO.GRE
    txPort.streams[stream1].packet.gre.version = 1
    #txPort.streams[stream1].packet.gre.key_field = "0xaa"
    #txPort.streams[stream1].packet.gre.sequence_number = "0xbb"
    #txPort.streams[stream1].packet.gre.use_checksum = True
    txPort.streams[stream1].packet.gre.l3_proto = "{aa bb}" #TGEnums.L3_PROTO.IPV4
    txPort.streams[stream1].packet.gre.l4_proto = TGEnums.L4_PROTO.TCP
    txPort.streams[stream1].packet.gre.ipv4.source_ip.value = '7.7.7.7'
    txPort.streams[stream1].packet.gre.tcp.destination_port.value = '777'


    txPort.apply()
    txPort.start_traffic()
    txPort.wait_tx_done()

    time.sleep(3)
    txPort.get_stats()
    while int(txPort.statistics.bits_sent_rate):
        time.sleep(1)
        txPort.get_stats()

#test_rate_polling()


def test_spirent():

    saMac = '00:00:00:00:44:55'
    daMac = 'FF:FF:FF:00:00:01'
    burst = 500
    #1/connect/reserve
    #txPort.properties.ignore_link_status = True
    txPort.properties.loopback_mode = TGEnums.PORT_PROPERTIES_LOOPBACK_MODE.INTERNAL_LOOPBACK
    #verify defaults
    #2 create stream mac/ip
    stream1 = txPort.add_stream()
    txPort.properties.transmit_mode = TGEnums.PORT_PROPERTIES_TRANSMIT_MODES.PORT_BASED
    txPort.streams[stream1].frame_size.value = 80
    txPort.streams[stream1].packet.data_pattern.type = TGEnums.DATA_PATTERN_TYPE.FIXED
    txPort.streams[stream1].packet.data_pattern.value = 'AA BB CC DD EE FF AA'
    # set mac/ip
    txPort.streams[stream1].packet.l2_proto = TGEnums.L2_PROTO.ETHERNETII
    txPort.streams[stream1].packet.mac.sa.value = saMac
    txPort.streams[stream1].packet.mac.da.value = daMac
    v1 = txPort.streams[stream1].packet.add_vlan()
    txPort.streams[stream1].packet.vlans[v1].vid.value = 555
    txPort.streams[stream1].packet.vlans[v1].priority = 3
    txPort.streams[stream1].packet.l3_proto = TGEnums.L3_PROTO.IPV4
    txPort.streams[stream1].packet.ipv4.source_ip.value = '1.1.1.1'
    txPort.streams[stream1].packet.ipv4.destination_ip.value = '2.2.2.2'
    txPort.streams[stream1].packet.ipv4.dscp_decimal_value = '11'
    txPort.streams[stream1].packet.ipv4.identifier = 5
    #set mode/burst
    txPort.streams[stream1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
    txPort.streams[stream1].control.packets_per_burst = burst
    #set mode pps
    txPort.streams[stream1].rate.mode = TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND
    txPort.streams[stream1].rate.pps_value = 50
    txPort.apply()
    txPort.clear_port_statistics()
    rxPort.clear_port_statistics()
    #send / verify rx = burst
    txPort.start_traffic()
    rxPort.get_stats()
    if rxPort.statistics.frames_received != burst:
        assert rxPort.statistics.frames_received == burst
    #set mode continuous / 50%
    txPort.streams[stream1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.CONTINUOUS_PACKET
    txPort.streams[stream1].rate.mode = TGEnums.STREAM_RATE_MODE.UTILIZATION
    txPort.streams[stream1].rate.utilization_value = 50
    #set frame random
    txPort.streams[stream1].frame_size.mode = TGEnums.MODIFIER_FRAME_SIZE_MODE.RANDOM
    txPort.streams[stream1].frame_size.min = 128
    txPort.streams[stream1].frame_size.max = 512
    txPort.streams[stream1].packet.data_pattern.type = TGEnums.DATA_PATTERN_TYPE.INCREMENT_BYTE
    txPort.apply()
    #clear counters/verify 0
    txPort.clear_port_statistics()
    rxPort.clear_port_statistics()
    #send /verify > 0 / rate 50%
    txPort.start_traffic()
    rxPort.get_stats()
    if txPort.statistics.frames_sent_rate == 0:
        assert txPort.statistics.frames_sent_rate > 0
        assert rxPort.statistics.frames_received_rate > 0
    #stop /verify rate 0
    txPort.stop_traffic()
    time.sleep(1)
    rxPort.get_stats()
    if txPort.statistics.frames_sent_rate != 0:
        assert txPort.statistics.frames_sent_rate == 0
        assert rxPort.statistics.frames_received_rate == 0
    #clear/ verify count 0
    txPort.clear_port_statistics()
    rxPort.clear_port_statistics()
    if txPort.statistics.frames_sent != -1:
        assert rxPort.statistics.frames_sent == -1
        assert rxPort.statistics.frames_received == -1

#test_trigger_2patterns_1filter()





def test_arp():
    init__setup_ports()
    stream1 = rxPort.add_stream()
    stream1 = rxPort.add_stream()
    rxPort.streams[stream1].packet.l2_proto = TGEnums.L2_PROTO.ETHERNETII
    rxPort.streams[stream1].packet.l3_proto = TGEnums.L3_PROTO.ARP
    rxPort.streams[stream1].packet.arp.operation = TGEnums.ARP_OPERATION.ARP_REQUEST
    rxPort.streams[stream1].packet.arp.sender_hw.value = '00:00:77:77:77:77'
    rxPort.streams[stream1].packet.arp.sender_hw.mode = TGEnums.MODIFIER_ARP_MODE.INCREMENT
    rxPort.streams[stream1].packet.arp.sender_hw.count = 10

    rxPort.streams[stream1].packet.arp.target_hw.value = '00:00:88:88:88:88'
    rxPort.streams[stream1].packet.arp.target_hw.mode = TGEnums.MODIFIER_ARP_MODE.DECREMENT
    rxPort.streams[stream1].packet.arp.target_hw.count = 20

    rxPort.streams[stream1].packet.arp.sender_ip.value = '1.1.1.7'
    rxPort.streams[stream1].packet.arp.sender_ip.mode = TGEnums.MODIFIER_ARP_MODE.CONTINUOUS_INCREMENT
    rxPort.streams[stream1].packet.arp.target_ip.value = '1.1.1.8'
    rxPort.streams[stream1].packet.arp.target_ip.mode = TGEnums.MODIFIER_ARP_MODE.CONTINUOUS_DECREMENT

    rxPort.streams[stream1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM  # this stream sen continues line rate
    rxPort.streams[stream1].control.packets_per_burst = 5
    rxPort.streams[stream1].control.bursts_per_stream = 1
    rxPort.apply()
    pass




def test1():
    #
    req_field = 'ptp.v2.correction.ns'
    rxPort.analyzer.init_default_view(fields=[req_field])
    rxPort.start_capture()
    txPort.start_traffic(True)
    rxPort.stop_capture()
    res = rxPort.analyzer.default_view.result[0][req_field][0]








#test1()

test_arp()

#txPort.receive_mode.packet_group = True
#txPort.receive_mode.sequence_checking = True
# txPort.receive_mode.automatic_signature.enabled = True
# txPort.apply()
# txPort.receive_mode.automatic_signature.enabled = False
# txPort.apply()
# txPort.receive_mode.wide_packet_group = False
# txPort.apply()
#txPort.receive_mode.sequence_checking = True




def test_trigger_pattern_and_not():
    testPattern = '22 33'
    testOffset = 24
    burst = 10

    init__setup_ports()

    stream1 = txPort.add_stream()

    txPort.streams[stream1].frame_size.value = 128
    txPort.streams[stream1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
    txPort.streams[stream1].control.packets_per_burst = burst
    txPort.streams[stream1].rate.mode = TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND
    txPort.streams[stream1].rate.pps_value = 100
    #
    #txPort.apply()
    udf1Name = txPort.streams[stream1].packet.add_modifier()
    txPort.streams[stream1].packet.modifiers[udf1Name].enabled = True
    txPort.streams[stream1].packet.modifiers[udf1Name].byte_offset = testOffset
    txPort.streams[stream1].packet.modifiers[udf1Name].bit_type = TGEnums.MODIFIER_UDF_BITS_MODE.BITS_16
    txPort.streams[stream1].packet.modifiers[udf1Name].mode = TGEnums.MODIFIER_UDF_MODE.COUNTER
    txPort.streams[stream1].packet.modifiers[udf1Name].continuously_counting = False
    txPort.streams[stream1].packet.modifiers[udf1Name].repeat_count = burst / 2
    txPort.streams[stream1].packet.modifiers[udf1Name].repeat_init = testPattern
    txPort.streams[stream1].packet.modifiers[udf1Name].repeat_mode = TGEnums.MODIFIER_UDF_REPEAT_MODE.DOWN
    txPort.streams[stream1].packet.modifiers[udf1Name].repeat_step = 1
    #
    term1 = rxPort.filter_properties.create_match_term(testPattern, testOffset)
    #
    myFilter_1 = rxPort.filter_properties.filters[1]
    myFilter_1.enabled = True
    myFilter_1.add_condition(term1)
    rxPort.apply()
    rxPort.apply()
    #
    # myFilter2 = rxPort.filter_properties.filters[2]
    # myFilter2.enabled = True
    # myFilter2.add_condition(term1, TGEnums.LOGICAL_OPERATOR.NOT)

    txPort.apply()
    if txPort is not rxPort:
        rxPort.apply()

    txPort.start_traffic()

    time.sleep(rxSleep)
    stats = rxPort.statistics
    rxPort.get_stats()

    expectedtriger1 = burst / txPort.streams[stream1].packet.modifiers[udf1Name].repeat_count
    assert int(stats.user_defined_stat_1) == expectedtriger1
    if int(stats.user_defined_stat_2) != burst - expectedtriger1:
        print ("Not good!!!")
    assert int(stats.user_defined_stat_2) == burst - expectedtriger1

test_trigger_pattern_and_not()
#test_trigger_pattern_and_not()

test_adv_stats()


def IPv6_ACL_01():

    ################################################neighbor discovery######################################################
    txPort.enable_protocol_managment = True
    p1_if_1 = txPort.protocol_managment.protocol_interfaces.add_interface()
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].enable = True
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].description = 'TX'
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].mac_addr = "00:00:00:00:12:12"
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv6.address = '2001::2'
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv6.mask = 64
    txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv6.gateway = '2001::1'
    txPort.apply()
    rxPort.enable_protocol_managment = True
    p2_if_1 = rxPort.protocol_managment.protocol_interfaces.add_interface()
    rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].enable = True
    rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].description = 'RX'
    rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].mac_addr = "00:00:00:00:11:32"
    rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].ipv6.address = '3001::2'
    rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].ipv6.mask = 64
    rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].ipv6.gateway = '3001::1'
    rxPort.apply()

    txPort.protocol_managment.protocol_interfaces.clear_neigbors_table()

    txPort.protocol_managment.protocol_interfaces.send_neighbor_solicitation()
    txPort.protocol_managment.protocol_interfaces.read_neigbors_table()
    rxPort.protocol_managment.protocol_interfaces.send_neighbor_solicitation()
    rxPort.protocol_managment.protocol_interfaces.read_neigbors_table()

    ################################################STRAM PARAMETERS########################################################
    txPort.add_stream("TX")
    txPort.streams["TX"].packet.l2_proto = TGEnums.L2_PROTO.ETHERNETII
    txPort.streams["TX"].packet.mac.da.mode = TGEnums.MODIFIER_MAC_MODE.ARP
    txPort.streams["TX"].packet.mac.sa.value = "00:00:00:00:11:11"
    txPort.streams["TX"].packet.ethertype = "0x86DD"
    txPort.streams["TX"].packet.l3_proto = TGEnums.L3_PROTO.IPV6
    txPort.streams["TX"].packet.ipv6.source_ip.value = "2001::2"
    txPort.streams["TX"].packet.ipv6.source_ip.mask = "64"
    txPort.streams["TX"].packet.ipv6.destination_ip.value = "3001::2"
    txPort.streams["TX"].packet.ipv6.destination_ip.mask = "64"
    txPort.streams[
        "TX"].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM  # this stream send Bursts
    txPort.streams["TX"].control.packets_per_burst = 1000

    txPort.streams["TX"].control.bursts_per_stream = 1
    """txPort.streams["TX"].control.mode = TGEnums.STREAM_TRANSMIT_MODE.CONTINUOUS_PACKET

    txPort.streams["TX"].rate.mode = TGEnums.STREAM_RATE_MODE.UTILIZATION
    txPort.streams["TX"].rate.utilization_value = "100" 
    """
    txPort.apply_streams()
    fltvlan = rxPort.filter_properties.create_match_term(pattern="20:01:00:00:00:00:00:00:00:00:00:00:00:00:00:02",
                                                         offset=22)
    rxPort.filter_properties.filters[1].enabled = True
    rxPort.filter_properties.filters[1].add_condition(fltvlan)
    rxPort.apply_filters()
    rxPort.clear_all_statistics()
    txPort.clear_all_statistics()
    txPort.start_traffic(blocking=True)
    status = True

    txPort.stop_traffic()
    time.sleep(3)
    txPort.get_stats()
    rxPort.get_stats()
    x = 1
    # check for expected value
    self.logger.info(
        "sent {} packets , received {} packets as expected".format(txPort.statistics.frames_sent,
                                                                   rxPort.statistics.frames_received))
    self.logger.info(
        "sent {} packets , received {} packets as expected".format(txPort.statistics.frames_sent,
                                                                   rxPort.statistics.user_defined_stat_1))

IPv6_ACL_01()



#test_adv_stats()

# txPort.properties.transmit_mode = TGEnums.PORT_PROPERTIES_TRANSMIT_MODES.PORT_BASED
# txPort.properties.auto_neg_enable = False
# txPort.apply()
#test_spirent()
saMac = '00:00:00:00:44:55'
daMac = 'FF:FF:FF:00:00:01'
burst = 500



p1 = txPort
fc = p1.properties.flow_control
fc.enable = True
fc.type = TGEnums.Flow_Control_Type.IEEE802_1Qbb
stream1 = txPort.add_stream()


#txPort.properties.transmit_mode = TGEnums.PORT_PROPERTIES_TRANSMIT_MODES.PORT_BASED
#txPort.streams[stream1].frame_size.value = 80
# txPort.streams[stream1].packet.data_pattern.type = TGEnums.DATA_PATTERN_TYPE.FIXED
# txPort.streams[stream1].packet.data_pattern.value = 'AA BB CC DD EE FF AA'
# set mac/ip
txPort.streams[stream1].packet.l2_proto = TGEnums.L2_PROTO.ETHERNETII
txPort.streams[stream1].packet.mac.sa.value = saMac
txPort.streams[stream1].packet.mac.da.value = daMac
v1 = txPort.streams[stream1].packet.add_vlan()
txPort.streams[stream1].packet.vlans[v1].vid.value = 555
txPort.streams[stream1].packet.vlans[v1].priority = 3
txPort.streams[stream1].packet.l3_proto = TGEnums.L3_PROTO.IPV4
txPort.streams[stream1].packet.ipv4.source_ip.value = '1.1.1.1'
txPort.streams[stream1].packet.ipv4.destination_ip.value = '2.2.2.2'
txPort.streams[stream1].packet.ipv4.dscp_decimal_value = '11'
txPort.streams[stream1].packet.ipv4.identifier = 5
#set mode/burst
txPort.streams[stream1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
txPort.streams[stream1].control.packets_per_burst = burst
#set mode pps
txPort.streams[stream1].rate.mode = TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND
txPort.streams[stream1].rate.pps_value = 50
txPort.apply()
txPort.clear_port_statistics()
txPort.start_traffic()
#txPort.properties.ignore_link_status = True


txPort.get_stats()
rxPort.get_stats()
txPort.clear_port_statistics()
rxPort.clear_all_statistics()
txPort.start_traffic()
txPort.get_stats()
rxPort.get_stats()


s = txPort.streams[stream1]._packet_view()
s = Converter.remove_non_hexa_sumbols(s)
x = str(txPort.streams[stream1].packet.to_string()).upper()

print('')

txPort.enable_protocol_managment = True
txPort.protocol_managment.enable_ARP = True
txPort.protocol_managment.arp_table.arp_for = TGEnums.ARP_For.RESOLVE
txPort.protocol_managment.protocol_interfaces.auto_neighbor_discovery = True
p1_if_1 = txPort.protocol_managment.protocol_interfaces.add_interface()
txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].enable = True
txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].description = '1X'
txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].mac_addr = '00:00:00:00:11:11'
txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.address = '1.1.1.1'
txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.gateway = '1.1.1.3'
# txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].vlans.enable = True
# txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].vlans.vid = '22,33,55'
# txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].vlans.priority = '2,3,4'
# txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].vlans.tpid = '0x8100,0x8100,0x9100'
# txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv6.address = '3000::1'
# txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv6.mask = 96
# txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv6.gateway = '3000::2'
p1_if_2 = txPort.protocol_managment.protocol_interfaces.add_interface()
txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_2].enable = True
txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_2].description = '2X'
txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_2].mac_addr = '00:00:00:00:11:22'
txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_2].ipv4.address = '1.1.1.2'
txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_2].ipv4.gateway = '1.1.1.1'
txPort.apply()


stream1 = txPort.add_stream()
txPort.streams[stream1].packet.l3_proto = TGEnums.L3_PROTO.IPV4
#txPort.streams[stream1].packet.ipv4.source_ip.value = '1.1.1.1'
#txPort.streams[stream1].packet.ipv4.source_ip.mode = TGEnums.MODIFIER_IPV4_ADDRESS_MODE.INCREMENT_HOST
#txPort.streams[stream1].packet.ipv4.source_ip.count = 20
#txPort.streams[stream1].packet.ipv4.destination_ip.value = '2.2.2.2'
#txPort.streams[stream1].packet.ipv4.dscp_decimal_value = '11'
#txPort.streams[stream1].packet.ipv4.identifier = 5
txPort.streams[stream1].source_interface.enabled = True
txPort.streams[stream1].source_interface.description_key = p1_if_1

txPort.apply()

rxPort.enable_protocol_managment = True
rxPort.protocol_managment.enable_ARP = True
#rxPort.protocol_managment.protocol_interfaces.auto_arp = True
p2_if_1 = rxPort.protocol_managment.protocol_interfaces.add_interface()
rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].enable = True
rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].description = '1X'
rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].mac_addr = '00:00:00:00:22:11'
rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].ipv4.address = '1.1.1.2'
rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].ipv4.gateway = '1.1.1.1'
rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].ipv6.address = '3000::2'
rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].ipv6.mask = 96
rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].ipv6.gateway = '3000::1'
p2_if_2 = rxPort.protocol_managment.protocol_interfaces.add_interface()
rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].enable = True
rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].description = '1XX'
rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].mac_addr = '00:00:00:00:22:22'
rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].ipv4.address = '1.1.1.3'
rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_2].ipv4.gateway = '1.1.1.1'
p2_if_3 = rxPort.protocol_managment.protocol_interfaces.add_interface()
rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_3].enable = True
rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_3].description = '2XX'
rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_3].mac_addr = '00:00:00:00:22:33'
rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_3].ipv4.address = '2.2.2.2'
rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_3].ipv4.gateway = '2.2.2.1'


rxPort.protocol_managment.arp_table.count = 2
rxPort.protocol_managment.arp_table.retries = 1

rxPort.protocol_managment.apply()

# txPort.protocol_managment.arp_table.refresh()
# txPort.protocol_managment.arp_table.clear()
# txPort.protocol_managment.arp_table.transmit()
# txPort.protocol_managment.arp_table.refresh()
# txPort.protocol_managment.arp_table.clear()
# txPort.protocol_managment.arp_table.refresh()

#txPort.router.arp_table.read()

#txPort.router.protocol_interfaces.interfaces[p1_if_1].arp.clear()
txPort.protocol_managment.protocol_interfaces.clear_neigbors_table()
rxPort.protocol_managment.protocol_interfaces.send_arp()
txPort.protocol_managment.protocol_interfaces.read_neigbors_table()
txPort.protocol_managment.protocol_interfaces.clear_neigbors_table()
txPort.protocol_managment.protocol_interfaces.send_neighbor_solicitation()
txPort.protocol_managment.protocol_interfaces.read_neigbors_table()

txPort.protocol_managment.arp_table.refresh()




stream1 = txPort.add_stream()
txPort.streams[stream1].source_interface.enable
txPort.streams[stream1].source_interface.description_key = p1_if_1

txPort.streams[stream1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
txPort.streams[stream1].control.packets_per_burst = 5
txPort.apply()



headers_list = list(filter(lambda x: isinstance(getattr(pkt.specialTag,x),header_object ), pkt.specialTag.__dict__))

for h in headers_list:
    h_obj = getattr(pkt.specialTag,h)
    assert len(h_obj.to_string()) > 0


#     pkt.specialTag.type = TGEnums.SpecialTagType.extDSA_Forward_use_vidx_1


# txPort.streams[''].packet.pause_control.destination_address
# txPort.streams[''].packet.pause_control.pause_quanta

pkt.specialTag.type = TGEnums.SpecialTagType.extDSA_Forward_use_vidx_1
pkt.specialTag.extDSA_Forward_use_vidx_1.Src_Trunk_ePort_6_5 = 0xA
txPort.apply()
pkt.specialTag.type = TGEnums.SpecialTagType.EDSA_To_CPU
pkt.specialTag.EDSA_To_CPU.eVLAN_11_0 = 5
txPort.apply()
pkt.specialTag.type = TGEnums.SpecialTagType.EDSA_To_ANALYZER_use_eVIDX_1
pkt.specialTag.EDSA_To_ANALYZER_use_eVIDX_1.UP = 1
txPort.apply()
# pkt.etag.E_PCP = 2
# pkt.etag.E_DEI = 1
# pkt.etag.Ingress_E_CID_base = 0x30
# pkt.etag.GRP = 2
# pkt.etag.E_CID_base = 0x15
# pkt.etag.Ingress_E_CID_ext = 0xAA
# pkt.etag.E_CID_ext = 0x66
txPort.apply()


txPort.enable_protocol_managment = True
txPort.protocol_managment.active = True
txPort.protocol_managment.enable_ARP = True
if_1 = txPort.protocol_managment.protocol_interfaces.add_interface()
txPort.protocol_managment.protocol_interfaces.interfaces[if_1].enable = True
txPort.protocol_managment.protocol_interfaces.interfaces[if_1].desctiption = 'xxx_1.1.1.1'
txPort.protocol_managment.protocol_interfaces.interfaces[if_1].mac_addr = '00:00:00:00:00:11'
txPort.protocol_managment.protocol_interfaces.interfaces[if_1].ipv4.ipv4_address = '1.1.1.1'
txPort.protocol_managment.protocol_interfaces.interfaces[if_1].arp_params.retries = 4
txPort.protocol_managment.arp.interfaces[if_1].arp_params.count = 5

txPort.protocol_managment.protocol_interfaces.interfaces[if_1].apply()
txPort.protocol_managment.protocol_interfaces.interfaces[if_1].arp.send()
txPort.protocol_managment.protocol_interfaces.interfaces[if_1].ipv6_solicitation.send()

txPort.protocol_managment.protocol_interfaces.interfaces[if_1].apply()
txPort.protocol_managment.protocol_interfaces.interfaces[if_1].arp.send()
txPort.protocol_managment.protocol_interfaces.interfaces[if_1].ipv6_solicitation.send()



txPort.protocol_managment.arp.interfaces[if_1].learned_table[0]


txPort.protocol_managment.protocol_interfaces.interfaces[if_1].ipv6.ipv6_address = '3000::01'


txPort.start_traffic(wait_up=False)
txPort.stop_traffic()
stream1 = txPort.add_stream()
txPort.apply()
txPort.start_traffic(wait_up=False)

stream1 = txPort.add_stream()

x = txPort.supported_split_modes




new_ports = txPort.apply_split_mode(TGEnums.splitSpeed.Two_200G)
txPort = new_ports[0]
new_ports = txPort.apply_split_mode(TGEnums.splitSpeed.Four_100G)
txPort = new_ports[0]
new_ports = txPort.apply_split_mode(TGEnums.splitSpeed.Eight_50G)
txPort = new_ports[0]
new_ports = txPort.apply_split_mode(TGEnums.splitSpeed.One_400G)

stream1 = txPort.add_stream()

mpls_1 =  txPort.streams[stream1].packet.add_mpls_label()
txPort.streams[stream1].packet.mpls_labels[mpls_1].label = 123
txPort.streams[stream1].packet.mpls_labels[mpls_1].ttl = 20
#txPort.streams[stream1].packet.mpls_labels[mpls_1].experimental = 5

txPort.streams[stream1].packet.mac.fcs = TGEnums.FCS_ERRORS_MODE.BAD_CRC
txPort.apply()

txPort.streams[stream1].packet.mac.fcs = TGEnums.FCS_ERRORS_MODE.NO_ERROR
txPort.apply()



new_ports = txPort.apply_split_mode(TGEnums.splitSpeed.Four_25G)

def filterer():
    daMac = "00:00:00:11:11:aa"
    daOffset = 20
    saMac = "aa:bb:00:22:22:BB"
    saOffset = 26
    burst = 10

    # stream1 = txPort.add_stream()
    # txPort.streams[stream1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.ADVANCE_TO_NEXT_STREAM
    # txPort.streams[stream1].control.packets_per_burst = burst
    # txPort.streams[stream1].rate.mode = TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND
    # txPort.streams[stream1].rate.pps_value = 100
    # txPort.streams[stream1].packet.mac.sa.value = saMac
    # txPort.streams[stream1].packet.mac.da.value = daMac

    termDA = rxPort.filter_properties.create_match_term(daMac, daOffset,mask='FFFFFFFF')
    termSA = rxPort.filter_properties.create_match_term(saMac, saOffset)

    size_128_256 = rxPort.filter_properties.create_size_match_term(from_size= 128,to_size=256)

    myFilter_1 = rxPort.filter_properties.filters[1]
    myFilter_1.enabled = True
    myFilter_1.add_condition(termDA,TGEnums.LOGICAL_OPERATOR.NOT)
    myFilter_1.add_condition(size_128_256)

    myFilter_2 = rxPort.filter_properties.filters[2]
    myFilter_2.enabled = True
    myFilter_2.add_condition(termDA,TGEnums.LOGICAL_OPERATOR.NOT)
    myFilter_2.add_condition(termSA,TGEnums.LOGICAL_OPERATOR.NOT)

    myFilter_3 = rxPort.filter_properties.filters[3]
    myFilter_3.enabled = True
    myFilter_3.add_condition(termDA)
    myFilter_3.add_condition(termSA,TGEnums.LOGICAL_OPERATOR.NOT)

    txPort.apply()

def modifier(stream1):
    testPattern = 'CC DD'
    testOffset = 24
    #burst = 10
    udf1Name = txPort.streams[stream1].packet.add_modifier()
    txPort.streams[stream1].packet.modifiers[udf1Name].enabled = True
    txPort.streams[stream1].packet.modifiers[udf1Name].byte_offset = testOffset
    txPort.streams[stream1].packet.modifiers[udf1Name].continuously_counting = False
    txPort.streams[stream1].packet.modifiers[udf1Name].repeat_count=5
    txPort.streams[stream1].packet.modifiers[udf1Name].repeat_init = testPattern
    txPort.streams[stream1].packet.modifiers[udf1Name].repeat_mode = TGEnums.MODIFIER_UDF_REPEAT_MODE.DOWN
    txPort.streams[stream1].packet.modifiers[udf1Name].repeat_step = 1


def stack_vlan():
    Vid1 = 2
    Vid2 = Vid1 * 2

    stream1 = txPort.add_stream()

    firstVlan = txPort.streams[stream1].packet.add_vlan()
    txPort.streams[stream1].packet.vlans[firstVlan].vid.value = str(Vid1)
    txPort.streams[stream1].packet.vlans[firstVlan].priority = "0"
    txPort.streams[stream1].packet.vlans[firstVlan].cfi = "0"
    txPort.streams[stream1].packet.vlans[firstVlan].vid.mode = TGEnums.MODIFIER_VLAN_MODE.FIXED
    txPort.streams[stream1].packet.vlans[firstVlan].vid.count = 1
    txPort.streams[stream1].packet.vlans[firstVlan].proto = "0x9100"

    secondVlan = txPort.streams[stream1].packet.add_vlan()
    txPort.streams[stream1].packet.vlans[secondVlan].vid.value = str(Vid2)
    txPort.streams[stream1].packet.vlans[secondVlan].priority = 3
    txPort.streams[stream1].packet.vlans[secondVlan].cfi = "1"
    txPort.streams[stream1].packet.vlans[secondVlan].vid.mode = TGEnums.MODIFIER_VLAN_MODE.INCREMENT
    txPort.streams[stream1].packet.vlans[secondVlan].vid.count = 50
    txPort.apply()


#stack_vlan()


txPort.properties.fec_mode = TGEnums.PORT_PROPERTIES_FEC_MODES.RS_FEC
#txPort.apply_port_config()
txPort.properties.loopback_mode = TGEnums.PORT_PROPERTIES_LOOPBACK_MODE.INTERNAL_LOOPBACK
#txPort.apply_port_config()
# txPort.properties.loopback_mode = TGEnums.PORT_PROPERTIES_LOOPBACK_MODE.NORMAL
# txPort.apply_port_config()


s1 = txPort.add_stream()
txPort.streams[s1].rate.mode = TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND
txPort.streams[s1].rate.pps_value = 10
#txPort.streams[s1].rate.utilization_value = 44
txPort.streams[s1].frame_size.value = 124
txPort.streams[s1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
txPort.streams[s1].control.packets_per_burst = 5
#txPort.streams[s1].apply()
# txPort.streams[s1].apply()
txPort.streams[s1].packet.mac.sa.value = 'aa:bb:11:22:33:44'
txPort.streams[s1].packet.mac.sa.count = 10
txPort.streams[s1].packet.mac.sa.mode = TGEnums.MODIFIER_MAC_MODE.INCREMENT
txPort.streams[s1].packet.mac.sa.step = 1

#txPort.streams[s1].packet.l2_proto = TGEnums.L2_PROTO.PROTOCOL_OFFSET
#txPort.streams[s1].packet.protocol_offset.value = "DDDDDDDDDDDDDDDD"
#txPort.streams[s1].packet.protocol_offset.offset = "14"


txPort.streams[s1].packet.l3_proto = TGEnums.L3_PROTO.IPV6
txPort.streams[s1].packet.ipv6.traffic_class = '3'
txPort.streams[s1].packet.ipv6.source_ip.value = "FE80:0:1::2"
txPort.streams[s1].packet.ipv6.source_ip.mode = TGEnums.MODIFIER_IPV6_ADDRESS_MODE.FIXED
txPort.streams[s1].packet.ipv6.destination_ip.value = "2001:0db8:0000:0000:0000:ff00:0042:8329"
txPort.streams[s1].packet.ipv6.destination_ip.mode = TGEnums.MODIFIER_IPV6_ADDRESS_MODE.INCREMENT_INTERFACE_ID
txPort.streams[s1].packet.ipv6.destination_ip.count = 10
    #TGEnums.MODIFIER_IPV6_ADDRESS_MODE.FIXED #

txPort.apply()
txPort.start_traffic()


mpls_1 =  txPort.streams[s1].packet.add_mpls_label()
txPort.streams[s1].packet.mpls_labels[mpls_1].label = 123
txPort.streams[s1].packet.mpls_labels[mpls_1].ttl = 20


txPort.streams[s1].packet.l4_proto = TGEnums.L4_PROTO.GRE
txPort.streams[s1].packet.gre.version = 1
txPort.streams[s1].packet.gre.key_field = "0xaa"
txPort.streams[s1].packet.gre.sequence_number = "0xbb"
txPort.streams[s1].packet.gre.use_checksum = True
txPort.streams[s1].packet.gre.l3_proto = TGEnums.L3_PROTO.IPV4
txPort.streams[s1].packet.gre.l4_proto = TGEnums.L4_PROTO.TCP
txPort.streams[s1].packet.gre.ipv4.source_ip.value = '7.7.7.7'
txPort.streams[s1].packet.gre.tcp.destination_port.value = '777'

txPort.streams[s1].packet.gre.ipv6.source_ip.value = "FE80:0:1::3"
txPort.streams[s1].packet.gre.ipv6.source_ip.mode = TGEnums.MODIFIER_IPV6_ADDRESS_MODE.FIXED
txPort.streams[s1].packet.gre.ipv6.destination_ip.value = "3001:0db8:0000:0000:0000:ff00:0042:8329"
txPort.streams[s1].packet.gre.ipv6.destination_ip.mode = TGEnums.MODIFIER_IPV6_ADDRESS_MODE.INCREMENT_INTERFACE_ID


#vid = txPort.streams[s1].packet.add_vlan()
# txPort.streams[s1].packet.vlans[vid].vid = 666
# txPort.streams[s1].packet.vlans[vid].priority = 3

txPort.streams[s1].packet.l3_proto = TGEnums.L3_PROTO.IPV4
txPort.streams[s1].packet.ipv4.source_ip.value = '1.1.1.1'
txPort.streams[s1].packet.ipv4.source_ip.mode = TGEnums.MODIFIER_IPV4_ADDRESS_MODE.INCREMENT_HOST
txPort.streams[s1].packet.ipv4.source_ip.count = 20
txPort.streams[s1].packet.ipv4.destination_ip.value = '2.2.2.2'
txPort.streams[s1].packet.ipv4.dscp_decimal_value = '11'
txPort.streams[s1].packet.ipv4.identifier = 5

################### TCP ############################################
# txPort.streams[s1].packet.l4_proto = TGEnums.L4_PROTO.TCP
# txPort.streams[s1].packet.tcp.destination_port.value = 777
# txPort.streams[s1].packet.tcp.source_port.value = 656
# txPort.streams[s1].packet.tcp.flag_no_more_data_from_sender = True
# txPort.streams[s1].packet.tcp.flag_acknowledge_valid = True
# txPort.streams[s1].packet.tcp.flag_push_function = True
# txPort.streams[s1].packet.tcp.flag_reset_connection = True
# txPort.streams[s1].packet.tcp.flag_synchronize_sequence = True
# txPort.streams[s1].packet.tcp.flag_urgent_pointer_valid = True
# txPort.streams[s1].packet.tcp.sequence_number = "0xFFFFFFFF"
# txPort.streams[s1].packet.tcp.acknowledgement_number = "0x123456"
# txPort.streams[s1].packet.tcp.window = "0x4321"
# txPort.streams[s1].packet.tcp.urgent_pointer = "0x1012"
# txPort.streams[s1].packet.tcp.header_length = "1"
# txPort.streams[s1].packet.tcp.valid_checksum = TGEnums.CHECKSUM_MODE.INVALID
# txPort.streams[s1].packet.tcp.custom_checksum = "0x2626"

################### UDP ############################################
#txPort.streams[s1].packet.l4_proto = TGEnums.L4_PROTO.UDP
txPort.streams[s1].packet.udp.source_port.value = 84
txPort.streams[s1].packet.udp.destination_port.value = 65535
txPort.streams[s1].packet.udp.valid_checksum = TGEnums.CHECKSUM_MODE.VALID
txPort.streams[s1].packet.udp.custom_checksum = "0x3333"
# tg.ports["my_port1"].streams["my_stream1"].packet.udp.length_override = True
# tg.ports["my_port1"].streams["my_stream1"].packet.udp.custom_length = 6060

#txPort.streams[s1].packet.l2_proto = TGEnums.L2_PROTO.SNAP
#txPort.streams[s1].packet.data_pattern.value = 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'
#txPort.streams[s1].packet.data_pattern.type = TGEnums.DATA_PATTERN_TYPE.FIXED

# s2 = txPort.add_stream()
# txPort.streams[s2].packet.data_pattern.value = 'abc'
# txPort.streams[s2].packet.data_pattern.type = TGEnums.DATA_PATTERN_TYPE.REPEATING
# # # #txPort.apply()
# # #
# s3 = txPort.add_stream()
# txPort.streams[s3].packet.data_pattern.type = TGEnums.DATA_PATTERN_TYPE.INCREMENT_BYTE

#modifier(s1)
txPort.add_stream()
txPort.apply()

mpls_2 =  txPort.streams[s1].packet.add_mpls_label()
txPort.streams[s1].packet.mpls_labels[mpls_2].label = 456
txPort.streams[s1].packet.mpls_labels[mpls_2].ttl = 128

txPort.apply()

txPort.clear_port_statistics()

txPort.start_capture()

txPort.start_traffic(True)

req_field = 'eth.src'
txPort.analyzer.init_default_view(filter=None, fields=[req_field])
txPort.stop_capture()



txPort.get_stats()

if (loopBackMode):
    rxPort = txPort
else:
    rxPort = tgPorts[1]

txPort.properties.use_ieee_defaults = False
txPort.properties.fec_an_list = []
txPort.apply()
txPort.properties.use_ieee_defaults = True
txPort.properties.fec_an_list = [TGEnums.PORT_PROPERTIES_FEC_AN.ADVERTISE_FC,
                                             # TGEnums.PORT_PROPERTIES_FEC_AN.REQUEST_FC,
                                             # TGEnums.PORT_PROPERTIES_FEC_AN.ADVERTISE_RS,
                                             TGEnums.PORT_PROPERTIES_FEC_AN.REQUEST_RS
                                             ]
txPort.apply()




def split_autoneg():
    new_ports = txPort.apply_split_mode(TGEnums.splitSpeed.Four_25G)
    for testPort in new_ports:
        testPort.properties.use_ieee_defaults = True

        testPort.apply_auto_neg()
        testPort.properties.fec_mode = TGEnums.PORT_PROPERTIES_FEC_MODES.DISABLED
        testPort.properties.auto_neg_enable = False
        testPort.apply()
        testPort.properties.auto_neg_enable = True
        testPort.apply()

split_autoneg()