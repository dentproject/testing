import re

from dent_os_testbed.lib.os.linux.linux_process import LinuxProcess

RE_SPACES = re.compile("\s+")


class LinuxProcessImpl(LinuxProcess):
    """
    Process details by reading /proc/[pid]/status
    """

    def format_show(self, command, *argv, **kwarg):

        """
        Name:    sshd
        Umask:    0022
        State:    S (sleeping)
        Tgid:    2069
        Ngid:    0
        Pid:    2069
        PPid:    1
        TracerPid:    0
        Uid:    0    0    0    0
        Gid:    0    0    0    0
        FDSize:    64
        Groups:
        NStgid:    2069
        NSpid:    2069
        NSpgid:    2069
        NSsid:    2069
        VmPeak:       76124 kB
        VmSize:       76120 kB
        VmLck:           0 kB
        VmPin:           0 kB
        VmHWM:        2972 kB
        VmRSS:        2972 kB

        """
        if "dut_discovery" in kwarg["params"]:
            return "ps -eo pid,comm,etime,vsize,time,pmem,bsdtime"
        if "pid" not in kwarg["params"]:
            return "cat /proc/stat"
        cmd = "cat /proc/%s/status" % (kwarg["params"]["pid"])
        # custom code here

        return cmd

    def parse_show(self, command, output, *argv, **kwarg):

        """
        Name:    ksoftirqd/0
        Umask:    0022
        State:    S (sleeping)
        ...
        """
        proc_usage = []
        record = output[2:]
        if "\\n" in record:
            records = record.split("\\n")[:-1]
        else:
            records = record.split("\n")[:-1]
        if "PID" in records[0]:
            # got ps for all the process
            keys = RE_SPACES.sub(" ", records[0].lower()).strip().split(" ")
            for line in records[1:]:
                usage = {}
                line = RE_SPACES.sub(" ", line.lower()).strip().split(" ")
                for i, k in enumerate(keys):
                    k = k[1:] if k[0] == "%" else k
                    try:
                        usage[k] = int(line[i])
                    except:
                        usage[k] = line[i]
                proc_usage.append(usage)
        else:
            usage = {}
            for line in records:
                line = RE_SPACES.sub(" ", line).strip().split(" ")
                key = (
                    line[0].replace("(", "_").replace(")", "_").replace(":", "").replace("\\t", "")
                )
                try:
                    val = int(line[1])
                except:
                    # only look for integer
                    continue
                usage[key] = val
            proc_usage.append(usage)
        """
        Return in {
           'Umask' : 22,
           ...
        }
        """
        return proc_usage
