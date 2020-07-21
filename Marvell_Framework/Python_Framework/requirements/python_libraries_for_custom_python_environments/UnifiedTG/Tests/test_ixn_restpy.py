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

import sys
import pytest

PY3K = sys.version_info >= (3, 0)
simple_debug = False

if PY3K:
    from UnifiedTG.Tests.restPy_setup import *
else:
    from restPy_setup import *

def pretest():
    tg.ixnHelper.clear_scenario()
    tg.ixnHelper.clear_traffic()

class Test_IxNetwork(object):

    @pytest.mark.skipif(simple_debug is True,reason="debug")
    def test_create_clear_Scenario(self):
        pretest()
        assert 0 == len(tg.ixnetwork.Topology.find()) == len(tg.topology)
        assert 0 == len(tg.device_group)
        topologies = [('Tx', [p1], ['DG1']), ('Rx', [ixn_ports[1]], ['DG2'])]
        tg.ixnHelper.create_scenario(topologies)
        assert len(topologies) == len(tg.ixnetwork.Topology.find()) == len(tg.topology)
        dg_count = 0
        for tp in tg.topology:
            dg_count+=len(tg.topology[tp].DeviceGroup.find())
        assert 2 == dg_count == len(tg.device_group)
        tg.ixnHelper.clear_scenario()
        assert 0 == len(tg.ixnetwork.Topology.find()) == len(tg.topology)
        assert 0 == len(tg.device_group)

    @pytest.mark.skipif(simple_debug is True, reason="debug")
    def test_create_clear_Traffic(self):
        pretest()
        ti_count = len(tg.ixnetwork.Traffic.TrafficItem.find())
        assert 0 == ti_count == len(tg.traffic_items)
        topologies = [('Tx', [p1], ['DG1']), ('Rx', [ixn_ports[1]], ['DG2'])]
        tg.ixnHelper.create_scenario(topologies)
        eth1 = tg.device_group['DG1'].Ethernet.add()  # type: Ethernet
        eth2 = tg.device_group['DG2'].Ethernet.add()  # type: Ethernet
        tg.ixnetwork.StartAllProtocols()
        TrafficItemName = 'testTraffic'
        endpoints = [('ep1', 'Tx', 'Rx')]
        traffic_item_obj23 = tg.ixnHelper.add_L2_3(TrafficItemName, ixNetworkRestPyEnums.Traffic_Type.Ethernet, endpoints)
        ti_count = len(tg.ixnetwork.Traffic.TrafficItem.find())
        assert 1 == ti_count == len(tg.traffic_items)
        tg.ixnHelper.clear_traffic()
        ti_count = len(tg.ixnetwork.Traffic.TrafficItem.find())
        assert 0 == ti_count == len(tg.traffic_items)

    @pytest.mark.skipif(simple_debug is True, reason="debug")
    def test_macsec_2_macsec_v4(self):
        pretest()
        # 2 Add a topology (topology 1) using the first port, with ethernet protocol
        topologies = [('Tx', [p1], ['DG1']), ('Rx', [ixn_ports[1]], ['DG2'])]
        tg.ixnHelper.create_scenario(topologies)
        eth1 = tg.device_group['DG1'].Ethernet.add()  # type: Ethernet
        macsec1 = eth1.StaticMacsec.add(Name='TxMacSec', SendGratArp=False)  # type: StaticMacsec
        macsec1.EncryptionEngine = ixNetworkRestPyEnums.Encryption_Engine.SW.value
        # 3 Add a topology (topology 2) using the second port, with Static MACsec protocol and ethernet protocol
        eth2 = tg.device_group['DG2'].Ethernet.add()  # type: Ethernet
        macsec2 = eth2.StaticMacsec.add(Name='RxMacSec', SendGratArp=False)  # type: StaticMacsec
        macsec2.EncryptionEngine = ixNetworkRestPyEnums.Encryption_Engine.SW.value
        # 4.	Reduce the number of devices in both topologies to 1
        # by default 1
        macsec2.Multiplier = 1
        # 5.change the MAC address
        eth2.Mac.Single('00:11:22:33:44:55')
        # 6.	In the MACsec protocol, change the Rx key (of the 128 bits)
        macsec2.RxSakPool.RxSak128.Single('0xF123456789ABCDEF0123456789ABFFFF')
        # 7 In the MACsec protocol, Disable Send Gratuitous ARP
        macsec2.SendGratArp = False
        # 8	In the MACsec protocol, Disable Include SCI
        macsec2.IncludeSci.Single(False)
        # 9.	In the MACsec protocol, Disable/Enable Confidentiality
        macsec2.EnableConfidentiality.Single(False)
        # engine
        macsec2.CipherSuite.Single(ixNetworkRestPyEnums.Cipher_Suite.AES256.value)
        macsec2.TxSakPoolSize = 4
        val_list = macsec2.TxSakPool.TxSak256.Values
        val_list[1] = '0xF123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDAA'
        macsec2.TxSakPool.TxSak256.ValueList(val_list)
        # macsec2.TxSakPool.TxSak256.Overlay
        # 10.	Start all protocols
        # tg.ixnetwork.StartAllProtocols()
        macsec1.Start()
        macsec2.Start()
        eth1.EnableVlans.Single(True)
        vlanObj = eth1.Vlan.find()[0].VlanId.Increment(start_value=103, step_value=0)
        # 11.	Create a traffic item from topology 1 to topology 2
        macsecTrafficItemName = 'macsec Traffic'
        endpoints = [('ep1', 'Tx', 'Rx')]
        msec_traffic_item_obj = tg.ixnHelper.add_L2_3(macsecTrafficItemName, ixNetworkRestPyEnums.Traffic_Type.Raw, endpoints)
        traffic_config = msec_traffic_item_obj.ConfigElement.find()  # type: ConfigElement
        # type = bitsPerSecond|framesPerSecond|interPacketGap|percentLineRate
        traffic_config.FrameRate.update(Type='framesPerSecond', Rate='20')
        # type = auto|burstFixedDuration|continuous|custom|fixedDuration|fixedFrameCount|fixedIterationCount
        burst = 5
        traffic_config.TransmissionControl.update(Type='fixedFrameCount', FrameCount=burst)
        eth = tg.ixnHelper.get_traffic_header(macsecTrafficItemName, ixNetworkRestPyEnums.ProtocolType.eth)
        dest_mac = '00:00:fa:ce:fa:aa'
        eth.Field.find(FieldTypeId='destinationAddress').SingleValue = dest_mac
        ethertype = eth.Field.find(FieldTypeId='etherType')
        ether_type_str = 'faaa'
        ethertype.update(Auto=False, ValueType='singleValue', SingleValue=ether_type_str)
        custom_header = tg.ixnHelper.add_traffic_header(macsecTrafficItemName,
                                                        ixNetworkRestPyEnums.ProtocolType.custom,
                                                        ixNetworkRestPyEnums.ProtocolType.eth)
        custom_header.Field.find(FieldTypeId='length').SingleValue = 100
        custom_header.Field.find(FieldTypeId='data').SingleValue = 'AABB'
        tg.traffic_items[macsecTrafficItemName].Generate()
        tg.ixnetwork.Traffic.Apply()
        # capture start:
        testPattern = ether_type_str
        testOffset = 12
        captureFilter = rxPort.filter_properties.capture_filter
        captureFilter.enabled = True
        #MAC DA/SA bug on restpy, till 9.10 release
        # term_mac = rxPort.filter_properties.create_match_term(dest_mac, 0)
        # captureFilter.add_condition(term_mac)
        term_ethtype = rxPort.filter_properties.create_match_term(testPattern, testOffset)
        captureFilter.add_condition(term_ethtype)
        rxPort.apply_filters()
        rxPort.start_capture()
        # 12.	Start traffic
        tg.ixnetwork.Traffic.StartStatelessTrafficBlocking()
        # 13.	Verify MACsec packets by adding a view for MACsec statistics in the receiving port:
        msNames = ixNetworkRestPyEnums.MacSec_Stats_Name
        tg.stats.macsec.Rows[p1][msNames.ValidPacketRx.value]
        # direct
        rxPort.vport.Capture.Stop()
        assert rxPort.vport.Capture.DataCapturedPacketCounter == burst
        req_field = 'eth.dst'
        # req_field_value = '00:00:00:00:00:02'
        # filter=req_field + '== ' + req_field_value,
        rxPort.analyzer.init_default_view(filter=None, fields=[req_field])
        rxPort.stop_capture()
        res_count = len(rxPort.analyzer.default_view.result)
        assert res_count == burst
        res_req_field = rxPort.analyzer.default_view.result[0][req_field][0]
        assert res_req_field == dest_mac

    #@pytest.mark.skipif(simple_debug is True, reason="debug")
    def test_v6_L4_7(self):
        pretest()
        topologies = [('Tx', [p1], ['DG1']), ('Rx', [ixn_ports[1]], ['DG2'])]
        tg.create_scenario(topologies)
        eth1 = tg.device_group['DG1'].Ethernet.add()  # type: Ethernet
        macsec1 = eth1.StaticMacsec.add(Name='TxMacSec', SendGratArp=False)  # type: StaticMacsec
        macsec1.EncryptionEngine = ixNetworkRestPyEnums.Encryption_Engine.SW.value
        macsec1_v6 = macsec1.Ipv6.add()  # type: Ipv6
        macsec1_v6.ResolveGateway.Single(False)
        # 3 Add a topology (topology 2) using the second port, with Static MACsec protocol and ethernet protocol
        eth2 = tg.device_group['DG2'].Ethernet.add()  # type: Ethernet
        macsec2 = eth2.StaticMacsec.add(Name='RxMacSec', SendGratArp=False)  # type: StaticMacsec
        macsec2.EncryptionEngine = ixNetworkRestPyEnums.Encryption_Engine.SW.value
        macsec2_v6 = macsec2.Ipv6.add()  # type: Ipv6
        macsec2_v6.ResolveGateway.Single(False)

        # macsec2_v6.Address.Single('3001::1')
        tg.ixnetwork.Globals.Topology.Ipv6.PermanentMacForGateway.Single(True)
        tg.ixnetwork.Globals.Topology.Ipv6.ReSendNsOnLinkUp.Single(False)
        tg.ixnetwork.Globals.Topology.Ipv6.SuppressNsForDuplicateGateway.Single(False)
        tg.ixnetwork.StartAllProtocols()

        macsecTrafficItemName = 'macsec_v6_L47'
        endpoints = [('ep1', 'Tx', 'Rx')]
        msec_traffic_item_obj = tg.ixnHelper.add_L4_7(macsecTrafficItemName, endpoints)
        #DISABLED,no 4-7 LICENSE !!!!!!!!!!!!!!!!!!
        #tg.traffic_items[macsecTrafficItemName].Generate()
        #tg.ixnetwork.Traffic.ApplyApplicationTraffic()
        #tg.ixnetwork.Traffic.StartApplicationTraffic()
        # str(simulatedUsers | throughputGbps | throughputKbps | throughputMbps)
