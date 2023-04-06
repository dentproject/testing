from dent_os_testbed.lib.iptables.linux.linux_ip_tables import LinuxIpTables


class LinuxIpTablesImpl(LinuxIpTables):
    """
    iptables [-t table] {-A|-C|-D} chain rule-specification
    ip6tables [-t table] {-A|-C|-D} chain rule-specification
    iptables [-t table] -I chain [rulenum] rule-specification
    iptables [-t table] -R chain rulenum rule-specification
    iptables [-t table] -D chain rulenum
    iptables [-t table] -S [chain [rulenum]]
    iptables [-t table] {-F|-L|-Z} [chain [rulenum]] [options...]
    iptables [-t table] -N chain
    iptables [-t table] -X [chain]
    iptables [-t table] -P chain target
    iptables [-t table] -E old-chain-name new-chain-name
    rule-specification = [matches...] [target]
    match = -m matchname [per-match-options]
    target = -j targetname [per-target-options]

    """

    def format_update_rules(self, command, *argv, **kwarg):
        """
        -A, --append chain rule-specification
               Append one or more rules to the end of the selected chain.  When the source and/or destination names resolve
               to more than one address, a rule will be added for each possible  address combination.

        -C, --check chain rule-specification
               Check whether a rule matching the specification does exist in the selected chain. This command uses the same
               logic as -D to find a matching entry, but does not alter the existing
               iptables configuration and uses its exit code to indicate success or failure.

        -D, --delete chain rule-specification
        -D, --delete chain rulenum
               Delete one or more rules from the selected chain.  There are two versions of this command: the rule
               can be specified as a number in the chain (starting at 1 for the  first  rule) or a rule to match.
        -I, --insert chain [rulenum] rule-specification
             Insert  one or more rules in the selected chain as the given rule number.  So, if the rule number is 1,
             the rule or rules are inserted at the head of the chain.  This is also the
             default if no rule number is specified.
        -R, --replace chain rulenum rule-specification
             Replace a rule in the selected chain.  If the source and/or destination names resolve to multiple
             addresses, the command will fail.  Rules are numbered starting at 1.

        """
        params = kwarg['params']
        cmd = 'iptables '
        cmd += '-t {} '.format(params['table']) if 'table' in params else ''
        cmd += '--{} '.format(command)
        cmd += '{} '.format(params['chain']) if 'chain' in params else ''
        if 'in-interface' in params:
            cmd += '-i {} '.format(params['in-interface'])
        if 'source' in params:
            cmd += '-s {} '.format(params['source'])
        if 'destination' in params:
            cmd += '-d {} '.format(params['destination'])
        if 'protocol' in params:
            cmd += '-p {} '.format(params['protocol'])
        if 'dport' in params:
            cmd += '--dport {} '.format(params['dport'])
        if 'sport' in params:
            cmd += '--sport {} '.format(params['sport'])
        if 'icmp-type' in params:
            cmd += '--icmp-type {} '.format(params['icmp-type'])
        if 'icmp-code' in params:
            cmd += '--icmp-code {} '.format(params['icmp-code'])
        if 'mac-source' in params:
            cmd += '-m mac --mac-source {} '.format(params['mac-source'])
        if 'target' in params:
            cmd += '-j {} '.format(params['target'])
        return cmd

    def format_show_rules(self, command, *argv, **kwarg):
        """
        -L, --list [chain]
         List all rules in the selected chain.  If no chain is selected, all chains are listed. Like every other
         iptables command, it applies to the specified table  (filter  is  the  default), so NAT rules get listed by
          iptables -t nat -n -L
          Please note that it is often used with the -n option, in order to avoid long reverse DNS lookups.
          It is legal to specify the -Z (zero) option as well, in which case the chain(s) will be atomically listed
          and zeroed.  The exact output is affected by the other arguments given. The exact rules are suppressed
          until you use iptables -L -v  or iptables-save(8).

        -S, --list-rules [chain]
         Print all rules in the selected chain.  If no chain is selected, all chains are printed like iptables-save.
         Like every other iptables command, it applies to the  specified  table (filter is the default).

        -F, --flush [chain]
         Flush the selected chain (all the chains in the table if none is given).  This is equivalent to deleting
         all the rules one by one.

        -Z, --zero [chain [rulenum]]
         Zero  the  packet and byte counters in all chains, or only the given chain, or only the given rule in a chain.
         It is legal to specify the -L, --list (list) option as well, to see the counters immediately before they are
         cleared. (See above.)

        """
        params = kwarg['params']
        ############# Implement me ################
        cmd = 'iptables '
        cmd += '-t {} '.format(params['table']) if 'table' in params else ''
        cmd += '{} '.format(params['cmd_options']) if 'cmd_options' in params else ''
        cmd += '--{} '.format(command)
        if 'chain' in params:
            cmd += '{} '.format(params['chain'])

        return cmd

    def parse_show_rules(self, command, output, *argv, **kwarg):
        lines = output.split('\n')
        chain = None
        chains = {}
        rules = []
        for line in lines:
            if line.startswith('Chain'):
                if chain is not None:
                    chains[chain] = rules
                    rules = []
                chain = line.split(' ')[1]
                continue
            if line.startswith('num'):
                continue
            r = {}
            t = line.split()
            if len(t) < 10:
                continue
            """
            num   pkts bytes target     prot opt in     out     source               destination
            1     6432  353K ACCEPT     all  --  *      *       127.0.0.1            127.0.0.1
            2        0     0 ACCEPT     tcp  --  swp+   *       0.0.0.0/0            10.2.96.0/19         tcp spt:8883
            """
            r['num'] = t.pop(0)
            r['packets'] = t.pop(0)
            r['bytes'] = t.pop(0)
            r['target'] = t.pop(0)
            r['keys'] = {}
            r['keys']['ipproto'] = t.pop(0)
            r['keys']['opt'] = t.pop(0)
            r['keys']['in'] = t.pop(0)
            r['keys']['out'] = t.pop(0)
            r['keys']['srcIp'] = t.pop(0)
            r['keys']['dstIp'] = t.pop(0)
            if t:
                more = t.pop(0)
                if more in ['tcp', 'udp']:
                    while t:
                        l4port = t.pop(0)
                        if l4port.startswith('dpt'):
                            r['keys']['dstPort'] = l4port.split(':')[1]
                        if l4port.startswith('spt'):
                            r['keys']['srcPort'] = l4port.split(':')[1]
            rules.append(r)
        if chain is not None:
            chains[chain] = rules
        return chains

    def format_update_chain(self, command, *argv, **kwarg):
        """
        -N, --new-chain chain
         Create a new user-defined chain by the given name.  There must be no target of that name already.
        -X, --delete-chain [chain]
         Delete the optional user-defined chain specified.  There must be no references to the chain.
         If there are, you must delete or replace the referring rules before the chain can be deleted.
         The chain must be empty, i.e. not contain any rules.  If no argument is given, it will attempt
         to delete every non-builtin chain in the table.

        -P, --policy chain target
         Set the policy for the built-in (non-user-defined) chain to the given target.  The policy target
         must be either ACCEPT or DROP.

        -E, --rename-chain old-chain new-chain
         Rename the user specified chain to the user supplied name.  This is cosmetic, and has no effect
         on the structure of the table.

        """
        params = kwarg['params']
        cmd = 'iptables {} '.format(command)
        ############# Implement me ################

        return cmd
