from enum import Enum
import asyncio
import random
import time


class PortRole(Enum):
    MASTER = 0
    ALTERNATE = 1
    ROOT = 2
    DESIGNATED = 3


def get_rand_mac(mask='xx:xx:xx:xx:xx:xx'):
    return ''.join([n.lower().replace('x', f'{random.randint(0, 15):x}') for n in mask])


async def poll(dent_dev, fn, *args, timeout=60, interval=10, **kwargs):
    start = time.time()
    dent_dev.applog.info(f'Start polling {timeout = } {interval = }')
    while time.time() < start + timeout:
        try:
            await fn(*args, **kwargs)
        except AssertionError as e:
            dent_dev.applog.info(f'Polling failed. Trying again in {interval}s\n{e}')
            await asyncio.sleep(interval)
        else:
            dent_dev.applog.info(f'Poll successful after {int(time.time() - start)}s')
            break
    else:
        raise TimeoutError(f'Polling failed after {int(time.time() - start)}s')
