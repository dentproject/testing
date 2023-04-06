import re

from dent_os_testbed.lib.onlp.linux.linux_onlp_system_info import LinuxOnlpSystemInfo

RE_SPACES = re.compile('\s+')


class LinuxOnlpSystemInfoImpl(LinuxOnlpSystemInfo):
    """
    ONLP system details by running onlpdump -s
    """

    def format_show(self, command, *argv, **kwarg):
        """
        System Information:
         Product Name: TN48M-P
         Serial Number: TN481P2TW20220013
         MAC: 18:be:92:12:ce:9a
         MAC Range: 55
         Manufacturer: DNI
         Manufacture Date: 06/02/2020 13:24:13
         Vendor: DNI
         Platform Name: 88F7040/88F6820
         Device Version: 1
         Label Revision: C1
         Country Code: TW
         Diag Version: V1.2.1
         Service Tag: 3810000054
         ONIE Version: 2019.08-V02

        """
        params = kwarg['params']
        cmd = '/lib/platform-config/current/onl/bin/onlpdump -s'
        return cmd

    def parse_show(self, command, output, *argv, **kwarg):
        """
        System Information:
         Product Name: TN48M-P
         Serial Number: TN481P2TW20220013
         MAC: 18:be:92:12:ce:9a
         MAC Range: 55
         Manufacturer: DNI
         Manufacture Date: 06/02/2020 13:24:13
         Vendor: DNI
         Platform Name: 88F7040/88F6820
         Device Version: 1
         Label Revision: C1
         Country Code: TW
         Diag Version: V1.2.1
         Service Tag: 3810000054
         ONIE Version: 2019.08-V02

        """
        if output[0] == 'b':
            output = output[2:]
        record = output
        onl_sys_info = {}
        if '\\n' in record:
            records = record.split('\\n')[:-1]
        else:
            records = record.split('\n')[:-1]
        for line in records:
            line = RE_SPACES.sub(' ', line).strip().split(':')
            key = line[0].replace(' ', '_').lower()
            val = ' '.join(line[1:])
            onl_sys_info[key] = val
        return onl_sys_info
