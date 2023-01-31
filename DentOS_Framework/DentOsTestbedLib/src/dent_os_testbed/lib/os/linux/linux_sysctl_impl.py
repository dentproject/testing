from dent_os_testbed.lib.os.linux.linux_sysctl import LinuxSysctl 
class LinuxSysctlImpl(LinuxSysctl):
    """
        system kernel attributes manager
    """
    def format_get(self, command, *argv, **kwarg):
        """
        Get the attribute value
        
        """
        params = kwarg["params"]
        cmd = "sysctl "
        if "options" in params:
            cmd += params["options"]
        
        cmd += " {}".format(params["variable"])
        ############# Implement me ################
        
        return cmd
        
    def parse_get(self, command, output, *argv, **kwarg):
        """
        Get the attribute value
        
        """
        values = dict()
        for line in output.splitlines():
            var, value = line.split(" = ")
            values[var] = value
        return values
        
    def format_set(self, command, *argv, **kwarg):
        """
        Set the attribute value
        
        """
        params = kwarg["params"]
        cmd = "sysctl "
        if "options" in params:
            cmd += params["options"]
        
        cmd += " {}={}".format(params["variable"], params["value"])
        ############# Implement me ################
        
        return cmd
        
    def parse_set(self, command, output, *argv, **kwarg):
        """
        Set the attribute value
        
        """
        if "sysctl:" in output:
            raise ValueError("Error while setting sysctl value:\n{}".format(output))
        return output.strip()
        
