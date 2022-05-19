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

from CLI_GlobalFunctions.SwitchDev.CLICommands.Executer import GlobalGetterSetter
from CLI_GlobalFunctions.SwitchDev.IPv4.IPConfig import IPConfig


class IPv4Config(IPConfig):
    _ipv4Forwarding = None
    _icmpEcho = None
    _intervalTimeout = None
    _minEntries = None
    _maxSoftEntries = None
    _maxHardEntries = None
    _portList = None

    def __init__(self, switchDevDutPort, otherDutChannel=False, executer=True):
        super(IPv4Config, self).__init__(switchDevDutPort, otherDutChannel, executer)
        self._ipAdrr = None  # type: str
        self._arpEntry = None  # type: str
        self._defGw = None
        self._reachableTimeout = None  # type: int
        self._agingTimeout = None  # type: int

    @classmethod
    def getPortList(cls):
        ret = GlobalGetterSetter().getter.ls('/sys/class/net/', '|', 'grep', 'sw1p*', '|', 'sort', '-t', 'p', '-k', '2', '-g')
        cls._portList = ret.split()
        return cls._portList

    @classmethod
    def getIpv4Forwarding(cls):
        return cls._ipv4Forwarding

    @classmethod
    def setIpv4Forwarding(cls, v):
        ret = GlobalGetterSetter().setter.sysctl('-w', f'net.ipv4.ip_forward={v}')
        # if GlobalGetterSetter().otherDutChannel:
        #     ret = GlobalGetterSetter().setterOtherDut.sysctl('-w', f'net.ipv4.ip_forward={v}')
        if not ret:
            cls._ipv4Forwarding = v
        return ret

    @classmethod
    def setPortUp(cls, port, v):
        return GlobalGetterSetter().setter.ip_link_set('dev', port, v)

    @classmethod
    def getICMPecho(cls):
        return cls._icmpEcho

    @classmethod
    def setICMPecho(cls, v):
        ret = GlobalGetterSetter().setter.sysctl('-w', f'net.ipv4.icmp_echo_ignore_all={v}')
        if not ret:
            cls._icmpEcho = v
        return ret

    @classmethod
    def getARPEntries(cls):
        return GlobalGetterSetter().getter.arp('-n', ' | ', 'wc', '-l')

    @classmethod
    def getRoute(cls, dev):
        return GlobalGetterSetter().getter.ip('route', '|', 'grep', '-E',
                                              f'"default via.*{dev.switchdevInterface.name}"')

    @classmethod
    def setGlobIP(cls, addr, mask, port):
        return GlobalGetterSetter().setter.ip_addr_add(f"{addr}/{mask}", 'dev', port)

    @classmethod
    def delGlobIP(cls, addr, mask, port):
        return GlobalGetterSetter().setter.ip_addr_del(f"{addr}/{mask}", 'dev', port)

    @classmethod
    def glblGetIPAddr(cls, port):
        return GlobalGetterSetter().getter.ip(f"-4 -o addr show {port}", " | awk '{print $4}' | cut -d '/' -f 1 ")

    def getIPAddr(self, port):
        return self._getter.ip(f"-4 -o addr show {port}", " | awk '{print $4}' | cut -d '/' -f 1 ")

    @classmethod
    def setDHCPService(cls, v):
        return GlobalGetterSetter().setter.service('isc-dhcp-server', v)

    def DHCPRequest(self):
        ret = self._setter.dhclient('-v', self._switchdevInterface.name)
        return ret

    def setARPEntry(self, ip, mac):
        ret = self._setter.arp('-s', ip, mac)
        if not ret:
            self._arpEntry = f'{ip} {mac}'
        return ret

    def remARPEntry(self, ip):
        ret = self._setter.arp('-d', ip)
        if not ret:
            self._arpEntry = None
        return ret

    def setNEIGHEntry(self, ip, mac):
        ret = self._setter.ip_neigh_add(ip, 'lladdr', mac, 'dev', self._switchdevInterface.name)
        if not ret:
            self._arpEntry = f'{ip} {mac}'
        return ret

    def remNEIGHEntry(self, ip, mac):
        ret = self._setter.ip_neigh_del(ip, 'lladdr', mac, 'dev', self._switchdevInterface.name,  timeout=20)
        if not ret:
            self._arpEntry = None
        return ret

    def setDefGw(self, gw):
        ret = self._setter.route_add_default_gw(gw, self._switchdevInterface.name)
        if not ret:
            self._defGw = gw
        return ret

    def remDefGw(self, gw):
        ret = self._setter.route_del_default_gw(gw, self._switchdevInterface.name)
        if not ret:
            self._defGw = None

    def setReachableTimeout(self, timeout):
        ret = self._setter.echo(timeout,
                                f'> /proc/sys/net/ipv4/neigh/{self._switchdevInterface.name}/base_reachable_time')
        if not ret:
            self._reachableTimeout = timeout
        return ret

    def setAgingTimeout(self, timeout):
        ret = self._setter.echo(timeout, f'> /proc/sys/net/ipv4/neigh/{self._switchdevInterface.name}/gc_stale_time')
        if not ret:
            self._agingTimeout = timeout
        return ret

    @classmethod
    def setIntervalTimeout(cls, timeout):
        ret = GlobalGetterSetter().setter.echo(timeout, f'> /proc/sys/net/ipv4/neigh/default/gc_interval')
        if not ret:
            cls._intervalTimeout = timeout
        return ret

    @classmethod
    def setArpTableMinEntries(cls, num):
        ret = GlobalGetterSetter().setter.echo(num, f'> /proc/sys/net/ipv4/neigh/default/gc_thresh1')
        if not ret:
            cls._minEntries = num
        return ret

    @classmethod
    def setArpTableSoftMaxEntries(cls, num):
        ret = GlobalGetterSetter().setter.echo(num, f'> /proc/sys/net/ipv4/neigh/default/gc_thresh2')
        if not ret:
            cls._maxSoftEntries = num
        return ret

    @classmethod
    def setArpTableHardMaxEntries(cls, num):
        ret = GlobalGetterSetter().setter.echo(num, f'> /proc/sys/net/ipv4/neigh/default/gc_thresh3')
        if not ret:
            cls._maxHardEntries = num
        return ret

    def getPortArpEntries(self):
        return self._getter.arp('-i', self._switchdevInterface.name)

    def ping(self, count, size, interval, addr):
        return self._setter.ping('-c', str(count), '-s', str(size), '-i', str(interval), addr, timeout=4000)

    def traceroute(self, addr, max_ttl, nqueries):
        return self._setter.traceroute('-m', str(max_ttl), '-q', str(nqueries), addr)

    def addRoute(self, addr):
        return self._setter.ip_route_add(f"{addr}", 'dev', self._switchdevInterface.name)

    def addRouteNextHop(self, routeTo='', via=''):
        return self._setter.ip_route_add(f"{routeTo}", 'nexthop', 'via', f"{via}")

    @classmethod
    def getPortMac(cls, port):
        return GlobalGetterSetter().getter.cat(f'/sys/class/net/{port}/address')

    @classmethod
    def getRouteEntries(cls):
        return GlobalGetterSetter().getter.route(' | ', 'wc', '-l')

    def getEthtoolPortStats(self):
        return self._getter.ethtool ('-S', self._switchdevInterface.name)

    @classmethod
    def fillStaticRouteEntries(self, index1='', index2='', dev=''):

        ret = GlobalGetterSetter().getter.execAsFile(f"""for ((i=0; i<={index1}; i++));
                                          do
                                          for ((j=0; j<={index2}; j++)); 
                                          do ip route add 192.0.$i.$j dev {dev};
                                          done
                                          done
                                          """)
        return ret

    @classmethod
    def fillStaticArpEntries(self, index1='', index2='', mac='', dev=''):

        ret = GlobalGetterSetter().getter.execAsFile(f"""for ((i=0; i<={index1}; i++));
                                          do
                                          for ((j=0; j<={index2}; j++)); 
                                          do ip neigh add 192.0.$i.$j lladdr {mac} dev {dev}
                                          done
                                          done
                                          """)
        return ret





