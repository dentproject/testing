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
from .VlanEnumTypes import *


class vlanInfo(object):
    def __init__(self):
        self.stgId = 0
        self.vrfId = 0
        self.ucastLocalSwitchingEn = False
        self.fdbLookupKeyMode = CPSS_DXCH_BRG_FDB_LOOKUP_KEY_MODE_ENT.CPSS_DXCH_BRG_FDB_LOOKUP_KEY_MODE_FID_E
        self.ipv4IpmBrgEn = False
        self.unregIpv4BcastCmd = CPSS_PACKET_CMD_ENT.CPSS_PACKET_CMD_FORWARD_E
        self.ipv6UcastRouteEn = False
        self.unregNonIpv4BcastCmd = CPSS_PACKET_CMD_ENT.CPSS_PACKET_CMD_FORWARD_E
        self.unregIpmEVidx = 4095
        self.ipv6McastRouteEn = False
        self.unregNonIpMcastCmd = CPSS_PACKET_CMD_ENT.CPSS_PACKET_CMD_FORWARD_E
        self.mruIdx = 0
        self.bcastUdpTrapMirrEn = False
        self.mirrToRxAnalyzerEn = False
        self.ipv6IcmpToCpuEn = False
        self.ipv4UcastRouteEn = False
        self.ipv4McBcMirrToAnalyzerIndex = 0
        self.floodVidxMode = CPSS_DXCH_BRG_VLAN_FLOOD_VIDX_MODE_ENT.CPSS_DXCH_BRG_VLAN_FLOOD_VIDX_MODE_UNREG_MC_E
        self.portIsolationMode = CPSS_DXCH_BRG_VLAN_PORT_ISOLATION_CMD_ENT.CPSS_DXCH_BRG_VLAN_PORT_ISOLATION_DISABLE_CMD_E
        self.unregIpmEVidxMode = CPSS_DXCH_BRG_VLAN_UNREG_IPM_EVIDX_MODE_ENT.CPSS_DXCH_BRG_VLAN_UNREG_IPM_EVIDX_MODE_BOTH_E
        self.ipv6IpmBrgMode = CPSS_BRG_IPM_MODE_ENT.CPSS_BRG_IPM_SGV_E
        self.ipv4McastRouteEn = False
        self.ipv6McMirrToAnalyzerIndex = 0
        self.floodVidx = 4095
        self.ipv4IpmBrgMode = CPSS_BRG_IPM_MODE_ENT.CPSS_BRG_IPM_SGV_E
        self.ipv6IpmBrgEn = False
        self.unkUcastCmd = CPSS_PACKET_CMD_ENT.CPSS_PACKET_CMD_FORWARD_E
        self.mirrToTxAnalyzerEn = False
        self.ipv6McMirrToAnalyzerEn = False
        self.ipv4McBcMirrToAnalyzerEn = False
        self.unregIpv6McastCmd = CPSS_PACKET_CMD_ENT.CPSS_PACKET_CMD_FORWARD_E
        self.ipv6SiteIdMode = CPSS_IP_SITE_ID_ENT.CPSS_IP_SITE_ID_INTERNAL_E
        self.unknownMacSaCmd = CPSS_PACKET_CMD_ENT.CPSS_PACKET_CMD_FORWARD_E
        self.unkSrcAddrSecBreach = False
        self.ipCtrlToCpuEn = CPSS_DXCH_BRG_IP_CTRL_TYPE_ENT.CPSS_DXCH_BRG_IP_CTRL_NONE_E
        self.fidValue = 1
        self.mirrToTxAnalyzerIndex = 0
        self.mirrToRxAnalyzerIndex = 0
        self.fcoeForwardingEn = False
        self.naMsgToCpuEn = True
        self.mcastLocalSwitchingEn = False
        self.ipv4IgmpToCpuEn = False
        self.unregIpv4McastCmd = CPSS_PACKET_CMD_ENT.CPSS_PACKET_CMD_FORWARD_E
        self.autoLearnDisable = True

    def tostring(self):
        print(vars(self))
