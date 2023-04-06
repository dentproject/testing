"""Module.py

Base class for testbed discovery modules.
"""

import sys
import os
import logging
import copy
import io
import importlib
import importlib.util
import operator
import asyncio

from dent_os_testbed.discovery.Report import Report

srcdir = os.path.dirname(os.path.abspath(__file__))
MODULES_DIR = os.path.join(srcdir, 'modules')

class DiscoveryFailed(Exception):
    def __init__(self, msg, info, report):
        Exception.__init__(self, msg)
        self.info = info
        self.report = report

class Module(object):

    PRIORITY = 100

    def __init__(self, ctx, report, log=None):
        self.ctx = ctx
        self.report = report
        self.log = log or logging.getLogger(self.__class__.__name__)

    async def discover(self):
        """Base class for discovery modules.

        Read state from 'self.rpt',
        write state to dict keys in 'self.rpt.asDict()'
        """
        raise NotImplementedError('this is a base class')

    async def do_discovery(self):

        rpt, self.report = self.report, self.report.clone(copy.deepcopy(self.report.asDict()))
        try:
            await self.discover()
        except:
            self.report = rpt
            raise

class DiscoveryRunner(object):
    """Gather and execute discovery modules.

    XXX TODO -- need some sort of way to filter/disable modules
    """

    def __init__(self, ctx=None, modulesDir=MODULES_DIR, log=None):
        self.ctx = ctx
        self.modulesDir = modulesDir
        self.log = log or logging.getLogger(self.__class__.__name__)

    async def discover(self, report=None, force=False):

        if report is None:
            report = Report.fromData({})

        dcl = []
        for e in os.listdir(self.modulesDir):
            if e == '__init__.py': continue
            if not e.endswith('.py'): continue

            b = os.path.splitext(e)[0]
            n = 'dent_os_testbed.discovery.%s' % b
            p = os.path.join(self.modulesDir, e)

            self.log.info('importing %s', n)
            print('importing %s', n)

            spec = importlib.util.spec_from_file_location(n, p)
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
            except Exception as ex:
                self.log.exception('import failed')
                return report

            for k, v in module.__dict__.items():

                if not isinstance(v, type): continue
                if Module is v: continue
                if Module not in v.mro(): continue

                dcl.append((k, v,))

        print(dcl)

        def _fn(item):
            k, dc = item
            return dc.PRIORITY

        for k, dc in sorted(dcl, key=_fn):
            dinst = dc(self.ctx, report, log=self.log.getChild(k))
            try:
                await dinst.do_discovery()
            except Exception as ex:
                if force:
                    msg = 'discovery failed for %s' % self.__class__.__name__
                    raise DiscoveryFailed(msg,
                                          sys.exc_info(),
                                          report)
                else:
                    raise
            report = dinst.report

        return report

def discovery_main():
    logging.basicConfig()
    logger = logging.getLogger('discover')
    logger.setLevel(logging.DEBUG)
    rpt = Report.fromData({})
    runner = DiscoveryRunner(log=logger)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(runner.discover(rpt))
    sys.exit(0)


if __name__ == '__main__':
    discovery_main()
