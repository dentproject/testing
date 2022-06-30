from dent_os_testbed.lib.tc.linux.linux_tc_filter import LinuxTcFilter


class LinuxTcFilterImpl(LinuxTcFilter):
    """"""

    def format_modify(self, command, *argv, **kwarg):
        """
        tc [ OPTIONS ] filter [ add | change | replace | delete | get ] dev DEV  [  parent
        qdisc-id  | root ] [ handle filter-id ] protocol protocol prio priority filtertype
        [ filtertype specific parameters ] flowid flow-id
        tc [ OPTIONS ] filter [ add | change | replace | delete | get ] block  BLOCK_INDEX
        [  handle filter-id ] protocol protocol prio priority filtertype [ filtertype spe
        cific parameters ] flowid flow-id

        """
        params = kwarg["params"]
        cmd = "tc {} filter {} ".format(params.get("options", ""), command)
        if "dev" in params:
            cmd += "dev {} ".format(params.get("dev"))
        if "block" in params:
            cmd += "block {} ".format(params.get("block"))
        if "direction" in params:
            cmd += "{} ".format(params["direction"])
        if "protocol" in params:
            cmd += "protocol {} ".format(params["protocol"])
        if "handle" in params:
            cmd += "handle {} ".format(params["handle"])
        if "pref" in params:
            cmd += "pref {} ".format(params["pref"])
        if "chain" in params:
            cmd += "chain {} ".format(params["chain"])
        if "filtertype" in params:
            if type(params["filtertype"]) is dict:
                cmd += "flower "
                for field, value in params["filtertype"].items():
                    cmd += "{} {} ".format(field, value)
        if "action" in params:
            if "police" in params["action"]:
                cmd += "action police "
                for field, value in params["action"]["police"].items():
                    cmd += "{} {} ".format(field, value)
            else:
                cmd += "action {} ".format(params["action"])
        return cmd

    def format_show(self, command, *argv, **kwarg):
        """
        tc [ OPTIONS ] filter show dev DEV
        tc [ OPTIONS ] filter show block BLOCK_INDEX

        """
        params = kwarg["params"]
        cmd = "tc {} filter {} ".format(params.get("options", ""), command)
        if "dev" in params:
            cmd += "dev {} ".format(params.get("dev"))
        if "block" in params:
            cmd += "block {} ".format(params.get("block"))
        if "direction" in params:
            cmd += "{} ".format(params.get("direction"))
        return cmd
