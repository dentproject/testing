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

import array
import binascii
import copy
import struct
import sys
from collections import OrderedDict
from copy import deepcopy

from pypacker.checksum import crc32_cksum

from UnifiedTG.Unified.TGEnums import TGEnums
from UnifiedTG.Unified.UtgObject import UtgObject
from UnifiedTG.Unified.Utils import attrWithDefault, Converter
from UnifiedTG.Unified.Ipv6_extentions import IPv6_Extension_Headers


class BaseField(object):
    def __init__(self, default_val=None, default_mode=None, default_count=None, default_step=None):
        self._value = attrWithDefault(str(default_val))#str(default_val)
        self._mode = attrWithDefault(default_mode)#default_mode
        self._count = attrWithDefault(str(default_count))#str(default_count)
        self._step = attrWithDefault(str(default_step))#str(default_step)
        self._driver_obj = None

    @property
    def value(self):
        """value : """
        return self._value.current_val

    @value.setter
    def value(self, v):
        """value docstring"""
        self._value.current_val = str(v)

    @property
    def mode(self):
        """mode : """
        return self._mode.current_val

    @mode.setter
    def mode(self, v):
        """mode docstring
        :param v:
        :type v: TGEnums.MODIFIER_MAC_MODE
        """
        self._mode.current_val = v

    @property
    def count(self):
        """count : """
        return self._count.current_val

    @count.setter
    def count(self, v):
        """count docstring"""
        self._count.current_val = str(v)

    @property
    def step(self):
        """step : """
        return self._step.current_val

    @step.setter
    def step(self, v):
        """step docstring"""
        self._step.current_val = str(v)

class AddressModifierField(BaseField):
    def __init__(self, default_val=None, default_mode=None, default_count=None, default_step=None, default_mask=None):
        super(self.__class__, self).__init__(default_val=default_val, default_mode=default_mode,
                                             default_count=default_count, default_step=default_step)
        self._mask = attrWithDefault(str(default_mask))#str(default_val)

    @property
    def mask(self):
        """mask : """
        return self._mask.current_val

    @mask.setter
    def mask(self, v):
        """mask docstring"""
        self._mask.current_val = str(v)

class BaseOptionalField(BaseField):
    def __init__(self, default_enabled=False):
        super(self.__class__, self).__init__()
        self._enabled = default_enabled

    @property
    def enabled(self):
        """enabled : """
        return self._enabled

    @enabled.setter
    def enabled(self, v):
        """enabled docstring"""
        self._enabled = v



class SpecialTag(object):

    def __init__(self):
        self.type = TGEnums.SpecialTagType.Undefined
        self.eTag = E_Tag()
        self.DSA_Forward = DSA_Forward()
        self.DSA_To_CPU = DSA_To_CPU()
        self.DSA_From_CPU_use_vidx_1 = DSA_From_CPU_use_vidx_1()
        self.DSA_From_CPU_use_vidx_0 = DSA_From_CPU_use_vidx_0()
        self.DSA_To_ANALYZER = DSA_To_ANALYZER()

        self.extDSA_Forward_use_vidx_0 = extDSA_Forward_use_vidx_0()
        self.extDSA_Forward_use_vidx_1 = extDSA_Forward_use_vidx_1()

        self.extDSA_To_CPU = extDSA_To_CPU()
        self.extDSA_From_CPU_use_vidx_0 = extDSA_From_CPU_use_vidx_0()
        self.extDSA_From_CPU_use_vidx_1_exclude_is_trunk_1 = extDSA_From_CPU_use_vidx_1_exclude_is_trunk_1()
        self.extDSA_From_CPU_use_vidx_1_exclude_is_trunk_0 = extDSA_From_CPU_use_vidx_1_exclude_is_trunk_0()
        self.extDSA_To_ANALYZER = extDSA_To_ANALYZER()

        self.EDSA_Forward_use_vidx_0 = EDSA_Forward_use_vidx_0()
        self.EDSA_Forward_use_vidx_1 = EDSA_Forward_use_vidx_1()

        self.EDSA_To_CPU = EDSA_To_CPU()
        self.EDSA_From_CPU_use_vidx_0 = EDSA_From_CPU_use_vidx_0()
        self.EDSA_From_CPU_use_vidx_1_exclude_is_trunk_0 = EDSA_From_CPU_use_vidx_1_exclude_is_trunk_0()
        self.EDSA_From_CPU_use_vidx_1_exclude_is_trunk_1 = EDSA_From_CPU_use_vidx_1_exclude_is_trunk_1()
        self.EDSA_To_ANALYZER_use_eVIDX_0 = EDSA_To_ANALYZER_use_eVIDX_0()
        self.EDSA_To_ANALYZER_use_eVIDX_1 = EDSA_To_ANALYZER_use_eVIDX_1()

        self.tags_dict = \
            {TGEnums.SpecialTagType.eTag:self.eTag,
             TGEnums.SpecialTagType.DSA_Forward:self.DSA_Forward,
             TGEnums.SpecialTagType.DSA_To_CPU:self.DSA_To_CPU,
             TGEnums.SpecialTagType.DSA_From_CPU_use_vidx_0:self.DSA_From_CPU_use_vidx_0,
             TGEnums.SpecialTagType.DSA_From_CPU_use_vidx_1:self.DSA_From_CPU_use_vidx_1,
             TGEnums.SpecialTagType.DSA_To_ANALYZER:self.DSA_To_ANALYZER,
             TGEnums.SpecialTagType.extDSA_Forward_use_vidx_0:self.extDSA_Forward_use_vidx_0,
             TGEnums.SpecialTagType.extDSA_Forward_use_vidx_1: self.extDSA_Forward_use_vidx_1,
             TGEnums.SpecialTagType.extDSA_To_CPU:self.extDSA_To_CPU,
             TGEnums.SpecialTagType.extDSA_From_CPU_use_vidx_0:self.extDSA_From_CPU_use_vidx_0,
             TGEnums.SpecialTagType.extDSA_From_CPU_use_vidx_1_exclude_is_trunk_0:self.extDSA_From_CPU_use_vidx_1_exclude_is_trunk_0,
             TGEnums.SpecialTagType.extDSA_From_CPU_use_vidx_1_exclude_is_trunk_1:self.extDSA_From_CPU_use_vidx_1_exclude_is_trunk_1,
             TGEnums.SpecialTagType.extDSA_To_ANALYZER:self.extDSA_To_ANALYZER,
             TGEnums.SpecialTagType.EDSA_Forward_use_vidx_0:self.EDSA_Forward_use_vidx_0,
             TGEnums.SpecialTagType.EDSA_Forward_use_vidx_1: self.EDSA_Forward_use_vidx_1,
             TGEnums.SpecialTagType.EDSA_To_CPU:self.EDSA_To_CPU,
             TGEnums.SpecialTagType.EDSA_From_CPU_use_vidx_0:self.EDSA_From_CPU_use_vidx_0,
             TGEnums.SpecialTagType.EDSA_From_CPU_use_vidx_1_exclude_is_trunk_0:self.EDSA_From_CPU_use_vidx_1_exclude_is_trunk_0,
             TGEnums.SpecialTagType.EDSA_From_CPU_use_vidx_1_exclude_is_trunk_1:self.EDSA_From_CPU_use_vidx_1_exclude_is_trunk_1,
             TGEnums.SpecialTagType.EDSA_To_ANALYZER_use_eVIDX_0:self.EDSA_To_ANALYZER_use_eVIDX_0,
             TGEnums.SpecialTagType.EDSA_To_ANALYZER_use_eVIDX_1:self.EDSA_To_ANALYZER_use_eVIDX_1
            }


class framePreemption(object):
    def __init__(self):
        self._packet_type = attrWithDefault(TGEnums.FP_PACKET_TYPE.Express)
        self._frag_count = attrWithDefault(TGEnums.FP_FRAG_COUNT.FragCountAuto)
        self._crc_type = attrWithDefault(TGEnums.FP_CRC_TYPE.CRCmCRC)
        self._enabled = None
        self._end_fragment = True

    @property
    def enabled(self):
        return self._enabled #.current_val

    @enabled.setter
    def enabled(self, v):
        self._enabled = v

    @property
    def packetType(self):
        return self._packet_type.current_val

    @packetType.setter
    def packetType(self, v):
        self._packet_type.current_val = v

    @property
    def fragCount(self):
        return self._frag_count.current_val

    @fragCount.setter
    def fragCount(self, v):
        self._frag_count.current_val = v

    @property
    def endFragmet(self):
        return self._end_fragment

    @endFragmet.setter
    def endFragmet(self, v):
        self._end_fragment = v

    # @property
    # def crcType(self):
    #     return self._crc_type.current_val
    #
    # @crcType.setter
    # def crcType(self, v):
    #     self._crc_type.current_val = v


class Packet(UtgObject):

    def __init__(self,size=64):
        # self._field_to_hw_field_dict = {}
        # self._field_to_hw_field_dict = self._init_fields_dict(self._field_to_hw_field_dict)
        # self._parent = parent_stream
        self.mac = MAC()
        self._l2_proto = attrWithDefault(TGEnums.L2_PROTO.ETHERNETII)
        self.mac._l2_proto = self._l2_proto.current_val
        self._l3_proto = attrWithDefault(TGEnums.L3_PROTO.NONE)
        self._l4_proto = attrWithDefault(TGEnums.L4_PROTO.NONE)
        self._current_vlan_idx = 0
        self._vlans_count = 0
        self._udfs_count = 0
        self.vlans = OrderedDict() # type: list[VLAN]
        self.mpls_labels = OrderedDict()  # type: list[MPLS_Label]
        self.modifiers = OrderedDict() # type: list[MODIFIER]
        self._ethertype = attrWithDefault("0x0800")
        self.mac._ethertype = self._ethertype
        self.arp = ARP()
        self.pause_control = PauseControl()
        self.ipv4 = IPV4()
        self.ipv6 = IPV6()
        self.tcp = TCP()
        self.udp = UDP()
        self.icmp = ICMP()
        self.gre = GRE()
        self.specialTag = SpecialTag()
        self.data_pattern = DATA_PATTERN()
        self.protocol_offset = PROTOCOL_OFFSET()
        self._preamble_size = attrWithDefault("8")
        self.data_integrity = DATA_INTEGRITY()
        self.ptp = PTP()
        self.protocol_pad = Protocol_Pad()
        self.size = size
        self.macSec = MacSec()
        self.preemption = framePreemption()


    def __str__(self):
        str_delimit = ", "
        temp_str =  "L2: "
        temp_str += "MAC: " + str(self.mac)
        for vlan in self.vlans:
            temp_str += "VLAN: " + str(vlan)
        temp_str += "EtherType: " + "[" + str(self.ethertype) + "]\n"
        temp_str += str(self.protocol_offset) + "\n"
        if self.l3_proto == TGEnums.L3_PROTO.IPV4:
            temp_str += "IPV4_HEADER: " + str(self.ipv4)
        elif self.l3_proto == TGEnums.L3_PROTO.IPV6:
            temp_str += "IPV6_HEADER: " + str(self.ipv6)
        elif self.l3_proto == TGEnums.L3_PROTO.ARP:
            temp_str += "ARP_HEADER: " + str(self.arp)
        if self.l3_proto == TGEnums.L3_PROTO.IPV4_O_IPV6:
            temp_str += "IPV4_HEADER: " + str(self.ipv4) + "\n"
            temp_str += "IPV6_HEADER: " + str(self.ipv6) + "\n"
        if self.l3_proto == TGEnums.L3_PROTO.IPV6_O_IPV4:
            temp_str += "IPV6_HEADER: " + str(self.ipv6) + "\n"
            temp_str += "IPV4_HEADER: " + str(self.ipv4) + "\n"
        if self.l4_proto == TGEnums.L4_PROTO.TCP:
            temp_str += "TCP_HEADER: " + str(self.tcp) + "\n"
        elif self.l4_proto == TGEnums.L4_PROTO.UDP:
            temp_str += "UDP_HEADER: " + str(self.udp) + "\n"
        temp_str += str(self.data_pattern) + "\n"
        return temp_str

    def _active_headers_sequence(self):
        seq = [self.mac]
        if len(self.vlans) > 0:
            seq.append(self.vlans)
        if len(self.mpls_labels) > 0:
            seq.append(self.mpls_labels)
        if self.specialTag.type is not TGEnums.SpecialTagType.Undefined:
            seq.append(self.specialTag.tags_dict[self.specialTag.type])
        if self.l2_proto is TGEnums.L2_PROTO.NONE:
            pass
        elif self.l2_proto is TGEnums.L2_PROTO.ETHERNETII:
            seq.append(self.ethertype)
        elif self.l2_proto is TGEnums.L2_PROTO.SNAP:
            seq.append(llc_snap())
        elif self.l2_proto is TGEnums.L2_PROTO.RAW:
            pass
        elif self.l2_proto is TGEnums.L2_PROTO.PROTOCOL_OFFSET:
            seq.append(self.protocol_offset)

        if self.l3_proto is TGEnums.L3_PROTO.NONE:
            pass
        elif self.l3_proto is TGEnums.L3_PROTO.IPV4:
            seq.append(self.ipv4)
        elif self.l3_proto is TGEnums.L3_PROTO.IPV6:
            seq.append(self.ipv6)
        elif self.l3_proto is TGEnums.L3_PROTO.IPV4_O_IPV6:
            seq.append(self.ipv6)
            seq.append(self.ipv4)
        elif self.l3_proto is TGEnums.L3_PROTO.IPV6_O_IPV4:
            seq.append(self.ipv4)
            seq.append(self.ipv6)

        if self.l4_proto is TGEnums.L4_PROTO.NONE:
            pass
        elif self.l4_proto is TGEnums.L4_PROTO.TCP:
            seq.append(self.tcp)
        elif self.l4_proto is TGEnums.L4_PROTO.UDP:
            seq.append(self.udp)
        elif self.l4_proto is TGEnums.L4_PROTO.GRE:
            if self.l3_proto is TGEnums.L3_PROTO.IPV4:
                self.ipv4.protocol = '47'
            elif self.l3_proto is TGEnums.L3_PROTO.IPV6:
                self.ipv6.next_header = '47'
            seq.append(self.gre)
            if self.gre.l3_proto is TGEnums.L3_PROTO.IPV4:
                seq.append(self.gre.ipv4)
            elif self.gre.l3_proto is TGEnums.L3_PROTO.IPV6:
                seq.append(self.gre.ipv6)
            if self.gre.l4_proto is TGEnums.L4_PROTO.UDP:
                seq.append(self.gre.udp)
            elif self.gre.l4_proto is TGEnums.L4_PROTO.TCP:
                seq.append(self.gre.tcp)
        seq.append(self.data_pattern)
        return seq

    def to_string(self, crc=True):
        crc_size = 4
        seq = self._active_headers_sequence()
        pkt = None
        prev_header = None
        for h in seq:
            if isinstance(h, header_object):
                if h.__class__ == DATA_PATTERN:
                    h.size = self.size - len(pkt)-crc_size
                prev_header = h.to_packer()
                pkt = pkt + prev_header if pkt else prev_header
            elif isinstance(h, OrderedDict):
                for v_key in h:
                    obj_utg = h[v_key]
                    if isinstance(obj_utg, VLAN):
                        v_obj = obj_utg.to_packer()
                        prev_header.vlan.append(v_obj)
                    elif isinstance(obj_utg, MPLS_Label):
                        obj = obj_utg.to_packer()
                        pkt += obj
            pkt_str = binascii.hexlify(prev_header.bin()).decode('utf-8')
            print("")
        pkt_str = binascii.hexlify(pkt.bin()).decode('utf-8')
        if crc:
            fcs = (binascii.crc32(pkt.bin())& 0xFFFFFFFF)
            fcs = struct.unpack("<I", struct.pack("!I", fcs))[0]
            fcs = '{:08x}'.format(fcs)
        else:
            fcs = ''
        return (pkt_str+fcs)

    # def set_from_json(self, path_to_json):
    #     '''
    #     Get a path to json file describing the packet and write it to the Packet object
    #     :param path_to_json: full path to the json file
    #     :type path_to_json: str
    #     :return:
    #     '''
    #     pass
    #
    # def set_from_scapy(self, scapy_packet):
    #     '''
    #     Get a Scapy packet obejct and write it to HW (the packet's structure currently doesn't get write to the Packet object
    #     :param scapy_packet:
    #     :return:
    #     '''



    # def __copy__(self):
    #     cls = self.__class__
    #     result = cls.__new__(cls)
    #     result.__dict__.update(self.__dict__)
    #     return result
    #
    # def __deepcopy__(self, memo):
    #     cls = self.__class__
    #     result = cls.__new__(cls)
    #     memo[id(self)] = result
    #     for k, v in self.__dict__.items():
    #         if k != '_parent':
    #             setattr(result, k, deepcopy(v, memo))
    #         else:
    #             setattr(result, k, deepcopy(None, memo))
    #     return result


    # @property
    # def Packet(self):
    #     return self.copy()

    @property
    def l2_proto(self):
        """l2_proto : """
        return self._l2_proto.current_val

    @l2_proto.setter
    def l2_proto(self, v):
        """l2_proto : """
        if v is TGEnums.L2_PROTO.SNAP:
            self.ethertype = str(self.size - 18)
        self._l2_proto.current_val = v

    @property
    def l3_proto(self):
        """l3_proto : """
        return self._l3_proto.current_val

    @l3_proto.setter
    def l3_proto(self, v):
        """l3_proto :
        :param v:
        :type v: TGEnums.L3_PROTO
        """
        self._l3_proto.current_val = v

    @property
    def l4_proto(self):
        """l4_proto : """
        return self._l4_proto.current_val

    @l4_proto.setter
    def l4_proto(self, v):
        """l4_proto : """
        self._l4_proto.current_val = v

    @property
    def ethertype(self):
        """ethertype : """
        return self._ethertype.current_val

    @ethertype.setter
    def ethertype(self, v):
        """ethertype : """
        self._ethertype.current_val = v

    @property
    def preamble_size(self):
        """preamble_size : """
        return self._preamble_size.current_val

    @preamble_size.setter
    def preamble_size(self, v):
        """preamble_size : """
        self._preamble_size.current_val = v


    def _print_ethertype_status(self):
        temp_str = ""
        temp_str += "current value: " + str(self._ethertype.current_val) + "\n"
        temp_str += "default value: " + str(self._ethertype._default_val) + "\n"
        temp_str += "is default value: " + str(self._ethertype._is_default) + "\n"
        return temp_str

    def del_vlan(self, vlan_name):
        del self.vlans[vlan_name]

    def add_vlan(self,vlan_name=None):
        if vlan_name is None:
            name = str(self._current_vlan_idx)
        else:
            name = vlan_name

        new_vlan = VLAN(vlan_name=name)
        self.vlans[name] = new_vlan
        self._current_vlan_idx += 1
        self._vlans_count += 1
        return name

    def add_mpls_label(self, name=None):
        self.ethertype = "8847"
        new_label = MPLS_Label()
        name = name if name else str(id(new_label))
        self.mpls_labels[name] = new_label
        return name

    def remove_mpls_label(self, name):
        del self.mpls_labels[name]

    def add_modifier(self, modifier_name=None):
        self._udfs_count += 1
        if modifier_name is None:
            modifier_name = str(self._udfs_count)
        self.modifiers[modifier_name] = MODIFIER(udf_name=modifier_name)
        return modifier_name

    def del_udf(self, modifier_name):
        del self.modifiers[modifier_name]

    def copy(self):
        # memo = {}
        # copy_packet = self.__deepcopy__(memo)
        copy_packet = copy.deepcopy(self)
        copy_packet._l2_proto._reset_to_default()
        copy_packet._l3_proto._reset_to_default()
        copy_packet._l4_proto._reset_to_default()
        copy_packet._ethertype._reset_to_default()
        copy_packet.mac._reset_to_default()
        for vlan in copy_packet.vlans:
            copy_packet.vlans[vlan]._reset_to_default()
        copy_packet.arp._reset_to_default()
        copy_packet.ipv4._reset_to_default()
        copy_packet.ipv6._reset_to_default()
        copy_packet.tcp._reset_to_default()
        copy_packet.udp._reset_to_default()
        copy_packet.icmp._reset_to_default()
        copy_packet.data_pattern._reset_to_default()
        copy_packet._preamble_size._reset_to_default()
        copy_packet.protocol_offset._reset_to_default()
        for udf in copy_packet.modifiers:
            copy_packet.modifiers[udf]._reset_to_default()
        return copy_packet

    # def _init_fields_dict(self, dict):
    #     dict["da.value"] = ""
    #     dict["da.mode"] = ""
    #     dict["da.count"] = ""
    #     dict["da.step"] = ""
    #     dict["sa.value"] = ""
    #     dict["sa.mode"] = ""
    #     dict["sa.count"] = ""
    #     dict["sa.step"] = ""
    #     return dict

    # def _hw_sync(self, parent_stream):
    #     self.mac.da.value = parent_stream._rgetattr(parent_stream._stream_driver_obj,
    #                                                self._field_to_hw_field_dict["da.value"])
    #     self.mac.da.mode = TGEnums.MODIFIER_MAC_MODE(int(parent_stream._rgetattr(parent_stream._stream_driver_obj, self._field_to_hw_field_dict["da.mode"])))
    #     self.mac.da.count = parent_stream._rgetattr(parent_stream._stream_driver_obj,
    #                                                self._field_to_hw_field_dict["da.count"])
    #     self.mac.da.step = parent_stream._rgetattr(parent_stream._stream_driver_obj,
    #                                               self._field_to_hw_field_dict["da.step"])
    #
    #     self.mac.sa.value = parent_stream._rgetattr(parent_stream._stream_driver_obj,
    #                                                self._field_to_hw_field_dict["sa.value"])
    #     self.mac.sa.mode = TGEnums.MODIFIER_MAC_MODE(int(parent_stream._rgetattr(parent_stream._stream_driver_obj, self._field_to_hw_field_dict["sa.mode"])))
    #     self.mac.sa.count = parent_stream._rgetattr(parent_stream._stream_driver_obj,
    #                                                self._field_to_hw_field_dict["sa.count"])
    #     self.mac.sa.step = parent_stream._rgetattr(parent_stream._stream_driver_obj,
    #                                               self._field_to_hw_field_dict["sa.step"])


class header_object(object):

    def __init__(self):
        self._parrent = None
        self.size = 0

    def to_packer(self):
        from UnifiedTG.PacketBuilder.UTG_2Packer import utg_2packer #TODO import loop fix
        return utg_2packer.create_packer_obj(self)

    def to_string(self):
        obj = self.to_packer()
        bin_headers = binascii.hexlify(obj.bin()).decode('utf-8') #'0x'
        return bin_headers

class llc_snap(header_object):
    def __init__(self):
        pass


class MPLS_Label(header_object):
    def __init__(self):
        self._label = attrWithDefault(None)
        self._bottom_stack = attrWithDefault(1)
        self._ttl = attrWithDefault(64)
        self._exp = attrWithDefault(0)

    @property
    def label(self):
        return self._label.current_val

    @label.setter
    def label(self, v):
        self._label.current_val = v

    @property
    def ttl(self):
        return self._ttl.current_val

    @ttl.setter
    def ttl(self, v):
        self._ttl.current_val = v

    @property
    def experimental(self):
        return self._exp.current_val

    @experimental.setter
    def experimental(self, v):
        self._exp.current_val = v

class E_Tag(header_object):
    def __init__(self):
        self._epcp = 0
        self._edei = 0
        self._ingress_ecid_base = 0
        self._reserved = 0
        self._grp = 0
        self._ecid_base = 0
        self._ingress_ecid_ext = 0
        self._ecid_ext = 0

    @property
    def E_PCP(self):
        """vid : """
        return self._epcp

    @E_PCP.setter
    def E_PCP(self, v):
        """vid docstring"""
        self._epcp = v

    @property
    def E_DEI(self):
        """vid : """
        return self._edei

    @E_DEI.setter
    def E_DEI(self, v):
        """vid docstring"""
        self._edei = v

    @property
    def Ingress_E_CID_base(self):
        """vid : """
        return self._ingress_ecid_base

    @Ingress_E_CID_base.setter
    def Ingress_E_CID_base(self, v):
        """vid docstring"""
        self._ingress_ecid_base = v

    @property
    def Reserved(self):
        """vid : """
        return self._reserved

    @Reserved.setter
    def Reserved(self, v):
        """vid docstring"""
        self._reserved = v

    @property
    def GRP(self):
        """vid : """
        return self._grp

    @GRP.setter
    def GRP(self, v):
        """vid docstring"""
        self._grp = v

    @property
    def E_CID_base(self):
        """vid : """
        return self._ecid_base

    @E_CID_base.setter
    def E_CID_base(self, v):
        """vid docstring"""
        self._ecid_base = v

    @property
    def Ingress_E_CID_ext(self):
        """vid : """
        return self._ingress_ecid_ext

    @Ingress_E_CID_ext.setter
    def Ingress_E_CID_ext(self, v):
        """vid docstring"""
        self._ingress_ecid_ext = v

    @property
    def E_CID_ext(self):
        """vid : """
        return self._ecid_ext

    @E_CID_ext.setter
    def E_CID_ext(self, v):
        """vid docstring"""
        self._ecid_ext = v

class PTP(header_object):
    def __init__(self):
        self.transport = 0
        self.messageType = 0
        self.versionPTP = 2
        self.messageLength = 0
        self.domainNumber = 0
        self.reserved2 = 0
        self.Flags = 0
        self.correctionField = 0
        self.reserved3 = 0
        self.sourcePortIdentify = 0
        self.sequenceID = 0
        self.controlField = 0
        self.logMessageInterval = 0x7F

class Protocol_Pad(object):
    def __init__(self):
        self._enabled = attrWithDefault(None)
        self.type = attrWithDefault(TGEnums.PROTOCOL_PAD_TYPE.CUSTOM)
        self._custom_data = attrWithDefault('')

    @property
    def enabled(self):
        return self._enabled.current_val

    @enabled.setter
    def enabled(self, v):
        self._enabled.current_val = v

    @property
    def custom_data(self):
        return self._custom_data.current_val

    @custom_data.setter
    def custom_data(self, v):
        self._custom_data.current_val = v


class VLAN(header_object):
    def __init__(self, vlan_name=None):
        self._name = vlan_name
        self._vid = BaseField(default_val="0", default_mode=TGEnums.MODIFIER_VLAN_MODE.FIXED, default_count="1",
                              default_step="1")
        self._cfi = attrWithDefault("0")
        self._priority = attrWithDefault("0")
        self._proto = attrWithDefault("0x8100")
        # self._enabled = attrWithDefault(False)

    def __iter__(self):
        return iter([attr for attr in dir(self) if attr[:2] != "__"])

    def __str__(self):
        str_delimit = ", "
        temp_str = ""
        temp_str += "VLAN: VID" + "[" + str(self.vid.value) + "]" + str_delimit + \
        "PRIORITY" + "[" + str(self.priority.current_val) + "]" + str_delimit + \
        "CFI" + "[" + self.cfi.current_val + "]" + str_delimit + \
        "PROTO" + "[" + self.proto + "]\n"


        return temp_str

    @property
    def vid(self):
        """vid : """
        return self._vid

    @vid.setter
    def vid(self, v):
        """vid docstring"""
        self._vid = v

    @property
    def cfi(self):
        """cfi : """
        return self._cfi.current_val

    @cfi.setter
    def cfi(self, v):
        """cfi docstring"""
        self._cfi.current_val = v

    @property
    def priority(self):
        """priority : """
        return self._priority.current_val

    @priority.setter
    def priority(self, v):
        """priority docstring"""
        self._priority.current_val = v

    @property
    def proto(self):
        """proto : """
        return self._proto.current_val

    @proto.setter
    def proto(self, v):
        """proto docstring"""
        self._proto.current_val = v


    # def append(self,vid):
    #     self._vid = vid

    def _reset_to_default(self):
        self.vid._value._reset_to_default()
        self.vid._mode._reset_to_default()
        self.vid._step._reset_to_default()
        self.vid._count._reset_to_default()
        self._cfi._reset_to_default()
        self._priority._reset_to_default()
        self._proto._reset_to_default()

class MAC(header_object):
    def __init__(self):
        self._da = AddressModifierField(default_val="00:00:00:00:00:02", default_mode=TGEnums.MODIFIER_MAC_MODE.FIXED, default_step=1, default_count=1)
        self._sa = AddressModifierField(default_val="00:00:00:00:00:01", default_mode=TGEnums.MODIFIER_MAC_MODE.FIXED, default_step=1, default_count=1)
        self._fcs = attrWithDefault(TGEnums.FCS_ERRORS_MODE.NO_ERROR)
        self._ethertype = None
        self._l2_proto = None
    def __iter__(self):
        return iter([attr for attr in dir(self) if attr[:2] != "__"])

    def __str__(self):
        str_delimit = ", "
        temp_str = "DA[{1}, mode={4}, step={5}, count={6}]{0}SA[{2}, mode={7}, step={8}, count={9}]\nFCS[{3}]\n".format(
            str_delimit,
            self.da.value,
            self.sa.value,
            self.fcs,
            self.da.mode,
            self.da.step,
            self.da.count,
            self.sa.mode,
            self.sa.step,
            self.sa.count,
        )
        return temp_str

    @property
    def da(self):
        """da : """
        return self._da

    @da.setter
    def da(self, v):
        """da docstring"""
        v = v.replace("-", ":")
        self._da = v

    @property
    def sa(self):
        """sa : """
        return self._sa

    @sa.setter
    def sa(self, v):
        """sa docstring"""
        v = v.replace("-", ":")
        self._sa = v

    @property
    def fcs(self):
        """fcs : """
        return self._fcs.current_val

    @fcs.setter
    def fcs(self, v):
        """fcs docstring"""
        self._fcs.current_val = v

    def _reset_to_default(self):
        self._da._value._reset_to_default()
        self._da._count._reset_to_default()
        self._da._mode._reset_to_default()
        self._da._step._reset_to_default()
        self._sa._value._reset_to_default()
        self._sa._count._reset_to_default()
        self._sa._mode._reset_to_default()
        self._sa._step._reset_to_default()
        self._fcs._reset_to_default()

class ARP(header_object):
    def __init__(self):
        self._operation = attrWithDefault(None)
        self._sender_hw = BaseField('00:00:00:00:00:00', TGEnums.MODIFIER_ARP_MODE.FIXED, 1)
        self._sender_ip = BaseField('0.0.0.0', TGEnums.MODIFIER_ARP_MODE.FIXED, 1)
        self._target_hw = BaseField('00:00:00:00:00:00', TGEnums.MODIFIER_ARP_MODE.FIXED, 1)
        self._target_ip = BaseField('0.0.0.0', TGEnums.MODIFIER_ARP_MODE.FIXED, 1)

    def __iter__(self):
        return iter([attr for attr in dir(self) if attr[:2] != "__"])

    def __str__(self):
        str_delimit = ", "
        temp_str = "OPERATION[{1}]{0}SENDER_HW[{2}, mode={6}, count={7}, step={8}]{0}SENDER_IP[{3}, mode={9}, count={10}, step={11}]{0}TARGET_HW[{4}, mode={12}, count={13}, step={14}]{0}TARGET_IP[{5}, mode={15}, count={16}, step={17}]".format(
            str_delimit,
            self.operation,
            self.sender_hw.value,
            self.sender_ip.value,
            self.target_hw.value,
            self.target_ip.value,
            self.sender_hw.mode,
            self.sender_hw.count,
            self.sender_hw.step,
            self.sender_ip.mode,
            self.sender_ip.count,
            self.sender_ip.step,
            self.target_hw.mode,
            self.target_hw.count,
            self.target_hw.step,
            self.target_ip.mode,
            self.target_ip.count,
            self.target_ip.step,
        )
        return temp_str

    @property
    def operation(self):
        """operation : """
        return self._operation.current_val

    @operation.setter
    def operation(self, v):
        """operation docstring"""
        self._operation.current_val = v

    @property
    def sender_hw(self):
        return self._sender_hw

    @sender_hw.setter
    def sender_hw(self, v):
        # type: ( BaseField)->None
        self._sender_hw = v

    @property
    def sender_ip(self):
        """sender_ip : """
        return self._sender_ip

    @sender_ip.setter
    def sender_ip(self, v):
        """sender_ip docstring"""
        self._sender_ip = v

    @property
    def target_hw(self):
        """target_hw : """
        return self._target_hw

    @target_hw.setter
    def target_hw(self, v):
        """target_hw docstring"""
        self._target_hw = v

    @property
    def target_ip(self):
        """target_ip : """
        return self._target_ip

    @target_ip.setter
    def target_ip(self, v):
        """target_ip docstring"""
        self._target_ip = v

    def _reset_to_default(self):
        self._operation._reset_to_default()
        self.sender_hw._value._reset_to_default()
        self.sender_hw._mode._reset_to_default()
        self.sender_hw._step._reset_to_default()
        self.sender_hw._count._reset_to_default()
        self.sender_ip._value._reset_to_default()
        self.sender_ip._mode._reset_to_default()
        self.sender_ip._step._reset_to_default()
        self.sender_ip._count._reset_to_default()
        self.target_hw._value._reset_to_default()
        self.target_hw._mode._reset_to_default()
        self.target_hw._step._reset_to_default()
        self.target_hw._count._reset_to_default()
        self.target_ip._value._reset_to_default()
        self.target_ip._mode._reset_to_default()
        self.target_ip._step._reset_to_default()
        self.target_ip._count._reset_to_default()

class IPV4(header_object):
    def __init__(self):
        self._enable_header_len_override = attrWithDefault(False)  # done
        self._header_len_override_value = attrWithDefault(0)  # done
        self._qos_type = attrWithDefault(TGEnums.QOS_MODE.DSCP)  # done
        self._tos_precedence = attrWithDefault(0)
        self._tos_delay = attrWithDefault(0)
        self._tos_throughput = attrWithDefault(0)
        self._tos_reliability = attrWithDefault(0)
        self._tos_cost = attrWithDefault(0)
        self._tos_reserved = attrWithDefault(0)
        self._dscp_decimal_value = attrWithDefault("0")  # done
        self._length_override = attrWithDefault(False)  # done
        self._length_value = attrWithDefault(0)  # done
        self._identifier = attrWithDefault("0")  # done
        self._fragment_enable = attrWithDefault(True)  # done
        self._fragment_last_enable = attrWithDefault(True)  # done
        self._fragment_offset_decimal_value = attrWithDefault(0)  # done
        self._ttl = attrWithDefault("64")  # done
        self._protocol = attrWithDefault(255)
        self._checksum_mode = attrWithDefault(TGEnums.CHECKSUM_MODE.VALID)  # done
        self._custom_checksum = attrWithDefault("{}")  # done
        self._options_padding = attrWithDefault("{}")  # done
        self._source_ip = AddressModifierField(default_val="0.0.0.0",
                                               default_mode=TGEnums.MODIFIER_IPV4_ADDRESS_MODE.FIXED, default_count=0,
                                               default_mask="255.0.0.0")  # done
        self._destination_ip = AddressModifierField(default_val="0.0.0.0",
                                                    default_mode=TGEnums.MODIFIER_IPV4_ADDRESS_MODE.FIXED,
                                                    default_count=0, default_mask="255.0.0.0")  # done

    def __iter__(self):
        return iter([attr for attr in dir(self) if attr[:2] != "__"])

    def __str__(self):
        str_delimit = ", "
        temp_str = "IPV4: SIP[{1}, mode={7}, count={8}, mask={9}]{0}DIP[{2}, mode={10}, count={11}, mask={12}]{0}TTL[{3}]{0}PROTOCOL[{4}]{0}IDENTIFIER[{5}]{0}OPTIONS[{6}]".format(
            str_delimit,
            self.source_ip.value,
            self.destination_ip.value,
            self.ttl,
            self.protocol,
            self.identifier,
            self.options_padding,
            self.source_ip.mode,
            self.source_ip.count,
            self.source_ip.mask,
            self.destination_ip.mode,
            self.destination_ip.count,
            self.destination_ip.mask,
        )

        if self._custom_checksum != True:
            temp_str += "{0}CUSTOM CHECKSUM[{1}]".format(str_delimit, self.custom_checksum)
        if self.fragment_enable == True:
            temp_str += "{0}FRAGMENT ENABLED[True]".format(str_delimit)
            temp_str += "{0}FRAGMENT OFFSET[{1}]".format(str_delimit, self.fragment_offset_decimal_value)
        else:
            temp_str += "{0}FRAGMENT ENABLED[False]".format(str_delimit)
        if self.fragment_last_enable == True:
            temp_str += "{0}FRAGMENT LAST[True]".format(str_delimit)
        else:
            temp_str += "{0}FRAGMENT LAST[False]".format(str_delimit)
        if self.length_override == True:
            temp_str += "{0}LENGTH OVERRIDE[{1}]".format(str_delimit, self.length_value)

        return temp_str

    @property
    def enable_header_len_override(self):
        """enable_header_len_override : """
        return self._enable_header_len_override.current_val

    @enable_header_len_override.setter
    def enable_header_len_override(self, v):
        """enable_header_len_override : """
        self._enable_header_len_override.current_val = v

    @property
    def header_len_override_value(self):
        """header_len_override_value : """
        return self._header_len_override_value.current_val

    @header_len_override_value.setter
    def header_len_override_value(self, v):
        """header_len_override_value : """
        v = v*4
        # v = str(v).split('.')[0]
        # v = int(v)
        self._header_len_override_value.current_val = v

    @property
    def qos_type(self):
        """qos_type : """
        return self._qos_type.current_val

    @qos_type.setter
    def qos_type(self, v):
        """qos_type : """
        self._qos_type.current_val = v

    @property
    def tos_precedence(self):
        """tos_precedence : """
        return self._tos_precedence.current_val

    @tos_precedence.setter
    def tos_precedence(self, v):
        """tos_precedence : """
        self._tos_precedence.current_val = v

    @property
    def tos_delay(self):
        """tos_delay : """
        return self._tos_delay.current_val

    @tos_delay.setter
    def tos_delay(self, v):
        """tos_delay : """
        self._tos_delay.current_val = v

    @property
    def tos_throughput(self):
        """tos_throughput : """
        return self._tos_throughput.current_val

    @tos_throughput.setter
    def tos_throughput(self, v):
        """tos_throughput : """
        self._tos_throughput.current_val = v

    @property
    def tos_reliability(self):
        """tos_reliability : """
        return self._tos_reliability.current_val

    @tos_reliability.setter
    def tos_reliability(self, v):
        """tos_reliability : """
        self._tos_reliability.current_val = v

    @property
    def tos_cost(self):
        """tos_cost : """
        return self._tos_cost.current_val

    @tos_cost.setter
    def tos_cost(self, v):
        """tos_cost : """
        self._tos_cost.current_val = v

    @property
    def tos_reserved(self):
        """tos_reserved : """
        return self._tos_reserved.current_val

    @tos_reserved.setter
    def tos_reserved(self, v):
        """tos_reserved : """
        self._tos_reserved.current_val = v

    @property
    def dscp_decimal_value(self):
        """dscp_decimal_value : """
        return self._dscp_decimal_value.current_val

    @dscp_decimal_value.setter
    def dscp_decimal_value(self, v):
        """dscp_decimal_value : """
        self._dscp_decimal_value.current_val = v

    @property
    def length_override(self):
        """length_override : """
        return self._length_override.current_val

    @length_override.setter
    def length_override(self, v):
        """length_override : """
        self._length_override.current_val = v

    @property
    def length_value(self):
        """length_value : """
        return self._length_value.current_val

    @length_value.setter
    def length_value(self, v):
        """length_value : """
        self._length_value.current_val = v

    @property
    def identifier(self):
        """identifier : """
        return self._identifier.current_val

    @identifier.setter
    def identifier(self, v):
        """identifier : """
        self._identifier.current_val = v

    @property
    def fragment_enable(self):
        """fragment_enable : """
        return self._fragment_enable.current_val

    @fragment_enable.setter
    def fragment_enable(self, v):
        """fragment_enable : """
        self._fragment_enable.current_val = v

    @property
    def fragment_last_enable(self):
        """fragment_last_enable : """
        return self._fragment_last_enable.current_val

    @fragment_last_enable.setter
    def fragment_last_enable(self, v):
        """fragment_last_enable : """
        self._fragment_last_enable.current_val = v

    @property
    def fragment_offset_decimal_value(self):
        """fragment_offset_decimal_value : """
        return self._fragment_offset_decimal_value.current_val

    @fragment_offset_decimal_value.setter
    def fragment_offset_decimal_value(self, v):
        """fragment_offset_decimal_value : """
        self._fragment_offset_decimal_value.current_val = v

    @property
    def ttl(self):
        """ttl : """
        return self._ttl.current_val

    @ttl.setter
    def ttl(self, v):
        """ttl : """
        self._ttl.current_val = v

    @property
    def protocol(self):
        """protocol : """
        return self._protocol.current_val

    @protocol.setter
    def protocol(self, v):
        """protocol : """
        self._protocol.current_val = v

    @property
    def checksum_mode(self):
        """valid_checksum : """
        return self._checksum_mode.current_val

    @checksum_mode.setter
    def checksum_mode(self, v):
        """checksum_mode : """
        self._checksum_mode.current_val = v

    @property
    def custom_checksum(self):
        """custom_checksum : """
        val = self._custom_checksum.current_val.rstrip("}")
        val = val.lstrip("{")
        return val

    @custom_checksum.setter
    def custom_checksum(self, v):
        """custom_checksum : """
        v = "{" + v + "}"
        self._custom_checksum.current_val = v

    @property
    def options_padding(self):
        """options_padding : """
        val = self._options_padding.current_val.rstrip("}")
        val = val.lstrip("{")
        return val

    @options_padding.setter
    def options_padding(self, v):
        """options_padding : """
        v = "{" + v + "}"
        self._options_padding.current_val = v

    @property
    def source_ip(self):
        """source_ip : """
        return self._source_ip

    @source_ip.setter
    def source_ip(self, v):
        """source_ip : """
        self._source_ip = v

    @property
    def destination_ip(self):
        """destination_ip : """
        return self._destination_ip

    @destination_ip.setter
    def destination_ip(self, v):
        """destination_ip : """
        self._destination_ip = v

    def _reset_to_default(self):
        self.source_ip._value._reset_to_default()
        self.source_ip._mode._reset_to_default()
        self.source_ip._count._reset_to_default()
        self.source_ip._step._reset_to_default()
        self.source_ip._mask._reset_to_default()
        self.destination_ip._value._reset_to_default()
        self.destination_ip._mode._reset_to_default()
        self.destination_ip._count._reset_to_default()
        self.destination_ip._step._reset_to_default()
        self.destination_ip._mask._reset_to_default()

        self._enable_header_len_override._reset_to_default()
        self._header_len_override_value._reset_to_default()
        self._qos_type._reset_to_default()
        self._tos_precedence._reset_to_default()
        self._tos_delay._reset_to_default()
        self._tos_throughput._reset_to_default()
        self._tos_reliability._reset_to_default()
        self._tos_cost._reset_to_default()
        self._tos_reserved._reset_to_default()
        self._dscp_decimal_value._reset_to_default()
        self._length_override._reset_to_default()
        self._length_value._reset_to_default()
        self._identifier._reset_to_default()
        self._fragment_enable._reset_to_default()
        self._fragment_last_enable._reset_to_default()
        self._fragment_offset_decimal_value._reset_to_default()
        self._ttl._reset_to_default()
        self._protocol._reset_to_default()
        self._checksum_mode._reset_to_default()
        self._custom_checksum._reset_to_default()
        self._options_padding._reset_to_default()

class IPV6(header_object):
    def __init__(self):
        self._source_ip = AddressModifierField(default_val="0000:0000:0000:0000:0000:0000:0000:0000",
                                               default_mode=TGEnums.MODIFIER_IPV6_ADDRESS_MODE.FIXED, default_count=0,
                                               default_mask="96", default_step="1")
        self._destination_ip = AddressModifierField(default_val="0000:0000:0000:0000:0000:0000:0000:0000",
                                                    default_mode=TGEnums.MODIFIER_IPV6_ADDRESS_MODE.FIXED,
                                                    default_count=0, default_mask="96", default_step="1")
        self._traffic_class = attrWithDefault("0")
        self._flow_label = attrWithDefault("0")
        # self._payload_length = attrWithDefault("0")
        self._next_header = attrWithDefault("59")
        self._hop_limit = attrWithDefault("255")
        self.extention_headers = IPv6_Extension_Headers()

    def __iter__(self):
        return iter([attr for attr in dir(self) if attr[:2] != "__"])

    def __str__(self):
        str_delimit = ", "
        temp_str = "IPV6: SIP[{1}, mode={7}, count={8}, step={9}, mask={10}]{0}DIP[{2}, mode={11}, count={12}, step={13}, mask={14}]{0}HOP_LIMIT[{3}]{0}NEXT_HEADER[{4}]{0}FLOW_LABEL[{5}]{0}TRAFFIC_CLASS[{6}]".format(
            str_delimit,
            self.source_ip.value,
            self.destination_ip.value,
            self.hop_limit,
            self.next_header,
            self.flow_label,
            self.traffic_class,
            self.source_ip.mode,
            self.source_ip.count,
            self.source_ip.step,
            self.source_ip.mask,
            self.destination_ip.mode,
            self.destination_ip.count,
            self.destination_ip.step,
            self.destination_ip.mask
        )

        return temp_str

    @property
    def source_ip(self):
        """source_ip : """
        return self._source_ip

    @source_ip.setter
    def source_ip(self, v):
        """source_ip : """
        self._source_ip = v

    @property
    def destination_ip(self):
        """destination_ip : """
        return self._destination_ip

    @destination_ip.setter
    def destination_ip(self, v):
        """destination_ip : """
        self._destination_ip = v

    @property
    def traffic_class(self):
        """traffic_class : """
        return self._traffic_class.current_val

    @traffic_class.setter
    def traffic_class(self, v):
        """traffic_class : """
        self._traffic_class.current_val = v

    @property
    def flow_label(self):
        """flow_label : """
        return self._flow_label.current_val

    @flow_label.setter
    def flow_label(self, v):
        """flow_label : """
        self._flow_label.current_val = v

    @property
    def next_header(self):
        """next_header : """
        return self._next_header.current_val

    @next_header.setter
    def next_header(self, v):
        """next_header : """
        self._next_header.current_val = v

    @property
    def hop_limit(self):
        """hop_limit : """
        return self._hop_limit.current_val

    @hop_limit.setter
    def hop_limit(self, v):
        """hop_limit : """
        self._hop_limit.current_val = v

    def _reset_to_default(self):
        self._source_ip._value._reset_to_default()
        self._source_ip._mode._reset_to_default()
        self._source_ip._count._reset_to_default()
        self._source_ip._step._reset_to_default()
        self._source_ip._mask._reset_to_default()
        self._destination_ip._value._reset_to_default()
        self._destination_ip._mode._reset_to_default()
        self._destination_ip._count._reset_to_default()
        self._destination_ip._step._reset_to_default()
        self._destination_ip._mask._reset_to_default()
        self._traffic_class._reset_to_default()
        self._flow_label._reset_to_default()
        # self._payload_length._reset_to_default()
        self._next_header._reset_to_default()
        self._hop_limit._reset_to_default()

class TCP(header_object):
    def __init__(self):
        self._source_port = BaseField(default_val=0,default_count=1, default_step=1,
                                      default_mode=TGEnums.MODIFIER_L4_PORT_MODE.FIXED)
        self._destination_port = BaseField(default_val=0,default_count=1, default_step=1,
                                      default_mode=TGEnums.MODIFIER_L4_PORT_MODE.FIXED)
        self._sequence_number = attrWithDefault("0")
        self._acknowledgement_number = attrWithDefault("0")
        self._header_length = attrWithDefault("5")
        self._window = attrWithDefault("0")
        self._valid_checksum = attrWithDefault(TGEnums.CHECKSUM_MODE.VALID)
        self._custom_checksum = attrWithDefault("0")
        self._urgent_pointer = attrWithDefault("0")
        self._flag_urgent_pointer_valid = attrWithDefault(False)
        self._flag_acknowledge_valid = attrWithDefault(False)
        self._flag_push_function = attrWithDefault(False)
        self._flag_reset_connection = attrWithDefault(False)
        self._flag_synchronize_sequence = attrWithDefault(False)
        self._flag_no_more_data_from_sender = attrWithDefault(False)

    def __iter__(self):
        return iter([attr for attr in dir(self) if attr[:2] != "__"])

    def __str__(self):
        str_delimit = ", "
        temp_str = "TCP: SPORT[{1}, mode={16}, count={17}, step={18}]{0}DPORT[{2}, mode={19}, count={20}, step={21}]{0}SEQ[{3}]{0}" \
                   "ACK[{4}]{0}LEN[{5}]{0}WINDOW[{6}]{0}VALID_CHEKSUM[{7}]{0}CUSTOM_CHECKSUM[{8}{0}URG[{9}]{0}" \
                   "FLAG_URG[{10}]{0}FLAG_ACK[{11}]{0}FLAG_PUSH[{12}]{0}FLAG_RESET[{13}]{0}FLAG_SYN[{14}]{0}FLAG_NO_MORE_DATA[{15}]]".format(
            str_delimit,
            self.source_port.value,
            self.destination_port.value,
            self.sequence_number,
            self.acknowledgement_number,
            self.header_length,
            self.window,
            self.valid_checksum,
            self.custom_checksum,
            self.urgent_pointer,
            self.flag_urgent_pointer_valid,
            self.flag_acknowledge_valid,
            self.flag_push_function,
            self.flag_reset_connection,
            self.flag_synchronize_sequence,
            self.flag_no_more_data_from_sender,
            self.source_port.mode,
            self.source_port.count,
            self.source_port.step,
            self.destination_port.mode,
            self.destination_port.count,
            self.destination_port.step
        )

        return temp_str

    @property
    def source_port(self):
        """source_port : """
        return self._source_port

    @source_port.setter
    def source_port(self, v):
        """source_port : """
        self._source_port = v

    @property
    def destination_port(self):
        """destination_port : """
        return self._destination_port

    @destination_port.setter
    def destination_port(self, v):
        """destination_port : """
        self._destination_port = v

    @property
    def sequence_number(self):
        """sequence_number : """
        return self._sequence_number.current_val

    @sequence_number.setter
    def sequence_number(self, v):
        """sequence_number : """
        self._sequence_number.current_val = v

    @property
    def acknowledgement_number(self):
        """acknowledgement_number : """
        return self._acknowledgement_number.current_val

    @acknowledgement_number.setter
    def acknowledgement_number(self, v):
        """acknowledgement_number : """
        self._acknowledgement_number.current_val = v

    @property
    def header_length(self):
        """header_length : """
        return self._header_length.current_val

    @header_length.setter
    def header_length(self, v):
        """header_length : """
        self._header_length.current_val = v

    @property
    def window(self):
        """window : """
        return self._window.current_val

    @window.setter
    def window(self, v):
        """window : """
        self._window.current_val = v

    @property
    def valid_checksum(self):
        """valid_checksum : """
        return self._valid_checksum.current_val

    @valid_checksum.setter
    def valid_checksum(self, v):
        """valid_checksum : """
        self._valid_checksum.current_val = v

    @property
    def custom_checksum(self):
        """custom_checksum : """
        return self._custom_checksum.current_val

    @custom_checksum.setter
    def custom_checksum(self, v):
        """custom_checksum : """
        self._custom_checksum.current_val = v

    @property
    def urgent_pointer(self):
        """urgent_pointer : """
        return self._urgent_pointer.current_val

    @urgent_pointer.setter
    def urgent_pointer(self, v):
        """urgent_pointer : """
        self._urgent_pointer.current_val = v

    @property
    def flag_urgent_pointer_valid(self):
        """flag_urgent_pointer_valid : """
        return self._flag_urgent_pointer_valid.current_val

    @flag_urgent_pointer_valid.setter
    def flag_urgent_pointer_valid(self, v):
        """flag_urgent_pointer_valid : """
        self._flag_urgent_pointer_valid.current_val = v

    @property
    def flag_acknowledge_valid(self):
        """flag_acknowledge_valid : """
        return self._flag_acknowledge_valid.current_val

    @flag_acknowledge_valid.setter
    def flag_acknowledge_valid(self, v):
        """flag_acknowledge_valid : """
        self._flag_acknowledge_valid.current_val = v

    @property
    def flag_push_function(self):
        """flag_push_function : """
        return self._flag_push_function.current_val

    @flag_push_function.setter
    def flag_push_function(self, v):
        """flag_push_function : """
        self._flag_push_function.current_val = v

    @property
    def flag_reset_connection(self):
        """flag_reset_connection : """
        return self._flag_reset_connection.current_val

    @flag_reset_connection.setter
    def flag_reset_connection(self, v):
        """flag_reset_connection : """
        self._flag_reset_connection.current_val = v

    @property
    def flag_synchronize_sequence(self):
        """flag_synchronize_sequence : """
        return self._flag_synchronize_sequence.current_val

    @flag_synchronize_sequence.setter
    def flag_synchronize_sequence(self, v):
        """flag_synchronize_sequence : """
        self._flag_synchronize_sequence.current_val = v

    @property
    def flag_no_more_data_from_sender(self):
        """flag_no_more_data_from_sender : """
        return self._flag_no_more_data_from_sender.current_val

    @flag_no_more_data_from_sender.setter
    def flag_no_more_data_from_sender(self, v):
        """flag_no_more_data_from_sender : """
        self._flag_no_more_data_from_sender.current_val = v

    def _reset_to_default(self):
        self._source_port._value._reset_to_default()
        self._source_port._count._reset_to_default()
        self._source_port._step._reset_to_default()
        self._source_port._mode._reset_to_default()
        self._destination_port._value._reset_to_default()
        self._destination_port._count._reset_to_default()
        self._destination_port._step._reset_to_default()
        self._destination_port._mode._reset_to_default()
        self._sequence_number._reset_to_default()
        self._acknowledgement_number._reset_to_default()
        self._header_length._reset_to_default()
        self._window._reset_to_default()
        self._valid_checksum._reset_to_default()
        self._custom_checksum._reset_to_default()
        self._urgent_pointer._reset_to_default()
        self._flag_urgent_pointer_valid._reset_to_default()
        self._flag_acknowledge_valid._reset_to_default()
        self._flag_push_function._reset_to_default()
        self._flag_reset_connection._reset_to_default()
        self._flag_synchronize_sequence._reset_to_default()
        self._flag_no_more_data_from_sender._reset_to_default()

class UDP(header_object):
    def __init__(self):
        self._source_port = BaseField(default_val=0, default_count=1, default_step=1,
                                      default_mode=TGEnums.MODIFIER_L4_PORT_MODE.FIXED)
        self._destination_port = BaseField(default_val=0, default_count=1, default_step=1,
                                           default_mode=TGEnums.MODIFIER_L4_PORT_MODE.FIXED)
        self._valid_checksum = attrWithDefault(TGEnums.CHECKSUM_MODE.VALID)
        self._custom_checksum = attrWithDefault("0")
        self._length_override = attrWithDefault(False)
        self._custom_length = attrWithDefault("0")

    def __iter__(self):
        return iter([attr for attr in dir(self) if attr[:2] != "__"])

    def __str__(self):
        str_delimit = ", "
        temp_str = "UDP: SPORT[{1}, mode={7}, count={8}, step={9}]{0}DPORT[{2}, mode={10}, count={11}, step={12}]{0}" \
                   "VALID_CHEKSUM[{3}]{0}CUSTOM_CHECKSUM[{4}{0}LEN_OVERRIDE[{5}]{0}CUSTOM_LEN[{6}]".format(
            str_delimit,
            self.source_port.value,
            self.destination_port.value,
            self.valid_checksum,
            self.custom_checksum,
            self.length_override,
            self.custom_length,
            self.source_port.mode,
            self.source_port.count,
            self.source_port.step,
            self.destination_port.mode,
            self.destination_port.count,
            self.destination_port.step
        )

        return temp_str

    @property
    def source_port(self):
        """source_port : """
        return self._source_port

    @source_port.setter
    def source_port(self, v):
        """source_port : """
        self._source_port = v

    @property
    def destination_port(self):
        """destination_port : """
        return self._destination_port

    @destination_port.setter
    def destination_port(self, v):
        """destination_port : """
        self._destination_port = v

    @property
    def valid_checksum(self):
        """valid_checksum : """
        return self._valid_checksum.current_val

    @valid_checksum.setter
    def valid_checksum(self, v):
        """valid_checksum : """
        self._valid_checksum.current_val = v

    @property
    def custom_checksum(self):
        """custom_checksum : """
        return self._custom_checksum.current_val

    @custom_checksum.setter
    def custom_checksum(self, v):
        """custom_checksum : """
        self._custom_checksum.current_val = v

    @property
    def length_override(self):
        """length_override : """
        return self._length_override.current_val

    @length_override.setter
    def length_override(self, v):
        """length_override : """
        self._length_override.current_val = v

    @property
    def custom_length(self):
        """custom_length : """
        return self._custom_length.current_val

    @custom_length.setter
    def custom_length(self, v):
        """custom_length : """
        self._custom_length.current_val = v

    def _reset_to_default(self):
        self._source_port._value._reset_to_default()
        self._source_port._mode._reset_to_default()
        self._source_port._count._reset_to_default()
        self._source_port._step._reset_to_default()
        self._destination_port._value._reset_to_default()
        self._destination_port._mode._reset_to_default()
        self._destination_port._count._reset_to_default()
        self._destination_port._step._reset_to_default()
        self._valid_checksum._reset_to_default()
        self._custom_checksum._reset_to_default()
        self._length_override._reset_to_default()
        self._custom_length._reset_to_default()


class ICMP(header_object):
    def __init__(self):
        self._type = attrWithDefault(TGEnums.ICMP_HEADER_TYPE.ECHO_REPLY)
        self._code = attrWithDefault(0)
        self._id = attrWithDefault(0)
        self._sequence = attrWithDefault(0)

    @property
    def icmp_type(self):
        return self._type.current_val

    @icmp_type.setter
    def icmp_type(self,v):
        self._type.current_val = v

    @property
    def code(self):
        return self._code.current_val

    @code.setter
    def code(self, v):
        self._code.current_val = v

    @property
    def id(self):
        return self._id.current_val

    @id.setter
    def id(self, v):
        self._id.current_val = v

    @property
    def sequence(self):
        return self._sequence.current_val

    @sequence.setter
    def sequence(self, v):
        self._sequence.current_val = v

    def _reset_to_default(self):
        self._type._reset_to_default()
        self._code._reset_to_default()
        self._id._reset_to_default()
        self._sequence._reset_to_default()


class GRE(header_object):
    def __init__(self):
        self._version = attrWithDefault(0)
        self._reserve_0 = attrWithDefault(0)
        self._key_field = attrWithDefault(None)
        self._sequence_number = attrWithDefault(None)
        self._use_checksum = attrWithDefault(False)
        self._l3_proto = attrWithDefault(TGEnums.L3_PROTO.IPV4)
        self._l4_proto = attrWithDefault(TGEnums.L4_PROTO.NONE)
        self.ipv4 = IPV4()
        self.ipv6 = IPV6()
        self.tcp = TCP()
        self.udp = UDP()

    @property
    def version(self):
        return self._version.current_val

    @version.setter
    def version(self, v):
        self._version.current_val = v

    @property
    def reserve_0(self):
        return self._reserve_0.current_val

    @reserve_0.setter
    def reserve_0(self, v):
        self._reserve_0.current_val = v


    @property
    def key_field(self):
        return self._key_field.current_val

    @key_field.setter
    def key_field(self, v):
        self._key_field.current_val = v

    @property
    def sequence_number(self):
        return self._sequence_number.current_val

    @sequence_number.setter
    def sequence_number(self, v):
        self._sequence_number.current_val = v

    @property
    def use_checksum(self):
        return self._use_checksum.current_val

    @use_checksum.setter
    def use_checksum(self, v):
        self._use_checksum.current_val = v


    @property
    def l3_proto(self):
        """l3_proto : """
        return self._l3_proto.current_val

    @l3_proto.setter
    def l3_proto(self, v):
        """l3_proto :
        :param v:
        :type v: TGEnums.L3_PROTO
        """
        self._l3_proto.current_val = v

    @property
    def l4_proto(self):
        """l4_proto : """
        return self._l4_proto.current_val

    @l4_proto.setter
    def l4_proto(self, v):
        """l4_proto : """
        self._l4_proto.current_val = v

class DATA_PATTERN(header_object):
    def __init__(self):
        self._type = attrWithDefault(TGEnums.DATA_PATTERN_TYPE.REPEATING)
        self._value = attrWithDefault("0000")
        self._file_path = attrWithDefault(None)

    def __iter__(self):
        return iter([attr for attr in dir(self) if attr[:2] != "__"])

    def __str__(self):
        str_delimit = ", "
        temp_str = "DATA_PATTERN: TYPE[{1}]{0}VALUE[{2}]{0}FILE_PATH[{3}]".format(
            str_delimit,
            self.type,
            self.value,
            self.file_path,
        )

        return temp_str

    @property
    def type(self):
        """_type : """
        return self._type.current_val

    @type.setter
    def type(self, v):
        """_type : """
        self._type.current_val = v

    @property
    def value(self):
        """value : """
        return self._value.current_val

    @value.setter
    def value(self, v):
        """value : """
        self._value.current_val = v

    @property
    def file_path(self):
        """file_path : """
        return self._file_path.current_val

    @file_path.setter
    def file_path(self, v):
        """file_path : """
        self._file_path.current_val = v

    def _reset_to_default(self):
        self._type._reset_to_default()
        self._value._reset_to_default()
        self._file_path._reset_to_default()

class PROTOCOL_OFFSET(header_object):
    def __init__(self):
        self._offset = attrWithDefault("14")
        self._value = attrWithDefault("{}")

    def __iter__(self):
        return iter([attr for attr in dir(self) if attr[:2] != "__"])

    def __str__(self):
        str_delimit = ", "
        temp_str = "PROTOCOL_OFFSET: OFFSET[{1}]{0}VALUE[{2}]".format(
            str_delimit,
            self.offset,
            self.value,
        )

        return temp_str

    @property
    def offset(self):
        """_offset : """
        return self._offset.current_val

    @offset.setter
    def offset(self, v):
        """_offset : """
        self._offset.current_val = v

    @property
    def value(self):
        """_value : """
        val = self._value.current_val.rstrip("}")
        val = val.lstrip("{")
        return val

    @value.setter
    def value(self, v):
        """_value : """
        v = "{" + v + "}"
        self._value.current_val = v

    def _reset_to_default(self):
        self._offset._reset_to_default()
        self._value._reset_to_default()

class MODIFIER(object):
    def __init__(self, udf_name=None):
        self._name = udf_name
        self._enabled = attrWithDefault(False)
        self._byte_offset = attrWithDefault("12")
        self._bit_offset = attrWithDefault("0")
        self._mode = attrWithDefault(TGEnums.MODIFIER_UDF_MODE.COUNTER)
        self._bit_type = attrWithDefault(TGEnums.MODIFIER_UDF_BITS_MODE.BITS_8)
        self._from_chain = attrWithDefault(TGEnums.MODIFIER_UDF_FROM_CHAIN_MODE.NONE)
        self._continuously_counting = attrWithDefault(True)
        self._repeat_count = attrWithDefault("1")
        self._repeat_step = attrWithDefault("1")
        self._repeat_init = attrWithDefault("00")
        self._repeat_mode = attrWithDefault(TGEnums.MODIFIER_UDF_REPEAT_MODE.UP)
        self._driver_obj = None
        self._inner_repeat_count = attrWithDefault("1")
        self._inner_repeat_step = attrWithDefault("1")
        self._inner_repeat_loop = attrWithDefault("1")
        self._value_list = attrWithDefault(None)

    def __iter__(self):
        return iter([attr for attr in dir(self) if attr[:2] != "__"])

    def __str__(self):
        str_delimit = ", "
        temp_str = ""
        return temp_str

    @property
    def value_list(self):
        return self._value_list.current_val

    @value_list.setter
    def value_list(self,value_list):
        self._value_list.current_val = value_list

    @property
    def enabled(self):
        """enabled : """
        return self._enabled.current_val

    @enabled.setter
    def enabled(self, v):
        """enabled docstring"""
        self._enabled.current_val = v

    @property
    def byte_offset(self):
        """byte_offset : """
        return self._byte_offset.current_val

    @byte_offset.setter
    def byte_offset(self, v):
        """byte_offset docstring"""
        self._byte_offset.current_val = v

    @property
    def bit_offset(self):
        """bit_offset : """
        return self._bit_offset.current_val

    @bit_offset.setter
    def bit_offset(self, v):
        """bit_offset docstring"""
        self._bit_offset.current_val = v

    @property
    def mode(self):
        """mode : """
        return self._mode.current_val

    @mode.setter
    def mode(self, v):
        """mode docstring"""
        self._mode.current_val = v

    @property
    def bit_type(self):
        """bit_type : """
        return self._bit_type.current_val

    @bit_type.setter
    def bit_type(self, v):
        """bit_type docstring"""
        self._bit_type.current_val = v

    @property
    def from_chain(self):
        """from_chain : """
        return self._from_chain.current_val

    @from_chain.setter
    def from_chain(self, v):
        """from_chain docstring"""
        self._from_chain.current_val = v

    @property
    def continuously_counting(self):
        """continuously_counting : """
        return self._continuously_counting.current_val

    @continuously_counting.setter
    def continuously_counting(self, v):
        """continuously_counting docstring"""
        self._continuously_counting.current_val = v

    @property
    def repeat_count(self):
        """repeat_count : """
        return self._repeat_count.current_val

    @repeat_count.setter
    def repeat_count(self, v):
        """repeat_count docstring"""
        self._repeat_count.current_val = v

    @property
    def repeat_step(self):
        """repeat_step : """
        return self._repeat_step.current_val

    @repeat_step.setter
    def repeat_step(self, v):
        """repeat_step docstring"""
        self._repeat_step.current_val = v

    @property
    def repeat_init(self):
        """repeat_init : """
        return self._repeat_init.current_val

    @repeat_init.setter
    def repeat_init(self, v):
        """repeat_init docstring"""
        self._repeat_init.current_val = v

    @property
    def repeat_mode(self):
        """repeat_mode : """
        return self._repeat_mode.current_val

    @repeat_mode.setter
    def repeat_mode(self, v):
        """repeat_mode docstring"""
        self._repeat_mode.current_val = v



    @property
    def inner_repeat_count(self):
        """repeat_count : """
        return self._inner_repeat_count.current_val

    @inner_repeat_count.setter
    def inner_repeat_count(self, v):
        """repeat_count docstring"""
        self._inner_repeat_count.current_val = v

    @property
    def inner_repeat_step(self):
        """repeat_count : """
        return self._inner_repeat_step.current_val

    @inner_repeat_step.setter
    def inner_repeat_step(self, v):
        """repeat_count docstring"""
        self._inner_repeat_step.current_val = v

    @property
    def inner_repeat_loop(self):
        """repeat_count : """
        return self._inner_repeat_loop.current_val

    @inner_repeat_loop.setter
    def inner_repeat_loop(self, v):
        """repeat_count docstring"""
        self._inner_repeat_loop.current_val = v







    def _reset_to_default(self):
        self._enabled._reset_to_default()
        self._byte_offset._reset_to_default()
        self._bit_offset._reset_to_default()
        self._mode._reset_to_default()
        self._bit_type._reset_to_default()
        self._from_chain._reset_to_default()
        self._continuously_counting._reset_to_default()
        self._repeat_count._reset_to_default()
        self._repeat_step._reset_to_default()
        self._repeat_init._reset_to_default()
        self._repeat_mode._reset_to_default()

class DATA_INTEGRITY(object):
    def __init__(self):
        self._enable = attrWithDefault(False)
        self._signature = attrWithDefault("08711800")
        self._signature_offset = attrWithDefault("40")
        self._enable_time_stamp = attrWithDefault(False)

    def __iter__(self):
        return iter([attr for attr in dir(self) if attr[:2] != "__"])

    @property
    def enable(self):
        """_enable : """
        return self._enable.current_val

    @enable.setter
    def enable(self, v):
        """_enable : """
        self._enable.current_val = v

    @property
    def signature(self):
        """_signature : """
        val = self._signature.current_val.rstrip("}")
        val = val.lstrip("{")
        return val

    @signature.setter
    def signature(self, v):
        """_signature : """
        v = "{" + v + "}"
        self._signature.current_val = v

    @property
    def signature_offset(self):
        """_signature_offset : """
        return self._signature_offset.current_val

    @signature_offset.setter
    def signature_offset(self, v):
        """_signature_offset : """
        self._signature_offset.current_val = v

    @property
    def enable_time_stamp(self):
        """_enable_time_stamp : """
        return self._enable_time_stamp.current_val

    @enable_time_stamp.setter
    def enable_time_stamp(self, v):
        """_enable_time_stamp : """
        self._enable_time_stamp.current_val = v

    def _reset_to_default(self):
        self._enable._reset_to_default()
        self._signature._reset_to_default()
        self._signature_offset._reset_to_default()
        self._enable_time_stamp._reset_to_default()

class DSA_Forward(header_object):
    def __init__(self, extend=0):
    #word0
        self.Tag_Command = 3
        self.Tag0_Src_Tagged = 0
        self.Src_Dev_4_0 = 0
        self.Src_Trunk_ePort_4_0 = 0
        self.Src_Is_Trunk = 0
        self.Hash_0 = 0
        self.CFI = 0
        self.UP = 0
        self.w0_Extend = extend
        self.eVLAN_11_0 = 0

class extDSA_Forward_use_vidx_0(DSA_Forward):
    def __init__(self, extend=0):
        super(extDSA_Forward_use_vidx_0, self).__init__(1)
    #word1
        self.w1_Extend = extend
        self.Src_Trunk_ePort_6_5 = 0
        self.Egress_Filter_Registered = 0
        self.Drop_On_Source = 0
        self.Packet_Is_Looped = 0
        self.Routed = 0
        self.Src_ID = 0
        self.Global_QoS_Profile = 0
        self.use_eVIDX = 0
        self.Trg_Phy_Port_6_0 = 0
        self.Trg_Dev = 0

class extDSA_Forward_use_vidx_1(DSA_Forward):
    def __init__(self, extend=0):
        super(extDSA_Forward_use_vidx_1, self).__init__(1)
    #word1
        self.w1_Extend = extend
        self.Src_Trunk_ePort_6_5 = 0
        self.Egress_Filter_Registered = 0
        self.Drop_On_Source = 0
        self.Packet_Is_Looped = 0
        self.Routed = 0
        self.Src_ID = 0
        self.Global_QoS_Profile = 0
        self.use_eVIDX = 1
        self.eVIDX_11_0 = 0

class EDSA_Forward_use_vidx_0(extDSA_Forward_use_vidx_0):
    def __init__(self):
        super(EDSA_Forward_use_vidx_0, self).__init__(1)
    #word2
        self.w2_Extend = 1
        self.Skip_FDB = 0
        self.Is_Trg_Phy_Port_Valid = 0
        self.Trg_Phy_Port_7 = 0
        #self.Reserved = 0
        self.Src_ID_11_5 = 0
        self.Hash_3_2 = 0
        self.Src_Dev_9_5 = 0
        self.Hash_1 = 0
        #self.Reserved = 0
        self.Src_Trunk_ePort_11_7 = 0
        # self.Reserved = 0
        self.TPID_Index = 0
    #word3
        self.w3_Extend = 0
        self.eVLAN_15_12 = 0
        self.Tag1_Src_Tagged = 0
        self.Src_Tag0_IsOuter_Tag = 0
        #self.Reserved
        self.Trg_Phy_Port_9_8 = 0
        self.Trg_ePort_15_0 = 0
        self.Hash_5_4_vidx0 = 0
        self.Trg_Dev_9_5 = 0

class EDSA_Forward_use_vidx_1(extDSA_Forward_use_vidx_1):
    def __init__(self):
        super(EDSA_Forward_use_vidx_1, self).__init__(1)
    #word2
        self.w2_Extend = 1
        self.Skip_FDB = 0
        #self.Reserved = 0
        self.Src_ID_11_5 = 0
        self.Hash_3_2 = 0
        self.Src_Dev_9_5 = 0
        self.Hash_1 = 0
        #self.Reserved = 0
        self.Src_Trunk_ePort_11_7 = 0
        # self.Reserved = 0
        self.TPID_Index = 0
    #word3
        self.w3_Extend = 0
        self.eVLAN_15_12 = 0
        self.Tag1_Src_Tagged = 0
        self.Src_Tag0_IsOuter_Tag = 0
        #self.Reserved
        self.eVIDX_15_12 = 0
        self.Orig_Src_Phy_Is_Trunk = 0
        self.Orig_Src_Phy_Port_Trunk = 0
        self.Phy_Src_MC_Filter_Enable = 0
        self.Hash_5_4_vidx1 = 0
        #self.Reserved = 0

class DSA_From_CPU_use_vidx_1(header_object):
    def __init__(self, extend=0):
        #word0
        self.Tag_Command = 1
        self.use_eVIDX = 1
        self.TC_0 = 0
        self.CFI = 0
        self.UP = 0
        self.w0_Extend = extend
        self.eVLAN_11_0 = 0
        # vidx= 1
        self.Tag0_Src_Tagged = 0
        self.eVIDX_9_0 = 0

class DSA_From_CPU_use_vidx_0(header_object):
    def __init__(self, extend=0):
        #word0
        self.Tag_Command = 1
        self.use_eVIDX = 0
        self.TC_0 = 0
        self.CFI = 0
        self.UP = 0
        self.w0_Extend = extend
        self.eVLAN_11_0 = 0
        #vidx= 0
        self.Trg_Tagged = 0
        self.Trg_Dev = 0
        self.Trg_Phy_Port_4_0 = 0

class extDSA_From_CPU_use_vidx_0(DSA_From_CPU_use_vidx_0):
    def __init__(self, extend=0):
        super(extDSA_From_CPU_use_vidx_0, self).__init__(1)
        #word1
        self.w1_Extend = extend
        self.Egress_Filter_Enable = 0
        #self.Reserved
        self.Egress_Filter_Registered = 0
        self.TC_2 = 0
        self.Drop_On_Source = 0
        self.Packet_Is_Looped = 0
        self.Src_ID_4_0 = 0
        self.Src_Dev_4_0 = 0
        self.TC_1 = 0
        #use_vidx = 0
        self.Mailbox_To_Neighbor_CPU = 0
        #self.Reserved = 0
        self.Trg_Phy_Port_6_5 = 0
        #self.Reserved = 0

class extDSA_From_CPU_use_vidx_1_exclude_is_trunk_0(DSA_From_CPU_use_vidx_1):
    def __init__(self, extend=0):
        super(extDSA_From_CPU_use_vidx_1_exclude_is_trunk_0, self).__init__(1)
        #word1
        self.w1_Extend = extend
        self.Egress_Filter_Enable = 0
        #self.Reserved
        self.Egress_Filter_Registered = 0
        self.TC_2 = 0
        self.Drop_On_Source = 0
        self.Packet_Is_Looped = 0
        self.Src_ID_4_0 = 0
        self.Src_Dev_4_0 = 0
        self.TC_1 = 0
        #use_vidx = 1
        self.eVIDX_11_10 = 0
        self.Exclude_Is_Trunk = 0
        self.Excluded_Phy_Port_ePort_5_0 = 0
        self.Excluded_Dev = 0

class extDSA_From_CPU_use_vidx_1_exclude_is_trunk_1(DSA_From_CPU_use_vidx_1):
    def __init__(self, extend=0):
        super(extDSA_From_CPU_use_vidx_1_exclude_is_trunk_1, self).__init__(1)
        #word1
        self.w1_Extend = extend
        self.Egress_Filter_Enable = 0
        #self.Reserved
        self.Egress_Filter_Registered = 0
        self.TC_2 = 0
        self.Drop_On_Source = 0
        self.Packet_Is_Looped = 0
        self.Src_ID_4_0 = 0
        self.Src_Dev_4_0 = 0
        self.TC_1 = 0
        #use_vidx = 1
        self.eVIDX_11_10 = 0
        self.Exclude_Is_Trunk = 1
        self.Mirror_To_All_CPUs = 0
        #self.Reserved
        self.Excluded_Trunk_6_0 = 0

class EDSA_From_CPU_use_vidx_0(extDSA_From_CPU_use_vidx_0):
    def __init__(self, extend=0):
        super(EDSA_From_CPU_use_vidx_0, self).__init__(1)
        #word2
        self.w2_Extend = 1
        #self.Reserved = 0
        #vidx = 0
        self.Is_Trg_Phy_Port_Valid = 0
        self.Trg_Phy_Port_7 = 0
        self.Src_ID_11_5 = 0
        #self.Reserved = 0
        self.Src_Dev_9_5 = 0
        # self.Reserved = 0
        self.TPID_Index = 0
        #word3
        self.w3_Extend = 0
        self.eVLAN_15_12 = 0
        self.Tag1_SrcTagged = 0
        self.SrcTag0_Is_OuterTag = 0
        self.Trg_Phy_Port= 0
        self.TRGePort_15_0 = 0
        self.TrgDev_11_5 = 0

class EDSA_From_CPU_use_vidx_1_exclude_is_trunk_0(extDSA_From_CPU_use_vidx_1_exclude_is_trunk_0):
    def __init__(self, extend=0):
        super(EDSA_From_CPU_use_vidx_1_exclude_is_trunk_0, self).__init__(1)
        # word2
        self.w2_Extend = 1
        #self.Reserved = 0
        #self.Reserved = 0
        #vidx = 1
        self.Src_ID_11_5 = 0
        #self.Reserved = 0
        self.Src_Dev_9_5 = 0
        self.Excluded_Phy_Port_ePort_16_6 = 0
        self.TPID_Index = 0
        #word3
        self.w3_Extend = 0
        self.eVLAN_15_12 = 0
        self.Tag1_SrcTagged = 0
        self.SrcTag0_Is_OuterTag = 0
        #usevidx = 1
        # self.Reserved = 0
        self.eVIDX_15_12 = 0
        self.Excluded_Is_PhyPort = 0
        # self.Reserved = 0
        #excludedTrunk = 0
        self.ExcludedDev_11_5 = 0

class EDSA_From_CPU_use_vidx_1_exclude_is_trunk_1(extDSA_From_CPU_use_vidx_1_exclude_is_trunk_1):
    def __init__(self, extend=0):
        super(EDSA_From_CPU_use_vidx_1_exclude_is_trunk_1, self).__init__(1)
        # word2
        self.w2_Extend = 1
        #self.Reserved = 0
        #self.Reserved = 0
        #vidx = 1
        self.Src_ID_11_5 = 0
        #self.Reserved = 0
        self.Src_Dev_9_5 = 0
        # self.Reserved = 0
        self.Excluded_Trunk_11_7 = 0
        self.TPID_Index = 0
        #word3
        self.w3_Extend = 0
        self.eVLAN_15_12 = 0
        self.Tag1_SrcTagged = 0
        self.SrcTag0_Is_OuterTag = 0
        #usevidx = 1
        # self.Reserved = 0
        self.eVIDX_15_12 = 0
        self.Excluded_Is_PhyPort = 0
        # self.Reserved = 0
        #excludedTrunk = 1
        # self.Reserved = 0

class DSA_To_CPU(header_object):
    def __init__(self, extend=0):
        #word0
        self.Tag_Command = 0
        self.SrcTrg_Tagged = 0
        self.SrcDev_TrgDev_4_0 = 0
        self.SrcPhyPort_TrgPhyPort_4_0 = 0
        self._w0_Reserved_16 = 1
        self.UP = 0
        self.w0_Extend = extend
        self.eVLAN_11_0 = 0

class extDSA_To_CPU(DSA_To_CPU):
    def __init__(self, extend=0):
        super(extDSA_To_CPU, self).__init__(1)
        #word1
        self.w1_Extend = extend
        self.CFI = 0
        self.Drop_On_Source = 0
        self.Packet_Is_Looped = 0
        self.Orig_Is_Trunk = 0
        self.Truncated = 0
        self.Timestamp_14_1_Pkt_Orig_BC = 0
        self.SrcPhyPort_TrgPhyPort_6_5 = 0
        self.Timestamp_0_Reserved = 0
        self.Src_Trg = 0
        self.Long_CPU_Code = 0

class EDSA_To_CPU(extDSA_To_CPU):
    def __init__(self, extend=0):
        super(EDSA_To_CPU, self).__init__(1)
        #word2
        self.w2_Extend = 1
        #self.reserved = 0
        self.Packet_Is_TT = 0
        #self.reserved = 0
        self.SrcPhyPort_TrgPhyPort_9_7 = 0
        # self.reserved = 0
        self.SrcePort_TrgePort_15_0_SrcTrunk_11_0 = 0
        self.TPID_Index = 0
        #word3
        self.w3_Extend = 0
        self.eVLAN_15_12 = 0
        self.Flow_ID_TT_Offset = 0
        # self.reserved = 0
        self.SrcDev_TrgDev_9_5 = 0

class DSA_To_ANALYZER(header_object):
    def __init__(self, extend=0):
        #word0
        self.Tag_Command = 2
        self.SrcTrg_Tagged = 0
        self.SrcDev_TrgDev_4_0 = 0
        self.SrcPhyPort_TrgPhyPort_4_0 = 0
        self.rx_sniff = 0
        #self.Reserved = 0
        self.CFI = 0
        self.UP = 0
        self.w0_Extend = extend
        self.eVLAN_11_0 = 0

class extDSA_To_ANALYZER(DSA_To_ANALYZER):
    def __init__(self, extend=0):
        super(extDSA_To_ANALYZER, self).__init__(1)
        #word1
        self.w1_Extend = extend
        #self.Reserved = 0
        self.Drop_On_Source = 0
        self.Packet_Is_Looped = 0
        self.Analyzer_Is_Trg_Phy_Port_Valid = 0
        self.Analyzer_Use_eVIDX = 0
        self.Analyzer_Trg_Dev = 0
        # self.Reserved = 0
        self.SrcPhyPort_TrgPhyPort_5 = 0
        self.Analyzer_Trg_Phy_Port = 0

class EDSA_To_ANALYZER_use_eVIDX_0(extDSA_To_ANALYZER):
    def __init__(self, extend=0):
        super(EDSA_To_ANALYZER_use_eVIDX_0, self).__init__(1)
        #word2
        self.w2_Extend = 1
        # self.Reserved = 0
        self.SrcPhyPort_TrgPhyPort_7 = 0
        # self.Reserved = 0
        self.SrcePort_TrgePort_15_0 = 0
        self.TPID_Index = 0
        #word3
        self.w3_Extend = 0
        self.eVLAN_15_12 = 0
        # self.Reserved = 0
        self.Analyzer_ePort = 0
        # self.Reserved = 0
        self.SrcDev_TrgDev_9_5 = 0

class EDSA_To_ANALYZER_use_eVIDX_1(extDSA_To_ANALYZER):
    def __init__(self, extend=0):
        super(EDSA_To_ANALYZER_use_eVIDX_1, self).__init__(1)
        #word2
        self.w2_Extend = 1
        # self.Reserved = 0
        self.SrcPhyPort_TrgPhyPort_7 = 0
        # self.Reserved = 0
        self.SrcePort_TrgePort_15_0 = 0
        self.TPID_Index = 0
        #word3
        self.w3_Extend = 0
        self.eVLAN_15_12 = 0
        # self.Reserved = 0
        # self.Reserved = 0
        self.Analyzer_eVIDX = 0
        # self.Reserved = 0
        self.SrcDev_TrgDev_9_5 = 0


class IEEE_802(object):
    def __init__(self):
        self._pause_quanta = attrWithDefault(255)

class PauseControl(header_object):

    def __init__(self):
        self._destination_address = attrWithDefault('01:80:C2:00:00:01')
        self._ieee_mode = attrWithDefault(TGEnums.Flow_Control_Type.IEEE802_3x)
        self._ieee_802 = IEEE_802()

    @property
    def destination_address(self):
        """_offset : """
        return self._destination_address.current_val

    @destination_address.setter
    def destination_address(self, v):
        """_offset : """
        self._destination_address.current_val = v

    @property
    def pause_quanta(self):
        """_offset : """
        return self._ieee_802._pause_quanta.current_val

    @pause_quanta.setter
    def pause_quanta(self, v):
        """_offset : """
        self._ieee_802._pause_quanta.current_val = v


class MacSecHeader(header_object):
    def __init__(self):
        self.tciVersion = 0
        self.enableTciVersionOverride = False
        self.enableForceByteCorruption = False
        self.enableOverrideFlagRestriction = False
        self.enableTciEndStation = False
        self.enableTciIncludeSci = False
        self.enableTciSingleCopyBroadcast = False
        self.enableTciEncryption = False
        self.enableTciChangedText = False
        self.associationNumber = 0
        self.macAddress = '00 00 00 00 00 00'
        self.portIdentifier = 0
        self.enableShortLengthOverride = False
        self.shortLength = 0
        self.packetNumber = '00 00 00 00'


class MacSecChannel(object):
    def __init__(self):
        self.channelName = ''
        self.macAddress = '00 00 00 00 00 00'
        self.portIdentifier = 0
        self.enableAssociation = False
        self.associationKey = '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00'
        self.associationNumber = 0
        self.direction = 'macSecTransmit'


class MacSecBase(object):

    def __init__(self):
        self.numChannels = 0
        self.confidentialityOffset = 0
        self.channels = OrderedDict()  # type: list[MacSecChannel]

    def add_channel(self, name=None):
        if not name:
            name = 'channel_{}'.format(len(self.channelsList))
        self.channels[name]

    def delete_channel(self):
        pass

    def clear_channels(self):
        pass

class MacSecRx(MacSecBase):
    def __init__(self):
        super(self.__class__, self).__init__()

class MacSecTx(MacSecBase):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.negativeTestingOffset = 0
        self.negativeTestingMask = 0


class MacSec(object):
    def __init__(self):
        self._enable = attrWithDefault(None)
        self.header = MacSecHeader()
        self.Tx = MacSecTx()
        self.Rx = MacSecRx()

    @property
    def enable(self):
        return self._enable.current_val

    @enable.setter
    def enable(self,v):
        self._enable.current_val = v







