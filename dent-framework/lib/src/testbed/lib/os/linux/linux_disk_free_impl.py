from testbed.lib.os.linux.linux_disk_free import LinuxDiskFree


class LinuxDiskFreeImpl(LinuxDiskFree):
    """
    Disk free inforamtion
    """

    def format_show(self, command, *argv, **kwarg):
        """
        > df -h
        Filesystem      Size  Used Avail Use% Mounted on
        devtmpfs        1.0M     0  1.0M   0% /dev
        /dev/sda4        24G  1.2G   22G   6% /
        /dev/sda3       976M  306M  603M  34% /mnt/onl/images
        /dev/sda1       123M   29M   89M  25% /mnt/onl/boot
        /dev/sda2       120M  1.6M  110M   2% /mnt/onl/config
        tmpfs           3.9G     0  3.9G   0% /dev/shm
        tmpfs           3.9G  8.9M  3.9G   1% /run
        tmpfs           5.0M     0  5.0M   0% /run/lock
        tmpfs           3.9G     0  3.9G   0% /sys/fs/cgroup
        ....

        """
        params = kwarg["params"]
        cmd = "df "
        ############# Implement me ################

        return cmd

    def parse_show(self, command, output, *argv, **kwarg):
        """
        > df -h
        Filesystem      Size  Used Avail Use% Mounted on
        devtmpfs        1.0M     0  1.0M   0% /dev
        /dev/sda4        24G  1.2G   22G   6% /
        /dev/sda3       976M  306M  603M  34% /mnt/onl/images
        /dev/sda1       123M   29M   89M  25% /mnt/onl/boot
        /dev/sda2       120M  1.6M  110M   2% /mnt/onl/config
        tmpfs           3.9G     0  3.9G   0% /dev/shm
        tmpfs           3.9G  8.9M  3.9G   1% /run
        tmpfs           5.0M     0  5.0M   0% /run/lock
        tmpfs           3.9G     0  3.9G   0% /sys/fs/cgroup
        ....

        """
        disk = []
        records = output.split("\n")[1:]
        for r in records:
            r = r.strip()
            if not r:
                continue
            tokens = r.split()
            filesystem = tokens.pop(0)
            size = int(tokens.pop(0))
            used = int(tokens.pop(0))
            available = int(tokens.pop(0))
            use_percentage = int(tokens.pop(0)[:-1])
            mounted_on = tokens.pop(0)
            disk.append(
                {
                    "filesystem": filesystem,
                    "size": size,
                    "used": used,
                    "available": available,
                    "use_percentage": use_percentage,
                    "mounted_on": mounted_on,
                }
            )

        return disk
