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

import logging,sys
import binascii
import xenavalkyrie
from enum import Enum
from string import Template

# from pypacker.layer12.ethernet import Ethernet, Dot1Q
# from pypacker.layer3.ip6 import IP6
# from pypacker.layer3.ip import IP
# from pypacker.layer4.tcp import TCP

from UnifiedTG.Unified.Utils import attrWithDefault
from trafficgenerator.tgn_utils import ApiType
from xenavalkyrie.xena_app import init_xena


class XenaParamsTypeEnum(Enum):
    indexNoParam = 0
    indexOneParam = 1
    indexTwoParams = 2
    indexThreeParams = 3
    indexSixParams = 6


class xenaCommandParams():
    regular_cmd_params= {XenaParamsTypeEnum.indexNoParam:Template(''),
                  XenaParamsTypeEnum.indexOneParam:Template(' $param1'),
                  XenaParamsTypeEnum.indexTwoParams:Template(' $param1 $param2'),
                  XenaParamsTypeEnum.indexSixParams: Template(' $param1 $param2 $param3 $param4 $param5 $param6')
                  }
    subindex_cmd_params = {XenaParamsTypeEnum.indexNoParam:Template(' [$ix]'),
                           XenaParamsTypeEnum.indexOneParam:Template(' [$ix] $param1'),
                           XenaParamsTypeEnum.indexTwoParams:Template(' [$ix] $param1 $param2'),
                           XenaParamsTypeEnum.indexThreeParams:Template(' [$ix] $param1 $param2 $param3'),
                           XenaParamsTypeEnum.indexSixParams: Template(' [$ix] $param1 $param2 $param3 $param4 $param5 $param6' )
                          }
    @staticmethod
    def build(paramsList=None,ix=None):
        cmd_type_id = 0
        cmd_args = {}
        cmd_dict = xenaCommandParams.regular_cmd_params
        if paramsList:
            cmd_type_id = len(paramsList)
            for i, p in enumerate(paramsList):
                cmd_args.update({'param'+str(i+1): p})
        if ix is not None:
            cmd_dict = xenaCommandParams.subindex_cmd_params
            cmd_args.update({'ix': ix})
        cmd_type = XenaParamsTypeEnum._value2member_map_[cmd_type_id]
        res = cmd_dict[cmd_type].substitute(**cmd_args)
        return res


class xenaUpdater():
    def _rsetattr(self, obj, attr, val):
        params = ''
        if isinstance(val, (list,)):
            for v in val:
                params = params+' '+v
        else:
            params = val
        obj.set_attributes(**{attr:params})
    #
    def _rgetattr(self, obj, attr):
        return obj.get_attribute(attr)
    #
    def _update_field(self, api_field=None, driver_field=None, value=None, exception_info="", always_write=False):
        res = True
        driver_obj = self._port_driver_obj if hasattr(self,'_port_driver_obj') else self._stream_driver_obj
        try:
            val = None
            # case 1 - field is hidden from api
            if api_field is None:
                if type(value) == attrWithDefault:
                    val = value.current_val
                    value._driver_field = driver_field
                else:
                    val = value
                # api_field._previous_val = api_field._current_val
                self._rsetattr(driver_obj, driver_field, val)
                if self._debug_prints: print ("updating " + driver_field)
            else:
                api_field._driver_field = driver_field
                # case 2 - value was never updated in driver
                if api_field._was_written_to_driver == False:
                    if value is None:
                        api_field._previous_val = api_field._current_val
                        val = api_field._current_val
                        if isinstance(val, Enum):
                            val = val.value
                        self._rsetattr(driver_obj, driver_field, val)
                        if self._debug_prints: print ("updating " + driver_field)
                        if not always_write: api_field._was_written_to_driver = True
                    else:
                        if type(value) == attrWithDefault:
                            val = value.current_val
                        else:
                            val = value
                        api_field._previous_val = api_field._current_val
                        self._rsetattr(driver_obj, driver_field, val)
                        if self._debug_prints: print ("updating " + driver_field)
                        if not always_write: api_field._was_written_to_driver = True
                # case 3 - value is different than previous
                elif api_field._current_val != api_field._previous_val or always_write:
                    if value is None:
                        api_field._previous_val = api_field._current_val
                        if isinstance(api_field._current_val, Enum):
                            val = api_field._current_val.value
                        else:
                            val = api_field._current_val
                        self._rsetattr(driver_obj, driver_field, val)
                        if self._debug_prints: print ("updating " + driver_field)
                        if not always_write: api_field._was_written_to_driver = True
                    else:
                        if type(value) == attrWithDefault:
                            val = value.current_val
                        else:
                            val = value
                        self._rsetattr(driver_obj, driver_field, val)
                        if self._debug_prints: print ("updating " + driver_field)
                        if not always_write: api_field._was_written_to_driver = True
                else:
                    if self._debug_prints: print ("no update need for " + driver_field)
                    res = False
                return res
        except Exception as e:
            raise Exception("Error in update field.\nField name = " + driver_field +
                            "\nValue to set: " + str(val) +
                            "\n" + exception_info +
                            "\n" + str(self) +
                            "\nDriver Exeption:\n" + str(e))
    #
    def _get_field(self, name):
        driver_obj = self._port_driver_obj if hasattr(self, '_port_driver_obj') else self._stream_driver_obj
        x = self._rgetattr(driver_obj, name)
        return x

    def _get_field_hw_value(self, field):
        return self._get_field(field._driver_field)





#with_metaclass(ConnectorMeta, object)
class xenaConnector():

    def __init__(self,_parent):
        self._app_driver = None
        self._parent = _parent

    def connect(self, login):
        if not self._app_driver:
            api = ApiType.socket
            loger = self._parent._logger
            owner = self._parent._login_name
            self._app_driver = init_xena(api, loger, owner)

    @property
    def connected(self):
        return True if self._app_driver else False
        #TODO

    @property
    def session(self):
        return self._app_driver.session

    def add(self,chassis_ip):
        self.session.add_chassis(chassis_ip)



# eth1 = Ethernet()
# ip1 = IP()
# ip1.dst_s = '1.1.1.1'
# ip1.src_s = '2.2.2.2'
#
# eth1.src_s = '00:11:22:33:44:55'
# eth1.dst_s = '66:77:88:99:AA:BB'
#
#
#
# pkt = eth1+ip1
# bin_headers = '0x' + binascii.hexlify(pkt.bin()).decode('utf-8')
# res = binascii.hexlify(pkt.bin()).decode('utf-8')
# bin_headers = pkt.hexdump()
#
#
# chassis = '10.4.48.191'
# port1 = chassis + '/' + '0/0'
# port0 = chassis + '/' + '0/1'
# owner = 'OlegK'

# def connect():
#     """ Create Xena manager object and connect to chassis. """
#
#     global xm
#
#     # Xena manager requires standard logger. To log all low level CLI commands set DEBUG level.
#     logger = logging.getLogger('log')
#     logger.setLevel(logging.DEBUG)
#     logger.addHandler(logging.StreamHandler(sys.stdout))
#
#     # Create XenaApp object and connect to chassis.
#     #xm = init_xena(api, logger, owner)
#     xm.session.add_chassis(chassis)
#
#     global ports
#     ports = xm.session.reserve_ports([port0, port1], True)
#
#     p1_s0 = ports[port1].add_stream('new stream')
#     # Set headers - all fields can be set with the constructor or by direct access after creation.
#     eth = Ethernet(src_s='22:22:22:22:22:22')
#     eth.dst_s = '11:11:11:11:11:11'
#     vlan = Dot1Q(vid=17)
#     eth.vlan.append(vlan)
#     # In order to add header simply concatenate it.
#     ip6 = IP6()
#     tcp = TCP()
#     headers = eth + ip6 + tcp
#     p1_s0.set_packet_headers(headers)



#connect()
#pass