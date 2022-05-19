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

from abc import abstractmethod
from enum import Enum

from CLI_GlobalFunctions.SwitchDev.Bridge.Bridge1QConfig import Bridge1QConfig
from CLI_GlobalFunctions.SwitchDev.CLICommands.Executer import GlobalGetterSetter
from CLI_GlobalFunctions.SwitchDev.Utils import Observable, EventNotFound


class STP_STATE(Enum):
    ENABLE = 'on'
    DISABLE = 'off'


class STP_MODE(Enum):
    RSTP = 'rstp'
    STP = 'stp'


class PORT_ADMIN_EDGE_STATE(Enum):
    ENABLE = 'yes'
    DISABLE = 'no'


class BDPU_FILTER(Enum):
    ENABLE = 'yes'
    DISABLE = 'no'


obs = Observable()


class AbstractSpanningTreeConfig(Bridge1QConfig):

    PROTOCOL_VERSION_IDENTIFIER = ""

    class STATES(Enum):
        FORWARDING = ''
        LEARNING = ''
        LISTENING = ''
        BLOCKING = ''
        DISABLED = ''

    class GUARD(Enum):
        ENABLE = ""
        DISABLE = ""

    _ipDetailedShow = {}

    @classmethod
    def delete(cls):
        try:
            obs.off('update')
        except EventNotFound:
            pass
        finally:
            return GlobalGetterSetter().getter.execute(f"sed -i \"/^[#]*MANAGE_MSTPD=/ cMANAGE_MSTPD='n'\" /etc/bridge-stp.conf")

    def __init__(self, switchDevInterface, otherDutChannel=False, executer=True):
        """
        :param switchDevInterface: the entity to be configured (e.g, bond, port, bridge)
        :param otherDutChannel: True if there is another DUT; False otherwise
        """
        super(Bridge1QConfig, self).__init__(switchDevInterface, otherDutChannel, executer)
        self._stpDetails = {}

    def setStpMode(self, mode: STP_MODE):
        """
        Set STP protocol version on the bridge (Rapid/Standard Spanning Tree)
        :param mode: the mode to set on an bridge (stp/rstp)
        :return: An error message if occurs; None otherwise
        """
        return self._getter.execute(f"mstpctl addbridge {self} && mstpctl setforcevers {self} {mode.value}")

    def createL2Entity(self, *args, **kwargs):
        return super(AbstractSpanningTreeConfig, self).createL2Entity(*args, **{'stp_state': 1, 'vlan_filtering': 0, **kwargs})

    def setStpState(self, state: STP_STATE):
        """
        Enable/disable Spanning tree on the bridge
        :param state: the state to set on an bridge (enable/disable)
        :return: An error message if occurs; None otherwise
        """
        return self._getter.execute(f'brctl stp {self} {state.value}')

    @property
    def stpDetails(self):
        if not self._stpDetails:
            self.getStpDetails()
        return self._stpDetails

    @abstractmethod
    def isRootBridge(self):
        pass

    @abstractmethod
    def setBridgePrio(self, value):
        pass

    @abstractmethod
    def getStpDetails(self):
        pass

    @abstractmethod
    def getBlockedPort(self):
        pass

    @abstractmethod
    def getDirectPort(self):
        pass

    @abstractmethod
    def getIndirectPort(self):
        pass

    def getEnslvaedIntState(self, interface):
        """
        Returns the state of the interface within the STP topology if enslaved to stp-aware bridge; returns None otherwise
        :param interface:
        :return: Returns the state of the interface within the STP topology if enslaved to stp-aware bridge; returns None otherwise
        """
        try:
            return self.stpDetails.get(interface.name, {}).get('state')
        except:
            return self.stpDetails.get(interface, {}).get('state')

    def setPortAdminEdge(self, interface, state: PORT_ADMIN_EDGE_STATE):
        """
        Enable/disable port-admin-edge state (portfast)
        :return: An error message from the Linux if occurs; None otherwise
        """
        return self._getter.execute(f"mstpctl setportadminedge {self} {interface} {state.value}")

    @abstractmethod
    def setPortPriority(self, interface, prio: int):
        pass

    @abstractmethod
    def setPortCost(self, interface, cost: int):
        pass

    @abstractmethod
    def setBdpuGuard(self, interface, state: GUARD):
        pass

    def setRootGuard(self, interface, state: GUARD):
        """
        Set root guard on/off to an enslaved interface
        :param interface: the interface to set the BDPU guard state on
        :param state: the root guard state to set on an interface (enable/disable)
        :return: An error message if occurs; None otherwise
        """
        return self._getter.execute(f"bridge link set dev {interface} root_block {state.value}")

    @abstractmethod
    def setMaxAge(self, time):
        pass

    @abstractmethod
    def setForwardDelay(self, time):
        pass

    def setBdpuFilter(self, interface, state: BDPU_FILTER):
        """
        Set BDPU filter on/off to an enslaved interface
        :param interface: the interface to set the BDPU filter state on
        :param state: the BDPU filter state to set on an interface (enable/disable)
        :return: An error message if occurs; None otherwise
        """

        obs.trigger("enableMstpd")
        from CLI_GlobalFunctions.SwitchDev.SpanningTree.StandardSpanningTreeConfig import StandardSpanningTreeConfig
        ret = self.setStpMode(STP_MODE.STP if isinstance(self, StandardSpanningTreeConfig) else STP_MODE.RSTP)
        if ret:
            return ret
        return self._getter.execute(f"mstpctl setportbpdufilter {self} {interface} {state.value}")

    @abstractmethod
    def setHelloTime(self, time):
        pass

    @abstractmethod
    def isRootPort(self, interface):
        pass

    @abstractmethod
    def getPortId(self, interface):
        pass