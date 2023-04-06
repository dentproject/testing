# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# generated using file ./gen/model/dent/system/os/process.yaml
#
# DONOT EDIT - generated by diligent bots

from dent_os_testbed.discovery.Module import Module
from dent_os_testbed.lib.os.process import Process
class ProcessMod(Module):
    """
    """
    def set_process(self, src, dst):

        for i,process in enumerate(src):
            if 'pid' in process: dst[i].pid = process.get('pid')
            if 'command' in process: dst[i].command = process.get('command')
            if 'elapsed' in process: dst[i].elapsed = process.get('elapsed')
            if 'vsz' in process: dst[i].vsz = process.get('vsz')
            if 'mem' in process: dst[i].mem = process.get('mem')
            if 'time' in process: dst[i].time = process.get('time')
            if 'cpu_usage_user' in process: dst[i].cpu_usage_user = process.get('cpu_usage_user')
            if 'cpu_usage_system' in process: dst[i].cpu_usage_system = process.get('cpu_usage_system')
            if 'cpu_utilization' in process: dst[i].cpu_utilization = process.get('cpu_utilization')
            if 'memory_usage' in process: dst[i].memory_usage = process.get('memory_usage')
            if 'memory_utilization' in process: dst[i].memory_utilization = process.get('memory_utilization')


    async def discover(self):
        # need to get device instance to get the data from
        #
        for i, dut in enumerate(self.report.duts):
            if not dut.device_id: continue
            dev = self.ctx.devices_dict[dut.device_id]
            if dev.os == "ixnetwork" or not await dev.is_connected():
                print("Device not connected skipping process discovery")
                continue
            print("Running process Discovery on " + dev.host_name)
            out = await Process.show(
                input_data=[{dev.host_name: [{'dut_discovery':True}]}],
                device_obj={dev.host_name: dev},
                parse_output=True
            )
            if out[0][dev.host_name]["rc"] != 0:
                print(out)
                print("Failed to get process")
                continue
            if 'parsed_output' not in out[0][dev.host_name]:
                print("Failed to get parsed_output process")
                print (out)
                continue
            self.set_process(out[0][dev.host_name]["parsed_output"], self.report.duts[i].system.os.processes)
            print("Finished process Discovery on {} with {} entries".format(dev.host_name, len(self.report.duts[i].system.os.processes)))
