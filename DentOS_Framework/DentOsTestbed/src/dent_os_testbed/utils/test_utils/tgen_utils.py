import json
import os
import random
import time
from collections import defaultdict

from dent_os_testbed.Device import DeviceType
from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan
from dent_os_testbed.lib.frr.bgp import Bgp
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.traffic.traffic_gen import TrafficGen
from dent_os_testbed.utils.test_utils.tb_utils import tb_get_all_devices


async def tgen_utils_get_dent_devices_with_tgen(testbed, device_types, min_links):
    """
    - Finds the tgen device and dent switches with atleast min_links in it
    """
    devices = await tb_get_all_devices(testbed, exclude_devices=[], skip_disconnected=False)
    tgen_dev, dent_devices = None, []
    for device in devices:
        if device.type == DeviceType.TRAFFIC_GENERATOR:
            device.applog.info(f"Found a tgen device {device.host_name}")
            tgen_dev = device
            # check if the links and the connected devices are in the testbed
            for dut, links in device.links_dict.items():
                if len(links[0]) < min_links:
                    continue
                if (
                    dut not in testbed.devices_dict
                    or testbed.devices_dict[dut].os != "dentos"
                    or not await testbed.devices_dict[dut].is_connected()
                ):
                    continue
                if device_types and not testbed.devices_dict[dut].type in device_types:
                    continue
                dent_devices.append(testbed.devices_dict[dut])
    return tgen_dev, dent_devices


async def _get_iface_addr_info(dd, iface, info):
    # get the n/w ip address
    out = await IpAddress.show(
        input_data=[{dd.host_name: [{"dev": iface, "cmd_options": "-j"}]}],
    )
    dd.applog.info(out)
    if out[0][dd.host_name]["rc"] != 0:
        dd.applog.info(f"Cannot find the IP address for {iface}")
        return False
    addresses = json.loads(out[0][dd.host_name]["result"])
    info["mac"] = addresses[0]["address"]
    for addr in addresses[0]["addr_info"]:
        if addr["family"] == "inet" and addr["scope"] == "global":
            info["ip"] = addr["local"].split(".")
            info["plen"] = addr["prefixlen"]
            return True
    dd.applog.info("Cannot find the Vlan GW IP address")
    return False


async def tgen_utils_get_swp_info(dent_dev, swp, swp_info):
    """
    - get the ipaddress, mac if there is a PVLAN on this interface else get it from
      the physical interface
    """
    dent = dent_dev.host_name
    # if there is a vlan configured on this port then we need use that
    out = await BridgeVlan.show(
        input_data=[
            {
                dent: [
                    {
                        "device": swp,
                        "cmd_options": "-j",
                    }
                ]
            }
        ]
    )
    dent_dev.applog.info(f"{out}")
    vlans = json.loads(out[0][dent]["result"])
    if vlans:
        for vlan in vlans[0]["vlans"]:
            # get a PVLAN to work on.
            if "flags" not in vlan or "PVID" not in vlan["flags"]:
                continue
            # get the IP address for it
            if await _get_iface_addr_info(dent_dev, "vlan{}".format(vlan["vlan"]), swp_info):
                return
    # get it from the interface
    await _get_iface_addr_info(dent_dev, swp, swp_info)


def tgen_utils_dev_groups_from_config(config):
    """
    - Creates a device group dict that can be used in *_traffic_generator_connect
    - Expects config to be a list of dicts:
    [
        {
            "ixp": tgen port,
            "ip": tgen port ip to be configured,
            "gw": peer ip,
            "plen": prefix length,
            "vlan": vlan id to be configured (optional),
        },
        ...
    ]
    """
    dev_groups = {}
    for el in config:
        if not dev_groups.get(el["ixp"], None):
            dev_groups[el["ixp"]] = []
        dev_groups[el["ixp"]].append({
            "name": f'{el["ixp"]}_{el["ip"]}/{el["plen"]}',
            "count": 1,
            "ip": el["ip"],
            "gw": el["gw"],
            "plen": el["plen"],
            "vlan": el.get("vlan", None),
        })
    return dev_groups


async def tgen_utils_traffic_generator_connect(device, tgen_ports, swp_ports, dev_groups):
    """
    - Connects to the tgen
    """
    ixia_port = device.port if device.port is not None else 443
    out = await TrafficGen.connect(
        input_data=[
            {
                device.host_name: [
                    {
                        "client_addr": device.ip,
                        "client_port": ixia_port,
                        "tgen_ports": tgen_ports,
                        "swp_ports": swp_ports,
                        "dev_groups": dev_groups,
                    }
                ]
            }
        ]
    )
    device.applog.info(out)
    assert out[0][device.host_name]["rc"] == 0


async def tgen_utils_connect_to_tgen(device, dent_dev):
    """
    - Connects to the tgen
    - sets up address for the tgen devices
    """
    dent = dent_dev.host_name
    device.applog.info("Connecting to Tgen")
    tgen_ports = device.links_dict[dent][0]
    swp_ports = device.links_dict[dent][1]
    device.applog.info(tgen_ports)
    dev_groups = {}
    for ixp, swp in zip(tgen_ports, swp_ports):
        swp_info = {}
        await tgen_utils_get_swp_info(dent_dev, swp, swp_info)
        dev_gw = swp_info["ip"]
        dev_plen = swp_info["plen"]
        dev_ip = str(int(swp[3:]) * 2)
        dev_groups[ixp] = [
            {
                "name": "ip_ep1",
                "count": 1,
                "ip": ".".join(dev_gw[:-1] + [dev_ip]),
                "gw": ".".join(dev_gw),
                "plen": dev_plen,
            }
        ]
    await tgen_utils_traffic_generator_connect(device, tgen_ports, swp_ports, dev_groups)
    return dev_groups


async def tgen_utils_create_devices_and_connect(
    tgen_dev, dent_devices, devices_info, need_vlan=True
):
    """
    - create end devices on tgen on given list of vlans on each of the switches.
    """
    # get a list of tgen and swp ports
    tgen_ports = []
    swp_ports = []
    dev_groups = {}
    dev_ip = {}
    for dd in dent_devices:
        tgen_ports += tgen_dev.links_dict[dd.host_name][0]
        swp_ports += [f"{dd.host_name}:{p}" for p in tgen_dev.links_dict[dd.host_name][1]]
        for ixp in tgen_dev.links_dict[dd.host_name][0]:
            dev_groups[ixp] = []
        # init the starting ip address for the device
        for device in devices_info[dd.host_name]:
            dev_ip[device["name"]] = 11

    for dd in dent_devices:
        for device in devices_info[dd.host_name]:
            # if this device needs to be on the vlan
            vid = None
            if "vlan" in device:
                vid = device["vlan"]
                vlan_info = {}
                if not await _get_iface_addr_info(dd, f"vlan{vid}", vlan_info):
                    continue
                dev_gw = vlan_info["ip"]
                dev_plen = vlan_info["plen"]
            for ixp, swp in zip(
                tgen_dev.links_dict[dd.host_name][0], tgen_dev.links_dict[dd.host_name][1]
            ):
                vname = device["name"]
                if "vlan" not in device:
                    # get it from the interface
                    swp_info = {}
                    await _get_iface_addr_info(dd, swp, swp_info)
                    dev_gw = swp_info["ip"]
                    dev_plen = swp_info["plen"]
                # now create tgen devices
                dev_groups[ixp].append(
                    {
                        "name": f"{dd.host_name}_{vname}_{swp}",
                        "count": device["count"],
                        "ip": ".".join(dev_gw[:-1] + [str(dev_ip[vname])]),
                        "gw": ".".join(dev_gw),
                        "plen": dev_plen,
                    }
                )
                if need_vlan and vid is not None:
                    dev_groups[ixp][-1]["vlan"] = vid
                dev_ip[vname] += 10
    await tgen_utils_traffic_generator_connect(tgen_dev, tgen_ports, swp_ports, dev_groups)


async def tgen_utils_create_bgp_devices_and_connect(tgen_dev, dent_devices, bgp_peers_info):
    """
    - get the IP address on the tgen link then create the device info
    """

    tgen_ports = []
    swp_ports = []
    dev_groups = {}
    tgen_ips = {
        DeviceType.DISTRIBUTION_ROUTER: "21.{}.{}.{}",  # 21.<dis#>.swp.1/24
        DeviceType.AGGREGATION_ROUTER: "22.{}.{}.{}",
        DeviceType.INFRA_SWITCH: "23.{}.{}.{}",
        DeviceType.OUT_OF_BOUND_SWITCH: "24.{}.{}.{}",
    }
    for dd in dent_devices:
        tgen_ports += tgen_dev.links_dict[dd.host_name][0]
        swp_ports += [f"{dd.host_name}:{p}" for p in tgen_dev.links_dict[dd.host_name][1]]
        for ixp, swp in zip(
            tgen_dev.links_dict[dd.host_name][0], tgen_dev.links_dict[dd.host_name][1]
        ):
            # if there is a vlan configured on this port then we need use that
            out = await BridgeVlan.show(
                input_data=[
                    {
                        dd.host_name: [
                            {
                                "device": swp,
                                "cmd_options": "-j",
                            }
                        ]
                    }
                ]
            )
            dd.applog.info(f"{out}")
            dev_ip = tgen_ips[dd.type].format(dd.host_name[-1], swp[3:], "2")
            dev_gw = tgen_ips[dd.type].format(dd.host_name[-1], swp[3:], "1")
            dev_plen = 24
            dev_vlan = None
            vlans = json.loads(out[0][dd.host_name]["result"])
            if vlans:
                vlan_gw, vlan_plen = None, None
                for vlan in vlans[0]["vlans"]:
                    # get the IP address for it
                    vlan_info = {}
                    if not await _get_iface_addr_info(dd, "vlan{}".format(vlan["vlan"]), vlan_info):
                        continue
                    vlan_gw = vlan_info["ip"]
                    vlan_plen = vlan_info["plen"]
                    break
                if vlan_gw is not None:
                    dev_ip = ".".join(vlan_gw[:-1] + [swp[3:]])
                    dev_gw = ".".join(vlan_gw)
                    dev_plen = vlan_plen
                    dev_vlan = vlan["vlan"]
                    dd.applog.info(
                        f"Updating the IXIA device up to vlan{dev_vlan} IP {dev_ip} GW {dev_gw}"
                    )
            else:
                # check if the aaddress is on the device else add one
                swp_info = {}
                await _get_iface_addr_info(dd, swp, swp_info)
                if dev_gw != ".".join(swp_info["ip"]):
                    # Add the address
                    out = await IpAddress.add(
                        input_data=[{dd.host_name: [{"dev": swp, "prefix": dev_gw + "/24"}]}],
                    )

            out = await Bgp.show(input_data=[{dd.host_name: [{"options": "json"}]}])
            bgp_summary = json.loads(out[0][dd.host_name]["result"])
            d1_as = bgp_summary["ipv4Unicast"]["as"]
            for cmd in [
                (
                    Bgp.configure,
                    [
                        {
                            dd.host_name: [
                                {
                                    "asn": d1_as,
                                    "neighbor": {"options": {"peer-group": ""}},
                                    "group": "IXIA",
                                }
                            ]
                        }
                    ],
                ),
                (
                    Bgp.configure,
                    [
                        {
                            dd.host_name: [
                                {
                                    "asn": d1_as,
                                    "neighbor": {"options": {"remote-as": 200}},
                                    "group": "IXIA",
                                }
                            ]
                        }
                    ],
                ),
                (
                    Bgp.configure,
                    [
                        {
                            dd.host_name: [
                                {
                                    "asn": d1_as,
                                    "neighbor": {"options": {"timers": "3 10"}},
                                    "group": "IXIA",
                                }
                            ]
                        }
                    ],
                ),
                (
                    Bgp.configure,
                    [
                        {
                            dd.host_name: [
                                {"asn": d1_as, "ip": dev_ip, "neighbor": {}, "group": "IXIA"}
                            ]
                        }
                    ],
                ),
                (
                    Bgp.configure,
                    [
                        {
                            dd.host_name: [
                                {
                                    "asn": d1_as,
                                    "address-family": "ipv4 unicast",
                                    "neighbor": {"options": {"soft-reconfiguration": "inbound"}},
                                    "group": "IXIA",
                                }
                            ]
                        }
                    ],
                ),
            ]:
                out = await cmd[0](input_data=cmd[1])
                dd.applog.info(f"added the IXIA peer {cmd[0]} out {out}")
            dev_groups[ixp] = [
                {
                    "name": f"{dd.host_name}_{swp}",
                    "count": 1,
                    "ip": dev_ip,
                    "gw": dev_gw,
                    "plen": dev_plen,
                    "bgp_peer": bgp_peers_info[dd.host_name][swp],
                    "vlan": dev_vlan,
                },
            ]
    await tgen_utils_traffic_generator_connect(tgen_dev, tgen_ports, swp_ports, dev_groups)


async def tgen_utils_setup_streams(device, config_file_name, streams, force_update=True):
    """
    - if there is a tgen config file then try to load it
    - else creates the streams and saves it and download a copy for future use.
    - start the protocols and resolve arp.
    """
    res = -1
    if not force_update and os.path.exists(config_file_name):
        device.applog.info(f"Loading Tgen config file {config_file_name}")
        out = await TrafficGen.load_config(
            input_data=[{device.host_name: [{"config_file_name": config_file_name}]}]
        )
        res = out[0][device.host_name]["rc"]
    if res != 0:
        for s in streams.keys():
            device.applog.info(f"Setting up Tgen traffic for {s}")
            out = await TrafficGen.set_traffic(
                input_data=[{device.host_name: [{"name": s, "pkt_data": streams[s]}]}]
            )
            device.applog.info(out)
            assert out[0][device.host_name]["rc"] == 0, "Setting tgen traffic failed.\n{out}"
        device.applog.info(f"Saving Tgen config file {config_file_name}")
        out = await TrafficGen.save_config(
            input_data=[{device.host_name: [{"config_file_name": config_file_name}]}]
        )
    device.applog.info("Starting Protocols")
    out = await TrafficGen.start_protocols(input_data=[{device.host_name: [{}]}])
    device.applog.info(out)
    assert out[0][device.host_name]["rc"] == 0


async def tgen_utils_start_traffic(device):
    """
    Start the tgen traffic
    """
    device.applog.info("Starting the Tgen Traffic")
    out = await TrafficGen.start_traffic(input_data=[{device.host_name: [{}]}])
    device.applog.info(out)
    # assert out[0][device.host_name]["rc"] == 0


async def tgen_utils_stop_traffic(device):
    """
    Stop the tgen traffic
    """
    device.applog.info("Stopping Traffic")
    out = await TrafficGen.stop_traffic(input_data=[{device.host_name: [{}]}])
    device.applog.info(out)
    # assert out[0][device.host_name]["rc"] == 0


async def tgen_utils_get_traffic_stats(device, stats_type="Port Statistics"):
    device.applog.info("Getting Traffic Stats")
    out = await TrafficGen.get_stats(input_data=[{device.host_name: [{"stats_type": stats_type}]}])
    device.applog.info(out)
    assert out[0][device.host_name]["rc"] == 0
    stats = out[0][device.host_name]["result"]
    for row in stats.Rows:
        if stats_type == "Port Statistics":
            device.applog.info(
                "Port {} Tx {} Rx {}".format(
                    row["Port Name"],
                    row["Frames Tx."],
                    row["Valid Frames Rx."],
                )
            )
        elif stats_type == "Flow Statistics":
            device.applog.info(
                "Tx {} Rx {} TI {} SIP-DIP {} Tx {} Rx {} Loss {}".format(
                    row["Tx Port"],
                    row["Rx Port"],
                    row["Traffic Item"],
                    row["Source/Dest Value Pair"],
                    row["Tx Frames"],
                    row["Rx Frames"],
                    row["Loss %"],
                )
            )
        elif stats_type == "Traffic Item Statistics":
            device.applog.info(
                "Traffic Item {} Tx {} Rx {} Frames Delta {} Loss {}".format(
                    row["Traffic Item"],
                    row["Tx Frames"],
                    row["Rx Frames"],
                    row["Frames Delta"],
                    row["Loss %"],
                )
            )

    return out[0][device.host_name]["result"]


async def tgen_utils_clear_traffic_stats(device):
    device.applog.info("Clearing Traffic Stats")
    out = await TrafficGen.clear_stats(input_data=[{device.host_name: [{}]}])
    device.applog.info(out)
    # assert out[0][device.host_name]["rc"] == 0


async def tgen_utils_stop_protocols(device):
    device.applog.info("Stopping Protocols")
    out = await TrafficGen.stop_protocols(input_data=[{device.host_name: [{}]}])
    # assert out[0][device.host_name]["rc"] == 0
    device.applog.info(out)
    time.sleep(10)
    device.applog.info("Removing Session")
    out = await TrafficGen.disconnect(input_data=[{device.host_name: [{}]}])
    # assert out[0][device.host_name]["rc"] == 0
    device.applog.info(out)


async def tgen_util_flap_bgp_peer(device, ixp, skip_down=False, skip_up=False):
    if not skip_down:
        device.applog.info(f"flapping bgp protocol peer {ixp} DOWN")
        out = await TrafficGen.set_protocol(
            input_data=[{device.host_name: [{"bgp_peer": ixp, "enable": False}]}]
        )
        device.applog.info(out)
        assert out[0][device.host_name]["rc"] == 0
        time.sleep(5)
    if not skip_up:
        device.applog.info(f"flapping bgp protocol peer {ixp} UP")
        out = await TrafficGen.set_protocol(
            input_data=[{device.host_name: [{"bgp_peer": ixp, "enable": True}]}]
        )
        device.applog.info(out)
        assert out[0][device.host_name]["rc"] == 0


def tgen_util_convert_aws_logs_to_streams():

    # this is the code used to convert aws packet capture to tgen streams.
    top_dir = "./logs/"
    raw_streams = {}
    valid_tokens = {
        "DST": ["10."],
        "PROTO": [],
        "DPT": [],
    }
    conversion = {
        "DST": "dstIp",
        "PROTO": "ipproto",
        "DPT": "dstPort",
    }
    files = sorted(os.listdir(top_dir))
    for file in files:
        with open(top_dir + file, "rt") as fd:
            for line in fd:
                skip = False
                stream = {"protocol": "ip"}
                words = line.split(" ")
                for word in words:
                    if "=" not in word:
                        continue
                    key, value = word.split("=")
                    if key not in valid_tokens:
                        continue
                    # skip if already covered.
                    for valid_token in valid_tokens[key]:
                        if value.startswith(valid_token):
                            skip = True
                            break
                    stream[conversion[key]] = value
                if skip:
                    continue
                raw_streams["_".join([k + "_" + v for k, v in stream.items()])] = stream
    # optimize the raw_streams now.
    streams = {}
    dpt_streams = {}
    # Construct the streams per DPT
    for key, value in raw_streams.items():
        dpt = value.get("dstPort", "0")
        dpt_streams.setdefault(dpt, {})
        dpt_streams[dpt][key] = value

    # now randomize the streams > 100 streams per DPT
    for dpt, data in dpt_streams.items():
        if len(data) > 100:
            # construct the streams from the starting octect of the IP
            dip_streams = defaultdict(list)
            for rval in data.values():
                msb_ip = rval["dstIp"].split(".")[0]
                dip_streams[msb_ip].append(rval)
            r_data = {}
            for dip, dip_data in dip_streams.items():
                dip_data = random.sample(dip_data, 10) if len(dip_data) > 10 else dip_data
                for rval in dip_data:
                    r_data["_".join([k + "_" + v for k, v in rval.items()])] = rval
            data = r_data
        streams.update(data)

    with open("streams.json", "w") as outfile:
        json.dump(streams, outfile, indent=4)
    print("Created %d Streams" % len(streams.keys()))


def tgen_utils_get_loss(row):
    loss = row["Loss %"]
    if loss == "":
        return 0.0
    return float(loss)
