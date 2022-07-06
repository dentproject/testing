import re

from testbed.lib.os.linux.linux_memory_usage import LinuxMemoryUsage

RE_SPACES = re.compile("\s+")


def camel_to_snake_case(str):
    res = [str[0].lower()]
    for c in str[1:]:
        if c in ("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            res.append("_")
            res.append(c.lower())
        else:
            res.append(c)

    return "".join(res)


class LinuxMemoryUsageImpl(LinuxMemoryUsage):
    """
    cat /proc/meminfo
    MemTotal:       15844588 kB
    MemFree:         1907880 kB
    MemAvailable:   14177180 kB
    Buffers:         2597832 kB
    Cached:          8131124 kB
    SwapCached:            0 kB
    Active:          8455648 kB
    Inactive:        3306968 kB

    """

    def format_show(self, command, *argv, **kwarg):

        """
        MemTotal:       15844588 kB
        MemFree:         1314612 kB
        MemAvailable:   14144464 kB
        Buffers:         2058212 kB
        Cached:          9129160 kB
        SwapCached:            0 kB
        Active:          9729612 kB
        Inactive:        2537912 kB
        Active(anon):    1080196 kB
        Inactive(anon):    99792 kB

        """
        cmd = "cat /proc/meminfo"
        # custom code here

        return cmd

    def parse_show(self, command, output, *argv, **kwarg):

        """
        MemTotal:       15844588 kB
        MemFree:         1314612 kB
        ...
        """
        if output[0] == "b":
            output = output[2:]
        mem_usage = {}
        record = output
        if "\\n" in record:
            records = record.split("\\n")[:-1]
        else:
            records = record.split("\n")[:-1]
        for line in records:
            line = RE_SPACES.sub(" ", line).strip().split(" ")
            key = line[0].replace("(", "_").replace(")", "_").replace(":", "")
            key = camel_to_snake_case(key)
            val = int(line[1])
            mem_usage[key] = val
        """
        Return in {
           'MemTotal' : 15844588,
           ...
        }
        """
        return mem_usage
