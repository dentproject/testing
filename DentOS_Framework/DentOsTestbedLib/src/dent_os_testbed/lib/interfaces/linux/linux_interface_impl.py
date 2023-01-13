from dent_os_testbed.lib.interfaces.linux.linux_interface import LinuxInterface


class LinuxInterfaceImpl(LinuxInterface):
    """
    ifupdown - network interface management commands
     ifup - bring a network interface up
     ifdown - take a network interface down
    ifquery - query network interface configuration
    ifreload - reload network interface configuration

    """

    def format_up_down(self, command, *argv, **kwarg):
        """
        ifup [-h] [-a] [-v] [-d] [--allow CLASS] [--with-depends]
               [-X EXCLUDEPATS] [-f] [-n] [-s] [--print-dependency {list,dot}] [IFACE [IFACE ...]]
        positional arguments:
        IFACE  interface list separated by spaces. IFACE list and '-a' argument are mutually exclusive.
        optional arguments:
        -a, --all
               process all interfaces marked "auto"
        --allow CLASS
               ignore non-"allow-CLASS" interfaces
        -w, --with-depends
               run with all dependent interfaces. This option is redundant when -a is specified.
               When '-a' is specified, interfaces are always executed in dependency order.
        -X EXCLUDEPATS, --exclude EXCLUDEPATS
               Exclude interfaces from the list of interfaces to operate on. Can be specified multiple
               times If the excluded interface has dependent interfaces, (e.g. a bridge or a bond with
               multiple  enslaved  interfaces)  then each dependent interface must be specified in
               order to be excluded.
        -f, --force
               force run all operations
        -n, --no-act
               print out what would happen, but don't do it
        -p, --print-dependency {list,dot}
               print iface dependency in list or dot format
        -s, --syntax-check
               Only run the interfaces file parser

        """
        params = kwarg["params"]
        cmd = "if{} ".format(command)
        ############# Implement me ################
        if "options" in params:
            cmd += "{} ".format(params["options"])
        if "exclude_iface" in params:
            # ifdown -X ma1 -X lo -a
            for e in params["exclude_iface"]:
                cmd += "-X {} ".format(e)
        if "force" in params and params["force"]:
            cmd += "-f "
        if "iface" in params:
            # ifdown ma1 lo
            for i in params["iface"]:
                cmd += "{} ".format(i)

        return cmd

    def format_query(self, command, *argv, **kwarg):
        """
        ifquery [-v] [--allow CLASS] [--with-depends] -a|IFACE...
        ifquery [-v] [-r|--running] [--allow CLASS] [--with-depends] -a|IFACE...
        ifquery [-v] [-c|--check] [--allow CLASS] [--with-depends] -a|IFACE...
        ifquery [-v] [-p|--print-dependency {list,dot}] [--allow CLASS] [--with-depends] -a|IFACE...
        ifquery [-v] -s|--syntax-help
        positional arguments:
        IFACE   interface list separated by spaces. IFACE list and '-a' argument are mutually exclusive.
        optional arguments:
        --allow CLASS
               ignore non-"allow-CLASS" interfaces
        -w, --with-depends
               run with all dependent interfaces. This option is redundant when -a is specified.
               When '-a' is specified, interfaces are always executed in dependency order.
        -r, --running
               print raw interfaces file entries
        -c, --check
               check interface file contents against running state of an interface. Returns
               exit code 0 on success and 1 on error
        -p, --print-dependency {list,dot}
               print iface dependency in list or dot format
        -s, --syntax-help
               print supported interface config syntax. Scans all addon modules and dumps
               supported syntax from them if provided by the module.

        """
        params = kwarg["params"]
        cmd = "ifquery "
        ############# Implement me ################
        if "options" in params:
            cmd += "{} ".format(params["options"])
        if "iface" in params:
            for i in params["iface"]:
                cmd += "{} ".format(i)
        return cmd

    def format_reload(self, command, *argv, **kwarg):
        """
        ifreload [-h] (-a|-c) [-v] [-d] [-f] [-n] [-s]
         -f, --force
                force run all operations
         -c, --currently-up
                Reload the configuration for all interfaces which are currently up regardless
                of whether an interface has "auto <interface>" configuration within the /etc/network/interfaces file.
         -X EXCLUDEPATS, --exclude EXCLUDEPATS
                Exclude  interfaces  from  the  list of interfaces to operate on. Can be specified
                multiple times If the excluded interface has dependent interfaces, (e.g. a bridge or
                a bond with multiple enslaved interfaces) then each dependent interface must be
                specified in order to be excluded.
         -s, --syntax-check
                Only run the interfaces file parser

        """
        params = kwarg["params"]
        cmd = "ifreload "
        ############# Implement me ################
        if "options" in params:
            cmd += "{} ".format(params["options"])
        if "exclude_iface" in params:
            # ifdown -X ma1 -X lo -a
            for e in params["exclude_iface"]:
                cmd += "-X {} ".format(e)

        return cmd
