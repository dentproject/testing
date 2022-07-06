import json

from testbed.lib.frr.bgp import Bgp
from testbed.lib.frr.frr_ip import FrrIp


async def bgp_routing_get_local_as(d1):
    out = await Bgp.show(input_data=[{d1.host_name: [{"options": "json"}]}])
    d1.applog.info(f"Ran command Bgp.show out {out}")
    assert out[0][d1.host_name]["rc"] == 0, f"Failed to determine the bgp summary on d1.host_name"
    bgp_summary = json.loads(out[0][d1.host_name]["result"])
    return bgp_summary["ipv4Unicast"]["as"]


def bgp_routing_get_prefix_list(num_routes, host_name):
    cmds = []
    seq = 10
    for i in range(num_routes):
        cmds.append(
            (
                FrrIp.set,
                [
                    {
                        host_name: [
                            {
                                "prefix-list": "IXIA-ROUTES",
                                "sequence": seq,
                                "options": {"permit": f"30.0.{i}.0/24"},
                            }
                        ]
                    }
                ],
            )
        )
        seq += 10
    return cmds
