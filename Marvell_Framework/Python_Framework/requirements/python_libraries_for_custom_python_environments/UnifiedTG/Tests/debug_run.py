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

# import paramiko
# from paramiko.py3compat import u
# s = 'xxx'
# s.encode()
# us = u(s)
# out = bytes()
import sys







PY3K = sys.version_info >= (3, 0)

if PY3K:
    from UnifiedTG.Tests.tg_setup import *
else:
    from tg_setup import *

rsa_path=''
# chas = '10.4.48.192' #XENA
# vendorType = TGEnums.TG_TYPE.Xena
# p1 = chas + '/10/0'
# portsList = [p1 + ":" + p1]
# serverHost2 = chas
# vendorType = TGEnums.TG_TYPE.Xena
# offset_adapter = 0

# # #chas = '10.5.238.39' #K400
# chas = '10.5.238.181' #T400
# serverHost2 = chas
# vendorType = TGEnums.TG_TYPE.IxiaSSH
# p1 = chas + '/1/5'
# #p2 = chas + '/1/8'
# portsList = ['Port 1' + ":" + p1]

# serverHost2 = "il-wtsvs01"
# chas = '10.5.224.97'
# vendorType = TGEnums.TG_TYPE.Ixia
# p1 = chas + '/3/13'
# p2 = chas + '/3/14'

# chas = '10.28.42.223'
# serverHost1 = chas#"il-wtsvs01"
# vendorType = TGEnums.TG_TYPE.Ixia
# #p1 = chas + '/4/40'
# p1 = chas + '/4/37'
# p2 = chas + '/6/1'
# portsList = [p1 + ":" + p1,p2 + ":" + p2]

# serverHost2 = '10.5.238.52'
# chas = '10.4.48.221'
# vendorType = TGEnums.TG_TYPE.Spirent
# p1 = chas + '/2/1'
# p2 = chas + '/2/9'

#portsList = [p1 + ":" + p1,p2 + ":" + p2]
#loopBackMode = True
#userLogin = '4.98'



# vendorType = TGEnums.TG_TYPE.Ostinato
# #vendorType = TGEnums.TG_TYPE.Ixia
# userLogin = "OlegK"
#
# if vendorType is TGEnums.TG_TYPE.Ostinato:
#     serverHost1 = '127.0.0.1'
#     chas = '127.0.0.1'
#     p1 = chas + '/1/0'
#     p2 = chas + '/1/1'
#     portsList = ['1' + ":" + p1,'2' + ":" + p2]
#     loopBackMode = False
#     tg = utg.connect(vendorType, serverHost1, userLogin)
#     tgPorts = tg.reserve_ports(portsList, clear=True, force=True)  # type: list[Port]
# else:
#     serverHost1 = '10.5.224.94'
#     chas = '10.5.224.94'
#     p1 = chas + '/6/10'
#     p2 = chas + '/6/11'
#     p3 = chas + '/6/9'
#     p4 = chas + '/6/12'
#     portsList = ['Port 1' + ":" + p1, 'Port 2' + ":" + p2, 'Port 3' + ":" + p3, 'Port 4' + ":" + p4] #, 'Port 2' + ":" + p2, 'Port 3' + ":" + p3
#     loopBackMode = False

tg = utg.connect(vendorType, serverHost1, userLogin)
tg.waitLinkUpOnTx = True
start = time.time()
print('start time:',start)

tgPorts = tg.reserve_ports(portsList, clear=True, force=True)  # type: list[Port]
finish = time.time()
print('finish time:',finish)
print('total time : ' ,finish-start)


# async def connectTG():
#
#     #a = time.clock()
#     print(f"started connected TG at {time.strftime('%X')}")
#     return await time.sleep(2)
#     #await asyncio.sleep(2)
#     #await time.sleep(10)
#
#     #tgPorts = tg.reserve_ports(portsList, clear=True, force=True)  # type: list[Port]
#     print(f"finished connected TG at {time.strftime('%X')}")
#     #b = time.clock()
#     #c = b-a
#
# async def connectDUT():
#     print(f"started conected dut {time.strftime('%X')}")
#     #await asyncio.sleep(4)
#     return await time.sleep(4)
#     #await time.sleep(5)
#     print(f"END connected dut at {time.strftime('%X')}")
#
# async def connect_all():
#     # task1 = asyncio.create_task(
#     #     connectTG())
#     # task2 = asyncio.create_task(
#     #     connectDUT())
#
#     print(f"started at {time.strftime('%X')}")
#
#     await asyncio.gather(connectDUT(),connectTG())
#
# asyncio.run(connect_all())



pass
# uriP1 = chasIx1 + "/10/1"
# p1_name = "my_port1"
# portsList = [p1_name + ":" + uriP1]
# tg = utg.connect("Ixia", serverHost1, userLogin)
# tg.reserve_ports(portsList, clear=True, force=True)
# tg.ports[p1_name].properties.auto_neg_enable = False
# tg.ports[p1_name].properties.use_ieee_defaults = False
# tg.ports[p1_name].apply_port_config()
# tg.ports[p1_name].apply_auto_neg()
#
# serverHost2 = "localhost"
# chas = '10.5.224.94'
# p1 = chas + '/7/5'
# p2 = chas + '/7/7'
# portsList = ['Port 1' + ":" + p1, 'Port 2' + ":" + p2]
# quick_test_config_path = "C:\\SC\\Shmir\\PyIxNetwork\\ixnetwork\\test\\configs\\quick_test_classic_oleg.ixncfg"
# traffic_protocols_config_path = "C:\\SC\\Shmir\\PyIxNetwork\\ixnetwork\\test\\configs\\default_olegz2.ixncfg"

# #connect To IxNetwork tcl server
# vendorType = TGEnums.TG_TYPE.IxNetwork
# rsa_path='C:\\Program Files (x86)\\Ixia\\IxNetwork\\8.42-EA'
# tg = utg.connect(vendorType, serverHost2, userLogin,rsa_path=rsa_path)
# tg.waitLinkUpOnTx = True
# #Quick Tests
# tg.load_config_file(quick_test_config_path)
# tgPorts = tg.reserve_ports(portsList, clear=True,force=True)  # type: list[Port]
# tg.quick_tests.apply()
# res = tg.quick_tests.start(blocking=True)
# vStats = tg.quick_tests.read_flow_view()
# iStats = tg.traffic.read_item_stats()
# #Traffic L2-3
# tg.load_config_file(traffic_protocols_config_path)
# tgPorts = tg.reserve_ports(portsList, clear=True,force=True)  # type: list[Port]
# tg.traffic.apply()
# tg.traffic.l23_start()
# tg.traffic.l23_stop()
# tg.get_all_ports_stats()
# gStats = tg.protocols.read_global_stats()
# iStats = tg.traffic.read_item_stats()
# #Protocols
# tg.protocols.start('ospf')
# tg.protocols.stop('ospf')
# gStats = tg.protocols.read_global_stats()


