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

from CLI_GlobalFunctions.SwitchDev.CLICommands.EntityConfig import L2EntityConfig
from CLI_GlobalFunctions.SwitchDev.CLICommands.Executer import GlobalGetterSetter
from PyInfra.BaseTest_SV.SV_Enums.SwitchDevInterface import SwitchDevDutInterface


class BridgeConfig(L2EntityConfig):

    def __init__(self, switchDevInterface, otherDutChannel=False, executer=True):
        """
        :param switchDevInterface: the entity to be configured (e.g, bond, port, bridge)
        :param otherDutChannel: True if there is another DUT; False otherwise
        """
        super(BridgeConfig, self).__init__(switchDevInterface, "bridge", otherDutChannel, executer)
        self._aging_time = None
        self._vlan_filtering = None
        self._learning = None  # type: str
        self._flood = None  # type: str
        self._vlan = None
        self._ipAdrr = None  # type: str

    @classmethod
    def getPortNumOfEntries(cls, dev, *args, timeout=10):
        """
        returns the number of MAC entries of a port/interface
        :param dev: the port/interface to get it's num of entries
        :type dev: SwitchDevDutInterface
        :param args: more filters on the MAC entries
        :type args: list[str]
        :return: the number of MAC entries of a port/interface
        """
        return GlobalGetterSetter().getter.bridge_fdb_show('brport', dev.name, *list('| grep  %s' % x for x in args),
                                                           '| wc -l', timeout=timeout)

    @property
    def aging_time(self):
        """
        :return: the aging time of bridge entity
        """
        return self._aging_time

    @aging_time.setter
    def aging_time(self, v):
        self._setter.ip_link_set(dev=self.switchdevInterface.name, type=self._type, ageing_time=v)
        self._aging_time = v

    @property
    def vlan_filtering(self):
        return self._vlan_filtering

    @vlan_filtering.setter
    def vlan_filtering(self, v):
        self._setter.ip_link_set(dev=self.switchdevInterface.name, type=self._type, vlan_filtering=v)
        self._vlan_filtering = v

    @property
    def learning(self):
        return self._learning

    def setLearning(self, v):
        for port in self.enslavedInterfaces:
            ret = self._setter.bridge_link_set(dev=port.name, learning=v)
            if not ret:
                self._learning = v
            else:
                return ret

    @property
    def flood(self):
        return self._flood

    def setFloodAll(self, v):
        for port in self.enslavedInterfaces:
            ret = self._setter.bridge_link_set(dev=port.name, flood=v)
            if not ret:
                self._flood = v
            else:
                return ret

    def setFlood(self, dev, v):
        return self._setter.bridge_link_set(dev=dev, flood=v)

    def setBridgeEntry(self, entry, interface, vlan):
        if int(vlan) != 1:
            ret = self._setter.bridge_fdb('add', entry, 'dev', interface, 'static', 'master', 'vlan', vlan)
        else:
            ret = self._setter.bridge_fdb('add', entry, 'dev', interface, 'static', 'master')
        return ret

    def fillBridgeStaticEntries(self, board_type_index='' , start_index='', dev=''):
        start_index = start_index
        index = board_type_index + start_index
        ret = self._getter.execAsFile(f"""  mac='00:00:00:00'
                                            for ((num={start_index}; num<={index}; num++)); do
                                            printf -v sfx ':%02X:%02X' $((num>>8)) $((num&255))
                                            bridge fdb add "${{mac}}${{sfx}}" dev {dev} static master
                                            done""")
        return ret

    def remBridgeEntry(self, entry, interface, vlan):
        if int(vlan) != 1:
            ret = self._setter.bridge_fdb('del', entry, 'dev', interface, 'static', 'master', 'vlan', vlan)
        else:
            ret = self._setter.bridge_fdb('del', entry, 'dev', interface, 'static', 'master')
        return ret

    def addInterfaceToVlan(self, dev, vid, *args):
        ret = self._setter.bridge_vlan_add(vid=vid, dev=dev, *args)
        if not ret:
            self._vlan = vid
        else:
            return ret

    def remInterfaceFromVlan(self, dev, vid, *args):
        ret = self._setter.bridge_vlan_del(vid=vid, dev=dev, *args)
        if not ret:
            self._vlan = None
        else:
            return ret

    def getPortEntries(self, interface):
        return self._getter.bridge_fdb_show(brport=interface)  # '|', 'grep', 'extern_learn')

    def getBridgeEntries(self, bridge):
        return self._getter.bridge_fdb_show(bridge)

    def getBridgeNumOfEntries(self, bridge):
        #return self._getter.brctl_showmacs(bridge, ' | ', 'wc', '-l')
        return self._getter.bridge_fdb_show('br', bridge, ' | ', 'grep', "'extern_learn.*offload'", ' | ', 'wc', '-l')

    def getStaticBridgeNumOfEntries(self, bridge):
        #return self._getter.brctl_showmacs(bridge, ' | ', 'wc', '-l')
        return self._getter.bridge_fdb_show('br', bridge, ' | ', 'grep', "'offload.*static'", ' | ', 'wc', '-l')

    def setBridgeSTP(self, bridge, mode):
        return self._setter.brctl_stp(bridge, mode)

    def setIP(self, addr, mask):
        ret = self._setter.ip_addr_add(f"{addr}/{mask}", 'dev', self.switchdevInterface.name)
        if not ret:
            self._ipAdrr = addr

    def setIPVlanDev(self, addr, mask, vlan):
        return self._setter.ip_addr_add(f"{addr}/{mask}", 'dev', f'{self.switchdevInterface.name}.{vlan}')

    def delIP(self, addr, mask):
        return self._setter.ip_addr_del(f"{addr}/{mask}", 'dev', self.switchdevInterface.name)

    def addVlanDev(self, bridge, vlan):
        return self._setter.ip_link_add_link(bridge, 'name', f'{bridge}.{vlan}', 'type', 'vlan', 'id', vlan)

    def addBridgeToVlan(self, bridge, vlan):
        return self._setter.bridge_vlan_add_dev(bridge, 'vid', vlan, 'self')

    def changeSelfMac(self, mac):
        return self._getter.execute(f'ifconfig {self} hw ether {mac}')

    @classmethod
    def setMaxSTPInstances(cls, max_instances):
        for i in range(max_instances):
            ret = GlobalGetterSetter().getter.ip_link_add(f'br{i}', 'type', 'bridge', 'stp_state', '1')
            if ret:
                return ret

    @classmethod
    def getMaxSTPInstances(cls):
        return GlobalGetterSetter().getter.ifconfig('-a', ' | ', 'grep', 'br.*', ' | ', 'wc', '-l')

    @classmethod
    def removeMaxSTPInstances(cls, max_instances):
        for i in range(max_instances):
            ret = GlobalGetterSetter().getter.ip_link_del(f'br{i}', 'type', 'bridge')
            if ret:
                return ret

    def maxVLANSFromFile(self, index1='', index2='', dev1='', dev2=''):

        ret = self._getter.execAsFile(f"""for ((i=1; i<={index1}; i++)); do bridge vlan add dev {dev1} vid $i; done
                                          for ((j=1; j<={index2}; j++));  do bridge vlan add dev {dev2} vid $j; done""")
        return ret
