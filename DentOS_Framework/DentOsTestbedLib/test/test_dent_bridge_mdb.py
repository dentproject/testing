# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# generated using file ./gen/model/dent/network/bridge/bridge.yaml
#
# DONOT EDIT - generated by diligent bots

import asyncio

from dent_os_testbed.lib.bridge.bridge_mdb import BridgeMdb

from .utils import TestDevice


def test_that_bridge_mdb_add(capfd):

    dv1 = TestDevice(platform='dentos')
    dv2 = TestDevice(platform='dentos')
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        BridgeMdb.add(
            input_data=[
                {
                    # device 1
                    'test_dev': [{}],
                }
            ],
            device_obj={'test_dev': dv1},
        )
    )
    print(out)
    assert 'command' in out[0]['test_dev'].keys()
    assert 'result' in out[0]['test_dev'].keys()
    # check the rc
    assert out[0]['test_dev']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        BridgeMdb.add(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            # command 1
                            'dev': 'wamsdoqp',
                            'port': 3806,
                            'grp': 5493,
                            'permanent': True,
                            'temp': True,
                            'vid': 5527,
                        },
                        {
                            # command 2
                            'dev': 'yveyzbpq',
                            'port': 7807,
                            'grp': 5484,
                            'permanent': False,
                            'temp': False,
                            'vid': 7640,
                        },
                    ],
                }
            ],
            device_obj={'test_dev1': dv1, 'test_dev2': dv2},
        )
    )
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        BridgeMdb.add(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            'dev': 'wamsdoqp',
                            'port': 3806,
                            'grp': 5493,
                            'permanent': True,
                            'temp': True,
                            'vid': 5527,
                        }
                    ],
                    # device 2
                    'test_dev2': [
                        {
                            'dev': 'yveyzbpq',
                            'port': 7807,
                            'grp': 5484,
                            'permanent': False,
                            'temp': False,
                            'vid': 7640,
                        }
                    ],
                }
            ],
            device_obj={'test_dev1': dv1, 'test_dev2': dv2},
        )
    )
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    assert 'command' in out[1]['test_dev2'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    assert 'result' in out[1]['test_dev2'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0
    assert out[1]['test_dev2']['rc'] == 0


def test_that_bridge_mdb_delete(capfd):

    dv1 = TestDevice(platform='dentos')
    dv2 = TestDevice(platform='dentos')
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        BridgeMdb.delete(
            input_data=[
                {
                    # device 1
                    'test_dev': [{}],
                }
            ],
            device_obj={'test_dev': dv1},
        )
    )
    print(out)
    assert 'command' in out[0]['test_dev'].keys()
    assert 'result' in out[0]['test_dev'].keys()
    # check the rc
    assert out[0]['test_dev']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        BridgeMdb.delete(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            # command 1
                            'dev': 'jfkcvrsj',
                            'port': 5804,
                            'grp': 7976,
                            'permanent': False,
                            'temp': True,
                            'vid': 8357,
                        },
                        {
                            # command 2
                            'dev': 'wpqakpaa',
                            'port': 9041,
                            'grp': 266,
                            'permanent': False,
                            'temp': True,
                            'vid': 4119,
                        },
                    ],
                }
            ],
            device_obj={'test_dev1': dv1, 'test_dev2': dv2},
        )
    )
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        BridgeMdb.delete(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            'dev': 'jfkcvrsj',
                            'port': 5804,
                            'grp': 7976,
                            'permanent': False,
                            'temp': True,
                            'vid': 8357,
                        }
                    ],
                    # device 2
                    'test_dev2': [
                        {
                            'dev': 'wpqakpaa',
                            'port': 9041,
                            'grp': 266,
                            'permanent': False,
                            'temp': True,
                            'vid': 4119,
                        }
                    ],
                }
            ],
            device_obj={'test_dev1': dv1, 'test_dev2': dv2},
        )
    )
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    assert 'command' in out[1]['test_dev2'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    assert 'result' in out[1]['test_dev2'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0
    assert out[1]['test_dev2']['rc'] == 0


def test_that_bridge_mdb_show(capfd):

    dv1 = TestDevice(platform='dentos')
    dv2 = TestDevice(platform='dentos')
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        BridgeMdb.show(
            input_data=[
                {
                    # device 1
                    'test_dev': [{}],
                }
            ],
            device_obj={'test_dev': dv1},
        )
    )
    print(out)
    assert 'command' in out[0]['test_dev'].keys()
    assert 'result' in out[0]['test_dev'].keys()
    # check the rc
    assert out[0]['test_dev']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        BridgeMdb.show(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            # command 1
                            'dev': 'nfvxxwdn',
                            'options': 'vxuouahs',
                        },
                        {
                            # command 2
                            'dev': 'vcltykyw',
                            'options': 'gveuorqo',
                        },
                    ],
                }
            ],
            device_obj={'test_dev1': dv1, 'test_dev2': dv2},
        )
    )
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        BridgeMdb.show(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            'dev': 'nfvxxwdn',
                            'options': 'vxuouahs',
                        }
                    ],
                    # device 2
                    'test_dev2': [
                        {
                            'dev': 'vcltykyw',
                            'options': 'gveuorqo',
                        }
                    ],
                }
            ],
            device_obj={'test_dev1': dv1, 'test_dev2': dv2},
        )
    )
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    assert 'command' in out[1]['test_dev2'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    assert 'result' in out[1]['test_dev2'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0
    assert out[1]['test_dev2']['rc'] == 0
