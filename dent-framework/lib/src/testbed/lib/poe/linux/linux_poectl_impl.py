import json

from testbed.lib.poe.linux.linux_poectl import LinuxPoectl


class LinuxPoectlImpl(LinuxPoectl):
    """
    POE details by running poectl
    """

    def format_show(self, command, *argv, **kwarg):
        """
        -i, --port-info PORT_LIST            Return detailed information for the specified ports.
          eg: -i swp1-swp5,swp10
        -j, --json                           Return output in json format
        """
        params = kwarg["params"]
        if params.get("dut_discovery", False):
            params["cmd_options"] = "-j -a"
        cmd = "poectl {} ".format(params.get("cmd_options", ""))
        if "port" in kwarg["params"]:
            cmd += "-i {} ".format(kwarg["params"]["port"])
        return cmd

    def parse_show(self, command, output, *argv, **kwarg):
        try:
            parsed_out = json.loads(output)
        except:
            return []
        ports = [p for _, p in parsed_out.get("ports", parsed_out).items()]
        for port in ports:
            port["port"] = port["swp"]
        return ports

    def format_modify(self, command, *argv, **kwarg):
        """
        -d, --disable-ports PORT_LIST        Disable POE operation on the specified ports.
        -e, --enable-ports PORT_LIST         Enable POE operation on the specified ports.

        """
        params = kwarg["params"]
        cmd = "poectl {} --{}-ports ".format(params.get("cmd_options", ""), command)
        ############# Implement me ################
        if "port" not in kwarg["params"]:
            return cmd
        cmd += " {} ".format(kwarg["params"]["port"])
        return cmd

    def parse_modify(self, command, output, *argv, **kwarg):
        return json.loads(output)

    def format_persist(self, command, *argv, **kwarg):
        """
        --save                               Save the current configuration. The saved configuration
                                             is automatically loaded on system boot.
        --load                               Load and apply the saved configuration.

        """
        params = kwarg["params"]
        cmd = "poectl  {} ".format(command)
        ############# Implement me ################

        return cmd

    def parse_persist(self, command, output, *argv, **kwarg):
        return json.loads(output)
