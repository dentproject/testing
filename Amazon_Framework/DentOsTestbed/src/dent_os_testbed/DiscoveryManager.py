""" Module to perform discovery related tasks
"""
import os

from dent_os_testbed.discovery.LocalRepository import LocalRepository
from dent_os_testbed.discovery.Module import DiscoveryRunner
from dent_os_testbed.discovery.ReportSchema import ReportSchema


class DiscoveryManager:
    """
    Implements discovery related APIs
    """

    def __init__(self, logger, args, config, devices, devices_dict):
        """
        Initializliation for DiscoveryManager

        Args:
            logger(Logger.Apploger): Logger
            args: Command line arguments for testbed
            config(dict): Testbed configuration
            devices(List): List of device instances
            devices_dict(dict): Mapping of device names to device instances
        """
        self.applog = logger
        self.args = args
        self.config = config
        self.devices_dict = devices_dict
        self.reports = LocalRepository(
            reportsDir=self.args.discovery_reports_dir,
            reportFromPath=ReportSchema.fromPath,
            log=logger,
        )
        self.devices = devices
        self.discoveryReport = None

    async def run(self):
        """
        Run discovery to determine the running config.
        """
        if self.config.get("discovery", False):
            self.applog.info("Discovery disabled in testbed config file, not running discovery")
            self.discoveryReport = None
        elif self.args.discovery_force:
            self.applog.info(
                "Discovery disabled through cli (-d option not passed), not running discovery"
            )
            self.discoveryReport = None
        else:
            self.discoveryReport = self._getDiscoveryReport()

        if self.discoveryReport is None:
            self.applog.info("generating a discovery report...")
            await self._discover()

        self.discoveryReport = self._getDiscoveryReport()

        if self.discoveryReport is None:
            self.applog.warning("cannot generate/retrieve a discovery report")
        return self.discoveryReport

    def _getDiscoveryReport(self):

        operator = None
        if self.args.discovery_operator:
            operator = self.args.discovery_operator
        elif "operator" in self.config:
            operator = self.config["operator"]

        topology = None
        if self.args.discovery_topology:
            topology = self.args.discovery_topology
        elif "topology" in self.config:
            topology = self.config["topology"]

        self.applog.info(f"Getting discovery resport for op:{operator}, topo:{topology}")
        return self.reports.getReport(operator=operator, topology=topology)
        # XXX rothcar -- possibly None if there are no matches

    async def _discover(self):
        """Trigger the discovery process and generate a new report."""

        discovery_path = self.args.discovery_path
        if not discovery_path:
            testdir = os.path.abspath(os.path.dirname(__file__))
            srcdir = os.path.abspath(os.path.join(testdir, "../"))
            discovery_path = srcdir + "/dent_os_testbed/discovery/modules/"
        self.applog.info("Running discovery module path " + discovery_path)

        runner = DiscoveryRunner(ctx=self, modulesDir=discovery_path, log=self.applog)

        devices = []
        for dev in self.devices:
            devices.append({"device_id": dev.host_name})
        rpt = ReportSchema({"duts": devices})
        rptData = rpt.asDict()

        operator = None
        if self.args.discovery_operator:
            operator = self.args.discovery_operator
        elif "operator" in self.config:
            operator = self.config["operator"]
        if "operator" is not None:
            rptData.setdefault("attributes", {})
            rptData["attributes"]["operator"] = operator

        topology = None
        if self.args.discovery_topology:
            topology = self.args.discovery_topology
        elif "topology" in self.config:
            topology = self.config["topology"]
        if "topology" is not None:
            rptData.setdefault("attributes", {})
            rptData["attributes"]["topology"] = topology

        rpt = await runner.discover(report=rpt)
        # XXX rothcar -- all modules must pass!

        self.reports.saveReport(rpt)
        self.reports.collectReports()
