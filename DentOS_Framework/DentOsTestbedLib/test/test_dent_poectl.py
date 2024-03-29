# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# generated using file ./gen/model/dent/platform/poe/peoctl.yaml
#
# DONOT EDIT - generated by diligent bots

import asyncio

from dent_os_testbed.lib.poe.poectl import Poectl

from .utils import TestDevice


def test_that_poectl_show(capfd):

    dv1 = TestDevice(platform='dentos')
    dv2 = TestDevice(platform='dentos')
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        Poectl.show(
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
        Poectl.show(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            # command 1
                            'port': 'frygpyfu',
                        },
                        {
                            # command 2
                            'port': 'qsjzaaay',
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
        Poectl.show(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            'port': 'frygpyfu',
                        }
                    ],
                    # device 2
                    'test_dev2': [
                        {
                            'port': 'qsjzaaay',
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


def test_that_poectl_enable(capfd):

    dv1 = TestDevice(platform='dentos')
    dv2 = TestDevice(platform='dentos')
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        Poectl.enable(
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
        Poectl.enable(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            # command 1
                            'port': 'lvycwhcl',
                        },
                        {
                            # command 2
                            'port': 'zzcrxgxy',
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
        Poectl.enable(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            'port': 'lvycwhcl',
                        }
                    ],
                    # device 2
                    'test_dev2': [
                        {
                            'port': 'zzcrxgxy',
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


def test_that_poectl_disable(capfd):

    dv1 = TestDevice(platform='dentos')
    dv2 = TestDevice(platform='dentos')
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        Poectl.disable(
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
        Poectl.disable(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            # command 1
                            'port': 'zmebdbfx',
                        },
                        {
                            # command 2
                            'port': 'tyeyiyde',
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
        Poectl.disable(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            'port': 'zmebdbfx',
                        }
                    ],
                    # device 2
                    'test_dev2': [
                        {
                            'port': 'tyeyiyde',
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


def test_that_poectl_save(capfd):

    dv1 = TestDevice(platform='dentos')
    dv2 = TestDevice(platform='dentos')
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        Poectl.save(
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
        Poectl.save(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            # command 1
                            'port': 'hfxuqtdo',
                        },
                        {
                            # command 2
                            'port': 'iolrvudo',
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
        Poectl.save(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            'port': 'hfxuqtdo',
                        }
                    ],
                    # device 2
                    'test_dev2': [
                        {
                            'port': 'iolrvudo',
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


def test_that_poectl_restore(capfd):

    dv1 = TestDevice(platform='dentos')
    dv2 = TestDevice(platform='dentos')
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        Poectl.restore(
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
        Poectl.restore(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            # command 1
                            'port': 'hbngkaka',
                        },
                        {
                            # command 2
                            'port': 'xdycfony',
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
        Poectl.restore(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            'port': 'hbngkaka',
                        }
                    ],
                    # device 2
                    'test_dev2': [
                        {
                            'port': 'xdycfony',
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
