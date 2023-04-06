# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# generated using file ./gen/model/dent/system/os/cpu.yaml
#
# DONOT EDIT - generated by diligent bots

from dent_os_testbed.discovery.Module import Module
from dent_os_testbed.lib.os.cpu_usage import CpuUsage
class CpuUsageMod(Module):
    """
    """
    def set_cpu_usage(self, src, dst):

        for i,cpu_usage in enumerate(src):
            if 'cpu' in cpu_usage: dst[i].cpu = cpu_usage.get('cpu')
            if 'usr' in cpu_usage: dst[i].usr = cpu_usage.get('usr')
            if 'nice' in cpu_usage: dst[i].nice = cpu_usage.get('nice')
            if 'sys' in cpu_usage: dst[i].sys = cpu_usage.get('sys')
            if 'iowait' in cpu_usage: dst[i].iowait = cpu_usage.get('iowait')
            if 'irq' in cpu_usage: dst[i].irq = cpu_usage.get('irq')
            if 'soft' in cpu_usage: dst[i].soft = cpu_usage.get('soft')
            if 'steal' in cpu_usage: dst[i].steal = cpu_usage.get('steal')
            if 'guest' in cpu_usage: dst[i].guest = cpu_usage.get('guest')
            if 'idle' in cpu_usage: dst[i].idle = cpu_usage.get('idle')


    async def discover(self):
        # need to get device instance to get the data from
        #
        for i, dut in enumerate(self.report.duts):
            if not dut.device_id: continue
            dev = self.ctx.devices_dict[dut.device_id]
            if dev.os == "ixnetwork" or not await dev.is_connected():
                print("Device not connected skipping cpu_usage discovery")
                continue
            print("Running cpu_usage Discovery on " + dev.host_name)
            out = await CpuUsage.show(
                input_data=[{dev.host_name: [{'dut_discovery':True}]}],
                device_obj={dev.host_name: dev},
                parse_output=True
            )
            if out[0][dev.host_name]["rc"] != 0:
                print(out)
                print("Failed to get cpu_usage")
                continue
            if 'parsed_output' not in out[0][dev.host_name]:
                print("Failed to get parsed_output cpu_usage")
                print (out)
                continue
            self.set_cpu_usage(out[0][dev.host_name]["parsed_output"], self.report.duts[i].system.os.cpu)
            print("Finished cpu_usage Discovery on {} with {} entries".format(dev.host_name, len(self.report.duts[i].system.os.cpu)))
