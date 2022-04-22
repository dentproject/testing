from dent_os_testbed.lib.os.linux.linux_service import LinuxService


class LinuxServiceImpl(LinuxService):
    """
    Service details by runnin systemctl --type=service
    """

    def format_show(self, command, *argv, **kwarg):
        """
        > systemctl list-units --type=service
        UNIT                               LOAD   ACTIVE SUB     DESCRIPTION
        cron.service                       loaded active running Regular background program processing daemon
        dbus.service                       loaded active running D-Bus System Message Bus
        dnsmasq.service                    loaded active running dnsmasq - A lightweight DHCP and caching DNS server
        faultd.service                     loaded active running LSB: Start Faultd Agent
        frr.service                        loaded active running FRRouting
        ....

        """
        params = kwarg["params"]
        if "name" in params:
            return "systemctl status {}.service".format(params["name"])
        cmd = "systemctl list-units --type=service "
        if "status" in params:
            cmd += " --state={} ".format("status")
        return cmd

    def parse_show(self, command, output, *argv, **kwarg):
        """
        > systemctl list-units --type=service
        UNIT                               LOAD   ACTIVE SUB     DESCRIPTION
        cron.service                       loaded active running Regular background program processing daemon
        dbus.service                       loaded active running D-Bus System Message Bus
        dnsmasq.service                    loaded active running dnsmasq - A lightweight DHCP and caching DNS server
        faultd.service                     loaded active running LSB: Start Faultd Agent
        frr.service                        loaded active running FRRouting
        ....

        """
        services = []
        records = output.split("\n")[1:-8]
        for r in records:
            r = r.strip()
            tokens = r.split()
            name = tokens.pop(0)
            loaded = tokens.pop(0)
            active = tokens.pop(0)
            status = tokens.pop(0)
            desc = " ".join(tokens)
            services.append(
                {
                    "name": name,
                    "loaded": loaded,
                    "active": active,
                    "status": status,
                    "description": desc,
                }
            )

        return services

    def format_operation(self, command, *argv, **kwarg):
        """
        > systemctl <operation> <name>

        """
        params = kwarg["params"]
        flags = params.get("flags", "")
        cmd = "systemctl {} {} ".format(flags, command)
        ############# Implement me ################
        if "name" in params:
            cmd += params["name"]
        return cmd
