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

from CLI_GlobalFunctions.SwitchDev.Bridge.BridgeConfig import BridgeConfig
from CLI_GlobalFunctions.SwitchDev.CLICommands.Executer import GlobalGetterSetter
from PyInfra.BaseTest_SV.SV_Enums.SwitchDevInterface import SwitchDevDutInterface


class Bridge1QConfig(BridgeConfig):
    MAX_VLANS = 4094

    __vlanConfiguration = {}  # type: dict[str, list[str]]
    __version = None

    @classmethod
    def addInterfaceToVlan(cls, dev, vid, *args, otherDut=False):
        if otherDut:
            executer = GlobalGetterSetter().getterOtherDut
        else:
            executer = GlobalGetterSetter().getter
        return executer.bridge_vlan_add(vid=vid, dev=dev, *args)

    @classmethod
    def removeInterfaceFromVlan(cls, dev, vid, *args, otherDut=False):
        if otherDut:
            executer = GlobalGetterSetter().getterOtherDut
        else:
            executer = GlobalGetterSetter().getter
        return executer.bridge_vlan_del(vid=vid, dev=dev, *args)

    @classmethod
    def isTagged(cls, dev, vid):
        try:
            return cls.__vlanConfiguration.get(dev.name, {}).get('vlans', {}).get(vid, '') == 'tagged'
        except AttributeError:
            return cls.interfaceVlanSettings()[dev]['vlans'][vid] == 'tagged'

    @classmethod
    def getPVID(cls, dev):
        try:
            pvid = cls.interfaceVlanSettings()[dev.name]['pvid']
        except AttributeError:
            pvid = cls.interfaceVlanSettings()[dev]['pvid']

        return pvid

    @classmethod
    def getVIDs(cls, dev):
        try:
            vids = cls.interfaceVlanSettings()[dev.name]['vlans']
        except AttributeError:
            vids = cls.interfaceVlanSettings()[dev]['vlans']

        return vids

    @classmethod
    def interfaceVlanSettings(cls):
        if not cls.__vlanConfiguration:
            cls.getVlanSettings()
        return cls.__vlanConfiguration

    def __init__(self, switchDevInterface=SwitchDevDutInterface('br0'), otherDutChannel=False, executer=True):
        super(Bridge1QConfig, self).__init__(switchDevInterface, otherDutChannel, executer)

    @classmethod
    def getVlanSettings(cls):
        import json5
        vlanTable = json5.loads(GlobalGetterSetter().getter.bridge('-j', 'vlan', 'show'))
        hasInFlags = lambda x, y: 'flags' in x and not y not in x['flags']
        vlanTable = {item['ifname']: item['vlans'] for item in vlanTable}
        for k, v in vlanTable.items():
            pvid = [str(vlans['vlan']) for vlans in v if (hasInFlags(vlans, 'PVID'))]
            cls.__vlanConfiguration[k] = {
                **{'vlans': {
                    str(vlans['vlan']): 'untagged' if hasInFlags(vlans, 'Egress Untagged') else 'tagged' for vlans
                    in v}},
                **{'pvid': pvid[0] if pvid else None}
            }

    def createL2Entity(self, *args, **kwargs):
        return super(Bridge1QConfig, self).createL2Entity(*args, **{'vlan_filtering':1, **kwargs} )

    def setDefaultPVID(self, v):
        return self._setter.ip_link_set(dev=self._switchdevInterface.name, type=self._type, vlan_default_pvid=v)

    def addBridgeToVlan(self, vid, *args):
        return self._getter.execute(f"bridge vlan add dev {self} vid {vid} {' '.join(list(filter(None, map(str, args))))} self")

    def removeBridgeFromVlan(self, vid, *args):
        return self._setter.bridge_vlan_del(vid=vid, dev=self, *args)

    def isBridgeVIDUntagged(self, vid):
        return self.__class__.isTagged(self._switchdevInterface.name, vid)

    def getBridgePVID(self):
        return self.__class__.getPVID(self._switchdevInterface)

    def getBridgeVIDs(self):
        return self.__class__.getVIDs(self._switchdevInterface.name)
