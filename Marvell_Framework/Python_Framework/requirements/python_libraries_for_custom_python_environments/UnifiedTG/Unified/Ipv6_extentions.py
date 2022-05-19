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

from enum import Enum
from collections import OrderedDict
#from UnifiedTG.Unified.Packet import header_object
from UnifiedTG.Unified.Utils import attrWithDefault
from UnifiedTG.Unified.TGEnums import TGEnums



class V6Option_PAD1(object):
    def __init__(self):
        self._mytype = TGEnums.Ipv6OptionType.PAD1

class V6Option_PADN(object):
    def __init__(self):
        self._mytype = TGEnums.Ipv6OptionType.PADN
        self.value = ''


class V6Option_Jumbo(object):
    def __init__(self):
        self._mytype = TGEnums.Ipv6OptionType.Jumbo
        self.payload = 0

class V6Option_RouterAlert(object):
    def __init__(self):
        self._mytype = TGEnums.Ipv6OptionType.RouterAlert
        self._type = attrWithDefault(TGEnums.RouterAlertType.MLD)

    @property
    def alert_type(self):
        return self._type.current_val

    @alert_type.setter
    def alert_type(self,v):
        self._type.current_val = v

class V6Option_BindingUpdate(object):
    def __init__(self):
        self._mytype = TGEnums.Ipv6OptionType.BindingUpdate
        self._length = attrWithDefault(8)
        self._acknowledge = attrWithDefault(0)
        self._home = attrWithDefault(0)
        self._router = attrWithDefault(0)
        self._duplicate = attrWithDefault(0)
        self._map = attrWithDefault(0)
        self._bicasting = attrWithDefault(0)
        self._prefix_length = attrWithDefault(0)
        self._sequence_number = attrWithDefault(0)
        self._life_time = attrWithDefault(0)

    @property
    def length(self):
        return self._length.current_val

    @length.setter
    def length(self,v):
        self._length.current_val = v

    @property
    def acknowledge(self):
        return self._acknowledge.current_val

    @acknowledge.setter
    def acknowledge(self, v):
        self._acknowledge.current_val = v

    @property
    def home(self):
        return self._home.current_val

    @home.setter
    def home(self, v):
        self._home.current_val = v

    @property
    def router(self):
        return self._router.current_val

    @router.setter
    def router(self, v):
        self._router.current_val = v

    @property
    def duplicate(self):
        return self._duplicate.current_val

    @duplicate.setter
    def duplicate(self, v):
        self._duplicate.current_val = v

    @property
    def map(self):
        return self._map.current_val

    @map.setter
    def map(self, v):
        self._map.current_val = v

    @property
    def bicasting(self):
        return self._bicasting.current_val

    @bicasting.setter
    def bicasting(self, v):
        self._bicasting.current_val = v

    @property
    def prefix_length(self):
        return self._prefix_length.current_val

    @prefix_length.setter
    def prefix_length(self, v):
        self._prefix_length.current_val = v

    @property
    def sequence_number(self):
        return self._sequence_number.current_val

    @sequence_number.setter
    def sequence_number(self, v):
        self._sequence_number.current_val = v

    @property
    def life_time(self):
        return self._life_time.current_val

    @life_time.setter
    def life_time(self, v):
        self._life_time.current_val = v

class V6Option_BindingAck(object):
    def __init__(self):
        self._mytype = TGEnums.Ipv6OptionType.BindingAcknowledgment
        self._length = attrWithDefault(8)
        self._status = attrWithDefault(0)
        self._sequence_number = attrWithDefault(0)
        self._life_time = attrWithDefault(0)
        self._refresh = attrWithDefault(0)

    @property
    def length(self):
        return self._length.current_val

    @length.setter
    def length(self,v):
        self._length.current_val = v

    @property
    def sequence_number(self):
        return self._sequence_number.current_val

    @sequence_number.setter
    def sequence_number(self, v):
        self._sequence_number.current_val = v

    @property
    def life_time(self):
        return self._life_time.current_val

    @life_time.setter
    def life_time(self, v):
        self._life_time.current_val = v

    @property
    def status(self):
        return self._status.current_val

    @status.setter
    def status(self, v):
        self._status.current_val = v

    @property
    def refresh(self):
        return self._refresh.current_val

    @refresh.setter
    def refresh(self, v):
        self._refresh.current_val = v

class V6Option_BindingRequest(object):
    def __init__(self):
        self._mytype = TGEnums.Ipv6OptionType.BindingRequest
        self._length = attrWithDefault(8)

    @property
    def length(self):
        return self._length.current_val

    @length.setter
    def length(self,v):
        self._length.current_val = v

class V6Option_HomeAddress(object):
    def __init__(self):
        self._mytype = TGEnums.Ipv6OptionType.HomeAddress
        self._length = attrWithDefault(16)
        self._address = attrWithDefault('0:0:0:0:0:0:0:0')

    @property
    def length(self):
        return self._length.current_val

    @length.setter
    def length(self,v):
        self._length.current_val = v

    @property
    def address(self):
        return self._address.current_val

    @address.setter
    def address(self, v):
        self._address.current_val = v

class V6Option_MIpV6UniqueIdSub(object):
    def __init__(self):
        self._mytype = TGEnums.Ipv6OptionType.MIpV6UniqueIdSub
        self.SubUniqueId = 0

class V6Option_MlpV6AlternativeCoaSub(object):
    def __init__(self):
        self._mytype = TGEnums.Ipv6OptionType.MlpV6AlternativeCoaSub
        self.address = '0:0:0:0:0:0:0:0'

class Ipv6_HopByHop_Extension(object):

    def __init__(self):
        self._opt_add_seq = []
        self._mytype = TGEnums.Ipv6ExtensionType.HopByHop
        self.options = OrderedDict()
        self.PAD1 = OrderedDict() # type: list[V6Option_PAD1]
        self.PADN = OrderedDict() # type: list[V6Option_PADN]
        self.jumbo = OrderedDict() # type: list[V6Option_Jumbo]
        self.router_alert = OrderedDict()  # type: list[V6Option_RouterAlert]
        self.binding_update = OrderedDict()  # type: list[V6Option_BindingUpdate]
        self.binding_ack = OrderedDict() # type: list[V6Option_BindingAck]
        self.binding_request = OrderedDict() # type: list[V6Option_BindingRequest]
        self.unique_id_sub = OrderedDict() # type: list[V6Option_MIpV6UniqueIdSub]
        self.alternative_coa_sub = OrderedDict() # type: list[V6Option_MlpV6AlternativeCoaSub]
        self.options[TGEnums.Ipv6OptionType.PAD1] = self.PAD1
        self.options[TGEnums.Ipv6OptionType.PADN] = self.PADN
        self.options[TGEnums.Ipv6OptionType.Jumbo] = self.jumbo
        self.options[TGEnums.Ipv6OptionType.RouterAlert] = self.router_alert
        self.options[TGEnums.Ipv6OptionType.BindingUpdate] = self.binding_update
        self.options[TGEnums.Ipv6OptionType.BindingAcknowledgment] = self.binding_ack
        self.options[TGEnums.Ipv6OptionType.BindingRequest] = self.binding_request
        self.options[TGEnums.Ipv6OptionType.MIpV6UniqueIdSub] = self.unique_id_sub
        self.options[TGEnums.Ipv6OptionType.MlpV6AlternativeCoaSub] = self.alternative_coa_sub
        self._auto_pad = attrWithDefault(True)

    @property
    def auto_pad(self):
        return self._auto_pad.current_val

    @auto_pad.setter
    def auto_pad(self,v):
        self._auto_pad.current_val = v

    def add_option(self, option_type):
        option_key = option_type.name +' '+ str(len(self.options[option_type]))
        option_obj = IPv6_Extension_Headers.ext_option_2obj[option_type]()
        self.options[option_type][option_key] = option_obj
        self._opt_add_seq.append(option_obj)
        return option_key

class IPV6_Routing_Extension(object):
    def __init__(self):
        self._mytype = TGEnums.Ipv6ExtensionType.Routing
        self._reserved = attrWithDefault("00 00 00 00")
        self._nodes = attrWithDefault('')

    @property
    def reserved(self):
        return self._reserved.current_val

    @reserved.setter
    def reserved(self,v):
        self._reserved.current_val = v

    @property
    def nodes(self):
        return self._nodes.current_val

    @nodes.setter
    def nodes(self,v):
        self._nodes = v

    def add_node(self,node):
        self._nodes.current_val = '{' + self._nodes.current_val.strip("{}") + ' '+node+'}'

class IPV6_Fragment_Extension(object):
    def __init__(self):
        self._mytype = TGEnums.Ipv6ExtensionType.Fragment
        self._reserved = attrWithDefault(0x1E)
        self._fragment_offset = attrWithDefault(100)
        self._res = attrWithDefault(11)
        self._mflag= attrWithDefault(True)
        self._id = attrWithDefault(286335522)

    @property
    def reserved(self):
        return self._reserved.current_val

    @reserved.setter
    def reserved(self,v):
        self._reserved.current_val = v

    @property
    def fragment_offset(self):
        return self._fragment_offset.current_val

    @fragment_offset.setter
    def fragment_offset(self,v):
        self._fragment_offset.current_val = v

    @property
    def res(self):
        return self._res.current_val

    @res.setter
    def res(self,v):
        self._res.current_val = v

    @property
    def mflag(self):
        return self._mflag.current_val

    @mflag.setter
    def mflag(self,v):
        self._mflag.current_val = v

    @property
    def id(self):
        return self._id.current_val

    @id.setter
    def id(self,v):
        self._id.current_val = v

class Ipv6_Destination_Extension(object):

    def __init__(self):
        self._mytype = TGEnums.Ipv6ExtensionType.Destination
        self._opt_add_seq = []
        self._whole_options = OrderedDict()
        self.PAD1 = OrderedDict()  # type: list[V6Option_PAD1]
        self.PADN = OrderedDict()  # type: list[V6Option_PADN]
        self.home_address = OrderedDict()  # type: list[V6Option_HomeAddress]

        self._whole_options[TGEnums.Ipv6OptionType.PAD1] = self.PAD1
        self._whole_options[TGEnums.Ipv6OptionType.PADN] = self.PADN
        self._whole_options[TGEnums.Ipv6OptionType.HomeAddress] = self.home_address

        self._auto_pad = attrWithDefault(True)

    @property
    def auto_pad(self):
        return self._auto_pad.current_val

    @auto_pad.setter
    def auto_pad(self, v):
        self._auto_pad.current_val = v

    def add_option(self, option_type):
        option_key = option_type.name +' '+ str(len(self._whole_options[option_type]))
        option_obj = IPv6_Extension_Headers.ext_option_2obj[option_type]()
        self._whole_options[option_type][option_key] = option_obj
        self._opt_add_seq.append(option_obj)
        return option_key

class Ipv6_Authentication_Extension(object):

    def __init__(self):
        self._mytype = TGEnums.Ipv6ExtensionType.Authentication
        self._payload_length = attrWithDefault(2)
        self._security_param_index = attrWithDefault(0)
        self._sequence_number_filed= attrWithDefault(0)

    @property
    def payload_length(self):
        return self._payload_length.current_val

    @payload_length.setter
    def payload_length(self, v):
        self._payload_length.current_val = v

    @property
    def security_param_index(self):
        return self._security_param_index.current_val

    @security_param_index.setter
    def security_param_index(self, v):
        self._security_param_index.current_val = v

    @property
    def sequence_number_filed(self):
        return self._sequence_number_filed.current_val

    @sequence_number_filed.setter
    def sequence_number_filed(self, v):
        self._sequence_number_filed.current_val = v


class IPv6_Extension_Headers(object):

    ext_option_2obj = {
        TGEnums.Ipv6OptionType.PAD1: V6Option_PAD1,
        TGEnums.Ipv6OptionType.PADN: V6Option_PADN,
        TGEnums.Ipv6OptionType.Jumbo: V6Option_Jumbo,
        TGEnums.Ipv6OptionType.RouterAlert: V6Option_RouterAlert,
        TGEnums.Ipv6OptionType.BindingUpdate:V6Option_BindingUpdate,
        TGEnums.Ipv6OptionType.BindingAcknowledgment:V6Option_BindingAck,
        TGEnums.Ipv6OptionType.BindingRequest: V6Option_BindingRequest,
        TGEnums.Ipv6OptionType.HomeAddress: V6Option_HomeAddress,
        TGEnums.Ipv6OptionType.MIpV6UniqueIdSub:V6Option_MIpV6UniqueIdSub,
        TGEnums.Ipv6OptionType.MlpV6AlternativeCoaSub:V6Option_MlpV6AlternativeCoaSub,
    }

    ext_type_2obj = {
        TGEnums.Ipv6ExtensionType.Routing: IPV6_Routing_Extension,
        TGEnums.Ipv6ExtensionType.HopByHop: Ipv6_HopByHop_Extension,
        TGEnums.Ipv6ExtensionType.Fragment:IPV6_Fragment_Extension,
        TGEnums.Ipv6ExtensionType.Destination:Ipv6_Destination_Extension,
        TGEnums.Ipv6ExtensionType.Authentication:Ipv6_Authentication_Extension
    }

    def __init__(self):
        self._ext_add_seq = []
        self._whole_headers = OrderedDict()
        self.routing = OrderedDict() # type: list[IPV6_Routing_Extension]
        self.hopbyhop = OrderedDict() # type: list[Ipv6_HopByHop_Extension]
        self.fragment = OrderedDict()  # type: list[IPV6_Fragment_Extension]
        self.destination = OrderedDict() # type: list[Ipv6_Destination_Extension]
        self.authentication = OrderedDict() # type: list[Ipv6_Authentication_Extension]

        self._whole_headers[TGEnums.Ipv6ExtensionType.Routing] = self.routing
        self._whole_headers[TGEnums.Ipv6ExtensionType.HopByHop] = self.hopbyhop
        self._whole_headers[TGEnums.Ipv6ExtensionType.Fragment] = self.fragment
        self._whole_headers[TGEnums.Ipv6ExtensionType.Destination] = self.destination
        self._whole_headers[TGEnums.Ipv6ExtensionType.Authentication] = self.authentication

    def add(self, extension_type):
        header_key = extension_type.name + ' ' + str(len(self._whole_headers[extension_type]))
        new_obj = IPv6_Extension_Headers.ext_type_2obj[extension_type]()
        self._whole_headers[extension_type][header_key] = new_obj
        self._ext_add_seq.append(new_obj)
        return header_key

    def clear(self):
        self._ext_add_seq = []
        self.routing.clear()
        self.hopbyhop.clear()
        self.fragment.clear()
        self.destination.clear()
        self.authentication.clear()

# x = IPv6_Extension_Headers()
# h1_key3 = x.add(TGEnums.Ipv6ExtensionType.HopByHop)
# r1_key1 = x.add(TGEnums.Ipv6ExtensionType.Routing)
# r1_key2 = x.add(TGEnums.Ipv6ExtensionType.Routing)
# x.clear()
# x.routing[r1_key2].nodes = '123'
# pass
# print('')

# x.routing[r1_key].routing_test = 1
#
# hbh_1 = x.add(TGEnums.Ipv6ExtensionType.HopByHop)
# hbh_1_p1 = x.hopbyhop[hbh_1].add_option(TGEnums.Ipv6OptionType.PADN)
# x.hopbyhop[hbh_1].PADN[hbh_1_p1].value = '00 00 11 33 55'
# hbh_1_j1 = x.hopbyhop[hbh_1].add_option(TGEnums.Ipv6OptionType.Jumbo)
# x.hopbyhop[hbh_1].jumbo[hbh_1_j1].payload = 7
# hbh1_ra1 = x.hopbyhop[hbh_1].add_option(TGEnums.Ipv6OptionType.RouterAlert)
# x.hopbyhop[hbh_1].router_alert[hbh1_ra1].alert_type = TGEnums.RouterAlertType.RSVP
# hbh1_bu_1 = x.hopbyhop[hbh_1].add_option(TGEnums.Ipv6OptionType.BindingUpdate)
# x.hopbyhop[hbh_1].binding_update[hbh1_bu_1].length = 22
# fr1 = x.add(TGEnums.Ipv6ExtensionType.Fragment)
# x.fragment[fr1].id = 11
# dst1 = x.add(TGEnums.Ipv6ExtensionType.Destination)
# home_1 = x.destination[dst1].add_option(TGEnums.Ipv6OptionType.HomeAddress)
# x.destination[dst1].home_address[home_1].address = '9:0:0:0:0:0:0:1'
# auth1 = x.add(TGEnums.Ipv6ExtensionType.Authentication)
# x.authentication[auth1].security_param_index = 22




