from enum import Enum
import random


class PortRole(Enum):
    MASTER = 0
    ALTERNATE = 1
    ROOT = 2
    DESIGNATED = 3


def get_rand_mac(mask='xx:xx:xx:xx:xx:xx'):
    return ''.join([n.lower().replace('x', f'{random.randint(0, 15):x}') for n in mask])
