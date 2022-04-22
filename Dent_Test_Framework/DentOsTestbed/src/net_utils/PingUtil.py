"""Utility module for doing a ping to a specific target.
"""

import asyncio


class PingUtil(object):
    """Utility class for doing a ping to a specific target. The APIs of the class are async
    and the  calling application needs to have a running event loop to call the APIs of
    the module.
    """

    @staticmethod
    async def verify_ping(target, pkt_loss_treshold, dump=False):
        """Check if target is reachable by doing an ICMP ping.

        Args:
            str target: IP address (or) domain name of the target.
            int pkt_loss_treshold: Treshold of packet loss. If packet loss is below the treshold,
            the ping is considered failure

        Returns:
            True if ping is successful, False otherwise.

        """
        proc = await asyncio.create_subprocess_exec(
            "ping", "-c", "10", target, stdout=asyncio.subprocess.PIPE
        )
        pkt_stats = ""
        while True:
            line = await proc.stdout.readline()
            if line == b"":
                return False
            line = line.decode("utf8").rstrip()
            if dump:
                print(line)
            if "transmitted" in line:
                pkt_stats = line
        pkt_loss = next(
            (pkt_stat for pkt_stat in pkt_stats.split(",") if "packet loss" in pkt_stat), None
        )
        if pkt_loss:
            pkt_loss_percent = pkt_loss.strip().split(" ")[0].split(".")[0]
            pkt_loss_percent = int(pkt_loss_percent[: pkt_loss_percent.find("%")])
        else:
            pkt_loss_percent = -1
        return True if pkt_loss_percent <= pkt_loss_treshold else False
