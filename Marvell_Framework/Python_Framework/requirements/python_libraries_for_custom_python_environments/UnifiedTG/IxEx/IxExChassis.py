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

from UnifiedTG.Unified.Chassis import Card,resourceGroup,Chassis
from UnifiedTG.Unified.Utils import Converter
from UnifiedTG.Unified.TGEnums import TGEnums
from UnifiedTG.IxEx.IxExEnums import *
import re,inspect,time

class IxExChassis(Chassis):
    def __init__(self,ip):
        super(self.__class__, self).__init__(ip)

    def __getitem__(self, items):
        pass

    def _discover(self):
        if self._driver_obj:
            return
        self._driver_obj = self._parent._connector.chassis_chain[self.ip]
        for cardId in self._driver_obj.cards:
            self._create_card(cardId)

    def _init(self,parent):
        if self._driver_obj:
            return
        self._driver_obj = parent._connector.chassis_chain[self.ip]

    def _card_exists(self,cardId):
        return cardId in self.cards

    def _create_card(self,cardId):
        if not self._card_exists(cardId):
            self._driver_obj.add_card(cardId)
            typeId = self._driver_obj.cards[cardId].type
            self.cards[cardId] = self.creator.create_card(cardId,typeId)
            self.cards[cardId]._init(self)
        return self.cards[cardId]

    def refresh(self):
        self._driver_obj.Refresh()

class IxExCard(Card):

    def __init__(self,id):
        super(IxExCard, self).__init__(id)

    def _init(self,parent):
        self._parent = parent
        self._driver_obj = parent._driver_obj.cards[self.id]
        self._discover()

    def apply(self):
        super(self.__class__, self).apply()
        self._driver_obj.write()

    def _discover(self):
        pass

class IxExCard_XM10_40GE12QSFP(IxExCard):
    def __init__(self,id):
        super(IxExCard, self).__init__(id)

class IxExCard_STX4(IxExCard):
    def __init__(self,id):
        super(IxExCard, self).__init__(id)

class IxExResourceGroup(resourceGroup):

    re_pBaseName = re.compile(r"(.+)(?:_\d+_\d+)$")

    def __init__(self):
        super(self.__class__, self).__init__()

    def _enable_capture_state(self, mode, wr=False):
        if self._enableCapture != mode:
           if self._driver_obj.enable_capture_state(mode,True):
               self._enableCapture = mode

    def _update_supported_modes(self):
        resPorts = len(self._driver_obj.resource_ports)
        if resPorts / 8 >= 1:
            if TGEnums.PORT_PROPERTIES_SPEED.GIGA_400 in self._parent._supported_speeds and \
               TGEnums.PORT_PROPERTIES_SPEED.GIGA_50 in self._parent._supported_speeds:
                self._supported_modes.append(TGEnums.splitSpeed.Eight_50G)
            resPorts -= 8
        if resPorts/4 >= 1:
            if TGEnums.PORT_PROPERTIES_SPEED.GIGA_400 in self._parent._supported_speeds:
                self._supported_modes.append(TGEnums.splitSpeed.Four_100G)
            else:
                if TGEnums.PORT_PROPERTIES_SPEED.GIGA_25 in self._parent._supported_speeds:
                    self._supported_modes.append(TGEnums.splitSpeed.Four_25G)
                if TGEnums.PORT_PROPERTIES_SPEED.GIGA_10 in self._parent._supported_speeds:
                    self._supported_modes.append(TGEnums.splitSpeed.Four_10G)
            resPorts -= 4
        if resPorts/2 >= 1:
            if TGEnums.PORT_PROPERTIES_SPEED.GIGA_400 in self._parent._supported_speeds:
                self._supported_modes.append(TGEnums.splitSpeed.Two_200G)
            else:
                if TGEnums.PORT_PROPERTIES_SPEED.GIGA_50 in self._parent._supported_speeds:
                    self._supported_modes.append(TGEnums.splitSpeed.Two_50G)
            resPorts-=2
        if resPorts == 1:
            if TGEnums.PORT_PROPERTIES_SPEED.GIGA_400 in self._parent._supported_speeds:
                self._supported_modes.append(TGEnums.splitSpeed.One_400G)
            else:
                if TGEnums.PORT_PROPERTIES_SPEED.GIGA_40 in self._parent._supported_speeds:
                    self._supported_modes.append(TGEnums.splitSpeed.One_40G)
                if TGEnums.PORT_PROPERTIES_SPEED.GIGA_100 in self._parent._supported_speeds:
                    self._supported_modes.append(TGEnums.splitSpeed.One_100G)

    def apply(self):
        caller_name = inspect.stack()[1][3]
        need_write = False if caller_name == "apply" else True
        release_list = Converter.ixia_ports_string_2list(self._driver_obj.activePortList)
        result = self._driver_obj.change_mode(self.split_mode,need_write)
        for i in range(1, 10):
            try:
                if len(self._driver_obj.activePortList) > 1:
                    reserve_list = Converter.ixia_ports_string_2list(self._driver_obj.activePortList)
                    break
                else:
                    time.sleep(1)
            except Exception as e:
                time.sleep(1)

        if not result:
            return None
        self._parent._parent.refresh()
        chasIp = self._parent._parent.ip
        pBaseName = chasIp
        if release_list != reserve_list:
            releasePorts = []
            for port in release_list:
                p = port.split(" ")
                cadrId = p[1]
                portId = p[2]
                PortUri = chasIp + "/" + cadrId + "/" + portId
                releasePorts.append(PortUri)
            releaseNames = self._parent._parent._parent._remove_ports(releasePorts)
            # if releaseNames:
            #     matchBaseName = self.re_pBaseName.search(releaseNames[0])
            #     pBaseName = releaseNames[0] if not matchBaseName else matchBaseName.group(1)
        reservePorts = []
        for port in reserve_list:
            p = port.split(" ")
            cadrId = p[1]
            portId = p[2]
            #pName_extetd = '_'+cadrId+"_"+portId
            PortNameUri = chasIp+"/"+cadrId+"/"+portId+':'+chasIp+"/"+cadrId+"/"+portId
            reservePorts.append(PortNameUri)
        return self._parent._parent._parent.reserve_ports(reservePorts,force=True)

class IxExResourceGroup_K400(IxExResourceGroup):
    def __init__(self):
        super(IxExResourceGroup, self).__init__()

    def _update_supported_modes(self):
        self._supported_modes.append(TGEnums.splitSpeed.Four_50G)
        self._supported_modes.append(TGEnums.splitSpeed.Two_100G)
        self._supported_modes.append(TGEnums.splitSpeed.One_200G)
        self._supported_modes.append(TGEnums.splitSpeed.One_400G)

class IxExCard_NOVUS100(IxExCard):

    def __init__(self,id):
        super(IxExCard, self).__init__(id)
        self._supported_speeds = [TGEnums.PORT_PROPERTIES_SPEED.GIGA_10,
                                  TGEnums.PORT_PROPERTIES_SPEED.GIGA_25,
                                  TGEnums.PORT_PROPERTIES_SPEED.GIGA_40,
                                  TGEnums.PORT_PROPERTIES_SPEED.GIGA_50,
                                  TGEnums.PORT_PROPERTIES_SPEED.GIGA_100
                                  ]

    def _discover(self):
        # matchSpeeds = self.reCardSpeed.findall(self._driver_obj.typeName)
        # if matchSpeeds:
        #     for speed in matchSpeeds:
        #         speed = IxExEnums._converter.speed_to_SPEED((int(speed)*1000))
        rgList = self._driver_obj.get_resource_groups()
        for idx,rg in enumerate(rgList):
            idx+=1
            self.resourceGroups[idx] = IxExResourceGroup()
            self.resourceGroups[idx]._parent = self
            self.resourceGroups[idx]._driver_obj = self._driver_obj.resource_groups[str(idx)]
            mode = str(self.resourceGroups[idx]._driver_obj.mode)
            ports_count = str(len(self.resourceGroups[idx]._driver_obj.active_ports))
            self.resourceGroups[idx].split_mode = TGEnums.splitSpeed._value2member_map_[mode+'.'+ports_count]
            self.resourceGroups[idx]._update_supported_modes()

class IxExCard_NOVUS10(IxExCard):
    def __init__(self,id):
        super(self.__class__, self).__init__(id)
        self._supported_speeds = [TGEnums.PORT_PROPERTIES_SPEED.FAST,
                                  TGEnums.PORT_PROPERTIES_SPEED.GIGA,
                                  TGEnums.PORT_PROPERTIES_SPEED.GIGA_2p5,
                                  TGEnums.PORT_PROPERTIES_SPEED.GIGA_5,
                                  TGEnums.PORT_PROPERTIES_SPEED.GIGA_10
        ]

class IxExCard_K400(IxExCard_NOVUS100):
    def __init__(self,id):
        super(self.__class__, self).__init__(id)
        self._supported_speeds = [TGEnums.PORT_PROPERTIES_SPEED.GIGA_50,
                                  TGEnums.PORT_PROPERTIES_SPEED.GIGA_100,
                                  TGEnums.PORT_PROPERTIES_SPEED.GIGA_200,
                                  TGEnums.PORT_PROPERTIES_SPEED.GIGA_400]
    def _discover(self):
        rgList = self._driver_obj.get_resource_groups()
        for idx,rg in enumerate(rgList):
            idx+=1
            self.resourceGroups[idx] = IxExResourceGroup_K400()
            self.resourceGroups[idx]._parent = self
            self.resourceGroups[idx]._driver_obj = self._driver_obj.resource_groups[idx]
            mode = str(self.resourceGroups[idx]._driver_obj.mode)
            ports_count = str(len(self.resourceGroups[idx]._driver_obj.active_ports))
            self.resourceGroups[idx].split_mode = TGEnums.splitSpeed._value2member_map_[mode+'.'+ports_count]
            self.resourceGroups[idx]._update_supported_modes()



class IxExCard_T400(IxExCard_NOVUS100):
    def __init__(self,id):
        super(self.__class__, self).__init__(id)
        self._supported_speeds = [TGEnums.PORT_PROPERTIES_SPEED.GIGA_50,
                                  TGEnums.PORT_PROPERTIES_SPEED.GIGA_100,
                                  TGEnums.PORT_PROPERTIES_SPEED.GIGA_200,
                                  TGEnums.PORT_PROPERTIES_SPEED.GIGA_400]

