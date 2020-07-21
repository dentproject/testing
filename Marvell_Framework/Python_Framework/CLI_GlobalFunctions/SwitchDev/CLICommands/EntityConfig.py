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

from CLI_GlobalFunctions.SwitchDev.CLICommands.Executer import Getter, Setter, GlobalGetterSetter
from PyInfra.BaseTest_SV.SV_Enums.SwitchDevInterface import SwitchDevDutInterface

"Represents General Entity Configurator"


class GeneralEntityConfig:

    def __init__(self, switchDevInterface, otherDutChannel, executer=True):
        """
        :param switchDevInterface: the interface entity
        :type switchDevInterface: SwitchDevDutInterface
        :param otherDutChannel: True if other DUT channel exist; False otherwise
        """
        self._switchdevInterface = switchDevInterface
        self._operstate = ""
        self._master = ""
        self._ipDetails = {}
        glblGetterSetter = GlobalGetterSetter()

        if not otherDutChannel:
            self._getter, self._setter = (glblGetterSetter.getter, glblGetterSetter.setter)
        else:
            self._getter, self._setter = (glblGetterSetter.getterOtherDut, glblGetterSetter.setterOtherDut)
        if executer:
            if not otherDutChannel:
                glblGetterSetter.setter = self._setter = self._getter
            else:
                glblGetterSetter.setterOtherDut = self._setter = self._getter
        elif isinstance(self._setter, Getter):
            self._setter = GlobalGetterSetter().setter = Setter()

    def __str__(self):
        return self.switchdevInterface.name

    @property
    def switchdevInterface(self):
        """
        :return: return the switchDevInterface being configured
        """
        return self._switchdevInterface

    @property
    def state(self):
        """
        :return: the state of the port (up or down)
        """
        return self._operstate

    def setState(self, v):
        """
        :param v: the state to be set (up or down)
        :return: the error message if one occurred; else None
        """
        ret = self._setter.ip_link_set(v, dev=self)
        if not ret:
            self._operstate = v
        return ret

    @property
    def master(self):
        return self._master

    def setMaster(self, v):
        ret = self._setter.ip_link_set(dev=self, master=v)
        if not ret:
            self._master = v
        return ret

    def setNomaster(self, interface, timing=False, timeout=10.0):
        """
        Removes all enslaved ports
        :return: ret: An Error message, if received
        """
        # FIXME: need to add functionality which parses timing of multiple set commands as well
        if timing:
            return self._getter.ip_link_set('nomaster', dev=interface.name, timing=timing, timeout=timeout)
        self._setter.ip_link_set('nomaster', dev=interface.name, timing=timing, timeout=timeout)

    def getActualState(self):
        """
        :return: the actual speed
        """
        self._getter.cat(r"/sys/class/net/{}/operstate".format(self))

    def getIPDetails(self):
        import json5
        self._ipDetails = json5.loads(self._getter.ip(f'-j -d link show dev {self}'))[0]
        for k, v in self._ipDetails.items():
            if f"_{k}" in self.__dict__:
                self.__dict__[f"_{k}"] = v


class L2EntityConfig(GeneralEntityConfig):

    def __init__(self, switchDevInterface, type, otherDutChannel, executer=True):
        """
        This class represents L2 entities like bond and bridge
        :param switchDevInterface:
        :param type: The type of the entity (e.g, bond, bridge, etc.)
        :param otherDutChannel: True if other DUT channel exist; False otherwise
        """
        super(L2EntityConfig, self).__init__(switchDevInterface, otherDutChannel, executer)
        self._type = type
        self._enslavedInterfaces = []  # type: list[SwitchDevDutInterface]

    @property
    def enslavedInterfaces(self):
        """
        :return: list of all enslaved interfaces
        """
        return self._enslavedInterfaces

    def createL2Entity(self, *args, **kwargs):
        return self._setter.ip_link(add=self, type=self._type, *args, **kwargs)

    def setEnslavedInterfaces(self, *enslavedInterfaces):
        """
        :param enslavedInterfaces: list of interfaces to be enslaved to self.switchDevInterface
        :type enslavedInterfaces: list[SwitchDevDutInterface]
        :return: ret: An Error message, if received
        """
        for interface in enslavedInterfaces:
            try:
                ret = self._setter.ip_link_set(dev=interface.name, master=self)
            except AttributeError:
                ret = self._setter.ip_link_set(dev=interface.DutDevPort.name, master=self)

            if not ret:
                self.enslavedInterfaces.append(interface)
            else:
                return ret

        return None

    def setNonSlaveInterface(self, enslavedInterface):
        return self._setter.ip_link_set(enslavedInterface.DutDevPort.name, 'nomaster')

    @property
    def entityType(self):
        """
        :return: the type the entity
        """
        return self._type

    def deleteEntity(self, timeout=10.0):
        self._setter.ip_link_delete(dev=self, timeout=timeout)
