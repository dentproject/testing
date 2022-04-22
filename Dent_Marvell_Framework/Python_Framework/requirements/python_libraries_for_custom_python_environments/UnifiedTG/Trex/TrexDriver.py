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

from collections import OrderedDict

from pytrex.trex_app import TrexApp as trex_app
from pytrex.trex_port import TrexPort

def init_trex(logger, username):
    return TrexApp(logger, username)


class TrexApp():

    def __init__(self, logger, username):
        self.logger = logger
        self.username = username
        self.servers = OrderedDict()

    def connect(self, login):
        pass

    @property
    def connected(self):
        return True

    @property
    def session(self):
        return self._app_driver.session

    def add(self, chassis_ip):

        self.servers[chassis_ip] = trex_app(logger=self.logger, username=self.username)#init_trex(logger=self.logger, username=self.username)
        self.servers[chassis_ip].connect(ip=chassis_ip)

    def reserve_ports(self, locations, force=False, reset=True):
        ports = {}

        for location in locations:
            server, chass, port = location.split('/')
            ports[location] = list(self.servers[server].server.reserve_ports([int(port)], force=force, reset=reset).values())[0]
            # self.servers[server].acquire(ports=int(port), force=force, sync_streams=False)
            # ports[location] = self.servers[server].server.ports[int(port)]
            # if reset:
            #     for location in locations:
            #         self.servers[location.split('/')[0]].reset()
        return ports

    def start_traffic(self, blocking=False, *ports):
        tx_servers = self._per_server_ports(*ports)
        for tx_server_ip, tx_ports in tx_servers.items():
            self.servers[tx_server_ip].start(tx_ports)
        if blocking:
            for tx_server_ip, tx_ports in tx_servers.items():
                self.wait_on_traffic[tx_server_ip].start(tx_ports)

    def stop_traffic(self, *ports):
        for tx_server_ip, tx_ports in self._per_server_ports(*ports).items():
            self.servers[tx_server_ip].stop(tx_ports)

    def _per_server_ports(self, *ports):
        per_server_ports = OrderedDict()
        for server_ip, server in self.servers.items():
            server_ports = list(set(ports) & set(server.ports.values()))
            if server_ports:
                per_server_ports[server_ip] = [p.port_id for p in server_ports]
        return per_server_ports
