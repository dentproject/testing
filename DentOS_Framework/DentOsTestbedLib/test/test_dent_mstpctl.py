# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# generated using file ./gen/model/dent/network/mstpctl/mstpctl.yaml
#
# DONOT EDIT - generated by diligent bots

import asyncio
from .utils import TestDevice
from dent_os_testbed.lib.mstpctl.mstpctl import Mstpctl


def test_that_mstpctl_set(capfd):
    dv1 = TestDevice(platform='dentos')
    dv2 = TestDevice(platform='dentos')
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(Mstpctl.set(input_data=[{
        # device 1
        'test_dev': [{}],
    }], device_obj={'test_dev': dv1}))
    print(out)
    assert 'command' in out[0]['test_dev'].keys()
    assert 'result' in out[0]['test_dev'].keys()
    # check the rc
    assert out[0]['test_dev']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(Mstpctl.set(input_data=[{
        # device 1
        'test_dev1': [{
            # command 1

        }, {
            # command 2

        }],
    }], device_obj={'test_dev1': dv1, 'test_dev2': dv2}))
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(Mstpctl.set(input_data=[{
        # device 1
        'test_dev1': [{

        }],
        # device 2
        'test_dev2': [{

        }],
    }], device_obj={'test_dev1': dv1, 'test_dev2': dv2}))
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


def test_that_mstpctl_add(capfd):
    dv1 = TestDevice(platform='dentos')
    dv2 = TestDevice(platform='dentos')
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(Mstpctl.add(input_data=[{
        # device 1
        'test_dev': [{}],
    }], device_obj={'test_dev': dv1}))
    print(out)
    assert 'command' in out[0]['test_dev'].keys()
    assert 'result' in out[0]['test_dev'].keys()
    # check the rc
    assert out[0]['test_dev']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(Mstpctl.add(input_data=[{
        # device 1
        'test_dev1': [{
            # command 1
            'bridge': 'qryvykac',

        }, {
            # command 2
            'bridge': 'ilwtwhvx',

        }],
    }], device_obj={'test_dev1': dv1, 'test_dev2': dv2}))
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(Mstpctl.add(input_data=[{
        # device 1
        'test_dev1': [{
            'bridge': 'qryvykac',

        }],
        # device 2
        'test_dev2': [{
            'bridge': 'ilwtwhvx',

        }],
    }], device_obj={'test_dev1': dv1, 'test_dev2': dv2}))
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


def test_that_mstpctl_show(capfd):
    dv1 = TestDevice(platform='dentos')
    dv2 = TestDevice(platform='dentos')
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(Mstpctl.show(input_data=[{
        # device 1
        'test_dev': [{}],
    }], device_obj={'test_dev': dv1}))
    print(out)
    assert 'command' in out[0]['test_dev'].keys()
    assert 'result' in out[0]['test_dev'].keys()
    # check the rc
    assert out[0]['test_dev']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(Mstpctl.show(input_data=[{
        # device 1
        'test_dev1': [{
            # command 1
            'bridge': 'gafzhldb',

        }, {
            # command 2
            'bridge': 'yuawqvqs',

        }],
    }], device_obj={'test_dev1': dv1, 'test_dev2': dv2}))
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(Mstpctl.show(input_data=[{
        # device 1
        'test_dev1': [{
            'bridge': 'gafzhldb',

        }],
        # device 2
        'test_dev2': [{
            'bridge': 'yuawqvqs',

        }],
    }], device_obj={'test_dev1': dv1, 'test_dev2': dv2}))
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


def test_that_mstpctl_remove(capfd):
    dv1 = TestDevice(platform='dentos')
    dv2 = TestDevice(platform='dentos')
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(Mstpctl.remove(input_data=[{
        # device 1
        'test_dev': [{}],
    }], device_obj={'test_dev': dv1}))
    print(out)
    assert 'command' in out[0]['test_dev'].keys()
    assert 'result' in out[0]['test_dev'].keys()
    # check the rc
    assert out[0]['test_dev']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(Mstpctl.remove(input_data=[{
        # device 1
        'test_dev1': [{
            # command 1
            'bridge': 'ikfedjyo',

        }, {
            # command 2
            'bridge': 'ragcwrtu',

        }],
    }], device_obj={'test_dev1': dv1, 'test_dev2': dv2}))
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(Mstpctl.remove(input_data=[{
        # device 1
        'test_dev1': [{
            'bridge': 'ikfedjyo',

        }],
        # device 2
        'test_dev2': [{
            'bridge': 'ragcwrtu',

        }],
    }], device_obj={'test_dev1': dv1, 'test_dev2': dv2}))
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
