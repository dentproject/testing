from dent_os_testbed.lib.ntp.linux.linux_ntp_date import LinuxNtpDate


class LinuxNtpDateImpl(LinuxNtpDate):
    """
    ntpdate [-46bBdqsuv] [-a key] [-e authdelay] [-k keyfile] [-o version] [-p samples] [-t timeout] server [...]

    """

    def format_set(self, command, *argv, **kwarg):
        """
        ntpdate [-46bBdqsuv] [-a key] [-e authdelay] [-k keyfile] [-o version] [-p samples] [-t timeout] server [...]
         -4     - Force DNS resolution of following host names on the command line to the IPv4 namespace.
         -6     - Force DNS resolution of following host names on the command line to the IPv6 namespace.
         -a key - Enable the authentication function and specify the key identifier to be used for
                  authentication as the argument keyntpdate. The keys and key identifiers must match in
                  both the client and server key files. The default is to disable the authentication function.
         -B     - Force the time to always be slewed using the adjtime() system call. This is the default.
         -b     - Force the time to be stepped using the settimeofday() system call, rather than slewed (default)
                  using the adjtime() system call. This option should be used when called from a startup
                  file at boot time.
         -d     - Enable the debugging mode, in which ntpdate will go through all the steps, but not adjust
                  the local clock and using an unprivileged port. Information useful for general debugging
                  will also be printed.
         -e     - authdelay Specify the processing delay to perform an authentication function as the value
                  authdelay, in seconds and fraction (see ntpd for details). This number is usually small
                  enough to be negligible for most purposes, though specifying a value may improve timekeeping
                  on very slow CPU's.
         -k keyfile - Specify the path for the authentication key file as the string keyfile. The default
                  is /etc/ntp.keys. This file should be in the format described in ntpd.
         -o version - Specify the NTP version for outgoing packets as the integer version, which can be
                     1, 2, 3 or 4. The default is 4. This allows ntpdate to be used with older NTP versions.
         -q     - Query only – don't set the clock.
         -s     - Divert logging output from the standard output (default) to the system syslog facility.
                 This is designed primarily for convenience of cron scripts.
         -t timeout - Specify the maximum time waiting for a server response as the value timeout, in seconds
                 and fraction. The value is rounded to a multiple of 0.2 seconds. The default is 1 second,
                 a value suitable for polling across a LAN.
         -u     - Direct ntpdate to use an unprivileged port for outgoing packets. This is most useful when
                  behind a firewall that blocks incoming traffic to privileged ports, and you want to
                  synchronise with hosts beyond the firewall. Note that the -d option always uses unprivileged ports.
         -v     - Be verbose. This option will cause ntpdate's version identification string to be logged.

        """
        params = kwarg["params"]
        cmd = "ntpdate {} ".format(command)
        ############# Implement me ################

        if "command_options" in params:
            cmd += "{} ".format(params["command_options"])

        if "key" in params:
            cmd += "-a {} ".format(params["key"])

        if "authdelay" in params:
            cmd += "-e {} ".format(params["authdelay"])

        if "keyfile" in params:
            cmd += "-k {} ".format(params["keyfile"])

        if "version" in params:
            cmd += "-o {} ".format(params["version"])

        if "samples" in params:
            cmd += "-p {} ".format(params["samples"])

        if "timeout" in params:
            cmd += "-t {} ".format(params["timeout"])

        if "servers" in params:
            for server in params["servers"]:
                cmd += "{} ".format(server)

        return cmd
