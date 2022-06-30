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




#import coverage
import time

from UnifiedTG.Unified.Utils import Converter

from UnifiedTG.Unified.Packet import header_object

from UnifiedTG.Unified import TGEnums
from UnifiedTG.Unified.TGEnums import TGEnums
cov = None

#cov = coverage.Coverage(omit={'*/site-packages/*', '*/Tests/*', '*/pycharm/*', '*/*init*'})
#cov.start()

#from CI_Run import *
#from debug_run import *
import sys

PY3K = sys.version_info >= (3, 0)

if PY3K:
    from UnifiedTG.Tests.debug_run import *
else:
    from debug_run import *


txPort = tgPorts[0]
rxPort = None

if (loopBackMode):
    rxPort = txPort
else:
    rxPort = tgPorts[1]



def init__setup_ports():
    txPort.reset_factory_defaults()
    txPort.clear_all_statistics()
    if loopBackMode:
        txPort.properties.loopback_mode = TGEnums.PORT_PROPERTIES_LOOPBACK_MODE.INTERNAL_LOOPBACK
    else:
        rxPort.reset_factory_defaults()
        rxPort.clear_all_statistics()

@pytest.fixture(scope="session")
def utgSuite():
    utgSuite = True


def stable_link_state(txPort,state):
    pass

init__setup_ports()


@pytest.fixture(scope="module", autouse=True)
def my_fixture():
    print('INITIALIZATION')

    yield utgSuite
    print('TEAR DOWN')
    try:
        if cov:
            cov.stop()
            cov.save()
            cov.html_report()
    except Exception as e:
        print("Failed coverage save")

# class Test_Known_Issues(object):
#     @pytest.mark.skipif(simple_debug is True or Known_Issues is False, reason="debug other test")
#     def test_Issue_DataCenterMode(self):
#         init__setup_ports()
#         stream1 = txPort.add_stream()

class Test_Packet_Builder(object):

    def verify_packet_string(self,stream):
        s = stream._packet_view()
        s = Converter.remove_non_hexa_sumbols(s)
        x = str(stream.packet.to_string()).upper()
        if s != x:
            pass
        return True if s == x else False

    @pytest.mark.skipif(simple_debug is True or Packet_Builder is False, reason="debug other test")
    def test_default_packet(self):
        stream1 = txPort.add_stream()
        txPort.apply()
        assert self.verify_packet_string(txPort.streams[stream1])

    @pytest.mark.skipif(simple_debug is True or Packet_Builder is False, reason="debug other test")
    def test_L2_packet(self):
        init__setup_ports()
        stream1 = txPort.add_stream()
        txPort.streams[stream1].packet.mac.sa.value = '00:11:22:33:44:55'
        txPort.streams[stream1].packet.mac.da.value = '66:77:88:99:aa:bb'
        txPort.streams[stream1].packet.l2_proto = TGEnums.L2_PROTO.ETHERNETII
        txPort.apply()
        assert self.verify_packet_string(txPort.streams[stream1])
        mpls_1 = txPort.streams[stream1].packet.add_mpls_label()
        txPort.streams[stream1].packet.mpls_labels[mpls_1].label = 123
        txPort.streams[stream1].packet.mpls_labels[mpls_1].ttl = 20
        # txPort.streams[stream1].packet.mpls_labels[mpls_1].experimental = 5
        txPort.apply()
        assert self.verify_packet_string(txPort.streams[stream1])
        v1 = txPort.streams[stream1].packet.add_vlan()
        txPort.streams[stream1].packet.vlans[v1].vid.value = 55
        txPort.streams[stream1].packet.vlans[v1].priority = 4
        txPort.apply()
        assert self.verify_packet_string(txPort.streams[stream1])

    @pytest.mark.skipif(simple_debug is True or Packet_Builder is False, reason="debug other test")
    def test_L3_packet(self):
        init__setup_ports()
        stream1 = txPort.add_stream()
        txPort.streams[stream1].packet.ipv4.source_ip.value = '15.15.5.55'
        txPort.streams[stream1].packet.l3_proto = TGEnums.L3_PROTO.IPV4
        txPort.streams[stream1].packet.ipv4.qos_type = TGEnums.QOS_MODE.TOS
        txPort.streams[stream1].packet.ipv4.tos_precedence = 7
        txPort.streams[stream1].packet.ipv4.tos_throughput = 1
        txPort.streams[stream1].packet.ipv4.tos_delay = 1
        txPort.apply()
        assert self.verify_packet_string(txPort.streams[stream1])
        txPort.streams[stream1].packet.l3_proto = TGEnums.L3_PROTO.IPV6
        txPort.streams[stream1].packet.ipv6.traffic_class = '3'
        txPort.streams[stream1].packet.ipv6.source_ip.value = "FE80:0:1::2"
        txPort.streams[stream1].packet.ipv6.destination_ip.value = "2001:0db8:0000:0000:0000:ff00:0042:8329"
        txPort.apply()
        assert self.verify_packet_string(txPort.streams[stream1])


    @pytest.mark.skipif(simple_debug is True or Packet_Builder is False, reason="debug other test")
    def test_L4_packet(self):
        init__setup_ports()
        stream1 = txPort.add_stream()
        ################### TCP ############################################
        txPort.streams[stream1].packet.l3_proto = TGEnums.L3_PROTO.IPV4
        txPort.streams[stream1].packet.l4_proto = TGEnums.L4_PROTO.TCP
        txPort.streams[stream1].packet.tcp.destination_port.value = 777
        txPort.streams[stream1].packet.tcp.source_port.value = 656
        txPort.streams[stream1].packet.tcp.flag_no_more_data_from_sender = True
        txPort.streams[stream1].packet.tcp.flag_acknowledge_valid = True
        txPort.streams[stream1].packet.tcp.flag_push_function = True
        txPort.streams[stream1].packet.tcp.flag_reset_connection = True
        txPort.streams[stream1].packet.tcp.flag_synchronize_sequence = True
        txPort.streams[stream1].packet.tcp.flag_urgent_pointer_valid = True
        txPort.streams[stream1].packet.tcp.sequence_number = "0xFFFFFFFF"
        txPort.streams[stream1].packet.tcp.acknowledgement_number = "0x123456"
        txPort.streams[stream1].packet.tcp.window = "0x4321"
        txPort.streams[stream1].packet.tcp.urgent_pointer = "0x1012"
        #txPort.streams[stream1].packet.tcp.header_length = "1"
        #txPort.streams[stream1].packet.tcp.valid_checksum = TGEnums.CHECKSUM_MODE.INVALID
        #txPort.streams[stream1].packet.tcp.custom_checksum = "0x2626"
        txPort.apply()
        assert self.verify_packet_string(txPort.streams[stream1])
        ################### UDP ############################################
        txPort.streams[stream1].frame_size.value = 80
        txPort.streams[stream1].packet.l3_proto = TGEnums.L3_PROTO.IPV6
        txPort.streams[stream1].packet.l4_proto = TGEnums.L4_PROTO.UDP
        txPort.streams[stream1].packet.udp.source_port.value = 84
        txPort.streams[stream1].packet.udp.destination_port.value = 65535
        txPort.streams[stream1].packet.udp.valid_checksum = TGEnums.CHECKSUM_MODE.VALID
        txPort.streams[stream1].packet.udp.custom_checksum = "0x3333"
        txPort.apply()
        assert self.verify_packet_string(txPort.streams[stream1])


    @pytest.mark.skipif(simple_debug is True or Packet_Builder is False, reason="debug other test")
    def test_GRE_packet(self):
        init__setup_ports()
        stream1 = txPort.add_stream()
        ################### GRE ############################################
        txPort.streams[stream1].frame_size.value = 110
        txPort.streams[stream1].packet.l3_proto = TGEnums.L3_PROTO.IPV4
        txPort.streams[stream1].packet.l4_proto = TGEnums.L4_PROTO.GRE
        txPort.streams[stream1].packet.gre.version = 1
        txPort.streams[stream1].packet.gre.key_field = "0xaa"
        txPort.streams[stream1].packet.gre.sequence_number = "0xbb"
        #txPort.streams[stream1].packet.gre.use_checksum = True
        txPort.streams[stream1].packet.gre.l3_proto = TGEnums.L3_PROTO.IPV4
        txPort.streams[stream1].packet.gre.l4_proto = TGEnums.L4_PROTO.TCP
        txPort.streams[stream1].packet.gre.ipv4.source_ip.value = '7.7.7.7'
        txPort.streams[stream1].packet.gre.tcp.destination_port.value = '777'
        txPort.apply()
        assert self.verify_packet_string(txPort.streams[stream1])






    @pytest.mark.skipif(simple_debug is True or Packet_Builder is False, reason="debug other test")
    def test_payload(self):
        stream1 = txPort.add_stream()
        txPort.streams[stream1].packet.data_pattern.type = TGEnums.DATA_PATTERN_TYPE.FIXED
        txPort.streams[stream1].packet.data_pattern.value = 'ABCDFF'
        txPort.apply()
        assert self.verify_packet_string(txPort.streams[stream1])
        txPort.streams[stream1].packet.data_pattern.type = TGEnums.DATA_PATTERN_TYPE.INCREMENT_BYTE
        txPort.apply()
        assert self.verify_packet_string(txPort.streams[stream1])
        txPort.streams[stream1].packet.data_pattern.type = TGEnums.DATA_PATTERN_TYPE.REPEATING
        txPort.streams[stream1].packet.data_pattern.value = '1a2b3c'
        txPort.apply()
        assert self.verify_packet_string(txPort.streams[stream1])
        txPort.streams[stream1].packet.data_pattern.type = TGEnums.DATA_PATTERN_TYPE.DECREMENT_BYTE
        txPort.apply()
        assert self.verify_packet_string(txPort.streams[stream1])

class Test_Packet_Headers(object):



    def run_traffic_2Patterns(self, pat_1, offset_1, pat_2, offset_2_):
        term1 = rxPort.filter_properties.create_match_term(pat_1, offset_1)
        term2 = rxPort.filter_properties.create_match_term(pat_2, offset_2_)

        myFilter_1 = rxPort.filter_properties.filters[1]
        myFilter_1.enabled = True
        myFilter_1.add_condition(term1)

        myFilter_2 = rxPort.filter_properties.filters[2]
        myFilter_2.enabled = True
        myFilter_2.add_condition(term2)

        txPort.apply()
        if txPort is not rxPort:
            rxPort.apply()

        txPort.start_traffic(True)
        time.sleep(rxSleep)
        stats = rxPort.statistics
        rxPort.get_stats()
        return stats

    @pytest.mark.skipif(simple_debug is True or Packet_Headers is False, reason="debug other test")
    def test_special_headers_offset(self):

        stream1 = txPort.add_stream()
        pkt = txPort.streams[stream1].packet

        headers_list = list(filter(lambda x: isinstance(getattr(pkt.specialTag, x), header_object), pkt.specialTag.__dict__))
        assert len(headers_list) > 0

        for h in headers_list:
            h_obj = getattr(pkt.specialTag, h)
            assert len(h_obj.to_string()) > 0


    @pytest.mark.skipif(simple_debug is True or Packet_Headers is False, reason="debug other test")
    def test_protocol_offset(self):

        pattern = 'DDDDDDDDDDDDDDDD'
        testOffset = 12
        burst = 10

        init__setup_ports()
        s1 = txPort.add_stream()
        txPort.streams[s1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
        txPort.streams[s1].control.packets_per_burst = burst

        txPort.streams[s1].packet.l2_proto = TGEnums.L2_PROTO.PROTOCOL_OFFSET
        txPort.streams[s1].packet.protocol_offset.value = pattern

        term1 = rxPort.filter_properties.create_match_term(pattern, testOffset)
        myFilter_1 = rxPort.filter_properties.filters[1]
        myFilter_1.enabled = True
        myFilter_1.add_condition(term1)

        txPort.apply()
        if txPort is not rxPort:
            rxPort.apply()

        txPort.start_traffic(True)
        time.sleep(rxSleep)
        stats = rxPort.statistics
        rxPort.get_stats()

        assert int(stats.user_defined_stat_1) == burst

    @pytest.mark.skipif(simple_debug is True or Packet_Headers is False, reason="debug other test")
    def test_v6(self):

        burst = 10
        source_pattern = '33 33'
        source_offset = 24
        dest_pattern = '83 29'
        dest_offset = 52

        init__setup_ports()
        s1 = txPort.add_stream()
        txPort.streams[s1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
        txPort.streams[s1].control.packets_per_burst = burst

        txPort.streams[s1].packet.l3_proto = TGEnums.L3_PROTO.IPV6
        txPort.streams[s1].packet.ipv6.source_ip.value = "0000:3333:0000:0000:0000:0000:0000:0000"
        txPort.streams[s1].packet.ipv6.source_ip.mode = TGEnums.MODIFIER_IPV6_ADDRESS_MODE.INCREMENT_HOST
        txPort.streams[s1].packet.ipv6.destination_ip.value = "2001:0db8:0000:0000:0000:ff00:0042:8329"
        txPort.streams[s1].packet.ipv6.destination_ip.mode = TGEnums.MODIFIER_IPV6_ADDRESS_MODE.INCREMENT_INTERFACE_ID
        txPort.streams[s1].packet.ipv6.destination_ip.count = 2
        txPort.streams[s1].packet.ipv6.destination_ip.step = 2

        term1 = rxPort.filter_properties.create_match_term(source_pattern, source_offset)
        term2 = rxPort.filter_properties.create_match_term(dest_pattern, dest_offset)

        myFilter_1 = rxPort.filter_properties.filters[1]
        myFilter_1.enabled = True
        myFilter_1.add_condition(term1)

        myFilter_2 = rxPort.filter_properties.filters[2]
        myFilter_2.enabled = True
        myFilter_2.add_condition(term2)

        txPort.apply()
        if txPort is not rxPort:
            rxPort.apply()

        txPort.start_traffic(True)
        time.sleep(rxSleep)
        stats = rxPort.statistics
        rxPort.get_stats()

        assert int(stats.user_defined_stat_1) == burst
        assert int(stats.user_defined_stat_2) == burst / 2


    @pytest.mark.skipif(simple_debug is True or Packet_Headers is False, reason="debug other test")
    def test_v6_extension(self):
        #fragment_id&udp
        burst = 10
        pattern = '00 7b 02 2b'
        offset = 60
        init__setup_ports()
        s1 = txPort.add_stream()
        txPort.streams[s1].frame_size.value = 128
        txPort.streams[s1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
        txPort.streams[s1].control.packets_per_burst = burst

        txPort.streams[s1].packet.l3_proto = TGEnums.L3_PROTO.IPV6
        # txPort.streams[s1].packet.ipv6.source_ip.value = "0000:3333:0000:0000:0000:0000:0000:0000"
        # txPort.streams[s1].packet.ipv6.source_ip.mode = TGEnums.MODIFIER_IPV6_ADDRESS_MODE.INCREMENT_HOST
        # txPort.streams[s1].packet.ipv6.destination_ip.value = "2001:0db8:0000:0000:0000:ff00:0042:8329"
        # txPort.streams[s1].packet.ipv6.destination_ip.mode = TGEnums.MODIFIER_IPV6_ADDRESS_MODE.INCREMENT_INTERFACE_ID
        # txPort.streams[s1].packet.ipv6.destination_ip.count = 2
        # txPort.streams[s1].packet.ipv6.destination_ip.step = 2

        # Fragment
        frag1 = txPort.streams[s1].packet.ipv6.extention_headers.add(TGEnums.Ipv6ExtensionType.Fragment)
        txPort.streams[s1].packet.ipv6.extention_headers.fragment[frag1].id = 123
        txPort.streams[s1].packet.ipv6.extention_headers.fragment[frag1].fragment_offset = 50
        txPort.streams[s1].packet.ipv6.extention_headers.fragment[frag1].mflag = True
        txPort.streams[s1].packet.ipv6.extention_headers.fragment[frag1].reserved = 60
        txPort.streams[s1].packet.ipv6.extention_headers.fragment[frag1].res= 0

        txPort.streams[s1].packet.l4_proto = TGEnums.L4_PROTO.UDP
        txPort.streams[s1].packet.udp.source_port.value = '555'
        txPort.streams[s1].packet.tcp.destination_port.value = '777'

        term1 = rxPort.filter_properties.create_match_term(pattern,offset)

        myFilter_1 = rxPort.filter_properties.filters[1]
        myFilter_1.enabled = True
        myFilter_1.add_condition(term1)

        txPort.apply()
        if txPort is not rxPort:
            rxPort.apply()

        txPort.start_traffic(True)
        time.sleep(rxSleep)
        stats = rxPort.statistics
        rxPort.get_stats()

        assert int(stats.user_defined_stat_1) == burst


    @pytest.mark.skipif(simple_debug is True or Packet_Headers is False, reason="debug other test")
    def test_ptp(self):

        burst = 10
        pattern = '0c 02'
        offset = 42
        init__setup_ports()
        s1 = txPort.add_stream()
        txPort.streams[s1].frame_size.value = 128
        txPort.streams[s1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
        txPort.streams[s1].control.packets_per_burst = burst
        txPort.streams[s1].packet.l3_proto = TGEnums.L3_PROTO.IPV4
        txPort.streams[s1].packet.l4_proto = TGEnums.L4_PROTO.UDP
        txPort.streams[s1].packet.protocol_pad.enabled = True
        txPort.streams[s1].packet.protocol_pad.type = TGEnums.PROTOCOL_PAD_TYPE.PTP
        #txPort.streams[s1].packet.protocol_pad.custom_data = '{aa bb cc dd ee ff 11}'
        txPort.streams[s1].packet.ptp.messageType = 12
        term1 = rxPort.filter_properties.create_match_term(pattern, offset)

        myFilter_1 = rxPort.filter_properties.filters[1]
        myFilter_1.enabled = True
        myFilter_1.add_condition(term1)

        txPort.apply()
        if txPort is not rxPort:
            rxPort.apply()

        txPort.start_traffic(True)
        time.sleep(rxSleep)
        stats = rxPort.statistics
        rxPort.get_stats()

        assert int(stats.user_defined_stat_1) == burst



    @pytest.mark.skipif(simple_debug is True or Packet_Headers is False, reason="debug other test")
    def test_mpls(self):

        burst = 10
        pattern_1 = '00 07'
        offset_1 = 14
        pattern_2 = '88 47'
        offset_2 = 12

        init__setup_ports()
        s1 = txPort.add_stream()
        txPort.streams[s1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
        txPort.streams[s1].control.packets_per_burst = burst
        mpls_1 = txPort.streams[s1].packet.add_mpls_label()
        txPort.streams[s1].packet.mpls_labels[mpls_1].label = 123
        txPort.streams[s1].packet.mpls_labels[mpls_1].ttl = 20

        stats = self.run_traffic_2Patterns(pattern_1, offset_1, pattern_2, offset_2)

        assert int(stats.user_defined_stat_1) == burst
        assert int(stats.user_defined_stat_2) == burst

    @pytest.mark.skipif(simple_debug is True or Packet_Headers is False, reason="debug other test")
    def test_gre(self):

        burst = 10
        pattern_1 = '03 09'
        offset_1 = 72
        pattern_2 = '2F'
        offset_2 = 23

        init__setup_ports()
        s1 = txPort.add_stream()
        txPort.streams[s1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
        txPort.streams[s1].control.packets_per_burst = burst

        txPort.streams[s1].frame_size.value = 124
        txPort.streams[s1].packet.l3_proto = TGEnums.L3_PROTO.IPV4
        txPort.streams[s1].packet.ipv4.source_ip.value = '1.1.1.1'
        txPort.streams[s1].packet.ipv4.source_ip.mode = TGEnums.MODIFIER_IPV4_ADDRESS_MODE.INCREMENT_HOST
        txPort.streams[s1].packet.ipv4.source_ip.count = 20
        txPort.streams[s1].packet.ipv4.destination_ip.value = '2.2.2.2'
        txPort.streams[s1].packet.ipv4.dscp_decimal_value = '11'
        txPort.streams[s1].packet.ipv4.identifier = 5

        txPort.streams[s1].packet.l4_proto = TGEnums.L4_PROTO.GRE
        txPort.streams[s1].packet.gre.version = 1
        txPort.streams[s1].packet.gre.key_field = "aa"
        txPort.streams[s1].packet.gre.sequence_number = "bb"
        txPort.streams[s1].packet.gre.use_checksum = True
        txPort.streams[s1].packet.gre.l3_proto = TGEnums.L3_PROTO.IPV4
        txPort.streams[s1].packet.gre.l4_proto = TGEnums.L4_PROTO.TCP
        txPort.streams[s1].packet.gre.ipv4.source_ip.value = '7.7.7.7'
        txPort.streams[s1].packet.gre.tcp.destination_port.value = '777'

        stats = self.run_traffic_2Patterns(pattern_1, offset_1, pattern_2, offset_2)

        assert int(stats.user_defined_stat_1) == burst
        assert int(stats.user_defined_stat_2) == burst

    @pytest.mark.skipif(simple_debug is True or Packet_Headers is False, reason="debug other test")
    def test_llc_snap(self):
        burst = 10
        pattern_1 = '00 6E AA AA'
        offset_1 = 12
        pattern_2 = '08 00'
        offset_2 = 20

        init__setup_ports()
        s1 = txPort.add_stream()
        txPort.streams[s1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
        txPort.streams[s1].control.packets_per_burst = burst

        txPort.streams[s1].frame_size.value = 128
        txPort.streams[s1].packet.l2_proto = TGEnums.L2_PROTO.SNAP
        txPort.streams[s1].packet.l3_proto = TGEnums.L3_PROTO.IPV4
        txPort.streams[s1].packet.ipv4.source_ip.value = '1.1.1.1'
        txPort.streams[s1].packet.ipv4.source_ip.mode = TGEnums.MODIFIER_IPV4_ADDRESS_MODE.INCREMENT_HOST
        txPort.streams[s1].packet.ipv4.source_ip.count = 20
        txPort.streams[s1].packet.ipv4.destination_ip.value = '2.2.2.2'
        txPort.streams[s1].packet.ipv4.dscp_decimal_value = '11'
        txPort.streams[s1].packet.ipv4.identifier = 5

        stats = self.run_traffic_2Patterns(pattern_1, offset_1, pattern_2, offset_2)

        assert int(stats.user_defined_stat_1) == burst
        assert int(stats.user_defined_stat_2) == burst

    @pytest.mark.skipif(simple_debug is True or Packet_Headers is False, reason="debug other test")
    def test_v6_over_v4(self):
        burst = 10
        pattern_1 = '29'
        offset_1 = 23
        pattern_2 = '00 54'
        offset_2 = 74

        init__setup_ports()
        s1 = txPort.add_stream()
        txPort.streams[s1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
        txPort.streams[s1].control.packets_per_burst = burst

        txPort.streams[s1].frame_size.value = 128
        txPort.streams[s1].packet.l3_proto = TGEnums.L3_PROTO.IPV6_O_IPV4
        txPort.streams[s1].packet.ipv4.source_ip.value = '1.1.1.1'
        txPort.streams[s1].packet.ipv4.source_ip.mode = TGEnums.MODIFIER_IPV4_ADDRESS_MODE.INCREMENT_HOST
        txPort.streams[s1].packet.ipv4.source_ip.count = 20
        txPort.streams[s1].packet.ipv4.destination_ip.value = '2.2.2.2'
        txPort.streams[s1].packet.ipv4.dscp_decimal_value = '11'
        txPort.streams[s1].packet.ipv4.identifier = 5

        txPort.streams[s1].packet.l4_proto = TGEnums.L4_PROTO.UDP
        txPort.streams[s1].packet.udp.source_port.value = 84
        txPort.streams[s1].packet.udp.destination_port.value = 65535
        txPort.streams[s1].packet.udp.valid_checksum = TGEnums.CHECKSUM_MODE.VALID
        txPort.streams[s1].packet.udp.custom_checksum = "0x3333"

        stats = self.run_traffic_2Patterns(pattern_1, offset_1, pattern_2, offset_2)

        assert int(stats.user_defined_stat_1) == burst
        assert int(stats.user_defined_stat_2) == burst

    @pytest.mark.skipif(simple_debug is True or Packet_Headers is False, reason="debug other test")
    def test_v4_over_v6(self):
        burst = 10
        pattern_1 = '04'
        offset_1 = 20
        pattern_2 = '00 54'
        offset_2 = 74

        init__setup_ports()
        s1 = txPort.add_stream()
        txPort.streams[s1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
        txPort.streams[s1].control.packets_per_burst = burst

        txPort.streams[s1].frame_size.value = 128
        txPort.streams[s1].packet.l3_proto = TGEnums.L3_PROTO.IPV4_O_IPV6
        txPort.streams[s1].packet.ipv4.source_ip.value = '1.1.1.1'
        txPort.streams[s1].packet.ipv4.source_ip.mode = TGEnums.MODIFIER_IPV4_ADDRESS_MODE.INCREMENT_HOST
        txPort.streams[s1].packet.ipv4.source_ip.count = 20
        txPort.streams[s1].packet.ipv4.destination_ip.value = '2.2.2.2'
        txPort.streams[s1].packet.ipv4.dscp_decimal_value = '11'
        txPort.streams[s1].packet.ipv4.identifier = 5

        txPort.streams[s1].packet.l4_proto = TGEnums.L4_PROTO.UDP
        txPort.streams[s1].packet.udp.source_port.value = 84
        txPort.streams[s1].packet.udp.destination_port.value = 65535
        txPort.streams[s1].packet.udp.valid_checksum = TGEnums.CHECKSUM_MODE.VALID
        txPort.streams[s1].packet.udp.custom_checksum = "0x3333"

        stats = self.run_traffic_2Patterns(pattern_1, offset_1, pattern_2, offset_2)

        assert int(stats.user_defined_stat_1) == burst
        assert int(stats.user_defined_stat_2) == burst

    @pytest.mark.skipif(simple_debug is True or Packet_Headers is False, reason="debug other test")
    def test_stacked_vlan(self):
        burst = 10
        pattern_1 = '91 00'
        offset_1 = 12
        pattern_2 = '81 00'
        offset_2 = 16

        init__setup_ports()
        s1 = txPort.add_stream()
        txPort.streams[s1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
        txPort.streams[s1].control.packets_per_burst = burst

        Vid1 = 1
        Vid2 = Vid1 * 2

        firstVlan = txPort.streams[s1].packet.add_vlan()
        txPort.streams[s1].packet.vlans[firstVlan].vid.value = str(Vid1)
        txPort.streams[s1].packet.vlans[firstVlan].priority = "0"
        txPort.streams[s1].packet.vlans[firstVlan].cfi = "0"
        txPort.streams[s1].packet.vlans[firstVlan].vid.mode = TGEnums.MODIFIER_VLAN_MODE.FIXED
        txPort.streams[s1].packet.vlans[firstVlan].vid.count = 1
        txPort.streams[s1].packet.vlans[firstVlan].proto = "0x9100"

        secondVlan = txPort.streams[s1].packet.add_vlan()
        txPort.streams[s1].packet.vlans[secondVlan].vid.value = str(Vid2)
        txPort.streams[s1].packet.vlans[secondVlan].priority = 3
        txPort.streams[s1].packet.vlans[secondVlan].cfi = "1"
        txPort.streams[s1].packet.vlans[secondVlan].vid.mode = TGEnums.MODIFIER_VLAN_MODE.INCREMENT
        txPort.streams[s1].packet.vlans[secondVlan].vid.count = 50

        stats = self.run_traffic_2Patterns(pattern_1, offset_1, pattern_2, offset_2)

        assert int(stats.user_defined_stat_1) == burst
        assert int(stats.user_defined_stat_2) == burst


    @pytest.mark.skipif(simple_debug is True or Packet_Headers is False or vendorType != 'Ixia', reason="debug other test")
    def test_arp_request(self):
        burst = 10
        pattern_1 = '00 01'
        offset_1 = 20
        pattern_2 = '11 11'
        offset_2 = 26

        init__setup_ports()
        s0 = txPort.add_stream()
        txPort.streams[s0].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
        txPort.streams[s0].control.packets_per_burst = burst
        txPort.streams[s0].packet.l2_proto = TGEnums.L2_PROTO.ETHERNETII
        txPort.streams[s0].packet.l3_proto = TGEnums.L3_PROTO.ARP
        txPort.streams[s0].packet.arp.operation = TGEnums.ARP_OPERATION.ARP_REQUEST
        txPort.streams[s0].packet.arp.sender_hw.value = '00:00:00:00:11:11'
        txPort.streams[s0].packet.arp.sender_hw.mode = TGEnums.MODIFIER_ARP_MODE.INCREMENT
        txPort.streams[s0].packet.arp.sender_hw.count = burst/2

        stats = self.run_traffic_2Patterns(pattern_1, offset_1, pattern_2, offset_2)
        assert int(stats.user_defined_stat_1) == burst
        assert int(stats.user_defined_stat_2) == burst/int(float(txPort.streams[s0].packet.arp.sender_hw.count))



    @pytest.mark.skipif(simple_debug is True or Packet_Headers is False or vendorType != 'Ixia', reason="debug other test")
    def test_arp_reply(self):
        burst = 20
        pattern_1 = '00 02'
        offset_1 = 20
        pattern_2 = '02 01'
        offset_2 = 30
        init__setup_ports()

        s1 = txPort.add_stream()
        txPort.streams[s1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
        txPort.streams[s1].control.packets_per_burst = burst
        txPort.streams[s1].packet.l2_proto = TGEnums.L2_PROTO.ETHERNETII
        txPort.streams[s1].packet.l3_proto = TGEnums.L3_PROTO.ARP
        txPort.streams[s1].packet.arp.operation = TGEnums.ARP_OPERATION.ARP_REPLY
        txPort.streams[s1].packet.arp.sender_hw.value = '00:00:77:77:77:77'
        txPort.streams[s1].packet.arp.sender_hw.mode = TGEnums.MODIFIER_ARP_MODE.DECREMENT
        txPort.streams[s1].packet.arp.sender_hw.count = burst/4
        txPort.streams[s1].packet.arp.sender_ip.value = "2.2.2.1"
        txPort.streams[s1].packet.arp.sender_ip.mode = TGEnums.MODIFIER_ARP_MODE.DECREMENT
        txPort.streams[s1].packet.arp.sender_ip.count = burst/4

        stats = self.run_traffic_2Patterns(pattern_1, offset_1, pattern_2, offset_2)
        assert int(stats.user_defined_stat_1) == burst
        assert int(stats.user_defined_stat_2) == burst/int(float(txPort.streams[s1].packet.arp.sender_hw.count))

    @pytest.mark.skipif(simple_debug is True or Packet_Headers is False or vendorType != 'Ixia', reason="debug other test")
    def test_imcp(self):
        burst = 20
        pattern_1 = '08 7B'
        offset_1 = 34
        pattern_2 = '03 E7 '
        offset_2 = 38
        init__setup_ports()
        s1 = txPort.add_stream()
        txPort.streams[s1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
        txPort.streams[s1].control.packets_per_burst = burst
        txPort.streams[s1].packet.l2_proto = TGEnums.L2_PROTO.ETHERNETII
        txPort.streams[s1].packet.l3_proto = TGEnums.L3_PROTO.IPV4
        txPort.streams[s1].packet.l4_proto = TGEnums.L4_PROTO.ICMP
        txPort.streams[s1].packet.icmp.icmp_type = TGEnums.ICMP_HEADER_TYPE.ECHO_REQUEST
        txPort.streams[s1].packet.icmp.code = 123
        txPort.streams[s1].packet.icmp.id = 999
        txPort.streams[s1].packet.icmp.sequence = 784
        txPort.apply_streams()
        stats = self.run_traffic_2Patterns(pattern_1, offset_1, pattern_2, offset_2)
        assert int(stats.user_defined_stat_1) == burst
        assert int(stats.user_defined_stat_2) == burst




class Test_Statistics(object):

    @pytest.mark.skipif(simple_debug is True or Statistics_suite is False, reason="debug other test")
    def test_advanced_stats_autoDI(self):
        init__setup_ports()
        stream1 = txPort.add_stream()
        # TX
        txPort.streams[stream1].instrumentation.automatic_enabled = True
        # txPort.streams[stream1].instrumentation.time_stamp_enabled = True
        # txPort.streams[stream1].instrumentation.packet_grouops_enabled =True
        # txPort.streams[stream1].instrumentation.sequence_checking_enabled = True
        txPort.streams[stream1].packet.data_integrity.enable = True
        # RX
        rxPort.receive_mode.automatic_signature.enabled = True
        # rxPort.receive_mode.wide_packet_group = True
        # rxPort.receive_mode.data_inetgrity = True
        txPort.apply()
        rxPort.apply()
        tg.clear_all_stats([txPort, rxPort])
        txPort.start_packet_groups()
        txPort.start_traffic()
        time.sleep(1)
        txPort.stop_traffic()
        time.sleep(1)
        tg.get_all_ports_stats()
        tg.get_advanced_stats()
        assert txPort.statistics.frames_sent == rxPort.statistics.data_integrity_frames
        assert txPort.statistics.frames_sent > 0
        assert rxPort.statistics.data_integrity_errors == 0


class Test_Streams_Suite(object):

    @pytest.mark.skipif(simple_debug is True or Streams_Suite is False, reason="debug other test")
    def test_ContMode_2streams(self):
        init__setup_ports()
        stream1 = txPort.add_stream()
        txPort.streams[stream1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.CONTINUOUS_PACKET
        txPort.streams[stream1].rate.mode = TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND
        txPort.streams[stream1].rate.pps_value = 1000
        txPort.streams[stream1].control.packets_per_burst = 100
        stream2 = txPort.add_stream()
        txPort.streams[stream2].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
        txPort.streams[stream2].rate.mode = TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND
        txPort.streams[stream2].rate.pps_value = 1000
        txPort.streams[stream1].control.packets_per_burst = 5

        txPort.apply()

        txPort.clear_all_statistics()
        txPort.start_traffic()
        stats = txPort.statistics
        time.sleep(rxSleep)
        txPort.get_stats()
        txPort.stop_traffic()

        assert int(stats.frames_sent) > 200

        txPort.streams[stream1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.ADVANCE_TO_NEXT_STREAM
        txPort.apply()

        txPort.clear_all_statistics()
        txPort.start_traffic()
        time.sleep(rxSleep)
        txPort.get_stats()
        txPort.stop_traffic()

        assert int(stats.frames_sent) == 105




class Test_Ports_Suite(object):

    @pytest.mark.skipif(simple_debug is True or Ports_Suite is False, reason="debug other test")
    def test_group_tx(self):
        init__setup_ports()
        txPort.add_stream()
        rxPort.add_stream()
        txPort.apply()
        rxPort.apply()

        def test_group(ports_list):
            tg.start_traffic(ports_list)
            time.sleep(1)
            txPort.get_stats()
            assert 0 < int(txPort.statistics.frames_sent)
            if type(ports_list) is list and len(ports_list)>1:
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

        test_group(txPort)
        test_group([txPort,rxPort])
        test_group(txPort._port_name)
        test_group([txPort._port_name, rxPort._port_name])



    @pytest.mark.skipif(simple_debug is True or Ports_Suite is False, reason="debug other test")
    def test_blocking_tx_modes(self):
        init__setup_ports()
        stream1 = txPort.add_stream()
        stream2 = txPort.add_stream()
        txPort.streams[stream1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.ADVANCE_TO_NEXT_STREAM
        txPort.streams[stream2].control.mode = TGEnums.STREAM_TRANSMIT_MODE.ADVANCE_TO_NEXT_STREAM
        assert not txPort._is_continuous_traffic()
        txPort.streams[stream2].control.mode = TGEnums.STREAM_TRANSMIT_MODE.RETURN_TO_ID
        assert txPort._is_continuous_traffic()
        txPort.streams[stream1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
        assert not txPort._is_continuous_traffic()

    @pytest.mark.skipif(simple_debug is True or Ports_Suite is False, reason="debug other test")
    def test_blocking_tx_negative(self):
        init__setup_ports()
        stream1 = txPort.add_stream()
        txPort.streams[stream1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.ADVANCE_TO_NEXT_STREAM
        txPort.streams[stream1].rate.mode = TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND
        txPort.streams[stream1].rate.pps_value = 10
        txPort.streams[stream1].control.packets_per_burst = 100
        stream2 = txPort.add_stream()
        txPort.streams[stream2].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
        txPort.streams[stream2].rate.mode = TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND
        txPort.streams[stream2].rate.pps_value = 10
        txPort.streams[stream2].control.packets_per_burst = 20
        txPort.apply()
        txPort.clear_all_statistics()
        txPort.start_traffic()
        stats = txPort.statistics
        txPort.get_stats()

        assert 120 > int(stats.frames_sent)

    @pytest.mark.skipif(simple_debug is True or Ports_Suite is False, reason="debug other test")
    def test_blocking_tx_positive(self):
        init__setup_ports()
        stream1 = txPort.add_stream()
        txPort.streams[stream1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.ADVANCE_TO_NEXT_STREAM
        txPort.streams[stream1].rate.mode = TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND
        txPort.streams[stream1].rate.pps_value = 10
        txPort.streams[stream1].control.packets_per_burst = 100
        stream2 = txPort.add_stream()
        txPort.streams[stream2].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
        txPort.streams[stream2].rate.mode = TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND
        txPort.streams[stream2].rate.pps_value = 10
        txPort.streams[stream2].control.packets_per_burst = 20

        txPort.apply()

        txPort.clear_all_statistics()
        txPort.start_traffic(blocking=True)
        stats = txPort.statistics
        time.sleep(0.1)
        txPort.get_stats()

        assert 120 == int(stats.frames_sent)


class Test_Capture_Suite(object):

    @pytest.mark.skipif(simple_debug is True or Capture_Suite is False, reason="debug other test")
    def test_Capture_default_view(self):

        init__setup_ports()

        req_field = 'eth.dst'
        req_field_value = '00:00:00:00:00:02'
        burst = 10
        rxPort.analyzer.init_default_view(filter=req_field + '== '+req_field_value, fields=[req_field])

        stream1 = txPort.add_stream()
        txPort.streams[stream1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
        txPort.streams[stream1].control.packets_per_burst = burst
        txPort.apply()
        rxPort.start_capture()
        txPort.start_traffic(True)
        rxPort.stop_capture()

        retries = 3
        for i in range(1,retries):
            if i < retries : #and vendorType == 'Ostinato'
                time.sleep(1)
                try:
                    res = rxPort.analyzer.default_view.result[0][req_field][0]
                    assert req_field_value == res
                    assert burst == len(rxPort.analyzer.default_view.result)
                    break
                except Exception as e:
                    pass
            else:
                res = rxPort.analyzer.default_view.result[0][req_field][0]
                assert req_field_value == res
                assert burst == len(rxPort.analyzer.default_view.result)
        if vendorType == 'Ostinato':
            time.sleep(6)

class Test_Vlans_Suite(object):

    @pytest.mark.skipif(simple_debug is True or Vlan_Suite is False, reason="debug other test")
    def test_Vlan_and_streamControl(self):

        init__setup_ports()


        macSA = "aa:bb:00:22:22:22"
        macDA = "cc:dd:00:33:33:33"
        Vid1 = 2
        txPort.properties
        pktLength = 128
        numOfPackets = 10

        stream1 = txPort.add_stream()
        stream1Obj = txPort.streams[stream1]
        # Configure the Stream Control Properties - traffic rate and number of frames
        txPort.streams[stream1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM  # this stream send Bursts
        txPort.streams[stream1].control.packets_per_burst = numOfPackets
        txPort.streams[stream1].control.bursts_per_stream = 1
        # Configure the Stream Rate Properties
        txPort.streams[stream1].rate.mode = TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND  # PPS unit
        txPort.streams[stream1].rate.pps_value = 100  # this stream will send 100 packets per second

        # Configure the Stream Packet Fields - L2 untagged Packet with src \ dst MAC addresses
        txPort.streams[stream1].packet.mac.sa.value = macSA
        txPort.streams[stream1].packet.mac.da.value = macDA
        txPort.streams[stream1].frame_size.value = pktLength

        firstVlan = txPort.streams[stream1].packet.add_vlan()
        txPort.streams[stream1].packet.vlans[firstVlan].vid.value = Vid1
        txPort.streams[stream1].packet.vlans[firstVlan].priority = 0
        txPort.streams[stream1].packet.vlans[firstVlan].cfi = 0
        txPort.streams[stream1].packet.vlans[firstVlan].vid.mode = TGEnums.MODIFIER_VLAN_MODE.FIXED
        txPort.streams[stream1].packet.vlans[firstVlan].vid.count = 1

        txPort.apply()
        vid = stream1Obj._get_field_hw_value(stream1Obj.packet.vlans[firstVlan].vid._value)
        assert vid is Vid1
        #additional test stream control
        frameSize = stream1Obj._get_field_hw_value(stream1Obj.frame_size._value )
        assert frameSize == txPort.streams[stream1].frame_size.value
        pps = stream1Obj._get_field_hw_value(stream1Obj.rate._pps_value)
        assert pps == txPort.streams[stream1].rate.pps_value
        mode = int(stream1Obj._get_field_hw_value(stream1Obj.rate._mode))
        assert mode == txPort.streams[stream1].rate.mode.value

    @pytest.mark.skipif(simple_debug is True or Vlan_Suite is False, reason="debug other test")
    def test_StackedVlan(self):

        init__setup_ports()

        Vid1 = 2
        Vid2 = Vid1*2

        stream1 = txPort.add_stream()
        stream1Obj = txPort.streams[stream1]

        firstVlan = txPort.streams[stream1].packet.add_vlan()
        txPort.streams[stream1].packet.vlans[firstVlan].vid.value = str(Vid1)
        txPort.streams[stream1].packet.vlans[firstVlan].priority = "0"
        txPort.streams[stream1].packet.vlans[firstVlan].cfi = "0"
        txPort.streams[stream1].packet.vlans[firstVlan].vid.mode = TGEnums.MODIFIER_VLAN_MODE.FIXED
        txPort.streams[stream1].packet.vlans[firstVlan].vid.count = 1

        secondVlan = txPort.streams[stream1].packet.add_vlan()
        txPort.streams[stream1].packet.vlans[secondVlan].vid.value = str(Vid2)
        txPort.streams[stream1].packet.vlans[secondVlan].priority = 3
        txPort.streams[stream1].packet.vlans[secondVlan].cfi = "1"
        txPort.streams[stream1].packet.vlans[secondVlan].vid.mode = TGEnums.MODIFIER_VLAN_MODE.INCREMENT
        txPort.streams[stream1].packet.vlans[secondVlan].vid.count = 50
        txPort.apply()

        vid = int(stream1Obj._get_field_hw_value(stream1Obj.packet.vlans[secondVlan].vid._value))
        assert vid is Vid2

class Test_Trigger_Suite(object):

    @pytest.mark.skipif(simple_debug is True or Trigger_Suite is False, reason="debug other test")
    def test_trigger_2patterns_1filter(self):

        # if txPort.properties.speed is TGEnums.PORT_PROPERTIES_SPEED.GIGA_400:
        #     assert False

        def run(udfList):
            txPort.streams[stream1].packet.modifiers[udf1Name].enabled = False
            txPort.streams[stream1].packet.modifiers[udf2Name].enabled = False
            for udfName in udfList:
                txPort.streams[stream1].packet.modifiers[udfName].enabled = True
            if len(udfList)>1:
                expectedtriger1 = burst/txPort.streams[stream1].packet.modifiers[udf1Name].repeat_count
            else :
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
        txPort.streams[stream1].packet.modifiers[udf1Name].mode = TGEnums.MODIFIER_UDF_MODE.COUNTER
        txPort.streams[stream1].packet.modifiers[udf1Name].continuously_counting = False
        txPort.streams[stream1].packet.modifiers[udf1Name].repeat_count =  burst/5
        txPort.streams[stream1].packet.modifiers[udf1Name].repeat_init = testPattern
        txPort.streams[stream1].packet.modifiers[udf1Name].repeat_mode = TGEnums.MODIFIER_UDF_REPEAT_MODE.DOWN
        txPort.streams[stream1].packet.modifiers[udf1Name].repeat_step = 1

        udf2Name = txPort.streams[stream1].packet.add_modifier()
        udf2 = txPort.streams[stream1].packet.modifiers[udf2Name]
        udf2.enabled = True
        udf2.byte_offset = patternOffset2
        udf2.bit_type = TGEnums.MODIFIER_UDF_BITS_MODE.BITS_32
        udf2.mode = TGEnums.MODIFIER_UDF_MODE.COUNTER
        udf2.continuously_counting = False
        udf2.repeat_count = burst/5
        udf2.repeat_init = pattern2
        udf2.repeat_mode = TGEnums.MODIFIER_UDF_REPEAT_MODE.UP
        udf2.repeat_step = 1
        #udf2.from_chain = TGEnums.MODIFIER_UDF_FROM_CHAIN_MODE.UDF1

        term1 = rxPort.filter_properties.create_match_term(testPattern,testOffset)
        term2 = rxPort.filter_properties.create_match_term(pattern2, patternOffset2+offset_adapter)

        myFilter_1 = rxPort.filter_properties.filters[1]
        myFilter_1.enabled = True
        myFilter_1.add_condition(term1)
        myFilter_1.add_condition(term2)

        #if txPort.properties.speed is not TGEnums.PORT_PROPERTIES_SPEED.GIGA_400:
            #run([udf1Name])
            #run([udf2Name])
        run([udf1Name,udf2Name])

    @pytest.mark.skipif(simple_debug is True or Trigger_Suite is False, reason="debug other test")
    def test_trigger_2patterns_2filters(self):

        # if txPort.properties.speed is TGEnums.PORT_PROPERTIES_SPEED.GIGA_400:
        #     assert False

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
        txPort.streams[stream1].packet.modifiers[udf1Name].mode = TGEnums.MODIFIER_UDF_MODE.COUNTER
        txPort.streams[stream1].packet.modifiers[udf1Name].continuously_counting = False
        txPort.streams[stream1].packet.modifiers[udf1Name].repeat_count =  burst/5
        txPort.streams[stream1].packet.modifiers[udf1Name].repeat_init = testPattern
        txPort.streams[stream1].packet.modifiers[udf1Name].repeat_mode = TGEnums.MODIFIER_UDF_REPEAT_MODE.DOWN
        txPort.streams[stream1].packet.modifiers[udf1Name].repeat_step = 1

        udf2Name = txPort.streams[stream1].packet.add_modifier()
        udf2 = txPort.streams[stream1].packet.modifiers[udf2Name]
        udf2.enabled = True
        udf2.byte_offset = patternOffset2
        udf2.bit_type = TGEnums.MODIFIER_UDF_BITS_MODE.BITS_32
        udf2.mode = TGEnums.MODIFIER_UDF_MODE.COUNTER
        udf2.continuously_counting = False
        udf2.repeat_count = 5
        udf2.repeat_init = pattern2
        udf2.repeat_mode = TGEnums.MODIFIER_UDF_REPEAT_MODE.UP
        udf2.repeat_step = 5

        term1 = rxPort.filter_properties.create_match_term(testPattern,testOffset)
        term2 = rxPort.filter_properties.create_match_term(pattern2, patternOffset2+offset_adapter)

        myFilter_1 = rxPort.filter_properties.filters[1]
        myFilter_1.enabled = True
        myFilter_1.add_condition(term1)

        myFilter2 = rxPort.filter_properties.filters[2]
        myFilter2.enabled = True
        myFilter2.add_condition(term2)

        txPort.apply()
        if txPort is not rxPort:
            rxPort.apply()

        stable_link_state(txPort,TGEnums.Link_State.linkLoopback)
        txPort.start_traffic()

        time.sleep(rxSleep)
        stats = rxPort.statistics
        rxPort.get_stats()

        expectedtriger1 = burst/txPort.streams[stream1].packet.modifiers[udf1Name].repeat_count
        assert int(stats.user_defined_stat_1) == expectedtriger1
        assert int(stats.user_defined_stat_2) == 2

    @pytest.mark.skipif(simple_debug is True or Trigger_Suite is False, reason="debug other test")
    def test_trigger_pattern_and_not(self):

        testPattern = '22 33'
        testOffset = 24
        burst = 10

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
        txPort.streams[stream1].packet.modifiers[udf1Name].mode = TGEnums.MODIFIER_UDF_MODE.COUNTER
        txPort.streams[stream1].packet.modifiers[udf1Name].continuously_counting = False
        txPort.streams[stream1].packet.modifiers[udf1Name].repeat_count = burst/2
        txPort.streams[stream1].packet.modifiers[udf1Name].repeat_init = testPattern
        txPort.streams[stream1].packet.modifiers[udf1Name].repeat_mode = TGEnums.MODIFIER_UDF_REPEAT_MODE.DOWN
        txPort.streams[stream1].packet.modifiers[udf1Name].repeat_step = 1

        term1 = rxPort.filter_properties.create_match_term(testPattern,testOffset)

        myFilter_1 = rxPort.filter_properties.filters[1]
        myFilter_1.enabled = True
        myFilter_1.add_condition(term1)

        myFilter2 = rxPort.filter_properties.filters[2]
        myFilter2.enabled = True
        myFilter2.add_condition(term1,TGEnums.LOGICAL_OPERATOR.NOT)

        txPort.apply()
        if txPort is not rxPort:
            rxPort.apply()

        stable_link_state(txPort, TGEnums.Link_State.linkLoopback)
        txPort.start_traffic()

        time.sleep(rxSleep)
        stats = rxPort.statistics
        rxPort.get_stats()

        expectedtriger1 = burst / txPort.streams[stream1].packet.modifiers[udf1Name].repeat_count
        assert int(stats.user_defined_stat_1) == expectedtriger1
        if int(stats.user_defined_stat_2) != burst - expectedtriger1:
            print ("Not good!!!")
        assert int(stats.user_defined_stat_2) == burst - expectedtriger1

    @pytest.mark.skipif(simple_debug is True or Trigger_Suite is False, reason="debug other test")
    def test_trigger_mac(self):

        daMac = "00:00:00:11:11:aa"
        daOffset = 0
        saMac = "aa:bb:00:22:22:BB"
        saOffset = 6
        burst = 10

        init__setup_ports()

        stream1 = txPort.add_stream()
        txPort.streams[stream1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.ADVANCE_TO_NEXT_STREAM
        txPort.streams[stream1].control.packets_per_burst = burst
        txPort.streams[stream1].rate.mode = TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND
        txPort.streams[stream1].rate.pps_value = 100
        txPort.streams[stream1].packet.mac.sa.value = saMac
        txPort.streams[stream1].packet.mac.da.value = daMac

        termDA = rxPort.filter_properties.create_match_term(daMac, daOffset)
        termSA = rxPort.filter_properties.create_match_term(saMac, saOffset)
        termSize = txPort.filter_properties.create_size_match_term(from_size=48, to_size=256)

        myFilter_1 = rxPort.filter_properties.filters[1]
        myFilter_1.enabled = True
        myFilter_1.add_condition(termDA)
        myFilter_1.add_condition(termSA)
        myFilter_1.add_condition(termSize)

        myFilter2 = rxPort.filter_properties.filters[2]
        myFilter2.enabled = True
        myFilter2.add_condition(termSA)

        txPort.apply()
        if txPort is not rxPort:
            rxPort.apply()

        stable_link_state(txPort, TGEnums.Link_State.linkLoopback)
        txPort.start_traffic()

        stats = rxPort.statistics
        time.sleep(rxSleep)
        rxPort.get_stats()

        assert int(stats.user_defined_stat_1) is burst
        assert int(stats.user_defined_stat_2) is burst

        rxPort.clear_all_statistics()

        txPort.streams[stream1].packet.mac.da.mode = TGEnums.MODIFIER_MAC_MODE.INCREMENT
        txPort.streams[stream1].packet.mac.da.count = 2

        txPort.apply()

        stable_link_state(txPort, TGEnums.Link_State.linkLoopback)
        txPort.start_traffic()
        time.sleep(rxSleep)
        rxPort.get_stats()

        assert int(stats.user_defined_stat_1) == burst/2
        assert int(stats.user_defined_stat_2) == burst

    @pytest.mark.skipif(simple_debug is True or Trigger_Suite is False, reason="debug other test")
    def test_trigger_payload(self):

        def run(positive):
            if positive:
                expected = burst
                txPort.streams[stream1].packet.data_pattern.value = DataPattern
                txPort.streams[stream1].packet.data_pattern.type = TGEnums.DATA_PATTERN_TYPE.FIXED
            else:
                txPort.streams[stream1].packet.data_pattern.type = TGEnums.DATA_PATTERN_TYPE.RANDOM
                expected = 0
            txPort.apply()
            if txPort is not rxPort:
                rxPort.apply()
            rxPort.clear_all_statistics()
            txPort.start_traffic()
            stats = rxPort.statistics
            time.sleep(rxSleep)
            rxPort.get_stats()
            assert int(stats.user_defined_stat_1) is expected

        DataPattern = "88f72f02002f0001"
        plOffset = 12
        burst = 10
        init__setup_ports()

        stream1 = txPort.add_stream()
        txPort.streams[stream1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.ADVANCE_TO_NEXT_STREAM
        txPort.streams[stream1].control.packets_per_burst = burst
        txPort.streams[stream1].rate.mode = TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND
        txPort.streams[stream1].rate.pps_value = 100
        txPort.streams[stream1].packet.l2_proto = TGEnums.L2_PROTO.NONE

        termPL = rxPort.filter_properties.create_match_term(DataPattern, plOffset)
        myFilter_1 = rxPort.filter_properties.filters[1]
        myFilter_1.enabled = True
        myFilter_1.add_condition(termPL)

        run(False)
        run(True)

    @pytest.mark.skipif(simple_debug is True or Trigger_Suite is False or vendorType != 'Ixia', reason="debug other test")
    def test_capture_filter_stats(self):

        daMac = "00:00:FF:44:44:44"
        saMac = "00:00:E0:55:55:55"
        burst = 10

        init__setup_ports()

        stream1 = txPort.add_stream()
        txPort.streams[stream1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.ADVANCE_TO_NEXT_STREAM
        txPort.streams[stream1].control.packets_per_burst = burst
        txPort.streams[stream1].rate.mode = TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND
        txPort.streams[stream1].rate.pps_value = 100
        txPort.streams[stream1].packet.mac.sa.value = saMac
        txPort.streams[stream1].packet.mac.da.value = daMac
        txPort.streams[stream1].packet.mac.da.mode = TGEnums.MODIFIER_MAC_MODE.INCREMENT
        txPort.streams[stream1].packet.mac.da.count = 2

        termDA = rxPort.filter_properties.create_match_term(daMac, 0)
        termSA = rxPort.filter_properties.create_match_term(saMac, 6)

        captureFilter = rxPort.filter_properties.capture_filter
        captureFilter.enabled = True
        captureFilter.add_condition(termDA)
        captureFilter.add_condition(termSA)

        txPort.apply()
        if txPort is not rxPort:
            rxPort.apply()

        stable_link_state(txPort, TGEnums.Link_State.linkLoopback)
        txPort.start_traffic()

        time.sleep(rxSleep)
        stats = rxPort.statistics
        rxPort.get_stats()

        expectedCount = burst/int(txPort.streams[stream1].packet.mac.da.count)
        assert int(stats.capture_filter) == expectedCount

    @pytest.mark.skipif(simple_debug is True or Trigger_Suite is False, reason="debug other test")
    def test_udf_list(self):

        testOffset = 24
        burst = 9
        testPattern = 'AD AD'
        pattern2 = 'BB BB'

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
        txPort.streams[stream1].packet.modifiers[udf1Name].mode = TGEnums.MODIFIER_UDF_MODE.VALUE_LIST
        txPort.streams[stream1].packet.modifiers[udf1Name].value_list = '{{AD AD} {00 00} {BB BB}}'

        term1 = rxPort.filter_properties.create_match_term(testPattern,testOffset)
        term2 = rxPort.filter_properties.create_match_term(pattern2, testOffset)

        myFilter_1 = rxPort.filter_properties.filters[1]
        myFilter_1.enabled = True
        myFilter_1.add_condition(term1)
        myFilter_2 = rxPort.filter_properties.filters[2]
        myFilter_2.enabled = True
        myFilter_2.add_condition(term2)
        txPort.apply()

        if txPort is not rxPort:
            rxPort.apply()
        rxPort.clear_all_statistics()
        txPort.start_traffic()

        time.sleep(rxSleep)
        stats = rxPort.statistics
        rxPort.get_stats()
        expectedtriger1 = 3
        if int(stats.user_defined_stat_1) != expectedtriger1:
            print ("Not good!!!")
        assert expectedtriger1 == int(stats.user_defined_stat_1)
        if int(stats.user_defined_stat_2) != expectedtriger1:
            print ("Not good!!!")
        assert expectedtriger1 == int(stats.user_defined_stat_1)


class Test_FlowControl_Suite(object):
    # @classmethod
    # def setUpClass(cls):
    #     pass
    # @classmethod
    # def tearDownClass(cls):
    #     pass
    @classmethod
    def equal_check(self,actual,expected):
        assert expected == actual

    @classmethod
    def enable_pfc(cls):
        p1 = txPort
        fc = p1.properties.flow_control
        fc.enable = True
        fc.type = TGEnums.Flow_Control_Type.IEEE802_1Qbb
        p1.apply()

    @pytest.mark.skipif(simple_debug is True or FlowControl_Suite is False, reason="debug other test")
    def test_stream_priority(self):
        p1 = txPort
        p1.reset_factory_defaults()
        Test_FlowControl_Suite.enable_pfc()
        stream1 = txPort.add_stream()
        stream1Obj = txPort.streams[stream1]
        stream1Obj.control.pfc_queue = 3
        p1.apply()
        priority = stream1Obj._get_field_hw_value(stream1Obj.control._pfc_queue)
        assert priority == stream1Obj.control.pfc_queue

    @pytest.mark.skipif(simple_debug is True or FlowControl_Suite is False, reason="debug other test")
    def test_enable_disable(self):
        p1 = txPort
        p1.reset_factory_defaults()
        p1.properties.flow_control.enable = True
        p1.apply()
        state = p1._get_field_hw_value(p1.properties.flow_control._enabled)
        assert state is p1.properties.flow_control.enable
        p1.properties.flow_control.enable = False
        p1.apply()
        state = bool(p1._get_field_hw_value(p1.properties.flow_control._enabled))
        assert state is p1.properties.flow_control.enable

    @pytest.mark.skipif(simple_debug is True or FlowControl_Suite is False, reason="debug other test")
    def test_typeQQ(self):
        p1 = txPort
        if p1.properties.speed < TGEnums.PORT_PROPERTIES_SPEED.GIGA_10:
            return
        p1.reset_factory_defaults()
        fc = p1.properties.flow_control
        Test_FlowControl_Suite.enable_pfc()
        type = p1._get_field_hw_value(p1.properties.flow_control._type)
        Test_FlowControl_Suite.equal_check(type,fc.type.value)
        fc.type = TGEnums.Flow_Control_Type.IEEE802_3x
        p1.apply()
        type = p1._get_field_hw_value(p1.properties.flow_control._type)
        Test_FlowControl_Suite.equal_check(type,fc.type.value)

    # @pytest.mark.skipif(simple_debug is True or FlowControl_Suite is False, reason="debug other test")
    # def test_mc_directed_addresses(self):
    #     p1 = txPort
    #     if p1.properties.speed < TGEnums.PORT_PROPERTIES_SPEED.GIGA_10:
    #         return
    #     p1.reset_factory_defaults()
    #     fc = p1.properties.flow_control
    #     fc.multicast_pause_address = '01 80 C2 00 00 05'
    #     fc.directed_address = '01 80 C2 00 00 06'
    #     Test_FlowControl_Suite.enable_pfc()
    #
    #     mc ='{'+p1._get_field_hw_value(p1.properties.flow_control._multicast_pause_address)+'}'
    #     Test_FlowControl_Suite.equal_check(mc, fc.multicast_pause_address)
    #     dc ='{'+ p1._get_field_hw_value(p1.properties.flow_control._directed_address)+'}'
    #     Test_FlowControl_Suite.equal_check(dc,fc.directed_address)

    @pytest.mark.skipif(simple_debug is True or FlowControl_Suite is False, reason="debug other test")
    def test_priority_matrix(self):
        p1 = txPort
        if p1.properties.speed < TGEnums.PORT_PROPERTIES_SPEED.GIGA_10:
            return
        p1.reset_factory_defaults()
        fc = p1.properties.flow_control
        fc.pfc_matrix[1].enable = True
        fc.pfc_matrix[1].value = 11
        fc.pfc_matrix[4].enable = True
        fc.pfc_matrix[4].value = 144
        Test_FlowControl_Suite.enable_pfc()

        matrix = p1._get_field('pfcEnableValueListBitMatrix')
        expected = '{0 0} {1 11} {0 0} {0 0} {1 144} {0 0} {0 0} {0 0}'
        Test_FlowControl_Suite.equal_check(matrix, expected)

        fc.pfc_matrix[1].enable = False
        fc.pfc_matrix[1].value = 0
        fc.pfc_matrix[4].value = 3
        fc.pfc_matrix[7].enable = True
        fc.pfc_matrix[7].value = 221
        p1.apply()

        matrix = p1._get_field('pfcEnableValueListBitMatrix')
        expected = '{0 0} {0 0} {0 0} {0 0} {1 3} {0 0} {0 0} {1 221}'
        Test_FlowControl_Suite.equal_check(matrix, expected)

class Test_L1_Suite(object):
    # @classmethod
    # def setUpClass(cls):
    #     pass
    # @classmethod
    # def tearDownClass(cls):
    #     pass
    #@pytest.mark.skipif(True is True)
    @pytest.mark.skipif(simple_debug is True or L1_Suite is False, reason="debug other test")
    def test_Split_Card(self):
        for p1 in tgPorts:
            mode_vs_speed = {TGEnums.splitSpeed.One_100G: TGEnums.PORT_PROPERTIES_SPEED.GIGA_100,
                             TGEnums.splitSpeed.Two_50G: TGEnums.PORT_PROPERTIES_SPEED.GIGA_50,
                             TGEnums.splitSpeed.Four_25G: TGEnums.PORT_PROPERTIES_SPEED.GIGA_25,
                             TGEnums.splitSpeed.Four_10G: TGEnums.PORT_PROPERTIES_SPEED.GIGA_10,
                             TGEnums.splitSpeed.One_40G: TGEnums.PORT_PROPERTIES_SPEED.GIGA_40,
                             TGEnums.splitSpeed.One_400G: TGEnums.PORT_PROPERTIES_SPEED.GIGA_400,
                             TGEnums.splitSpeed.One_200G: TGEnums.PORT_PROPERTIES_SPEED.GIGA_200,
                             TGEnums.splitSpeed.Two_100G: TGEnums.PORT_PROPERTIES_SPEED.GIGA_100,
                             TGEnums.splitSpeed.Four_50G: TGEnums.PORT_PROPERTIES_SPEED.GIGA_50}

            if p1.card.splitable:
                modes = p1.supported_split_modes
                #[TGEnums.splitSpeed.One_100G,TGEnums.splitSpeed.One_40G]
                for mode in modes:
                    if mode == p1.split_mode:
                        continue
                    newTgPorts = p1.apply_split_mode(mode) #type: list[Port]
                    p1 = newTgPorts[0]
                    assert mode == p1.split_mode
                    assert p1.properties.speed == mode_vs_speed[mode]

    @pytest.mark.skipif(simple_debug is True or L1_Suite is False, reason="debug other test")
    def test_Autoneg(self):
        ixAnList = [{"advertise10HalfDuplex": TGEnums.DUPLEX_AND_SPEED.HALF10},
                    {"advertise10FullDuplex": TGEnums.DUPLEX_AND_SPEED.FULL10},
                    {"advertise100HalfDuplex": TGEnums.DUPLEX_AND_SPEED.HALF100},
                    {"advertise100FullDuplex": TGEnums.DUPLEX_AND_SPEED.FULL100},
                    {"advertise1000FullDuplex": TGEnums.DUPLEX_AND_SPEED.FULL1000},
                    {"advertise2P5FullDuplex": TGEnums.DUPLEX_AND_SPEED.FULL2500},
                    {"advertise5FullDuplex": TGEnums.DUPLEX_AND_SPEED.FULL5000}]
        for p in tgPorts:
            def run():
                autoNegs = p.properties.supported_autoneg_speeds
                p.chassis_refresh()
                autoNegs = p.properties.supported_autoneg_speeds
                p.properties.auto_neg_enable = True
                for an in autoNegs:
                    p.properties.auto_neg_adver_list = [an]
                    p.apply_auto_neg()

                    ixRes = list(filter(lambda ixAn: (list(ixAn.items())[0][1] == an), ixAnList))
                    if ixRes:
                        ixCommand = list(ixRes[0].items())[0][0]
                        enabled = bool(int(p._get_field(ixCommand)))
                        assert enabled is True
            run()
            if p.properties.dual_phy:
                if p.properties.media_type == TGEnums.PORT_PROPERTIES_MEDIA_TYPE.COPPER:
                    p.properties.media_type = TGEnums.PORT_PROPERTIES_MEDIA_TYPE.FIBER
                    p.apply_port_config()
                    run()
                else:
                    p.properties.media_type = TGEnums.PORT_PROPERTIES_MEDIA_TYPE.COPPER
                    p.apply_port_config()
                    run()

    @pytest.mark.skipif(simple_debug is True or L1_Suite is False, reason="debug other test")
    def test_Speed(self):
        def run():

            speeds = p.properties.supported_forced_speeds
            countHD = filter(lambda spd: spd > TGEnums.PORT_PROPERTIES_SPEED.GIGA_10, speeds)
            if countHD or len(speeds) < 2:
                return
            succeed = []
            for speed in speeds:
                p.properties.auto_neg_enable = False
                p.properties.auto_neg_speed = speed
                p.apply_auto_neg()
                p.chassis_refresh()
                if p.properties.speed == speed:
                    succeed.append(speed)

            expected = p.properties.available_forced_speeds
            if succeed != expected:
                print ("Fail")
            assert succeed == expected

        for p in tgPorts:
            run()
            if p.properties.dual_phy:
                if p.properties.media_type == TGEnums.PORT_PROPERTIES_MEDIA_TYPE.COPPER:
                    p.properties.media_type = TGEnums.PORT_PROPERTIES_MEDIA_TYPE.FIBER
                    p.apply_port_config()
                    run()
                else:
                    p.properties.media_type = TGEnums.PORT_PROPERTIES_MEDIA_TYPE.COPPER
                    p.apply_port_config()
                    run()

    @pytest.mark.skipif(simple_debug is True or L1_Suite is False, reason="debug other test")
    def test_Fec_and_IEEE(self):
        if txPort.properties.speed is TGEnums.PORT_PROPERTIES_SPEED.GIGA_400:
            assert False
        for p in tgPorts:
            if p.card.splitable:
                original_mode = p.split_mode
                newPort = p.apply_split_mode(TGEnums.splitSpeed.One_100G)[0] if original_mode is not TGEnums.splitSpeed.One_100G else p
                newPort.reset_factory_defaults()
                txPort.properties.loopback_mode = TGEnums.PORT_PROPERTIES_LOOPBACK_MODE.NORMAL
                newPort.properties.fec_mode = TGEnums.PORT_PROPERTIES_FEC_MODES.RS_FEC
                newPort.apply()
                fec_mode = newPort._get_field('enableRsFec')
                assert fec_mode == True
                newPort.properties.fec_mode = TGEnums.PORT_PROPERTIES_FEC_MODES.DISABLED
                newPort.apply()
                fec_mode = newPort._get_field('enableRsFec')
                assert fec_mode == False
                newPort.properties.use_ieee_defaults = True
                newPort.apply()
                p.chassis_refresh()
                fec_mode = newPort._get_field('enableRsFec')
                assert fec_mode == False
                # newPort = p.apply_split_mode(TGEnums.splitSpeed.Four_25G)[0]
                # newPort.properties.fec_mode = TGEnums.PORT_PROPERTIES_FEC_MODES.FC_FEC
                # newPort.properties.use_ieee_defaults = True
                # newPort.apply()
                # p.chassis_refresh()
                # # port config -firecodeForceOn 0
                # # port config -firecodeForceOff 0
                # # port config -reedSolomonForceOff 0
                # fecStates = {'firecodeForceOn': 0, 'firecodeForceOff': 0,'reedSolomonForceOn': 0,'reedSolomonForceOff': 0}
                # for fec_state in fecStates:
                #     test = newPort._get_field('firecodeForceOn')
                #     fec_mode = newPort._get_field(fec_state)
                #     assert fec_mode ==  fecStates[fec_state]
                # newPort.properties.use_ieee_defaults = False
                # newPort.apply()
                # p.chassis_refresh()
                # fecStates['firecodeForceOn'] = 1
                # for fec_state in fecStates:
                #     fec_mode = newPort._get_field(fec_state)
                #     assert fec_mode ==  fecStates[fec_state]
                # newPort.apply_split_mode(original_mode)

    @pytest.mark.skipif(simple_debug is True or L1_Suite is False, reason="debug other test")
    def test_autoneg_and_IEEE(self):
        for p in tgPorts:
            if p.card.splitable and p.properties.speed > TGEnums.PORT_PROPERTIES_SPEED.GIGA_10:
                p.reset_factory_defaults()
                txPort.properties.loopback_mode = TGEnums.PORT_PROPERTIES_LOOPBACK_MODE.NORMAL
                p.properties.auto_neg_enable = True
                p.apply()
                neg_mode = p._get_field_hw_value(p.properties._auto_neg_enable)
                assert neg_mode
                p.properties.auto_neg_enable = False
                p.apply()
                neg_mode = p._get_field_hw_value(p.properties._auto_neg_enable)
                assert not neg_mode
                p.properties.use_ieee_defaults = True
                p.apply()
                p.chassis_refresh()
                neg_mode = p._get_field_hw_value(p.properties._auto_neg_enable)
                assert not neg_mode
                p.properties.use_ieee_defaults = False
                p.properties.auto_neg_enable = False
                p.apply()
                p.chassis_refresh()
                neg_mode = p._get_field_hw_value(p.properties._auto_neg_enable)
                assert not neg_mode


    @pytest.mark.skipif(simple_debug is True or L1_Suite is False, reason="debug other test")
    def test_IEEE(self):
        for p in tgPorts:
            if p.card.splitable and p.properties.speed > TGEnums.PORT_PROPERTIES_SPEED.GIGA_10:
                p.reset_factory_defaults()
                ieee_state = p._get_field_hw_value(p.properties._use_ieee)
                assert not ieee_state
                p.properties.use_ieee_defaults = True
                p.apply()
                ieee_state = p._get_field_hw_value(p.properties._use_ieee)
                assert ieee_state

    # def test_Fec_AN(self):
    #     pass
    #     #enable IEEE
    #     #run list
    #     txPort.properties.use_ieee_defaults = False
    #     txPort.properties.fec_an_list = []
    #     txPort.apply()
    #     txPort.properties.use_ieee_defaults = True
    #     txPort.properties.fec_an_list = [TGEnums.PORT_PROPERTIES_FEC_AN.ADVERTISE_FC,
    #                                      # TGEnums.PORT_PROPERTIES_FEC_AN.REQUEST_FC,
    #                                      # TGEnums.PORT_PROPERTIES_FEC_AN.ADVERTISE_RS,
    #                                      TGEnums.PORT_PROPERTIES_FEC_AN.REQUEST_RS
    #                                      ]
    #     txPort.apply()



    @pytest.mark.skipif(simple_debug is True or L1_Suite is False, reason="debug other test")
    def Test_Discover(self):
        chasList = [mGigChassis,chasIx2]
        tg.discover(chasList)
        for chasIp in chasList:
            assert len(tg.chassis[chasIp].cards)>0

class Test_Protocol_Management(object):
    @pytest.mark.skipif(simple_debug is True or Protocol_Management_Suite is False, reason="debug other test")
    def test_Arp_params(self):
        pass

    @pytest.mark.skipif(simple_debug is True or Protocol_Management_Suite is False, reason="debug other test")
    def test_Arp_v4_if(self):
        init__setup_ports()
        txPort.enable_protocol_managment = True
        txPort.protocol_managment.enable_ARP = True
        p1_if_1 = txPort.protocol_managment.protocol_interfaces.add_interface()
        txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].enable = True
        txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].description = 'TX11'
        txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].mac_addr = '00:00:00:00:11:11'
        txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.address = '1.1.1.1'
        txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.gateway = '1.1.1.2'
        txPort.apply()
        rxPort.enable_protocol_managment = True
        rxPort.protocol_managment.enable_ARP = True
        p2_if_1 = rxPort.protocol_managment.protocol_interfaces.add_interface()
        rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].enable = True
        rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].description = 'RX22'
        rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].mac_addr = '00:00:00:00:11:22'
        rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].ipv4.address = '1.1.1.2'
        rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].ipv4.gateway = '1.1.1.1'
        rxPort.apply()
        txPort.protocol_managment.arp_table.clear()
        txPort.protocol_managment.arp_table.transmit()
        txPort.protocol_managment.arp_table.refresh()
        assert len(txPort.protocol_managment.arp_table.learned_table) == 1
        assert txPort.protocol_managment.arp_table.learned_table[0].ip == '1.1.1.2'
        assert txPort.protocol_managment.arp_table.learned_table[0].mac == '00 00 00 00 11 22'
        rxPort.protocol_managment.arp_table.refresh()
        assert len(rxPort.protocol_managment.arp_table.learned_table) == 1
        assert rxPort.protocol_managment.arp_table.learned_table[0].ip == '1.1.1.1'
        assert rxPort.protocol_managment.arp_table.learned_table[0].mac == '00 00 00 00 11 11'


    @pytest.mark.skipif(simple_debug is True or Protocol_Management_Suite is False, reason="debug other test")
    def test_Arp_v4_from_source_if(self):
        init__setup_ports()
        burst = 5
        txPort.enable_protocol_managment = True
        txPort.protocol_managment.enable_ARP = True
        p1_if_1 = txPort.protocol_managment.protocol_interfaces.add_interface()
        txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].enable = True
        txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].description = 'TX11'
        txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].mac_addr = '00:00:00:00:11:11'
        txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.address = '1.1.1.1'
        txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.gateway = '1.1.1.2'
        stream1 = txPort.add_stream()
        txPort.streams[stream1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
        txPort.streams[stream1].control.packets_per_burst = burst
        txPort.streams[stream1].rate.mode = TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND
        txPort.streams[stream1].rate.pps_value = 10
        txPort.streams[stream1].packet.l3_proto = TGEnums.L3_PROTO.IPV4
        txPort.streams[stream1].source_interface.enabled = True
        txPort.streams[stream1].source_interface.description_key = p1_if_1
        txPort.apply()

        sIp = '01:01:01:01'
        saMac = '00:00:00:00:11:11'
        term1 = rxPort.filter_properties.create_match_term(saMac, 6)
        term2 = rxPort.filter_properties.create_match_term(sIp, 26)
        myFilter_1 = rxPort.filter_properties.filters[1]
        myFilter_1.enabled = True
        myFilter_1.add_condition(term1)
        myFilter_1.add_condition(term2)
        rxPort.apply()
        rxPort.wait_link_up()
        txPort.start_traffic()
        time.sleep(rxSleep)
        stats = rxPort.statistics
        rxPort.get_stats()
        expectedCount = burst
        assert int(stats.user_defined_stat_1) == expectedCount


    @pytest.mark.skipif(simple_debug is True or Protocol_Management_Suite is False, reason="debug other test")
    def test_Arp_v6_if(self):
        init__setup_ports()
        txPort.enable_protocol_managment = True
        p1_if_1 = txPort.protocol_managment.protocol_interfaces.add_interface()
        txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].enable = True
        txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].description = 'TX'
        txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv6.address = '3000::1'
        txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv6.mask = 96
        txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv6.gateway = '3000::2'
        txPort.apply()
        rxPort.enable_protocol_managment = True
        p2_if_1 = rxPort.protocol_managment.protocol_interfaces.add_interface()
        rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].enable = True
        rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].description = 'RX'
        rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].ipv6.address = '3000::2'
        rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].ipv6.mask = 96
        rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].ipv6.gateway = '3000::1'
        rxPort.apply()

        txPort.protocol_managment.protocol_interfaces.clear_neigbors_table()
        assert len(txPort.protocol_managment.protocol_interfaces.discovered_neighbors) == 0

        txPort.protocol_managment.protocol_interfaces.send_neighbor_solicitation()
        txPort.protocol_managment.protocol_interfaces.read_neigbors_table()
        txPort.protocol_managment.protocol_interfaces.discovered_neighbors[p1_if_1][0].ip == '3000:0:0:0:0:0:0:2'
        txPort.protocol_managment.protocol_interfaces.discovered_neighbors[p1_if_1][0].mac = '00 00 00 00 00 01'
        assert len(txPort.protocol_managment.protocol_interfaces.discovered_neighbors)  == 1


    @pytest.mark.skipif(simple_debug is True or Protocol_Management_Suite is False, reason="debug other test")
    def test_Arp_vlan_if(self):
        init__setup_ports()
        burst = 5
        txPort.enable_protocol_managment = True
        txPort.protocol_managment.enable_ARP = True
        p1_if_1 = txPort.protocol_managment.protocol_interfaces.add_interface()
        txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].enable = True
        txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].description = '1X'
        txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].mac_addr = '00:00:00:00:11:11'
        txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.address = '1.1.1.1'
        txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv4.gateway = '1.1.1.2'
        txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].vlans.enable = True
        txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].vlans.vid = '22,33'
        txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].vlans.priority = '2,3'
        txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].vlans.tpid = '0x8100,0x9100'

        stream1 = txPort.add_stream()
        txPort.streams[stream1].control.mode = TGEnums.STREAM_TRANSMIT_MODE.STOP_AFTER_THIS_STREAM
        txPort.streams[stream1].control.packets_per_burst = burst
        txPort.streams[stream1].rate.mode = TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND
        txPort.streams[stream1].rate.pps_value = 10
        txPort.streams[stream1].packet.l3_proto = TGEnums.L3_PROTO.IPV4
        txPort.streams[stream1].source_interface.enabled = True
        txPort.streams[stream1].source_interface.description_key = p1_if_1
        txPort.apply()

        vlan1 = '40 16'
        vlan2 = '60 21'
        term1 = rxPort.filter_properties.create_match_term(vlan1, 14)
        term2 = rxPort.filter_properties.create_match_term(vlan2, 18)
        myFilter_1 = rxPort.filter_properties.filters[1]
        myFilter_1.enabled = True
        myFilter_1.add_condition(term1)
        myFilter_1.add_condition(term2)
        rxPort.apply()
        rxPort.wait_link_up()
        txPort.start_traffic()
        time.sleep(rxSleep)
        stats = rxPort.statistics
        rxPort.get_stats()
        expectedCount = burst
        assert int(stats.user_defined_stat_1) == expectedCount



    @pytest.mark.skipif(simple_debug is True or Protocol_Management_Suite is False, reason="debug other test")
    def test_router_solocitation(self):
        init__setup_ports()
        txPort.enable_protocol_managment = True
        p1_if_1 = txPort.protocol_managment.protocol_interfaces.add_interface()
        txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].enable = True
        txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].description = 'TX'
        txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv6.address = '3000::1'
        txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv6.mask = 96
        txPort.protocol_managment.protocol_interfaces.interfaces[p1_if_1].ipv6.gateway = '3000::2'
        txPort.apply()

        solicitation = '85'
        term1 = rxPort.filter_properties.create_match_term(solicitation, 54)
        myFilter_1 = rxPort.filter_properties.filters[1]
        myFilter_1.enabled = True
        myFilter_1.add_condition(term1)
        rxPort.apply()
        rxPort.wait_link_up()
        time.sleep(7)
        rxPort.clear_all_statistics()
        txPort.protocol_managment.protocol_interfaces.send_router_solicitation()
        stats = rxPort.statistics
        time.sleep(rxSleep)
        rxPort.get_stats()
        expectedCount = 1
        assert int(stats.user_defined_stat_1) == expectedCount

    @pytest.mark.skipif(simple_debug is True or Protocol_Management_Suite is False, reason="debug other test")
    def test_ping(self):
        init__setup_ports()
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
        txPort.get_stats()
        assert int(txPort.statistics.tx_ping_request) == 1
        assert int(txPort.statistics.tx_ping_reply) == 0
        assert int(txPort.statistics.rx_ping_request) == 0
        assert int(txPort.statistics.rx_ping_reply) == 1

        rxPort.protocol_managment.protocol_interfaces.interfaces[p2_if_1].send_ping('1.1.1.1')
        txPort.get_stats()
        assert int(txPort.statistics.tx_ping_request) == 1
        assert int(txPort.statistics.tx_ping_reply) == 1
        assert int(txPort.statistics.rx_ping_request) == 1
        assert int(txPort.statistics.rx_ping_reply) == 1

