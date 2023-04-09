import time

from dent_os_testbed.Device import DeviceType


class AttrSetAndUnsetMeta(object):
    """Base metadata type for set-and-unset tests."""

    @staticmethod
    def cls_name(obj=None):
        return 'undefined'

    @staticmethod
    def set_fn(obj=None):
        return lambda: True

    @staticmethod
    def show_fn(obj=None):
        return lambda: True

    @staticmethod
    def dev_objects(obj=None):
        raise NotImplementedError

    @staticmethod
    def dev_object_filter(obj=None):
        raise NotImplementedError

    @staticmethod
    def dev_object_set_params(obj=None):
        raise NotImplementedError

    @staticmethod
    def dev_object_reset_params(obj=None):
        raise NotImplementedError

    @staticmethod
    def dev_object_show_params(obj=None):
        raise NotImplementedError


class AttrSetAndUnsetBase(object):
    """Base class for set-and-unset test."""

    meta = AttrSetAndUnsetMeta

    async def run_test(self, testbed):

        if testbed.args.is_provisioned:
            testbed.applog.info('Skipping test since on provisioned setup')
            return

        if not testbed.discovery_report:
            testbed.applog.info(
                'Discovery report not present, +' 'skipping run_test in AttrSetAndUnsetBase'
            )
            return

        for i, dev in enumerate(testbed.discovery_report.duts):
            if dev.device_id not in testbed.devices_dict:
                testbed.applog.info('Skipping device {}'.format(dev.device_id))
                continue
            device = testbed.devices_dict[dev.device_id]
            if device.type == DeviceType.TRAFFIC_GENERATOR:
                continue
            dev_objects = self.meta.dev_objects(dev)

            device.applog.info(
                '{} has {} {}(s)'.format(
                    testbed.discovery_report.duts[i].device_id,
                    len(dev_objects),
                    self.meta.cls_name(),
                )
            )
            if not await device.is_connected():
                device.applog.info('Device not connected skipping')
                continue
            for obj in dev_objects.filter(fn=self.meta.dev_object_filter):
                device.applog.info('Settting %s', self.meta.cls_name())
                params = self.meta.dev_object_set_params(obj)
                await self.meta.set_fn()(input_data=[{dev.device_id: [params]}])

                time.sleep(4)
                device.applog.info('Show %s', self.meta.cls_name())
                params = self.meta.dev_object_show_params(obj)
                await self.meta.show_fn()(input_data=[{dev.device_id: [params]}])

                device.applog.info('Reseting %s', self.meta.cls_name())
                params = self.meta.dev_object_reset_params(obj)
                await self.meta.set_fn()(input_data=[{dev.device_id: [params]}])

                time.sleep(4)
                device.applog.info('Show %s', self.meta.cls_name())
                params = self.meta.dev_object_show_params(obj)
                await self.meta.show_fn()(input_data=[{dev.device_id: [params]}])
