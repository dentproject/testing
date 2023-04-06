from collections import namedtuple
import asyncio
import random
import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan

from dent_os_testbed.utils.test_utils.tb_utils import (
    tb_ping_device,
)

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_get_loss,
)

from dent_os_testbed.test.test_suite.functional.ipv6.ipv6_utils import (
    verify_dut_neighbors,
    verify_dut_routes,
)

pytestmark = [
    pytest.mark.suite_functional_ipv6,
    pytest.mark.usefixtures("cleanup_ip_addrs", "enable_ipv6_forwarding", "cleanup_bridges"),
    pytest.mark.asyncio,
]


async def test_ipv6_on_bridge(testbed):
    """
    Test Name: test_ipv6_on_bridge
    Test Suite: suite_functional_ipv6
    Test Overview: Verify correct routing over bridge interface
    Test Procedure:
    1. Add IP address for port, bridge 1D, bridge 1Q. Configure hosts on TG
    2. Verify IP configuration: no errors on IP address adding, connected routes added and offloaded
    3. Send bidirectional traffic between TG ports for primary IP addresses
    4. Verify clear traffic between port and bridge1 and bridge2
    5. Verify neighbors resolved
    """
    num_of_ports = 3
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], num_of_ports)
    if not tgen_dev or not dent_devices:
        pytest.skip("The testbed does not have enough dent with tgen connections")
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0][:num_of_ports]
    ports = tgen_dev.links_dict[dent][1][:num_of_ports]
    addr_info = namedtuple("addr_info", ["swp", "tg", "swp_ip", "tg_ip", "plen"])
    traffic_duration = 10
    wait_for_stats = 10
    plen = 64
    bridge_d = "br0"
    bridge_dot1q = "br1"

    address_map = (
        # primary
        addr_info(ports[0], tg_ports[0], "2001:1111::1", "2001:1111::2", plen),
        addr_info(bridge_d, tg_ports[1], "2001:2222::1", "2001:2222::2", plen),
        addr_info(bridge_dot1q, tg_ports[2], "2001:3333::1", "2001:3333::2", plen),
        # secondary
        addr_info(ports[0], tg_ports[0], "2001:4444::1", "2001:4444::2", plen),
        addr_info(bridge_d, tg_ports[1], "2001:5555::1", "2001:5555::2", plen),
        addr_info(bridge_dot1q, tg_ports[2], "2001:6666::1", "2001:6666::2", plen),
    )

    # 1. Add IP address for port, bridge 1D, bridge 1Q
    out = await IpLink.add(input_data=[{dent: [
        {"device": bridge_d, "type": "bridge", "vlan_filtering": 0},
        {"device": bridge_dot1q, "type": "bridge", "vlan_filtering": 1},
    ]}])
    assert out[0][dent]["rc"] == 0, "Failed to create bridges"

    out = await IpLink.set(input_data=[{dent: [
        {"device": ports[0], "operstate": "up"},
        {"device": ports[1], "operstate": "up", "master": bridge_d},
        {"device": ports[2], "operstate": "up", "master": bridge_dot1q},
        {"device": bridge_d, "operstate": "up"},
        {"device": bridge_dot1q, "operstate": "up"},
    ]}])
    assert out[0][dent]["rc"] == 0, "Failed to set port state UP"

    out = await IpAddress.add(input_data=[{dent: [
        {"dev": info.swp, "prefix": f"{info.swp_ip}/{info.plen}"}
        for info in address_map
    ]}])
    assert out[0][dent]["rc"] == 0, "Failed to add IP addr to port"

    # Configure hosts on TG
    dev_groups = tgen_utils_dev_groups_from_config(
        {"ixp": info.tg, "ip": info.tg_ip, "gw": info.swp_ip,
         "plen": info.plen, "version": "ipv6"}
        for info in address_map
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    streams = {
        f"{src} <-> {dst}": {
            "type": "ipv6",
            "ip_source": [ep["name"] for ep in dev_groups[src]],
            "ip_destination": [ep["name"] for ep in dev_groups[dst]],
            "rate": 10000,  # pps
            "bi_directional": True,
        } for src, dst in ((tg_ports[0], tg_ports[1]),
                           (tg_ports[0], tg_ports[2]),
                           (tg_ports[1], tg_ports[2]))
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # 2. Verify IP configuration: no errors on IP address adding,
    #    connected routes added and offloaded
    expected_routes = {}
    for info in address_map:
        if info.swp not in expected_routes:
            expected_routes[info.swp] = []
        expected_routes[info.swp].append(info.swp_ip[:-1] + f"/{info.plen}")

    await verify_dut_routes(dent, expected_routes)

    # 3. Send bidirectional traffic between TG ports for primary IP addresses
    out = await asyncio.gather(*[tb_ping_device(dent_dev, info.tg_ip, pkt_loss_treshold=0, dump=True)
                                 for info in address_map])
    assert all(rc == 0 for rc in out), "Some pings from DUT did not have a reply"

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # 4. Verify clear traffic between port and d-bridge and q-bridge
    await asyncio.sleep(wait_for_stats)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        assert loss == 0, f"Expected loss: 0%, actual: {loss}%"

    # 5. Verify neighbors resolved
    expected_neis = {}
    for info in address_map:
        if info.swp not in expected_neis:
            expected_neis[info.swp] = []
        expected_neis[info.swp].append(info.tg_ip)

    await verify_dut_neighbors(dent, expected_neis)


async def test_ipv6_on_bridge_vlan(testbed):
    """
    Test Name: test_ipv6_on_bridge_vlan
    Test Suite: suite_functional_ipv6
    Test Overview:
        Verify correct routing over bridge VLAN interface
        Verify routing between VLANs
    Test Procedure:
    1. Create 1Q bridge, enslave ports, add vlan interfaces, set all interfaces up
    2. Add primary/secondary IP addresses DUT ports/bridges. Configure Hosts on TG side
    3. Configure and send bidirectional traffic between TG port and bridge VLAN interface,
       between bridge VLAN interfaces for primary/secondary IP address
    4. Verify there is no packet loss
    """
    num_of_ports = 3
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], num_of_ports)
    if not tgen_dev or not dent_devices:
        pytest.skip("The testbed does not have enough dent with tgen connections")
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0][:num_of_ports]
    ports = tgen_dev.links_dict[dent][1][:num_of_ports]
    addr_info = namedtuple("addr_info", ["swp", "tg", "swp_ip", "tg_ip", "plen", "vlan"])
    traffic_duration = 10
    wait_for_stats = 10
    plen = 64
    bridge = "br0"
    vlans = random.sample(range(1, 4095), 4)
    vlan_ifs = [f"{bridge}.{vlan}" for vlan in vlans]

    address_map = [
        addr_info(vlan_if, tg, f"2001:{idx}0::1", f"2001:{idx}0::2", plen, vlan)
        for idx, (vlan_if, vlan, tg) in enumerate(zip(vlan_ifs, vlans, tg_ports[1:]+tg_ports[1:]), start=1)
    ] + [
        addr_info(ports[0], tg_ports[0], "2001:100::1", "2001:100::2", plen, None)
    ]

    # 1. Create 1Q bridge
    out = await IpLink.add(input_data=[{dent: [
        {"device": bridge, "type": "bridge", "vlan_filtering": 1, "vlan_default_pvid": 0},
    ]}])
    assert out[0][dent]["rc"] == 0, "Failed to create bridges"

    # Enslave ports
    out = await IpLink.set(input_data=[{dent: [
        {"device": port, "master": bridge}
        for port in ports[1:]
    ]}])
    assert out[0][dent]["rc"] == 0, "Failed to set port state UP"

    # Add vlan interfaces
    out = await BridgeVlan.add(input_data=[{dent: [
        {"device": bridge, "vid": vlan, "self": True}
        for vlan in vlans
    ] + [
        {"device": port, "vid": vlan, "untagged": False}
        for port, vlan in zip(ports[1:]+ports[1:], vlans)
    ]}])
    assert out[0][dent]["rc"] == 0, "Failed to add vlans"

    out = await IpLink.add(input_data=[{dent: [
        {"name": vlan_dev, "type": f"vlan id {vid}", "link": bridge}
        for vlan_dev, vid in zip(vlan_ifs, vlans)
    ]}])
    assert out[0][dent]["rc"] == 0, "Failed to create vlan subifs"

    # Set all interfaces up
    out = await IpLink.set(input_data=[{dent: [
        {"device": dev, "operstate": "up"}
        for dev in [bridge] + ports + vlan_ifs
    ]}])
    assert out[0][dent]["rc"] == 0, "Failed to set port state UP"

    # 2. Add primary/secondary IP addresses DUT ports/bridges. Configure Hosts on TG side
    out = await IpAddress.add(input_data=[{dent: [
        {"dev": info.swp, "prefix": f"{info.swp_ip}/{info.plen}"}
        for info in address_map
    ]}])
    assert out[0][dent]["rc"] == 0, "Failed to add IP addr to port"

    # Configure hosts on TG
    dev_groups = tgen_utils_dev_groups_from_config(
        {"ixp": info.tg, "ip": info.tg_ip, "gw": info.swp_ip,
         "plen": info.plen, "vlan": info.vlan, "version": "ipv6"}
        for info in address_map
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    # 3. Configure and bidirectional traffic
    streams = {
        f"{src} <-> {dst}": {
            "type": "ipv6",
            "ip_source": [ep["name"] for ep in dev_groups[src]],
            "ip_destination": [ep["name"] for ep in dev_groups[dst]],
            "rate": 10000,  # pps
            "bi_directional": True,
        } for src, dst in ((tg_ports[0], tg_ports[1]),
                           (tg_ports[0], tg_ports[2]),
                           (tg_ports[1], tg_ports[2]))
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # Send traffic
    out = await asyncio.gather(*[tb_ping_device(dent_dev, info.tg_ip, pkt_loss_treshold=0, dump=True)
                                 for info in address_map])
    assert all(rc == 0 for rc in out), "Some pings from DUT did not have a reply"

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # 4. Verify there is no packet loss
    await asyncio.sleep(wait_for_stats)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        assert loss == 0, f"Expected loss: 0%, actual: {loss}%"


async def test_ipv6_move_host_on_bridge(testbed):
    """
    Test Name: test_ipv6_move_host_on_bridge
    Test Suite: suite_functional_ipv6
    Test Overview: Verify neighbor is relearned after host moved to another port of bridge
    Test Procedure:
    1. Add IP address port and bridge. Configure Hosts on TG
    2. Verify IP configuration: no errors on IP address adding, connected routes added and offloaded
    3. Send bidirectional traffic between TG ports for primary IP addresses. Verify clear traffic
    4. Verify neighbors resolved
    5. Delete host from TG port#2. Add host to TG port#3
    6. Send bidirectional traffic between TG ports for primary IP addresses. Verify clear traffic
    7. Verify IP configuration: no errors arise on IP address adding, connected routes added and offloaded
    8. Verify neighbors resolved
    """
    num_of_ports = 3
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], num_of_ports)
    if not tgen_dev or not dent_devices:
        pytest.skip("The testbed does not have enough dent with tgen connections")
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0][:num_of_ports]
    ports = tgen_dev.links_dict[dent][1][:num_of_ports]
    addr_info = namedtuple("addr_info", ["swp", "tg", "swp_ip", "tg_ip", "plen"])
    traffic_duration = 10
    wait_for_stats = 10
    plen = 64
    bridge = "br0"

    address_map = (
        addr_info(ports[0], tg_ports[0], "2001:1111::1", "2001:1111::2", plen),
        addr_info(bridge, tg_ports[1], "2001:2222::1", "2001:2222::2", plen),
    )

    # 1. Add IP address port and bridge
    out = await IpLink.add(input_data=[{dent: [
        {"device": bridge, "type": "bridge", "vlan_filtering": 1},
    ]}])
    assert out[0][dent]["rc"] == 0, "Failed to create bridges"

    out = await IpLink.set(input_data=[{dent: [
        {"device": port, "operstate": "up", "master": bridge} for port in ports[1:]
    ] + [
        {"device": bridge, "operstate": "up"},
    ]}])
    assert out[0][dent]["rc"] == 0, "Failed to set port state UP"

    out = await IpAddress.add(input_data=[{dent: [
        {"dev": info.swp, "prefix": f"{info.swp_ip}/{info.plen}"}
        for info in address_map
    ]}])
    assert out[0][dent]["rc"] == 0, "Failed to add IP addr to port"

    # Configure hosts on TG
    dev_groups = tgen_utils_dev_groups_from_config(
        {"ixp": info.tg, "ip": info.tg_ip, "gw": info.swp_ip,
         "plen": info.plen, "version": "ipv6"}
        for info in address_map
    )
    await tgen_utils_traffic_generator_connect(
        tgen_dev,
        [info.tg for info in address_map],
        [info.swp for info in address_map],
        dev_groups,
    )

    streams = {
        f"{tg_ports[0]} <-> {tg_ports[1]}": {
            "type": "ipv6",
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "rate": 10000,  # pps
            "bi_directional": True,
        },
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # 2. Verify IP configuration: no errors on IP address adding, connected routes added and offloaded
    expected_routes = {
        info.swp: [info.swp_ip[:-1] + f"/{info.plen}"]
        for info in address_map
    }
    await verify_dut_routes(dent, expected_routes)

    # 3. Send bidirectional traffic between TG ports for primary IP addresses
    out = await asyncio.gather(*[tb_ping_device(dent_dev, info.tg_ip, pkt_loss_treshold=0, dump=True)
                                 for info in address_map[:2]])
    assert all(rc == 0 for rc in out), "Some pings from DUT did not have a reply"

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # Verify clear traffic
    await asyncio.sleep(wait_for_stats)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        assert loss == 0, f"Expected loss: 0%, actual: {loss}%"

    # 4. Verify neighbors resolved
    expected_neis = {
        info.swp: [info.tg_ip]
        for info in address_map
    }
    learned_macs = await verify_dut_neighbors(dent, expected_neis)

    # 5. Delete host from TG port#2. Add host to TG port#3
    address_map = (
        addr_info(ports[0], tg_ports[0], "2001:1111::1", "2001:1111::2", plen),
        # placeholder, so that port 2 will have a different mac
        addr_info(bridge, tg_ports[1], "::", "::", plen),
        # port 2 will have the same ip, but a different mac, as port 1 at step 1
        addr_info(bridge, tg_ports[2], "2001:2222::1", "2001:2222::2", plen),
    )
    dev_groups = tgen_utils_dev_groups_from_config(
        {"ixp": info.tg, "ip": info.tg_ip, "gw": info.swp_ip,
         "plen": info.plen, "version": "ipv6"}
        for info in address_map
    )
    # will reset the current session, clear all traffic items, and will create
    # new tg port endpoints with different MACs and IPs
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    streams = {
        f"{tg_ports[0]} <-> {tg_ports[2]}": {
            "type": "ipv6",
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[2]][0]["name"],
            "rate": 10000,  # pps
            "bi_directional": True,
        },
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # 6. Send bidirectional traffic between TG ports for primary IP addresses
    out = await asyncio.gather(*[tb_ping_device(dent_dev, info.tg_ip, pkt_loss_treshold=0, dump=True)
                                 for info in address_map[::2]])
    assert all(rc == 0 for rc in out), "Some pings from DUT did not have a reply"

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # Verify clear traffic
    await asyncio.sleep(wait_for_stats)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        assert loss == 0, f"Expected loss: 0%, actual: {loss}%"

    # 7. Verify IP configuration: no errors arise on IP address adding, connected routes added and offloaded
    await verify_dut_routes(dent, expected_routes)

    # 8. Verify neighbors resolved
    new_learned_macs = await verify_dut_neighbors(dent, expected_neis)
    for mac in new_learned_macs[bridge]:
        assert mac not in learned_macs[bridge], "Expected learned mac to change"
