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

from __future__ import print_function
from __future__ import absolute_import

from builtins import object
import os
import sys
import json
from abc import ABCMeta, abstractmethod

from Executer import *
from .VlanEntry import vlanInfo
from future.utils import with_metaclass

class ISerialize(with_metaclass(ABCMeta, object)):
    def __init__(self):
        raise NotImplementedError('ERROR: Cant instantiate abstract class')

    @abstractmethod
    def Serialize(self):
        pass

    @abstractmethod
    def Deserialize(self, response):
        pass


#class PortVlanMember:
#    def __init__(self, portId, tag = CPSS_DXCH_BRG_VLAN_PORT_TAG_CMD_ENT.CPSS_DXCH_BRG_VLAN_PORT_UNTAGGED_CMD_E):
#        self.portId = portId
#        self.portTaggingCmd = tag;

class VlanEntry(ISerialize):

    def __init__(self, devId, vlanId):
        
        self.devId = devId
        self.vlanId = vlanId

        self.portsMembers = []
        self.portsTagging = []
        # self.portVlanMembers = []
        #self.portsTaggingCmds = []

        self.isValid = True
        self.info = vlanInfo()

    def Serialize(self):

        sendCmd = {}
        sendCmd['funcname'] = 'cpssDxChBrgVlanEntryRead'
        sendCmd['params'] = [["IN", "GT_U8", "devNum", self.devId],
                             ["IN", "GT_U16", "vlanId", self.vlanId],
                             ["OUT", "CPSS_PORTS_BMP_STC", "portsMembers"],
                             ["OUT", "CPSS_PORTS_BMP_STC", "portsTagging"],
                             ["OUT", "CPSS_DXCH_BRG_VLAN_INFO_STC", "vlanInfo"],
                             ["OUT", "GT_BOOL", "isValid"],
                             ["OUT", "CPSS_DXCH_BRG_VLAN_PORTS_TAG_CMD_STC", "portsTaggingCmd"]
                            ]
        request = json.dumps(sendCmd, sort_keys = True, indent=4)
        print(request)

        return request

    def Deserialize(self, response):
        obj = json.JSONDecoder().decode(response)
        if isinstance(obj['values'], dict):
            dictResult = obj['values']
            self.isValid = dictResult['isValid']

            if isinstance(dictResult['portsMembers'], dict):
                for key, value in dictResult['portsMembers'].items():
                    if isinstance(value, dict):
                        for k, v in value.items(): #ports
                            self.portsMembers.append(v)

            if isinstance(dictResult['portsTagging'], dict):
                for key, value in dictResult['portsTagging'].items():
                    if isinstance(value, dict):
                        for k, v in value.items(): #ports
                            self.portsTagging.append(v)

            #for key, value in obj.values['vlanInfo']:
            if isinstance(dictResult['vlanInfo'], dict):
                dictVlanEntry = dictResult['vlanInfo']

            self.info.stgId = dictVlanEntry['stgId']
            self.info.vrfId = dictVlanEntry['vrfId']
            self.info.ucastLocalSwitchingEn = dictVlanEntry['ucastLocalSwitchingEn']
            self.info.fdbLookupKeyMode._value2member_map_[dictVlanEntry['fdbLookupKeyMode']]
            self.info.ipv4IpmBrgEn = dictVlanEntry['ipv4IpmBrgEn']
            self.info.unregIpv4BcastCmd._value2member_map_[dictVlanEntry['unregIpv4BcastCmd']]
            self.info.ipv6UcastRouteEn = dictVlanEntry['ipv6UcastRouteEn']
            self.info.unregNonIpv4BcastCmd._value2member_map_[dictVlanEntry['unregNonIpv4BcastCmd']]
            self.info.unregIpmEVidx = dictVlanEntry['unregIpmEVidx']
            self.info.ipv6McastRouteEn = dictVlanEntry['ipv6McastRouteEn']
            self.info.unregNonIpMcastCmd._value2member_map_[dictVlanEntry['unregNonIpMcastCmd']]
            self.info.mruIdx = dictVlanEntry['mruIdx']
            self.info.bcastUdpTrapMirrEn = dictVlanEntry['bcastUdpTrapMirrEn']
            self.info.mirrToRxAnalyzerEn = dictVlanEntry['mirrToRxAnalyzerEn']
            self.info.ipv6IcmpToCpuEn = dictVlanEntry['ipv6IcmpToCpuEn']
            self.info.ipv4UcastRouteEn = dictVlanEntry['ipv4UcastRouteEn']
            self.info.ipv4McBcMirrToAnalyzerIndex = dictVlanEntry['ipv4McBcMirrToAnalyzerIndex']
            self.info.floodVidxMode._value2member_map_[dictVlanEntry['floodVidxMode']]
            self.info.portIsolationMode._value2member_map_[dictVlanEntry['portIsolationMode']]
            self.info.unregIpmEVidxMode._value2member_map_[dictVlanEntry['unregIpmEVidxMode']]
            self.info.ipv6IpmBrgMode._value2member_map_[dictVlanEntry['ipv6IpmBrgMode']]
            self.info.ipv4McastRouteEn = dictVlanEntry['ipv4UcastRouteEn']
            self.info.ipv6McMirrToAnalyzerIndex = dictVlanEntry['ipv6McMirrToAnalyzerIndex']
            self.info.floodVidx = dictVlanEntry['floodVidx']
            self.info.ipv4IpmBrgMode._value2member_map_[dictVlanEntry['ipv4IpmBrgMode']]
            self.info.ipv6IpmBrgEn = dictVlanEntry['ipv6IpmBrgEn']
            self.info.unkUcastCmd._value2member_map_[dictVlanEntry['unkUcastCmd']]
            self.info.mirrToTxAnalyzerEn = dictVlanEntry['mirrToTxAnalyzerEn']
            self.info.ipv6McMirrToAnalyzerEn = dictVlanEntry['ipv6McMirrToAnalyzerEn']
            self.info.ipv4McBcMirrToAnalyzerEn = dictVlanEntry['ipv4McBcMirrToAnalyzerEn']
            self.info.unregIpv6McastCmd._value2member_map_[dictVlanEntry['unregIpv6McastCmd']]
            self.info.ipv6SiteIdMode._value2member_map_[dictVlanEntry['ipv6SiteIdMode']]
            self.info.unknownMacSaCmd._value2member_map_[dictVlanEntry['unknownMacSaCmd']]
            self.info.unkSrcAddrSecBreach = dictVlanEntry['unkSrcAddrSecBreach']
            self.info.ipCtrlToCpuEn._value2member_map_[dictVlanEntry['ipCtrlToCpuEn']]
            self.info.fidValue = dictVlanEntry['fidValue']
            self.info.mirrToTxAnalyzerIndex = dictVlanEntry['mirrToTxAnalyzerIndex']
            self.info.mirrToRxAnalyzerIndex = dictVlanEntry['mirrToRxAnalyzerIndex']
            self.info.fcoeForwardingEn = dictVlanEntry['fcoeForwardingEn']
            self.info.naMsgToCpuEn = dictVlanEntry['naMsgToCpuEn']
            self.info.mcastLocalSwitchingEn = dictVlanEntry['mcastLocalSwitchingEn']
            self.info.ipv4IgmpToCpuEn = dictVlanEntry['ipv4IgmpToCpuEn']
            self.info.unregIpv4McastCmd._value2member_map_[dictVlanEntry['unregIpv4McastCmd']]
            self.info.autoLearnDisable = dictVlanEntry['autoLearnDisable']

        return self


class VlanTable(object):
    def __init__(self):
        self.devId = 0
        self.entries = [VlanEntry(self.devId, 0)]
        self.entries.pop(0)

    def refresh(self, alias):
        isValidPtr = False
        count = 0
        while (count < 1 and isValidPtr == False):
            vt = VlanEntry(self.devId, count)
            vt = Executer.execute(alias, vt)
            self.entries.append(vt)
            count = count + 1



