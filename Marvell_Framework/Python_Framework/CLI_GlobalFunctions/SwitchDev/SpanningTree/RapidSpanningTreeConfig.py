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
from CLI_GlobalFunctions.SwitchDev.SpanningTree.AbstractSpanningTreeConfig import AbstractSpanningTreeConfig, STP_MODE, \
    obs, STP_STATE


class RapidSpanningTreeConfig(AbstractSpanningTreeConfig):
    __ipDetailedShow = None

    PROTOCOL_VERSION_IDENTIFIER = "02"

    class STATES(Enum):
        FORWARDING = 'forwarding'
        LEARNING = 'learning'
        LISTENING = 'listening'
        BLOCKING = 'discarding'
        DISABLED = 'discarding'

    class GUARD(Enum):
        ENABLE = "yes"
        DISABLE = "no"

    def __init__(self, switchDevInterface, otherDutChannel=False, executer=True):
        """
        :param switchDevInterface: the entity to be configured (e.g, bond, port, bridge)
        :param otherDutChannel: True if there is another DUT; False otherwise
        """

        @obs.on("update")
        def refresh():
            import json5
            portDetails = json5.loads(self._getter.execute(f"mstpctl --format json showportdetail {self}"))
            bridgeDetails = json5.loads(self._getter.execute(f"mstpctl --format json showbridge {self}"))
            for entry in portDetails + bridgeDetails:
                if 'port' in entry:
                    self._stpDetails[entry.get('port')] = dict(entry)
                else:
                    self._stpDetails[entry.get('bridge')] = dict(entry)

        super(RapidSpanningTreeConfig, self).__init__(switchDevInterface, otherDutChannel, executer)

    def createL2Entity(self, *args, **kwargs):
        self._getter.execute(" sed -i \"/^[#]*MANAGE_MSTPD=/ cMANAGE_MSTPD='y'\" /etc/bridge-stp.conf && mstpd")
        super(RapidSpanningTreeConfig, self).createL2Entity(*args, **kwargs)
        self._getter.execute(f"mstpctl addbridge {self}")

    @classmethod
    def getStpDetails(cls):
        """
        Get the STP details using "mstpctl showall json" command
        :return:
        """
        obs.trigger("update")
        return cls._ipDetailedShow

    def setStpState(self, state: STP_STATE):
        ret = super(RapidSpanningTreeConfig, self).setStpState(state)
        if ret:
            return ret
        if state == STP_STATE.ENABLE:
            return self.setStpMode(STP_MODE.RSTP)

    def setBridgePrio(self, value):
        """
        Set priority value to the bridge
        :param value: the new priority value to set on the bridge
        :return: An error message if occurs; None otherwise
        """
        return self._getter.execute(f"mstpctl settreeprio {self} 0 {value}")

    def isRootBridge(self):
        """
        Returns if the bridge is a root bridge
        :return: True if the bridge is a root bridge; False otherwise
        """
        if not self.stpDetails[str(self)].get('root-port'):
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
            if self._stpDetails[interface.name]['state'] == 'discarding':
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
            if self.stpDetails[interface.name]['state'] == 'discarding' and \
                    self.stpDetails[interface.name]['role'] == 'Alternate':
                break
        else:
            return None

        # if there was a break in the previous loop, you will get here
        for interface in self._enslavedInterfaces:
            if self.stpDetails[interface.name]['role'] == 'Root':
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
            if self.stpDetails[interface.name]['state'] == 'discarding' and \
                    self.stpDetails[interface.name]['role'] == 'Alternate':
                return None

        for interface in self._enslavedInterfaces:
            if self.stpDetails[interface.name]['role'] == 'Root':
                return interface

    def setPortPriority(self, interface, prio: int):
        """
        Set priority value value to an interface
        :param interface: the interface to set the new port priority value on
        :param prio: the port priority value to set on an interface
        :return: An error message if occurs; None otherwise
        """
        return self._getter.execute(f"mstpctl settreeportprio {self} {interface} 0 {prio}")

    def setPortCost(self, interface, cost: int):
        """
        Set cost value to an interface
        :param interface: the interface to set the new cost value on
        :param cost: the cost value to set on an interface
        :return: An error message if occurs; None otherwise
        """
        return self._getter.execute(f"mstpctl setportpathcost {self} {interface} {cost}")

    def setBdpuGuard(self, interface, state: GUARD):
        """
        Set BDPU guard on/off to an enslaved interface
        :param interface: the interface to set the BDPU guard state on
        :param state: the BDPU guard state to set on an interface (enable/disable)
        :return: An error message if occurs; None otherwise
        """
        return self._getter.execute(f"mstpctl setbpduguard {self} {interface} {state.value}")

    def setForwardDelay(self, time):
        """
        Set forward delay time
        :param time: the new forward delay time
        :return: An error message if occurs; None otherwise
        """
        return self._getter.execute(f"mstpctl setfdelay {self} {time}")

    def setMaxAge(self, time):
        """
        Set max age time
        :param time: the new max age time
        :return: An error message if occurs; None otherwise
        """
        return self._getter.execute(f"mstpctl setmaxage {self} {time}")

    def setHelloTime(self, time):
        """
        Set hello time
        :param time: the new hello time
        :return: An error message if occurs; None otherwise
        """
        return self._getter.execute(f"mstpctl sethello {self} {time}")

    def isRootPort(self, interface):
        """
        Return True if a given interface's role is root; else return False
        :param interface: the given interface to verify whether it's role is root
        :return: True if a given interface's role is root; else return False
        """
        return self.stpDetails[interface.name]['role'] == 'Root'

    def getPortId(self, interface):
        try:
            return int(self.stpDetails[interface.name]['port-id'].replace('.', ''))
        except:
            return int(self.stpDetails[interface]['port-id'].replace('.', ''))
