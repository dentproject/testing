from dent_os_testbed.lib.os.sysctl import Sysctl


class RecoverableSysctl(Sysctl):

    saved_values = dict()

    async def set(*argv, **kwarg):
        devices = kwarg['input_data']
        kwarg['parse_output'] = True
        saved_options = {}
        for device in devices:
            for device_name in device:
                saved_options[device_name] = []
                for command in device[device_name]:
                    saved_options[device_name].append(command.get("options", ""))
                    command["options"] = ""
        out = await Sysctl.get(*argv, **kwarg)
        for device in devices:
            for device_name in device:
                if device_name in RecoverableSysctl.saved_values:
                    for variable, value in out[0][device_name]['parsed_output'].items():
                        if variable not in RecoverableSysctl.saved_values[device_name]:
                            RecoverableSysctl.saved_values[device_name][variable] = value
                else:
                    RecoverableSysctl.saved_values[device_name] = out[0][device_name]['parsed_output']
        for device in devices:
            for device_name in device:
                for i, command in enumerate(device[device_name]):
                    command["options"] = saved_options[device_name][i]
                saved_options[device_name] = []
        return await Sysctl.set(*argv, **kwarg)

    async def recover():
        for device_name, config in RecoverableSysctl.saved_values.items():
            await Sysctl.set(input_data=[{
                device_name : [{
                    'variable': variable,
                    'value': value,
                } for variable, value in config.items()],
            }])
        RecoverableSysctl.saved_values.clear()
