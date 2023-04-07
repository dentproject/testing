"""LocalRepository.py

Implement the local repository of discovery reports
on a single testbed server.
"""

import logging
import sys
import os
import time
import tempfile
import io
import json

from dent_os_testbed.discovery.constants import (
    REPORTS_DIR,
    REPORTS_HORIZON,
    REPORTS_SAVE_MIN,
    REPORTS_SAVE_MAX)

from dent_os_testbed.discovery.Report import Report


class LocalRepository(object):

    def __init__(self,
                 reportsDir=REPORTS_DIR,
                 maxAge=None,
                 minSave=None, maxSave=None,
                 reportFromPath=Report.fromPath,
                 log=None):
        self.log = log or logging.getLogger(self.__class__.__name__)

        self.reportsDir = reportsDir or self.getReportsDir()
        if not os.path.isdir(reportsDir):
            self.log.debug('+ /bin/mkdir -p %s', self.reportsDir)
            os.makedirs(self.reportsDir)
            # Whee, moved from 'shutil' to 'os' in PY3

        self.maxAge = maxAge
        if self.maxAge is None:
            self.maxAge = REPORTS_HORIZON

        self.minSave = minSave
        if self.minSave is None:
            self.minSave = REPORTS_SAVE_MIN

        self.maxSave = maxSave
        if self.maxSave is None:
            self.maxSave = REPORTS_SAVE_MAX

        self.reportFromPath = reportFromPath

        # dumb index for a directory-backed collection
        # of test reports, could use e.g. sqlite for this

        self.reports = []
        # (path, report) for all reports

        self.reportsPerTopology = {}
        # (path, report) for reports keyed by topo

        self.reportsPerOperator = {}
        # (path, report) for reports keyed by oper

        self.reportsPerTopologyOperator = {}
        # (path, report) for reports keyed by (topo, oper)

        self.collectReports()
        # collect reports on the spot,
        # XXX roth -- can defer this to a timed task

    def getReportsDir(self):
        """Generate the default reportsDir."""

        if os.getuid() == 0:
            return REPORTS_DIR

        if sys.platform == 'darwin':
            return os.path.expanduser('~/Library/Caches/com.amazon.netprod/testbed/reports')

        # assume linux
        dataDir = os.path.expanduser('~/.local/share')
        dataDir = os.environ.get('XDG_DATA_HOME', dataDir)
        return os.path.join(dataDir, 'com.amazon.netprod/testbed/reports')

    def collectReports(self):
        """Gather all of the reports in the local store.

        Sort all of the reports on each scan.
        - could use a DB for this
        - could use e.g. heapq to speed up scan a bit
        """

        perAll = []
        perTopo = {}
        perOper = {}
        perTopoOper = {}

        for el in os.listdir(self.reportsDir):
            p = os.path.join(self.reportsDir, el)
            if not p.endswith('.json'):
                self.log.warning('unrecognized file %s', el)
                continue

            try:
                rpt = self.reportFromPath(p)
            except ValueError as ex:
                self.log.warning('invalid JSON in %s: %s',
                                 p, str(ex))
                continue

            ts = os.path.getmtime(p)
            # on the local testbed, JSON mtime == report generation time

            oper = rpt.operator
            topo = rpt.topology

            perAll.append((ts, p, rpt,))
            if topo is not None:
                perTopo.setdefault(topo, [])
                perTopo[topo].append((ts, p, rpt,))
            if oper is not None:
                perOper.setdefault(oper, [])
                perOper[oper].append((ts, p, rpt,))
            if topo is not None and oper is not None:
                k = (topo, oper,)
                perTopoOper.setdefault(k, [])
                perTopoOper[k].append((ts, p, rpt,))

        self.log.info('collected %d reports', len(perAll))

        # collate the reports
        self.reports = [x[1:3] for x in sorted(perAll)]
        self.reportsPerTopology = {}
        for topo, coll in perTopo.items():
            self.reportsPerTopology[topo] = [x[1:3] for x in sorted(coll)]
        self.reportsPerOperator = {}
        for oper, coll in perOper.items():
            self.reportsPerOperator[oper] = [x[1:3] for x in sorted(coll)]
        self.reportsPerTopologyOperator = {}
        for topoOper, coll in perTopoOper.items():
            self.reportsPerTopologyOperator[topoOper] = [x[1:3] for x in sorted(coll)]

    def getReports(self,
                   topology=None, operator=None,
                   maxReports=1,
                   before=None, after=None):
        """Retrieve the latest report for this topology and/or operator.

        Returns a list of (timestamp, report) based on the query specifiers.
        """

        if topology is not None and operator is not None:
            k = (topology, operator,)
            coll = list(self.reportsPerTopologyOperator.get(k, []))
        elif topology is not None:
            coll = list(self.reportsPerTopology.get(topology, []))
        elif operator is not None:
            coll = list(self.reportsPerOperator.get(operator, []))
        else:
            coll = list(self.reports)

        reports = []
        while True:
            if not coll: break
            if len(reports) >= maxReports: break

            p, rpt = coll.pop(-1)
            if not os.path.exists(p):
                self.log.warning('missing report %s', p)
                continue
            ts = os.path.getmtime(p)

            if after is not None and ts <= after:
                break
            # reports are in order by time,
            # so if we are moving backwards and cross 'after'
            # we can stop immediately

            if before is not None and ts >= before:
                continue
            # still looking for a report before this

            reports.insert(0, (rpt, ts,))

        if not reports:
            self.log.warning('no reports available for the query'
                             ' topology=%s'
                             ' operator=%s'
                             ' before=%s'
                             ' after=%s'
                             ' maxReports=%d',
                             topology, operator, before, after, maxReports)

        return reports

    def getReport(self,
                  topology=None, operator=None,
                  maxReports=1,
                  before=None, after=None):
        """Get the latest report for the given specifiers."""
        l = self.getReports(topology=topology, operator=operator,
                            before=before, after=after)
        return l[0][0] if l else None

    def expireReports(self):
        """Expire out old reports.

        Uploading reports is a separate issue and is ignored here.
        """

        past = time.time() - self.maxAge
        cnt = 0

        def _trim(coll):
            """Trim unneeded items.

            - save at least minSave
            - drop items beyond minSave that are too old
            - drop items beyond maxSave regardless of age
            """
            while True:
                if len(coll) <= self.minSave:
                    break
                p, rpt = coll[0]

                if not os.path.exists(p):
                    coll.pop(0)
                    continue
                # maybe we deleted this one out of band

                ts = os.path.getmtime(p)
                if ts < past or len(coll) > self.maxSave:
                    self.log.debug('+ /bin/rm %s', p)
                    os.unlink(p)
                else:
                    break

        for k, coll in self.reportsPerTopologyOperator.items():
            _trim(coll)

        for topo, coll in self.reportsPerTopology.items():
            coll = [x for x in coll if x[1].operator is None]
            _trim(coll)
        # trim per-topology, but only if the operator is unset

        for oper, coll in self.reportsPerOperator.items():
            coll = [x for x in coll if x[1].topology is None]
            _trim(coll)
        # trim per-operator, but only if the topology is unset

        coll = [x for x in self.reports if x[1].operator is None and x[1].topology is None]
        _trim(coll)
        # trim reports with no topology, no operator

        # re-generate the collections since we deleted them willy-nilly
        # and didn't keep the collections in sync
        self.collectReports()

    def saveReport(self, rpt):
        """Save a report object into the local repository.

        Returns the pathname for the persisted report.
        """

        salt = next(iter(tempfile._get_candidate_names()))
        ts = int(time.time())

        if rpt.topology and rpt.operator:
            base = ('r-%d-t-%s-o-%s-%s.json' % (ts, rpt.topology, rpt.operator, salt,))
        elif rpt.topology:
            base = ('r-%d-t-%s-%s.json' % (ts, rpt.topology, salt,))
        elif rpt.operator:
            base = ('r-%d-o-%s-%s.json' % (ts, rpt.operator, salt,))
        else:
            base = ('r-%d-%s.json' % (ts, salt,))

        path = os.path.join(self.reportsDir, base)
        with io.open(path, 'wt') as fd:
            json.dump(rpt.asDict(), fd)
        os.utime(path, (ts, ts,))

        return path
