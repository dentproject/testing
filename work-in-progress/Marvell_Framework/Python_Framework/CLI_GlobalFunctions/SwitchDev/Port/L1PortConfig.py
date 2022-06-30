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

import re
from builtins import str, range
from UnifiedTG.Unified.TGEnums import TGEnums
from CLI_GlobalFunctions.SwitchDev.CLICommands.EntityConfig import GeneralEntityConfig
from CLI_GlobalFunctions.SwitchDev.CLICommands.Executer import GlobalGetterSetter


class L1PortConfig(GeneralEntityConfig):
    ADVERTISE_MAP = {
        '10_half': '0x001',
        '10_full': '0x002',
        '100_half': '0x004',
        '100_full': '0x008',
        '1000_full': '0x020'
    }

    TG_ADVERTISE_MAP = {
        f'10{TGEnums.DUPLEX.HALF.value}': '0x001',
        f'10{TGEnums.DUPLEX.FULL.value}': '0x002',
        f'100{TGEnums.DUPLEX.HALF.value}': '0x004',
        f'100{TGEnums.DUPLEX.FULL.value}': '0x008',
        f'1000{TGEnums.DUPLEX.HALF.value}': '0x010',
        f'1000{TGEnums.DUPLEX.FULL.value}': '0x020',
    }

    __l1PortConfigObjects = {}  # type: dict[str, L1PortConfig]

    @classmethod
    def getNumberOfPorts(cls):
        return GlobalGetterSetter().getter.ifconfig(' -a | grep -Eo "sw1p[0-9]+" | wc -l')

    @classmethod
    def getEthtoolConf(cls, ports):
        """
        Parses ethtool <DEVNAME> command of ports list passed as argument and puts its output in a dictionary
        :param ports: list of L1PortConfig objects
        :type ports: L1PortConfig
        :return: the result of the output and the
        """
        portsIndices = [port.switchdevInterface.name.replace('sw1p', '') for port in ports]
        cmd = f"for i in {' '.join(portsIndices)}; do ethtool sw1p$i; done"
        res, err = GlobalGetterSetter().getter.getCmdOutputAsFile(cmd)
        for st in filter(None, res.split('Settings for ')):
            cls.__l1PortConfigObjects[re.match('sw1p[0-9]+', st).group(0)].getPortEthtoolConf(st)
        return res, err

    @classmethod
    def getEthtoolStats(cls, ports):
        portsIndices = [port.switchdevInterface.name.replace('sw1p', '') for port in ports]
        res, err = GlobalGetterSetter().getter.getCmdOutputAsFile(
            f"for i in {' '.join(portsIndices)};"
            "do echo -e \"sw1p$i\n $(ethtool -S sw1p$i)\" | awk '{++n} n!=2'; done")
        for portName, stats in zip(*[filter(None, re.split(r'(sw1p[0-9]+)', res))] * 2):
            cls.__l1PortConfigObjects[portName].getEthtoolPortStats(stats)
        return res, err

    def __init__(self, switchDevDutPort, otherDutChannel=False, executer=True):
        super(L1PortConfig, self).__init__(switchDevDutPort, otherDutChannel, executer)
        self._speed = None
        self._mtu = None  # type: int
        self._autoneg = None  # type: int
        self._advertise = None  # type: int
        self._duplex = None
        self._statistics = None
        self._ethtoolSettings = {}

        # make each dictionary item to be an attribute, to make it easier to access
        # e.g, instead of calling x['key'], just use x.key
        class __Stats(dict):
            def __setitem__(self, key, value):
                self.__setattr__(key, value)

        self.__ethtoolStats = __Stats()
        self.__ipLinkStats = __Stats()
        self.__class__.__l1PortConfigObjects[switchDevDutPort.name] = self

    @property
    def ethtoolStats(self):
        return self.__ethtoolStats

    @property
    def ipLinkStats(self):
        return self.__ipLinkStats

    @property
    def mtu(self):
        return self._mtu

    def setMTU(self, v):
        ret = self._setter.ip_link_set(dev=self._switchdevInterface.name, mtu=str(v))
        if not ret:
            self._mtu = v
        return ret

    def setSpeedDuplexAutonegOff(self, speed=None, duplex=None):
        return self._setter.ethtool('--change', self.switchdevInterface.name, 'autoneg', 'off',
                             f'speed {speed}' if speed else '', f'duplex {duplex}' if duplex else '')

    def setSpeed(self, v):
        return self._setter.ethtool('--change', self.switchdevInterface.name, 'speed', str(v))

    def setAutoneg(self, v):
        return self._setter.ethtool('--change', self.switchdevInterface.name, 'autoneg', str(v))

    def setAdvertise(self, v):
        return self._setter.ethtool('--change', self.switchdevInterface.name, 'advertise', str(v))

    def setDuplex(self, v):
        return self._setter.ethtool('--change', self.switchdevInterface.name, 'duplex', str(v).lower())

    """
    Getters
    """

    def getLinkDetected(self):
        return self._ethtoolSettings.get('link_detected', '').lower()

    def getAutonegAdvertised(self):
        return self._ethtoolSettings.get('advertised_auto_negotiation', '').lower()

    def getLinkPartnerAdvertisedAutoNegotiation(self):
        return self._ethtoolSettings.get('link_partner_advertised_auto_negotiation', '').lower()

    def getPortType(self):
        """
        :return: the type of the port (copper of fiber)
        """
        return self._ethtoolSettings.get('port', '').lower()

    def getSpeed(self):
        try:
            lst = re.findall('[0-9]+', self._ethtoolSettings['speed'])
        except TypeError as e:
            if e.args[0] == "'NoneType' object is not subscriptable":
                self.getPortEthtoolConf()
                lst = re.findall('[0-9]+', self._ethtoolSettings['speed'])
            else:
                raise TypeError
        if lst:
            return lst[0]
        elif 'speed' in self._ethtoolSettings:
            return self._ethtoolSettings['speed']
        return -1

    def getAutoneg(self):
        return self._ethtoolSettings['auto_negotiation']

    def getDuplex(self):
        return self._ethtoolSettings['duplex'].lower()

    def getAdvertise(self):
        actualAdv = f'{self.getSpeed()}_{self.getDuplex()}'
        try:
            return self.ADVERTISE_MAP[actualAdv]
        except KeyError:
            return -1

    def getEthtoolPortStats(self, stats=None):
        if not stats:
            stats = self._getter.ethtool('S', self.switchdevInterface.name, '| awk \'{++n} n!=1\'')
        for i, j in zip(*[filter(None, re.split(r'\s', stats))] * 2):
            self.__ethtoolStats[i.strip(':')] = int(j)

    # TODO: implement this function
    def getIpLinkPortStats(self):
        pass

    def getSupportedLinkModes(self):
        return self.__parseSupportedLinkModes('supported_link_modes')

    def getAdvertisedLinkModes(self):
        return self.__parseSupportedLinkModes('advertised_link_modes')

    def getLinkPartnerAdvertisedLinkModes(self):
        return self.__parseSupportedLinkModes('link_partner_advertised_link_modes')

    def getPortEthtoolConf(self, portConf=None):
        """
        Parses ethtool <DEVNAME> command and puts its output in a dictionary
        :param portConf:
        :return:
        """
        if not portConf:
            portConf = self._getter.ethtool(self.switchdevInterface.name)
        y = [x.strip() for x in re.split(r"((?:[\w]+[ \t]*|[-]*)*[:](?:[\w]+[ \t]*)*)", portConf) if
             x and not str(x).isspace()]
        self._ethtoolSettings = {re.sub(r'([- /])', '_', y[i].strip(':').lower()): y[i + 1] for i in
                                 range(1, len(y), 2)}
        return self._ethtoolSettings

    def __parseSupportedLinkModes(self, suppLinkModes):
        """
        Little util to parse link supported modes & link partner advertised modes
        :param suppLinkModes: 'supported_link_modes' or 'link_partner_advertised_link_modes' fields from
        'ethtool <DEVNAME>' command (if exists)
        :return: returns the list of supported modes in format '<speed>_<duplex>'
        """
        if suppLinkModes in self._ethtoolSettings:
            if isinstance(self._ethtoolSettings[suppLinkModes], str) and \
                    'Not reported' not in self._ethtoolSettings[suppLinkModes]:
                supModeList = []
                linkModeReg = re.compile('(?P<speed>[0-9]+)(?:base[T, X][/])(?P<duplex>Half|Full)')
                for linkMode in self._ethtoolSettings[suppLinkModes].split():
                    linkMode = linkModeReg.match(linkMode)
                    linkMode = f"{linkMode.group('speed')}_{linkMode.group('duplex').lower()}"
                    supModeList.append(linkMode)
                return supModeList
            elif 'Not reported' in self._ethtoolSettings[suppLinkModes] or \
                    isinstance(self._ethtoolSettings[suppLinkModes], list):
                return self._ethtoolSettings[suppLinkModes]
