from dent_os_testbed.Device import DeviceType


class DeleteAndAddMeta(object):

    """Base metadata type for delete-and-add tests."""

    @staticmethod
    def cls_name(obj=None):
        return 'undefined'

    @staticmethod
    def delete_fn(obj=None):
        return lambda: True

    @staticmethod
    def add_fn(obj=None):
        return lambda: True

    @staticmethod
    def show_fn(obj=None):
        return lambda: True

    @staticmethod
    def device_objects(obj=None):
        raise NotImplementedError

    @staticmethod
    def device_object_filter(obj=None):
        raise NotImplementedError


class DeleteAndAddBase(object):
    meta = DeleteAndAddMeta
    """Setup if required, enable performance, go through discovered objects and
    delete them and add them back again.
    """

    async def run_test(self, testbed):

        if not testbed.discovery_report:
            testbed.applog.info('Discovery report is none, skipping run_test of DeleteAndAddBase')
            return

        for i, dev in enumerate(testbed.discovery_report.duts):
            if dev.device_id not in testbed.devices_dict:
                device.applog.info('Skipping device {}'.format(dev.device_id))
                continue
            device = testbed.devices_dict[dev.device_id]
            if device.type == DeviceType.TRAFFIC_GENERATOR:
                continue
            dev_objects = self.meta.device_objects(dev)
            device.applog.info(
                '{} has {} {}'.format(
                    testbed.discovery_report.duts[i].device_id,
                    len(dev_objects),
                    self.meta.cls_name(),
                )
            )
            if not await device.is_connected():
                device.applog.info('Device not connected skipping')
                continue
            for obj in dev_objects.filter(fn=self.meta.device_object_filter):
                device.applog.info('Deleting/Adding ' + self.meta.cls_name())
                out = await self.meta.delete_fn()(input_data=[{dev.device_id: [obj.__dikt__]}])

                device.applog.info('Show ' + self.meta.cls_name())
                out = await self.meta.show_fn()(input_data=[{dev.device_id: [obj.__dikt__]}])

                device.applog.info('Add ' + self.meta.cls_name())
                out = await self.meta.add_fn()(input_data=[{dev.device_id: [obj.__dikt__]}])

                device.applog.info('Show ' + self.meta.cls_name())
                out = await self.meta.show_fn()(input_data=[{dev.device_id: [obj.__dikt__]}])
