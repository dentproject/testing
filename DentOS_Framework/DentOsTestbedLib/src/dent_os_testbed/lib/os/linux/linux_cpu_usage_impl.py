import re

from dent_os_testbed.lib.os.linux.linux_cpu_usage import LinuxCpuUsage

RE_SPACES = re.compile('\s+')


class LinuxCpuUsageImpl(LinuxCpuUsage):
    def format_show(self, command, *argv, **kwarg):
        """
        mpstat [ -A ] [ -I { SUM | CPU | ALL } ] [ -u ] [ -P { cpu [,...] | ALL } ] [ -V ] [ interval [ count ] ]
        """
        params = kwarg['params']
        cmd = 'mpstat'
        if params.get('dut_discovery', False):
            cmd = 'mpstat -P ALL'
        # custom code here
        if 'cpu' in params:
            cmd = 'mpstat -P {}'.format(params['cpu'])
        return cmd

    def parse_show(self, command, output, *argv, **kwarg):
        """
        # 06:56:44 AM  CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest   %idle
        # 06:56:44 AM  all    0.50    0.05    0.07    0.02    0.00    0.00    0.00    0.00   99.36
        """
        if '\\n' in output:
            lines = output.split('\\n')[2:]
        else:
            lines = output.split('\n')[2:]
        if len(lines) < 2:
            return []
        names = RE_SPACES.sub(' ', lines[0]).strip().split(' ')[-10:]
        ret = []
        for record in lines[1:]:
            cpu_usage = {}
            values = RE_SPACES.sub(' ', record).strip().split(' ')[-10:]
            if len(values) != len(names):
                continue
            for i, name in enumerate(names):
                name = name[1:] if name[0] == '%' else name
                try:
                    k, v = name.lower(), float(values[i])
                except Exception as e:
                    k, v = name.lower(), 0
                cpu_usage[k] = v
            ret.append(cpu_usage)
        """
        Return in [{
           'usr' : 0.50,
           ...
        }]
        """
        return ret
