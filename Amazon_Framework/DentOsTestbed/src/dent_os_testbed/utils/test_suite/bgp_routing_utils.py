import json


async def bgp_routing_get_local_as(d1):
    cmd = f"vtysh -c 'show bgp summary json'"
    rc, out = await d1.run_cmd(cmd, sudo=True)
    d1.applog.info(f"Ran command {cmd} rc {rc} out {out}")
    assert rc == 0, f"Failed to determine the bgp summary on d1.host_name"
    bgp_summary = json.loads(out)
    return bgp_summary["ipv4Unicast"]["as"]


def bgp_routing_get_prefix_list(num_routes):
    cmds = []
    seq = 10
    for i in range(num_routes):
        cmds.append(
            f"vtysh -c 'conf terminal' -c 'ip prefix-list IXIA-ROUTES seq {seq} permit 30.0.{i}.0/24'"
        )
        seq += 10
    return cmds
