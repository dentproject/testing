import re

from dent_os_testbed.lib.onlp.linux.linux_onlp_sfp_info import LinuxOnlpSfpInfo

RE_SPACES = re.compile('\s+')


class LinuxOnlpSfpInfoImpl(LinuxOnlpSfpInfo):
    """
    ONLP SFP details by running onlpdump -S
    """

    def format_show(self, command, *argv, **kwarg):
        """
        Port  Type            Media   Status  Len    Vendor            Model             S/N
        ----  --------------  ------  ------  -----  ----------------  ----------------  ----------------
        49  10GBASE-CR      Copper          2m     FS                SFP-10G-DAC       G1807081119-1
        50  10GBASE-CR      Copper          1m     FCI Electronics   10110818-2010LF               0009

        """
        params = kwarg['params']
        cmd = '/lib/platform-config/current/onl/bin/onlpdump -S'
        return cmd

    def parse_show(self, command, output, *argv, **kwarg):
        """
        Port  Type            Media   Status  Len    Vendor            Model             S/N
        ----  --------------  ------  ------  -----  ----------------  ----------------  ----------------
          49  10GBASE-CR      Copper          2m     FS                SFP-10G-DAC       G1807081119-1
          50  10GBASE-CR      Copper          1m     FCI Electronics   10110818-2010LF               0009

        """
        sfps_info = []
        record = output
        if '\\n' in record:
            records = record.split('\\n')[:-1]
        else:
            records = record.split('\n')[:-1]
        sfp = {}
        keys = RE_SPACES.sub(' ', records[0].lower()).strip().split(' ')
        spaces = RE_SPACES.sub(' ', records[1].lower()).strip().split(' ')
        keys.pop()
        keys.append('serial_number')
        for line in records[2:]:
            sfp = {}
            for k, s in zip(keys, spaces):
                s = len(s)
                sfp[k] = RE_SPACES.sub(' ', line[:s]).strip()
                line = line[s + 2:]
            try:
                port = int(sfp['port'])
                sfps_info.append(sfp)
            except:
                pass
        return sfps_info
