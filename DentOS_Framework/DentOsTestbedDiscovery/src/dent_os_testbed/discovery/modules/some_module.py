"""some_module.py

"""

from dent_os_testbed.discovery.Module import Module

class SomeMod(Module):

    async def discover(self):
        self.log.info("Hello from some_module.SomeMod!")
