import json
import subprocess


class ConnectionParams:
    def __init__(self):
        self.pssh = False


class TestDevice:
    def __init__(self, name='test_dev', platform='dentos'):
        self.os = platform
        self.host_name = name
        self.name = name
        self.ssh_conn_params = ConnectionParams()

    async def is_connected(self):
        return True

    async def run_cmd(self, cmd):
        print('\n[' + self.name + '] Running ' + cmd + '\n')
        if 'ip -j address show' in cmd:
            address_show = [
                {
                    'ifindex': 1,
                    'ifname': 'lo',
                    'flags': ['LOOPBACK', 'UP', 'LOWER_UP'],
                    'mtu':65536,
                    'qdisc':'noqueue',
                    'operstate':'UNKNOWN',
                    'group':'default',
                    'txqlen':1000,
                    'link_type':'loopback',
                    'address':'00:00:00:00:00:00',
                    'broadcast':'00:00:00:00:00:00',
                    'addr_info':[
                        {'family': 'inet', 'local': '127.0.0.1', 'prefixlen': 8, 'scope': 'host', 'label': 'lo', 'valid_life_time': 4294967295, 'preferred_life_time': 4294967295},
                        {'family': 'inet', 'local': '10.1.0.1', 'prefixlen': 32, 'scope': 'global', 'label': 'lo', 'valid_life_time': 4294967295, 'preferred_life_time': 4294967295},
                        {'family': 'inet6', 'local': '::1', 'prefixlen': 128, 'scope': 'host', 'valid_life_time': 4294967295, 'preferred_life_time': 4294967295}
                    ]
                },
                {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}
            ]
            return (0, json.dumps(address_show))

        if 'ip -j route show' in cmd:
            route_show = [
                {
                    'dst': 'default',
                    'gateway': '54.240.208.143',
                    'dev': 'ens1f1',
                    'protocol': 'bgp',
                    'metric': 20,
                    'flags': []
                }
            ]
            return (0, json.dumps(route_show))

        if 'ip -j link show' in cmd:
            link_show = [
                {
                    'ifindex': 1,
                    'ifname': 'lo',
                    'flags': ['LOOPBACK', 'UP', 'LOWER_UP'],
                    'mtu':65536, 'qdisc':'noqueue',
                    'operstate':'UNKNOWN',
                    'linkmode':'DEFAULT',
                    'group':'default',
                    'txqlen':1000,
                    'link_type':'loopback',
                    'address':'00:00:00:00:00:00',
                    'broadcast':'00:00:00:00:00:00'
                }
            ]
            return (0, json.dumps(link_show))

        try:
            process = subprocess.Popen(cmd.split(' '), stdout=subprocess.PIPE)
            (stdout, stderr) = process.communicate()
        except Exception:
            return 0, ''
        finally:
            # process.wait()
            pass
        return 0, (str(stdout) if stdout else '') + (str(stderr) if stderr else '')
