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
from CLI_GlobalFunctions.SwitchDev.CLICommands.Executer import GlobalGetterSetter
from CLI_GlobalFunctions.SwitchDev.SpanningTree.AbstractSpanningTreeConfig import AbstractSpanningTreeConfig, obs


class StandardSpanningTreeConfig(AbstractSpanningTreeConfig):
    PROTOCOL_VERSION_IDENTIFIER = "00"

    class STATES(Enum):
        FORWARDING = 'forwarding'
        LEARNING = 'learning'
        LISTENING = 'listening'
        BLOCKING = 'blocking'
        DISABLED = 'disabled'

    class GUARD(Enum):
        ENABLE = "on"
        DISABLE = "off"

    def __init__(self, switchDevInterface, otherDutChannel=False, executer=True):
        """
        :param switchDevInterface: the entity to be configured (e.g, bond, port, bridge)
        :param otherDutChannel: True if there is another DUT; False otherwise
        """
        @obs.on("update")
        def refresh():
            self._stpDetails = self._ipDetailedShow

        super(StandardSpanningTreeConfig, self).__init__(switchDevInterface, otherDutChannel, executer)

    @classmethod
    def getStpDetails(cls):
        """
        Get the STP details using "ip -d -j link show" command
        :return:
        """
        import json5
        stpDetails = json5.loads(GlobalGetterSetter().getter.execute('ip -d -j link show'))
        for interfaceDits in filter(lambda x: x.get('linkinfo', {}).get('info_slave_kind') == 'bridge' or
                                              x.get('linkinfo', {}).get('info_kind') == 'bridge', stpDetails):
            infoDataKey = 'info_slave_data' if 'info_slave_data' in interfaceDits['linkinfo'] else 'info_data'
            cls._ipDetailedShow[interfaceDits['ifname']] = interfaceDits['linkinfo'][infoDataKey]
        obs.trigger("update")
        return cls._ipDetailedShow

    def setBridgePrio(self, value):
        """
        Set priority value to the bridge
        :param value: the new priority value to set on the bridge
        :return: An error message if occurs; None otherwise
        """
        return self._getter.execute(f"brctl setbridgeprio {self} {value}")

    def isRootBridge(self):
        """
        Returns if the bridge is a root bridge
        :return: True if the bridge is a root bridge; False otherwise
        """
        rootPort = self.stpDetails[str(self)]['root_port']
        if rootPort == 0:
            return True
        return False

    def getBlockedPort(self):
        """
        Returns the port blocked port (if there is such); Otherwise, returns None
        :return: Returns the port the blocked port (if there is such); Otherwise, returns None
        """

        if self.isRootBridge():
            return None

        # returns None if there is NO port with blocking state - the return statement will take place only
        # if there the was no break
        for interface in self._enslavedInterfaces:
            if self.stpDetails[interface.name]['state'] == 'blocking':
                return interface

    def getDirectPort(self):
        """
        Returns the port the indirect link (if there is such); Otherwise, returns None
        :return: Returns the port the indirect link (if there is such); Otherwise, returns None
        """

        if self.isRootBridge():
            return None

        # returns None if there is NO port with blocking state - the return statement will take place only
        # if there the was no break
        for interface in self._enslavedInterfaces:
            if self.stpDetails[interface.name]['state'] == 'blocking':
                break
        else:
            return None

        # if there was a break in the previous loop, you will get here
        for interface in self._enslavedInterfaces:
            if self.stpDetails[interface.name]['bridge_id'] == \
                    self.stpDetails[interface.name]['root_id'] and \
                    self.stpDetails[interface.name]['state'] == 'forwarding':
                return interface

    def getIndirectPort(self):
        """
        Returns the port the direct link (if there is such); Otherwise, returns None
        :return: Returns the port the direct link (if there is such); Otherwise, returns None
        """

        if self.isRootBridge():
            return None

        # returns None if there is a port with blocking state
        for interface in self._enslavedInterfaces:
            if self.stpDetails[interface.name]['state'] == 'blocking':
                return None

        for interface in self._enslavedInterfaces:
            if self.stpDetails[interface.name]['bridge_id'] == \
                    self.stpDetails[interface.name]['root_id'] and \
                    self.stpDetails[interface.name]['state'] == 'forwarding':
                return interface

    def setPortPriority(self, interface, prio: int):
        """
        Set priority value value to an interface
        :param interface: the interface to set the new port priority value on
        :param prio: the port priority value to set on an interface
        :return: An error message if occurs; None otherwise
        """
        return self._getter.execute(f"brctl setportprio {self} {interface} {prio}")

    def setPortCost(self, interface, cost: int):
        """
        Set cost value to an interface
        :param interface: the interface to set the new cost value on
        :param cost: the cost value to set on an interface
        :return: An error message if occurs; None otherwise
        """
        return self._getter.execute(f"brctl setpathcost {self} {interface} {cost}")

    def setBdpuGuard(self, interface, state: GUARD):
        """
        Set BDPU guard on/off to an enslaved interface
        :param interface: the interface to set the BDPU guard state on
        :param state: the BDPU guard state to set on an interface (enable/disable)
        :return: An error message if occurs; None otherwise
        """
        return self._getter.execute(f"bridge link set dev {interface} guard {state.value}")

    def setForwardDelay(self, time):
        """
        Set forward delay time
        :param time: the new forward delay time
        :return: An error message if occurs; None otherwise
        """
        return self._getter.execute(f"brctl setfd {self} {time}")

    def setMaxAge(self, time):
        """
        Set max age time
        :param time: the new max age time
        :return: An error message if occurs; None otherwise
        """
        return self._getter.execute(f"brctl setmaxage {self} {time}")

    def setHelloTime(self, time):
        """
        Set hello time
        :param time: the new hello time
        :return: An error message if occurs; None otherwise
        """
        return self._getter.execute(f"brctl sethello {self} {time}")

    def isRootPort(self, interface):
        return self.stpDetails[interface.name]['bridge_id'] == \
               self.stpDetails[interface.name]['root_id'] and \
               self.stpDetails[interface.name]['state'] == 'forwarding' and not self.isRootBridge()

    def getPortId(self, interface):
        try:
            return int((self.stpDetails[interface.name]['id']), 16)
        except:
            return int(str(self.stpDetails[interface]['id']), 16)
