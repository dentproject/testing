"""
  Utility to monitor system resources
  1. CPU
  2. Memory
  3. Process
"""

import asyncio
import threading
import time

from dent_os_testbed.lib.os.cpu_usage import CpuUsage
from dent_os_testbed.lib.os.memory_usage import MemoryUsage
from dent_os_testbed.lib.os.process import Process


class PerfValueException(ValueError):
    pass


class PerfBase(object):
    def __init__(self, *args, **kwargs):
        self._device = kwargs['device']
        self._type = kwargs['type']
        self._data = []
        self._threshold = kwargs['thresholds'].get(self._type, {})
        self._max_records = kwargs['max_records']

    def set_thresholds(self, thresholds):
        if self._type in thresholds:
            self._threshold = thresholds[self._type]

    def get_thresholds(self, thresholds):
        if self._type in thresholds:
            thresholds[self._type] = self._threshold

    def add_data(self, data):
        self._data.append(data)
        if len(self._data) > self._max_records:
            # get rid of the oldest item
            self._data.pop(0)


class PerfCpu(PerfBase):
    def __init__(self, *args, **kwargs):
        super(PerfCpu, self).__init__(*args, **kwargs)

    def run(self):
        output = CpuUsage.show(
            input_data=[
                {
                    self._device.host_name: [{}],
                }
            ],
            device_obj={self._device.host_name: self._device},
            parse_output=True,
        )
        try:
            ctime = time.strftime('%X %x %Z')
            record = output[0][self._device.host_name]['parsed_output']
            if self._threshold:
                self.analyze_data(ctime, record, self._threshold)
            self.add_data((ctime, record))
        except Exception as e:
            print(str(e))
            pass

    def analyze_data(self, time, record, threshold):
        # 1. check for analomies using threshold
        # 06:56:44 AM  CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest   %idle
        # 06:56:44 AM  all    0.50    0.05    0.07    0.02    0.00    0.00    0.00    0.00   99.36
        for k, v in record[0].items():
            if k in threshold:
                if v < threshold[k][0] or v > threshold[k][1]:
                    raise PerfValueException(
                        'Cpu {} Usage out of range usage {} threshold {} at {}'.format(
                            k, v, threshold[k], time
                        )
                    )

    def analyze(self, thresholds):
        threshold = thresholds.get('CPU', self._threshold)
        for time, record in self._data:
            self.analyze_data(time, record, threshold)


class PerfMemory(PerfBase):
    def __init__(self, *args, **kwargs):
        super(PerfMemory, self).__init__(*args, **kwargs)

    def run(self):
        output = MemoryUsage.show(
            input_data=[
                {
                    self._device.host_name: [{}],
                }
            ],
            device_obj={self._device.host_name: self._device},
            parse_output=True,
        )
        try:
            ctime = time.strftime('%X %x %Z')
            record = output[0][self._device.host_name]['parsed_output']
            if self._threshold:
                self.analyze_data(ctime, record, self._threshold)
            self.add_data((ctime, record))
        except Exception as e:
            print(str(e))
            pass

    def analyze_data(self, time, record, threshold):
        for key, val in record.items():
            if key in threshold:
                if val < threshold[key][1] or val > threshold[key][1]:
                    raise PerfValueException(
                        'Memory {} Usage(in kB) out of range usage {} threshold {} at {}'.format(
                            key, val, threshold[key], time
                        )
                    )

    def analyze(self, thresholds):
        threshold = thresholds.get('Memory', self._threshold)
        for time, record in self._data:
            self.analyze_data(time, record, threshold)


class PerfProcesses(PerfBase):
    critical_processes = [
        'sshd',
        'zebra',
        'bfpd',
        'watchfrr',
        'staticd',
        'tfpd',
    ]

    def __init__(self, *args, **kwargs):
        super(PerfProcesses, self).__init__(*args, **kwargs)
        self._data = dict()
        for name in PerfProcesses.critical_processes:
            self._data[name] = {}
            self._data[name]['pid'] = None
            self._data[name]['data'] = []

    def construct_command(self):
        return 'ps -eo pid,comm'

    def run(self):
        # 1. get the PID of the process
        cmd = self.construct_command()
        rc, lines = self._device.run_command(cmd)
        for line in lines.split('\\n'):
            words = line.strip().split(' ')
            if len(words) != 2:
                continue
            pid, name = words[0], words[1]
            # if this is a process to monitor
            if name in PerfProcesses.critical_processes:
                self._data[name]['pid'] = pid
        # 2. get the stats for the process
        for proc in PerfProcesses.critical_processes:
            if not self._data[proc]['pid']:
                continue
            pid = self._data[proc]['pid']
            output = Process.show(
                input_data=[
                    {
                        self._device.host_name: [{'pid': pid}],
                    }
                ],
                device_obj={self._device.host_name: self._device},
                parse_output=True,
            )
            try:
                ctime = time.strftime('%X %x %Z')
                record = output[0][self._device.host_name]['parsed_output']
                if pid in self._threshold or 'all' in self._threshold:
                    self.analyze_data(
                        proc, ctime, record, self._threshold.get(pid, self._threshold['all'])
                    )
                # save for future processing.
                self._data[proc]['data'].append((ctime, record))
                if len(self._data[proc]['data'] > self._max_records):
                    self._data[proc]['data'].pop(0)
            except Exception as e:
                print(str(e))
                pass

    def analyze_data(self, name, time, record, threshold):
        for key, val in record[0].items():
            if key in threshold:
                if val < threshold[key][0] or val > threshold[key][1]:
                    raise PerfValueException(
                        'Process {} {} Usage out of range usage {} threshold {} at {}'.format(
                            name, key, val, threshold[key], time
                        )
                    )

    def analyze(self, thresholds):
        if thresholds:
            threshold = thresholds['Process']
        else:
            threshold = self._threshold
        for name, proc in self._data.items():
            if name not in threshold:
                # if there no process name then try for all
                if 'all' in threshold:
                    threshold = threshold['all']
                else:
                    continue
            else:
                threshold = threshold[name]
            for time, record in proc['data']:
                self.analyze_data(name, time, record, threshold)


class PerfRunner(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(PerfRunner, self).__init__()
        self._event = threading.Event()
        self._event.set()
        self.device = kwargs['device']
        self._frequency = kwargs['frequency']
        self._max_records = kwargs['max_records']
        self._thresholds = kwargs['thresholds']
        self._run = True
        self._objects = []
        self._objects.append(
            PerfCpu(
                device=self.device,
                type='CPU',
                thresholds=self._thresholds,
                max_records=self._max_records,
            )
        )
        self._objects.append(
            PerfMemory(
                device=self.device,
                type='Memory',
                thresholds=self._thresholds,
                max_records=self._max_records,
            )
        )
        self._objects.append(
            PerfProcesses(
                device=self.device,
                type='Process',
                thresholds=self._thresholds,
                max_records=self._max_records,
            )
        )
        self._loop = asyncio.new_event_loop()

    def set_thresholds(self, thresholds):
        for o in self._objects:
            o.set_thresholds(thresholds)

    def get_thresholds(self, thresholds):
        for o in self._objects:
            o.get_thresholds(thresholds)

    def analyze(self, thresholds=None):
        for o in self._objects:
            o.analyze(thresholds)

    def pause(self):
        self._event.clear()

    def resume(self):
        self._event.set()

    def stop(self):
        self._run = False

    def run(self):
        asyncio.set_event_loop(self._loop)
        while self._run:
            self._event.wait()
            if self.device.is_connected():
                for o in self._objects:
                    o.run()
            time.sleep(self._frequency)


class PerfUtil(object):
    def __init__(self, *args, **kwargs):
        devices = kwargs['devices']
        frequency = kwargs.get('frequency', 10)
        max_records = kwargs.get('max_records', 1000)
        thresholds = kwargs.get('thresholds', {})
        self.threads = {}
        for device in devices:
            self.threads[device.host_name] = PerfRunner(
                device=device, frequency=frequency, max_records=max_records, thresholds=thresholds
            )

    def start_monitoring(self, device=None):
        if device:
            self.threads[device.host_name].start()
        else:
            for _, t in self.threads.items():
                t.start()

    def analyze(self, device=None, thresholds={}):
        if device:
            self.threads[device.host_name].pause()
            self.threads[device.host_name].analyze(thresholds)
            self.threads[device.host_name].resume()
        else:
            for _, t in self.threads.items():
                t.pause()
                t.analyze(thresholds)
                t.resume()

    def set_thresholds(self, device=None, thresholds={}):
        if device:
            self.threads[device.host_name].set_thresholds(thresholds)
        else:
            for _, t in self.threads.items():
                t.set_thresholds(thresholds)

    def get_thresholds(self, device=None, thresholds={}):
        if device:
            self.threads[device.host_name].get_thresholds(thresholds)
        else:
            for _, t in self.threads.items():
                t.get_thresholds(thresholds)

    def stop_monitoring(self, device=None):
        if device:
            self.threads[device.host_name].stop()
        else:
            for _, t in self.threads.items():
                t.stop()

    def resume(self, device=None):
        if device:
            self.threads[device.host_name].resume()
        else:
            for _, t in self.threads.items():
                t.resume()

    def pause(self, device=None):
        if device:
            self.threads[device.host_name].pause()
        else:
            for _, t in self.threads.items():
                t.pause()
