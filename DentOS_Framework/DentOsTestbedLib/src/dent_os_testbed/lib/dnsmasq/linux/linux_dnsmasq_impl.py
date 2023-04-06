from dent_os_testbed.lib.dnsmasq.linux.linux_dnsmasq import LinuxDnsmasq


class LinuxDnsmasqImpl(LinuxDnsmasq):
    """
    dnsmasq is a lightweight DNS, TFTP, PXE, router advertisement and DHCP server.
    It is intended to provide coupled DNS and DHCP service to a LAN.
    dnsmasq [OPTION]...

    """

    def format_test(self, command, *argv, **kwarg):
        """
        --test - Read and syntax check configuration file(s). Exit with code 0 if
          all is OK, or a non-zero code otherwise. Do not start up dnsmasq.

        """
        params = kwarg['params']
        cmd = 'dnsmasq {} '.format(command)
        ############# Implement me ################

        return cmd

    def parse_test(self, command, output, *argv, **kwarg):
        """
        --test - Read and syntax check configuration file(s). Exit with code 0 if
          all is OK, or a non-zero code otherwise. Do not start up dnsmasq.

        """
        params = kwarg['params']
        cmd = 'dnsmasq {} '.format(command)
        ############# Implement me ################

        return cmd
