# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# generated using file ./gen/model/dent/network/tc/tc.yaml
#
# DONOT EDIT - generated by diligent bots

import asyncio

from dent_os_testbed.lib.tc.tc_filter import TcFilter

from .utils import TestDevice


def test_that_tc_filter_add(capfd):

    dv1 = TestDevice(platform='dentos')
    dv2 = TestDevice(platform='dentos')
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        TcFilter.add(
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
        TcFilter.add(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            # command 1
                            'dev': 'nstteomt',
                            'parent': 367,
                            'root': False,
                            'handle': 2687,
                            'protocol': 'jsbremqg',
                            'prio': 340,
                            'filtertype': 'wkosxyap',
                            'flowid': 5769,
                            'options': 'hrseshnx',
                        },
                        {
                            # command 2
                            'dev': 'ddanvlij',
                            'parent': 8425,
                            'root': True,
                            'handle': 5827,
                            'protocol': 'blfcpdsb',
                            'prio': 8331,
                            'filtertype': 'aenqufkj',
                            'flowid': 6706,
                            'options': 'atebrfcn',
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
        TcFilter.add(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            'dev': 'nstteomt',
                            'parent': 367,
                            'root': False,
                            'handle': 2687,
                            'protocol': 'jsbremqg',
                            'prio': 340,
                            'filtertype': 'wkosxyap',
                            'flowid': 5769,
                            'options': 'hrseshnx',
                        }
                    ],
                    # device 2
                    'test_dev2': [
                        {
                            'dev': 'ddanvlij',
                            'parent': 8425,
                            'root': True,
                            'handle': 5827,
                            'protocol': 'blfcpdsb',
                            'prio': 8331,
                            'filtertype': 'aenqufkj',
                            'flowid': 6706,
                            'options': 'atebrfcn',
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


def test_that_tc_filter_change(capfd):

    dv1 = TestDevice(platform='dentos')
    dv2 = TestDevice(platform='dentos')
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        TcFilter.change(
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
        TcFilter.change(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            # command 1
                            'dev': 'nbnfmhla',
                            'parent': 9684,
                            'root': False,
                            'handle': 8876,
                            'protocol': 'kmpvmctv',
                            'prio': 6842,
                            'filtertype': 'caahtsvm',
                            'flowid': 9170,
                            'options': 'todmaarj',
                        },
                        {
                            # command 2
                            'dev': 'zdihykjz',
                            'parent': 2191,
                            'root': True,
                            'handle': 3463,
                            'protocol': 'xekvypvf',
                            'prio': 6255,
                            'filtertype': 'qwifhwve',
                            'flowid': 624,
                            'options': 'wwgdgawz',
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
        TcFilter.change(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            'dev': 'nbnfmhla',
                            'parent': 9684,
                            'root': False,
                            'handle': 8876,
                            'protocol': 'kmpvmctv',
                            'prio': 6842,
                            'filtertype': 'caahtsvm',
                            'flowid': 9170,
                            'options': 'todmaarj',
                        }
                    ],
                    # device 2
                    'test_dev2': [
                        {
                            'dev': 'zdihykjz',
                            'parent': 2191,
                            'root': True,
                            'handle': 3463,
                            'protocol': 'xekvypvf',
                            'prio': 6255,
                            'filtertype': 'qwifhwve',
                            'flowid': 624,
                            'options': 'wwgdgawz',
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


def test_that_tc_filter_replace(capfd):

    dv1 = TestDevice(platform='dentos')
    dv2 = TestDevice(platform='dentos')
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        TcFilter.replace(
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
        TcFilter.replace(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            # command 1
                            'dev': 'lnxayvof',
                            'parent': 2384,
                            'root': True,
                            'handle': 6837,
                            'protocol': 'mtjgqelf',
                            'prio': 8918,
                            'filtertype': 'rjktfagh',
                            'flowid': 6682,
                            'options': 'aillxzdw',
                        },
                        {
                            # command 2
                            'dev': 'qelzblmv',
                            'parent': 1187,
                            'root': False,
                            'handle': 7322,
                            'protocol': 'szcqetfh',
                            'prio': 6277,
                            'filtertype': 'bhnnmnox',
                            'flowid': 6481,
                            'options': 'ufzyuoxx',
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
        TcFilter.replace(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            'dev': 'lnxayvof',
                            'parent': 2384,
                            'root': True,
                            'handle': 6837,
                            'protocol': 'mtjgqelf',
                            'prio': 8918,
                            'filtertype': 'rjktfagh',
                            'flowid': 6682,
                            'options': 'aillxzdw',
                        }
                    ],
                    # device 2
                    'test_dev2': [
                        {
                            'dev': 'qelzblmv',
                            'parent': 1187,
                            'root': False,
                            'handle': 7322,
                            'protocol': 'szcqetfh',
                            'prio': 6277,
                            'filtertype': 'bhnnmnox',
                            'flowid': 6481,
                            'options': 'ufzyuoxx',
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


def test_that_tc_filter_delete(capfd):

    dv1 = TestDevice(platform='dentos')
    dv2 = TestDevice(platform='dentos')
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        TcFilter.delete(
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
        TcFilter.delete(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            # command 1
                            'dev': 'gbwprcxm',
                            'parent': 5881,
                            'root': False,
                            'handle': 8818,
                            'protocol': 'wgnmkecq',
                            'prio': 6750,
                            'filtertype': 'tihpsyty',
                            'flowid': 5406,
                            'options': 'cuuemikg',
                        },
                        {
                            # command 2
                            'dev': 'sqigwmcg',
                            'parent': 2148,
                            'root': False,
                            'handle': 655,
                            'protocol': 'zsbgblbs',
                            'prio': 1523,
                            'filtertype': 'ezbberog',
                            'flowid': 9360,
                            'options': 'ytbhkjkp',
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
        TcFilter.delete(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            'dev': 'gbwprcxm',
                            'parent': 5881,
                            'root': False,
                            'handle': 8818,
                            'protocol': 'wgnmkecq',
                            'prio': 6750,
                            'filtertype': 'tihpsyty',
                            'flowid': 5406,
                            'options': 'cuuemikg',
                        }
                    ],
                    # device 2
                    'test_dev2': [
                        {
                            'dev': 'sqigwmcg',
                            'parent': 2148,
                            'root': False,
                            'handle': 655,
                            'protocol': 'zsbgblbs',
                            'prio': 1523,
                            'filtertype': 'ezbberog',
                            'flowid': 9360,
                            'options': 'ytbhkjkp',
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


def test_that_tc_filter_get(capfd):

    dv1 = TestDevice(platform='dentos')
    dv2 = TestDevice(platform='dentos')
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        TcFilter.get(
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
        TcFilter.get(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            # command 1
                            'dev': 'zpbefgpw',
                            'parent': 7383,
                            'root': True,
                            'handle': 8560,
                            'protocol': 'stvcyuuz',
                            'prio': 9615,
                            'filtertype': 'kgitqszn',
                            'flowid': 3368,
                            'options': 'gobykggt',
                        },
                        {
                            # command 2
                            'dev': 'flsfsjqr',
                            'parent': 1036,
                            'root': True,
                            'handle': 654,
                            'protocol': 'jiumzgkn',
                            'prio': 4342,
                            'filtertype': 'omkbssuw',
                            'flowid': 9288,
                            'options': 'jwsgtchi',
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
        TcFilter.get(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            'dev': 'zpbefgpw',
                            'parent': 7383,
                            'root': True,
                            'handle': 8560,
                            'protocol': 'stvcyuuz',
                            'prio': 9615,
                            'filtertype': 'kgitqszn',
                            'flowid': 3368,
                            'options': 'gobykggt',
                        }
                    ],
                    # device 2
                    'test_dev2': [
                        {
                            'dev': 'flsfsjqr',
                            'parent': 1036,
                            'root': True,
                            'handle': 654,
                            'protocol': 'jiumzgkn',
                            'prio': 4342,
                            'filtertype': 'omkbssuw',
                            'flowid': 9288,
                            'options': 'jwsgtchi',
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


def test_that_tc_filter_show(capfd):

    dv1 = TestDevice(platform='dentos')
    dv2 = TestDevice(platform='dentos')
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        TcFilter.show(
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
        TcFilter.show(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            # command 1
                            'dev': 'pppkltvq',
                            'block': 9205,
                            'options': 'hwpvhiye',
                        },
                        {
                            # command 2
                            'dev': 'hbifwlsy',
                            'block': 2776,
                            'options': 'qlwfpnfr',
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
        TcFilter.show(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            'dev': 'pppkltvq',
                            'block': 9205,
                            'options': 'hwpvhiye',
                        }
                    ],
                    # device 2
                    'test_dev2': [
                        {
                            'dev': 'hbifwlsy',
                            'block': 2776,
                            'options': 'qlwfpnfr',
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
